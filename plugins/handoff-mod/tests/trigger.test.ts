import {test, expect} from 'claude-code/testing';
import {initialState, effectiveThreshold, decideTrigger, afterAsk, snooze, suppress, resetThreshold, onPercentSeen, hasUnfinishedSign} from '../hooks/trigger.js';

const ready = () => ({percent: 65, config: {thresholdPct: 60}, state: initialState(), idle: true, hasUnfinishedSign: true, handoffRunning: false});
const action = (o: any = {}) => decideTrigger({...ready(), ...o}).action;

test('asks when every condition holds', () => {
  expect(action()).toBe('ask');
  expect(action({percent: 60})).toBe('ask');
});
test('does not ask when any condition fails', () => {
  expect(action({percent: 59})).toBe('none');
  expect(action({percent: undefined})).toBe('none');
  expect(action({hasUnfinishedSign: false})).toBe('none');
  expect(action({idle: false})).toBe('none');
  expect(action({handoffRunning: true})).toBe('none');
  expect(action({state: {...initialState(), suppressed: true}})).toBe('none');
  expect(action({state: {...initialState(), askPending: true}})).toBe('none');
});
test('a threshold that was already asked about is not asked again', () => {
  expect(action({state: {...initialState(), askedAt: 60}})).toBe('none');
  expect(action({state: {...initialState(), askedAt: 50}})).toBe('ask');
});
test('a snoozed threshold replaces the configured one', () => {
  const state = {...initialState(), nextAt: 70, askedAt: 60};
  expect(effectiveThreshold(state, {thresholdPct: 60})).toBe(70);
  expect(action({state, percent: 65})).toBe('none');
  expect(action({state, percent: 70})).toBe('ask');
  expect(effectiveThreshold(initialState(), {thresholdPct: 55})).toBe(55);
});
test('state transitions: ask, snooze by ten points, suppress', () => {
  const asked = afterAsk(initialState(), 60);
  expect(asked.askedAt).toBe(60);
  expect(snooze(asked, {percent: 63, at: 60}).nextAt).toBe(73);
  expect(snooze(asked, {percent: 58, at: 60}).nextAt).toBe(70);
  expect(snooze(asked, {percent: 95, at: 90}).nextAt).toBe(99);
  expect(suppress(asked).suppressed).toBe(true);
});
test('snoozing leads to a second prompt at the new threshold and not before', () => {
  let state = afterAsk(initialState(), 60);
  state = snooze(state, {percent: 63, at: 60});
  expect(action({state, percent: 72})).toBe('none');
  expect(action({state, percent: 73})).toBe('ask');
});
test('resetThreshold clears the threshold memory but keeps suppression', () => {
  const state = {...initialState(), nextAt: 70, askedAt: 60, suppressed: true};
  expect(resetThreshold(state)).toEqual({...initialState(), suppressed: true});
});
test('a percent that falls below the last asked threshold restarts the memory (compaction, /clear)', () => {
  const state = {...initialState(), nextAt: 70, askedAt: 60};
  expect(onPercentSeen(state, 5)).toEqual(initialState());
  expect(onPercentSeen(state, 61)).toEqual(state);
  expect(onPercentSeen(state, undefined)).toEqual(state);
  expect(onPercentSeen(initialState(), 3)).toEqual(initialState());
});
test('unfinished-work signs: an edit or a dirty tree is enough', () => {
  expect(hasUnfinishedSign({editedFile: true})).toBe(true);
  expect(hasUnfinishedSign({gitDirty: true})).toBe(true);
  expect(hasUnfinishedSign({editedFile: false, gitDirty: false})).toBe(false);
  expect(hasUnfinishedSign({})).toBe(false);
  expect(hasUnfinishedSign(undefined)).toBe(false);
});
