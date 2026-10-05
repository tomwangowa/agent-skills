import {test,expect} from 'claude-code/testing';
import {host,begin,prompt,paneTarget,renderedText,append} from './fixtures.js';

test('clear recovers when the session ID changes without any new start event',async($,on)=>{
  const h=host(on);
  await begin($);
  await prompt($,'old task');
  await h.clock.advance(1000);
  await $.session.end({reason:'clear',sessionId:'session-one',resume:{}});
  await h.clock.advance(60000);
  expect(h.record.models.length).toBe(1);
  h.setSession('new-session-after-clear');
  await prompt($,'fresh task');
  await h.clock.advance(2000);
  expect(h.record.models.length).toBe(2);
  expect(JSON.parse(h.record.models[1].request.prompt).sources.some(s=>s.text==='fresh task')).toBe(true);
  expect(JSON.parse(h.record.models[1].request.prompt).sources.some(s=>s.text==='old task')).toBe(false);
});

test('resume restores idle conversation without a start event or new prompt',async($,on)=>{
  let reads=0;
  const h=host(on,{readMessages:()=>({value:++reads===1?[]:[{role:'user',text:'resumed task',toolUses:[]}]})});
  await begin($);
  await h.clock.settle();
  await $.session.end({reason:'resume',sessionId:'session-one',resume:{}});
  h.setSession('resumed-session');
  await h.clock.advance(2000);
  expect(h.record.models.length).toBe(1);
  expect(JSON.parse(h.record.models[0].request.prompt).sources.some(s=>s.text==='resumed task')).toBe(true);
});

test('new prompt and clear invalidate late summaries without releasing their lock',async($,on)=>{
  let answer;
  const h=host(on,{model:e=>new Promise(resolve=>{answer=()=>resolve({value:{isAnswered:true,text:JSON.stringify({goal:{text:'old-task',sources:[JSON.parse(e.prompt).sources[0].id]},context:null,evidence:null}),usage:{}}});})});
  await begin($);
  await prompt($,'old-task');
  await h.clock.advance(1000);
  await prompt($,'new-task');
  await $.session.end({reason:'clear',sessionId:'session-one',resume:{}});
  h.setSession('session-two');
  await $.classic.SessionStart({hook_event_name:'SessionStart',source:'clear',session_id:'session-two',transcript_path:'/fixture',cwd:'/fixture'});
  await prompt($,'fresh-task');
  await h.clock.advance(60000);
  expect(h.record.models.length).toBe(1);
  answer();
  await h.clock.settle();
  const pane=await $.ui.mount(paneTarget());
  expect(await renderedText(pane)).not.toContain('old-task');
  await h.clock.advance(1000);
  expect(h.record.models.length).toBe(2);
  answer();
  await h.clock.settle();
});
test('failed revision is attempted once and malformed update preserves previous snapshot age',async($,on)=>{
  let count=0;
  const h=host(on,{model:e=>({value:++count===1?{isAnswered:true,text:JSON.stringify({goal:{text:'task',sources:[JSON.parse(e.prompt).sources[0].id]},context:null,evidence:null}),usage:{}}:{isAnswered:true,text:'bad json',usage:{}}})});
  await begin($);
  await prompt($,'task');
  await h.clock.advance(1000);
  await append($,'a1','new evidence');
  await h.clock.advance(59999);
  expect(count).toBe(1);
  await h.clock.advance(1);
  expect(count).toBe(2);
  await h.clock.advance(120000);
  expect(count).toBe(2);
  const pane=await $.ui.mount(paneTarget());
  expect(await renderedText(pane)).toContain('摘要更新失敗');
  expect(await renderedText(pane)).toContain('脈絡與證據更新：180 秒前');
});

test('restoration retains actual user goal before tool-result user rows',async($,on)=>{
  const h=host(on,{messages:[{role:'user',text:'修正登入',toolUses:[]},{role:'assistant',text:'Claude 懷疑 token 過期',toolUses:[]},{role:'user',text:'',toolUses:[],toolResults:[{tool_use_id:'t',text:'test failed',isError:true}]}]});
  await begin($);
  await h.clock.advance(1000);
  const data=JSON.parse(h.record.models[0].request.prompt);
  expect(data.goalSource).not.toBe(null);
  expect(data.sources.find(s=>s.id === data.goalSource).text).toBe('修正登入');
  expect(data.sources.some(s=>s.text.includes('Claude 懷疑'))).toBe(true);
});

test('restoration excludes native local-command output and system wrappers',async($,on)=>{
  const h=host(on,{messages:[{role:'user',text:'real task',toolUses:[]},{role:'user',text:'<local-command-stdout>previous generated summary</local-command-stdout>',toolUses:[]},{role:'user',text:'<command-name>/clear</command-name>',toolUses:[]},{role:'user',text:'<system-reminder>irrelevant wrapper</system-reminder>',toolUses:[]}]});
  await begin($);
  await h.clock.advance(1000);
  const data=JSON.parse(h.record.models[0].request.prompt);
  expect(data.sources.length).toBe(1);
  expect(data.sources[0].text).toBe('real task');
});

test('new prompt during a transcript read rejects the old bootstrap',async($,on)=>{
  let release;
  const h=host(on,{readMessages:()=>new Promise(r=>{release=()=>r({value:[{role:'user',text:'old goal',toolUses:[]}]});})});
  await begin($);
  await h.clock.settle();
  await prompt($,'fresh goal');
  release();
  await h.clock.advance(1000);
  const data=JSON.parse(h.record.models[0].request.prompt);
  expect(data.sources.some(s=>s.text === 'fresh goal')).toBe(true);
  expect(data.sources.some(s=>s.text === 'old goal')).toBe(false);
});

test('resume retries bootstrap after an earlier generation read settles',async($,on)=>{
  let release;
  let reads=0;
  const h=host(on,{readMessages:()=>++reads===1?new Promise(r=>{release=()=>r({value:[{role:'user',text:'old goal',toolUses:[]}]});}):{value:[{role:'user',text:'resumed goal',toolUses:[]}]}});
  await begin($);
  await h.clock.settle();
  await $.session.end({reason:'resume',sessionId:'session-one',resume:{}});
  h.setSession('resumed');
  await $.classic.SessionStart({source:'resume',session_id:'resumed'});
  release();
  await h.clock.advance(1000);
  expect(reads).toBe(2);
  expect(JSON.parse(h.record.models[0].request.prompt).sources.some(s=>s.text==='resumed goal')).toBe(true);
});

test('API rejection and timeout retain old summary without retrying the same revision',async($,on)=>{
  let count=0;
  const h=host(on,{model:e=>++count===1?{value:{isAnswered:true,text:JSON.stringify({goal:{text:'task',sources:[JSON.parse(e.prompt).sources[0].id]},context:null,evidence:null}),usage:{}}}:count===2?{deny:'fixture policy refused'}:{value:{isAnswered:false,reason:'aborted',usage:{}}}});
  await begin($);
  await prompt($,'task');
  await h.clock.advance(1000);
  await append($,'a1','fixture update');
  await h.clock.advance(60000);
  let pane=await $.ui.mount(paneTarget());
  expect(await renderedText(pane)).toContain('摘要更新失敗');
  expect(await renderedText(pane)).toContain('目標：task');
  await pane.unmount();
  await append($,'a2','fixture update 2');
  await h.clock.advance(60000);
  await h.clock.advance(120000);
  expect(count).toBe(3);
  pane=await $.ui.mount(paneTarget());
  expect(await renderedText(pane)).toContain('脈絡與證據更新：240 秒前');
});

test('a dropped prompt is passed through without changing the task or requesting another summary',async($,on)=>{
  const h=host(on,{submit:e=>e.text==='blocked task'?{drop:'refused'}:{text:e.text}});
  await begin($);
  await prompt($,'accepted task');
  await h.clock.advance(1000);
  expect(await prompt($,'blocked task')).toEqual({drop:'refused'});
  await h.clock.advance(120000);
  expect(h.record.models.length).toBe(1);
});
