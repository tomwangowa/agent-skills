/*
 * Cleaning for text that came from a file or a conversation before it is shown or stored.
 *
 * redactSecrets covers these shapes, no more. It lowers the risk; it is NOT a guarantee that a secret never survives.
 *   1  private key blocks (terminated, or cut off)      2  Authorization: Bearer/Basic/Token values
 *   3  user:password@ in URLs                            4  JWTs (three dot-separated base64url parts)
 *   5  AWS access key ids (AKIA/ASIA)                    6  GitHub tokens (ghp_/gho_/ghu_/ghs_/ghr_, github_pat_)
 *   7  Slack tokens (xox[baprs]-)                        8  sk- style API keys
 *   9  name=value / name: value where the name contains api key, secret, token, passwd, password, pwd, access key or private key
 * Words about secrets without an assignment ("password policy", "token count") are left alone; an assignment such as
 * "tokens: 1000" is redacted even though it is harmless, which is the safe direction.
 */
const REDACTED = '[redacted]';
const RULES = [
  [/-----BEGIN [A-Z0-9 ]*PRIVATE KEY-----[\s\S]*?-----END [A-Z0-9 ]*PRIVATE KEY-----/g, REDACTED],
  [/-----BEGIN [A-Z0-9 ]*PRIVATE KEY-----[\s\S]*$/g, REDACTED],
  [/(\bAuthorization\s*:\s*(?:Bearer|Basic|Token)\s+)[^\s'"]+/gi, `$1${REDACTED}`],
  [/(\b[a-z][a-z0-9+.-]*:\/\/)[^\s/:@]+:[^\s/@]+@/gi, `$1${REDACTED}@`],
  [/\beyJ[A-Za-z0-9_-]{5,}\.[A-Za-z0-9_-]{5,}\.[A-Za-z0-9_-]{5,}\b/g, REDACTED],
  [/\b(?:AKIA|ASIA)[0-9A-Z]{16}\b/g, REDACTED],
  [/\bgh[pousr]_[A-Za-z0-9]{30,}\b/g, REDACTED],
  [/\bgithub_pat_[A-Za-z0-9_]{20,}\b/g, REDACTED],
  [/\bxox[baprs]-[A-Za-z0-9-]{10,}\b/g, REDACTED],
  [/\bsk-[A-Za-z0-9_-]{20,}\b/g, REDACTED],
  [/([A-Za-z0-9_-]*(?:api[_-]?key|secret|token|passwd|password|pwd|access[_-]?key|private[_-]?key)[A-Za-z0-9_-]*\s*[:=]\s*)(?:"[^"]*"|'[^']*'|[^\s,;]+)/gi, `$1${REDACTED}`],
];

/** Remove terminal escapes and control characters; keep newlines, tabs, CJK and emoji. CRLF becomes LF. */
export function stripControl(text) {
  return String(text)
    .replace(/\r\n?/g, '\n')
    .replace(/\x1b\][^\x07\x1b]*(?:\x07|\x1b\\)?/g, '')
    .replace(/\x1b\[[0-?]*[ -/]*[@-~]/g, '')
    .replace(/\x1b[@-Z\\-_]/g, '')
    .replace(/[\x00-\x08\x0b\x0c\x0e-\x1f\x7f-\x9f]/g, '');
}

/** Cut to at most `max` Unicode code points, ending with an ellipsis when something was removed. */
export function truncateCodePoints(text, max) {
  const value = String(text);
  const points = [...value];
  return points.length <= max ? value : `${points.slice(0, Math.max(0, max - 1)).join('')}…`;
}

export function redactSecrets(text) {
  let out = String(text);
  for (const [pattern, replacement] of RULES) out = out.replace(pattern, replacement);
  return out;
}

/** The pipeline for quoted text. The order matters: redact before truncating, so a cut can never leave half a secret. */
export const cleanForNote = (text, max) => truncateCodePoints(redactSecrets(stripControl(text)), max);
