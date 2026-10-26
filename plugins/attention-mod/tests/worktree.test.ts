import {test,expect} from 'claude-code/testing';
import {GIT_ARGS,GIT_TIMEOUT_MS,FAILED_READ,parseWorktree,worktreeView} from '../hooks/worktree.js';

const LINKED='/repo/.git/worktrees/x\n/repo/.git\nfeat/x\n';
const MAIN='/repo/.git\n/repo/.git\nmain\n';
const DETACHED='/repo/.git/worktrees/x\n/repo/.git\nHEAD\n';
const CWD='/repo/worktrees/x';
const linkedRead=patch=>({cwd:CWD,state:'linked',branch:'feat/x',detached:false,...patch});

test('the git read is the one read-only command, with a two-second budget', ()=>{
  expect(GIT_ARGS).toEqual(['git','--no-optional-locks','rev-parse','--path-format=absolute','--git-dir','--git-common-dir','--abbrev-ref','HEAD']);
  expect(GIT_TIMEOUT_MS).toBe(2000);
});

test('parseWorktree tells a linked worktree, the main checkout and a detached HEAD apart', ()=>{
  expect(parseWorktree(LINKED,0)).toEqual({state:'linked',branch:'feat/x',detached:false});
  expect(parseWorktree(MAIN,0)).toEqual({state:'main',branch:'main',detached:false});
  expect(parseWorktree(DETACHED,0)).toEqual({state:'linked',branch:null,detached:true});
});

test('a relative path in the output is unreadable, never guessed; the main checkout subdirectory is main', ()=>{
  // Without --path-format=absolute, git prints ../.git from a subdirectory of the main checkout, and that must not read as linked.
  expect(parseWorktree('/repo/.git\n../.git\nmain\n',0)).toEqual(FAILED_READ);
  expect(parseWorktree('.git\n.git\nmain\n',0)).toEqual(FAILED_READ);
  expect(parseWorktree('/repo/.git\n/repo/.git\nmain\n',0)).toEqual({state:'main',branch:'main',detached:false});
});

test('a trailing newline or an extra line does not change the three fields read', ()=>{
  expect(parseWorktree(LINKED+'\n',0)).toEqual({state:'linked',branch:'feat/x',detached:false});
  expect(parseWorktree(LINKED+'extra\n',0)).toEqual({state:'linked',branch:'feat/x',detached:false});
});

test('exit 128 means not a repository; other failures and short output are unreadable', ()=>{
  expect(parseWorktree('',128)).toEqual({state:'not-git',branch:null,detached:false});
  expect(parseWorktree('',1)).toEqual(FAILED_READ);
  expect(parseWorktree('/repo/.git\n/repo/.git\n',0)).toEqual(FAILED_READ);
});

test('worktreeView shows nothing without a read, without a cwd, or outside a linked worktree', ()=>{
  expect(worktreeView(null,CWD)).toBeNull();
  expect(worktreeView(linkedRead(),null)).toBeNull();
  expect(worktreeView({cwd:CWD,state:'main',branch:'main',detached:false},CWD)).toBeNull();
  expect(worktreeView({cwd:CWD,state:'not-git',branch:null,detached:false},CWD)).toBeNull();
});

test('worktreeView gives the full path with the branch, the detached label, or the unreadable label', ()=>{
  expect(worktreeView(linkedRead(),CWD)).toEqual({path:CWD,branch:'feat/x'});
  expect(worktreeView(linkedRead({branch:null,detached:true}),CWD)).toEqual({path:CWD,branch:'分離 HEAD'});
  expect(worktreeView(linkedRead({state:'unreadable',branch:null}),CWD)).toEqual({path:CWD,branch:'無法讀取'});
});

test('a directory change shows the waiting label and never the old branch', ()=>{
  expect(worktreeView(linkedRead(),'/repo/worktrees/y')).toEqual({path:'/repo/worktrees/y',branch:'待下一回合更新'});
});

test('a long path with CJK characters and spaces comes back whole', ()=>{
  const long='/repo/工作 樹/'+'x'.repeat(100);
  expect(worktreeView(linkedRead({cwd:long}),long).path).toBe(long);
});
