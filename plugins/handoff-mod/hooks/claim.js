export const CLAIM_TTL_MS = 12 * 3600 * 1000;

const valid = (entry) => entry && typeof entry === 'object' && typeof entry.sessionId === 'string' && typeof entry.at === 'number';

/** How a stored claim looks to this session: free, mine, other (live) or expired. */
export function claimView(entry, sessionId, now) {
  if (!valid(entry)) return {state: 'free'};
  if (now - entry.at > CLAIM_TTL_MS) return {state: 'expired', holder: entry.sessionId};
  return entry.sessionId === sessionId ? {state: 'mine'} : {state: 'other', holder: entry.sessionId};
}

/**
 * Claim a handoff for this session under every key in `keys` (the new key first, then each copy's old path key, D22).
 * A live claim by another session under any key wins. A get followed by a set is not atomic, so the first key is read
 * back and the winner is whoever is there. If the store fails, resuming is still allowed: `degraded` says the duplicate
 * guard is off.
 */
export async function tryClaim({keys, sessionId, now, store}) {
  try {
    for (const key of keys) {
      const view = claimView(await store.get(key), sessionId, now);
      if (view.state === 'other') return {won: false, holder: view.holder};
    }
    for (const key of keys) await store.set(key, {sessionId, at: now});
    const back = await store.get(keys[0]);
    return valid(back) && back.sessionId === sessionId ? {won: true} : {won: false, holder: valid(back) ? back.sessionId : undefined};
  } catch {
    return {won: true, degraded: true};
  }
}
