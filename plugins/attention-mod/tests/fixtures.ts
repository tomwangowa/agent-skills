import {mock} from 'claude-code/testing';

export const paneTarget=(surface='terminal',placement='dock',requestId='attention-mod')=>({plugin:'attention-mod',surface,component:'Pane',requestId,viewport:{columns:140,rows:40},props:{title:'Attention',isFocused:false,bodyColumns:40,placement,scroll:{offset:0,bodyRows:20},view:{}}});

/** Stub the native host before the test's first dispatch. */
export function host(on, options={}) {
  const clock=mock.clock(on);
  // `ops` keeps reads and writes in the order they happened, so a test can check one came before another.
  const record={opens:[],prompts:[],models:[],commands:[],closes:[],statuses:[],usage:[],stored:[],sets:[],deletes:[],ops:[]};
  let sessionId='session-one';
  on('session.id',()=>({value:sessionId}));
  on('session.messages',()=>options.readMessages ? options.readMessages() : {value:options.messages ?? []});
  on('command.register',($,e)=>{record.commands.push(e);return {value:{command:e.name}};});
  on('ui.open',($,e)=>{record.opens.push(e);return {value:{isPlaced:true}};});
  on('session.start',($,e)=>({cwd:e.cwd}));
  on('session.end',($,e)=>({sessionId:e.sessionId}));
  on('prompt.submit',($,e)=>{record.prompts.push(e);return options.submit ? options.submit(e) : {text:e.text};});
  on('command.run',()=>({}));
  on('tool.call',($,e)=>options.tool ? options.tool(e) : {result:'fixture-output'});
  // Allow by default. In the runtime we tested, an 'ask' is denied at once, so the call never shows as running.
  on('tool.check',()=>({decision:options.check?.() ?? 'allow'}));
  on('turn.start',()=>({turnId:'turn-one'}));
  on('turn.complete',()=>({text:''}));
  // The panel's own reads. The defaults hide the worktree and subagent rows, so tests that do not ask for them keep the 0.2.0 layout.
  on('process.run',async($,e)=>({value:options.git ? await options.git(e) : {exitCode:128,stdout:'',stderr:'fatal: not a git repository'}}));
  on('session.cwd',async()=>({value:options.cwd ? await options.cwd() : '/repo/worktrees/feat-x'}));
  on('agent.list',async()=>({value:options.agents ? await options.agents() : null}));
  on('ui.close',($,e)=>{record.closes.push(e.id);return {value:undefined};});
  on('ui.status',($,e)=>{record.statuses.push(e.text);return {value:undefined};});
  on('ui.render',($,e)=>e.component === 'AskUserQuestion' ? {type:'engine',ref:1} : $.ui.resolve(e).Text({children:'native-component'}));
  on('model.complete',($,e)=>{record.models.push({request:e,at:clock.now()});return options.model ? options.model(e) : {value:{isAnswered:false,reason:'empty-reply',usage:{}}};});
  // The session reads of page two. Defaults: a model name, no rate-limit reading, no context breakdown.
  // `usage` may be a function, so a test can make a later read fail.
  on('session.model',()=>{ if(options.modelFails) throw new Error('model read failed'); return {value:options.sessionModel ?? 'claude-haiku-5-5'}; });
  on('session.usage',($,e)=>{ record.usage.push(e); const usage = typeof options.usage === 'function' ? options.usage() : options.usage; return {value:usage ?? {startedAt:0, context:{window:200000}, rateLimits:[]}}; });
  // Quick Notes' store, as a test host: `store` answers a read of one key; the keys read are recorded.
  on('store.get', async ($, e) => { record.stored.push(e.key); record.ops.push(`get ${e.key}`); return {value: options.store ? await options.store(e.key) : undefined}; });
  // `storeWriteFails` makes every write reject, so a test can see the panel report it. An attempt is recorded in `ops` before the rejection, so a test can count retries.
  // `storeWrite` runs before each write and may hold it open or reject it, so a test can edit the note while a write is in flight.
  on('store.set', async ($, e) => { record.ops.push(`set ${e.key}`); if (options.storeWrite) await options.storeWrite(e.key); if (options.storeWriteFails) throw new Error('store write failed'); record.sets.push({key:e.key, value:e.value}); return {value:undefined}; });
  on('store.delete', ($, e) => { record.ops.push(`delete ${e.key}`); if (options.storeWriteFails) throw new Error('store write failed'); record.deletes.push(e.key); return {value:undefined}; });
  // The bottom of the turn.step chain: an empty reply, so a test only sees what the panel's hook recorded.
  on('turn.step', async function*($,e){ return {turnId:e.turnId, index:e.index, text:'', answer:'', toolUses:[], stopReason:'end_turn', usage:null}; });
  return {clock,record,setSession:id=>{sessionId=id;}};
}

export const begin=$=>$.session.start({cwd:'/fixture',surface:'terminal',isInteractive:true});
export const prompt=($,text)=>$.prompt.submit({text,wait:false,origin:{kind:'composer'}});
export const append=($,id,text)=>$.tool.call({tool:'Bash',command:text,tool_use_id:id});
/** Flatten each drawn row to its visible text, so styled label/value spans still read as one line. */
const rowText=node=>typeof node==='string' ? node : node?.type==='Button' ? node.props.label : (node?.children ?? []).map(rowText).join(node?.type==='Box' ? '\n' : '');
export const renderedText=async mounted=>rowText(await mounted.drawn());
