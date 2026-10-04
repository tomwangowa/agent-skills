import {test,expect} from 'claude-code/testing';
import {createState,reduceState} from '../hooks/state.js';
import {paneLines,paneRows} from '../hooks/view.js';
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
