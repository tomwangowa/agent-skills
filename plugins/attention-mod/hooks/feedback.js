const TEAMS_CHAT = 'https://teams.microsoft.com/l/chat/0/0';
/** Link's href allows 2,048 characters once encoded; keep a margin for what a terminal re-encodes. */
export const LINK_LIMIT = 2000;
const MARKER = '\n[truncated]';
const KIND_LABEL = {bug: '問題', idea: '建議', other: '回饋'};
const PREFIX = /^(bug|idea|問題|建議)\s*[:：]\s*/i;
// Deliberately loose: Teams resolves the account; this only keeps stray text out of the link.
const EMAIL = /^[^\s@,&?#=]+@[^\s@,&?#=]+\.[^\s@,&?#=]+$/;
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

/** The recipient as configured, or null when it is unset or not an email address. */
export function parseRecipient(value) {
  const email = String(value ?? '').trim();
  return EMAIL.test(email) ? email : null;
}

/**
 * Build a Teams chat deep link that opens a chat with `recipient` and fills the compose box
 * with what the person typed, and nothing else. The person presses Enter in Teams to send, so
 * the mod itself sends no request. `message` is the plain text, for copying when the link fails.
 */
export function buildTeamsLink(raw, recipient) {
  const parsed = parseFeedback(raw);
  const email = parseRecipient(recipient);
  if (!parsed || !email) return null;
  const header = `[attention-mod ${KIND_LABEL[parsed.kind]}]`;
  const compose = text => `${header} ${text}`;
  const link = text => `${TEAMS_CHAT}?users=${encodeURIComponent(email)}&message=${encodeURIComponent(compose(text))}`;
  let body = parsed.text;
  let truncated = false;
  if (link(body).length > LINK_LIMIT) {
    truncated = true;
    // Shrink by code points so a surrogate pair is never split.
    let points = Array.from(body);
    while (points.length && link(points.join('') + MARKER).length > LINK_LIMIT) points = points.slice(0, Math.floor(points.length * 0.9));
    body = points.join('') + MARKER;
  }
  return {url: link(body), kind: parsed.kind, truncated, message: compose(parsed.text)};
}
