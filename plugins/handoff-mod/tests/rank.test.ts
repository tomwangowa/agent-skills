import {test, expect} from 'claude-code/testing';
import {rankHandoffs} from '../hooks/rank.js';

const DAY = 24 * 3600 * 1000;
const now = Date.parse('2026-10-20T00:00:00Z');
const item = (path: string, daysAgo: number, o: any = {}) => ({
  path, effectiveStatus: o.status ?? 'in-progress', claimedByOther: o.claimed ?? false,
  meta: {root: o.root ?? '/other', repo: o.repo, branch: o.branch, created: now - daysAgo * DAY, source: o.source, task: path},
});
const ctx = {base: '/work/app', repo: '/work/app', now};
const paths = (r: any) => r.shown.map((i: any) => i.path);
const restPaths = (r: any) => r.rest.map((i: any) => i.path);

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
test('the rest is everything that is not shown, in ranked order', () => {
  const r = rankHandoffs([1, 2, 3, 4, 5].map((n) => item(`p${n}`, n)), ctx);
  expect(restPaths(r)).toEqual(['p4', 'p5']);
  expect(r.collapsed).toBe(2);
});
test('on one branch only the newest automatic note can be shown; older ones sit in the rest, flagged and counted', () => {
  const r = rankHandoffs([item('auto-new', 1, {source: 'auto', branch: 'b'}), item('auto-mid', 2, {source: 'auto', branch: 'b'}), item('auto-old', 3, {source: 'auto', branch: 'b'})], ctx);
  expect(paths(r)).toEqual(['auto-new']);
  expect(restPaths(r)).toEqual(['auto-mid', 'auto-old']);
  expect(r.rest.every((i: any) => i.olderAuto === true)).toBe(true);
  expect(r.shown[0].olderAuto).toBeUndefined();
  expect(r.collapsed).toBe(2);
});
test('a folded older automatic note is not pulled up when the shown list has room', () => {
  const r = rankHandoffs([item('auto-new', 1, {source: 'auto', branch: 'b'}), item('auto-old', 2, {source: 'auto', branch: 'b'}), item('manual', 5)], ctx);
  expect(paths(r)).toEqual(['auto-new', 'manual']);
  expect(restPaths(r)).toEqual(['auto-old']);
});
test('automatic notes on different branches or roots do not fold each other', () => {
  const r = rankHandoffs([item('a', 1, {source: 'auto', branch: 'x'}), item('b', 2, {source: 'auto', branch: 'y'}), item('c', 3, {source: 'auto', branch: 'x', root: '/work/app'})], ctx);
  expect(paths(r).sort()).toEqual(['a', 'b', 'c']);
  expect(r.rest).toEqual([]);
});
test('manual handoffs are never folded and do not affect the grouping of automatic notes', () => {
  const r = rankHandoffs([item('manual-new', 1, {branch: 'b'}), item('auto-new', 2, {source: 'auto', branch: 'b'}), item('auto-old', 3, {source: 'auto', branch: 'b'})], ctx);
  expect(paths(r)).toEqual(['manual-new', 'auto-new']);
  expect(restPaths(r)).toEqual(['auto-old']);
});
test('automatic notes with no branch are grouped by root', () => {
  const r = rankHandoffs([item('new', 1, {source: 'auto'}), item('old', 2, {source: 'auto'}), item('elsewhere', 3, {source: 'auto', root: '/another'})], ctx);
  expect(paths(r).sort()).toEqual(['elsewhere', 'new']);
  expect(restPaths(r)).toEqual(['old']);
});
test('automatic notes past 7 days are hidden before grouping, so they never count as folded', () => {
  const r = rankHandoffs([item('new', 1, {source: 'auto', branch: 'b'}), item('week-old', 8, {source: 'auto', branch: 'b'})], ctx);
  expect(paths(r)).toEqual(['new']);
  expect(r.rest).toEqual([]);
  expect(r.collapsed).toBe(0);
  expect(r.hidden).toBe(1);
});
test('folding does not depend on the input order and does not touch the input items', () => {
  const items = [item('a', 1, {source: 'auto', branch: 'b'}), item('b', 2, {source: 'auto', branch: 'b'}), item('c', 2, {source: 'auto', branch: 'b'})];
  const forward = rankHandoffs(items, ctx);
  const backward = rankHandoffs([...items].reverse(), ctx);
  expect(restPaths(forward)).toEqual(restPaths(backward));
  expect(items.every((i: any) => i.olderAuto === undefined)).toBe(true);
});
