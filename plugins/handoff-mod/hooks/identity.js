/*
 * D20 to D22: one handoff is its file name plus its created time, so copies of one file in several working trees (or
 * left behind by a moved folder) are one handoff. State is kept under a key built from that, and, for 0.1.x, under each
 * copy's absolute path as well.
 */

const nameOf = (path) => path.slice(path.lastIndexOf('/') + 1);
const dirOf = (path) => path.slice(0, path.lastIndexOf('/'));

/** D20: `<file name>|<created as ISO>`; `created` is milliseconds, so two spellings of one instant give one key. */
export function handoffKey(name, created) {
  return `${name}|${new Date(created).toISOString()}`;
}

/**
 * Group `found` ({path, meta, fields, closed}) by key. Each item shows one copy: the one in `base`'s handoff folder,
 * else the one in `repo`'s, else the first found. `paths` keeps every copy in scan order; `fileClosed` is true when any
 * copy's own status is closed.
 */
export function mergeCopies(found, {base, repo, dir}) {
  const groups = new Map();
  for (const f of found) {
    const key = handoffKey(nameOf(f.path), f.meta.created);
    if (!groups.has(key)) groups.set(key, []);
    groups.get(key).push(f);
  }
  const rank = (f) => (dirOf(f.path) === `${base}/${dir}` ? 0 : repo && dirOf(f.path) === `${repo}/${dir}` ? 1 : 2);
  return [...groups].map(([key, copies]) => {
    const shown = copies.reduce((best, f) => (rank(f) < rank(best) ? f : best));
    return {key, path: shown.path, paths: copies.map((f) => f.path), meta: shown.meta, fields: shown.fields, fileClosed: copies.some((f) => f.closed)};
  });
}

/** D21, D22: the new key first, then every copy's old `state:<path>`. New keys start with `id:`, old ones with `/`. */
export const stateKeys = (item) => [`state:id:${item.key}`, ...item.paths.map((path) => `state:${path}`)];

/** The same for claims. */
export const claimKeys = (item) => [`claim:id:${item.key}`, ...item.paths.map((path) => `claim:${path}`)];

/** The newest stored record that has a status, or undefined. Anything else in the store is ignored. */
export function newestState(records) {
  let best;
  for (const record of records) {
    if (!record || typeof record !== 'object' || typeof record.status !== 'string') continue;
    if (!best || Number(record.at) > Number(best.at)) best = record;
  }
  return best;
}
