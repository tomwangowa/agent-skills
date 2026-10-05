import {test,expect} from 'claude-code/testing';
import {host,begin,prompt,append,paneTarget,renderedText} from './fixtures.js';

test('whole JSON fence is displayed, while prose-wrapped updates preserve the previous summary',async($,on)=>{
  let count=0;
  const h=host(on,{model:e=>{
    const data=JSON.parse(e.prompt);
    const fenced='```json\n'+JSON.stringify({goal:{text:'修正登入',sources:[data.goalSource]},context:null,evidence:null})+'\n```';
    return {value:{isAnswered:true,text:++count===1?fenced:'Explanation\n'+fenced,usage:{}}};
  }});
  await begin($);
  await prompt($,'修正登入');
  await h.clock.advance(1000);
  const pane=await $.ui.mount(paneTarget());
  expect(await renderedText(pane)).toContain('目標：修正登入');
  await append($,'update','new fixture');
  await h.clock.advance(60000);
  expect(await renderedText(pane)).toContain('目標：修正登入');
  expect(await renderedText(pane)).toContain('摘要更新失敗');
  expect(await renderedText(pane)).toContain('脈絡與證據更新：60 秒前');
});

test('slow background model does not block tools, or overwrite current action with old context',async($,on)=>{
  let answer;
  const h=host(on,{model:e=>new Promise(resolve=>{answer=()=>resolve({value:{isAnswered:true,text:JSON.stringify({goal:{text:'修正登入',sources:[JSON.parse(e.prompt).sources[0].id]},context:null,evidence:null}),usage:{}}});})});
  await begin($);
  await prompt($,'修正登入');
  await h.clock.advance(1000);
  expect(h.record.models.length).toBe(1);
  const result=await $.tool.call({tool:'Bash',command:'fixture',tool_use_id:'one'});
  expect(result).toEqual({result:'fixture-output'});
  await append($,'a1','Claude 懷疑 token 過期，尚未驗證');
  answer();
  await h.clock.settle();
  const pane=await $.ui.mount(paneTarget());
  expect(await renderedText(pane)).toContain('修正登入');
  expect(await renderedText(pane)).toContain('有新活動，摘要待更新');
  expect(await renderedText(pane)).not.toContain('正在執行');
  expect(h.record.models[0].request.model).toBe('haiku');
  expect(h.record.models[0].request.maxTokens).toBe(512);
  expect(h.record.models[0].request.timeoutMs).toBe(15000);
  expect(h.record.prompts.length).toBe(1);
  expect(h.record.opens[0].focus).toBe(undefined);
  expect(h.record.opens[0].rows).toBe(18);
});
test('pane closes permanently across updates; attention command opens without a main prompt',async($,on)=>{
  const h=host(on);
  await begin($);
  const initialPane=await $.ui.mount(paneTarget());
  await initialPane.press({key:'close-attention'});
  await initialPane.unmount();
  await prompt($,'task');
  await h.clock.advance(1000);
  expect(h.record.opens.length).toBe(1);
  await $.command.run({command:'attention',args:'',origin:{kind:'composer'}});
  expect(h.record.opens.length).toBe(2);
  expect(h.record.prompts.length).toBe(1);
  expect(h.record.commands[0].immediate).toBe(true);
  for(const surface of ['terminal','desktop']) for(const placement of ['dock','inline']) {
    const pane=await $.ui.mount(paneTarget(surface,placement));
    expect(await renderedText(pane)).toContain('你到底在忙什麼');
    await pane.unmount();
  }
  const other=await $.ui.mount(paneTarget('terminal','dock','other'));
  expect(await renderedText(other)).toContain('native-component');
});
test('pane draws a bold question title, a rule sized to the body, and bold field labels',async($,on)=>{
  host(on);
  await begin($);
  const pane=await $.ui.mount(paneTarget());
  const [title,rule,...rest]=(await pane.drawn()).children;
  expect(title).toMatchObject({type:'Text',props:{bold:true},children:['你到底在忙什麼？']});
  expect(rule.children).toEqual(['─'.repeat(40)]);
  const labels=rest.filter(row=>row.type==='Text' && row.children[0]?.props?.bold).map(row=>row.children[0].children[0]);
  expect(labels).toEqual(['目標：','脈絡：','動作：','證據：','需要你：','外部輸入：']);
  expect(await renderedText(pane)).toContain('目標：目的尚不清楚');
  expect(await renderedText(pane)).toContain('外部輸入：尚無');
});
