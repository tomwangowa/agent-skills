import {test, expect} from 'claude-code/testing';
import {handoffKey, mergeCopies, stateKeys, claimKeys, newestState} from '../hooks/identity.js';

const DIR = '.claude/handoffs';
const ctx = {base: '/work/wt', repo: '/work/app', dir: DIR};
const copy = (path: string, o: {created?: string; closed?: boolean; task?: string} = {}) => ({
  path,
  meta: {created: Date.parse(o.created ?? '2026-10-09T03:15:22Z'), status: o.closed ? 'resumed' : 'in-progress'},
  fields: {task: o.task ?? 't', next: ''},
  closed: o.closed ?? false,
});

test('the key is the file name and the created time as ISO, however created was written', () => {
  expect(handoffKey('main--20261009-111522.md', Date.parse('2026-10-09T11:15:22+08:00'))).toBe('main--20261009-111522.md|2026-10-09T03:15:22.000Z');
  expect(handoffKey('a.md', Date.parse('2026-10-09T03:15:22Z'))).toBe(handoffKey('a.md', Date.parse('2026-10-09T11:15:22+08:00')));
});
test('copies of one file in several working trees become one item that knows every path, in scan order', () => {
  const items = mergeCopies([copy('/work/app/.claude/handoffs/a.md'), copy('/work/other/.claude/handoffs/a.md'), copy('/work/wt/.claude/handoffs/a.md')], ctx);
  expect(items.length).toBe(1);
  expect(items[0].key).toBe('a.md|2026-10-09T03:15:22.000Z');
  expect(items[0].paths).toEqual(['/work/app/.claude/handoffs/a.md', '/work/other/.claude/handoffs/a.md', '/work/wt/.claude/handoffs/a.md']);
});
test("the shown copy is this working tree's, then the main checkout's, then the first found", () => {
  expect(mergeCopies([copy('/work/app/.claude/handoffs/a.md'), copy('/work/wt/.claude/handoffs/a.md')], ctx)[0].path).toBe('/work/wt/.claude/handoffs/a.md');
  expect(mergeCopies([copy('/work/other/.claude/handoffs/a.md'), copy('/work/app/.claude/handoffs/a.md')], ctx)[0].path).toBe('/work/app/.claude/handoffs/a.md');
  expect(mergeCopies([copy('/x/.claude/handoffs/a.md'), copy('/y/.claude/handoffs/a.md')], ctx)[0].path).toBe('/x/.claude/handoffs/a.md');
});
test('a worktree nested under the base is not taken for the base', () => {
  const nested = '/work/wt/.claude/worktrees/n/.claude/handoffs/a.md';
  expect(mergeCopies([copy(nested), copy('/work/app/.claude/handoffs/a.md')], ctx)[0].path).toBe('/work/app/.claude/handoffs/a.md');
});
test('the shown copy gives the task and the meta', () => {
  const main = copy('/work/app/.claude/handoffs/a.md', {task: 'main copy'});
  const here = copy('/work/wt/.claude/handoffs/a.md', {task: 'edited here'});
  const [item] = mergeCopies([main, here], ctx);
  expect(item.fields.task).toBe('edited here');
  expect(item.meta).toBe(here.meta);
});
test('another created time, or another name, stays a separate handoff', () => {
  const items = mergeCopies([copy('/x/.claude/handoffs/a.md'), copy('/y/.claude/handoffs/a.md', {created: '2026-10-09T03:15:23Z'}), copy('/y/.claude/handoffs/b.md')], ctx);
  expect(items.length).toBe(3);
});
test('one closed copy closes the item; with no closed copy it stays open', () => {
  expect(mergeCopies([copy('/x/.claude/handoffs/a.md'), copy('/y/.claude/handoffs/a.md', {closed: true})], ctx)[0].fileClosed).toBe(true);
  expect(mergeCopies([copy('/x/.claude/handoffs/a.md')], ctx)[0].fileClosed).toBe(false);
});
test("state and claim keys: the new key first, then every copy's old path key", () => {
  const [item] = mergeCopies([copy('/work/app/.claude/handoffs/a.md'), copy('/work/wt/.claude/handoffs/a.md')], ctx);
  expect(stateKeys(item)).toEqual(['state:id:a.md|2026-10-09T03:15:22.000Z', 'state:/work/app/.claude/handoffs/a.md', 'state:/work/wt/.claude/handoffs/a.md']);
  expect(claimKeys(item)).toEqual(['claim:id:a.md|2026-10-09T03:15:22.000Z', 'claim:/work/app/.claude/handoffs/a.md', 'claim:/work/wt/.claude/handoffs/a.md']);
});
test('newestState picks the latest record with a status and ignores the rest', () => {
  expect(newestState([undefined, {status: 'abandoned', at: 1}, {status: 'resumed', at: 5}, 'garbage', {at: 9}, null])).toEqual({status: 'resumed', at: 5});
  expect(newestState([undefined, null])).toBeUndefined();
});
