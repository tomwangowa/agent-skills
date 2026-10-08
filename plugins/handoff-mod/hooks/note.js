import {cleanForNote} from './sanitize.js';
import {t} from './i18n.js';

const QUOTE_MAX = 2000;
const FILES_MAX = 50;

/** The end-of-session note is written only for an interactive session that did something and is not being cleared (T2 handles /clear). */
export const shouldWriteNote = ({interactive, turns, hasUnfinishedSign, reason, config}) =>
  Boolean(interactive && turns > 0 && hasUnfinishedSign && reason !== 'clear' && config?.autoNote);

const pad = (n) => String(n).padStart(2, '0');
const stamp = (ms) => {
  const d = new Date(ms);
  return `${d.getFullYear()}${pad(d.getMonth() + 1)}${pad(d.getDate())}-${pad(d.getHours())}${pad(d.getMinutes())}${pad(d.getSeconds())}`;
};
const safeBranch = (branch) => String(branch ?? '').replace(/[^A-Za-z0-9._-]+/g, '-').replace(/^-+|-+$/g, '') || 'no-branch';
const single = (text, max) => cleanForNote(text, max).replace(/\s+/g, ' ').trim();
/** Quote each line, so a "## heading" inside quoted text can never become a section of the note. */
const quote = (text) => text.split('\n').map((line) => `> ${line}`).join('\n');

/** Build the facts-only note: the last request, the last response, git state and changed files. No tool output, nothing earlier. */
export function buildEndNote({lastRequest, lastResponse, branch, head, dirtyFiles = [], root, repo, now, lang}) {
  const request = cleanForNote(lastRequest ?? '', QUOTE_MAX);
  const response = cleanForNote(lastResponse ?? '', QUOTE_MAX);
  const task = single(request.split('\n').find((line) => line.trim()) ?? '', 80);
  const front = ['schema: 1', `root: ${single(root ?? '', 300)}`];
  if (repo) front.push(`repo: ${single(repo, 300)}`);
  if (branch) front.push(`branch: ${single(branch, 200)}`);
  if (head) front.push(`head: ${single(head, 64)}`);
  front.push(`created: ${new Date(now).toISOString()}`, `task: ${task}`, 'status: in-progress', 'source: auto');

  const state = [];
  if (branch) state.push(`- ${t(lang, 'note.branchLine', {branch: single(branch, 200)})}`);
  if (head) state.push(`- ${t(lang, 'note.headLine', {head: single(head, 64)})}`);
  const files = dirtyFiles.slice(0, FILES_MAX).map((file) => `- ${single(file, 200)}`);

  const body = [
    t(lang, 'note.task'), task, '',
    t(lang, 'note.next'), t(lang, 'note.nextText'), '',
    t(lang, 'note.unreviewed'), '',
    t(lang, 'note.lastRequest'), quote(request), '',
    t(lang, 'note.lastResponse'), quote(response), '',
    ...(state.length ? [t(lang, 'note.state'), ...state, ''] : []),
    ...(files.length ? [t(lang, 'note.changed'), ...files, ''] : []),
  ];
  return {fileName: `${safeBranch(branch)}--${stamp(now)}--auto.md`, content: `---\n${front.join('\n')}\n---\n\n${body.join('\n')}`};
}

/**
 * Run `run()` but give up after `ms`. `after(ms, cb)` is $.clock.after, injected because a hooks module has no timers of its own.
 * Resolves to {value}, {timedOut: true} or {error}; the caller must write nothing when it timed out.
 */
export function withDeadline(run, ms, after) {
  return new Promise((resolve) => {
    let settled = false;
    const finish = (result, timer) => {
      if (settled) return;
      settled = true;
      timer?.cancel?.();
      resolve(result);
    };
    const timer = after(ms, () => finish({timedOut: true}));
    run().then((value) => finish({value}, timer), (error) => finish({error}, timer));
  });
}
