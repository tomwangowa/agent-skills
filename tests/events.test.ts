import {test,expect} from 'claude-code/testing';
import {host,begin,prompt,paneTarget,renderedText} from './fixtures.js';

test('native concurrent tools and child calls keep their own lifetimes',async($,on)=>{
  let finish;
  const h=host(on,{tool:e=>e.tool_use_id === 'one' ? new Promise(r=>{finish=()=>r({result:'ok'});}) : {result:'ok'}});
  await begin($);
  await prompt($,'task');
  const pending=$.tool.call({tool:'Bash',command:'one',tool_use_id:'one'});
  await h.clock.settle();
  await $.tool.call({tool:'Bash',command:'two',tool_use_id:'two'});
  await $.tool.call({tool:'Bash',command:'child',tool_use_id:'child',agentId:'agent'});
  const pane=await $.ui.mount(paneTarget());
  expect(await renderedText(pane)).toContain('正在執行 Bash：one');
  expect(await renderedText(pane)).not.toContain('Bash：child');
  finish();
  await pending;
  await h.clock.advance(1000);
  expect(await renderedText(pane)).not.toContain('正在執行');
});
test('native ask route is unknown until a question is drawn and completion releases it',async($,on)=>{
  let finish;
  const h=host(on,{tool:()=>new Promise(r=>{finish=()=>r({result:'answer'});})});
  await begin($);
  await $.tool.check({tool:'AskUserQuestion',tool_use_id:'q'});
  const pane=await $.ui.mount(paneTarget());
  expect(await renderedText(pane)).toContain('等待狀態不明');
  const pending=$.tool.call({tool:'AskUserQuestion',questions:[],tool_use_id:'q'});
  await h.clock.settle();
  const question=await $.ui.mount({plugin:'attention-mod',surface:'terminal',component:'AskUserQuestion',requestId:'q',props:{tool:'AskUserQuestion',questions:[]}});
  await h.clock.advance(1000);
  expect(await renderedText(pane)).toContain('有問題等你回答');
  finish();
  await pending;
  await h.clock.advance(1000);
  expect(await renderedText(pane)).toContain('目前沒有待回覆訊號');
  await question.unmount();
});
test('empty input and a terminated session never call the model',async($,on)=>{
  const h=host(on);
  await begin($);
  await h.clock.advance(120000);
  expect(h.record.models.length).toBe(0);
  await $.session.end({reason:'prompt_input_exit',sessionId:'session-one',resume:{}});
  await prompt($,'late input');
  await h.clock.advance(120000);
  expect(h.record.models.length).toBe(0);
});
