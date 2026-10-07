import {test, expect} from 'claude-code/testing';
import {shouldWriteNote, buildEndNote, withDeadline} from '../hooks/note.js';
import {parseHandoff} from '../hooks/handoff-file.js';

const config = {autoNote: true};
const yes = {interactive: true, turns: 3, hasUnfinishedSign: true, reason: 'prompt_input_exit', config};
const input = (o: any = {}) => ({
  lastRequest: '修正登入逾時', lastResponse: '已修正 refreshToken，測試還沒跑。', branch: 'feat/x', head: '781ac6b',
  dirtyFiles: ['src/auth.ts', 'tests/auth.test.ts'], root: '/work/app', repo: '/work/app', now: Date.parse('2026-10-06T10:30:00Z'), lang: 'zh-TW', ...o,
});

test('a note is written only when every condition holds', () => {
  expect(shouldWriteNote(yes)).toBe(true);
  expect(shouldWriteNote({...yes, reason: 'other'})).toBe(true);
  expect(shouldWriteNote({...yes, interactive: false})).toBe(false);
  expect(shouldWriteNote({...yes, turns: 0})).toBe(false);
  expect(shouldWriteNote({...yes, hasUnfinishedSign: false})).toBe(false);
  expect(shouldWriteNote({...yes, reason: 'clear'})).toBe(false);
  expect(shouldWriteNote({...yes, config: {autoNote: false}})).toBe(false);
});
test('the note is facts only and marked automatic', () => {
  const {content, fileName}: any = buildEndNote(input());
  expect(content).toContain('schema: 1');
  expect(content).toContain('status: in-progress');
  expect(content).toContain('source: auto');
  expect(content).toContain('branch: feat/x');
  expect(content).toContain('修正登入逾時');
  expect(content).toContain('已修正 refreshToken');
  expect(content).toContain('src/auth.ts');
  expect(fileName).toMatch(/^feat-x--\d{8}-\d{6}--auto\.md$/);
});
test('with no git, branch, head and repo are omitted and the file name says no-branch', () => {
  const {content, fileName}: any = buildEndNote(input({branch: undefined, head: undefined, repo: null, dirtyFiles: []}));
  expect(content).not.toContain('branch:');
  expect(content).not.toContain('head:');
  expect(content).not.toContain('repo:');
  expect(fileName).toMatch(/^no-branch--/);
});
test('each quoted text is cut to 2000 code points', () => {
  const {content}: any = buildEndNote(input({lastResponse: 'x'.repeat(5000)}));
  expect(content).toContain('x'.repeat(1999) + '…');
  expect(content).not.toContain('x'.repeat(2000));
});
test('secrets and terminal escapes in the quoted text are removed', () => {
  const {content}: any = buildEndNote(input({lastRequest: 'fix it, password=hunter2hunter2', lastResponse: '\x1b[31mdone\x1b[0m'}));
  expect(content).not.toContain('hunter2');
  expect(content).toContain('[redacted]');
  expect(content).not.toContain('\x1b');
});
test('the note can be read back by the parser in both languages', () => {
  for (const lang of ['zh-TW', 'en']) {
    const {content}: any = buildEndNote(input({lang}));
    const r: any = parseHandoff(content);
    expect(r.ok).toBe(true);
    expect(r.meta.source).toBe('auto');
    expect(r.meta.status).toBe('in-progress');
    expect(r.fields.task).toBe('修正登入逾時');
    expect(r.fields.next.length > 0).toBe(true);
  }
});
test('a long changed-file list is capped and cleaned', () => {
  const dirtyFiles = Array.from({length: 80}, (_, i) => `file${i}\x1b[0m.ts`);
  const {content}: any = buildEndNote(input({dirtyFiles}));
  expect(content).toContain('file49.ts');
  expect(content).not.toContain('file50.ts');
  expect(content).not.toContain('\x1b');
});
test('withDeadline returns the value, the timeout or the error, and cancels its timer', async () => {
  let fire: any = null, cancelled = false;
  const after = (_ms: number, cb: () => void) => { fire = cb; return {cancel: () => { cancelled = true; }}; };
  expect(await withDeadline(async () => 7, 1500, after)).toEqual({value: 7});
  expect(cancelled).toBe(true);
  cancelled = false;
  const slow = withDeadline(() => new Promise(() => {}), 1500, after);
  fire();
  expect(await slow).toEqual({timedOut: true});
  const failed: any = await withDeadline(async () => { throw new Error('boom'); }, 1500, after);
  expect(failed.error.message).toBe('boom');
});
