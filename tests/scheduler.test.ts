import {test,expect} from 'claude-code/testing';
import {createSchedule,claimSnapshot,settleRequest} from '../hooks/scheduler.js';
const snap=(epoch=0,revision=1)=>({sessionId:'s',epoch,revision,capturedAt:0,prompt:'data',sourceIds:['s1']});
test('new data respects 60000 ms between starts and failures are not retried forever',()=>{
  const schedule=createSchedule();
  const first=claimSnapshot(schedule,snap(),0);
  expect(first).not.toBe(null);
  settleRequest(schedule,first);
  expect(claimSnapshot(schedule,snap(),120000)).toBe(null);
  expect(claimSnapshot(schedule,snap(0,2),59999)).toBe(null);
  expect(claimSnapshot(schedule,snap(0,2),60000)).not.toBe(null);
});
test('old request keeps the lock through resets and wrong tokens cannot release it',()=>{
  const schedule=createSchedule();
  const token=claimSnapshot(schedule,snap(),0);
  expect(token).not.toBe(null);
  expect(claimSnapshot(schedule,snap(1),60000)).toBe(null);
  settleRequest(schedule,{requestId:'wrong'});
  expect(claimSnapshot(schedule,snap(1),120000)).toBe(null);
  settleRequest(schedule,token);
  expect(claimSnapshot(schedule,snap(1),120000)).not.toBe(null);
});
