import {test, expect} from 'claude-code/testing';
import {resolveConfig} from '../hooks/config.js';

test('defaults apply when nothing is set', () => {
  expect(resolveConfig()).toEqual({thresholdPct: 60, lang: 'zh-TW', autoNote: true});
  expect(resolveConfig({env: {}, userConfig: {}})).toEqual({thresholdPct: 60, lang: 'zh-TW', autoNote: true});
});
test('test-only env overrides win over userConfig, userConfig wins over defaults', () => {
  const userConfig = {thresholdPct: 70, lang: 'en', autoNote: false};
  expect(resolveConfig({userConfig})).toEqual({thresholdPct: 70, lang: 'en', autoNote: false});
  expect(resolveConfig({userConfig, env: {HANDOFF_THRESHOLD_PCT: '10', HANDOFF_LANG: 'zh-TW', HANDOFF_AUTO_NOTE: 'on'}}))
    .toEqual({thresholdPct: 10, lang: 'zh-TW', autoNote: true});
});
test('invalid env values are ignored and fall back', () => {
  for (const bad of ['0', '100', 'abc', '5.5', '', '-3']) {
    expect(resolveConfig({env: {HANDOFF_THRESHOLD_PCT: bad}, userConfig: {thresholdPct: 40}}).thresholdPct).toBe(40);
    expect(resolveConfig({env: {HANDOFF_THRESHOLD_PCT: bad}}).thresholdPct).toBe(60);
  }
  expect(resolveConfig({env: {HANDOFF_LANG: 'fr'}, userConfig: {lang: 'en'}}).lang).toBe('en');
  expect(resolveConfig({env: {HANDOFF_LANG: 'fr'}}).lang).toBe('zh-TW');
});
test('HANDOFF_AUTO_NOTE accepts off and on in any case, anything else defers', () => {
  expect(resolveConfig({env: {HANDOFF_AUTO_NOTE: 'OFF'}}).autoNote).toBe(false);
  expect(resolveConfig({env: {HANDOFF_AUTO_NOTE: 'On'}, userConfig: {autoNote: false}}).autoNote).toBe(true);
  expect(resolveConfig({env: {HANDOFF_AUTO_NOTE: 'maybe'}, userConfig: {autoNote: false}}).autoNote).toBe(false);
  expect(resolveConfig({env: {HANDOFF_AUTO_NOTE: 'maybe'}}).autoNote).toBe(true);
});
test('a userConfig with wrong types never throws and falls back to defaults', () => {
  expect(resolveConfig({userConfig: {thresholdPct: 'high', lang: 5, autoNote: 'yes'}})).toEqual({thresholdPct: 60, lang: 'zh-TW', autoNote: true});
  expect(resolveConfig({userConfig: {thresholdPct: 120}}).thresholdPct).toBe(60);
});
