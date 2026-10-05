/** Create a process-lifetime request schedule. */
export function createSchedule() { return {lastStartedAt:null, inFlight:null, attempted:null, sequence:0}; }
/** Reserve a source revision if both limits allow it. */
export function claimSnapshot(schedule, snapshot, now) {
  const key = `${snapshot.sessionId}:${snapshot.epoch}:${snapshot.revision}`;
  if (schedule.inFlight || schedule.attempted === key || (schedule.lastStartedAt !== null && now - schedule.lastStartedAt < 60000)) return null;
  const token = {requestId:++schedule.sequence, snapshot};
  schedule.inFlight = token;
  schedule.attempted = key;
  schedule.lastStartedAt = now;
  return token;
}
/** Release only the request that owns the lock. */
export function settleRequest(schedule, token) {
  if (schedule.inFlight === token) schedule.inFlight = null;
}
