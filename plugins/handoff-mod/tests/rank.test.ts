import {test, expect} from 'claude-code/testing';
import {rankHandoffs} from '../hooks/rank.js';

const DAY = 24 * 3600 * 1000;
const now = Date.parse('2026-10-20T00:00:00Z');
const item = (path: string, daysAgo: number, o: any = {}) => ({
  path, effectiveStatus: o.status ?? 'in-progress', claimedByOther: o.claimed ?? false,
  meta: {root: o.root ?? '/other', repo: o.repo, created: now - daysAgo * DAY, source: o.source, task: path},
});
const ctx = {base: '/work/app', repo: '/work/app', now};
const paths = (r: any) => r.shown.map((i: any) => i.path);

test('only open statuses are listed', () => {
  const r = rankHandoffs([item('a', 1), item('b', 1, {status: 'resumed'}), item('c', 1, {status: 'done'}), item('d', 1, {status: 'abandoned'}), item('e', 1, {status: 'blocked'})], ctx);
  expect(paths(r).sort()).toEqual(['a', 'e']);
});
test('same base first, then same repo, then newest', () => {
  const r = rankHandoffs([item('old-other', 5), item('new-other', 1), item('repo-mate', 3, {root: '/work/app-wt', repo: '/work/app'}), item('here-old', 9, {root: '/work/app'})], ctx);
  expect(paths(r)).toEqual(['here-old', 'repo-mate', 'new-other']);
});
test('three are shown and the rest collapse into a count', () => {
  const r = rankHandoffs([1, 2, 3, 4, 5].map((n) => item(`p${n}`, n)), ctx);
  expect(paths(r)).toEqual(['p1', 'p2', 'p3']);
  expect(r.collapsed).toBe(2);
});
test('entries older than 14 days are folded', () => {
  const r = rankHandoffs([item('fresh', 2), item('stale', 20)], ctx);
  expect(paths(r)).toEqual(['fresh']);
  expect(r.collapsed).toBe(1);
});
test('automatic notes older than 7 days are neither shown nor counted', () => {
  const r = rankHandoffs([item('auto-old', 8, {source: 'auto'}), item('auto-new', 3, {source: 'auto'}), item('manual-8d', 8)], ctx);
  expect(paths(r).sort()).toEqual(['auto-new', 'manual-8d']);
  expect(r.collapsed).toBe(0);
  expect(r.hidden).toBe(1);
});
test('an item claimed by another session stays in the list with its flag', () => {
  const r = rankHandoffs([item('taken', 1, {claimed: true})], ctx);
  expect(r.shown[0].claimedByOther).toBe(true);
});
test('the order does not depend on the input order', () => {
  const items = [item('a', 3), item('b', 3), item('c', 3), item('d', 1)];
  const forward = paths(rankHandoffs(items, ctx));
  const backward = paths(rankHandoffs([...items].reverse(), ctx));
  expect(forward).toEqual(backward);
});
