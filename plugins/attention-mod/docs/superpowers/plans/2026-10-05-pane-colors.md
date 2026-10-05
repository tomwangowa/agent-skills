# Pane Colors (0.3.0) Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Colour the attention pane: three round-bordered sections in the dock, coloured labels and status dots in the flat inline layout, with the live section turning green / yellow / terminal default by state.

**Architecture:** `hooks/view.js` returns semantic sections (tones, not colours). A new pure `hooks/theme.js` maps tones to named terminal colours. `hooks/register.js` picks `drawDock` or `drawInline` by `e.props.placement` and only adds the close button.

**Tech Stack:** Claude Code 2.1.288+ mod, plain ES modules, `claude-code/testing`.

**Spec:** `docs/superpowers/specs/2026-10-05-pane-colors-design.md` (approved 2026-10-05). Branch: `feat/pane-colors`.

---

## Ground rules

- `claude plugin test .` runs every suite (no filter). Baseline on this branch: **63 pass, 0 fail**.
- Also run `claude plugin validate --strict .` and `node --check hooks/<file>.js`. No `tsc`.
- **Do not commit inside tasks.** Tom approves every commit (Task 4).
- Mod static analysis: pass `$` only to top-level functions; element constructors from `$.ui.resolve(e)` are plain values and may be passed anywhere.
- `tests/fixtures.ts` `paneTarget()` defaults to `placement:'dock'`, so after this change every existing `paneTarget()` mount draws the bordered layout.
- If `claude plugin test` says hooks modules are turned off, run `claude -p "ok"` once and retry.

## File map

| File | Change | Responsibility |
| --- | --- | --- |
| `hooks/theme.js` | Create | Tone → named colour |
| `hooks/view.js` | Modify | Sections with tones; `liveTone`, `actionDot`, `inlineFields`, `footerNotes`; `paneLines` from sections |
| `hooks/register.js` | Modify | `drawDock`, `drawInline`, Pane handler split by placement |
| `tests/theme.test.ts` | Create | Mapping tests |
| `tests/view.test.ts` | Modify | Section shape, tone rules |
| `tests/integration.test.ts` | Modify | Dock boxes and colours, inline labels, layout parity |
| `README.md`, `.claude/CLAUDE.md`, `docs/prototype-results.md`, `.claude-plugin/plugin.json`, `package.json` | Modify | Docs and version 0.3.0 |

---

### Task 0: Colour micro-PoC (needs Tom)

Proves that `borderStyle:'round'`, named colours, `dimColor` and a left/right header row actually render, before the real change.

- [ ] **Step 1: Write the probe mod** under the session scratchpad, `<scratchpad>/color-poc/`:

`.claude-plugin/plugin.json`
```json
{ "name": "color-poc", "version": "0.0.1", "description": "Colour and border probe", "author": { "name": "Tom Wang" } }
```
`hooks/hooks.json`
```json
{ "modules": ["./register.js"] }
```
`hooks/register.js`
```js
const COLORS = ['blue', 'green', 'yellow', 'red', 'gray', 'magenta'];

export function register(on) {
  on('session.start', async ($, e, next) => {
    const result = await next(e);
    try {
      await $.command.register({name:'color-poc', description:'Open the colour probe pane', immediate:true});
      if (e.isInteractive) await $.ui.open({id:'color-poc', title:'color poc', rows:24, columns:48});
    } catch {}
    return result;
  });
  on('command.run', {command:'color-poc'}, async ($) => {
    await $.ui.open({id:'color-poc', title:'color poc', rows:24, columns:48});
    return {};
  });
  on('ui.render', {component:'Pane', requestId:'color-poc'}, ($, e) => {
    const {Box, Text} = $.ui.resolve(e);
    return Box({flexDirection:'column', children:[
      Text({children:`placement=${e.props.placement} bodyColumns=${e.props.bodyColumns}`}),
      ...COLORS.map(c => Box({borderStyle:'round', borderColor:c, paddingX:1, flexDirection:'row', justifyContent:'space-between', children:[
        Text({bold:true, color:c, children:`[ ${c} ]`}),
        Text({dimColor:true, children:'meta right'}),
      ]})),
      Box({borderStyle:'single', paddingX:1, children:[Text({children:'single border fallback'})]}),
      Text({children:[Text({color:'green', children:'● '}), Text({bold:true, color:'blue', children:'目標：'}), 'plain text']}),
    ]});
  });
}
```

- [ ] **Step 2:** `claude plugin validate --strict <scratchpad>/color-poc` → `✔ Validation passed`.
- [ ] **Step 3: Tom runs** `claude --plugin-dir <scratchpad>/color-poc` once in a wide terminal (dock) and once in a terminal under 100 columns (inline; `/color-poc` reopens the pane), and sends screenshots.
- [ ] **Step 4: Record** in `docs/prototype-results.md` (Task 3) which of round border, each named colour, `dimColor`, and space-between rendered. If `round` fails, replace `'round'` with `'single'` everywhere in this plan; if a colour name fails, change only `hooks/theme.js`.

---

### Task 1: Tone → colour module

**Files:** Create `hooks/theme.js`, `tests/theme.test.ts`.

- [ ] **Step 1: Failing test** — `tests/theme.test.ts`:
```ts
import {test, expect} from 'claude-code/testing';
import {colorFor} from '../hooks/theme.js';

test('each semantic tone maps to a named terminal colour, muted to the terminal default', () => {
  expect(['accent','success','warning','danger','muted','input'].map(colorFor)).toEqual(['blue','green','yellow','red',undefined,'magenta']);
});
test('unknown tones fall back to the terminal default instead of throwing', () => {
  expect(colorFor('sparkly')).toBe(undefined);
  expect(colorFor(undefined)).toBe(undefined);
  expect(colorFor('toString')).toBe(undefined);
});
```
- [ ] **Step 2:** `claude plugin test .` → `theme.test.ts` fails to load; 63 pass.
- [ ] **Step 3: Implement** `hooks/theme.js`:
```js
/** Named terminal colours, so the pane follows the user's theme instead of fixed hex values. */
// muted is left out on purpose: gray vanished on the dock's gray background in the 2026-10-05 PoC, so it uses the terminal default.
const COLORS = {accent:'blue', success:'green', warning:'yellow', danger:'red', input:'magenta'};

/** Colour for a semantic tone; unknown tones return undefined, which draws in the terminal default. */
export function colorFor(tone) {
  return Object.hasOwn(COLORS, tone) ? COLORS[tone] : undefined;
}
```
- [ ] **Step 4:** `claude plugin test .` → **65 pass, 0 fail**; `node --check hooks/theme.js` clean.

---

### Task 2: Sections in view.js and the two drawings in register.js

These change together: `register.js` reads the old `paneRows` shape, so both move in one task.

**Files:** Modify `hooks/view.js` (whole file below), `hooks/register.js` (imports, two new top-level functions, Pane handler), `tests/view.test.ts`, `tests/integration.test.ts`.

- [ ] **Step 1: Update existing view tests** (`tests/view.test.ts`):
  - Change the view import to `import {paneLines,paneRows,clockTime,liveTone,actionDot,inlineFields,footerNotes} from '../hooks/view.js';`
  - Replace the body of `'pane rows expose the question title and each field label apart from its value'` with:
```ts
  const view=paneRows(createState('s'),0);
  expect(view.title).toBe('你到底在忙什麼？');
  expect(view.sections.map(s=>s.label)).toEqual(['摘要','即時','外部輸入']);
  expect(inlineFields(view).map(f=>f.label)).toEqual(['目標','脈絡','動作','證據','需要你']);
  expect(inlineFields(view)[0].text).toBe('目的尚不清楚');
```
  - In `'external inputs list newest first...'`: replace `const {inputs}=paneRows(s,0);` with `const inputs=paneRows(s,0).sections[2];`, replace every `inputs.items` with `inputs.rows`, and add `expect(inputs.meta).toBe('4 筆');` after the label assertion.
  - In `'empty inputs say when recording started...'`: replace `paneRows(createState('s'),0).inputs.empty` with `paneRows(createState('s'),0).sections[2].empty`.
  - In the carried-row test: replace `paneRows(s,0).inputs.items` with `paneRows(s,0).sections[2].rows` (both occurrences).

- [ ] **Step 2: New view tests** (append to `tests/view.test.ts`):
```ts
test('live tone puts a wait ahead of a running tool, and the action dot shows the last failure',()=>{
  let s=createState('s');
  expect(liveTone(s)).toBe('muted');
  expect(actionDot(s)).toBe('muted');
  s=reduceState(s,{type:'tool-start',epoch:s.epoch,id:'t',tool:'Bash',label:'t',at:0});
  expect(liveTone(s)).toBe('success');
  expect(actionDot(s)).toBe('success');
  s=reduceState(s,{type:'wait-start',kind:'question',id:'q',at:0});
  expect(liveTone(s)).toBe('warning');
  s=reduceState(s,{type:'tool-end',id:'t',epoch:s.epoch,status:'error',at:1});
  expect(liveTone(s)).toBe('warning');
  expect(actionDot(s)).toBe('danger');
  s=reduceState(s,{type:'wait-end',id:'q',at:2});
  expect(liveTone(s)).toBe('muted');
  expect(paneRows(s,0).sections[1].rows.map(r=>r.dot)).toEqual(['danger','muted']);
});
test('needs-you dot is yellow only while something waits',()=>{
  let s=reduceState(createState('s'),{type:'wait-unknown',at:0});
  expect(paneRows(s,0).sections[1].rows[1].dot).toBe('muted');
  s=reduceState(s,{type:'wait-start',kind:'question',id:'q',at:0});
  expect(paneRows(s,0).sections[1].rows[1].dot).toBe('warning');
});
test('meta and notes sit in the section they describe, and the flat footer keeps the 0.2.0 order',()=>{
  const s={...createState('s'),revision:2,summaryRevision:1,snapshotAt:1000,lastEventAt:5000,summaryError:'request-failed',summary:{goal:{text:'g',sources:['s']},context:null,evidence:null}};
  const view=paneRows(s,21000);
  const [summary,live,inputs]=view.sections;
  expect(summary.meta).toBe('脈絡與證據更新：20 秒前');
  expect(summary.notes).toEqual([{text:'有新活動，摘要待更新',tone:'muted'},{text:'摘要更新失敗',tone:'danger'}]);
  expect(live.meta).toBe('距離最近事件：16 秒');
  expect(inputs.meta).toBe(null);
  expect(footerNotes(view).map(n=>n.text)).toEqual(['脈絡與證據更新：20 秒前','有新活動，摘要待更新','摘要更新失敗','距離最近事件：16 秒']);
});
```

- [ ] **Step 3: Integration tests** (`tests/integration.test.ts`):
  - Add after the imports:
```ts
/** Props of every bordered Box in a drawn pane, in tree order. */
const borderedBoxes=async pane=>{
  const found=[];
  const walk=node=>{ if(node && typeof node==='object'){ if(node.type==='Box' && node.props?.borderStyle) found.push(node.props); (node.children??[]).forEach(walk); } };
  walk(await pane.drawn());
  return found;
};
```
  - In `'pane closes permanently across updates...'`, replace `expect(await renderedText(pane)).toContain('你到底在忙什麼');` with `expect(await renderedText(pane)).toContain('目標：');` (the dock no longer draws the inner title).
  - Replace the whole test `'pane draws a bold question title, a rule sized to the body, and bold field labels'` with:
```ts
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
});
```
  - Append:
```ts
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
```

- [ ] **Step 4:** `claude plugin test .` → `view.test.ts` fails to load (missing exports) and the new/changed integration tests fail; record the counts.

- [ ] **Step 5: Replace `hooks/view.js`** with:
```js
/** Local wall-clock HH:MM for a clock reading in milliseconds; follows the host time zone. */
export function clockTime(ms) {
  const d = new Date(ms);
  return `${String(d.getHours()).padStart(2,'0')}:${String(d.getMinutes()).padStart(2,'0')}`;
}

/** Newest first; only the two newest keep an excerpt to limit pane height. */
export function inputRows(state) {
  const items = [...state.inputs].reverse().map((i, index) => ({text:`${clockTime(i.at)} ${i.kind} · ${i.origin}`, excerpt:index < 2 ? (i.excerpt ?? null) : null}));
  const empty = items.length ? null : state.inputsSince === null ? '尚無' : `尚無（${clockTime(state.inputsSince)} 起記錄）`;
  return {label:'外部輸入', empty, items};
}

const seconds = (now, at) => Math.max(0, Math.floor((now - at) / 1000));

/** Live-section tone: a wait outranks a running tool, because "needs you" is what a glance must catch. */
export function liveTone(state) {
  if (state.waits.length) return 'warning';
  if (state.activities.length) return 'success';
  return 'muted';
}

/** Action dot: a running tool, else a failed last tool, else quiet. */
export function actionDot(state) {
  if (state.activities.length) return 'success';
  if (state.lastTool?.status === 'error') return 'danger';
  return 'muted';
}

/** Observed state as sections; tones stay semantic so each layout picks its own colours. */
export function paneRows(state, now) {
  const summary = state.summary;
  const active = state.activities;
  let action = state.turnStatus === 'ended' ? '本回合已結束' : state.turnStatus === 'active' ? '本回合進行中，尚無執行中工具' : '尚未觀測到工作動作';
  if (active.length) action = active.length === 1 ? `正在執行 ${active[0].label}` : `共 ${active.length} 個工具執行中：${active.slice(0,3).map(a => a.tool).join('、')}`;
  let attention = state.waitUnknown ? '等待狀態不明' : '目前沒有待回覆訊號';
  if (state.waits.length) attention = state.waits.some(w => w.kind === 'question') ? '有問題等你回答' : '有權限通知，請確認原生授權介面';
  const notes = [];
  if (summary && state.summaryRevision !== state.revision) notes.push({text:'有新活動，摘要待更新', tone:'muted'});
  if (state.summaryError) notes.push({text:'摘要更新失敗', tone:'danger'});
  const inputs = inputRows(state);
  return {title:'你到底在忙什麼？', sections:[
    {id:'summary', label:'摘要', tone:'accent', meta:state.snapshotAt === null ? null : `脈絡與證據更新：${seconds(now, state.snapshotAt)} 秒前`, notes, rows:[
      {label:'目標', text:summary?.goal?.text ?? '目的尚不清楚'},
      {label:'脈絡', text:summary?.context?.text ?? '尚無摘要'},
      {label:'證據', text:summary?.evidence?.text ?? '尚無摘要'},
    ]},
    {id:'live', label:'即時', tone:liveTone(state), meta:state.lastEventAt === null ? null : `距離最近事件：${seconds(now, state.lastEventAt)} 秒`, notes:[], rows:[
      {label:'動作', text:action, dot:actionDot(state)},
      {label:'需要你', text:attention, dot:state.waits.length ? 'warning' : 'muted'},
    ]},
    {id:'inputs', label:inputs.label, tone:'input', meta:inputs.items.length ? `${inputs.items.length} 筆` : null, notes:[], empty:inputs.empty, rows:inputs.items},
  ]};
}

/** Fields in the flat layout's 0.2.0 order, each carrying its section tone. */
export function inlineFields(view) {
  const [summary, live] = view.sections;
  const [goal, context, evidence] = summary.rows;
  const [action, attention] = live.rows;
  const fromSummary = row => ({...row, tone:summary.tone});
  const fromLive = row => ({...row, tone:live.tone});
  return [fromSummary(goal), fromSummary(context), fromLive(action), fromSummary(evidence), fromLive(attention)];
}

/** Bottom lines of the flat layout, in the 0.2.0 order. */
export function footerNotes(view) {
  const [summary, live] = view.sections;
  return [...(summary.meta ? [{text:summary.meta, tone:'muted'}] : []), ...summary.notes, ...(live.meta ? [{text:live.meta, tone:'muted'}] : [])];
}

/** Plain-text form of the flat layout. */
export function paneLines(state, now) {
  const view = paneRows(state, now);
  const inputs = view.sections[2];
  const inputLines = [`${inputs.label}：${inputs.empty ?? ''}`, ...inputs.rows.flatMap(i => [`  ${i.text}`, ...(i.excerpt ? [`    「${i.excerpt}」`] : [])])];
  return [view.title, '', ...inlineFields(view).map(f => `${f.label}：${f.text}`), ...inputLines, '', ...footerNotes(view).map(n => n.text)];
}
```

- [ ] **Step 6: `hooks/register.js`**
  - Replace `import {paneRows} from './view.js';` with:
```js
import {paneRows, inlineFields, footerNotes} from './view.js';
import {colorFor} from './theme.js';
```
  - Add these top-level functions just above `/** Serialize an excerpt, never retain full tool arguments or outputs. */`:
```js
/** A dot then a coloured bold label, shared by both layouts so "● 動作：正在執行" reads the same. */
function labelled(Text, row, tone) {
  return Text({wrap:'wrap', children:[
    ...(row.dot ? [Text({color:colorFor(row.dot), children:'● '})] : []),
    Text({bold:true, color:colorFor(tone), children:`${row.label}：`}),
    row.text,
  ]});
}

/** Bordered sections for the dock, which has the height for them. */
function drawDock(view, {Box, Text}) {
  return view.sections.map(section => Box({flexDirection:'column', borderStyle:'round', borderColor:colorFor(section.tone), paddingX:1, children:[
    Box({flexDirection:'row', justifyContent:'space-between', children:[
      Text({bold:true, wrap:'truncate', children:`[ ${section.label} ]`}),
      ...(section.meta ? [Text({dimColor:true, wrap:'truncate', children:section.meta})] : []),
    ]}),
    ...(section.id === 'inputs'
      ? (section.empty ? [Text({dimColor:true, wrap:'truncate', children:section.empty})] : section.rows.flatMap(i => [Text({wrap:'truncate', children:i.text}), ...(i.excerpt ? [Text({dimColor:true, wrap:'truncate', children:`  「${i.excerpt}」`})] : [])]))
      : section.rows.map(row => labelled(Text, row, section.tone))),
    ...section.notes.map(note => Text({wrap:'wrap', color:colorFor(note.tone), children:note.text})),
  ]}));
}

/** The 0.2.0 flat rows with colour added; used wherever height is scarce. */
function drawInline(view, {Text}, bodyColumns) {
  const inputs = view.sections[2];
  return [
    Text({bold:true, wrap:'truncate', children:view.title}),
    // Box borders draw all four sides, so the rule is a line of box-drawing cells sized to the body.
    Text({dimColor:true, wrap:'truncate', children:'─'.repeat(Math.max(1, bodyColumns))}),
    ...inlineFields(view).map(field => labelled(Text, field, field.tone)),
    Text({wrap:'truncate', children:[Text({bold:true, color:colorFor(inputs.tone), children:`${inputs.label}：`}), inputs.empty ?? '']}),
    ...inputs.rows.flatMap(i => [Text({wrap:'truncate', children:`  ${i.text}`}), ...(i.excerpt ? [Text({dimColor:true, wrap:'truncate', children:`    「${i.excerpt}」`})] : [])]),
    Text({wrap:'wrap', children:''}),
    ...footerNotes(view).map(note => Text({wrap:'wrap', color:colorFor(note.tone), children:note.text})),
  ];
}
```
  - Replace the whole `on('ui.render', {component:'Pane', requestId:'attention-mod'}, …)` handler with:
```js
  on('ui.render', {component:'Pane', requestId:'attention-mod'}, ($, e) => {
    const els = $.ui.resolve(e);
    const view = paneRows(state, now);
    // Only the dock reliably has the height for bordered sections; any other placement keeps the compact layout.
    const body = e.props.placement === 'dock' ? drawDock(view, els) : drawInline(view, els, e.props.bodyColumns);
    return els.Box({flexDirection:'column', children:[
      ...body,
      els.Button({key:'close-attention', label:'收起', onPress:() => $.ui.close({id:'attention-mod'})}),
    ]});
  });
```

- [ ] **Step 7:** Run:
```bash
claude plugin test .
claude plugin validate --strict .
for f in hooks/*.js; do node --check "$f"; done
```
Expected: **71 pass, 0 fail** (post-review: 76 after adding dot/note colour tests, a reversed-sections test and a dim-footer test); validate passes with the same `calls:` list as before (no new `$.` calls); `node --check` silent. If an existing lifecycle/events test fails on pane text, report the exact assertion — do not change its expectation without asking.

---

### Task 3: Docs and version

**Files:** `README.md`, `.claude/CLAUDE.md`, `docs/prototype-results.md`, `.claude-plugin/plugin.json`, `package.json`.

- [ ] **Step 1:** Version `0.2.0` → `0.3.0` in `.claude-plugin/plugin.json` and `package.json`.
- [ ] **Step 2: README.md** — in the 「開啟」 section, after the paragraph that starts `面板預設開啟`, add:
```markdown
側邊面板（dock）用三個圓角框分區：摘要是藍色，外部輸入是洋紅，「即時」框依狀態變色——有工具在跑是綠色，有東西等你是黃色，閒置時用終端機預設色。放在輸入框上方時（inline）維持原本的版面，只把欄位名稱和狀態點上色。顏色用終端機的具名色，會跟著你的終端機主題走。
```
- [ ] **Step 3: .claude/CLAUDE.md** — replace the `view.js` bullet with:
```markdown
- `view.js`：`paneRows` 把狀態轉成三個區塊（摘要、即時、外部輸入），只帶語意色調不帶顏色；`liveTone`／`actionDot` 決定即時區塊和狀態點的色調；`inlineFields`／`footerNotes` 還原 0.2.0 的平面順序；`paneLines` 是純文字版本。不呼叫模型。
- `theme.js`：`colorFor(tone)` 把色調對應到終端機具名色，未知色調回傳 undefined。`register.js` 依 `e.props.placement` 呼叫 `drawDock`（圓角框）或 `drawInline`（平面）。
```
- [ ] **Step 4: docs/prototype-results.md** — append the Task 0 result and the live checks of Task 4 under `## 面板配色（0.3.0）`, listing what was VERIFIED and what stays NOT VERIFIED (Claude Desktop rendering at minimum).

---

### Task 4: Live check, gate, release (Tom approves each step)

- [ ] **Step 1:** Tom disables the installed copy: `claude plugin disable attention-mod@tomwangowa`, then runs `claude --plugin-dir "<path to this mod>"`:
  1. Wide terminal (dock): three coloured round boxes; live box green while a tool runs, yellow while a question waits.
  2. Terminal under 100 columns (inline): same row count as 0.2.0, close button visible, coloured labels.
  3. Claude Desktop, if available: record what renders.
- [ ] **Step 2:** Record results (Task 3 Step 4), then `completion-gate` at L1 (fresh test, validate, node --check, one `code-review-claude` over `git diff main`).
- [ ] **Step 3:** Ask Tom, then commit on `feat/pane-colors` and fast-forward `main`:
```bash
git add hooks/theme.js tests/theme.test.ts hooks/view.js hooks/register.js tests/view.test.ts tests/integration.test.ts README.md .claude/CLAUDE.md docs/prototype-results.md .claude-plugin/plugin.json package.json docs/superpowers/specs/2026-10-05-pane-colors-design.md docs/superpowers/plans/2026-10-05-pane-colors.md
git commit -F - <<'EOF'
feat(attention): colour the pane by section and state

Co-Authored-By: Claude Opus 5.5 <noreply@anthropic.com>
EOF
```
- [ ] **Step 4:** Ask Tom, then `git -C ~/.claude/skills subtree pull --prefix=plugins/attention-mod "<path to this mod>" main -m "chore(plugins): update attention-mod to 0.3.0 via subtree"`, validate, push.
- [ ] **Step 5:** `claude plugin update attention-mod@tomwangowa`, `claude plugin enable attention-mod@tomwangowa`, restart Claude Code.
