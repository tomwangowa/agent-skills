const DEFAULTS = {thresholdPct: 60, lang: 'zh-TW', autoNote: true};
const LANGS = ['zh-TW', 'en'];

/** A whole percentage from 1 to 99, given as a number or a digit string; anything else is undefined. */
const asPct = (value) => {
  const n = typeof value === 'string' && /^\d+$/.test(value.trim()) ? Number(value) : value;
  return Number.isInteger(n) && n >= 1 && n <= 99 ? n : undefined;
};

/** Resolve settings: test-only env overrides win, then userConfig, then defaults. Never throws. */
export function resolveConfig({env = {}, userConfig = {}} = {}) {
  const lang = LANGS.includes(env.HANDOFF_LANG) ? env.HANDOFF_LANG : LANGS.includes(userConfig.lang) ? userConfig.lang : DEFAULTS.lang;
  const flag = String(env.HANDOFF_AUTO_NOTE ?? '').toLowerCase();
  const autoNote = flag === 'off' ? false : flag === 'on' ? true : typeof userConfig.autoNote === 'boolean' ? userConfig.autoNote : DEFAULTS.autoNote;
  return {thresholdPct: asPct(env.HANDOFF_THRESHOLD_PCT) ?? asPct(userConfig.thresholdPct) ?? DEFAULTS.thresholdPct, lang, autoNote};
}
