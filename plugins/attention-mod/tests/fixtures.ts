import {mock} from 'claude-code/testing';

export const paneTarget=(surface='terminal',placement='dock',requestId='attention-mod')=>({plugin:'attention-mod',surface,component:'Pane',requestId,viewport:{columns:140,rows:40},props:{title:'Attention',isFocused:false,bodyColumns:40,placement,scroll:{offset:0,bodyRows:20},view:{}}});

/** Stub the native host before the test's first dispatch. */
export function host(on, options={}) {
  const clock=mock.clock(on);
  const record={opens:[],prompts:[],models:[],commands:[],closes:[],statuses:[]};
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
  return {clock,record,setSession:id=>{sessionId=id;}};
}

export const begin=$=>$.session.start({cwd:'/fixture',surface:'terminal',isInteractive:true});
export const prompt=($,text)=>$.prompt.submit({text,wait:false,origin:{kind:'composer'}});
export const append=($,id,text)=>$.tool.call({tool:'Bash',command:text,tool_use_id:id});
/** Flatten each drawn row to its visible text, so styled label/value spans still read as one line. */
const rowText=node=>typeof node==='string' ? node : node?.type==='Button' ? node.props.label : (node?.children ?? []).map(rowText).join(node?.type==='Box' ? '\n' : '');
export const renderedText=async mounted=>rowText(await mounted.drawn());
