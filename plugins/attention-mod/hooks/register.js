import {createState, reduceState, boundedText, UNKNOWN_SESSION, BETWEEN_SESSIONS} from './state.js';
import {buildSnapshot} from './snapshot.js';
import {parseSummary, summarySystemPrompt, unwrapSummaryJson} from './summary.js';
import {createSchedule, claimSnapshot, settleRequest} from './scheduler.js';
import {paneRows, inlineFields, footerNotes, sectionById, inputRowNodes, collapsedLine} from './view.js';
import {colorFor} from './theme.js';
import {VERSION} from './meta.js';
import {entryFromAppend} from './inputs.js';
import {buildTeamsLink, composeMessage, parseRecipient, recipientStatus, SETUP_STEPS, SETUP_HEADLINE, SETUP_COPY_HINT} from './feedback.js';

let state = createState(UNKNOWN_SESSION);
const schedule = createSchedule();
let sequence = 0;
let timer = null;
let reading = false;
let closed = false;
// A view preference, so it survives /clear and resume; only a reload returns the pane to expanded.
let collapsed = false;
// Dock only: the dock cannot shrink, so folding it closes the pane and pins a status line instead.
let parked = false;
let now = 0;
let endingSessionId = null;
let reconnecting = false;
// Feedback form: memory-only. A reload or any session-reset (/clear, resume, end) starts it closed again.
const closedFeedback = () => ({open:false, draft:'', link:null, copied:null, empty:false});
let feedback = closedFeedback();
// Teams account of whoever receives feedback; set per install so no address lives in this public repo.
let recipient = null;
// Why there is no recipient, so an unset value and a mistyped one get different guidance.
let recipientNotice = 'unset';
const sourceId = () => `e${state.epoch}-s${++sequence}`;
const apply = event => {
  state = reduceState(state, event);
  if (event.type === 'session-reset') feedback = closedFeedback();
};

/** Keep observation failures from changing the caller's result. */
function redraw($) {
  try { $.ui.invalidate('ui.render'); } catch {}
  if (parked) pinStatus($);
}

/** The one-line stand-in for a parked pane: the wait when there is one, else the action. */
function pinStatus($) {
  try {
    const line = collapsedLine(paneRows(state, now));
    // No plugin name here: the host prefixes the line with it.
    $.ui.status(`${line.label}：${line.text}（輸入 /attention 展開）`);
  } catch { /* A failed status line must not disturb the caller. */ }
}

/** Close the pane like a native × (so updates do not reopen it) and leave the status line behind. */
async function park($) {
  parked = true;
  pinStatus($);
  try { await $.ui.close({id:'attention-mod'}); } catch { /* A refused close leaves the pane open beside the status. */ }
}

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
export function register(on, options) {
  recipient = parseRecipient(options?.feedbackRecipient);
  recipientNotice = recipientStatus(options?.feedbackRecipient);
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
      if (!closed && e.isInteractive) await $.ui.open({id:'attention-mod', title:`你到底在忙什麼 v${VERSION}`, rows:18, columns:48});
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
    if (parked) { parked = false; try { $.ui.status(undefined); } catch {} }
    await $.ui.open({id:'attention-mod', title:`你到底在忙什麼 v${VERSION}`, rows:18, columns:48});
    return {};
  });
  on('ui.close', {id:'attention-mod'}, ($, e, next) => { closed = true; return next(e); });
  on('ui.render', {component:'AskUserQuestion'}, ($, e, next) => {
    if (state.activities.some(a => a.id === e.requestId)) apply({type:'wait-start', id:e.requestId, kind:'question', at:now});
    return next(e);
  });
  on('ui.render', {component:'Pane', requestId:'attention-mod'}, ($, e) => {
    const els = $.ui.resolve(e);
    const view = paneRows(state, now);
    // Only the dock reliably has the height for bordered sections; any other placement keeps the compact layout.
    const dock = e.props.placement === 'dock';
    // The dock's height belongs to the host, so folding it would only leave a tall empty frame.
    const header = drawHeader(view, els, dock ? () => park($) : () => { collapsed = !collapsed; redraw($); }, e.props.placement);
    if (collapsed && !dock) {
      const line = collapsedLine(view);
      return els.Box({flexDirection:'column', children:[header, labelled(els.Text, line, line.tone, 'truncate')]});
    }
    const body = dock ? drawDock(view, els, header) : drawInline(view, els, e.props.bodyColumns, header);
    return els.Box({flexDirection:'column', children:[...body, ...drawFeedback($, els)]});
  });
}

/**
 * Feedback form. Submitting only builds a Teams chat link with the typed text prefilled;
 * the person presses Enter in Teams, so the mod sends nothing and reads no session data.
 */
function drawFeedback($, {Box, Text, Button, Input, Link}) {
  const change = patch => { feedback = {...feedback, ...patch}; redraw($); };
  if (!feedback.open) return [Button({key:'open-feedback', label:'回饋', onPress:() => change({open:true, empty:false})})];
  const hasRecipient = recipient !== null;
  const copy = text => async press => {
    try { const r = await $.ui.copy({text, surface:press.surface}); change({copied:r.isCopied}); } catch { change({copied:false}); }
  };
  return [Box({flexDirection:'column', children:[
    Text({bold:true, children:'回饋'}),
    Text({dimColor:true, wrap:'wrap', children:'描述問題或改善建議，可用 bug: 或 idea: 開頭分類，Enter 產生 Teams 連結。'}),
    ...(hasRecipient ? [] : [
      Text({color:colorFor('warning'), wrap:'wrap', children:SETUP_HEADLINE[recipientNotice] ?? SETUP_HEADLINE.unset}),
      ...SETUP_STEPS.map(step => Text({wrap:'wrap', children:step})),
      Text({dimColor:true, wrap:'wrap', children:SETUP_COPY_HINT}),
    ]),
    Input({key:'attention-feedback', label:'內容', placeholder:'bug: ...', value:feedback.draft, submitLabel:hasRecipient ? '產生連結' : '產生內容', autoFocus:true,
      // Editing invalidates a link made from the older text, so redraw to drop it.
      onInput:value => change({draft:value, link:null, copied:null, empty:false}),
      onSubmit:value => {
        // A prefix with no text is empty feedback, so both paths agree on what counts as typed.
        const composed = composeMessage(value);
        const link = composed && hasRecipient ? buildTeamsLink(value, recipient) : null;
        // Without a recipient there is no link, but the same labelled text can still be copied.
        change({draft:value, link:link ?? (composed ? {message:composed.message, url:null, truncated:false} : null), copied:null, empty:!composed});
      }}),
    ...(feedback.empty ? [Text({color:colorFor('warning'), children:'請先輸入內容。'})] : []),
    ...(feedback.link ? [
      ...(feedback.link.url ? [
        Text({wrap:'wrap', children:'連結只含你輸入的文字，點開後在 Teams 確認內容，按 Enter 才會送出：'}),
        Link({href:feedback.link.url, label:'[ 在 Teams 開啟 ]'}),
        ...(feedback.link.truncated ? [Text({dimColor:true, wrap:'wrap', children:'內容過長，連結內已截斷；請改用「複製內容」貼上完整文字。'})] : []),
      ] : []),
      Button({key:'copy-feedback', label:'複製內容', onPress:copy(feedback.link.message)}),
      ...(feedback.copied === true ? [Text({dimColor:true, children:'已複製。'})] : feedback.copied === false ? [Text({dimColor:true, children:'無法複製，請手動選取文字。'})] : []),
    ] : []),
    Button({key:'close-feedback', label:'取消回饋', onPress:() => change(closedFeedback())}),
  ]})];
}

/** A dot then a coloured bold label, shared by both layouts so "● 動作：正在執行" reads the same. */
function labelled(Text, row, tone, wrap = 'wrap') {
  return Text({wrap, children:[
    ...(row.dot ? [Text({color:colorFor(row.dot), children:'● '})] : []),
    Text({bold:true, color:colorFor(tone), children:`${row.label}：`}),
    row.text,
  ]});
}

/** Title and version, then the toggle: native × closes the pane, this only folds it. */
function drawHeader(view, {Box, Text, Button}, toggle, placement) {
  return Box({flexDirection:'row', children:[
    Text({bold:true, wrap:'truncate', children:view.title}),
    // A plain space: Button prints its brackets flush against whatever precedes it.
    Text({children:' '}),
    Button({key:'toggle-collapse', label:collapsed && placement !== 'dock' ? '展開面板' : '收起面板', onPress:toggle}),
  ]});
}

/** Bordered sections for the dock, which has the height for them. */
function drawDock(view, {Box, Text}, header) {
  // A lone dock pane gets no tab strip, so the frame shows no title; the body carries it instead.
  return [header, ...view.sections.map(section => Box({flexDirection:'column', borderStyle:'round', borderColor:colorFor(section.tone), paddingX:1, children:[
    Box({flexDirection:'row', justifyContent:'space-between', children:[
      // No brackets: the host's Button draws "[ label ]", so only things you can press may wear them.
      Text({bold:true, color:colorFor(section.tone), wrap:'truncate', children:section.label}),
      ...(section.meta ? [Text({dimColor:true, wrap:'truncate', children:section.meta})] : []),
    ]}),
    ...(section.id === 'inputs'
      ? (section.empty ? [Text({dimColor:true, wrap:'truncate', children:section.empty})] : inputRowNodes(section.rows, {Box, Text}, 0))
      : section.rows.map(row => labelled(Text, row, section.tone))),
    ...section.notes.map(note => Text({wrap:'wrap', color:colorFor(note.tone), dimColor:note.tone === 'muted', children:note.text})),
  ]}))];
}

/** The 0.2.0 flat rows with colour added; used wherever height is scarce. */
function drawInline(view, els, bodyColumns, header) {
  const {Text} = els;
  const inputs = sectionById(view, 'inputs');
  return [
    header,
    // Box borders draw all four sides, so the rule is a line of box-drawing cells sized to the body.
    Text({dimColor:true, wrap:'truncate', children:'─'.repeat(Math.max(1, bodyColumns))}),
    ...inlineFields(view).map(field => labelled(Text, field, field.tone)),
    Text({wrap:'truncate', children:[Text({bold:true, color:colorFor(inputs.tone), children:`${inputs.label}：`}), inputs.empty ?? '']}),
    ...inputRowNodes(inputs.rows, els, 2),
    Text({wrap:'wrap', children:''}),
    ...footerNotes(view).map(note => Text({wrap:'wrap', color:colorFor(note.tone), dimColor:note.tone === 'muted', children:note.text})),
  ];
}

/** Serialize an excerpt, never retain full tool arguments or outputs. */
function safeText(value) {
  try { return boundedText(JSON.stringify(value)); } catch { return '[unavailable source]'; }
}
