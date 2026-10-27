import {test,expect} from 'claude-code/testing';
import {ENDED_LIMIT,noteEnded,summarizeAgents,agentsView} from '../hooks/agents.js';

const agent=(id,status,extra={})=>({id,type:'Explore',description:`task ${id}`,status,...extra});

test('every live subagent is listed, and only running and waiting are counted', ()=>{
  const list=[agent('a','running'),agent('b','waiting'),agent('c','pending'),agent('d','idle')];
  const view=summarizeAgents(list,0,new Map());
  expect(view.runningCount).toBe(2);
  expect(view.rows.map(r=>[r.id,r.live])).toEqual([['a',true],['b',true],['c',true],['d',true]]);
});

test('live subagents are never capped, however many there are', ()=>{
  const list=[1,2,3,4,5,6,7].map(n=>agent(`r${n}`,'running'));
  const view=summarizeAgents(list,0,new Map());
  expect(view.rows.filter(r=>r.live)).toHaveLength(7);
  expect(view.runningCount).toBe(7);
});

test('an unknown status is listed as live but never counted', ()=>{
  const view=summarizeAgents([agent('x','paused')],0,new Map());
  expect(view.runningCount).toBe(0);
  expect(view.rows).toEqual([{id:'x',type:'Explore',description:'task x',status:'paused',live:true}]);
});

test('ended subagents are capped at the newest five by the time they were first seen ended', ()=>{
  const ended=['e1','e2','e3','e4','e5','e6','e7'];
  // Each poll sees one more subagent end, one second apart.
  let endedAt=new Map();
  ended.forEach((id,i)=>{ endedAt=noteEnded(endedAt,ended.slice(0,i+1).map(p=>agent(p,'completed')),(i+1)*1000); });
  const view=summarizeAgents(ended.map(id=>agent(id,'completed')),9000,endedAt);
  expect(ENDED_LIMIT).toBe(5);
  expect(view.rows.map(r=>r.id)).toEqual(['e7','e6','e5','e4','e3']);
  expect(view.rows.every(r=>r.live===false)).toBe(true);
});

test('the ended order follows when each one was seen ended, not its place in the list', ()=>{
  let endedAt=noteEnded(new Map(),[agent('a','completed'),agent('b','running')],1000);
  endedAt=noteEnded(endedAt,[agent('a','completed'),agent('b','completed')],2000);
  const view=summarizeAgents([agent('a','completed'),agent('b','completed')],3000,endedAt);
  expect(view.rows.map(r=>r.id)).toEqual(['b','a']);
});

test('live rows come before ended rows, and an empty list gives zero', ()=>{
  const view=summarizeAgents([agent('done','completed'),agent('run','running')],0,new Map([['done',0]]));
  expect(view.rows.map(r=>r.id)).toEqual(['run','done']);
  expect(summarizeAgents([],0,new Map())).toEqual({runningCount:0,rows:[]});
});

test('noteEnded keeps the first time an ended subagent was seen and drops ids the list no longer holds', ()=>{
  const first=noteEnded(new Map(),[agent('a','completed'),agent('gone','failed')],1000);
  const second=noteEnded(first,[agent('a','completed')],5000);
  expect(second.get('a')).toBe(1000);
  expect(second.has('gone')).toBe(false);
});

test('noteEnded returns a new map and leaves the one it was given unchanged', ()=>{
  const before=new Map([['a',1000]]);
  const after=noteEnded(before,[agent('a','completed'),agent('b','killed')],2000);
  expect(before.has('b')).toBe(false);
  expect(after.get('b')).toBe(2000);
});

test('agentsView hides on no read, reports a failed read, and summarizes a list', ()=>{
  expect(agentsView(null,0,new Map())).toBeNull();
  expect(agentsView({failed:true},0,new Map())).toEqual({failed:true});
  expect(agentsView({list:[agent('r','running')]},0,new Map()).runningCount).toBe(1);
});
