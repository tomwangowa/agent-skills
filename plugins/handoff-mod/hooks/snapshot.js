/*
 * D23: an end-of-session note is written only when this session changed the working tree. The first request records
 * what was already dirty (code, path, mtime); the end compares against it.
 */

export const BASELINE_MAX = 50;

const isDeletion = (code) => code.includes('D');
const idOf = (entry) => `${entry.code}\u0000${entry.path}`;

/**
 * Parse `git status --porcelain -z`: NUL-separated `XY path` entries, paths relative to the repository root and never
 * quoted. A rename or copy is followed by its old path as one more field, which is skipped.
 */
export function parseStatusZ(stdout) {
  const fields = String(stdout ?? '').split('\0');
  const entries = [];
  for (let i = 0; i < fields.length; i++) {
    const field = fields[i];
    if (field.length < 4) continue;
    const code = field.slice(0, 2);
    entries.push({code, path: field.slice(3)});
    if (/[RC]/.test(code)) i++;
  }
  return entries;
}

/** `statted` are {code, path, mtimeMs} (a deletion has null); `total` is how many entries git listed. */
export function takeBaseline(statted, total) {
  return {
    entries: statted.slice(0, BASELINE_MAX).map(({code, path, mtimeMs}) => ({code, path, mtimeMs: mtimeMs ?? null})),
    truncated: total > BASELINE_MAX,
  };
}

/** Is any of `current` ({code, path}) missing from the baseline? Needs no stat. */
export function hasNewEntry(baseline, current) {
  const known = new Set(baseline.entries.map(idOf));
  return current.some((entry) => !known.has(idOf(entry)));
}

/**
 * Did the session change anything? Yes for a new code and path, a different mtime, or an unreadable file that is not a
 * deletion. A deletion from before the session that was left alone is null on both sides, which is no change.
 */
export function changedSince(baseline, current) {
  const before = new Map(baseline.entries.map((entry) => [idOf(entry), entry.mtimeMs]));
  for (const entry of current) {
    if (!before.has(idOf(entry))) return true;
    if (entry.mtimeMs === null && !isDeletion(entry.code)) return true;
    if (before.get(idOf(entry)) !== entry.mtimeMs) return true;
  }
  return false;
}
