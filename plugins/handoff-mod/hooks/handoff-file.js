import {stripControl, truncateCodePoints} from './sanitize.js';

const MAX_READ = 64 * 1024;
export const OPEN_STATUSES = ['in-progress', 'blocked', 'ready-for-review'];

/** Section headings, Chinese or English (D11), matched on the start of the heading text. */
const HEADINGS = [
  ['task', /^(任務|task)/i],
  ['done', /^(已完成|done|completed)/i],
  ['todo', /^(未完成|remaining|todo|to-do|not done)/i],
  ['next', /^(下一步|next)/i],
  ['premises', /^(前提|premises|assumptions)/i],
  ['rules', /^(規矩|rules|constraints)/i],
  ['verified', /^(已驗證|verified)/i],
];

const oneLine = (text, max) => truncateCodePoints(stripControl(String(text)).replace(/\s+/g, ' ').trim(), max);
const value = (raw) => {
  const text = String(raw).replace(/\s+#.*$/, '').trim();
  return /^(["']).*\1$/.test(text) ? text.slice(1, -1) : text;
};
const firstLine = (lines = []) => {
  const line = lines.map((l) => l.trim()).find(Boolean);
  return line === undefined ? undefined : line.replace(/^(?:[-*+]\s+|\d+[.)]\s+)?(?:\[[ xX]\]\s*)?/, '');
};

/** Split `---` frontmatter from the body; null when the file has none. */
function split(text) {
  const t = text.replace(/^﻿/, '').replace(/\r\n?/g, '\n');
  if (!t.startsWith('---\n')) return null;
  let from = 3;
  for (;;) {
    const at = t.indexOf('\n---', from);
    if (at === -1) return null;
    const after = t[at + 4];
    if (after === undefined || after === '\n') return {front: t.slice(4, at + 1), body: t.slice(at + 5)};
    from = at + 4;
  }
}

/**
 * Parse a handoff file. Returns {ok:true, meta, fields} or {ok:false, reason}.
 * Everything from the file is a plain string: nothing is executed, and branch/head are validated later, before git sees them.
 */
export function parseHandoff(input) {
  const parts = split(String(input ?? '').slice(0, MAX_READ));
  if (!parts) return {ok: false, reason: 'frontmatter'};
  const fm = {};
  for (const line of parts.front.split('\n')) {
    const m = /^([A-Za-z_][A-Za-z0-9_-]*):[ \t]*(.*)$/.exec(line);
    if (m && !(m[1] in fm)) fm[m[1]] = value(m[2]);
  }
  if (!OPEN_STATUSES.includes(fm.status)) return {ok: false, reason: 'status'};
  const created = Date.parse(fm.created);
  if (!Number.isFinite(created)) return {ok: false, reason: 'created'};
  const text = (v) => (v === undefined || v === '' ? undefined : oneLine(v, 500));

  const sections = {};
  let current = null;
  for (const line of parts.body.split('\n')) {
    if (line.startsWith('## ')) {
      const heading = line.slice(3).trim();
      current = HEADINGS.find(([, pattern]) => pattern.test(heading))?.[0] ?? null;
      if (current && !sections[current]) sections[current] = [];
    } else if (current) sections[current].push(line);
  }
  return {
    ok: true,
    meta: {
      schema: text(fm.schema), root: text(fm.root ?? fm.worktree), repo: text(fm.repo), branch: text(fm.branch),
      head: text(fm.head), created, status: fm.status, source: text(fm.source),
    },
    fields: {task: oneLine(fm.task ?? firstLine(sections.task) ?? '', 80), next: oneLine(firstLine(sections.next) ?? '', 120)},
  };
}
