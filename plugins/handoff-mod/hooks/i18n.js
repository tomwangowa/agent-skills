/** All user-facing strings, in one file (D8, D11). Both languages must define the same keys and placeholders. */
export const STRINGS = {
  'zh-TW': {
    'band.question': 'Context 已用 {percent}%，要先交接嗎？',
    'band.agree': '同意',
    'band.snooze': '再多 {step}% 再問',
    'band.suppress': '這個 session 別再問',
    'status.threshold': 'Context 已用 {percent}%。需要時輸入 /handoff-mod:handoff 交接',
    'ask.clear.question': '要先交接再清除嗎？',
    'ask.clear.cancel': '取消',
    'ask.clear.handoffFirst': '先交接再清除',
    'ask.clear.clearNow': '直接清除',
    'clear.held': '已暫停清除，交接完成後請再下 /clear。',
    'clear.cancelled': '已取消清除。',
    'list.header': '有 {count} 筆未完成交接',
    'list.item': '{n}. {task}（{branch}・{age}）',
    'list.next': '下一步：{next}',
    'list.auto': '自動留下，未經審查',
    'list.more': '還有 {count} 筆',
    'list.claimed': '另一個 session 正在接續',
    'list.resume': '接續',
    'list.skip': '略過',
    'list.none': '目前沒有未完成的交接。',
    'status.pending': '有 {count} 筆未完成交接，輸入 /handoff-resume 查看',
    'resume.prompt': '請先讀 {path}，驗證其中前提是否仍成立，再接續「下一步」。',
    'resume.claimedElsewhere': '這份交接正由另一個 session 接續。',
    'toast.written': '交接已寫入 {path}',
    'toast.invalid': '未偵測到有效交接檔',
    'fresh.branchGone': 'branch {branch} 已不存在',
    'fresh.ahead': '交接後 {branch} 多了 {count} 個 commit',
    'fresh.merged': '交接的 HEAD 已包含在 {base}',
    'fresh.unverifiable': '無法驗證（不在 git 內或缺少資料）',
    'age.minutes': '{n} 分鐘前',
    'age.hours': '{n} 小時前',
    'age.days': '{n} 天前',
    'stats.line': '交接寫入 {written} 次，接續 {resumed} 次',
    'note.task': '## 任務',
    'note.next': '## 下一步',
    'note.nextText': '請先看「最後一個要求」與「最後一段回應」，確認現況再接續。',
    'note.unreviewed': '> 自動留下，未經審查。',
    'note.lastRequest': '## 最後一個要求',
    'note.lastResponse': '## 最後一段回應',
    'note.state': '## 狀態（事實）',
    'note.branchLine': 'branch：{branch}',
    'note.headLine': 'HEAD：{head}',
    'note.changed': '## 有改動的檔案',
  },
  en: {
    'band.question': 'Context is {percent}% full. Write a handoff first?',
    'band.agree': 'Yes',
    'band.snooze': 'Ask again in {step}%',
    'band.suppress': 'Not this session',
    'status.threshold': 'Context is {percent}% full. Run /handoff-mod:handoff to hand off',
    'ask.clear.question': 'Write a handoff before clearing?',
    'ask.clear.cancel': 'Cancel',
    'ask.clear.handoffFirst': 'Hand off, then clear',
    'ask.clear.clearNow': 'Clear now',
    'clear.held': 'Clear is on hold. Run /clear again once the handoff is written.',
    'clear.cancelled': 'Clear cancelled.',
    'list.header': '{count} unfinished handoff(s)',
    'list.item': '{n}. {task} ({branch}, {age})',
    'list.next': 'Next: {next}',
    'list.auto': 'Saved automatically, not reviewed',
    'list.more': '{count} more',
    'list.claimed': 'Another session is resuming this',
    'list.resume': 'Resume',
    'list.skip': 'Skip',
    'list.none': 'No unfinished handoffs.',
    'status.pending': '{count} unfinished handoff(s). Run /handoff-resume to see them',
    'resume.prompt': 'Read {path} first, check that its premises still hold, then continue from "Next".',
    'resume.claimedElsewhere': 'Another session is already resuming this handoff.',
    'toast.written': 'Handoff written to {path}',
    'toast.invalid': 'No valid handoff file was found',
    'fresh.branchGone': 'Branch {branch} no longer exists',
    'fresh.ahead': '{branch} has {count} new commit(s) since the handoff',
    'fresh.merged': 'The handoff HEAD is already in {base}',
    'fresh.unverifiable': 'Cannot verify (not in git, or data missing)',
    'age.minutes': '{n} min ago',
    'age.hours': '{n} h ago',
    'age.days': '{n} d ago',
    'stats.line': 'Handoffs written: {written}, resumed: {resumed}',
    'note.task': '## Task',
    'note.next': '## Next',
    'note.nextText': 'Read "Last request" and "Last response" first, check the current state, then continue.',
    'note.unreviewed': '> Saved automatically; not reviewed.',
    'note.lastRequest': '## Last request',
    'note.lastResponse': '## Last response',
    'note.state': '## State (facts)',
    'note.branchLine': 'Branch: {branch}',
    'note.headLine': 'HEAD: {head}',
    'note.changed': '## Changed files',
  },
};

/** Look up a string and fill its {placeholders}. An unknown language falls back to zh-TW; a missing key or variable throws, so mistakes show up in tests. */
export function t(lang, key, vars = {}) {
  const table = STRINGS[lang] ?? STRINGS['zh-TW'];
  if (!Object.hasOwn(table, key)) throw new Error(`i18n: unknown key ${key}`);
  return table[key].replace(/\{(\w+)\}/g, (_, name) => {
    if (!Object.hasOwn(vars, name)) throw new Error(`i18n: missing variable ${name} for ${key}`);
    return String(vars[name]);
  });
}

/** The three choices of the /clear prompt, in the order shown: the first one is what a stray Enter picks (D13). */
export const clearOptions = (lang) => [t(lang, 'ask.clear.cancel'), t(lang, 'ask.clear.handoffFirst'), t(lang, 'ask.clear.clearNow')];

const isWide = (cp) =>
  (cp >= 0x1100 && cp <= 0x115f) || (cp >= 0x2e80 && cp <= 0xa4cf) || (cp >= 0xac00 && cp <= 0xd7a3) ||
  (cp >= 0xf900 && cp <= 0xfaff) || (cp >= 0xfe30 && cp <= 0xfe4f) || (cp >= 0xff00 && cp <= 0xff60) ||
  (cp >= 0xffe0 && cp <= 0xffe6) || (cp >= 0x1f300 && cp <= 0x1faff) || (cp >= 0x20000 && cp <= 0x3fffd);

/** Terminal columns a string takes: CJK and emoji count as two. */
export function displayWidth(text) {
  let width = 0;
  for (const ch of String(text)) width += isWide(ch.codePointAt(0)) ? 2 : 1;
  return width;
}
