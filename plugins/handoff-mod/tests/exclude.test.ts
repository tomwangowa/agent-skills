import {test, expect} from 'claude-code/testing';
import {ensureExcluded} from '../hooks/exclude.js';

const PATTERN = '.claude/handoffs/';
function setup(o: {ignored?: number; excludePath?: string; files?: Record<string, string>; writeThrows?: boolean; revParseFails?: boolean} = {}) {
  const files = new Map(Object.entries(o.files ?? {}));
  const writes: Array<[string, string]> = [];
  const calls: string[][] = [];
  const git = async (args: string[]) => {
    calls.push(args);
    if (args[0] === 'check-ignore') return {exitCode: o.ignored ?? 1, stdout: ''};
    if (args[0] === 'rev-parse') return o.revParseFails ? {exitCode: 128, stdout: ''} : {exitCode: 0, stdout: `${o.excludePath ?? '.git/info/exclude'}\n`};
    return {exitCode: 128, stdout: ''};
  };
  const fs = {
    exists: async (p: string) => files.has(p),
    read: async (p: string) => files.get(p) ?? '',
    write: async (p: string, text: string) => { if (o.writeThrows) throw new Error('read-only'); files.set(p, text); writes.push([p, text]); },
  };
  return {git, fs, files, writes, calls};
}

test('outside a git repository nothing is touched', async () => {
  const s = setup({ignored: 128});
  expect(await ensureExcluded({git: s.git, fs: s.fs, pattern: PATTERN})).toMatchObject({ok: false, skipped: true});
  expect(s.writes.length).toBe(0);
});
test('an already ignored path is left alone', async () => {
  const s = setup({ignored: 0});
  expect(await ensureExcluded({git: s.git, fs: s.fs, pattern: PATTERN})).toMatchObject({ok: true, changed: false});
  expect(s.writes.length).toBe(0);
});
test('a missing exclude file is created with the pattern', async () => {
  const s = setup();
  expect(await ensureExcluded({git: s.git, fs: s.fs, pattern: PATTERN})).toMatchObject({ok: true, changed: true});
  expect(s.files.get('.git/info/exclude')).toBe(`${PATTERN}\n`);
});
test('an existing file gets the pattern appended, with a newline added when it was missing', async () => {
  const withNewline = setup({files: {'.git/info/exclude': 'foo\n'}});
  await ensureExcluded({git: withNewline.git, fs: withNewline.fs, pattern: PATTERN});
  expect(withNewline.files.get('.git/info/exclude')).toBe(`foo\n${PATTERN}\n`);
  const without = setup({files: {'.git/info/exclude': 'foo'}});
  await ensureExcluded({git: without.git, fs: without.fs, pattern: PATTERN});
  expect(without.files.get('.git/info/exclude')).toBe(`foo\n${PATTERN}\n`);
});
test('a file that already has the line is not written again, so repeated runs are harmless', async () => {
  const s = setup({files: {'.git/info/exclude': `foo\n${PATTERN}\n`}});
  expect(await ensureExcluded({git: s.git, fs: s.fs, pattern: PATTERN})).toMatchObject({ok: true, changed: false});
  expect(s.writes.length).toBe(0);
  const first = setup();
  await ensureExcluded({git: first.git, fs: first.fs, pattern: PATTERN});
  const second = await ensureExcluded({git: first.git, fs: first.fs, pattern: PATTERN});
  expect(second).toMatchObject({changed: false});
  expect(first.writes.length).toBe(1);
});
test('the path comes from git, so a worktree gets its own correct location', async () => {
  const s = setup({excludePath: '/repo/.git/worktrees/wt/info/exclude'});
  await ensureExcluded({git: s.git, fs: s.fs, pattern: PATTERN});
  expect(s.files.has('/repo/.git/worktrees/wt/info/exclude')).toBe(true);
  expect(s.calls.some((c) => c.join(' ') === 'rev-parse --git-path info/exclude')).toBe(true);
});
test('a failing write or a failing rev-parse reports failure without throwing', async () => {
  expect(await ensureExcluded({git: setup({writeThrows: true}).git, fs: setup({writeThrows: true}).fs, pattern: PATTERN})).toMatchObject({ok: false});
  const s = setup({revParseFails: true});
  expect(await ensureExcluded({git: s.git, fs: s.fs, pattern: PATTERN})).toMatchObject({ok: false});
});
