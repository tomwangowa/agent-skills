import {test,expect} from 'claude-code/testing';
import {host,begin,paneTarget,renderedText} from './fixtures.js';

const CWD='/repo/worktrees/feat-x';
const agent=(id,status,description=`task ${id}`)=>({id,type:'Explore',description,status});
/** Page two, where the model, effort and usage rows live. */
const pageTwo=async pane=>{ await pane.press({key:'page-2'}); return renderedText(pane); };
/** One model request inside a turn, run through the turn.step chain; the effort is left off when undefined. */
const runStep=async($,effort,agentId)=>{
  const step=$.turn.step({turnId:'turn-one',index:0,model:'haiku',messageCount:1,...(effort===undefined?{}:{effort}),...(agentId?{agentId}:{})});
  for await (const chunk of step) void chunk;
  return step.result;
};

test('the usage read asks for the summary breakdown only, once every five ticks',async($,on)=>{
  const h=host(on);
  await begin($);
  await h.clock.advance(4000);
  expect(h.record.usage.length).toBe(0);
  await h.clock.advance(1000);
  expect(h.record.usage.length).toBe(1);
  await h.clock.advance(10000);
  expect(h.record.usage.length).toBe(3);
  for(const args of h.record.usage) expect(args).toEqual({breakdown:'summary'});
});

test('a turn step that names a text effort shows it on page two',async($,on)=>{
  host(on);
  await begin($);
  const pane=await $.ui.mount(paneTarget('terminal','inline'));
  await runStep($,'high');
  expect(await pageTwo(pane)).toContain('努力程度：high');
});

test('a turn step that names a numeric effort shows the number',async($,on)=>{
  host(on);
  await begin($);
  const pane=await $.ui.mount(paneTarget('terminal','inline'));
  await runStep($,3);
  expect(await pageTwo(pane)).toContain('努力程度：3');
});

test('before any turn step the effort reads 未知',async($,on)=>{
  host(on);
  await begin($);
  const pane=await $.ui.mount(paneTarget('terminal','inline'));
  expect(await pageTwo(pane)).toContain('努力程度：未知');
});

test('a subagent step does not change the session effort',async($,on)=>{
  host(on,{agents:()=>[agent('sub-1','running')]});
  await begin($);
  const pane=await $.ui.mount(paneTarget('terminal','inline'));
  await runStep($,'high');
  await runStep($,'low','sub-1');
  expect(await pageTwo(pane)).toContain('努力程度：high');
});

test('the session clearing resets the effort to 未知',async($,on)=>{
  host(on);
  await begin($);
  const pane=await $.ui.mount(paneTarget('terminal','inline'));
  await runStep($,'high');
  await $.session.end({reason:'clear',sessionId:'session-one',resume:{}});
  expect(await pageTwo(pane)).toContain('努力程度：未知');
});

test('an empty rate-limit reading says no reading yet',async($,on)=>{
  const h=host(on,{usage:{startedAt:0,context:{window:200000},rateLimits:[]}});
  await begin($);
  await h.clock.advance(5000);
  const pane=await $.ui.mount(paneTarget('terminal','inline'));
  expect(await pageTwo(pane)).toContain('額度：尚無讀數');
});

test('each rate-limit window shows its own percentage used',async($,on)=>{
  const h=host(on,{usage:{startedAt:0,context:{window:200000},rateLimits:[{kind:'five_hour',percentUsed:11},{kind:'seven_day',percentUsed:24}]}});
  await begin($);
  await h.clock.advance(5000);
  const pane=await $.ui.mount(paneTarget('terminal','inline'));
  const shown=await pageTwo(pane);
  expect(shown).toContain('額度（5 小時）：11% 已用');
  expect(shown).toContain('額度（7 天）：24% 已用');
});

test('a usage read that throws keeps the last reading',async($,on)=>{
  let fail=false;
  const h=host(on,{usage:()=>{ if(fail) throw new Error('usage read failed'); return {startedAt:0,context:{window:200000},rateLimits:[{kind:'five_hour',percentUsed:11}]}; }});
  await begin($);
  await h.clock.advance(5000);
  fail=true;
  await h.clock.advance(5000);
  const pane=await $.ui.mount(paneTarget('terminal','inline'));
  expect(await pageTwo(pane)).toContain('額度（5 小時）：11% 已用');
});

test('the skill row reads the listing as included of total',async($,on)=>{
  const h=host(on,{usage:{startedAt:0,context:{window:200000,breakdown:{skills:{includedSkills:3,totalSkills:5,tokens:1200,skillFrontmatter:[]}}},rateLimits:[]}});
  await begin($);
  await h.clock.advance(5000);
  const pane=await $.ui.mount(paneTarget('terminal','inline'));
  expect(await pageTwo(pane)).toContain('已載入 skill：3 / 5');
});

test('the model row shows the session model once it is read',async($,on)=>{
  const h=host(on,{sessionModel:'claude-sonnet-5-5'});
  await begin($);
  await h.clock.advance(5000);
  const pane=await $.ui.mount(paneTarget('terminal','inline'));
  expect(await pageTwo(pane)).toContain('模型：claude-sonnet-5-5');
});

test('a failed model read leaves the panel up and the model row at 未知',async($,on)=>{
  const h=host(on,{modelFails:true});
  await begin($);
  await h.clock.advance(5000);
  const pane=await $.ui.mount(paneTarget('terminal','inline'));
  expect(await renderedText(pane)).toContain('摘要');
  expect(await pageTwo(pane)).toContain('模型：未知');
});

test('the MCP row counts the MCP tools in the context breakdown',async($,on)=>{
  const h=host(on,{usage:{startedAt:0,context:{window:200000,breakdown:{mcpTools:[{serverName:'docs'},{serverName:'docs'},{serverName:'db'}]}},rateLimits:[]}});
  await begin($);
  await h.clock.advance(5000);
  const pane=await $.ui.mount(paneTarget('terminal','inline'));
  expect(await pageTwo(pane)).toContain('MCP 工具：3 個');
});

test('an empty MCP tool list reads 0 個, not 未知',async($,on)=>{
  const h=host(on,{usage:{startedAt:0,context:{window:200000,breakdown:{mcpTools:[]}},rateLimits:[]}});
  await begin($);
  await h.clock.advance(5000);
  const pane=await $.ui.mount(paneTarget('terminal','inline'));
  expect(await pageTwo(pane)).toContain('MCP 工具：0 個');
});

test('a usage reading without an MCP breakdown reads 未知',async($,on)=>{
  const h=host(on,{usage:{startedAt:0,context:{window:200000},rateLimits:[]}});
  await begin($);
  await h.clock.advance(5000);
  const pane=await $.ui.mount(paneTarget('terminal','inline'));
  expect(await pageTwo(pane)).toContain('MCP 工具：未知');
});
