/** @typedef {{id:string, role:string, phase?:string, text:string, at:number}} Source */
/** @typedef {{id:string, epoch:number, agentId:string|null, tool:string, label:string, startedAt:number, status:string}} Activity */
/** @typedef {{sessionId:string, epoch:number, revision:number, sources:Source[], goalId:string|null, goalContextIds:string[], activities:Activity[], waits:object[], summary:object|null, summaryRevision:number|null, summaryError:string|null, snapshotAt:number|null, turnStatus:string, enabled:boolean, lastTool:object|null, lastEventAt:number|null, waitUnknown:boolean}} State */

/** Bound retained text by Unicode code points, marking omitted content. */
export function boundedText(text, limit = 8000) {
  const points = Array.from(String(text));
  if (points.length <= limit) return points.join('');
  const marker = '\n[truncated]\n';
  const room = Math.max(0, limit - Array.from(marker).length);
  return points.slice(0, Math.ceil(room / 2)).join('') + marker + points.slice(-Math.floor(room / 2)).join('');
}

/** Create an isolated, memory-only session state. @returns {State} */
export function createState(sessionId) {
  return {sessionId, epoch:0, revision:0, sources:[], goalId:null, goalContextIds:[], activities:[], waits:[], summary:null, summaryRevision:null, summaryError:null, snapshotAt:null, turnStatus:'unknown', enabled:true, lastTool:null, lastEventAt:null, waitUnknown:false};
}

/** Apply an observation immutably; activity generations survive a new prompt. */
export function reduceState(state, event) {
  if (event.type === 'session-reset') {
    return {...createState(event.sessionId), epoch:state.epoch + 1, enabled:state.enabled, lastEventAt:event.at};
  }
  if (event.type === 'new-prompt') {
    const goalContextIds = (state.summary?.goal?.sources ?? (state.goalContextIds.length ? state.goalContextIds : state.goalId ? [state.goalId] : [])).slice(0,4);
    const next = {...state, epoch:state.epoch + 1, revision:state.revision, sources:state.sources.map(s=>({...s,phase:'earlier-turn'})), goalId:event.id, goalContextIds, summary:null, summaryRevision:null, summaryError:null, snapshotAt:null, waits:[], waitUnknown:false, turnStatus:'active'};
    return reduceState(next, {type:'source', source:{id:event.id, role:'user', text:event.text, at:event.at}});
  }
  if (event.type === 'source') {
    if (event.epoch !== undefined && event.epoch !== state.epoch) return state;
    const source = {...event.source, phase:event.source.phase ?? 'current-turn', id:boundedText(event.source.id, 160), role:boundedText(event.source.role, 40), text:boundedText(event.source.text)};
    if (!source.text.trim() || state.sources.some(s => s.id === source.id)) return state;
    let sources = [...state.sources, source];
    if (sources.length > 64) {
      const pinned = sources.filter(s => s.id === state.goalId || state.goalContextIds.includes(s.id));
      sources = [...pinned, ...sources.filter(s => !pinned.includes(s)).slice(-(64-pinned.length))];
    }
    return {...state, sources, revision:state.revision + 1, lastEventAt:source.at};
  }
  if (event.type === 'tool-start') {
    if (event.agentId || event.epoch !== state.epoch) return state;
    const activity = {id:event.id, epoch:event.epoch, agentId:null, tool:event.tool, label:boundedText(event.label, 160), startedAt:event.at, status:'running'};
    return {...state, activities:[...state.activities.filter(a => a.id !== event.id), activity], turnStatus:'active', lastEventAt:event.at};
  }
  if (event.type === 'tool-end') {
    const activity = state.activities.find(a => a.id === event.id && a.epoch === event.epoch);
    if (!activity) return state;
    return {...state, activities:state.activities.filter(a => a !== activity), waits:state.waits.filter(w => w.id !== event.id), lastTool:{tool:activity.tool, status:event.status, at:event.at}, lastEventAt:event.at, waitUnknown:false};
  }
  if (event.type === 'wait-start') {
    return {...state, waits:[...state.waits.filter(w => w.id !== event.id), {id:event.id, kind:event.kind, tool:event.tool, at:event.at}], lastEventAt:event.at};
  }
  if (event.type === 'wait-end') return {...state, waits:state.waits.filter(w => w.id !== event.id), lastEventAt:event.at};
  if (event.type === 'wait-unknown') return {...state, waitUnknown:true, lastEventAt:event.at};
  if (event.type === 'turn-start') return {...state, turnStatus:'active', lastEventAt:event.at};
  if (event.type === 'turn-end') return {...state, turnStatus:'ended', waits:[], waitUnknown:false, lastEventAt:event.at};
  return state;
}
