import {VERSION} from './meta.js';

/** Local wall-clock HH:MM for a clock reading in milliseconds; follows the host time zone. */
export function clockTime(ms) {
  const d = new Date(ms);
  return `${String(d.getHours()).padStart(2,'0')}:${String(d.getMinutes()).padStart(2,'0')}`;
}

/** A note's label is just its door name, so only its excerpt says what it is; it keeps one at any age. */
const ALWAYS_EXCERPT_DOORS = new Set(['note']);

/** Newest first; only the two newest keep an excerpt to limit pane height, plus any door that cannot name itself. */
export function inputRows(state) {
  const items = [...state.inputs].reverse().map((i, index) => ({text:`${clockTime(i.at)} ${i.kind} · ${i.origin}`, excerpt:index < 2 || ALWAYS_EXCERPT_DOORS.has(i.door) ? (i.excerpt ?? null) : null}));
  const empty = items.length ? null : state.inputsSince === null ? '尚無' : `尚無（${clockTime(state.inputsSince)} 起記錄）`;
  return {label:'外部輸入', empty, items};
}

/** Input rows as drawable nodes. Both lines wrap rather than truncate: the pane is narrow and the cut-off part is
 * the useful part. A Box carries the indent because wrapped continuation lines would otherwise start flush left. */
export function inputRowNodes(rows, {Box, Text}, indent) {
  return rows.flatMap(i => [
    Box({paddingLeft:indent, children:[Text({wrap:'wrap', children:i.text})]}),
    ...(i.excerpt ? [Box({paddingLeft:indent + 2, children:[Text({dimColor:true, wrap:'wrap', children:`「${i.excerpt}」`})]})] : []),
  ]);
}

const seconds = (now, at) => Math.max(0, Math.floor((now - at) / 1000));

/** Live-section tone: a wait outranks a running tool, because "needs you" is what a glance must catch. */
export function liveTone(state) {
  if (state.waits.length) return 'warning';
  if (state.activities.length) return 'success';
  return 'muted';
}

/** Action dot: a running tool, else a failed last tool, else quiet. */
export function actionDot(state) {
  if (state.activities.length) return 'success';
  if (state.lastTool?.status === 'error') return 'danger';
  return 'muted';
}

/** Observed state as sections; tones stay semantic so each layout picks its own colours. */
export function paneRows(state, now) {
  const summary = state.summary;
  const active = state.activities;
  let action = state.turnStatus === 'ended' ? '本回合已結束' : state.turnStatus === 'active' ? '本回合進行中，尚無執行中工具' : '尚未觀測到工作動作';
  if (active.length) action = active.length === 1 ? `正在執行 ${active[0].label}` : `共 ${active.length} 個工具執行中：${active.slice(0,3).map(a => a.tool).join('、')}`;
  let attention = state.waitUnknown ? '等待狀態不明' : '目前沒有待回覆訊號';
  if (state.waits.length) attention = state.waits.some(w => w.kind === 'question') ? '有問題等你回答' : '有權限通知，請確認原生授權介面';
  const notes = [];
  if (summary && state.summaryRevision !== state.revision) notes.push({text:'有新活動，摘要待更新', tone:'muted'});
  if (state.summaryError) notes.push({text:'摘要更新失敗', tone:'danger'});
  const inputs = inputRows(state);
  return {title:`你到底在忙什麼？ v${VERSION}`, sections:[
    {id:'summary', label:'摘要', tone:'accent', meta:state.snapshotAt === null ? null : `脈絡與證據更新：${seconds(now, state.snapshotAt)} 秒前`, notes, rows:[
      {label:'目標', text:summary?.goal?.text ?? '目的尚不清楚'},
      {label:'脈絡', text:summary?.context?.text ?? '尚無摘要'},
      {label:'證據', text:summary?.evidence?.text ?? '尚無摘要'},
    ]},
    {id:'live', label:'即時', tone:liveTone(state), meta:state.lastEventAt === null ? null : `距離最近事件：${seconds(now, state.lastEventAt)} 秒`, notes:[], rows:[
      {label:'動作', text:action, dot:actionDot(state)},
      {label:'需要你', text:attention, dot:state.waits.length ? 'warning' : 'muted'},
    ]},
    {id:'inputs', label:inputs.label, tone:'input', meta:inputs.items.length ? `${inputs.items.length} 筆` : null, notes:[], empty:inputs.empty, rows:inputs.items},
  ]};
}

/** A section by id, so layouts never depend on section order. */
export function sectionById(view, id) {
  return view.sections.find(s => s.id === id);
}

/** Fields in the flat layout's 0.2.0 order, each carrying its section tone. */
export function inlineFields(view) {
  const summary = sectionById(view, 'summary');
  const live = sectionById(view, 'live');
  const [goal, context, evidence] = summary.rows;
  const [action, attention] = live.rows;
  const fromSummary = row => ({...row, tone:summary.tone});
  const fromLive = row => ({...row, tone:live.tone});
  return [fromSummary(goal), fromSummary(context), fromLive(action), fromSummary(evidence), fromLive(attention)];
}

/** Bottom lines of the flat layout, in the 0.2.0 order. */
export function footerNotes(view) {
  const summary = sectionById(view, 'summary');
  const live = sectionById(view, 'live');
  return [...(summary.meta ? [{text:summary.meta, tone:'muted'}] : []), ...summary.notes, ...(live.meta ? [{text:live.meta, tone:'muted'}] : [])];
}

/** Plain-text form of the flat layout. */
export function paneLines(state, now) {
  const view = paneRows(state, now);
  const inputs = sectionById(view, 'inputs');
  const inputLines = [`${inputs.label}：${inputs.empty ?? ''}`, ...inputs.rows.flatMap(i => [`  ${i.text}`, ...(i.excerpt ? [`    「${i.excerpt}」`] : [])])];
  return [view.title, '', ...inlineFields(view).map(f => `${f.label}：${f.text}`), ...inputLines, '', ...footerNotes(view).map(n => n.text)];
}
