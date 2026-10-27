import {test,expect} from 'claude-code/testing';
import {host,begin,paneTarget,renderedText} from './fixtures.js';
import {GIT_ARGS} from '../hooks/worktree.js';
import {createState,reduceState} from '../hooks/state.js';
import {paneRows,paneLines,inlineFields,footerNotes,sectionById} from '../hooks/view.js';
import {agentsView} from '../hooks/agents.js';

const CWD='/repo/worktrees/feat-x';
const deferred=()=>{ let resolve; const promise=new Promise(r=>{ resolve=r; }); return {promise,resolve}; };
const linked=branch=>({exitCode:0,stdout:`/repo/.git/worktrees/x\n/repo/.git\n${branch}\n`,stderr:''});
const agent=(id,status,description=`task ${id}`)=>({id,type:'Explore',description,status});

test('a linked worktree shows its path and branch, read with the one allowed git call',async($,on)=>{
  const calls=[];
  const h=host(on,{cwd:()=>CWD,git:e=>{calls.push(e);return linked('feat/x');}});
  await begin($);
  await h.clock.advance(1000);
  const shown=await renderedText(await $.ui.mount(paneTarget()));
  expect(shown).toContain('工作樹');
  expect(shown).toContain(CWD);
  expect(shown).toContain('feat/x');
  expect(calls[0].argv).toEqual(GIT_ARGS);
  expect(calls[0].init).toMatchObject({cwd:CWD,timeoutMs:2000});
});

test('the main checkout shows no worktree row',async($,on)=>{
  const h=host(on,{cwd:()=>CWD,git:()=>({exitCode:0,stdout:'/repo/.git\n/repo/.git\nmain\n',stderr:''})});
  await begin($);
  await h.clock.advance(1000);
  expect(await renderedText(await $.ui.mount(paneTarget()))).not.toContain('工作樹');
});

test('a git read that throws keeps the path and marks the branch unreadable',async($,on)=>{
  const h=host(on,{cwd:()=>CWD,git:async()=>{ throw new Error('spawn failed'); }});
  await begin($);
  await h.clock.advance(1000);
  const shown=await renderedText(await $.ui.mount(paneTarget()));
  expect(shown).toContain(CWD);
  expect(shown).toContain('無法讀取');
});

test('a directory change after the read shows the waiting label, never the old branch',async($,on)=>{
  let here=CWD;
  const h=host(on,{cwd:()=>here,git:()=>linked('feat/x')});
  await begin($);
  await h.clock.advance(1000);
  here='/repo/worktrees/y';
  await h.clock.advance(1000);
  const shown=await renderedText(await $.ui.mount(paneTarget()));
  expect(shown).toContain('待下一回合更新');
  expect(shown).toContain('/repo/worktrees/y');
  expect(shown).not.toContain('feat/x');
});

test('a detached HEAD shows the detached label',async($,on)=>{
  const h=host(on,{cwd:()=>CWD,git:()=>({exitCode:0,stdout:'/repo/.git/worktrees/x\n/repo/.git\nHEAD\n',stderr:''})});
  await begin($);
  await h.clock.advance(1000);
  expect(await renderedText(await $.ui.mount(paneTarget()))).toContain('分離 HEAD');
});

test('a read that finishes after a session reset is dropped, and its branch never shows',async($,on)=>{
  const first=deferred();
  const second=deferred();
  let reads=0;
  const h=host(on,{cwd:()=>CWD,git:()=>{ reads+=1; return reads===1 ? first.promise : second.promise; }});
  await begin($);
  const pane=await $.ui.mount(paneTarget());
  await $.session.end({reason:'clear',sessionId:'session-one',resume:{}});
  h.setSession('session-two');
  await h.clock.advance(1000);
  first.resolve(linked('old/x'));
  await h.clock.advance(1000);
  // The bound session's read is still pending, so the old branch must not be on screen yet.
  expect(reads).toBe(2);
  expect(await renderedText(pane)).not.toContain('old/x');
  second.resolve(linked('new/y'));
  await h.clock.advance(1000);
  expect(await renderedText(pane)).toContain('new/y');
  expect(await renderedText(pane)).not.toContain('old/x');
});

test('a turn that starts while a read is in flight reads again once it lands, so the new directory is not left waiting',async($,on)=>{
  const first=deferred();
  let here=CWD;
  let reads=0;
  const h=host(on,{cwd:()=>here,git:()=>{ reads+=1; return reads===1 ? first.promise : linked('feat/y'); }});
  await begin($);
  const pane=await $.ui.mount(paneTarget());
  await h.clock.advance(1000);
  // The first read started in the old directory and is still pending when the next turn begins after a cd.
  await $.turn.start({text:'turn two',turnId:'turn-two'});
  here='/repo/worktrees/y';
  expect(reads).toBe(1);
  first.resolve(linked('feat/x'));
  await h.clock.advance(1000);
  expect(reads).toBe(2);
  expect(await renderedText(pane)).toContain('feat/y');
  expect(await renderedText(pane)).not.toContain('待下一回合更新');
});

test('a git read that never answers blocks no turn, and only one read is in flight',async($,on)=>{
  const never=deferred();
  let reads=0;
  host(on,{cwd:()=>CWD,git:()=>{ reads+=1; return never.promise; }});
  await begin($);
  await $.turn.start({text:'first turn',turnId:'turn-one'});
  await $.turn.start({text:'second turn',turnId:'turn-two'});
  expect(reads).toBe(1);
  never.resolve({exitCode:128,stdout:'',stderr:''});
});

test('the subagent section collapses to a count of running and waiting subagents',async($,on)=>{
  const h=host(on,{cwd:()=>CWD,agents:()=>[agent('r1','running','find routes'),agent('r2','running'),agent('w1','waiting'),agent('p1','pending'),agent('c1','completed'),agent('c2','completed')]});
  await begin($);
  await h.clock.advance(1000);
  const shown=await renderedText(await $.ui.mount(paneTarget()));
  expect(shown).toContain('子代理：3 個執行中');
  expect(shown).not.toContain('find routes');
});

test('when the subagent list fails, the section says unreadable instead of keeping the last count',async($,on)=>{
  let fail=false;
  const h=host(on,{cwd:()=>CWD,agents:async()=>{ if(fail) throw new Error('boom'); return [agent('r1','running')]; }});
  await begin($);
  const pane=await $.ui.mount(paneTarget());
  await h.clock.advance(1000);
  expect(await renderedText(pane)).toContain('子代理：1 個執行中');
  fail=true;
  await h.clock.advance(1000);
  const shown=await renderedText(pane);
  expect(shown).toContain('子代理：無法讀取');
  expect(shown).not.toContain('1 個執行中');
});

test('a subagent that never answers turns the section unreadable after two seconds, not stale',async($,on)=>{
  const never=deferred();
  const h=host(on,{cwd:()=>CWD,agents:()=>never.promise});
  await begin($);
  const pane=await $.ui.mount(paneTarget());
  await h.clock.advance(1000);
  expect(await renderedText(pane)).not.toContain('子代理');
  await h.clock.advance(2000);
  expect(await renderedText(pane)).toContain('子代理：無法讀取');
  never.resolve([]);
});

test('a subagent tool call leaves the action row alone',async($,on)=>{
  const never=deferred();
  const h=host(on,{tool:e=>e.agentId ? never.promise : {result:'fixture-output'}});
  await begin($);
  await $.turn.start({text:'task',turnId:'turn-one'});
  const call=$.tool.call({tool:'Read',file_path:'/repo/a.ts',tool_use_id:'sub-read',agentId:'sub-1'});
  await h.clock.advance(1000);
  const shown=await renderedText(await $.ui.mount(paneTarget()));
  expect(shown).toContain('本回合進行中，尚無執行中工具');
  expect(shown).not.toContain('正在執行');
  never.resolve({result:'fixture-output'});
  await call;
});

test('without git or subagent answers, the worktree and subagent rows stay hidden',async($,on)=>{
  const h=host(on);
  await begin($);
  await h.clock.advance(1000);
  const shown=await renderedText(await $.ui.mount(paneTarget()));
  expect(shown).not.toContain('工作樹');
  expect(shown).not.toContain('子代理');
});

/** The key of every Button in a drawn pane, in tree order. */
const buttonKeys=async pane=>{
  const keys=[];
  const walk=node=>{ if(node && typeof node==='object'){ if(node.type==='Button') keys.push(node.props?.key); (node.children??[]).forEach(walk); } };
  walk(await pane.drawn());
  return keys;
};

test('the dock subagent button expands the rows, keeps the choice across ticks, and lists the newest five ended',async($,on)=>{
  const ended=[1,2,3,4,5,6,7].map(n=>agent(`c${n}`,'completed',`done ${n}`));
  const h=host(on,{cwd:()=>CWD,agents:()=>[agent('r1','running','find routes'),...ended]});
  await begin($);
  const pane=await $.ui.mount(paneTarget());
  await h.clock.advance(1000);
  expect(await buttonKeys(pane)).toContain('toggle-agents');
  expect(await renderedText(pane)).toContain('展開子代理');
  expect(await renderedText(pane)).not.toContain('find routes');
  await pane.press({key:'toggle-agents'});
  await h.clock.advance(1000);
  const shown=await renderedText(pane);
  expect(shown).toContain('收起子代理');
  expect(shown).toContain('find routes（running）');
  expect(shown).toContain('done 7（completed）');
  expect(shown).toContain('done 3（completed）');
  expect(shown).not.toContain('done 2（completed）');
});

/** The visible text of a node, flattened the way a reader sees it. */
const visibleText=node=>typeof node==='string' ? node : (node?.children ?? []).map(visibleText).join('');
/** Every Text node in a drawn pane whose visible text contains the needle. */
const textNodesWith=async(pane,needle)=>{
  const found=[];
  const walk=node=>{ if(node && typeof node==='object'){ if(node.type==='Text' && visibleText(node).includes(needle)) found.push(node); (node.children??[]).forEach(walk); } };
  walk(await pane.drawn());
  return found;
};
test('a long path with CJK characters and spaces is drawn as a wrapping row, with its branch whole',async($,on)=>{
  const path='/repo/工作 樹/'+'資料夾 '.repeat(6)+'feat-x';
  const h=host(on,{cwd:()=>path,git:()=>linked('feat/x')});
  await begin($);
  await h.clock.advance(1000);
  const pane=await $.ui.mount(paneTarget());
  const rows=await textNodesWith(pane,path);
  expect(rows.length).toBeGreaterThan(0);
  expect(rows.every(node=>node.props?.wrap==='wrap')).toBe(true);
  expect(await renderedText(pane)).toContain(path);
  expect(await renderedText(pane)).toContain('feat/x');
});

// The inline pane is declared with rows:18 in register.js (ui.open); the need-you line must land inside that height.
const INLINE_ROWS=18;
test('worst inline case: a 120-character path, three inputs and five subagents keep the need-you line above the inputs',()=>{
  let s=createState('s');
  for(const [id,at] of [['a',0],['b',60000],['c',120000]]) s=reduceState(s,{type:'external-input',entry:{id,kind:'hook 注入',origin:'引擎',excerpt:`text-${id}`},sessionId:'s',epoch:s.epoch,at});
  s=reduceState(s,{type:'wait-start',kind:'question',id:'q',at:130000});
  const path='/repo/'+'a'.repeat(114);
  expect(path.length).toBe(120);
  const agents=agentsView({list:[1,2,3,4,5].map(n=>agent(`r${n}`,'running'))},0,new Map());
  const extras={worktree:{path,branch:'feat/x'},agents};
  const view=paneRows(s,0,extras);
  const lines=paneLines(s,0,extras);
  const lineAt=prefix=>lines.findIndex(l=>l.startsWith(prefix));
  expect(inlineFields(view).map(f=>f.label)).toEqual(['目標','脈絡','動作','證據','需要你','工作樹','子代理']);
  expect(lineAt('需要你：')).toBeGreaterThan(lineAt('動作：'));
  expect(lineAt('需要你：')).toBeLessThan(lineAt('外部輸入：'));
  expect(lineAt('需要你：')).toBeLessThan(INLINE_ROWS);
  // Title, blank, one line per field, the inputs label with its rows and gap note, a blank, then the footer.
  const inputs=sectionById(view,'inputs');
  const inputLines=1+inputs.rows.reduce((n,r)=>n+(r.excerpt ? 2 : 1),0)+inputs.notes.length;
  expect(lines.length).toBe(2+inlineFields(view).length+inputLines+1+footerNotes(view).length);
});

test('the inline layout shows the subagent count without the button',async($,on)=>{
  const h=host(on,{cwd:()=>CWD,agents:()=>[agent('r1','running')]});
  await begin($);
  await h.clock.advance(1000);
  const pane=await $.ui.mount(paneTarget('terminal','inline'));
  expect(await buttonKeys(pane)).not.toContain('toggle-agents');
  expect(await renderedText(pane)).toContain('子代理：1 個執行中');
});
