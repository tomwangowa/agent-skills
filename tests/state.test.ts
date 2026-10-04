import {test, expect} from 'claude-code/testing';
import {createState, reduceState} from '../hooks/state.js';

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
