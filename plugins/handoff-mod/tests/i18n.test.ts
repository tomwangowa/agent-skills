import {test, expect} from 'claude-code/testing';
import {t, STRINGS, displayWidth, clearOptions} from '../hooks/i18n.js';

const placeholders = (text: string) => [...text.matchAll(/\{(\w+)\}/g)].map((m) => m[1]).sort();

test('both languages define exactly the same keys', () => {
  expect(Object.keys(STRINGS['zh-TW']).sort()).toEqual(Object.keys(STRINGS.en).sort());
});
test('each key uses the same placeholders in both languages', () => {
  for (const key of Object.keys(STRINGS['zh-TW'])) {
    expect(placeholders(STRINGS['zh-TW'][key])).toEqual(placeholders(STRINGS.en[key]));
  }
});
test('t fills placeholders and leaves none behind', () => {
  expect(t('en', 'band.question', {percent: 62})).toBe('Context is 62% full. Write a handoff first?');
  expect(t('zh-TW', 'band.question', {percent: 62})).toContain('62%');
  for (const lang of ['zh-TW', 'en']) {
    for (const key of Object.keys(STRINGS[lang])) {
      const vars = Object.fromEntries(placeholders(STRINGS[lang][key]).map((name) => [name, 'X']));
      expect(t(lang, key, vars)).not.toContain('{');
    }
  }
});
test('an unknown language falls back to zh-TW; an unknown key or missing variable throws', () => {
  expect(t('fr', 'ask.clear.cancel')).toBe(STRINGS['zh-TW']['ask.clear.cancel']);
  let keyError = false, varError = false;
  try { t('en', 'no.such.key'); } catch { keyError = true; }
  try { t('en', 'band.question', {}); } catch { varError = true; }
  expect(keyError).toBe(true);
  expect(varError).toBe(true);
});
test('displayWidth counts CJK and emoji as two columns', () => {
  expect(displayWidth('abc')).toBe(3);
  expect(displayWidth('同意')).toBe(4);
  expect(displayWidth('a同')).toBe(3);
  expect(displayWidth('😀')).toBe(2);
});
test('the band button row fits in 67 columns in both languages', () => {
  for (const lang of ['zh-TW', 'en']) {
    const row = `1: ${t(lang, 'band.agree')}  2: ${t(lang, 'band.snooze', {step: 10})}  3: ${t(lang, 'band.suppress')}`;
    expect(displayWidth(row) <= 67).toBe(true);
  }
});
test('the clear prompt lists cancel first, then handoff, then clear (D13)', () => {
  for (const lang of ['zh-TW', 'en']) {
    expect(clearOptions(lang)).toEqual([t(lang, 'ask.clear.cancel'), t(lang, 'ask.clear.handoffFirst'), t(lang, 'ask.clear.clearNow')]);
  }
});
