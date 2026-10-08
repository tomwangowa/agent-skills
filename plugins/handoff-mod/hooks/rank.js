import {OPEN_STATUSES} from './handoff-file.js';

const DAY = 24 * 3600 * 1000;
const FOLD_AFTER = 14 * DAY;
const AUTO_HIDE_AFTER = 7 * DAY;
const SHOWN = 3;

/** Newest first; the path settles a tie so the order never depends on the input order. */
const byNewest = (a, b) => b.meta.created - a.meta.created || (a.path < b.path ? -1 : a.path > b.path ? 1 : 0);
/** Automatic notes of one working tree and branch; with no branch, of one working tree. */
const groupKey = (item) => `${item.meta.root ?? ''}\u0000${item.meta.branch ?? ''}`;

/**
 * Pick what the start-up list shows. `items` are {path, meta, effectiveStatus, claimedByOther}.
 * Same working tree first, then same repository, then newest; the order never depends on the input order.
 * Returns {shown, rest, collapsed, hidden}: `rest` is everything not shown (folded by age, by the limit of three, or because
 * it is an older automatic note on a branch that has a newer one, D15; those carry `olderAuto: true`). `collapsed` is
 * `rest.length`. `hidden` counts automatic notes older than 7 days, which are neither shown nor in `rest`.
 */
export function rankHandoffs(items, {base, repo, now}) {
  const open = items.filter((item) => OPEN_STATUSES.includes(item.effectiveStatus));
  const live = open.filter((item) => !(item.meta.source === 'auto' && now - item.meta.created > AUTO_HIDE_AFTER));
  const hidden = open.length - live.length;
  const newestAuto = new Map();
  for (const item of live) {
    if (item.meta.source !== 'auto') continue;
    const best = newestAuto.get(groupKey(item));
    if (!best || byNewest(item, best) < 0) newestAuto.set(groupKey(item), item);
  }
  const flagged = live.map((item) => (item.meta.source === 'auto' && newestAuto.get(groupKey(item)) !== item ? {...item, olderAuto: true} : item));
  const score = (item) => (base && item.meta.root === base ? 0 : repo && item.meta.repo === repo ? 1 : 2);
  const sorted = flagged.sort((a, b) => score(a) - score(b) || byNewest(a, b));
  const shown = sorted.filter((item) => !item.olderAuto && now - item.meta.created <= FOLD_AFTER).slice(0, SHOWN);
  const rest = sorted.filter((item) => !shown.includes(item));
  return {shown, rest, collapsed: rest.length, hidden};
}
