import {test,expect} from 'claude-code/testing';
import {createState,reduceState,BETWEEN_SESSIONS} from '../hooks/state.js';
import {paneLines,paneRows,clockTime} from '../hooks/view.js';
test('pane uses snapshot age, marks newer data, and never claims task completion',()=>{
  const s={...createState('s'),revision:2,summaryRevision:1,snapshotAt:1000,summary:{goal:{text:'修正登入',sources:['s']},context:null,evidence:null},turnStatus:'ended'};
  const lines=paneLines(s,21000).join('\n');
  expect(lines).toContain('脈絡與證據更新：20 秒前');
  expect(lines).toContain('有新活動，摘要待更新');
  expect(lines).toContain('本回合已結束');
  expect(lines).not.toContain('任務完成');
});
test('waits are explicit, ask routes stay unknown, and concurrent tools are visible',()=>{
  let s=reduceState(createState('s'),{type:'wait-unknown',at:0});
  expect(paneLines(s,0).join('\n')).toContain('等待狀態不明');
  s=reduceState(s,{type:'wait-start',kind:'question',id:'q',at:0});
  expect(paneLines(s,0).join('\n')).toContain('有問題等你回答');
  for(const id of ['one','two']) s=reduceState(s,{type:'tool-start',epoch:s.epoch,id,tool:'Bash',label:id,at:0});
  expect(paneLines(s,0).join('\n')).toContain('共 2 個工具執行中');
});
test('pane rows expose the question title and each field label apart from its value',()=>{
  const rows=paneRows(createState('s'),0);
  expect(rows.title).toBe('你到底在忙什麼？');
  expect(rows.fields.map(f=>f.label)).toEqual(['目標','脈絡','動作','證據','需要你']);
  expect(rows.fields[0].text).toBe('目的尚不清楚');
});
test('external inputs list newest first with excerpts on the two newest only',()=>{
  let s=createState('s');
  for(const [id,at] of [['a',0],['b',60000],['c',120000]]) s=reduceState(s,{type:'external-input',entry:{id,kind:'hook 注入',origin:'引擎',excerpt:`text-${id}`},sessionId:'s',epoch:s.epoch,at});
  s=reduceState(s,{type:'new-prompt',id:'goal',text:'task',at:130000});
  s=reduceState(s,{type:'external-input',entry:{id:'d',kind:'附件 file',origin:'引擎',excerpt:'text-d'},sessionId:'s',epoch:s.epoch,at:180000});
  const {inputs}=paneRows(s,0);
  expect(inputs.label).toBe('外部輸入');
  expect(inputs.items.map(i=>i.text)).toEqual([
    `${clockTime(180000)} 附件 file · 引擎`,
    `${clockTime(120000)} hook 注入 · 引擎`,
    `${clockTime(60000)} hook 注入 · 引擎`,
    `${clockTime(0)} hook 注入 · 引擎`,
  ]);
  expect(inputs.items.map(i=>i.excerpt)).toEqual(['text-d','text-c',null,null]);
  expect(inputs.empty).toBe(null);
  const lines=paneLines(s,0).join('\n');
  expect(lines).toContain('「text-d」');
  expect(lines).not.toContain('text-a');
  expect(paneLines(s,0).join('\n')).not.toContain('（本回合）');
  expect(paneLines(s,0).join('\n')).not.toContain('（前幾回合）');
});
test('clockTime is zero-padded local HH:MM',()=>{
  expect(clockTime(new Date(2026,0,1,9,5).getTime())).toBe('09:05');
  expect(clockTime(new Date(2026,0,1,23,59).getTime())).toBe('23:59');
});
test('a row carried into a new session stays listed across the next prompt',()=>{
  let s=createState('one');
  s=reduceState(s,{type:'session-reset',sessionId:BETWEEN_SESSIONS,at:10});
  s=reduceState(s,{type:'external-input',entry:{id:'carried',kind:'hook 注入',origin:'引擎',excerpt:'x'},sessionId:s.sessionId,epoch:s.epoch,at:15});
  s=reduceState(s,{type:'session-reset',sessionId:'two',at:20});
  let texts=paneRows(s,0).inputs.items.map(i=>i.text);
  expect(texts.length).toBe(1);
  expect(texts[0].endsWith('引擎')).toBe(true);
  expect(texts[0]).not.toContain('回合');
  s=reduceState(s,{type:'new-prompt',id:'goal',text:'task',at:30});
  texts=paneRows(s,0).inputs.items.map(i=>i.text);
  expect(texts.length).toBe(1);
  expect(texts[0].endsWith('引擎')).toBe(true);
  expect(texts[0]).not.toContain('回合');
});
test('empty inputs say when recording started, without inventing a time',()=>{
  expect(paneRows(createState('s'),0).inputs.empty).toBe('尚無');
  const s={...createState('s'),inputsSince:60000};
  expect(paneLines(s,0).join('\n')).toContain(`外部輸入：尚無（${clockTime(60000)} 起記錄）`);
});
