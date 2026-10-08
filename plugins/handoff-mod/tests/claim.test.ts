import {test, expect} from 'claude-code/testing';
import {tryClaim, claimView, CLAIM_TTL_MS} from '../hooks/claim.js';

function fakeStore(initial: Record<string, any> = {}, o: {afterSet?: (data: Map<string, any>) => void; throws?: boolean} = {}) {
  const data = new Map(Object.entries(initial));
  return {
    data,
    get: async (key: string) => { if (o.throws) throw new Error('store down'); return data.get(key); },
    set: async (key: string, value: any) => { if (o.throws) throw new Error('store down'); data.set(key, value); o.afterSet?.(data); },
  };
}
const now = 1_000_000_000_000;

test('a free handoff is claimed', async () => {
  const store = fakeStore();
  expect(await tryClaim({id: 'h1', sessionId: 'A', now, store})).toMatchObject({won: true});
  expect(store.data.get('claim:h1')).toEqual({sessionId: 'A', at: now});
});
test('a live claim by another session is respected and left untouched', async () => {
  const store = fakeStore({'claim:h1': {sessionId: 'B', at: now - 1000}});
  const r: any = await tryClaim({id: 'h1', sessionId: 'A', now, store});
  expect(r.won).toBe(false);
  expect(r.holder).toBe('B');
  expect(store.data.get('claim:h1')).toEqual({sessionId: 'B', at: now - 1000});
});
test('a claim older than 12 hours is taken over', async () => {
  const store = fakeStore({'claim:h1': {sessionId: 'B', at: now - CLAIM_TTL_MS - 1}});
  expect(((await tryClaim({id: 'h1', sessionId: 'A', now, store})) as any).won).toBe(true);
  expect(store.data.get('claim:h1').sessionId).toBe('A');
});
test('losing a race is detected by reading back', async () => {
  const store = fakeStore({}, {afterSet: (data) => data.set('claim:h1', {sessionId: 'B', at: now})});
  expect(((await tryClaim({id: 'h1', sessionId: 'A', now, store})) as any).won).toBe(false);
});
test('claiming again from the same session is idempotent', async () => {
  const store = fakeStore({'claim:h1': {sessionId: 'A', at: now - 5000}});
  expect(((await tryClaim({id: 'h1', sessionId: 'A', now, store})) as any).won).toBe(true);
});
test('a failing store degrades instead of blocking the resume', async () => {
  const r: any = await tryClaim({id: 'h1', sessionId: 'A', now, store: fakeStore({}, {throws: true})});
  expect(r).toMatchObject({won: true, degraded: true});
});
test('claimView tells free, mine, other and expired apart', () => {
  expect(claimView(undefined, 'A', now).state).toBe('free');
  expect(claimView({sessionId: 'A', at: now}, 'A', now).state).toBe('mine');
  expect(claimView({sessionId: 'B', at: now}, 'A', now).state).toBe('other');
  expect(claimView({sessionId: 'B', at: now - CLAIM_TTL_MS - 1}, 'A', now).state).toBe('expired');
  expect(claimView('garbage', 'A', now).state).toBe('free');
});
