// Throwaway probes for the handoff-mod design (V1-V6 in docs/superpowers/plans/2026-10-06-handoff-mod-poc.md).
// Every probe writes a line to the transcript (dim) and to <TMPDIR>/handoff-poc.log, because /clear wipes the transcript.
// Read-only toward Claude: nothing here changes a tool call, prompt or permission decision.

const LOG_NAME = 'handoff-poc.log';
const COMMANDS = [
  ['poc-usage', 'POC V1: log context usage'],
  ['poc-submit', 'POC V2: submit a skill call (plain | user | fill | cmd | cmd:<name>)'],
  ['poc-band', 'POC V4: show the band with hotkeys 1/2/3'],
  ['poc-ask', 'POC V4: $.ui.ask with three options'],
  ['poc-ask-timer', 'POC V4: $.ui.ask from a timer, 3 s later'],
  ['poc-pane-timer', 'POC V5: open a pane from a timer, 2 s later'],
  ['poc-facts', 'POC V6: log session root/cwd/repo and git facts'],
  ['poc-block-clear', 'POC V3: toggle answering /clear in its place (no next), to test cancelling it'],
  ['poc-store', 'POC: write a $.store key (then inspect the file permissions from a shell)'],
  ['poc-config', 'POC: show userConfig options, /config rows and pluginConfigs'],
  ['poc-config-set', 'POC: $.config.set <field> <value>, then re-read'],
  ['poc-fill-hook', 'POC: call $.prompt.fill directly inside a command.run hook'],
  ['poc-text', 'POC: command returns {text} with a marker'],
  ['poc-log', 'POC: command prints a marker with $.ui.log'],
  ['poc-context', 'POC: command returns {text, context} with a marker in context'],
  ['poc-t2', 'POC: toggle the T2 flow (ask before /clear)'],
  ['poc-status', 'POC D9: $.ui.status <text> (no text clears)'],
  ['poc-toast', 'POC D9: $.ui.toast'],
];

let band = null; // {last} while the band probe is showing
let blockClear = false;
let t2 = false;
let USER_CONFIG = {}; // userConfig values as register(on, options) received them at load
const LOAD_ID = Math.random().toString(36).slice(2, 8); // changes when the module reloads

async function logPath($) {
  const dir = await safe(() => $.env.get('TMPDIR'));
  const base = typeof dir === 'string' && !dir.startsWith('ERR ') && dir ? dir : '/tmp';
  return `${base.replace(/\/$/, '')}/${LOG_NAME}`;
}

/** Append a timestamped line to the transcript and the log file. Never throws. */
async function note($, text) {
  try { $.ui.log(`poc: ${text}`); } catch { /* the transcript line is a convenience */ }
  text = `[load ${LOAD_ID}] ${text}`;
  try {
    const path = await logPath($);
    const stamp = new Date(await $.clock.now()).toISOString();
    const exists = await $.fs.exists(path);
    const old = exists ? await $.fs.read(path) : '';
    const text0 = typeof old === 'string' ? old : (old?.text ?? '');
    await $.fs.write(path, `${text0}${stamp} ${text}\n`);
  } catch { /* file logging is best effort */ }
}

/** Run a probe call and return its value, or an 'ERR ...' string, so one failing API never hides the others. */
async function safe(fn) {
  try { return await fn(); } catch (error) { return `ERR ${error?.message ?? error}`; }
}

const short = (value, max = 240) => {
  const text = typeof value === 'string' ? value : (JSON.stringify(value) ?? String(value));
  return text.length > max ? `${text.slice(0, max)}…` : text;
};

const OPTIONS = ['同意', '再多 10% 再問', '這個 session 別再問'];

export function register(on, options) {
  USER_CONFIG = options ?? {};
  // V6 + registration: what a fresh session reports about itself.
  on('session.start', async ($, e, next) => {
    const result = await next(e);
    try {
      for (const [name, description] of COMMANDS) {
        await safe(() => $.command.register({name, description, immediate:true}));
      }
      await note($, `session.start interactive=${e.isInteractive} id=${short(await safe(() => $.session.id()))}`);
    } catch { /* probes must not block the session */ }
    return result;
  });
  on('classic.SessionStart', async ($, e, next) => {
    const result = await next(e);
    if (!e.agent_id) await note($, `classic.SessionStart source=${e.source} session=${e.session_id}`);
    return result;
  });
  on('session.end', async ($, e, next) => {
    // Measures how long a session.end hook gets to do real work (budget is ~1.5 s for all hooks together).
    const t0 = await $.clock.now();
    await note($, `session.end reason=${e.reason} session=${e.sessionId}`);
    const spent = (await $.clock.now()) - t0;
    await note($, `session.end note took ${spent} ms`);
    return next(e);
  });

  on('command.run', {command:'poc-facts'}, async ($) => {
    const git = async (...args) => { const r = await safe(() => $.process.run(['git', ...args])); return typeof r === 'string' ? r : `${r.exitCode}:${(r.stdout || r.stderr).trim()}`; };
    await note($, `facts cwd=${short(await safe(() => $.session.cwd()))} root=${short(await safe(() => $.session.root()))} repo=${short(await safe(() => $.session.repo()))} surfaces=${short(await safe(() => $.session.surfaces()))} messages=${short((await safe(() => $.session.messages()))?.length)}`);
    await note($, `git toplevel=${await git('rev-parse', '--show-toplevel')} commonDir=${await git('rev-parse', '--git-common-dir')} head=${await git('rev-parse', 'HEAD')} branch=${await git('branch', '--show-current')}`);
    // Do skills (ours and the user's own /handoff) show up in the command list, and with which source? That decides how a mod detects them.
    const commands = await safe(() => $.command.list());
    const like = Array.isArray(commands) ? commands.filter(c => /handoff|poc/.test(c.name)).map(c => `${c.name}[${c.source}${c.plugin ? `:${c.plugin}` : ''}]`) : commands;
    await note($, `commands n=${Array.isArray(commands) ? commands.length : commands} handoff-like=${short(like)}`);
    return {};
  });

  // V1: is context.percent used or remaining, and what window does this model report?
  on('command.run', {command:'poc-usage'}, async ($) => {
    await note($, `usage ${short(await safe(() => $.session.usage()), 600)}`);
    return {};
  });
  on('turn.complete', async ($, e, next) => {
    const result = await next(e);
    if (!e.agentId) {
      const usage = await safe(() => $.session.usage());
      await note($, `turn.complete turnUsage=${short(e.usage)} context=${short(usage?.context)}`);
    }
    return result;
  });
  on('session.measure', async ($, e, next) => {
    await note($, `session.measure ${short(e)}`);
    return next(e);
  });

  // V2: can a mod start a skill? Plugin skills are namespaced, so the text is /<plugin>:<skill>.
  on('command.run', {command:'poc-submit'}, async ($, e) => {
    // The host refuses prompt.submit and command.run from inside a command.run hook (it would wait on its own turn),
    // so each mode runs from a timer, which fires outside any event.
    const mode = (e.args || 'plain').trim();
    const text = '/handoff-poc:poc-skill';
    $.clock.after(500, async () => {
      if (mode === 'plain') await $.prompt.submit({text}).then(r => note($, `submit plain resolved ${short(r)}`), error => note($, `submit plain rejected ${error?.message}`));
      else if (mode === 'user') await $.prompt.submit({text, asUser:true}).then(r => note($, `submit user resolved ${short(r)}`), error => note($, `submit user rejected ${error?.message}`));
      else if (mode === 'fill') await note($, `fill ${short(await safe(() => $.prompt.fill({text})))}`);
      else if (mode === 'cmd') await note($, `command.run ${short(await safe(() => $.command.run({command:'handoff-poc:poc-skill'})))}`);
      // cmd:<name> runs any command or skill by name, e.g. /poc-submit cmd:handoff to try the user's own /handoff skill.
      else if (mode.startsWith('cmd:')) await note($, `command.run ${mode.slice(4)} ${short(await safe(() => $.command.run({command:mode.slice(4)})), 300)}`);
      else await note($, `unknown mode ${mode}; use plain | user | fill | cmd | cmd:<name>`);
    });
    return {};
  });
  on('skill.prompt', async ($, e, next) => {
    await note($, `skill.prompt fired ${short(e, 160)}`);
    return next(e);
  });
  on('prompt.submit', async ($, e, next) => {
    if (e.text.startsWith('/')) await note($, `prompt.submit origin=${e.origin?.kind} text=${short(e.text, 60)}`);
    return next(e);
  });

  // V3: do built-in commands reach command.run, and what do compaction and /exit look like?
  on('command.run', {command:'clear'}, async ($, e, next) => {
    await note($, `command.run clear blocked=${blockClear} t2=${t2}`);
    if (t2) {
      // Same shape as the planned T2: ask inside the held command, treat anything but the explicit choice as cancel.
      let answer;
      try { answer = await $.ui.ask('poc T2：要先交接再清除嗎？', ['先交接再清除', '直接清除', '取消']); } catch (error) { answer = `REJECTED ${error?.message}`; }
      await note($, `t2 answer=${short(answer)}`);
      if (answer === '直接清除') return next(e);
      return {text:`poc T2: /clear held (${short(answer, 60)})`};
    }
    // Answering without next() runs no command, so the conversation stays. This is how a handoff prompt could hold /clear.
    if (blockClear) return {text:'poc: /clear was held by handoff-poc (blockClear is on)'};
    return next(e);
  });
  on('command.run', {command:'poc-block-clear'}, async ($) => { blockClear = !blockClear; await note($, `blockClear=${blockClear}`); return {text:`poc: blockClear=${blockClear}`}; });
  on('command.run', {command:'compact'}, async ($, e, next) => { await note($, 'command.run compact'); return next(e); });
  on('command.run', {command:'exit'}, async ($, e, next) => { await note($, 'command.run exit'); return next(e); });
  on('session.compact', async ($, e, next) => { await note($, `session.compact ${short(e, 160)}`); return next(e); });

  // V4: band with digit hotkeys, and $.ui.ask, user-initiated and from a timer.
  on('command.run', {command:'poc-band'}, async ($) => {
    band = {last:'(none)'};
    $.ui.invalidate('ui.render');
    return {};
  });
  on('ui.render', {component:'AbovePrompt'}, async ($, e, next) => {
    if (!band) return next(e);
    const {Box, Text, Button} = $.ui.resolve(e);
    const theirs = await next(e);
    const press = (n) => async () => {
      band.last = n;
      await note($, `band press ${n}`);
      if (n === '3') band = null;
      $.ui.invalidate('ui.render');
    };
    return Box({flexDirection:'column', children:[
      theirs,
      Text({children:`poc band · maxRows=${e.props.maxRows} bodyColumns=${e.props.bodyColumns} isWorking=${e.props.isWorking} hasSurvey=${e.props.hasSurvey} viewport=${e.viewport?.columns}x${e.viewport?.rows} last=${band.last}`}),
      Box({flexDirection:'row', columnGap:2, children:[
        Button({key:'b1', label:OPTIONS[0], hotkey:'1', plain:true, onPress:press('1')}),
        Button({key:'b2', label:OPTIONS[1], hotkey:'2', plain:true, onPress:press('2')}),
        Button({key:'b3', label:OPTIONS[2], hotkey:'3', plain:true, onPress:press('3')}),
      ]}),
    ]});
  });
  on('command.run', {command:'poc-ask'}, async ($) => {
    const answer = await safe(() => $.ui.ask('poc：context 已用 60%，要先交接嗎？', OPTIONS));
    await note($, `ask answer=${short(answer)}`);
    return {};
  });
  on('command.run', {command:'poc-ask-timer'}, async ($) => {
    $.clock.after(3000, async () => {
      const working = short(await safe(() => $.session.turns()));
      const answer = await safe(() => $.ui.ask('poc：計時器觸發的提問', OPTIONS));
      await note($, `ask(timer) turns=${working} answer=${short(answer)}`);
    });
    return {};
  });

  // V5: a pane the mod opens by itself, at different terminal widths.
  on('command.run', {command:'poc-pane-timer'}, async ($) => {
    $.clock.after(2000, async () => {
      const placed = await safe(() => $.ui.open({id:'poc-pane', title:'poc pane', rows:8}));
      await note($, `pane open ${short(placed)}`);
    });
    return {};
  });
  on('ui.render', {component:'Pane'}, async ($, e, next) => {
    if (e.requestId !== 'poc-pane') return next(e);
    const {Text} = $.ui.resolve(e);
    return Text({children:`poc pane placement=${e.props.placement} bodyColumns=${e.props.bodyColumns} viewport=${e.viewport?.columns}x${e.viewport?.rows}`});
  });

  // Store, userConfig, fill-in-hook, output visibility, T2 toggle, status/toast.
  on('command.run', {command:'poc-store'}, async ($) => {
    await $.store.set('poc-store-test', {text:'POC-STORE-VALUE', n:1});
    await note($, `store set ok keys=${short(await safe(() => $.store.keys()))} get=${short(await safe(() => $.store.get('poc-store-test')))}`);
    return {};
  });
  on('command.run', {command:'poc-config'}, async ($) => {
    const rows = await safe(() => $.config.list());
    const mine = Array.isArray(rows) ? rows.filter(r => String(r.key).startsWith('handoff-poc.')) : rows;
    const settings = await safe(() => $.settings.read());
    await note($, `config options(at load)=${short(USER_CONFIG)} rows=${short(mine, 700)} pluginConfigs=${short(settings?.pluginConfigs)}`);
    return {};
  });
  on('command.run', {command:'poc-config-set'}, async ($, e) => {
    const [field, raw] = (e.args || '').trim().split(/\s+/);
    const value = raw === 'true' ? true : raw === 'false' ? false : Number.isNaN(Number(raw)) ? raw : Number(raw);
    const result = await safe(() => $.config.set({key:`handoff-poc.${field}`, value}));
    await note($, `config.set ${field}=${short(value)} -> ${short(result)}`);
    $.clock.after(1500, async () => {
      const rows = await safe(() => $.config.list());
      const mine = Array.isArray(rows) ? rows.filter(r => String(r.key).startsWith('handoff-poc.')) : rows;
      await note($, `after set: options(at load)=${short(USER_CONFIG)} rows=${short(mine, 700)}`);
    });
    return {};
  });
  on('command.run', {command:'poc-fill-hook'}, async ($) => {
    await note($, `fill inside command.run hook -> ${short(await safe(() => $.prompt.fill({text:'poc: filled from inside a command.run hook'})))}`);
    return {};
  });
  on('command.run', {command:'poc-text'}, async () => ({text:'POC-TEXT-MARKER-7391'}));
  on('command.run', {command:'poc-log'}, async ($) => { $.ui.log('POC-LOG-MARKER-5528'); return {}; });
  on('command.run', {command:'poc-context'}, async () => ({text:'poc-context shown', context:['POC-CONTEXT-MARKER-3306']}));
  on('command.run', {command:'poc-t2'}, async ($) => { t2 = !t2; await note($, `t2=${t2}`); return {text:`poc: t2=${t2}`}; });
  on('command.run', {command:'poc-status'}, async ($, e) => {
    const text = (e.args || '').trim();
    $.ui.status(text ? `poc status: ${text}` : undefined);
    await note($, `status ${text ? 'set' : 'cleared'}`);
    return {};
  });
  on('command.run', {command:'poc-toast'}, async ($) => {
    $.ui.toast('poc toast: hello', {timeoutMs:6000});
    await note($, 'toast shown');
    return {};
  });
}
