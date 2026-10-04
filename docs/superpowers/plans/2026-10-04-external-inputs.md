# External Inputs Column Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Show the five latest rows that entered the main Claude context without Tom typing them (hook context, attachments, deliveries, notices) in the attention pane, display-only.

**Architecture:** A new pure module `hooks/inputs.js` classifies each `session.append` row into an entry or null. `hooks/state.js` keeps the entries in a separate `inputs` slice that never touches `sources`, so they cannot reach the summary snapshot. `hooks/view.js` renders them; `hooks/register.js` only wires the event and draws the rows.

**Tech Stack:** Claude Code 2.1.288 mod (function hooks plugin), plain ES modules, `claude-code/testing` kit.

**Spec:** `docs/superpowers/specs/2026-10-04-external-inputs-design.md` (approved 2026-10-04).

---

## Ground rules for this repo

- Run tests with `claude plugin test .` from the repo root. It has **no per-file filter**; every run executes all suites. Baseline before this plan: 40 pass, 0 fail.
- There is no `tsc`. Also run `claude plugin validate --strict .` and `node --check hooks/<file>.js`.
- **Do not commit inside tasks.** Tom approves every commit. Task 6 asks for the single feature commit.
- `session.append` **cannot be dispatched end-to-end in the test kit**: a spike on 2026-10-04 showed the test's stub is skipped and the call fails with `HooksError: no implementation for session.append`. All classification logic therefore lives in the pure `entryFromAppend`; the `register.js` wiring is covered by Task 6 live checks.
- `.claude/CLAUDE.md` says to load the `plugin-authoring` skill before editing `hooks/` when it is available.

## File map

| File | Change | Responsibility |
| --- | --- | --- |
| `hooks/inputs.js` | Create | Door allowlist, noise denylist with reasons, origin/kind labels, excerpt, `entryFromAppend` |
| `hooks/state.js` | Modify | `inputs` / `inputsSince` fields, `external-input` event, carry rule on `session-reset` |
| `hooks/view.js` | Modify | `clockTime`, `inputRows`, `paneRows().inputs`, `paneLines` output |
| `hooks/register.js` | Modify | Call `entryFromAppend` in `session.append`, set `inputsSince`, pane `rows:18`, draw the section |
| `tests/inputs.test.ts` | Create | Classification tests |
| `tests/state.test.ts` | Modify | Slice, carry, and not-a-source tests |
| `tests/view.test.ts` | Modify | Ordering, excerpt limit, empty state |
| `tests/integration.test.ts` | Modify | Pane label list, `rows:18`, empty section drawn |
| `README.md`, `.claude/CLAUDE.md`, `docs/prototype-results.md` | Modify | Document behaviour and live results |

---

### Task 1: Classifier module

**Files:**
- Create: `hooks/inputs.js`
- Test: `tests/inputs.test.ts`

- [ ] **Step 1: Write the failing test**

Create `tests/inputs.test.ts`:

```ts
import {test, expect} from 'claude-code/testing';
import {entryFromAppend, originLabel, excerptOf, NOISE} from '../hooks/inputs.js';

const row = (door, message = {}, extra = {}) => ({door, uuid:'u1', origin:{kind:'engine'}, message:{type:'attachment', content:[{type:'text', text:'hello'}], ...message}, ...extra});

test('typed prompts, responses, tool results, commands and subagent rows are not external inputs', () => {
  for (const door of ['prompt','response','tool-result','command']) expect(entryFromAppend(row(door), undefined)).toBe(null);
  expect(entryFromAppend(row('hook-context', {}, {agentId:'agent-one'}), undefined)).toBe(null);
});
test('known noise is dropped but an unseen attachment kind stays visible', () => {
  expect(NOISE.has('total_tokens_reminder')).toBe(true);
  expect(entryFromAppend(row('attachment', {name:'total_tokens_reminder'}), undefined)).toBe(null);
  expect(entryFromAppend(row('attachment', {name:'some_new_kind'}), undefined)).toEqual({id:'u1', kind:'附件 some_new_kind', origin:'引擎', excerpt:'hello'});
});
test('every listed door produces an entry', () => {
  for (const door of ['delivery','hook-context','notice','note','compaction','tool-message']) expect(entryFromAppend(row(door, {type:'user'}), undefined)?.id).toBe('u1');
});
test('hook context is labelled with the settings hook event', () => {
  const entry = entryFromAppend(row('hook-context', {name:'hook_additional_context'}, {origin:{kind:'hook', event:'SessionStart'}}), undefined);
  expect(entry.kind).toBe('hook 注入');
  expect(entry.origin).toBe('hook（SessionStart）');
});
test('excerpt reads the stored row, first line only, bounded by code points', () => {
  const stored = {uuid:'u1', message:{type:'attachment', name:'file', content:[{type:'text', text:'😀'.repeat(50) + '\nsecond line'}]}};
  const entry = entryFromAppend(row('attachment', {name:'file', content:[{type:'text', text:'original'}]}), stored);
  expect(Array.from(entry.excerpt).length).toBe(40);
  expect(entry.excerpt.endsWith('…')).toBe(true);
  expect(entry.excerpt).not.toContain('second line');
  expect(excerptOf([{type:'image', source:{}}])).toBe('[圖片]');
  expect(excerptOf([])).toBe('[無文字內容]');
});
test('unknown origin kinds are shown raw and missing origins are not guessed', () => {
  expect(originLabel({kind:'observer-activity'})).toBe('observer-activity');
  expect(originLabel({kind:'task-notification'})).toBe('背景工作');
  expect(originLabel(undefined)).toBe('來源不明');
});
```

- [ ] **Step 2: Run tests to verify the new suite fails**

Run: `claude plugin test .`
Expected: `tests/inputs.test.ts` fails to load (module `../hooks/inputs.js` not found); the other 40 tests still pass.

- [ ] **Step 3: Write the implementation**

Create `hooks/inputs.js`:

```js
/** Doors whose rows reach the main model without Tom typing them. */
const DOORS = new Set(['delivery','attachment','hook-context','notice','note','compaction','tool-message']);

/** Engine-generated attachments, each with the reason it is noise. Unlisted names stay visible on purpose. */
export const NOISE = new Map([
  ['total_tokens_reminder', 'token balance reminder on every turn'],
  ['environment', 'working directory and platform snapshot'],
  ['model', 'model identity'],
  ['date', 'current date'],
  ['deferred_tools_delta', 'deferred tool catalog change'],
  ['deferred_tools_record', 'deferred tool schemas'],
  ['agent_listing_delta', 'available agent catalog'],
  ['skill_listing', 'available skill catalog'],
  ['advisor_tool', 'tool availability switch'],
  ['auto_mode', 'permission mode switch'],
  ['prompt_snapshot', 'system prompt snapshot'],
  ['command_permissions', 'tools a command may use'],
  ['remote_session_change', 'remote session and attribution settings'],
]);

const ORIGINS = {engine:'引擎', model:'模型', 'task-notification':'背景工作', peer:'其他 session', 'peer-send-message':'其他 session', 'scheduled-trigger':'排程'};

/** Clip to a code-point budget with a visible ellipsis. */
export function clip(text, limit) {
  const points = Array.from(String(text));
  return points.length <= limit ? points.join('') : points.slice(0, limit - 1).join('') + '…';
}

/** Name who caused a row; kinds this build does not label are shown raw instead of guessed. */
export function originLabel(origin) {
  const kind = origin?.kind;
  if (typeof kind !== 'string') return '來源不明';
  if (kind === 'hook') return origin.event ? `hook（${origin.event}）` : 'hook';
  if (kind === 'plugin') return origin.event ? `plugin（${origin.event}）` : 'plugin';
  if (kind === 'tool') return `工具 ${origin.tool ?? 'unknown'}`;
  return ORIGINS[kind] ?? kind;
}

/** Short kind label from the door and the attachment name. */
export function kindLabel(door, name) {
  if (door === 'hook-context' || name === 'hook_additional_context') return 'hook 注入';
  if (door === 'attachment') return name ? `附件 ${name}` : '附件';
  return name ?? door;
}

/** First line of the first text block; media-only rows get a marker instead of nothing. */
export function excerptOf(content) {
  const blocks = Array.isArray(content) ? content : [];
  const block = blocks.find(b => b?.type === 'text' && typeof b.text === 'string' && b.text.trim());
  if (block) return clip(block.text.trim().split('\n')[0], 40);
  return blocks.some(b => b?.type === 'image' || b?.type === 'document') ? '[圖片]' : '[無文字內容]';
}

/** Classify one kept row; null for Tom's own input, known noise, or a subagent's conversation. */
export function entryFromAppend(e, result) {
  if (!e || e.agentId || !DOORS.has(e.door)) return null;
  // The stored row is what the model reads, so excerpt it rather than the incoming one.
  const message = result?.message ?? e.message ?? {};
  if (e.door === 'attachment' && NOISE.has(message.name)) return null;
  return {id:String(result?.uuid ?? e.uuid), kind:clip(kindLabel(e.door, message.name), 24), origin:clip(originLabel(e.origin), 24), excerpt:excerptOf(message.content)};
}
```

- [ ] **Step 4: Run tests to verify they pass**

Run: `claude plugin test .` and `node --check hooks/inputs.js`
Expected: 46 pass, 0 fail; `node --check` prints nothing.

---

### Task 2: State slice

**Files:**
- Modify: `hooks/state.js` (typedefs, `createState`, `session-reset` branch, new `external-input` branch)
- Test: `tests/state.test.ts`

- [ ] **Step 1: Write the failing tests**

In `tests/state.test.ts`, add the import below the existing ones:

```ts
import {buildSnapshot} from '../hooks/snapshot.js';
```

Append these tests to the end of the file:

```ts
const input = (s, id, at = 10) => reduceState(s, {type:'external-input', entry:{id, kind:'hook 注入', origin:'引擎', excerpt:id}, sessionId:s.sessionId, epoch:s.epoch, at});

test('external inputs keep the latest five, once per row, across prompts', () => {
  let s = createState('one');
  for (const id of ['a','b','c','d','e','f']) s = input(s, id);
  s = input(s, 'f');
  expect(s.inputs.map(i => i.id)).toEqual(['b','c','d','e','f']);
  const next = reduceState(s, {type:'new-prompt', id:'goal', text:'task', at:20});
  expect(next.inputs.map(i => i.id)).toEqual(['b','c','d','e','f']);
  expect(next.inputs[0].epoch < next.epoch).toBe(true);
});
test('session end clears inputs; the next session keeps rows that arrived in between', () => {
  let s = input(createState('one'), 'old');
  s = reduceState(s, {type:'session-reset', sessionId:'between-sessions', at:20});
  expect(s.inputs).toEqual([]);
  expect(s.inputsSince).toBe(20);
  s = input({...s, enabled:false}, 'start-hook', 25);
  expect(s.inputs.length).toBe(1);
  s = reduceState(s, {type:'session-reset', sessionId:'two', at:30});
  expect(s.inputs.map(i => i.id)).toEqual(['start-hook']);
  expect(s.inputs[0].epoch).toBe(s.epoch);
  expect(s.inputsSince).toBe(20);
});
test('startup rows survive the first reset, rows of another known session do not', () => {
  const boot = reduceState(input(createState('unknown'), 'boot'), {type:'session-reset', sessionId:'two', at:30});
  expect(boot.inputs.map(i => i.id)).toEqual(['boot']);
  const other = reduceState(input(createState('one'), 'from-one'), {type:'session-reset', sessionId:'two', at:30});
  expect(other.inputs).toEqual([]);
  expect(other.inputsSince).toBe(30);
});
test('external inputs never become summary material', () => {
  let s = reduceState(createState('one'), {type:'new-prompt', id:'goal', text:'task', at:0});
  s = input(s, 'INJECTED-MARKER');
  expect(s.sources.map(x => x.id)).toEqual(['goal']);
  expect(s.revision).toBe(1);
  expect(buildSnapshot(s, [], 10).prompt).not.toContain('INJECTED-MARKER');
});
```

- [ ] **Step 2: Run tests to verify they fail**

Run: `claude plugin test .`
Expected: the four new state tests fail (`s.inputs` is undefined); all others pass.

- [ ] **Step 3: Write the implementation**

In `hooks/state.js`, replace the `State` typedef line with these two lines:

```js
/** @typedef {{id:string, kind:string, origin:string, excerpt:string, sessionId:string, epoch:number, at:number}} Input */
/** @typedef {{sessionId:string, epoch:number, revision:number, sources:Source[], goalId:string|null, goalContextIds:string[], activities:Activity[], waits:object[], summary:object|null, summaryRevision:number|null, summaryError:string|null, snapshotAt:number|null, turnStatus:string, enabled:boolean, lastTool:object|null, lastEventAt:number|null, waitUnknown:boolean, inputs:Input[], inputsSince:number|null}} State */
```

Replace `createState` with:

```js
/** Create an isolated, memory-only session state. @returns {State} */
export function createState(sessionId) {
  return {sessionId, epoch:0, revision:0, sources:[], goalId:null, goalContextIds:[], activities:[], waits:[], summary:null, summaryRevision:null, summaryError:null, snapshotAt:null, turnStatus:'unknown', enabled:true, lastTool:null, lastEventAt:null, waitUnknown:false, inputs:[], inputsSince:null};
}

/** Session IDs held before a real session is known: startup and the gap after session.end. */
const UNBOUND_SESSIONS = ['unknown', 'between-sessions'];
```

Replace the `session-reset` branch at the top of `reduceState` with:

```js
  if (event.type === 'session-reset') {
    const epoch = state.epoch + 1;
    // SessionStart hook context can land between session.end and the new session's reset; it belongs to the new session.
    const inputs = event.sessionId === 'between-sessions' ? [] : state.inputs.filter(i => UNBOUND_SESSIONS.includes(i.sessionId)).map(i => ({...i, epoch}));
    const inputsSince = inputs.length && state.inputsSince !== null ? state.inputsSince : event.at;
    return {...createState(event.sessionId), epoch, enabled:state.enabled, lastEventAt:event.at, inputs, inputsSince};
  }
  if (event.type === 'external-input') {
    // Display-only: never a source, so the summary snapshot cannot read it. Accepted while disabled on purpose.
    if (state.inputs.some(i => i.id === event.entry.id)) return state;
    return {...state, inputs:[...state.inputs, {...event.entry, sessionId:event.sessionId, epoch:event.epoch, at:event.at}].slice(-5)};
  }
```

- [ ] **Step 4: Run tests to verify they pass**

Run: `claude plugin test .` and `node --check hooks/state.js`
Expected: 50 pass, 0 fail.

---

### Task 3: View rows

**Files:**
- Modify: `hooks/view.js`
- Test: `tests/view.test.ts`

- [ ] **Step 1: Write the failing tests**

In `tests/view.test.ts`, change the view import to:

```ts
import {paneLines,paneRows,clockTime} from '../hooks/view.js';
```

Append:

```ts
test('external inputs list newest first with excerpts on the two newest only',()=>{
  let s=createState('s');
  for(const [id,at] of [['a',0],['b',60000],['c',120000]]) s=reduceState(s,{type:'external-input',entry:{id,kind:'hook 注入',origin:'引擎',excerpt:`text-${id}`},sessionId:'s',epoch:s.epoch,at});
  s=reduceState(s,{type:'new-prompt',id:'goal',text:'task',at:130000});
  s=reduceState(s,{type:'external-input',entry:{id:'d',kind:'附件 file',origin:'引擎',excerpt:'text-d'},sessionId:'s',epoch:s.epoch,at:180000});
  const {inputs}=paneRows(s,0);
  expect(inputs.label).toBe('外部輸入');
  expect(inputs.items.map(i=>i.text)).toEqual([
    `${clockTime(180000)} 附件 file · 引擎（本回合）`,
    `${clockTime(120000)} hook 注入 · 引擎（前幾回合）`,
    `${clockTime(60000)} hook 注入 · 引擎（前幾回合）`,
    `${clockTime(0)} hook 注入 · 引擎（前幾回合）`,
  ]);
  expect(inputs.items.map(i=>i.excerpt)).toEqual(['text-d','text-c',null,null]);
  const lines=paneLines(s,0).join('\n');
  expect(lines).toContain('「text-d」');
  expect(lines).not.toContain('text-a');
});
test('empty inputs say when recording started, without inventing a time',()=>{
  expect(paneRows(createState('s'),0).inputs.empty).toBe('尚無');
  const s={...createState('s'),inputsSince:60000};
  expect(paneLines(s,0).join('\n')).toContain(`外部輸入：尚無（${clockTime(60000)} 起記錄）`);
});
```

- [ ] **Step 2: Run tests to verify they fail**

Run: `claude plugin test .`
Expected: the two new view tests fail (`clockTime` is not exported); all others pass.

- [ ] **Step 3: Write the implementation**

In `hooks/view.js`, add above `paneRows`:

```js
/** Local wall-clock HH:MM for a clock reading in milliseconds. */
export function clockTime(ms) {
  const d = new Date(ms);
  return `${String(d.getHours()).padStart(2,'0')}:${String(d.getMinutes()).padStart(2,'0')}`;
}

/** Newest first; only the two newest keep an excerpt so the pane fits in 18 rows. */
export function inputRows(state) {
  const items = [...state.inputs].reverse().map((i, index) => ({text:`${clockTime(i.at)} ${i.kind} · ${i.origin}（${i.epoch === state.epoch ? '本回合' : '前幾回合'}）`, excerpt:index < 2 ? i.excerpt : null}));
  const empty = items.length ? null : state.inputsSince === null ? '尚無' : `尚無（${clockTime(state.inputsSince)} 起記錄）`;
  return {label:'外部輸入', empty, items};
}
```

In `paneRows`, change the return line to:

```js
  return {title:'你到底在忙什麼？', fields, notes, inputs:inputRows(state)};
```

Replace `paneLines` with:

```js
/** Plain-text form of the pane rows. */
export function paneLines(state, now) {
  const {title, fields, notes, inputs} = paneRows(state, now);
  const inputLines = [`${inputs.label}：${inputs.empty ?? ''}`, ...inputs.items.flatMap(i => [`  ${i.text}`, ...(i.excerpt ? [`    「${i.excerpt}」`] : [])])];
  return [title, '', ...fields.map(f => `${f.label}：${f.text}`), ...inputLines, '', ...notes];
}
```

- [ ] **Step 4: Run tests to verify they pass**

Run: `claude plugin test .` and `node --check hooks/view.js`
Expected: 52 pass, 0 fail. The existing `pane rows expose ... each field label` test still expects five `fields`, because inputs are a separate section.

---

### Task 4: Wire into register.js and draw the section

**Files:**
- Modify: `hooks/register.js` (imports; `session.start`; `session.append`; both `ui.open` calls; Pane render)
- Test: `tests/integration.test.ts`

- [ ] **Step 1: Update the integration tests (they will fail)**

In `tests/integration.test.ts`, in the test `slow background model does not block tools...`, add after `expect(h.record.opens[0].focus).toBe(undefined);`:

```ts
  expect(h.record.opens[0].rows).toBe(18);
```

In the test `pane draws a bold question title...`, replace the two lines starting at `expect(labels).toEqual(` with:

```ts
  expect(labels).toEqual(['目標：','脈絡：','動作：','證據：','需要你：','外部輸入：']);
  expect(await renderedText(pane)).toContain('目標：目的尚不清楚');
  expect(await renderedText(pane)).toContain('外部輸入：尚無');
```

- [ ] **Step 2: Run tests to verify they fail**

Run: `claude plugin test .`
Expected: those two integration tests fail (`rows` is 12; no `外部輸入：` label); all others pass.

- [ ] **Step 3: Write the implementation**

In `hooks/register.js`, add after the `import {paneRows} from './view.js';` line:

```js
import {entryFromAppend} from './inputs.js';
```

In the `session.start` handler, after `now = await $.clock.now();` add:

```js
      if (state.inputsSince === null) state = {...state, inputsSince:now};
```

Replace the start of the `session.append` handler, up to and including the existing filter line, with:

```js
  on('session.append', async ($, e, next) => {
    const epoch = state.epoch;
    const result = await next(e);
    try {
      // Display-only record of rows Tom did not type; kept apart from summary sources.
      const entry = entryFromAppend(e, result);
      if (entry) { apply({type:'external-input', entry, sessionId:state.sessionId, epoch:state.epoch, at:await $.clock.now()}); redraw($); }
    } catch { /* Classification failures must not change the stored row or the caller's result. */ }
    if (e.agentId || e.message.isMeta || !['response','tool-result'].includes(e.door)) return result;
```

The rest of the handler stays as it is.

Change both `$.ui.open({id:'attention-mod', title:'你到底在忙什麼', rows:12, columns:48})` calls (`session.start` and `command.run`) to use `rows:18`.

In the `ui.render` Pane handler, replace `const {title, fields, notes} = paneRows(state, now);` with:

```js
    const {title, fields, notes, inputs} = paneRows(state, now);
```

Then insert, directly after the `...fields.map(...)` line:

```js
      Text({wrap:'truncate', children:[Text({bold:true, children:`${inputs.label}：`}), inputs.empty ?? '']}),
      ...inputs.items.flatMap(i => [Text({wrap:'truncate', children:`  ${i.text}`}), ...(i.excerpt ? [Text({dimColor:true, wrap:'truncate', children:`    「${i.excerpt}」`})] : [])]),
```

- [ ] **Step 4: Run the full checks**

Run:

```bash
claude plugin test .
claude plugin validate --strict .
for f in hooks/*.js; do node --check "$f"; done
```

Expected: 52 pass, 0 fail; validate prints `✔ Validation passed`, and its `calls` list is unchanged (no new `$.` calls besides those already listed); `node --check` prints nothing.

---

### Task 5: Documentation

**Files:**
- Modify: `README.md`, `.claude/CLAUDE.md`, `docs/prototype-results.md`

- [ ] **Step 1: README**

In `README.md`, insert after the paragraph that starts with `「動作」「需要你」來自原生事件。`:

```markdown
「外部輸入」列出最近 5 筆不是你打、但進了 Claude context 的內容，例如 hook 注入、附件、背景工作回報、notice，附時間、種類、來源，最新 2 筆另外附單行節錄。它只顯示，不會成為摘要素材；資料只在記憶體，`/clear`、resume、重載後清空。已知的系統附件（token 提醒、環境、工具清單等）由 `hooks/inputs.js` 的黑名單濾掉，沒見過的種類照樣顯示。事後追查請看對話紀錄 JSONL，每一列都有時間。
```

- [ ] **Step 2: CLAUDE.md**

In `.claude/CLAUDE.md`, insert after the `- \`view.js\`：...` bullet:

```markdown
- `inputs.js`：`entryFromAppend(e, result)` 把 `session.append` 的列分類成外部輸入或 null；`NOISE` 黑名單每項附原因，沒列的種類照樣顯示。外部輸入只進 `state.inputs`，不進 `sources`，所以不會進摘要快照；`session-reset` 換到新 session 時保留 `'unknown'`／`'between-sessions'` 期間收到的列。測試 kit 無法端到端觸發 `session.append`，分類邏輯要放在這個純函式裡測。
```

- [ ] **Step 3: prototype-results.md**

Append to `docs/prototype-results.md`:

```markdown
## 外部輸入欄位（2026-10-04）

自動化：`tests/inputs.test.ts`、`state.test.ts`、`view.test.ts`、`integration.test.ts` 覆蓋分類、黑名單、保留 5 筆、跨回合、`/clear` 空窗期保留、不進摘要快照、面板繪製。`session.append` 無法在測試 kit 端到端觸發，`register.js` 的接線只由實機驗證。

NOT VERIFIED（待實機）：SessionStart hook 注入在 `/clear` 後是否留在面板；`@` 附檔的 door 與 name；背景工作回報是否走 `delivery`；窄終端機 `rows:18` 的實際版面。
```

---

### Task 6: Live verification with Tom, gate, and commit

Live checks need Tom's interactive terminal. Do them together; record what is observed, not what was expected.

- [ ] **Step 1: Prepare a probe settings file**

Write `/tmp/attention-probe-settings.json` (outside the repo; delete after the session):

```json
{"hooks":{"SessionStart":[{"hooks":[{"type":"command","command":"echo '{\"hookSpecificOutput\":{\"hookEventName\":\"SessionStart\",\"additionalContext\":\"EXTERNAL-INPUT-PROBE\"}}'"}]}]}}
```

- [ ] **Step 2: Tom runs the live session**

```bash
claude --plugin-dir "$PWD" --settings /tmp/attention-probe-settings.json
```

Checks, in order:
1. Pane shows `外部輸入：` with a `hook 注入 · hook（SessionStart）` row and excerpt `「EXTERNAL-INPUT-PROBE」`.
2. Run `/clear`. The probe row must appear again for the new session; rows from before the clear must be gone.
3. Send a prompt that `@`-mentions `README.md`. Note the shown kind and origin.
4. Ask Claude to run a short background task (e.g. a background `sleep 3`), and note whether its completion shows up and under which kind.
5. In a terminal under 100 columns, confirm the pane with `rows:18` does not take input focus.

- [ ] **Step 3: Record results**

Replace the NOT VERIFIED line added in Task 5 Step 3 with the observed door/kind/origin for each check, keeping any check that could not be run under NOT VERIFIED.

- [ ] **Step 4: Completion gate**

Apply `completion-gate` at L1: fresh `claude plugin test .`, `claude plugin validate --strict .`, `node --check` for every `hooks/*.js`, then one `code-review-claude` pass over the diff from `4f02ba8`.

- [ ] **Step 5: Ask Tom, then commit**

Show the file list and the message below; commit only after Tom says yes:

```bash
git add hooks/inputs.js hooks/state.js hooks/view.js hooks/register.js tests/inputs.test.ts tests/state.test.ts tests/view.test.ts tests/integration.test.ts README.md .claude/CLAUDE.md docs/prototype-results.md
git commit -F - <<'EOF'
feat(attention): show external inputs in the pane

Co-Authored-By: Claude Opus 5.5 <noreply@anthropic.com>
EOF
```
