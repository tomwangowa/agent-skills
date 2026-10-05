import {test, expect} from 'claude-code/testing';
import {createState, reduceState, UNKNOWN_SESSION, BETWEEN_SESSIONS} from '../hooks/state.js';
import {buildSnapshot} from '../hooks/snapshot.js';

const start = (s, id, agentId = null) => reduceState(s, {type:'tool-start', id, tool:'Bash', label:id, agentId, at:10, epoch:s.epoch});
const end = (s, id, epoch = s.epoch) => reduceState(s, {type:'tool-end', id, status:'success', at:20, epoch});

test('parallel tools finish independently without mutating input', () => {
  const s = start(start(createState('one'), 'first'), 'second');
  const result = end(s, 'first');
  expect(result.activities.map(a => a.id)).toEqual(['second']);
  expect(s.activities.length).toBe(2);
});
test('old epoch completion does not remove new activity with reused ID', () => {
  const old = start(createState('one'), 'same');
  const reset = reduceState(old, {type:'session-reset', sessionId:'two', at:20});
  const fresh = start(reset, 'same');
  expect(end(fresh, 'same', old.epoch).activities.length).toBe(1);
});
test('new prompt invalidates summary but preserves live tools and clears obsolete sources', () => {
  const s = {...start(createState('one'), 'first'), summary:{goal:{text:'old',sources:['old']}}, snapshotAt:10};
  const result = reduceState(s, {type:'new-prompt', id:'goal', text:'new task', at:30});
  expect(result.summary).toBe(null);
  expect(result.snapshotAt).toBe(null);
  expect(result.activities.length).toBe(1);
  expect(result.sources.map(x => x.id)).toEqual(['goal']);
});
test('explicit waits are released and child agents do not overwrite main actions', () => {
  const s = start(createState('one'), 'child', 'agent-one');
  expect(s.activities.length).toBe(0);
  const waiting = reduceState(s, {type:'wait-start', id:'question', kind:'question', at:10});
  expect(waiting.waits.length).toBe(1);
  expect(reduceState(waiting, {type:'wait-end', id:'question', at:20}).waits.length).toBe(0);
});
test('sources are bounded and retain the current goal through 1000 observations', () => {
  let s = reduceState(createState('one'), {type:'new-prompt', id:'goal', text:'task', at:0});
  for (let i = 0; i < 1000; i++) s = reduceState(s, {type:'source', source:{id:`s${i}`, role:'tool', text:'😀'.repeat(9000), at:i}});
  expect(s.sources.length <= 64).toBe(true);
  expect(s.sources[0].id).toBe('goal');
  expect(Array.from(s.sources[1].text).length <= 8000).toBe(true);
  expect(s.sources[1].text).toContain('truncated');
});
test('tool outcomes remain distinct and turn completion never means task completion', () => {
  for (const status of ['success', 'error', 'denied', 'cancelled']) {
    const s = start(createState('one'), 'tool');
    const done = reduceState(s, {type:'tool-end', id:'tool', epoch:s.epoch, status, at:20});
    expect(done.lastTool.status).toBe(status);
    expect(reduceState(done, {type:'turn-end', at:30}).turnStatus).toBe('ended');
  }
});

test('another Bash completion cannot release the first Bash permission wait',()=>{
  let s=start(createState('one'),'a');
  s=reduceState(s,{type:'wait-start',id:'a',tool:'Bash',kind:'permission',at:10});
  s=start(s,'b');
  const result=end(s,'b');
  expect(result.waits.map(w=>w.id)).toEqual(['a']);
  expect(end(result,'a').waits.length).toBe(0);
});
test('follow-up prompt retains bounded original sources while invalidating the generated summary',()=>{
  let s=reduceState(createState('s'),{type:'new-prompt',id:'goal',text:'修正登入 token 過期處理',at:0});
  s=reduceState(s,{type:'source',source:{id:'a',role:'assistant',text:'Claude 懷疑 refresh token 處理',at:1}});
  s=reduceState(s,{type:'new-prompt',id:'followup',text:'好，照這個方向繼續',at:2});
  expect(s.sources.some(x=>x.id==='goal')).toBe(true);
  expect(s.sources.some(x=>x.id==='a')).toBe(true);
  expect(s.summary).toBe(null);
  expect(s.goalId).toBe('followup');
});

const input = (s, id, at = 10) => reduceState(s, {type:'external-input', entry:{id, kind:'hook 注入', origin:'引擎', excerpt:id}, sessionId:s.sessionId, epoch:s.epoch, at});

test('external inputs keep the latest five, once per row, across prompts', () => {
  let s = createState('one');
  for (const id of ['a','b','c','d','e','f']) s = input(s, id);
  s = input(s, 'f');
  expect(s.inputs.map(i => i.id)).toEqual(['b','c','d','e','f']);
  const next = reduceState(s, {type:'new-prompt', id:'goal', text:'task', at:20});
  expect(next.inputs.map(i => i.id)).toEqual(['b','c','d','e','f']);
  expect(next.inputs[0].epoch < next.epoch).toBe(true);
});
test('session end clears inputs; the next session keeps rows that arrived in between', () => {
  let s = input(createState('one'), 'old');
  s = reduceState(s, {type:'session-reset', sessionId:BETWEEN_SESSIONS, at:20});
  expect(s.inputs).toEqual([]);
  expect(s.inputsSince).toBe(20);
  s = input({...s, enabled:false}, 'start-hook', 25);
  expect(s.inputs.length).toBe(1);
  s = reduceState(s, {type:'session-reset', sessionId:'two', at:30});
  expect(s.inputs.map(i => i.id)).toEqual(['start-hook']);
  expect(s.inputs[0].epoch).toBe(s.epoch);
  expect(s.inputsSince).toBe(20);
});
test('startup rows survive the first reset, rows of another known session do not', () => {
  const boot = reduceState(input(createState(UNKNOWN_SESSION), 'boot'), {type:'session-reset', sessionId:'two', at:30});
  expect(boot.inputs.map(i => i.id)).toEqual(['boot']);
  const other = reduceState(input(createState('one'), 'from-one'), {type:'session-reset', sessionId:'two', at:30});
  expect(other.inputs).toEqual([]);
  expect(other.inputsSince).toBe(30);
});
test('external inputs never become summary material', () => {
  let s = reduceState(createState('one'), {type:'new-prompt', id:'goal', text:'task', at:0});
  s = input(s, 'INJECTED-MARKER');
  expect(s.sources.map(x => x.id)).toEqual(['goal']);
  expect(s.revision).toBe(1);
  expect(s.inputs.map(i => i.id)).toEqual(['INJECTED-MARKER']);
  expect(buildSnapshot(s, [], 10).prompt).not.toContain('INJECTED-MARKER');
});
test('rows stamped after reconnect rebinds the session id survive the start reset', () => {
  let s = createState('one');
  s = reduceState(s, {type:'session-reset', sessionId:BETWEEN_SESSIONS, at:20});
  s = {...s, sessionId:'two', enabled:true}; // simulates reconnect() rebinding the id without a reset event
  s = input(s, 'hook-row');
  s = reduceState(s, {type:'session-reset', sessionId:'two', at:30});
  expect(s.inputs.map(i => i.id)).toEqual(['hook-row']);
  expect(s.inputs[0].epoch).toBe(s.epoch);
});
test('stale gap rows are not dragged into a later session', () => {
  let s = createState('one');
  s = reduceState(s, {type:'session-reset', sessionId:BETWEEN_SESSIONS, at:20});
  s = input(s, 'gap-row');
  s = {...s, sessionId:'two', enabled:true}; // reconnect() rebinds the id
  s = reduceState(s, {type:'new-prompt', id:'goal', text:'task', at:25}); // bumps epoch past the gap row's epoch
  s = reduceState(s, {type:'session-reset', sessionId:'three', at:30});
  expect(s.inputs).toEqual([]);
});
