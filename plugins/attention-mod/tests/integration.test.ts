import {test,expect} from 'claude-code/testing';
import {host,begin,prompt,append,paneTarget,renderedText} from './fixtures.js';
/** Props of every bordered Box in a drawn pane, in tree order. */
const borderedBoxes=async pane=>{
  const found=[];
  const walk=node=>{ if(node && typeof node==='object'){ if(node.type==='Box' && node.props?.borderStyle) found.push(node.props); (node.children??[]).forEach(walk); } };
  walk(await pane.drawn());
  return found;
};
/** Every Text node in a drawn pane, at any depth, in tree order. */
const allTexts=async pane=>{
  const found=[];
  const walk=node=>{ if(node && typeof node==='object'){ if(node.type==='Text') found.push(node); (node.children??[]).forEach(walk); } };
  walk(await pane.drawn());
  return found;
};
/** The top-level row Text whose bold label span reads exactly `label`. */
const rowByLabel=(rows,label)=>rows.find(row=>row.type==='Text' && (row.children??[]).some(c=>c?.props?.bold && c.children?.[0]===label));
/** The first Text node whose own (string) children include `text`, at any depth. */
const textByContent=(texts,text)=>texts.find(t=>(t.children??[]).includes(text));

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
    expect(await renderedText(pane)).toContain('目標：');
    await pane.unmount();
  }
  const other=await $.ui.mount(paneTarget('terminal','dock','other'));
  expect(await renderedText(other)).toContain('native-component');
});
test('inline pane keeps the 0.2.0 rows, draws no borders, and colours the labels',async($,on)=>{
  host(on);
  await begin($);
  const pane=await $.ui.mount(paneTarget('terminal','inline'));
  const [title,rule,...rest]=(await pane.drawn()).children;
  expect(title).toMatchObject({type:'Text',props:{bold:true},children:['你到底在忙什麼？']});
  expect(rule.children).toEqual(['─'.repeat(40)]);
  const labels=rest.filter(row=>row.type==='Text').flatMap(row=>(row.children??[]).filter(c=>c?.props?.bold)).map(c=>({text:c.children[0],color:c.props.color}));
  expect(labels).toEqual([{text:'目標：',color:'blue'},{text:'脈絡：',color:'blue'},{text:'動作：',color:undefined},{text:'證據：',color:'blue'},{text:'需要你：',color:undefined},{text:'外部輸入：',color:'magenta'}]);
  expect((await borderedBoxes(pane)).length).toBe(0);
  expect(await renderedText(pane)).toContain('目標：目的尚不清楚');
  expect(await renderedText(pane)).toContain('外部輸入：尚無');
  // 0.2.0 row count (commit ed1c236, hooks/register.js) for this idle state:
  // title(1) + rule(1) + 5 fields(5) + inputs label line(1) + 0 input rows (none yet)
  // + blank line(1) + 0 notes (no snapshot/summary/error/lastEvent yet) + close button(1) = 10.
  expect((await pane.drawn()).children.length).toBe(10);
});
test('dock pane draws three round sections coloured by meaning and no inner title',async($,on)=>{
  host(on);
  await begin($);
  const pane=await $.ui.mount(paneTarget('terminal','dock'));
  const boxes=await borderedBoxes(pane);
  expect(boxes.map(b=>b.borderStyle)).toEqual(['round','round','round']);
  expect(boxes.map(b=>b.borderColor)).toEqual(['blue',undefined,'magenta']);
  const text=await renderedText(pane);
  for(const header of ['[ 摘要 ]','[ 即時 ]','[ 外部輸入 ]']) expect(text).toContain(header);
  expect(text).not.toContain('你到底在忙什麼？');
});
test('dock live border is green while a tool runs, yellow while a question waits, default after',async($,on)=>{
  let finish;
  const h=host(on,{tool:()=>new Promise(r=>{finish=()=>r({result:'answer'});})});
  await begin($);
  const pane=await $.ui.mount(paneTarget('terminal','dock'));
  const liveColor=async()=>(await borderedBoxes(pane))[1].borderColor;
  const pending=$.tool.call({tool:'AskUserQuestion',questions:[],tool_use_id:'q'});
  await h.clock.settle();
  expect(await liveColor()).toBe('green');
  const question=await $.ui.mount({plugin:'attention-mod',surface:'terminal',component:'AskUserQuestion',requestId:'q',props:{tool:'AskUserQuestion',questions:[]}});
  await h.clock.advance(1000);
  expect(await liveColor()).toBe('yellow');
  finish();
  await pending;
  await h.clock.advance(1000);
  expect(await liveColor()).toBe(undefined);
  await question.unmount();
});
test('dock and inline show the same field values',async($,on)=>{
  host(on);
  await begin($);
  await prompt($,'修正登入');
  const dockPane=await $.ui.mount(paneTarget('terminal','dock'));
  const dock=await renderedText(dockPane);
  // The test kit allows one live mount per surface and requestId, so the dock goes before the inline mount.
  await dockPane.unmount();
  const inline=await renderedText(await $.ui.mount(paneTarget('terminal','inline')));
  for(const value of ['目標：','脈絡：','動作：','證據：','需要你：','外部輸入','目的尚不清楚','尚無摘要','本回合進行中','目前沒有待回覆訊號']) {
    expect(dock).toContain(value);
    expect(inline).toContain(value);
  }
});
test('inline dot and label turn green while a tool runs',async($,on)=>{
  const h=host(on,{tool:()=>new Promise(()=>{})});
  await begin($);
  const pane=await $.ui.mount(paneTarget('terminal','inline'));
  $.tool.call({tool:'Bash',command:'fixture',tool_use_id:'t'});
  await h.clock.settle();
  const rows=(await pane.drawn()).children;
  const actionRow=rowByLabel(rows,'動作：');
  const [dot,label]=actionRow.children;
  expect(dot).toMatchObject({type:'Text',props:{color:'green'},children:['● ']});
  expect(label).toMatchObject({type:'Text',props:{bold:true,color:'green'},children:['動作：']});
});
test('inline dot and label turn yellow while a question waits',async($,on)=>{
  const h=host(on,{tool:()=>new Promise(()=>{})});
  await begin($);
  const pane=await $.ui.mount(paneTarget('terminal','inline'));
  const pending=$.tool.call({tool:'AskUserQuestion',questions:[],tool_use_id:'q'});
  await h.clock.settle();
  const question=await $.ui.mount({plugin:'attention-mod',surface:'terminal',component:'AskUserQuestion',requestId:'q',props:{tool:'AskUserQuestion',questions:[]}});
  await h.clock.advance(1000);
  const rows=(await pane.drawn()).children;
  const needsRow=rowByLabel(rows,'需要你：');
  const [dot,label]=needsRow.children;
  expect(dot).toMatchObject({type:'Text',props:{color:'yellow'},children:['● ']});
  expect(label).toMatchObject({type:'Text',props:{bold:true,color:'yellow'},children:['需要你：']});
  await question.unmount();
  void pending;
});
test('dock and inline both show the failure note in red',async($,on)=>{
  const h=host(on,{model:()=>{throw new Error('model unavailable');}});
  await begin($);
  await prompt($,'修正登入');
  await h.clock.advance(1000);
  const dockPane=await $.ui.mount(paneTarget('terminal','dock'));
  const dockFailNote=textByContent(await allTexts(dockPane),'摘要更新失敗');
  expect(dockFailNote.props.color).toBe('red');
  // The test kit allows one live mount per surface and requestId, so the dock goes before the inline mount.
  await dockPane.unmount();
  const inlinePane=await $.ui.mount(paneTarget('terminal','inline'));
  const inlineFailNote=textByContent(await allTexts(inlinePane),'摘要更新失敗');
  expect(inlineFailNote.props.color).toBe('red');
});
test('inline footer meta is dim while a successful summary keeps its field colours',async($,on)=>{
  const h=host(on,{model:e=>({value:{isAnswered:true,text:JSON.stringify({goal:{text:'修正登入',sources:[JSON.parse(e.prompt).sources[0].id]},context:null,evidence:null}),usage:{}}})});
  await begin($);
  await prompt($,'修正登入');
  await h.clock.advance(1000);
  const pane=await $.ui.mount(paneTarget('terminal','inline'));
  const texts=await allTexts(pane);
  const metaNote=texts.find(t=>(t.children??[]).some(c=>typeof c==='string' && c.startsWith('脈絡與證據更新')));
  const goalLabel=textByContent(texts,'目標：');
  expect(metaNote.props.dimColor).toBe(true);
  expect(goalLabel.props.dimColor).toBe(undefined);
  expect(goalLabel.props.color).toBe('blue');
});
