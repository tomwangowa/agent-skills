const ISSUE_URL = 'https://github.com/tomwangowa/agent-skills/issues/new';
/** Link's href allows 2,048 characters once encoded; keep a margin for what a terminal re-encodes. */
export const ISSUE_URL_LIMIT = 2000;
const TITLE_LIMIT = 60;
const FOOTER = '\n\n---\n由 attention-mod 面板的回饋功能產生；除上述文字外，未附帶任何對話、路徑或工具內容。';
const MARKER = '\n[truncated]';
const KIND_LABEL = {bug: '問題', idea: '建議', other: '回饋'};
const PREFIX = /^(bug|idea|問題|建議)\s*[:：]\s*/i;
// encodeURIComponent throws URIError on an unpaired surrogate (e.g. a pasted half emoji).
const LONE_SURROGATE = /[\uD800-\uDBFF](?![\uDC00-\uDFFF])|(?<![\uD800-\uDBFF])[\uDC00-\uDFFF]/g;

/** Split an optional `bug:`/`idea:` prefix off the typed text; blank input gives null. */
export function parseFeedback(raw) {
  const trimmed = String(raw ?? '').replace(LONE_SURROGATE, '\uFFFD').trim();
  const match = PREFIX.exec(trimmed);
  const text = match ? trimmed.slice(match[0].length).trim() : trimmed;
  if (!text) return null;
  const word = match?.[1].toLowerCase();
  const kind = word === 'bug' || word === '問題' ? 'bug' : word === 'idea' || word === '建議' ? 'idea' : 'other';
  return {kind, text};
}

const cut = (text, limit) => Array.from(text).slice(0, limit).join('');

/**
 * Build a prefilled GitHub new-issue link from what the person typed, and nothing else.
 * The user opens it and confirms on GitHub, so the mod itself sends no request.
 */
export function buildIssueUrl(raw) {
  const parsed = parseFeedback(raw);
  if (!parsed) return null;
  const firstLine = parsed.text.split(/\r?\n/)[0].trim();
  const title = `[attention-mod] ${KIND_LABEL[parsed.kind]}：${cut(firstLine, TITLE_LIMIT)}`;
  const link = body => `${ISSUE_URL}?title=${encodeURIComponent(title)}&body=${encodeURIComponent(body + FOOTER)}`;
  let body = parsed.text;
  let truncated = false;
  if (link(body).length > ISSUE_URL_LIMIT) {
    truncated = true;
    // Shrink by code points so a surrogate pair is never split.
    let points = Array.from(body);
    while (points.length && link(points.join('') + MARKER).length > ISSUE_URL_LIMIT) points = points.slice(0, Math.floor(points.length * 0.9) || 0);
    body = points.join('') + MARKER;
  }
  return {url: link(body), kind: parsed.kind, truncated};
}
