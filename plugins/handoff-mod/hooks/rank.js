import {OPEN_STATUSES} from './handoff-file.js';

const DAY = 24 * 3600 * 1000;
const FOLD_AFTER = 14 * DAY;
const AUTO_HIDE_AFTER = 7 * DAY;
const SHOWN = 3;

/**
 * Pick what the start-up list shows. `items` are {path, meta, effectiveStatus, claimedByOther}.
 * Same working tree first, then same repository, then newest; the order never depends on the input order.
 * Returns {shown, collapsed, hidden}: `hidden` counts automatic notes older than 7 days, which are neither shown nor counted in `collapsed`.
 */
export function rankHandoffs(items, {base, repo, now}) {
  const open = items.filter((item) => OPEN_STATUSES.includes(item.effectiveStatus));
  const live = open.filter((item) => !(item.meta.source === 'auto' && now - item.meta.created > AUTO_HIDE_AFTER));
  const hidden = open.length - live.length;
  const score = (item) => (base && item.meta.root === base ? 0 : repo && item.meta.repo === repo ? 1 : 2);
  const sorted = [...live].sort((a, b) => score(a) - score(b) || b.meta.created - a.meta.created || (a.path < b.path ? -1 : a.path > b.path ? 1 : 0));
  const fresh = sorted.filter((item) => now - item.meta.created <= FOLD_AFTER);
  const shown = fresh.slice(0, SHOWN);
  return {shown, collapsed: sorted.length - shown.length, hidden};
}
