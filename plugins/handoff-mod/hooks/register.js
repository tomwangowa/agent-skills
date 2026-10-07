import {atom, read, update} from 'claude-code';
import {resolveConfig} from './config.js';
import {t, clearOptions} from './i18n.js';
import {parseHandoff} from './handoff-file.js';
import {rankHandoffs} from './rank.js';
import {freshnessFacts} from './freshness.js';
import {tryClaim, claimView} from './claim.js';
import {ensureExcluded} from './exclude.js';
import {decideTrigger, effectiveThreshold, snooze, onPercentSeen, hasUnfinishedSign} from './trigger.js';

/*
 * Wiring for the handoff mod. Every pure decision lives in its own module; this file only connects events to them.
 * Invariants (see docs/superpowers/plans/2026-10-07-handoff-mod.md): never touch a tool call, a permission decision or
 * Claude's prompt; every hook body is wrapped in try/catch; session-scoped state lives in $.state, not in module variables,
 * because changing any setting reloads the module; list output goes through $.ui.log, which Claude does not read.
 */

const SKILL = 'handoff-mod:handoff';
const SKILL_COMMAND = new RegExp(`^/${SKILL}(\\s|$)`);
const DIR = '.claude/handoffs';
const PATTERN = `${DIR}/`;
const MAX_DIRS = 20;
const MAX_PER_DIR = 30;
const GIVE_UP_TURNS = 10;
const WARN_AT_TURN = 4;
const GIVE_UP_MS = 60 * 60 * 1000;

// Session-scoped state, kept in $.state: it survives a module reload and is reset by /clear, /resume and /branch.
const handoffStartedAt = atom({plugin: 'handoff-mod', key: 'handoffStartedAt'}, 0);
const handoffTurns = atom({plugin: 'handoff-mod', key: 'handoffTurns'}, 0);
const listDone = atom({plugin: 'handoff-mod', key: 'listDone'}, false);
const askPending = atom({plugin: 'handoff-mod', key: 'askPending'}, false);
// T1 (D12): the next threshold after "ask again in 10%", the threshold last asked about, "never ask again", and the
// percentage the open prompt reports (0 while no prompt is open).
const nextAt = atom({plugin: 'handoff-mod', key: 'nextAt'}, 0);
const askedAt = atom({plugin: 'handoff-mod', key: 'askedAt'}, 0);
const suppressed = atom({plugin: 'handoff-mod', key: 'suppressed'}, false);
const t1Percent = atom({plugin: 'handoff-mod', key: 't1Percent'}, 0);

// Rebuilt from userConfig and disk whenever the module (re)loads or a session starts.
let USER_CONFIG = {};
let config = resolveConfig({});
let list = null; // {items, total} while the start-up list is showing
let listing = false;
let debugOn = false; // HANDOFF_DEBUG=1: trace the post-write detection through $.ui.log (Claude does not read it)

/** Run git without a shell; resolves to {exitCode, stdout} and never throws. */
async function git($, args) {
  try {
    const result = await $.process.run(['git', ...args], {timeoutMs: 5000});
    return {exitCode: result.exitCode, stdout: String(result.stdout ?? '')};
  } catch {
    return {exitCode: -1, stdout: ''};
  }
}

/** One diagnostic line, only when HANDOFF_DEBUG is set. Never throws. */
function trace($, text) {
  if (!debugOn) return;
  try { $.ui.log(`[handoff-mod debug] ${text}`); } catch { /* ignore */ }
}

/** Test-only env overrides (literal names, so validate can list them), then userConfig, then defaults. */
async function loadConfig($) {
  try {
    const env = {
      HANDOFF_THRESHOLD_PCT: await $.env.get('HANDOFF_THRESHOLD_PCT'),
      HANDOFF_LANG: await $.env.get('HANDOFF_LANG'),
      HANDOFF_AUTO_NOTE: await $.env.get('HANDOFF_AUTO_NOTE'),
    };
    debugOn = ['1', 'on', 'true'].includes(String((await $.env.get('HANDOFF_DEBUG')) ?? '').toLowerCase());
    return resolveConfig({env, userConfig: USER_CONFIG});
  } catch {
    return resolveConfig({userConfig: USER_CONFIG});
  }
}

/** The handoff directory's base: the git toplevel of this working tree, else the session root (D10). */
async function projectBase($) {
  const top = await git($, ['rev-parse', '--show-toplevel']);
  const line = top.exitCode === 0 ? top.stdout.trim() : '';
  return line || (await $.session.root());
}

async function repoRoot($) {
  try {
    return (await $.session.repo())?.root ?? null;
  } catch {
    return null;
  }
}

/** The working tree's own directory, the main checkout's, and every other worktree's (D2); no index, bounded. */
async function candidateDirs($, base, repo) {
  const dirs = [`${base}/${DIR}`];
  if (repo) {
    dirs.push(`${repo}/${DIR}`);
    const trees = await git($, ['worktree', 'list', '--porcelain']);
    if (trees.exitCode === 0) {
      for (const line of trees.stdout.split('\n')) if (line.startsWith('worktree ')) dirs.push(`${line.slice(9).trim()}/${DIR}`);
    }
  }
  return [...new Set(dirs)].slice(0, MAX_DIRS);
}

/** Newest first by the timestamp in the file name, then by name. */
const byStamp = (a, b) => {
  const key = (name) => /--(\d{8}-\d{6})/.exec(name)?.[1] ?? '';
  return key(b).localeCompare(key(a)) || (a < b ? 1 : a > b ? -1 : 0);
};

async function readHandoffs($, dirs) {
  const found = [];
  for (const dir of dirs) {
    try {
      if (!(await $.fs.exists(dir))) continue;
      const names = (await $.fs.list(dir)).filter((entry) => entry.kind === 'file' && entry.name.endsWith('.md')).map((entry) => entry.name).sort(byStamp).slice(0, MAX_PER_DIR);
      for (const name of names) {
        const path = `${dir}/${name}`;
        try {
          const parsed = parseHandoff(await $.fs.read(path));
          if (parsed.ok) found.push({path, meta: parsed.meta, fields: parsed.fields});
        } catch { /* An unreadable file is skipped. */ }
      }
    } catch { /* An unreadable directory counts as no handoffs. */ }
  }
  return found;
}

const age = (lang, ms) => {
  const minutes = Math.max(1, Math.round(ms / 60000));
  if (minutes < 60) return t(lang, 'age.minutes', {n: minutes});
  const hours = Math.round(minutes / 60);
  return hours < 48 ? t(lang, 'age.hours', {n: hours}) : t(lang, 'age.days', {n: Math.round(hours / 24)});
};

const factText = (lang, fact) =>
  fact.kind === 'branchGone' ? t(lang, 'fresh.branchGone', {branch: fact.branch})
    : fact.kind === 'ahead' ? t(lang, 'fresh.ahead', {branch: fact.branch, count: fact.count})
      : fact.kind === 'merged' ? t(lang, 'fresh.merged', {base: fact.base})
        : t(lang, 'fresh.unverifiable');

async function storeGet($, key) {
  try {
    return await $.store.get(key);
  } catch {
    return undefined;
  }
}

/** Collect, rank and describe the unfinished handoffs for this working tree and its repository. */
async function buildList($) {
  const lang = config.lang;
  const sessionId = await $.session.id();
  const now = await $.clock.now();
  const base = await projectBase($);
  const repo = await repoRoot($);
  const found = await readHandoffs($, await candidateDirs($, base, repo));
  const items = [];
  for (const f of found) {
    const override = await storeGet($, `state:${f.path}`);
    items.push({
      path: f.path, meta: f.meta, fields: f.fields,
      effectiveStatus: override && typeof override.status === 'string' ? override.status : f.meta.status,
      claimedByOther: claimView(await storeGet($, `claim:${f.path}`), sessionId, now).state === 'other',
    });
  }
  const ranked = rankHandoffs(items, {base, repo, now});
  const views = [];
  for (const item of ranked.shown) {
    const facts = await freshnessFacts({meta: item.meta, git: (args) => git($, args)});
    views.push({
      id: item.path,
      title: t(lang, 'list.item', {n: views.length + 1, task: item.fields.task || item.path.split('/').pop(), branch: item.meta.branch ?? '-', age: age(lang, now - item.meta.created)}),
      next: item.fields.next ? t(lang, 'list.next', {next: item.fields.next}) : '',
      facts: facts.map((fact) => factText(lang, fact)),
      auto: item.meta.source === 'auto',
      claimed: item.claimedByOther,
    });
  }
  return {items: views, total: ranked.shown.length + ranked.collapsed};
}

/** A plugin has one status line: the start-up list wins, else an open T1 prompt, else nothing. Redraws the band too. */
async function syncStatus($) {
  const open = await read($, t1Percent);
  $.ui.status(list ? t(config.lang, 'status.pending', {count: list.total}) : open > 0 ? t(config.lang, 'status.threshold', {percent: open}) : undefined);
  $.ui.invalidate('ui.render');
}

async function showList($, built) {
  list = built.items.length ? built : null;
  await syncStatus($);
}

async function clearList($) {
  list = null;
  await syncStatus($);
}

async function closeT1($) {
  await update($, t1Percent, () => 0);
  await syncStatus($);
}

const readT1 = async ($) => ({
  nextAt: await read($, nextAt), askedAt: await read($, askedAt), suppressed: await read($, suppressed), askPending: await read($, askPending),
});

/**
 * T1: after a turn, ask once per threshold when the context is filling up and there is unfinished work (D1, design
 * component 2). "Unfinished" is a dirty working tree; every unknown (no percentage, not a git tree) means do not ask.
 */
async function checkThreshold($) {
  const percent = (await $.session.usage())?.context?.percent;
  const state = await readT1($);
  const seen = onPercentSeen(state, percent);
  if (seen !== state) {
    // Compaction or /clear made the percentage fall: forget which thresholds were asked, and take any open prompt down.
    await update($, nextAt, () => seen.nextAt);
    await update($, askedAt, () => seen.askedAt);
    if ((await read($, t1Percent)) > 0) await closeT1($);
  }
  if (typeof percent !== 'number' || percent < effectiveThreshold(seen, config)) return;
  const dirty = await git($, ['status', '--porcelain']);
  const decision = decideTrigger({
    percent, config, state: seen, idle: true,
    hasUnfinishedSign: hasUnfinishedSign({gitDirty: dirty.exitCode === 0 && dirty.stdout.trim() !== ''}),
    handoffRunning: (await read($, handoffStartedAt)) > 0,
  });
  trace($, `threshold: percent=${percent} at=${decision.at} dirty=${dirty.exitCode === 0 && dirty.stdout.trim() !== ''} -> ${decision.action}`);
  if (decision.action !== 'ask') return;
  await update($, askedAt, () => decision.at);
  await update($, t1Percent, () => Math.max(1, percent));
  await syncStatus($);
}

/** The prompt's three answers. Each takes it down; a press on a prompt that is already gone does nothing. */
async function answerT1($, answer) {
  const percent = await read($, t1Percent);
  if (percent <= 0) return;
  if (answer === 'snooze') {
    const next = snooze({}, {percent, at: await read($, askedAt)}).nextAt;
    await update($, nextAt, () => next);
  }
  if (answer === 'suppress') await update($, suppressed, () => true);
  await closeT1($);
  if (answer === 'agree') startHandoffLater($);
}

/** Compute the start-up list once per call; `force` ignores "already dismissed" (used by /handoff-resume). */
async function refreshList($, {force = false} = {}) {
  if (listing) return;
  listing = true;
  try {
    if (!force && (await read($, listDone))) return;
    await showList($, await buildList($));
  } catch {
    /* The list is a convenience; never let it break the session. */
  } finally {
    listing = false;
  }
}

async function bumpStat($, field) {
  try {
    const stats = (await $.store.get('stats')) ?? {};
    await $.store.set('stats', {written: 0, resumed: 0, ...stats, [field]: (Number(stats[field]) || 0) + 1});
  } catch { /* Counts are local and optional. */ }
}

/** Resume one handoff: claim it, remember that, and put a prompt in the input box for the user to send. */
async function resume($, item) {
  const lang = config.lang;
  const now = await $.clock.now();
  const sessionId = await $.session.id();
  const claim = await tryClaim({id: item.id, sessionId, now, store: {get: (key) => $.store.get(key), set: (key, value) => $.store.set(key, value)}});
  if (!claim.won) {
    $.ui.toast(t(lang, 'resume.claimedElsewhere'));
    return;
  }
  try { await $.store.set(`state:${item.id}`, {status: 'resumed', at: now, sessionId}); } catch { /* Resuming still works without the record. */ }
  await bumpStat($, 'resumed');
  await $.prompt.fill({text: t(lang, 'resume.prompt', {path: item.id})});
  await update($, listDone, () => true);
  await clearList($);
}

/** A handoff run starts when the skill is expanded, however it was started (typed, or run by this mod). */
async function markHandoffStarted($) {
  const already = await read($, handoffStartedAt);
  if (already > 0) {
    trace($, `start signal ignored, a run is already pending since ${already}`);
    return;
  }
  const now = Math.max(1, await $.clock.now());
  await update($, handoffStartedAt, () => now);
  await update($, handoffTurns, () => 0);
  trace($, `handoff run started at ${now}`);
  if ((await read($, t1Percent)) > 0) await closeT1($);
}

/** The newest valid handoff file written since `since`, or null. Never trusts that the model wrote one. */
async function findNewHandoff($, since) {
  const dir = `${await projectBase($)}/${DIR}`;
  const exists = await $.fs.exists(dir);
  trace($, `looking in ${dir} (exists=${exists}), since=${since}`);
  if (!exists) return null;
  let newest = null;
  for (const entry of await $.fs.list(dir)) {
    if (entry.kind !== 'file' || !entry.name.endsWith('.md')) {
      trace($, `skip ${entry.name}: kind=${entry.kind}`);
      continue;
    }
    const path = `${dir}/${entry.name}`;
    try {
      const stat = await $.fs.stat(path);
      if (stat.mtimeMs < since - 2000 || (newest && stat.mtimeMs <= newest.mtimeMs)) {
        trace($, `skip ${entry.name}: mtimeMs=${stat.mtimeMs}, older than the run or not newest`);
        continue;
      }
      const parsed = parseHandoff(await $.fs.read(path));
      trace($, `${entry.name}: mtimeMs=${stat.mtimeMs}, valid=${parsed.ok}${parsed.ok ? '' : `, reason=${String(parsed.reason ?? "?")}`}`);
      if (parsed.ok) newest = {path, mtimeMs: stat.mtimeMs};
    } catch (error) {
      trace($, `${entry.name}: ${String(error?.message ?? error)}`); // Skip files that cannot be read.
    }
  }
  return newest;
}

/**
 * After each turn while a handoff is pending: report the file once a valid one exists. The review gate makes a handoff
 * span at least two turns (draft, then confirm), so "no file yet" is only reported after WARN_AT_TURN turns, once.
 */
async function checkHandoff($) {
  const since = await read($, handoffStartedAt);
  if (since <= 0) return;
  const lang = config.lang;
  const turns = (await read($, handoffTurns)) + 1;
  await update($, handoffTurns, () => turns);
  const found = await findNewHandoff($, since);
  trace($, `check after turn ${turns}: ${found ? `found ${found.path}` : 'nothing valid yet'}`);
  if (found) {
    await ensureExcluded({
      git: (args) => git($, args),
      fs: {exists: (path) => $.fs.exists(path), read: (path) => $.fs.read(path), write: (path, text) => $.fs.write(path, text)},
      pattern: PATTERN,
    });
    await bumpStat($, 'written');
    $.ui.toast(t(lang, 'toast.written', {path: found.path}));
    await update($, handoffStartedAt, () => 0);
    return;
  }
  if (turns === WARN_AT_TURN) $.ui.toast(t(lang, 'toast.invalid'));
  if (turns >= GIVE_UP_TURNS || (await $.clock.now()) - since > GIVE_UP_MS) await update($, handoffStartedAt, () => 0);
}

/** Start the handoff skill the way a user would. Must run from a timer: the host refuses it inside a command.run hook. */
function startHandoffLater($) {
  $.clock.after(300, async () => {
    try { await $.command.run({command: SKILL}); } catch { /* The user can still run /handoff-mod:handoff by hand. */ }
  });
}

/**
 * T2: ask what to do with a /clear. The question is the only $.ui.ask this mod makes: it is awaited inside the held command,
 * so it never outlives the command, and a flag keeps a second /clear from stacking another question.
 * Returns 'clear', 'handoff', 'cancel' or 'stale' (the session changed while the question was open).
 */
async function askBeforeClear($) {
  if (await read($, askPending)) return 'cancel';
  const lang = config.lang;
  const options = clearOptions(lang);
  const sessionId = await $.session.id();
  await update($, askPending, () => true);
  let answer = null;
  try {
    answer = await $.ui.ask(t(lang, 'ask.clear.question'), options);
  } catch {
    answer = null; // dismissed (Esc) or nobody to ask: treated as cancel
  } finally {
    await update($, askPending, () => false);
  }
  if ((await $.session.id()) !== sessionId) return 'stale';
  // Anything but an exact label, including text typed under "Other", cancels: never clear on a guess.
  return answer === options[2] ? 'clear' : answer === options[1] ? 'handoff' : 'cancel';
}

/** Register the handoff hooks. */
export function register(on, options) {
  USER_CONFIG = options ?? {};
  config = resolveConfig({userConfig: USER_CONFIG});

  on('session.start', async ($, e, next) => {
    const result = await next(e);
    try {
      config = await loadConfig($);
      await $.command.register({name: 'handoff-resume', description: t(config.lang, 'cmd.resume'), argumentHint: t(config.lang, 'cmd.resume.hint')});
    } catch { /* A taken name or a failed read must not stop the session. */ }
    try {
      // A reload of this module re-fires session.start; only a session with no prompts yet gets the list.
      if (e.isInteractive && (await $.session.turns()) === 0) void refreshList($);
    } catch { /* ignore */ }
    return result;
  });

  on('classic.SessionStart', async ($, e, next) => {
    const result = await next(e);
    if (e.agent_id) return result;
    try {
      // resume, fork and compact keep a conversation that already has its context; only a fresh start or /clear lists handoffs.
      if (!['startup', 'clear'].includes(e.source)) return result;
      if ((await $.session.surfaces()).length === 0 || (await $.session.turns()) > 0) return result;
      config = await loadConfig($);
      // A fresh conversation: $.state is already reset by the host, say so explicitly (design component 2), and redraw.
      await update($, nextAt, () => 0);
      await update($, askedAt, () => 0);
      await update($, t1Percent, () => 0);
      void refreshList($);
    } catch { /* ignore */ }
    return result;
  });

  on('prompt.submit', async ($, e, next) => {
    const result = await next(e);
    try {
      if ('drop' in result) return result;
      const text = result.text ?? e.text ?? '';
      if (text.startsWith('/')) trace($, `prompt.submit origin=${e.origin?.kind ?? '-'} command=${text.trim().split(/\s/)[0]}`);
      // skill.prompt does not fire for a typed plugin skill in every environment, so the command text starts a run too.
      if (SKILL_COMMAND.test(text.trim())) await markHandoffStarted($);
      // The first real prompt ends the start-up list; slash commands such as /handoff-resume do not.
      if (list && ['composer', 'bridge', 'sdk'].includes(e.origin?.kind) && !text.startsWith('/')) {
        await update($, listDone, () => true);
        await clearList($);
      }
    } catch { /* ignore */ }
    return result;
  });

  // Debug only: show which skill names arrive, to see whether the matcher below would have fired.
  on('skill.prompt', async ($, e, next) => {
    trace($, `skill.prompt skill=${String(e.skill)}`);
    return next(e);
  });

  on('skill.prompt', {skill: SKILL}, async ($, e, next) => {
    const result = await next(e);
    try { await markHandoffStarted($); } catch { /* ignore */ }
    return result;
  });

  // A third way to see a run start: the skill is a command, however it was started (typed, or run by this mod).
  on('command.run', {command: SKILL}, async ($, e, next) => {
    const result = await next(e);
    try {
      trace($, `command.run command=${SKILL}`);
      await markHandoffStarted($);
    } catch (error) { trace($, `markHandoffStarted failed: ${String(error?.message ?? error)}`); }
    return result;
  });

  on('turn.complete', async ($, e, next) => {
    const result = await next(e);
    trace($, `turn.complete agentId=${e.agentId ?? '-'} aborted=${Boolean(e.isAborted)}`);
    if (e.agentId || e.isAborted) return result;
    try { await checkHandoff($); } catch (error) { trace($, `checkHandoff failed: ${String(error?.message ?? error)}`); }
    try { await checkThreshold($); } catch (error) { trace($, `checkThreshold failed: ${String(error?.message ?? error)}`); }
    return result;
  });

  on('command.run', {command: 'clear'}, async ($, e, next) => {
    try {
      // Only a person's own /clear in an interactive session that has had prompts (D3); not another plugin's, not headless.
      if (e.origin?.kind === 'plugin') return next(e);
      if ((await $.session.surfaces()).length === 0 || (await $.session.turns()) === 0) return next(e);
    } catch {
      return next(e);
    }
    let choice = 'clear';
    try {
      choice = await askBeforeClear($);
    } catch {
      return next(e); // if asking itself fails, do what the user asked rather than swallow the /clear
    }
    if (choice === 'clear') return next(e);
    if (choice === 'stale') return {};
    if (choice === 'handoff') {
      startHandoffLater($);
      return {text: t(config.lang, 'clear.held')};
    }
    return {text: t(config.lang, 'clear.cancelled')};
  });

  on('command.run', {command: 'handoff-resume'}, async ($, e) => {
    try {
      config = await loadConfig($);
      await refreshList($, {force: true});
      const lang = config.lang;
      const arg = String(e.args ?? '').trim();
      if (!list) {
        $.ui.log(t(lang, 'list.none'));
      } else if (arg === '') {
        $.ui.log(t(lang, 'list.header', {count: list.total}));
        for (const item of list.items) {
          const extra = [item.next, ...item.facts, item.auto ? t(lang, 'list.auto') : '', item.claimed ? t(lang, 'list.claimed') : ''].filter(Boolean);
          $.ui.log(extra.length ? `${item.title} — ${extra.join('；')}` : item.title);
        }
      } else {
        const n = Number(arg);
        const item = Number.isInteger(n) ? list.items[n - 1] : undefined;
        if (item) await resume($, item);
        else $.ui.log(t(lang, 'list.bad', {n: arg}));
      }
    } catch { /* ignore */ }
    return {};
  });

  on('ui.render', {component: 'AbovePrompt'}, async ($, e, next) => {
    const open = await read($, t1Percent);
    if (!list && open <= 0) return next(e);
    const {Box, Text, Button} = $.ui.resolve(e);
    const theirs = await next(e);
    const lang = config.lang;
    const blocks = [theirs];
    if (list) {
      const rows = [];
      list.items.forEach((item, i) => {
        rows.push(Text({bold: true, wrap: 'wrap', children: [item.title]}));
        if (item.next) rows.push(Text({wrap: 'wrap', children: [item.next]}));
        for (const [j, fact] of item.facts.entries()) rows.push(Text({dimColor: true, wrap: 'wrap', children: [fact]}));
        if (item.auto) rows.push(Text({dimColor: true, children: [t(lang, 'list.auto')]}));
        rows.push(item.claimed
          ? Text({dimColor: true, children: [t(lang, 'list.claimed')]})
          : Button({key: `resume-${i}`, label: t(lang, 'list.resume'), plain: true, onPress: () => resume($, item)}));
      });
      blocks.push(
        Text({bold: true, children: [t(lang, 'list.header', {count: list.total})]}),
        ...rows,
        ...(list.total > list.items.length ? [Text({dimColor: true, children: [t(lang, 'list.more', {count: list.total - list.items.length})]})] : []),
        Button({key: 'skip', label: t(lang, 'list.skip'), plain: true, onPress: async () => { await update($, listDone, () => true); await clearList($); }}),
      );
    }
    if (open > 0) {
      // No digit hotkeys: a digit typed at the start of a message in an empty prompt would answer the question.
      blocks.push(
        Text({bold: true, wrap: 'wrap', children: [t(lang, 'band.question', {percent: open})]}),
        Button({key: 't1-agree', label: t(lang, 'band.agree'), plain: true, onPress: () => answerT1($, 'agree')}),
        Button({key: 't1-snooze', label: t(lang, 'band.snooze', {step: 10}), plain: true, onPress: () => answerT1($, 'snooze')}),
        Button({key: 't1-suppress', label: t(lang, 'band.suppress'), plain: true, onPress: () => answerT1($, 'suppress')}),
      );
    }
    return Box({flexDirection: 'column', children: blocks});
  });
}
