/** Session-scoped T1 state (kept in $.state, D12). */
export const initialState = () => ({nextAt: 0, askedAt: 0, suppressed: false, askPending: false, handoffStartedAt: 0});

/** The threshold in force: a snoozed value if there is one, else the configured one. */
export const effectiveThreshold = (state, config) => (state.nextAt > 0 ? state.nextAt : config.thresholdPct);

/** Ask only when every condition holds; anything unknown means "do not ask". */
export function decideTrigger({percent, config, state, idle, hasUnfinishedSign, handoffRunning}) {
  const at = effectiveThreshold(state, config);
  if (typeof percent !== 'number' || state.suppressed || state.askPending || handoffRunning) return {action: 'none', at};
  if (!idle || !hasUnfinishedSign || percent < at || state.askedAt >= at) return {action: 'none', at};
  return {action: 'ask', at};
}

export const afterAsk = (state, at) => ({...state, askedAt: at});
export const suppress = (state) => ({...state, suppressed: true});

/** "Ask again in 10%": the next threshold is ten points above where the user is now (or the asked threshold), at most 99. */
export const snooze = (state, {percent, at}) => ({...state, nextAt: Math.min(99, Math.max(percent, at) + 10)});

/** Forget which thresholds were asked about; used on compaction and /clear. Suppression stays. */
export const resetThreshold = (state) => ({...state, nextAt: 0, askedAt: 0});

/** Compaction and /clear make the percentage fall; a value below the last asked threshold restarts the memory. */
export const onPercentSeen = (state, percent) => (typeof percent === 'number' && state.askedAt > 0 && percent < state.askedAt ? resetThreshold(state) : state);

/** Something worth handing off: a file was edited this session, or the working tree is dirty. */
export const hasUnfinishedSign = (signs) => Boolean(signs && (signs.editedFile || signs.gitDirty));
