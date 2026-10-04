/** Render observed state without running a model; labels stay apart so the pane can style them. */
export function paneRows(state, now) {
  const summary = state.summary;
  const active = state.activities;
  let action = state.turnStatus === 'ended' ? '本回合已結束' : state.turnStatus === 'active' ? '本回合進行中，尚無執行中工具' : '尚未觀測到工作動作';
  if (active.length) action = active.length === 1 ? `正在執行 ${active[0].label}` : `共 ${active.length} 個工具執行中：${active.slice(0,3).map(a => a.tool).join('、')}`;
  let attention = state.waitUnknown ? '等待狀態不明' : '目前沒有待回覆訊號';
  if (state.waits.length) attention = state.waits.some(w => w.kind === 'question') ? '有問題等你回答' : '有權限通知，請確認原生授權介面';
  const fields = [
    {label:'目標', text:summary?.goal?.text ?? '目的尚不清楚'},
    {label:'脈絡', text:summary?.context?.text ?? '尚無摘要'},
    {label:'動作', text:action},
    {label:'證據', text:summary?.evidence?.text ?? '尚無摘要'},
    {label:'需要你', text:attention},
  ];
  const notes = [];
  if (state.snapshotAt !== null) notes.push(`脈絡與證據更新：${Math.max(0,Math.floor((now - state.snapshotAt)/1000))} 秒前`);
  if (summary && state.summaryRevision !== state.revision) notes.push('有新活動，摘要待更新');
  if (state.summaryError) notes.push('摘要更新失敗');
  if (state.lastEventAt !== null) notes.push(`距離最近事件：${Math.max(0,Math.floor((now-state.lastEventAt)/1000))} 秒`);
  return {title:'你到底在忙什麼？', fields, notes};
}

/** Plain-text form of the pane rows. */
export function paneLines(state, now) {
  const {title, fields, notes} = paneRows(state, now);
  return [title, '', ...fields.map(f => `${f.label}：${f.text}`), '', ...notes];
}
