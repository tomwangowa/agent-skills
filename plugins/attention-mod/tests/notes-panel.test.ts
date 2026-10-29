import {test,expect} from 'claude-code/testing';
import {host,begin,paneTarget,renderedText} from './fixtures.js';

const CWD='/repo/worktrees/feat-x';
const linked=(commonDir='/repo/.git')=>({exitCode:0,stdout:`/repo/.git/worktrees/x\n${commonDir}\nfeat/x\n`,stderr:''});
const deferred=()=>{ let resolve; const promise=new Promise(r=>{ resolve=r; }); return {promise,resolve}; };
/** Page three, where Quick Notes lives. */
const pageThree=async pane=>{ await pane.press({key:'page-3'}); return pane; };
/** The props of every Input node in a drawn pane, in tree order. */
const inputProps=async pane=>{
  const found=[];
  const walk=node=>{ if(node && typeof node==='object'){ if(node.type==='Input') found.push(node.props); (node.children??[]).forEach(walk); } };
  walk(await pane.drawn());
  return found;
};

test('the note input stays unmounted until the stored note has been read, then opens empty',async($,on)=>{
  const read=deferred();
  const h=host(on,{cwd:()=>CWD,git:()=>linked(),store:()=>read.promise});
  await begin($);
  await h.clock.settle();
  const pane=await pageThree(await $.ui.mount(paneTarget('terminal','inline')));
  expect(await renderedText(pane)).toContain('讀取中');
  expect((await inputProps(pane)).filter(p=>p.key==='attention-notes')).toEqual([]);
  read.resolve(undefined);
  await h.clock.settle();
  expect(await renderedText(pane)).not.toContain('讀取中');
  const [note]=(await inputProps(pane)).filter(p=>p.key==='attention-notes');
  expect(note.value).toBe('');
  expect(note.autoFocus).toBeUndefined();
});

test('a stored note reads into the input as its saved text',async($,on)=>{
  const h=host(on,{cwd:()=>CWD,git:()=>linked(),store:()=>'saved text'});
  await begin($);
  await h.clock.settle();
  const pane=await pageThree(await $.ui.mount(paneTarget('terminal','inline')));
  const [note]=(await inputProps(pane)).filter(p=>p.key==='attention-notes');
  expect(note.value).toBe('saved text');
});

test('a stored value that is not text shows the read failure, and retry reads the store again',async($,on)=>{
  const h=host(on,{cwd:()=>CWD,git:()=>linked(),store:()=>42});
  await begin($);
  await h.clock.settle();
  const pane=await pageThree(await $.ui.mount(paneTarget('terminal','inline')));
  expect(await renderedText(pane)).toContain('讀取失敗');
  expect((await inputProps(pane)).filter(p=>p.key==='attention-notes')).toEqual([]);
  await pane.press({key:'retry-notes'});
  await h.clock.settle();
  expect(h.record.stored).toEqual(['notes:/repo/.git','notes:/repo/.git']);
});

test('a store read that throws shows the read failure with a retry',async($,on)=>{
  const h=host(on,{cwd:()=>CWD,git:()=>linked(),store:()=>{ throw new Error('store unavailable'); }});
  await begin($);
  await h.clock.settle();
  const pane=await pageThree(await $.ui.mount(paneTarget('terminal','inline')));
  expect(await renderedText(pane)).toContain('讀取失敗');
  expect(await renderedText(pane)).toContain('重試');
});

test('an unreadable git read shows the read failure and never reads the store',async($,on)=>{
  const h=host(on,{cwd:()=>CWD,git:async()=>{ throw new Error('spawn failed'); }});
  await begin($);
  await h.clock.settle();
  const pane=await pageThree(await $.ui.mount(paneTarget('terminal','inline')));
  expect(await renderedText(pane)).toContain('讀取失敗');
  expect(h.record.stored).toEqual([]);
});

test('outside git the note is keyed by its directory',async($,on)=>{
  const h=host(on,{cwd:()=>CWD,git:()=>({exitCode:128,stdout:'',stderr:'fatal: not a git repository'}),store:()=>undefined});
  await begin($);
  await h.clock.settle();
  expect(h.record.stored).toEqual([`notes-cwd:${CWD}`]);
});

test('inside git the note is keyed by the common dir, which every worktree of the repository shares',async($,on)=>{
  const h=host(on,{cwd:()=>CWD,git:()=>linked('/repo/.git'),store:()=>undefined});
  await begin($);
  await h.clock.settle();
  expect(h.record.stored).toEqual(['notes:/repo/.git']);
});

test('a directory change re-keys the note within two ticks, while the worktree row keeps waiting for the next turn',async($,on)=>{
  let here=CWD;
  let common='/repo/.git';
  const h=host(on,{cwd:()=>here,git:()=>linked(common),store:()=>undefined});
  await begin($);
  await h.clock.advance(1000);
  expect(h.record.stored).toEqual(['notes:/repo/.git']);
  here='/other/worktree';
  common='/other/.git';
  await h.clock.advance(2000);
  expect(h.record.stored).toContain('notes:/other/.git');
  const pane=await $.ui.mount(paneTarget('terminal','inline'));
  await pane.press({key:'page-2'});
  expect(await renderedText(pane)).toContain('待下一回合更新');
});

/** Types into the Quick Notes input the way the person would: `change` on each edit, `submit` on Enter. */
const typeNote=(pane,text,kind='change')=>pane.input({key:'attention-notes',text,kind});

test('an idle edit is saved on the first tick a second after it, not before',async($,on)=>{
  const h=host(on,{cwd:()=>CWD,git:()=>linked(),store:()=>undefined});
  await begin($);
  await h.clock.settle();
  const pane=await pageThree(await $.ui.mount(paneTarget('terminal','inline')));
  await typeNote(pane,'draft');
  await h.clock.advance(999);
  expect(h.record.sets).toEqual([]);
  await h.clock.advance(1);
  expect(h.record.sets).toEqual([{key:'notes:/repo/.git',value:'draft'}]);
});

test('Enter saves at once, without waiting for the timer',async($,on)=>{
  const h=host(on,{cwd:()=>CWD,git:()=>linked(),store:()=>undefined});
  await begin($);
  await h.clock.settle();
  const pane=await pageThree(await $.ui.mount(paneTarget('terminal','inline')));
  await typeNote(pane,'hello','submit');
  expect(h.record.sets).toEqual([{key:'notes:/repo/.git',value:'hello'}]);
});

test('a note of exactly 32,768 code points is saved, and one more is held back with a notice, not cut',async($,on)=>{
  const h=host(on,{cwd:()=>CWD,git:()=>linked(),store:()=>undefined});
  await begin($);
  await h.clock.settle();
  const pane=await pageThree(await $.ui.mount(paneTarget('terminal','inline')));
  const exact='😀'.repeat(32768);
  await typeNote(pane,exact,'submit');
  expect(h.record.sets).toEqual([{key:'notes:/repo/.git',value:exact}]);
  await typeNote(pane,exact+'😀','submit');
  expect(h.record.sets.length).toBe(1);
  expect(await renderedText(pane)).toContain('未存：超過上限');
});

test('a write that fails shows 未存, waits five seconds, then tries again',async($,on)=>{
  const h=host(on,{cwd:()=>CWD,git:()=>linked(),store:()=>undefined,storeWriteFails:true});
  await begin($);
  await h.clock.settle();
  const pane=await pageThree(await $.ui.mount(paneTarget('terminal','inline')));
  await typeNote(pane,'draft','submit');
  expect(await renderedText(pane)).toContain('未存：寫入失敗');
  const attempts=()=>h.record.ops.filter(op=>op.startsWith('set ')).length;
  const before=attempts();
  await h.clock.advance(4999);
  expect(attempts()).toBe(before);
  await h.clock.advance(1);
  expect(attempts()).toBe(before+1);
});

test('clearing the note deletes its key instead of storing an empty string',async($,on)=>{
  const h=host(on,{cwd:()=>CWD,git:()=>linked(),store:()=>undefined});
  await begin($);
  await h.clock.settle();
  const pane=await pageThree(await $.ui.mount(paneTarget('terminal','inline')));
  await typeNote(pane,'draft','submit');
  await typeNote(pane,'','submit');
  expect(h.record.deletes).toEqual(['notes:/repo/.git']);
  expect(h.record.sets.length).toBe(1);
});

test('leaving page three saves the unsaved note first',async($,on)=>{
  const h=host(on,{cwd:()=>CWD,git:()=>linked(),store:()=>undefined});
  await begin($);
  await h.clock.settle();
  const pane=await pageThree(await $.ui.mount(paneTarget('terminal','inline')));
  await typeNote(pane,'draft');
  await pane.press({key:'page-1'});
  expect(h.record.sets).toEqual([{key:'notes:/repo/.git',value:'draft'}]);
});

test('a directory change saves the unsaved note under its own key before the new key is read',async($,on)=>{
  let here=CWD;
  let common='/repo/.git';
  const h=host(on,{cwd:()=>here,git:()=>linked(common),store:()=>undefined});
  await begin($);
  await h.clock.settle();
  const pane=await pageThree(await $.ui.mount(paneTarget('terminal','inline')));
  await typeNote(pane,'draft');
  here='/other/worktree';
  common='/other/.git';
  await h.clock.advance(2000);
  const setAt=h.record.ops.indexOf('set notes:/repo/.git');
  expect(setAt).toBeGreaterThanOrEqual(0);
  expect(h.record.ops.indexOf('get notes:/other/.git')).toBeGreaterThan(setAt);
});

test('a note too long to save holds the directory switch, so its text is not dropped',async($,on)=>{
  let here=CWD;
  let common='/repo/.git';
  const h=host(on,{cwd:()=>here,git:()=>linked(common),store:()=>undefined});
  await begin($);
  await h.clock.settle();
  const pane=await pageThree(await $.ui.mount(paneTarget('terminal','inline')));
  await typeNote(pane,'😀'.repeat(32769));
  here='/other/worktree';
  common='/other/.git';
  await h.clock.advance(2000);
  expect(h.record.ops.some(op=>op.startsWith('get notes:/other'))).toBe(false);
  expect(await renderedText(pane)).toContain('未存：超過上限');
});

test('a note that could not be read is never written, even as the timer keeps running',async($,on)=>{
  const h=host(on,{cwd:()=>CWD,git:()=>linked(),store:()=>{ throw new Error('store unavailable'); }});
  await begin($);
  await h.clock.settle();
  await h.clock.advance(10000);
  expect(h.record.sets).toEqual([]);
  expect(h.record.deletes).toEqual([]);
});

test('a failed write does not replace the too-long notice when the person pasted over the limit mid-write',async($,on)=>{
  const gate=deferred();
  const h=host(on,{cwd:()=>CWD,git:()=>linked(),store:()=>undefined,storeWrite:async()=>{ await gate.promise; throw new Error('store write failed'); }});
  await begin($);
  await h.clock.settle();
  const pane=await pageThree(await $.ui.mount(paneTarget('terminal','inline')));
  await typeNote(pane,'draft','submit');
  await typeNote(pane,'😀'.repeat(32769));
  gate.resolve();
  await h.clock.settle();
  const shown=await renderedText(pane);
  expect(shown).toContain('未存：超過上限');
  expect(shown).not.toContain('寫入失敗');
});

test('ending the session saves the unsaved note before the panel goes quiet',async($,on)=>{
  const h=host(on,{cwd:()=>CWD,git:()=>linked(),store:()=>undefined});
  await begin($);
  await h.clock.settle();
  const pane=await pageThree(await $.ui.mount(paneTarget('terminal','inline')));
  await typeNote(pane,'draft');
  await $.session.end({reason:'exit',sessionId:'session-one',resume:{}});
  expect(h.record.sets).toEqual([{key:'notes:/repo/.git',value:'draft'}]);
});
