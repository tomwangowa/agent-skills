/** Doors whose rows Tom did not type; most reach the main model, notices only reach the screen. */
const DOORS = new Set(['delivery','attachment','hook-context','notice','note','compaction','tool-message']);

/** Engine-generated attachments, each with the reason it is noise. Unlisted names stay visible on purpose. */
export const NOISE = new Map([
  ['total_tokens_reminder', 'token balance reminder on every turn'],
  ['environment', 'working directory and platform snapshot'],
  ['model', 'model identity'],
  ['date', 'current date'],
  ['deferred_tools_delta', 'deferred tool catalog change'],
  ['deferred_tools_record', 'deferred tool schemas'],
  ['agent_listing_delta', 'available agent catalog'],
  ['skill_listing', 'available skill catalog'],
  ['advisor_tool', 'tool availability switch'],
  ['auto_mode', 'permission mode switch'],
  ['prompt_snapshot', 'system prompt snapshot'],
  ['command_permissions', 'tools a command may use'],
  ['remote_session_change', 'remote session and attribution settings'],
  ['instructions', 'CLAUDE.md contents attached at the first prompt of every session'],
  ['session_context', 'fixed session context attached at the first prompt of every session'],
]);

const ORIGINS = {engine:'引擎', model:'模型', 'task-notification':'背景工作', peer:'其他 session', 'peer-send-message':'其他 session', 'scheduled-trigger':'排程'};

/** Code-point budgets: labels name a row, the excerpt says what it carries, so it gets the room. */
export const LABEL_LIMIT = 40;
export const EXCERPT_LIMIT = 120;

/** Clip to a code-point budget with a visible ellipsis. */
export function clip(text, limit) {
  const points = Array.from(String(text));
  return points.length <= limit ? points.join('') : points.slice(0, limit - 1).join('') + '…';
}

/** Name who caused a row; kinds this build does not label are shown raw instead of guessed. */
export function originLabel(origin) {
  const kind = origin?.kind;
  if (typeof kind !== 'string') return '來源不明';
  if (kind === 'hook') return origin.event ? `hook（${origin.event}）` : 'hook';
  if (kind === 'plugin') return origin.event ? `plugin（${origin.event}）` : 'plugin';
  if (kind === 'tool') return `工具 ${origin.tool ?? 'unknown'}`;
  return ORIGINS[kind] ?? kind;
}

/** Short kind label from the door and the attachment name. */
export function kindLabel(door, name) {
  if (door === 'hook-context' || name === 'hook_additional_context') return 'hook 注入';
  if (door === 'attachment') return name ? `附件 ${name}` : '附件';
  return name ?? door;
}

const isText = b => b?.type === 'text' && typeof b.text === 'string' && b.text.trim() !== '';
const isMedia = b => b?.type === 'image' || b?.type === 'document';
const isBlankText = b => b?.type === 'text' && !isText(b);

/** False only when a row is empty: no blocks, or nothing but blank text. Unknown block kinds count as content. */
export function hasContent(content) {
  return Array.isArray(content) && content.length > 0 && !content.every(isBlankText);
}

const TAG_ONLY_LINE = /^<\/?[A-Za-z][\w:-]*>$/;

/** First real line across the text blocks: a wrapper tag on its own line (e.g. <system-reminder>) is skipped in
 * favour of the next non-blank line; if every non-blank line is a tag, the first one is shown rather than nothing.
 * Media-only or textless rows get a marker instead. */
export function excerptOf(content) {
  const blocks = Array.isArray(content) ? content : [];
  let firstNonBlank = null;
  for (const block of blocks) {
    if (!isText(block)) continue;
    for (const line of block.text.split(/\r?\n/)) {
      const trimmed = line.trim();
      if (!trimmed) continue;
      if (firstNonBlank === null) firstNonBlank = trimmed;
      if (!TAG_ONLY_LINE.test(trimmed)) return clip(trimmed, EXCERPT_LIMIT);
    }
  }
  if (firstNonBlank !== null) return clip(firstNonBlank, EXCERPT_LIMIT);
  return blocks.some(isMedia) ? '[圖片]' : '[無文字內容]';
}

/** Classify one kept row; null for Tom's own input, known noise, or a subagent's conversation. */
export function entryFromAppend(e, result) {
  // Only a plugin's own note append can be refused; a denied append never reached the model, so show nothing.
  if (result?.deny !== undefined) return null;
  if (!e || e.agentId || !DOORS.has(e.door)) return null;
  // The stored row is what the model reads, so excerpt it rather than the incoming one.
  const message = result?.message ?? e.message ?? {};
  if (e.door === 'attachment' && NOISE.has(message.name)) return null;
  // Empty rows (e.g. hook runs with no output) give the model nothing to read.
  if (!hasContent(message.content)) return null;
  return {id:String(result?.uuid ?? e.uuid), door:e.door, kind:clip(kindLabel(e.door, message.name), LABEL_LIMIT), origin:clip(originLabel(e.origin), LABEL_LIMIT), excerpt:excerptOf(message.content)};
}
