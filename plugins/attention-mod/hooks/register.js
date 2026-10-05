import {createState, reduceState, boundedText, UNKNOWN_SESSION, BETWEEN_SESSIONS} from './state.js';
import {buildSnapshot} from './snapshot.js';
import {parseSummary, summarySystemPrompt, unwrapSummaryJson} from './summary.js';
import {createSchedule, claimSnapshot, settleRequest} from './scheduler.js';
import {paneRows} from './view.js';
import {entryFromAppend} from './inputs.js';

let state = createState(UNKNOWN_SESSION);
const schedule = createSchedule();
let sequence = 0;
let timer = null;
let reading = false;
let closed = false;
let now = 0;
let endingSessionId = null;
let reconnecting = false;
const sourceId = () => `e${state.epoch}-s${++sequence}`;
const apply = event => { state = reduceState(state, event); };

/** Keep observation failures from changing the caller's result. */
function redraw($) { try { $.ui.invalidate('ui.render'); } catch {} }

/** Restore only an unchanged, empty generation; messages lack stable IDs. */
async function restore($) {
  if (reading || state.sources.length) return;
  reading = true;
  const epoch = state.epoch;
  try {
    const messages = await $.session.messages();
    if (!Array.isArray(messages) || state.epoch !== epoch || state.sources.length || !state.enabled) return;
    const rows = messages.filter(m => !/^\s*<(command-name|local-command|system-reminder)/.test(m.text ?? '')).slice(-64);
    const lastUser = rows.map(m => m.role === 'user' && m.text?.trim() && !m.toolResults?.length && !/^<(command-name|local-command|system-reminder)/.test(m.text) ? 'goal' : '').lastIndexOf('goal');
    const selected = rows;
    for (const message of selected) {
      if (message.text?.trim()) {
        const id = sourceId();
        if (selected.indexOf(message) === lastUser) state = {...state, goalId:id};
        apply({type:'source', source:{id, role:message.role, phase:selected.indexOf(message) < lastUser ? 'earlier-turn' : 'current-turn', text:message.text, at:now}});
      }
      for (const result of message.toolResults ?? []) apply({type:'source', source:{id:sourceId(), role:'tool', text:safeText(result), at:now}});
    }
  } catch { /* The live stream can recover even when transcript reads fail. */ }
  finally {
    reading = false;
    if (state.enabled && state.epoch !== epoch && !state.sources.length) void restore($);
  }
}

/** Run independently of event/render hooks; the lock spans session resets. */
async function summarize($) {
  if (!state.enabled || reading || schedule.inFlight) return;
  try {
    now = await $.clock.now();
    if (!state.enabled || schedule.inFlight) return;
    const snapshot = buildSnapshot(state, [], now);
    if (!snapshot) return;
    const token = claimSnapshot(schedule, snapshot, now);
    if (!token) return;
    try {
      const response = await $.model.complete({model:'haiku', system:summarySystemPrompt(), prompt:snapshot.prompt, maxTokens:512, timeoutMs:15000});
      const summary = response.isAnswered ? parseSummary(unwrapSummaryJson(response.text), snapshot) : null;
      if (!state.enabled || state.sessionId !== snapshot.sessionId || state.epoch !== snapshot.epoch) return;
      if (summary) state = {...state, summary, summaryRevision:snapshot.revision, snapshotAt:snapshot.capturedAt, summaryError:null};
      else state = {...state, summaryError:'unanswered-or-invalid'};
    } catch {
      if (state.enabled && state.sessionId === snapshot.sessionId && state.epoch === snapshot.epoch) state = {...state, summaryError:'request-failed'};
    } finally { settleRequest(schedule, token); redraw($); }
  } catch { /* A refused clock call must not escape an unawaited timer. */ }
}

/** Start one timer; neither tick nor UI awaits the model. */
function startTimer($) {
  if (timer) return;
  timer = $.clock.every(1000, () => {
    if (!state.enabled) { void reconnect($); return; }
    now += 1000;
    redraw($);
    void summarize($);
  });
}

/** Clear/resume may emit no start event; wait for the native ID to change. */
async function reconnect($) {
  if (reconnecting || endingSessionId === null) return;
  reconnecting = true;
  const epoch = state.epoch;
  try {
    const sessionId = await $.session.id();
    if (state.enabled || state.epoch !== epoch || sessionId === endingSessionId) return;
    state = {...state, sessionId, enabled:true};
    endingSessionId = null;
    void restore($);
    redraw($);
  } catch { /* Keep waiting rather than restoring the ending conversation. */ }
  finally { reconnecting = false; }
}

/** Register passive observers and a memory-only attention panel. */
export function register(on) {
  on('session.start', async ($, e, next) => {
    const result = await next(e);
    try {
      state = {...state, sessionId:await $.session.id(), enabled:true};
      endingSessionId = null;
      now = await $.clock.now();
      if (state.inputsSince === null) state = {...state, inputsSince:now};
      await $.command.register({name:'attention', description:'開啟目前工作脈絡面板', immediate:true});
      startTimer($);
      void restore($);
      if (!closed && e.isInteractive) await $.ui.open({id:'attention-mod', title:'你到底在忙什麼', rows:18, columns:48});
    } catch { /* Panel setup cannot block the main session. */ }
    return result;
  });
  on('classic.SessionStart', async ($, e, next) => {
    const result = await next(e);
    if (e.agent_id) return result;
    try {
      if (e.session_id !== state.sessionId || ['clear','resume','fork'].includes(e.source)) apply({type:'session-reset', sessionId:e.session_id, at:await $.clock.now()});
      state = {...state, enabled:true};
      endingSessionId = null;
      startTimer($);
      void restore($);
      redraw($);
    } catch {}
    return result;
  });
  on('session.end', async ($, e, next) => {
    // Invalidate before awaiting downstream work, so late responses cannot land.
    apply({type:'session-reset', sessionId:BETWEEN_SESSIONS, at:now});
    state = {...state, enabled:false};
    endingSessionId = ['clear','resume'].includes(e.reason) ? e.sessionId : null;
    if (!['clear','resume'].includes(e.reason)) { timer?.cancel(); timer = null; }
    return next(e);
  });
  on('prompt.submit', async ($, e, next) => {
    const result = await next(e);
    if ('drop' in result) return result;
    if (!['composer','bridge','sdk'].includes(e.origin.kind)) return result;
    try {
      now = await $.clock.now();
      apply({type:'new-prompt', id:sourceId(), text:result.text ?? e.text, at:now});
      redraw($);
    } catch {}
    return result;
  });
  on('session.append', async ($, e, next) => {
    const epoch = state.epoch;
    const result = await next(e);
    try {
      // Display-only record of rows Tom did not type; kept apart from summary sources.
      const entry = entryFromAppend(e, result);
      if (entry) {
        const stampSession = state.sessionId, stampEpoch = state.epoch;
        const at = await $.clock.now();
        // A row from a session that ended during the clock read must not reappear after the reset;
        // an unbound row (startup or the /clear gap) belongs to whichever session got bound meanwhile.
        const unbound = stampSession === UNKNOWN_SESSION || stampSession === BETWEEN_SESSIONS;
        if (state.sessionId === stampSession) { apply({type:'external-input', entry, sessionId:stampSession, epoch:stampEpoch, at}); redraw($); }
        else if (unbound) { apply({type:'external-input', entry, sessionId:state.sessionId, epoch:state.epoch, at}); redraw($); }
      }
    } catch { /* Classification failures must not change the stored row or the caller's result. */ }
    if (e.agentId || e.message.isMeta || !['response','tool-result'].includes(e.door)) return result;
    try {
      const content = result.message?.content ?? e.message.content;
      const text = content.map(block => block.type === 'text' ? block.text : block.type === 'tool_result' ? typeof block.content === 'string' ? block.content : (block.content ?? []).filter(b => b.type === 'text').map(b => b.text).join('\n') : '').filter(Boolean).join('\n');
      apply({type:'source', epoch, source:{id:`e${epoch}-${e.uuid}`, role:e.door === 'tool-result' ? 'tool' : 'assistant', text, at:await $.clock.now()}});
      redraw($);
    } catch {}
    return result;
  });
  on('tool.call', async ($, e, next) => {
    if (e.agentId || next.origin.plugin !== 'engine') return next(e);
    const epoch = state.epoch;
    const id = e.tool_use_id ?? sourceId();
    try {
      now = await $.clock.now();
      const label = e.tool === 'Bash' ? `Bash：${boundedText(e.command ?? '',120)}` : e.tool;
      apply({type:'tool-start', id, epoch, agentId:null, tool:e.tool, label, at:now});
      apply({type:'source', epoch, source:{id:`e${epoch}-${id}-input`, role:'tool-input', text:safeText(e), at:now}});
      redraw($);
    } catch {}
    let result;
    try { result = await next(e); }
    catch (error) {
      apply({type:'tool-end', id, epoch, status:next.signal.aborted ? 'cancelled' : 'error', at:now});
      redraw($);
      throw error;
    }
    try {
      now = await $.clock.now();
      const status = next.signal.aborted || result.result?.interrupted === true ? 'cancelled' : result.deny ? 'denied' : result.isError || result.result?.isError === true ? 'error' : 'success';
      apply({type:'tool-end', id, epoch, status, at:now});
      apply({type:'source', epoch:state.epoch === epoch ? epoch : -1, source:{id:`e${epoch}-${id}-result`, role:`tool-${status}`, text:safeText({tool:e.tool,status,...result}), at:now}});
      redraw($);
    } catch {}
    return result;
  });
  on('tool.check', async ($, e, next) => {
    const result = await next(e);
    if (!e.agentId && result.decision === 'ask') { apply({type:'wait-unknown', at:now}); redraw($); }
    return result;
  });
  on('classic.Notification', async ($, e, next) => {
    const result = await next(e);
    if (!e.agent_id && e.notification_type === 'permission_prompt') {
      if (state.activities.length === 1) apply({type:'wait-start', id:state.activities[0].id, kind:'permission', tool:state.activities[0].tool, at:now});
      else apply({type:'wait-unknown', at:now});
      redraw($);
    }
    return result;
  });
  on('turn.start', async ($, e, next) => {
    const result = await next(e);
    if (!e.agentId) { apply({type:'turn-start', at:now}); redraw($); }
    return result;
  });
  on('turn.complete', async ($, e, next) => {
    const result = await next(e);
    if (!e.agentId) { apply({type:'turn-end', at:now}); redraw($); }
    return result;
  });
  on('command.run', {command:'attention'}, async ($, e) => {
    closed = false;
    await $.ui.open({id:'attention-mod', title:'你到底在忙什麼', rows:18, columns:48});
    return {};
  });
  on('ui.close', {id:'attention-mod'}, ($, e, next) => { closed = true; return next(e); });
  on('ui.render', {component:'AskUserQuestion'}, ($, e, next) => {
    if (state.activities.some(a => a.id === e.requestId)) apply({type:'wait-start', id:e.requestId, kind:'question', at:now});
    return next(e);
  });
  on('ui.render', {component:'Pane', requestId:'attention-mod'}, ($, e) => {
    const {Box, Text, Button} = $.ui.resolve(e);
    const {title, fields, notes, inputs} = paneRows(state, now);
    // Box borders draw all four sides, so the rule is a line of box-drawing cells sized to the body.
    const rule = '─'.repeat(Math.max(1, e.props.bodyColumns));
    return Box({flexDirection:'column', children:[
      Text({bold:true, wrap:'truncate', children:title}),
      Text({dimColor:true, wrap:'truncate', children:rule}),
      ...fields.map(f => Text({wrap:'wrap', children:[Text({bold:true, children:`${f.label}：`}), f.text]})),
      Text({wrap:'truncate', children:[Text({bold:true, children:`${inputs.label}：`}), inputs.empty ?? '']}),
      ...inputs.items.flatMap(i => [Text({wrap:'truncate', children:`  ${i.text}`}), ...(i.excerpt ? [Text({dimColor:true, wrap:'truncate', children:`    「${i.excerpt}」`})] : [])]),
      Text({wrap:'wrap', children:''}),
      ...notes.map(line => Text({wrap:'wrap', children:line})),
      Button({key:'close-attention', label:'收起', onPress:() => $.ui.close({id:'attention-mod'})}),
    ]});
  });
}

/** Serialize an excerpt, never retain full tool arguments or outputs. */
function safeText(value) {
  try { return boundedText(JSON.stringify(value)); } catch { return '[unavailable source]'; }
}
