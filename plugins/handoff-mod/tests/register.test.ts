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
// The skill.prompt event does not fire for a typed plugin skill in Tom's environment (macOS, 2.1.292), so the command text
// and the command itself must start a run as well.
const FILE_AFTER = `${HANDOFF_DIR}/feat-x--20261007-120500.md`;
test('typing the skill command starts a run even when skill.prompt never fires', async ($, on) => {
  const w = world(on);
  await startSession($);
  await $.prompt.submit({text: '/handoff-mod:handoff', wait: false, origin: {kind: 'composer'}});
  await doneTurn($);
  w.files.set(FILE_AFTER, {text: handoffText(), mtimeMs: NOW + 5000});
  await doneTurn($);
  expect(w.rec.toasts).toEqual([`交接已寫入 ${FILE_AFTER}`]);
});
test('running the skill as a command starts a run even when skill.prompt never fires', async ($, on) => {
  const w = world(on);
  await startSession($);
  await $.command.run({command: 'handoff-mod:handoff', args: ''});
  await doneTurn($);
  w.files.set(FILE_AFTER, {text: handoffText(), mtimeMs: NOW + 5000});
  await doneTurn($);
  expect(w.rec.toasts).toEqual([`交接已寫入 ${FILE_AFTER}`]);
});
test('other slash commands, and a longer command name, do not start a run', async ($, on) => {
  const w = world(on);
  await startSession($);
  await w.flush();
  const before = w.rec.fsCalls;
  await $.prompt.submit({text: '/handoff-resume', wait: false, origin: {kind: 'composer'}});
  await $.prompt.submit({text: '/handoff-mod:handoffs', wait: false, origin: {kind: 'composer'}});
  await doneTurn($);
  await doneTurn($);
  expect(w.rec.fsCalls).toBe(before);
});
test('a start signal arriving three ways is one run', async ($, on) => {
  const w = world(on);
  await startSession($);
  await $.prompt.submit({text: '/handoff-mod:handoff', wait: false, origin: {kind: 'composer'}});
  await $.command.run({command: 'handoff-mod:handoff', args: ''});
  await $.skill.prompt(START_SKILL);
  await doneTurn($);
  w.files.set(FILE_AFTER, {text: handoffText(), mtimeMs: NOW + 5000});
  await doneTurn($);
  expect(w.rec.toasts.length).toBe(1);
  expect(w.store.get('stats').written).toBe(1);
});
test('HANDOFF_DEBUG traces the detection, and without it nothing extra is logged', async ($, on) => {
  const w = world(on, {env: {HANDOFF_DEBUG: '1'}});
  await startSession($);
  await $.skill.prompt(START_SKILL);
  await doneTurn($);
  w.files.set(`${HANDOFF_DIR}/feat-x--20261007-120500.md`, {text: handoffText(), mtimeMs: NOW + 5000});
  await doneTurn($);
  const traced = w.rec.logs.filter((line) => line.startsWith('[handoff-mod debug]'));
  expect(traced.some((line) => line.includes('skill.prompt skill=handoff-mod:handoff'))).toBe(true);
  expect(traced.some((line) => line.includes('handoff run started'))).toBe(true);
  expect(traced.some((line) => line.includes('nothing valid yet'))).toBe(true);
  expect(traced.some((line) => line.includes('valid=true'))).toBe(true);
  expect(traced.some((line) => line.includes('found '))).toBe(true);
});
test('without HANDOFF_DEBUG no trace line is logged', async ($, on) => {
  const w = world(on);
  await startSession($);
  await $.skill.prompt(START_SKILL);
  await doneTurn($);
  w.files.set(`${HANDOFF_DIR}/feat-x--20261007-120500.md`, {text: handoffText(), mtimeMs: NOW + 5000});
  await doneTurn($);
  expect(w.rec.logs.filter((line) => line.includes('[handoff-mod debug]')).length).toBe(0);
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

// --- slice c: /clear interception (T2) ---------------------------------------------------------------------------
const OPTIONS = ['取消', '先交接再清除', '直接清除'];
const labels = (question: any) => question.options.map((option: any) => (typeof option === 'string' ? option : option.label));
const clear = ($: any) => $.command.run({command: 'clear', args: ''});

test('a /clear in a session with prompts asks first, with cancel as the first option', async ($, on) => {
  const w = world(on, {turns: 3, ask: () => '直接清除'});
  await startSession($);
  await clear($);
  expect(w.rec.asks.length).toBe(1);
  expect(labels(w.rec.asks[0])).toEqual(OPTIONS);
  expect(w.rec.asks[0].question).toBe('要先交接再清除嗎？');
});
test('"clear now" lets the /clear run', async ($, on) => {
  const w = world(on, {turns: 3, ask: () => '直接清除'});
  await startSession($);
  await clear($);
  expect(w.rec.ran).toEqual(['clear']);
});
test('cancel, dismissing the question, and typed text all keep the conversation', async ($, on) => {
  let answer = '取消';
  const w = world(on, {turns: 3, ask: () => answer});
  await startSession($);
  const results: any[] = [];
  results.push(await clear($));
  answer = 'reject';
  results.push(await clear($));
  answer = '請幫我清掉吧';
  results.push(await clear($));
  expect(w.rec.ran.filter((c) => c === 'clear').length).toBe(0);
  expect(results[0].text).toBe('已取消清除。');
  expect(results[1].text).toBe('已取消清除。');
  expect(results[2].text).toBe('已取消清除。');
  expect(w.rec.asks.length).toBe(3);
});
test('"hand off, then clear" holds the /clear and starts the handoff skill after the command has finished', async ($, on) => {
  const w = world(on, {turns: 3, ask: () => '先交接再清除'});
  await startSession($);
  const result: any = await clear($);
  expect(result.text).toBe('已暫停清除，交接完成後請再下 /clear。');
  expect(w.rec.ran).toEqual([]);
  await w.clock.advance(500);
  expect(w.rec.ran).toEqual(['handoff-mod:handoff']);
});
test('no question when the conversation has no prompts yet', async ($, on) => {
  const w = world(on, {turns: 0});
  await startSession($);
  await clear($);
  expect(w.rec.asks.length).toBe(0);
  expect(w.rec.ran).toEqual(['clear']);
});
test('no question in a headless session', async ($, on) => {
  const w = world(on, {turns: 3, surfaces: []});
  await clear($);
  expect(w.rec.asks.length).toBe(0);
  expect(w.rec.ran).toEqual(['clear']);
});
test('a second /clear while a question is open is cancelled without a second question', async ($, on) => {
  const w = world(on, {turns: 3, askDelay: 1000, ask: () => '直接清除'});
  await startSession($);
  const first = clear($);
  await w.flush();
  const second: any = await clear($);
  expect(second.text).toBe('已取消清除。');
  expect(w.rec.asks.length).toBe(1);
  await w.clock.advance(1500);
  await first;
  expect(w.rec.ran).toEqual(['clear']);
});
test('after a question has been answered the next /clear asks again', async ($, on) => {
  const w = world(on, {turns: 3, ask: () => '取消'});
  await startSession($);
  await clear($);
  await clear($);
  expect(w.rec.asks.length).toBe(2);
});
test('an answer that arrives after the session has changed does nothing', async ($, on) => {
  let id = 'sess-A';
  const w = world(on, {turns: 3, sessionId: () => id, ask: () => { id = 'sess-B'; return '直接清除'; }});
  await startSession($);
  const result: any = await clear($);
  expect(result).toEqual({});
  expect(w.rec.ran).toEqual([]);
});

// --- slice b: T1, the context threshold prompt ----------------------------------------------------------------------
const DIRTY = {'status --porcelain': [0, ' M src/login.ts\n'] as [number, string]};
const QUESTION = (percent: number) => `Context 已用 ${percent}%，要先交接嗎？`;
const STATUS = (percent: number) => `Context 已用 ${percent}%。需要時輸入 /handoff-mod:handoff 交接`;
const t1Keys = ['t1-agree', 't1-snooze', 't1-suppress'];
const turnAt = async ($: any, w: any, percent: number | undefined) => { w.setPercent(percent); await doneTurn($); await w.flush(); };

test('at the threshold with unfinished work, a status line and a band with three answers appear', async ($, on) => {
  const w = world(on, {git: DIRTY, turns: 2});
  await startSession($);
  await turnAt($, w, 60);
  expect(w.lastStatus()).toBe(STATUS(60));
  const band = await mountBand($);
  expect(await band.find({type: 'Text', text: QUESTION(60)})).toBeDefined();
  for (const key of t1Keys) expect(await band.find({key})).toBeDefined();
});
test('nothing is asked below the threshold, without a percentage, on a clean tree, or outside git', async ($, on) => {
  const below = world(on, {git: DIRTY});
  await startSession($);
  await turnAt($, below, 59);
  await turnAt($, below, undefined);
  expect(below.lastStatus()).toBe(undefined);
});
test('a clean working tree is not unfinished work', async ($, on) => {
  const w = world(on, {git: {'status --porcelain': [0, '']}});
  await startSession($);
  await turnAt($, w, 80);
  expect(w.lastStatus()).toBe(undefined);
  expect(await (await mountBand($)).find({key: 't1-agree'})).toBeUndefined();
});
test('outside a git tree nothing is asked', async ($, on) => {
  const w = world(on, {git: {'status --porcelain': [128, '']}});
  await startSession($);
  await turnAt($, w, 80);
  expect(w.lastStatus()).toBe(undefined);
});
test('a threshold is asked once: later turns neither stack nor reopen it', async ($, on) => {
  const w = world(on, {git: DIRTY});
  await startSession($);
  await turnAt($, w, 61);
  const statuses = w.rec.statuses.length;
  await turnAt($, w, 63);
  expect(w.rec.statuses.length).toBe(statuses);
  expect(w.lastStatus()).toBe(STATUS(61));
});
test('agree takes the prompt down and starts the handoff skill from a timer', async ($, on) => {
  const w = world(on, {git: DIRTY});
  await startSession($);
  await turnAt($, w, 62);
  const band = await mountBand($);
  await band.press({key: 't1-agree'});
  expect(w.lastStatus()).toBe(undefined);
  expect(await band.find({key: 't1-agree'})).toBeUndefined();
  expect(w.rec.ran).toEqual([]);
  await w.clock.advance(500);
  expect(w.rec.ran).toEqual(['handoff-mod:handoff']);
});
test('"ask again in 10%" hides the prompt and asks at ten points above where the person is', async ($, on) => {
  const w = world(on, {git: DIRTY});
  await startSession($);
  await turnAt($, w, 61);
  await (await mountBand($)).press({key: 't1-snooze'});
  expect(w.lastStatus()).toBe(undefined);
  await turnAt($, w, 70);
  expect(w.lastStatus()).toBe(undefined);
  await turnAt($, w, 71);
  expect(w.lastStatus()).toBe(STATUS(71));
});
test('"do not ask again" silences the session', async ($, on) => {
  const w = world(on, {git: DIRTY});
  await startSession($);
  await turnAt($, w, 61);
  const band = await mountBand($);
  await band.press({key: 't1-suppress'});
  expect(w.lastStatus()).toBe(undefined);
  await turnAt($, w, 95);
  expect(w.lastStatus()).toBe(undefined);
  expect(await band.find({key: 't1-agree'})).toBeUndefined();
});
test('"do not ask again" survives a compaction that makes the threshold askable again', async ($, on) => {
  const w = world(on, {git: DIRTY});
  await startSession($);
  await turnAt($, w, 61);
  await (await mountBand($)).press({key: 't1-suppress'});
  await turnAt($, w, 8);
  await turnAt($, w, 75);
  expect(w.lastStatus()).toBe(undefined);
});
test('after compaction the percentage falls, the prompt goes, and the threshold is asked again', async ($, on) => {
  const w = world(on, {git: DIRTY});
  await startSession($);
  await turnAt($, w, 65);
  expect(w.lastStatus()).toBe(STATUS(65));
  await turnAt($, w, 8);
  expect(w.lastStatus()).toBe(undefined);
  await turnAt($, w, 60);
  expect(w.lastStatus()).toBe(STATUS(60));
});
test('no question while a handoff is running, and starting one takes an open prompt down', async ($, on) => {
  const w = world(on, {git: DIRTY});
  await startSession($);
  await turnAt($, w, 65);
  await $.prompt.submit({text: '/handoff-mod:handoff', wait: false, origin: {kind: 'composer'}});
  await w.flush();
  expect(w.lastStatus()).toBe(undefined);
  await turnAt($, w, 90);
  expect(w.lastStatus()).toBe(undefined);
});
test('a new conversation after /clear starts without the old prompt', async ($, on) => {
  const w = world(on, {git: DIRTY});
  await startSession($);
  await turnAt($, w, 65);
  await startSession($, 'clear');
  await w.flush();
  expect(w.lastStatus()).toBe(undefined);
  expect(await (await mountBand($)).find({key: 't1-agree'})).toBeUndefined();
});
test('HANDOFF_THRESHOLD_PCT moves the threshold', async ($, on) => {
  const w = world(on, {git: DIRTY, env: {HANDOFF_THRESHOLD_PCT: '10'}});
  await startSession($);
  await turnAt($, w, 9);
  expect(w.lastStatus()).toBe(undefined);
  await turnAt($, w, 10);
  expect(w.lastStatus()).toBe(STATUS(10));
});
test('the start-up list keeps the status line while it shows, and the prompt takes it over after the list goes', async ($, on) => {
  const w = world(on, {files: twoHandoffs, git: DIRTY});
  await startSession($);
  await w.flush();
  await turnAt($, w, 70);
  expect(w.lastStatus()).toBe('有 2 筆未完成交接，輸入 /handoff-resume 查看');
  await (await mountBand($)).press({key: 'skip'});
  expect(w.lastStatus()).toBe(STATUS(70));
});
test('sub-agent and aborted turns still go through the threshold check without breaking it', async ($, on) => {
  const w = world(on, {git: DIRTY});
  await startSession($);
  w.setPercent(70);
  await doneTurn($, {agentId: 'sub'});
  await doneTurn($, {isAborted: true});
  await w.flush();
  expect(w.lastStatus()).toBe(undefined);
});
