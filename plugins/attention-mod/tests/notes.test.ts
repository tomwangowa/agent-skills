import {test,expect} from 'claude-code/testing';
import {NOTE_LIMIT,IDLE_MS,RETRY_MS,createNotes,keyFor,beginRead,loaded,loadFailed,edit,nextSave,saveStarted,saveSettled,switchKey} from '../hooks/notes.js';

const ready=(text='',key='k')=>loaded(beginRead(createNotes(),key),key,text);

test('the key is the common dir when there is one, the cwd otherwise, and nothing without a read', ()=>{
  expect(keyFor({commonDir:'/r/.git',cwd:'/x'})).toBe('notes:/r/.git');
  expect(keyFor({commonDir:null,cwd:'/x'})).toBe('notes-cwd:/x');
  expect(keyFor(null)).toBeNull();
});

test('nothing is saved while the stored text is still being read, even when forced', ()=>{
  const typing=edit(beginRead(createNotes(),'k'),'draft',0);
  expect(nextSave(typing,5000,false).action).toBe('none');
  expect(nextSave(typing,5000,true).action).toBe('none');
});

test('an unset key loads as an empty note, and a value that is not a string fails the read', ()=>{
  expect(loaded(beginRead(createNotes(),'k'),'k',undefined)).toMatchObject({status:'ready',text:''});
  expect(loaded(beginRead(createNotes(),'k'),'k','saved')).toMatchObject({status:'ready',text:'saved'});
  expect(loaded(beginRead(createNotes(),'k'),'k',42).status).toBe('read-failed');
});

test('a read result for another key changes nothing', ()=>{
  const reading=beginRead(createNotes(),'new');
  expect(loaded(reading,'old','stale')).toEqual(reading);
  expect(loadFailed(reading,'old')).toEqual(reading);
});

test('an idle edit is saved only after one second without another edit', ()=>{
  expect(IDLE_MS).toBe(1000);
  const typed=edit(ready(),'a',0);
  expect(nextSave(typed,999,false).action).toBe('none');
  expect(nextSave(typed,1000,false)).toMatchObject({action:'save',value:'a'});
});

test('a forced save ignores the idle second', ()=>{
  expect(nextSave(edit(ready(),'a',0),0,true)).toMatchObject({action:'save',value:'a'});
});

test('the limit counts code points: exactly 32,768 saves, one more is refused and marked too long', ()=>{
  const max='a'.repeat(NOTE_LIMIT-1)+'😀';
  expect([...max].length).toBe(NOTE_LIMIT);
  expect(nextSave(edit(ready(),max,0),1000,false).action).toBe('save');
  const over=edit(ready(),max+'a',0);
  expect(nextSave(over,1000,false).action).toBe('refuse');
  expect(over.saveError).toBe('too-long');
  expect(edit(over,max,0).saveError).toBeNull();
});

test('clearing the note deletes the key', ()=>{
  expect(nextSave(edit(ready('a'),'',0),1000,false).action).toBe('delete');
});

test('a second write waits while one is in flight', ()=>{
  const inFlight=saveStarted(edit(ready(),'a',0),'a');
  expect(nextSave(inFlight,5000,true).action).toBe('none');
});

test('a failed write waits five seconds before the next try', ()=>{
  expect(RETRY_MS).toBe(5000);
  const failed=saveSettled(saveStarted(edit(ready(),'a',0),'a'),'a',false,1000);
  expect(failed.saveError).toBe('failed');
  expect(failed.retryAt).toBe(1000+RETRY_MS);
  expect(failed.dirty).toBe(true);
  expect(nextSave(failed,1000+RETRY_MS-1,false).action).toBe('none');
  expect(nextSave(failed,1000+RETRY_MS,false).action).toBe('save');
});

test('a write that lands after a newer edit keeps the note dirty; one that matches clears it', ()=>{
  const edited=edit(saveStarted(edit(ready(),'a',0),'a'),'ab',500);
  expect(saveSettled(edited,'a',true,600).dirty).toBe(true);
  expect(saveSettled(edit(ready(),'a',0),'a',true,600).dirty).toBe(false);
});

test('switching key flushes the old note only when it has unsaved text', ()=>{
  const r=switchKey(edit(ready('x','old'),'x2',0),'new');
  expect(r.flush).toEqual({key:'old',text:'x2'});
  expect(r.notes).toMatchObject({status:'idle',key:'new'});
  expect(switchKey(ready('x','old'),'new').flush).toBeNull();
});
