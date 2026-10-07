import {expect, test} from 'claude-code/testing';
import {handoffText} from './fixtures.js';
import {world, twoHandoffs, fileA, fileB, HANDOFF_DIR, bandTarget, startSession, doneTurn, NOW} from './world.js';

const mountBand = ($: any) => $.ui.mount(bandTarget);

// --- slice a: registration and settings ---------------------------------------------------------------------------
test('the resume command is registered at session start, in the configured language', async ($, on) => {
  const w = world(on, {env: {HANDOFF_LANG: 'en'}});
  await $.session.start({surface: 'terminal', isInteractive: true, cwd: '/work/app'});
  expect(w.rec.commands.length).toBe(1);
  expect(w.rec.commands[0].name).toBe('handoff-resume');
  expect(w.rec.commands[0].description).toContain('List unfinished handoffs');
});

// --- slice e: start-up read-back ----------------------------------------------------------------------------------
test('unfinished handoffs show as a status line and a band with their details', async ($, on) => {
  const w = world(on, {files: twoHandoffs});
  await startSession($);
  await w.flush();
  expect(w.lastStatus()).toBe('有 2 筆未完成交接，輸入 /handoff-resume 查看');
  const band = await mountBand($);
  expect(await band.find({type: 'Text', text: 'engine band'})).toBeDefined();
  expect(await band.find({type: 'Text', text: /1\. 修正登入逾時（feat\/login-timeout・\d+ 小時前）/})).toBeDefined();
  expect(await band.find({type: 'Text', text: /2\. 其他工作/})).toBeDefined();
  expect(await band.find({type: 'Text', text: '下一步：重跑 auth 測試'})).toBeDefined();
  expect(await band.find({key: 'resume-0'})).toBeDefined();
  expect(await band.find({key: 'skip'})).toBeDefined();
});
test('with no handoffs nothing is drawn or shown', async ($, on) => {
  const w = world(on);
  await startSession($);
  await w.flush();
  expect(w.rec.statuses.filter((s) => s !== undefined).length).toBe(0);
  const band = await mountBand($);
  expect(await band.find({type: 'Text', text: 'engine band'})).toBeDefined();
  expect(await band.find({key: 'skip'})).toBeUndefined();
});
test('resuming claims the handoff, records it, fills the input box and clears the list', async ($, on) => {
  const w = world(on, {files: twoHandoffs});
  await startSession($);
  await w.flush();
  const band = await mountBand($);
  await band.press({key: 'resume-0'});
  expect(w.rec.fills.length).toBe(1);
  expect(w.rec.fills[0]).toContain(fileA);
  expect(w.rec.fills[0]).toContain('驗證其中前提');
  expect(w.store.get(`claim:${fileA}`).sessionId).toBe('sess-A');
  expect(w.store.get(`state:${fileA}`).status).toBe('resumed');
  expect(w.store.get('stats').resumed).toBe(1);
  expect(w.lastStatus()).toBe(undefined);
});
test('a handoff claimed by another session shows a label and no resume button, and nothing is filled', async ($, on) => {
  const w = world(on, {files: twoHandoffs, store: {[`claim:${fileA}`]: {sessionId: 'sess-B', at: NOW - 1000}}});
  await startSession($);
  await w.flush();
  const band = await mountBand($);
  expect(await band.find({key: 'resume-0'})).toBeUndefined();
  expect(await band.find({type: 'Text', text: '另一個 session 正在接續'})).toBeDefined();
  expect(w.rec.fills.length).toBe(0);
});
test('losing the claim race after the list was drawn tells the user and fills nothing', async ($, on) => {
  const w = world(on, {files: twoHandoffs});
  await startSession($);
  await w.flush();
  const band = await mountBand($);
  w.store.set(`claim:${fileA}`, {sessionId: 'sess-B', at: NOW});
  await band.press({key: 'resume-0'});
  expect(w.rec.toasts).toEqual(['這份交接正由另一個 session 接續。']);
  expect(w.rec.fills.length).toBe(0);
  expect(w.store.get(`state:${fileA}`)).toBe(undefined);
});
test('a handoff that was already resumed is not listed again', async ($, on) => {
  const w = world(on, {files: twoHandoffs, store: {[`state:${fileA}`]: {status: 'resumed', at: NOW, sessionId: 'sess-A'}}});
  await startSession($);
  await w.flush();
  expect(w.lastStatus()).toBe('有 1 筆未完成交接，輸入 /handoff-resume 查看');
});
test('skip hides the list for this session, and /handoff-resume still shows it', async ($, on) => {
  const w = world(on, {files: twoHandoffs});
  await startSession($);
  await w.flush();
  await (await mountBand($)).press({key: 'skip'});
  expect(w.lastStatus()).toBe(undefined);
  await $.classic.SessionStart({source: 'clear', session_id: 'sess-A'});
  await w.flush();
  // $.state is reset by /clear in a real session; here it is not, so the list stays hidden until the command forces it.
  await $.command.run({command: 'handoff-resume', args: ''});
  expect(w.rec.logs[0]).toBe('有 2 筆未完成交接');
  expect(w.rec.logs.length).toBe(3);
  expect(w.rec.logs[1]).toContain('1. 修正登入逾時');
});
test('resume, fork and compact starts do not list', async ($, on) => {
  const w = world(on, {files: twoHandoffs});
  for (const source of ['resume', 'fork', 'compact']) {
    await $.classic.SessionStart({source, session_id: 'sess-A'});
    await w.flush();
  }
  expect(w.rec.statuses.length).toBe(0);
});
test('a session with no surface (headless) does not list', async ($, on) => {
  const w = world(on, {files: twoHandoffs, surfaces: []});
  await $.classic.SessionStart({source: 'startup', session_id: 'sess-A'});
  await w.flush();
  expect(w.rec.statuses.length).toBe(0);
});
test('a conversation that already has prompts does not list at start', async ($, on) => {
  const w = world(on, {files: twoHandoffs, turns: 3});
  await startSession($);
  await w.flush();
  expect(w.rec.statuses.length).toBe(0);
});
test('/handoff-resume <n> resumes item n, and a bad number says so', async ($, on) => {
  const w = world(on, {files: twoHandoffs});
  await $.command.run({command: 'handoff-resume', args: '2'});
  expect(w.store.get(`state:${fileB}`).status).toBe('resumed');
  expect(w.rec.fills[0]).toContain(fileB);
  await $.command.run({command: 'handoff-resume', args: '9'});
  expect(w.rec.logs.some((line) => line.includes('沒有第 9 筆'))).toBe(true);
});
test('the first real prompt ends the list; a slash command does not', async ($, on) => {
  const w = world(on, {files: twoHandoffs});
  await startSession($);
  await w.flush();
  await $.prompt.submit({text: '/handoff-resume', wait: false, origin: {kind: 'composer'}});
  expect(w.lastStatus()).toBe('有 2 筆未完成交接，輸入 /handoff-resume 查看');
  await $.prompt.submit({text: '請繼續', wait: false, origin: {kind: 'composer'}});
  expect(w.lastStatus()).toBe(undefined);
});
test('freshness facts from git are shown with each handoff', async ($, on) => {
  const w = world(on, {files: {[fileA]: handoffText()}, git: {
    'rev-parse --verify --quiet refs/heads/feat/login-timeout': [0, ''],
    'rev-list --count 781ac6b..refs/heads/feat/login-timeout': [0, '12\n'],
  }});
  await startSession($);
  await w.flush();
  const band = await mountBand($);
  expect(await band.find({type: 'Text', text: 'feat/login-timeout 多了 12 個 commit'.replace('feat/login-timeout 多了', '交接後 feat/login-timeout 多了')})).toBeDefined();
});
test('a file with a bad status or a path outside the handoff directories is ignored', async ($, on) => {
  const w = world(on, {files: {[fileA]: handoffText({status: 'done'}), '/elsewhere/x--20261006-183000.md': handoffText()}});
  await startSession($);
  await w.flush();
  expect(w.rec.statuses.filter((s) => s !== undefined).length).toBe(0);
});

// --- slice d: verify the file the handoff wrote -------------------------------------------------------------------
const START_SKILL = {skill: 'handoff-mod:handoff', text: 'draft the handoff'};
test('a handoff run is confirmed by the file it wrote, which is also kept out of git status', async ($, on) => {
  const w = world(on);
  await startSession($);
  await $.skill.prompt(START_SKILL);
  await doneTurn($);
  expect(w.rec.toasts.length).toBe(0);
  w.files.set(`${HANDOFF_DIR}/feat-x--20261007-120500.md`, {text: handoffText(), mtimeMs: NOW + 5000});
  await doneTurn($);
  expect(w.rec.toasts).toEqual([`交接已寫入 ${HANDOFF_DIR}/feat-x--20261007-120500.md`]);
  expect(w.rec.writes.some(([path, text]) => path.endsWith('.git/info/exclude') && text.includes('.claude/handoffs/'))).toBe(true);
  expect(w.store.get('stats').written).toBe(1);
  await doneTurn($);
  expect(w.rec.toasts.length).toBe(1);
});
test('without a handoff run, turns do not touch the file system', async ($, on) => {
  const w = world(on);
  await startSession($);
  await w.flush();
  const before = w.rec.fsCalls;
  await doneTurn($);
  await doneTurn($);
  expect(w.rec.fsCalls).toBe(before);
  expect(w.rec.toasts.length).toBe(0);
});
test('no file after four turns is reported once, and a later file is still confirmed', async ($, on) => {
  const w = world(on);
  await startSession($);
  await $.skill.prompt(START_SKILL);
  for (let i = 0; i < 6; i++) await doneTurn($);
  expect(w.rec.toasts).toEqual(['未偵測到有效交接檔']);
  w.files.set(`${HANDOFF_DIR}/feat-x--20261007-121500.md`, {text: handoffText(), mtimeMs: NOW + 9000});
  await doneTurn($);
  expect(w.rec.toasts.length).toBe(2);
  expect(w.rec.toasts[1]).toContain('交接已寫入');
});
test('aborted turns and sub-agent turns neither count nor report', async ($, on) => {
  const w = world(on);
  await startSession($);
  await $.skill.prompt(START_SKILL);
  w.files.set(`${HANDOFF_DIR}/feat-x--20261007-120500.md`, {text: handoffText(), mtimeMs: NOW + 5000});
  await doneTurn($, {isAborted: true});
  await doneTurn($, {agentId: 'sub-1'});
  expect(w.rec.toasts.length).toBe(0);
  await doneTurn($);
  expect(w.rec.toasts.length).toBe(1);
});
test('a file with an invalid status, or one older than the run, is not reported as the handoff', async ($, on) => {
  const w = world(on);
  await startSession($);
  await $.skill.prompt(START_SKILL);
  w.files.set(`${HANDOFF_DIR}/feat-x--20261007-120500.md`, {text: handoffText({status: 'weird'}), mtimeMs: NOW + 5000});
  w.files.set(`${HANDOFF_DIR}/feat-y--20261001-010000.md`, {text: handoffText(), mtimeMs: NOW - 86_400_000});
  await doneTurn($);
  expect(w.rec.toasts.length).toBe(0);
});
test('starting the skill twice does not restart the count', async ($, on) => {
  const w = world(on);
  await startSession($);
  await $.skill.prompt(START_SKILL);
  await doneTurn($);
  await doneTurn($);
  await $.skill.prompt(START_SKILL);
  await doneTurn($);
  await doneTurn($);
  expect(w.rec.toasts).toEqual(['未偵測到有效交接檔']);
});
