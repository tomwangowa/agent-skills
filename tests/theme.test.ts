import {test, expect} from 'claude-code/testing';
import {colorFor} from '../hooks/theme.js';

test('each semantic tone maps to a named terminal colour, muted to the terminal default', () => {
  expect(['accent','success','warning','danger','muted','input'].map(colorFor)).toEqual(['blue','green','yellow','red',undefined,'magenta']);
});
test('unknown tones fall back to the terminal default instead of throwing', () => {
  expect(colorFor('sparkly')).toBe(undefined);
  expect(colorFor(undefined)).toBe(undefined);
  expect(colorFor('toString')).toBe(undefined);
});
