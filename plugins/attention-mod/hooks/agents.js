/** Statuses that count as ended; any other status, known or not, is shown as live. */
const ENDED = new Set(['completed', 'failed', 'killed']);

/** Only these two count toward the collapsed number: a pending or idle subagent is listed but not counted. */
const COUNTED = new Set(['running', 'waiting']);

/** How many ended subagents the expanded list keeps. Live ones are never capped. */
export const ENDED_LIMIT = 5;

/**
 * Records when each subagent was first seen ended. agent.list has no end time, so the poll that first sees an
 * ended status stamps it. Ids the list no longer holds are dropped, so the map cannot grow without bound.
 */
export function noteEnded(endedAt, list, now) {
  const next = new Map();
  for (const agent of list) {
    if (!ENDED.has(agent.status)) continue;
    next.set(agent.id, endedAt.has(agent.id) ? endedAt.get(agent.id) : now);
  }
  return next;
}

/**
 * The live rows in list order, then the newest ended rows, up to ENDED_LIMIT. Ties on the stamp fall back to the
 * list's order read backwards, since a later entry usually ended later.
 */
export function summarizeAgents(list, now, endedAt) {
  const row = (agent, live) => ({id: agent.id, type: agent.type, description: agent.description, status: agent.status, live});
  const live = list.filter(agent => !ENDED.has(agent.status)).map(agent => row(agent, true));
  const ended = list
    .map((agent, index) => ({agent, index, at: endedAt.get(agent.id) ?? now}))
    .filter(entry => ENDED.has(entry.agent.status))
    .sort((a, b) => b.at - a.at || b.index - a.index)
    .slice(0, ENDED_LIMIT)
    .map(entry => row(entry.agent, false));
  return {runningCount: list.filter(agent => COUNTED.has(agent.status)).length, rows: [...live, ...ended]};
}

/**
 * The panel's view of one read: null hides the section, {failed} shows the unreadable line, and {list} is summarized.
 */
export function agentsView(read, now, endedAt) {
  if (!read) return null;
  if (read.failed) return {failed: true};
  return summarizeAgents(read.list, now, endedAt);
}
