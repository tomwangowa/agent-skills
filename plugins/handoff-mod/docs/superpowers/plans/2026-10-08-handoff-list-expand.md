# 啟動清單展開與自動筆記折疊 實作計畫

> **給執行者：** 必讀子技能：`superpowers:subagent-driven-development`（建議）或 `superpowers:executing-plans`，逐任務執行。步驟用 `- [ ]` 追蹤。

**目標：** 「還有 N 筆」變成可按的展開按鈕，`/handoff-resume all` 列出全部，同 branch 較舊的自動筆記預設折進「還有 N 筆」。

**架構：** `rank.js`（純函式）多回傳 `rest`，並替同 `root` 加同 `branch` 的較舊自動筆記標 `olderAuto`。`register.js` 新增 `$.state` atom `expanded`；`buildList` 在 `expanded` 為 `false` 時只替 `shown` 跑 git 新鮮度，為 `true` 時替 `shown` 加 `rest` 全部建立。按鈕與 `/handoff-resume all` 都只是把 `expanded` 設成 `true` 再重建清單。

**技術：** Claude Code mod，純 ES modules，`claude-code/testing`。

**規格：** [啟動清單展開與自動筆記折疊](../specs/2026-10-08-handoff-list-expand-design.md)（決定 D15、D16）。**分支：** `main`；工作樹已有尚未 commit 的邊框樣式改動（`hooks/register.js`、`tests/register.test.ts`、`plugin.json` 版號 0.1.1），本計畫疊在上面。

**每個 commit 前都要先問作者。** 下面每個任務結尾的 commit 步驟，執行者要先停下來問，得到同意才下指令；前一次的同意不延續。commit 訊息結尾加 `Co-Authored-By: Claude Sonnet 5.5 <noreply@anthropic.com>`。

**測試指令：** `claude plugin test .`（在 `plugins/handoff-mod` 目錄下執行；只吃資料夾，沒有單檔篩選，所以「跑單一測試」都是整批跑、看指定名稱的結果）。本機沒有 `tsc`，型別不會被檢查。

---

## 檔案結構

| 檔案 | 動作 | 責任 |
| --- | --- | --- |
| `hooks/i18n.js` | 修改 | 新增 `list.moreCmd`、`list.older`（中英各一） |
| `hooks/rank.js` | 修改 | 回傳 `rest`；較舊自動筆記標 `olderAuto` |
| `hooks/register.js` | 修改 | `expanded` atom、`buildList`、band 按鈕與標示、`/handoff-resume` |
| `types/index.d.ts` | 修改 | 宣告 `expanded`（每個 `$.state` atom 都要在這裡宣告，否則 `validate` 失敗） |
| `tests/rank.test.ts` | 修改 | 折疊規則的單元測試 |
| `tests/world.ts` | 修改 | 新增 `fiveHandoffs` 測試資料 |
| `tests/register.test.ts` | 修改 | 按鈕、`all`、編號超出範圍、提示行、延遲建立 |
| `docs/superpowers/specs/2026-10-06-handoff-mod-design.md` | 修改 | 決定紀錄補 D15、D16；元件 3 排序一行 |
| `README.md`、`README-en.md` | 修改 | 各補一句 |

---

### Task 1：i18n 字串

**Files:**
- Modify: `hooks/i18n.js`（zh-TW 區塊 `list.more` 附近，en 區塊 `list.more` 附近）
- Test: `tests/i18n.test.ts`（既有的「兩種語言 key 相同」「占位符相同」兩個測試會擋）

- [ ] **Step 1：先跑基準測試，記下目前結果**

Run: `cd plugins/handoff-mod && claude plugin test .`
Expected: 全部通過（記下通過的數量，之後比對；若已有失敗，先停下來告訴作者，不要往下做）。

- [ ] **Step 2：只加中文 key，確認 parity 測試會紅**

在 `hooks/i18n.js` zh-TW 區塊，`'list.more': '還有 {count} 筆',` 之後加：

```js
    'list.moreCmd': '還有 {count} 筆，輸入 /handoff-resume all 全部列出',
    'list.older': '同 branch 較舊的自動筆記',
```

Run: `claude plugin test .`
Expected: `both languages define exactly the same keys` FAIL。

- [ ] **Step 3：補英文 key**

在 en 區塊，`'list.more': '{count} more',` 之後加：

```js
    'list.moreCmd': '{count} more. Run /handoff-resume all to list them all',
    'list.older': 'Older automatic note on the same branch',
```

- [ ] **Step 4：跑測試確認通過**

Run: `claude plugin test .`
Expected: 全部通過，數量與 Step 1 相同（沒有新增測試，只是 parity 回到綠）。

- [ ] **Step 5：Commit（先問作者）**

```bash
git add plugins/handoff-mod/hooks/i18n.js
git commit -m "feat(handoff-mod): add strings for the expandable list and older automatic notes"
```

---

### Task 2：`rank.js` 折疊規則（D15）

**Files:**
- Modify: `hooks/rank.js`
- Test: `tests/rank.test.ts`

- [ ] **Step 1：讓測試用的 `item` 輔助函式支援 `branch`**

`tests/rank.test.ts` 的 `item` 改成（只多一個 `branch: o.branch`）：

```ts
const item = (path: string, daysAgo: number, o: any = {}) => ({
  path, effectiveStatus: o.status ?? 'in-progress', claimedByOther: o.claimed ?? false,
  meta: {root: o.root ?? '/other', repo: o.repo, branch: o.branch, created: now - daysAgo * DAY, source: o.source, task: path},
});
```

並在 `const paths = ...` 之後加：

```ts
const restPaths = (r: any) => r.rest.map((i: any) => i.path);
```

- [ ] **Step 2：寫會失敗的測試**

附加在檔案最後：

```ts
test('the rest is everything that is not shown, in ranked order', () => {
  const r = rankHandoffs([1, 2, 3, 4, 5].map((n) => item(`p${n}`, n)), ctx);
  expect(restPaths(r)).toEqual(['p4', 'p5']);
  expect(r.collapsed).toBe(2);
});
test('on one branch only the newest automatic note can be shown; older ones sit in the rest, flagged and counted', () => {
  const r = rankHandoffs([item('auto-new', 1, {source: 'auto', branch: 'b'}), item('auto-mid', 2, {source: 'auto', branch: 'b'}), item('auto-old', 3, {source: 'auto', branch: 'b'})], ctx);
  expect(paths(r)).toEqual(['auto-new']);
  expect(restPaths(r)).toEqual(['auto-mid', 'auto-old']);
  expect(r.rest.every((i: any) => i.olderAuto === true)).toBe(true);
  expect(r.shown[0].olderAuto).toBeUndefined();
  expect(r.collapsed).toBe(2);
});
test('a folded older automatic note is not pulled up when the shown list has room', () => {
  const r = rankHandoffs([item('auto-new', 1, {source: 'auto', branch: 'b'}), item('auto-old', 2, {source: 'auto', branch: 'b'}), item('manual', 5)], ctx);
  expect(paths(r)).toEqual(['auto-new', 'manual']);
  expect(restPaths(r)).toEqual(['auto-old']);
});
test('automatic notes on different branches or roots do not fold each other', () => {
  const r = rankHandoffs([item('a', 1, {source: 'auto', branch: 'x'}), item('b', 2, {source: 'auto', branch: 'y'}), item('c', 3, {source: 'auto', branch: 'x', root: '/work/app'})], ctx);
  expect(paths(r).sort()).toEqual(['a', 'b', 'c']);
  expect(r.rest).toEqual([]);
});
test('manual handoffs are never folded and do not affect the grouping of automatic notes', () => {
  const r = rankHandoffs([item('manual-new', 1, {branch: 'b'}), item('auto-new', 2, {source: 'auto', branch: 'b'}), item('auto-old', 3, {source: 'auto', branch: 'b'})], ctx);
  expect(paths(r)).toEqual(['manual-new', 'auto-new']);
  expect(restPaths(r)).toEqual(['auto-old']);
});
test('automatic notes with no branch are grouped by root', () => {
  const r = rankHandoffs([item('new', 1, {source: 'auto'}), item('old', 2, {source: 'auto'}), item('elsewhere', 3, {source: 'auto', root: '/another'})], ctx);
  expect(paths(r).sort()).toEqual(['elsewhere', 'new']);
  expect(restPaths(r)).toEqual(['old']);
});
test('automatic notes past 7 days are hidden before grouping, so they never count as folded', () => {
  const r = rankHandoffs([item('new', 1, {source: 'auto', branch: 'b'}), item('week-old', 8, {source: 'auto', branch: 'b'})], ctx);
  expect(paths(r)).toEqual(['new']);
  expect(r.rest).toEqual([]);
  expect(r.collapsed).toBe(0);
  expect(r.hidden).toBe(1);
});
test('folding does not depend on the input order and does not touch the input items', () => {
  const items = [item('a', 1, {source: 'auto', branch: 'b'}), item('b', 2, {source: 'auto', branch: 'b'}), item('c', 2, {source: 'auto', branch: 'b'})];
  const forward = rankHandoffs(items, ctx);
  const backward = rankHandoffs([...items].reverse(), ctx);
  expect(restPaths(forward)).toEqual(restPaths(backward));
  expect(items.every((i: any) => i.olderAuto === undefined)).toBe(true);
});
```

- [ ] **Step 3：跑測試確認紅**

Run: `claude plugin test .`
Expected: 上面新增的測試 FAIL（`r.rest` 是 undefined 之類）；既有的 rank 測試仍通過。

- [ ] **Step 4：實作**

把 `hooks/rank.js` 中 `rankHandoffs` 以上的常數保留，並把函式與註解整段換成：

```js
/** Newest first; the path settles a tie so the order never depends on the input order. */
const byNewest = (a, b) => b.meta.created - a.meta.created || (a.path < b.path ? -1 : a.path > b.path ? 1 : 0);
/** Automatic notes of one working tree and branch; with no branch, of one working tree. */
const groupKey = (item) => `${item.meta.root ?? ''}\u0000${item.meta.branch ?? ''}`;

/**
 * Pick what the start-up list shows. `items` are {path, meta, effectiveStatus, claimedByOther}.
 * Same working tree first, then same repository, then newest; the order never depends on the input order.
 * Returns {shown, rest, collapsed, hidden}: `rest` is everything not shown (folded by age, by the limit of three, or because
 * it is an older automatic note on a branch that has a newer one, D15; those carry `olderAuto: true`). `collapsed` is
 * `rest.length`. `hidden` counts automatic notes older than 7 days, which are neither shown nor in `rest`.
 */
export function rankHandoffs(items, {base, repo, now}) {
  const open = items.filter((item) => OPEN_STATUSES.includes(item.effectiveStatus));
  const live = open.filter((item) => !(item.meta.source === 'auto' && now - item.meta.created > AUTO_HIDE_AFTER));
  const hidden = open.length - live.length;
  const newestAuto = new Map();
  for (const item of live) {
    if (item.meta.source !== 'auto') continue;
    const best = newestAuto.get(groupKey(item));
    if (!best || byNewest(item, best) < 0) newestAuto.set(groupKey(item), item);
  }
  const flagged = live.map((item) => (item.meta.source === 'auto' && newestAuto.get(groupKey(item)) !== item ? {...item, olderAuto: true} : item));
  const score = (item) => (base && item.meta.root === base ? 0 : repo && item.meta.repo === repo ? 1 : 2);
  const sorted = flagged.sort((a, b) => score(a) - score(b) || byNewest(a, b));
  const shown = sorted.filter((item) => !item.olderAuto && now - item.meta.created <= FOLD_AFTER).slice(0, SHOWN);
  const rest = sorted.filter((item) => !shown.includes(item));
  return {shown, rest, collapsed: rest.length, hidden};
}
```

（`flagged` 是 `map` 產生的新陣列，直接 `sort` 不會動到輸入。）

- [ ] **Step 5：跑測試確認全綠**

Run: `claude plugin test .`
Expected: 全部通過，包含 Task 2 新增的 8 個與既有 rank 測試。

- [ ] **Step 6：Commit（先問作者）**

```bash
git add plugins/handoff-mod/hooks/rank.js plugins/handoff-mod/tests/rank.test.ts
git commit -m "feat(handoff-mod): fold older automatic notes of the same branch into the rest"
```

---

### Task 3：`expanded` 狀態、`buildList`、band 按鈕（D16）

**Files:**
- Modify: `tests/world.ts`（檔尾新增 `fiveHandoffs`）
- Modify: `hooks/register.js`（atom 區塊約第 36–45 行；`buildList` 約第 158–189 行；`ui.render` 約第 620–665 行）
- Test: `tests/register.test.ts`

- [ ] **Step 1：新增測試資料**

`tests/world.ts` 在 `twoHandoffs` 之後加：

```ts
/** Five handoffs on five branches, all fresh; task 1 is the newest. */
export const fiveHandoffs: Record<string, string> = Object.fromEntries([1, 2, 3, 4, 5].map((n) => [
  `${HANDOFF_DIR}/feat-n${n}--20261006-0${10 - n}0000.md`,
  handoffText({created: `2026-10-06T0${10 - n}:00:00Z`}).replace('task: 修正登入逾時', `task: 任務${n}`).replace('branch: feat/login-timeout', `branch: feat/n${n}`),
]));
/** An automatic note; `hh` is the hour it was written on 2026-10-06. */
export const autoNote = (hh: string, task: string, branch: string): [string, string] => [
  `${HANDOFF_DIR}/${branch.replace('/', '-')}--20261006-${hh}0000--auto.md`,
  handoffText({created: `2026-10-06T${hh}:00:00Z`, extra: 'source: auto'}).replace('task: 修正登入逾時', `task: ${task}`).replace('branch: feat/login-timeout', `branch: ${branch}`),
];
```

並在 `tests/register.test.ts` 的 import 補上 `fiveHandoffs, autoNote`：

```ts
import {world, twoHandoffs, fiveHandoffs, autoNote, fileA, fileB, HANDOFF_DIR, bandTarget, startSession, doneTurn, NOW} from './world.js';
```

- [ ] **Step 2：寫會失敗的測試**

附加在 `tests/register.test.ts` 的 slice e 區塊最後（`/handoff-resume <n>` 測試之後）：

```ts
test('beyond three, the rest sit behind a button, and git is asked only about the shown ones', async ($, on) => {
  const w = world(on, {files: fiveHandoffs});
  await startSession($);
  await w.flush();
  const band = await mountBand($);
  expect(await band.find({type: 'Text', text: /3\. 任務3/})).toBeDefined();
  expect(await band.find({type: 'Text', text: /4\. 任務4/})).toBeUndefined();
  const more = await band.find({key: 'more'});
  expect(more.props).toMatchObject({label: '還有 2 筆', variant: 'secondary'});
  expect(more.props.plain).toBeUndefined();
  expect(w.rec.git.some((key) => key.includes('refs/heads/feat/n3'))).toBe(true);
  expect(w.rec.git.some((key) => key.includes('refs/heads/feat/n4'))).toBe(false);
});
test('pressing the button lists everything with continuous numbers, asks git about the rest, and the button goes away', async ($, on) => {
  const w = world(on, {files: fiveHandoffs});
  await startSession($);
  await w.flush();
  const band = await mountBand($);
  await band.press({key: 'more'});
  await w.flush();
  expect(await band.find({type: 'Text', text: /4\. 任務4/})).toBeDefined();
  expect(await band.find({type: 'Text', text: /5\. 任務5/})).toBeDefined();
  expect(await band.find({key: 'resume-4'})).toBeDefined();
  expect(await band.find({key: 'more'})).toBeUndefined();
  expect(w.rec.git.some((key) => key.includes('refs/heads/feat/n4'))).toBe(true);
  expect(w.lastStatus()).toBe('有 5 筆未完成交接，輸入 /handoff-resume 查看');
});
test('an older automatic note on a branch is folded, counted, and labelled once expanded', async ($, on) => {
  const files = {...fiveHandoffs, ...Object.fromEntries([autoNote('11', '新的筆記', 'feat/same'), autoNote('10', '舊的筆記', 'feat/same')])};
  const w = world(on, {files});
  await startSession($);
  await w.flush();
  const before = await mountBand($);
  expect(await before.find({type: 'Text', text: '有 7 筆未完成交接'})).toBeDefined();
  expect(await before.find({type: 'Text', text: /新的筆記/})).toBeDefined();
  expect(await before.find({type: 'Text', text: /舊的筆記/})).toBeUndefined();
  expect((await before.find({key: 'more'})).props.label).toBe('還有 4 筆');
  await before.press({key: 'more'});
  await w.flush();
  // A mounted band is live: reading it again draws the current list. Mounting twice throws.
  const after = before;
  expect(await after.find({type: 'Text', text: /舊的筆記/})).toBeDefined();
  expect(await after.find({type: 'Text', text: '同 branch 較舊的自動筆記'})).toBeDefined();
});
```

> 數字怎麼來的：任務 1 至 5 的建立時間是 09:00 到 05:00（Z），自動筆記是 11:00（新）與 10:00（舊）。排序是 新的筆記、舊的筆記、任務 1、2、3、4、5，共 7 筆。舊的筆記是 `olderAuto`，不能進 `shown`，所以 `shown` = 新的筆記、任務 1、任務 2；`rest` = 舊的筆記、任務 3、4、5，共 4 筆。標頭「有 7 筆」，按鈕「還有 4 筆」。

- [ ] **Step 3：跑測試確認紅**

Run: `claude plugin test .`
Expected: 新增的 3 個測試 FAIL（找不到 `key: 'more'`）。

- [ ] **Step 4：實作 `expanded` atom**

`hooks/register.js` 在 `const listDone = ...` 之後加：

```js
// D16: whether the folded part of the start-up list has been asked for; reset by /clear like the other session state.
const expanded = atom({plugin: 'handoff-mod', key: 'expanded'}, false);
```

- [ ] **Step 5：實作 `buildList`**

把 `buildList` 中 `for (const item of ranked.shown) {` 一整段與最後的 `return` 改成：

```js
  const picked = (await read($, expanded)) ? [...ranked.shown, ...ranked.rest] : ranked.shown;
  const views = [];
  for (const item of picked) {
    const facts = await freshnessFacts({meta: item.meta, git: (args) => git($, args)});
    views.push({
      id: item.path,
      title: t(lang, 'list.item', {n: views.length + 1, task: item.fields.task || item.path.split('/').pop(), branch: item.meta.branch ?? '-', age: age(lang, now - item.meta.created)}),
      next: item.fields.next ? t(lang, 'list.next', {next: item.fields.next}) : '',
      facts: facts.map((fact) => factText(lang, fact)),
      auto: item.meta.source === 'auto',
      older: Boolean(item.olderAuto),
      claimed: item.claimedByOther,
    });
  }
  return {items: views, total: ranked.shown.length + ranked.collapsed};
```

（原本緊接在 `const ranked = ...` 之後的 `const views = [];` 要刪掉，避免重複宣告。）

- [ ] **Step 6：實作 `expandList`**

放在 `refreshList` 之後：

```js
/** D16: build the folded part too. Setting the flag first means a press during a rebuild still ends up expanded. */
async function expandList($) {
  await update($, expanded, () => true);
  await refreshList($, {force: true});
}
```

- [ ] **Step 7：band 的按鈕與標示**

在 `ui.render` 的 `list.items.forEach` 內，`if (item.auto) rows.push(...)` 之後加：

```js
        if (item.older) rows.push(Text({dimColor: true, children: [t(lang, 'list.older')]}));
```

並把

```js
          ...(list.total > list.items.length ? [Text({dimColor: true, children: [t(lang, 'list.more', {count: list.total - list.items.length})]})] : []),
```

換成：

```js
          ...(list.total > list.items.length ? [Button({key: 'more', label: t(lang, 'list.more', {count: list.total - list.items.length}), variant: 'secondary', onPress: () => expandList($)})] : []),
```

- [ ] **Step 7b：宣告 atom 型別**

`types/index.d.ts` 的 `PluginState['handoff-mod']` 在 `listDone` 之後加：

```ts
      /** The folded part of the start-up list was asked for (button or `/handoff-resume all`); D16. */
      expanded: boolean
```

沒有這一步，`claude plugin validate --strict .` 會報 `handoff-mod.expanded is not declared`（`claude plugin test` 不會報，所以測試全綠仍可能 validate 失敗）。

- [ ] **Step 8：跑測試確認全綠**

Run: `claude plugin test .`
Expected: 全部通過，包含 Task 3 的 3 個新測試與先前的邊框測試。若 `created: ...Z` 被解析器拒絕（`bad created`），把 `world.ts` 裡的時間改成 `+00:00` 結尾再跑一次。

- [ ] **Step 9：Commit（先問作者）**

```bash
git add plugins/handoff-mod/hooks/register.js plugins/handoff-mod/types/index.d.ts plugins/handoff-mod/tests/world.ts plugins/handoff-mod/tests/register.test.ts
git commit -m "feat(handoff-mod): expand the folded part of the start-up list with a button"
```

> 注意：`register.js` 與 `register.test.ts` 還有未 commit 的邊框樣式改動，會一起被加進這個 commit。執行者在 commit 前要先問作者：是否把邊框樣式拆成獨立 commit（用 `git add -p`），或接受併在一起。

---

### Task 4：`/handoff-resume all`、編號超出範圍、提示行

**Files:**
- Modify: `hooks/register.js`（`command.run` `handoff-resume` handler，約第 599–620 行）
- Test: `tests/register.test.ts`

- [ ] **Step 1：寫會失敗的測試**

附加在 Task 3 的測試之後：

```ts
test('/handoff-resume with folded items ends with a line saying how to list them all', async ($, on) => {
  const w = world(on, {files: fiveHandoffs});
  await $.command.run({command: 'handoff-resume', args: ''});
  expect(w.rec.logs[0]).toBe('有 5 筆未完成交接');
  expect(w.rec.logs.length).toBe(5);
  expect(w.rec.logs[4]).toBe('還有 2 筆，輸入 /handoff-resume all 全部列出');
});
test('/handoff-resume all lists every item, folded or not, and labels older automatic notes', async ($, on) => {
  const files = {...fiveHandoffs, ...Object.fromEntries([autoNote('11', '新的筆記', 'feat/same'), autoNote('10', '舊的筆記', 'feat/same')])};
  const w = world(on, {files});
  await $.command.run({command: 'handoff-resume', args: 'all'});
  expect(w.rec.logs[0]).toBe('有 7 筆未完成交接');
  expect(w.rec.logs.length).toBe(8);
  expect(w.rec.logs.some((line) => line.includes('舊的筆記') && line.includes('同 branch 較舊的自動筆記'))).toBe(true);
  expect(w.rec.logs.some((line) => line.includes('還有'))).toBe(false);
});
test('/handoff-resume all with nothing folded behaves like the plain command', async ($, on) => {
  const w = world(on, {files: twoHandoffs});
  await $.command.run({command: 'handoff-resume', args: 'all'});
  expect(w.rec.logs.length).toBe(3);
});
test('/handoff-resume <n> beyond the shown items expands first, then resumes', async ($, on) => {
  const w = world(on, {files: fiveHandoffs});
  await $.command.run({command: 'handoff-resume', args: '4'});
  const fourth = `${HANDOFF_DIR}/feat-n4--20261006-060000.md`;
  expect(w.store.get(`state:${fourth}`).status).toBe('resumed');
  expect(w.rec.fills[0]).toContain(fourth);
});
test('/handoff-resume with a number past the total, or zero, says the number is bad', async ($, on) => {
  const w = world(on, {files: fiveHandoffs});
  await $.command.run({command: 'handoff-resume', args: '6'});
  await $.command.run({command: 'handoff-resume', args: '0'});
  expect(w.rec.fills.length).toBe(0);
  expect(w.rec.logs).toContain('沒有第 6 筆。');
  expect(w.rec.logs).toContain('沒有第 0 筆。');
});
```

- [ ] **Step 2：跑測試確認紅**

Run: `claude plugin test .`
Expected: 前四個新測試 FAIL（沒有提示行、`all` 被當成壞編號、`4` 回「編號無效」）；`6`／`0` 那個可能已經通過，這是預期的（它鎖住既有行為）。

- [ ] **Step 3：實作**

把 `handoff-resume` handler 整段換成：

```js
  on('command.run', {command: 'handoff-resume'}, async ($, e) => {
    try {
      config = await loadConfig($);
      const lang = config.lang;
      const arg = String(e.args ?? '').trim();
      if (arg === 'all') await update($, expanded, () => true);
      await refreshList($, {force: true});
      if (!list) {
        $.ui.log(t(lang, 'list.none'));
      } else if (arg === '' || arg === 'all') {
        $.ui.log(t(lang, 'list.header', {count: list.total}));
        for (const item of list.items) {
          const extra = [item.next, ...item.facts, item.auto ? t(lang, 'list.auto') : '', item.older ? t(lang, 'list.older') : '', item.claimed ? t(lang, 'list.claimed') : ''].filter(Boolean);
          $.ui.log(extra.length ? `${item.title} — ${extra.join('；')}` : item.title);
        }
        if (list.total > list.items.length) $.ui.log(t(lang, 'list.moreCmd', {count: list.total - list.items.length}));
      } else {
        const n = Number(arg);
        // A number past the shown items may still be a folded one (D15/D16): expand, then look again.
        if (Number.isInteger(n) && n > list.items.length && list.total > list.items.length) await expandList($);
        const item = Number.isInteger(n) ? list?.items[n - 1] : undefined;
        if (item) await resume($, item);
        else $.ui.log(t(lang, 'list.bad', {n: arg}));
      }
    } catch { /* ignore */ }
    return {};
  });
```

- [ ] **Step 4：跑測試確認全綠**

Run: `claude plugin test .`
Expected: 全部通過。既有的「skip hides … logs.length toBe(3)」與「`/handoff-resume <n>` resumes item n」測試仍通過。

- [ ] **Step 5：validate**

Run: `claude plugin validate --strict .`
Expected: 通過（`gating hook 沒有 .catch` 的警告是刻意的，見專案 CLAUDE.md）。若出現與本次改動有關的新錯誤（例如新的 atom 未宣告），照訊息修正。

- [ ] **Step 6：Commit（先問作者）**

```bash
git add plugins/handoff-mod/hooks/register.js plugins/handoff-mod/tests/register.test.ts
git commit -m "feat(handoff-mod): add /handoff-resume all and expand on a number beyond the shown items"
```

---

### Task 5：變異檢查

專案慣例：改接線時，弄壞一處、確認有測試變紅、還原。每一項都是**暫時改、跑測試、改回來**，不 commit。

**Files:** `hooks/rank.js`、`hooks/register.js`（暫時修改，結束時 `git diff` 必須與 Task 4 結束時相同）

- [ ] **Step 1：記下乾淨狀態**

Run: `git diff --stat plugins/handoff-mod/hooks`
Expected: 只有 Task 1–4 的改動（記下輸出，最後比對）。

- [ ] **Step 2：逐項變異**，每項跑 `claude plugin test .`，確認指定測試變紅，再把該處改回：

| # | 暫時改動 | 預期變紅的測試 |
| --- | --- | --- |
| 1 | `rank.js`：`!item.olderAuto &&` 從 `shown` 的 filter 拿掉 | `an older automatic note … is folded`、`a folded older automatic note is not pulled up…` |
| 2 | `rank.js`：`groupKey` 只用 `branch`（拿掉 `root`） | `automatic notes on different branches or roots do not fold each other` |
| 3 | `rank.js`：`item.meta.source === 'auto' &&` 從 `flagged` 的條件拿掉 | `manual handoffs are never folded…` |
| 4 | `register.js`：`buildList` 的 `picked` 固定為 `ranked.shown` | `pressing the button lists everything…`、`/handoff-resume all lists every item…` |
| 5 | `register.js`：`buildList` 的 `picked` 固定為 `[...ranked.shown, ...ranked.rest]` | `beyond three, the rest sit behind a button, and git is asked only about the shown ones` |
| 6 | `register.js`：`more` 按鈕的 `onPress` 改成 `() => {}` | `pressing the button lists everything…` |
| 7 | `register.js`：`/handoff-resume` 拿掉 `if (arg === 'all') await update(...)` | `/handoff-resume all lists every item…` |
| 8 | `register.js`：拿掉 `await expandList($);` 那行 | `/handoff-resume <n> beyond the shown items expands first…` |

若某項**沒有**測試變紅，表示測試沒鎖住該行為：補測試，再重做該項。

- [ ] **Step 3：還原並確認**

Run: `git diff --stat plugins/handoff-mod/hooks` 並與 Step 1 比對；再跑 `claude plugin test .`
Expected: diff 相同，測試全綠。

（這個任務不 commit。）

---

### Task 6：文件

**Files:**
- Modify: `docs/superpowers/specs/2026-10-06-handoff-mod-design.md`
- Modify: `README.md`、`README-en.md`

- [ ] **Step 1：設計主檔的決定紀錄補 D15、D16**

在 D14 那一列（表格最後一列，約第 282 行）之後加兩列：

```markdown
| D15 | 同 `root` 加 `branch` 的較舊自動筆記是否折疊、折疊到哪 | **已決（Tom，2026-10-08）：折疊，不隱藏。** 每個 branch 只有最新一份自動筆記有資格進前 3 筆，較舊的進「還有 N 筆」（算進 N、展開後看得到並標示）；手動交接不分組；程式無法判斷是否同一任務，所以不做任務判斷。詳見 [啟動清單展開與自動筆記折疊](2026-10-08-handoff-list-expand-design.md) |
| D16 | 折疊項目何時建立資料 | **已決（Tom，2026-10-08）：展開時才建。** 「還有 N 筆」按鈕與 `/handoff-resume all` 把 `$.state` 的 `expanded` 設為 true 再重建；啟動時只替前 3 筆跑 git 新鮮度。`/handoff-resume <n>` 超出範圍時先展開再找 |
```

並把頂端第 4 行「待決項目 D1 至 D14」那句後面補上：`D15、D16 於 2026-10-08 增補（見 [啟動清單展開與自動筆記折疊](2026-10-08-handoff-list-expand-design.md)）。`

- [ ] **Step 2：元件 3 的「排序」一行**

把第 117 行的

```
- **排序：** 同 `root` 優先，其次同 `repo`，其餘依 `created` 由新到舊。預設展開 3 筆，其餘折疊成「還有 N 筆」。創建超過 14 天的預設折疊。
```

改成

```
- **排序：** 同 `root` 優先，其次同 `repo`，其餘依 `created` 由新到舊。預設展開 3 筆，其餘折疊成「還有 N 筆」按鈕，按下去（或 `/handoff-resume all`）展開（D16）。創建超過 14 天的預設折疊；同 `root` 加 `branch` 的較舊自動筆記也折疊，只有最新一份有資格進前 3 筆（D15）。
```

- [ ] **Step 3：README（繁中）**

`README.md` 第 16 行，`` `/handoff-resume 2` 接續第 2 筆。`` 之後、「接續只會…」之前插入：

```
超過 3 筆時，其餘折疊成「還有 N 筆」按鈕，按下去展開；`/handoff-resume all` 也能列出全部。同一個 branch 較舊的自動筆記預設折在裡面。
```

- [ ] **Step 4：README（英文）**

`README-en.md` 第 16 行，`` and `/handoff-resume 2` resumes the second one. `` 之後、`Resuming only fills` 之前插入：

```
Beyond three, the rest fold into a "N more" button that expands them; `/handoff-resume all` lists everything too. Older automatic notes on the same branch are folded there by default.
```

- [ ] **Step 5：確認公開 repo 規則**

Run: `grep -rn "/Users/" plugins/handoff-mod/docs/superpowers plugins/handoff-mod/README.md plugins/handoff-mod/README-en.md`
Expected: 沒有輸出（追蹤的檔案不放個人路徑）。

- [ ] **Step 6：Commit（先問作者）**

```bash
git add plugins/handoff-mod/docs plugins/handoff-mod/README.md plugins/handoff-mod/README-en.md
git commit -m "docs(handoff-mod): record D15 and D16 and document the expand button and /handoff-resume all"
```

> 設計文件（`2026-10-08-handoff-list-expand-design.md`）與本計畫都還沒 commit，一併加入上面的 `git add` 前先問作者。

---

### Task 7：收尾驗證與版號

- [ ] **Step 1：完整驗證**

Run: `claude plugin validate --strict .` 與 `claude plugin test .`
Expected: validate 通過；測試全綠，數量 = Task 1 Step 1 的基準加上本計畫新增的 8（rank）＋ 3 ＋ 5（register）= 基準 + 16。

- [ ] **Step 2：問作者版號**

`plugin.json` 目前是未 commit 的 0.1.1。先問作者：這次改動併進 0.1.1，還是升 0.1.2。專案教訓：改 hooks 行為就要升版號，否則 plugin cache 以版號為目錄名，`plugin update` 不會拉新程式碼。得到答案才改 `.claude-plugin/plugin.json`（以及 `package.json` 若作者要同步）。

- [ ] **Step 3：實機驗證（作者的 macOS，不是 Cloud）**

用 `claude --plugin-dir "$PWD"` 載入，在有 4 筆以上未完成交接的專案開新 session：

1. band 底部是「還有 N 筆」按鈕（不是純文字）；用 Tab 與滑鼠各按一次，確認展開。
2. 輸入 `/handoff-resume all`，確認列出全部，且較舊的自動筆記有標示。
3. 輸入 `/handoff-resume 4`（未展開前），確認直接接續第 4 筆。

結果寫進 `docs/implementation-results.md`，**Cloud 與作者的 macOS 分開記**，沒親眼看到的不要寫成已驗證。

---

## 自我檢查

**規格對照：**

| 規格章節 | 對應任務 |
| --- | --- |
| 1. `rank.js`（`rest`、`olderAuto`、`collapsed`、`hidden`、順序） | Task 2 |
| 2. `register.js`（`expanded`、`buildList`、按鈕、`refreshList` 鎖） | Task 3 |
| 3. `/handoff-resume`（`all`、`<n>` 超出範圍、提示行） | Task 4 |
| 4. i18n（`list.moreCmd`、`list.older`、`list.more` 改當按鈕標籤） | Task 1、3、4 |
| 錯誤處理（git 失敗、重建拋錯、無折疊時按 `all`） | Task 4 的 handler 沿用既有 `try/catch`；`all` 無折疊的行為由 `with nothing folded` 測試鎖住 |
| 測試清單（rank 與 register 各項） | Task 2、3、4；變異檢查 Task 5 |
| 文件與版號 | Task 6、7 |
| 「不做」：不改 `SHOWN`、14 天、7 天、`autoNote` 預設與寫入條件、不刪檔、不做收合、`all` 不截斷 | 沒有任務動到這些 |

**型別與名稱一致：** `rankHandoffs` 回傳 `{shown, rest, collapsed, hidden}`；項目旗標 `olderAuto`（rank 輸出）→ view 欄位 `older`（`buildList`）→ band 與指令都讀 `item.older`；atom 名 `expanded`；helper 名 `expandList`；i18n key `list.moreCmd`、`list.older`、`list.more`；按鈕 key `more`。各任務用的名稱相同。

**已知需執行者留意的地方：**

- `register.js` 與 `register.test.ts` 有未 commit 的邊框改動，Task 3 commit 前要問作者是否拆開。
