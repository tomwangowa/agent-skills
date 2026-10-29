import {test, expect} from 'claude-code/testing';
import {register} from '../hooks/register.js';

// sec-default (2.1.312) skips these doors for attention-mod, and each skip raises a notice in the terminal.
const PASSED_OVER = ['attachment', 'hook-context', 'compaction', 'tool-message', 'note'];

// Records every `on(...)` call made by register, so the registration itself is what the test checks.
const registrationsOf = event => {
  const calls = [];
  register((name, ...rest) => calls.push({name, rest}), {});
  return calls.filter(call => call.name === event);
};

test('session.append is registered for the doors sec-default never passes over, and for both summary doors', () => {
  const [registration] = registrationsOf('session.append');
  expect(registrationsOf('session.append').length).toBe(1);
  // on(name, matcher, hook): with a matcher, the first argument after the name is the matcher.
  const matcher = registration.rest[0];
  expect([...matcher.door].sort()).toEqual(['delivery', 'notice', 'response', 'tool-result']);
});

test('no session.append matcher names a door that sec-default passes over', () => {
  const [registration] = registrationsOf('session.append');
  for (const door of PASSED_OVER) expect(registration.rest[0].door.includes(door)).toBe(false);
});
