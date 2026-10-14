import {test, expect} from 'claude-code/testing';
import {parseStatusZ, takeBaseline, hasNewEntry, changedSince, BASELINE_MAX} from '../hooks/snapshot.js';

const before = takeBaseline([
  {code: ' M', path: 'a.ts', mtimeMs: 100},
  {code: '??', path: 'GEMINI.md', mtimeMs: 50},
  {code: ' D', path: 'gone.ts', mtimeMs: null},
], 3);
const same = () => [
  {code: ' M', path: 'a.ts', mtimeMs: 100},
  {code: '??', path: 'GEMINI.md', mtimeMs: 50},
  {code: ' D', path: 'gone.ts', mtimeMs: null},
];

test('-z output: plain entries, a rename that carries its old path, untracked and Chinese names, deletions', () => {
  expect(parseStatusZ(' M src/a.ts\0R  new.ts\0old.ts\0?? 筆記.md\0 D gone.ts\0')).toEqual([
    {code: ' M', path: 'src/a.ts'}, {code: 'R ', path: 'new.ts'}, {code: '??', path: '筆記.md'}, {code: ' D', path: 'gone.ts'},
  ]);
  expect(parseStatusZ('')).toEqual([]);
  expect(parseStatusZ(undefined as any)).toEqual([]);
});
test('a baseline keeps at most BASELINE_MAX entries and says when the status was longer', () => {
  const entries = Array.from({length: BASELINE_MAX}, (_, i) => ({code: '??', path: `f${i}`, mtimeMs: i}));
  expect(takeBaseline(entries, BASELINE_MAX)).toEqual({entries, truncated: false});
  expect(takeBaseline(entries, BASELINE_MAX + 1).truncated).toBe(true);
  expect(takeBaseline([...entries, {code: '??', path: 'extra', mtimeMs: 1}], BASELINE_MAX + 1).entries.length).toBe(BASELINE_MAX);
});
test('nothing touched, including a deletion from before: no change', () => {
  expect(changedSince(before, same())).toBe(false);
});
test('a file written again: change', () => {
  expect(changedSince(before, same().map((e) => (e.path === 'a.ts' ? {...e, mtimeMs: 101} : e)))).toBe(true);
});
test('a new file: change', () => {
  expect(changedSince(before, [...same(), {code: '??', path: 'new.ts', mtimeMs: 1}])).toBe(true);
});
test('staging only changes the code, and that is a change', () => {
  expect(changedSince(before, same().map((e) => (e.path === 'a.ts' ? {...e, code: 'M '} : e)))).toBe(true);
});
test('a file deleted during the session: change', () => {
  expect(changedSince(before, same().map((e) => (e.path === 'a.ts' ? {code: ' D', path: 'a.ts', mtimeMs: null} : e)))).toBe(true);
});
test('a file that cannot be read now, and is not a deletion: change', () => {
  expect(changedSince(before, same().map((e) => (e.path === 'a.ts' ? {...e, mtimeMs: null} : e)))).toBe(true);
});
test('a file that went back to clean is not a change', () => {
  expect(changedSince(before, same().filter((e) => e.path !== 'a.ts'))).toBe(false);
});
test('hasNewEntry looks at codes and paths only', () => {
  expect(hasNewEntry(before, [{code: ' M', path: 'a.ts'}])).toBe(false);
  expect(hasNewEntry(before, [{code: 'M ', path: 'a.ts'}])).toBe(true);
  expect(hasNewEntry(before, [{code: '??', path: 'other'}])).toBe(true);
});
