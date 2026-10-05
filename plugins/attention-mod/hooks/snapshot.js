import {boundedText} from './state.js';

/** @typedef {{sessionId:string, epoch:number, revision:number, capturedAt:number, prompt:string, sourceIds:string[], sourceRoles:Object<string,string>}} Snapshot */

/** Build a source-labelled input bounded after JSON escaping. @returns {Snapshot|null} */
export function buildSnapshot(state, messages = [], now = 0) {
  const all = [...state.sources];
  for (const source of messages) if (!all.some(s => s.id === source.id)) all.push(source);
  const usable = all.filter(s => s.text?.trim());
  if (!usable.length) return null;
  const goal = usable.find(s => s.id === state.goalId);
  // Bound metadata as well as source text; serialized escaping counts in the cap.
  const priorUsers = usable.filter(s=>s !== goal && s.role === 'user').slice(-3).reverse();
  const goalContext = usable.filter(s=>state.goalContextIds.includes(s.id));
  const priority = [...(goal ? [goal] : []), ...goalContext, ...priorUsers];
  const ordered = [...new Set([...priority, ...usable.filter(s => !priority.includes(s)).reverse()])];
  const selected = ordered.slice(0, 8);
  let limit = 2000;
  let payload;
  let prompt;
  do {
    payload = {responseFormat:'Return only a raw JSON object. No Markdown, no ```json code fence. Start with { and end with }.', kind:'untrusted-source-data', goalSource:goal?.id ?? null, omittedSources:usable.length - selected.length, sources:selected.map(s => ({id:boundedText(s.id,160), role:boundedText(s.role,40), phase:s.phase ?? 'current-turn', at:s.at, text:boundedText(s.text,limit)}))};
    prompt = JSON.stringify(payload);
    limit = Math.max(64, Math.floor(limit * 0.75));
    if (Array.from(prompt).length > 8000 && limit === 64 && selected.length > 1) selected.pop();
  } while (Array.from(prompt).length > 8000);
  return {sessionId:state.sessionId, epoch:state.epoch, revision:state.revision, capturedAt:now, prompt, sourceIds:payload.sources.map(s => s.id), sourceRoles:Object.fromEntries(payload.sources.map(s=>[s.id,s.role]))};
}
