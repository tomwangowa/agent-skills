# 放棄交接與「本 session 忽略」實作計畫

> **給執行者：** 必讀子技能：`superpowers:subagent-driven-development`（建議）或 `superpowers:executing-plans`，逐任務執行。步驟用 `- [ ]` 追蹤。

**目標：** 新增 `/handoff-resume drop <編號|all>` 把交接標成放棄（D17），並把按鈕「略過」改名為「本 session 忽略」（D18）。

**架構：** 放棄只在 `$.store` 寫 `state:<path>` = `{status: 'abandoned', at, sessionId}`，交接檔不動；`abandoned` 本來就不在 `OPEN_STATUSES`，所以 `rank.js` 不用改。`register.js` 新增兩個函式 `abandon`（寫一筆）與 `dropCommand`（解析目標、跳過被認領的、輸出結果），`/handoff-resume` 的 handler 把參數拆成字，`drop` 走新函式。其餘是字串（`i18n.js`）與提示行。

**技術：** Claude Code mod，純 ES modules，`claude-code/testing`。

**規格：** [放棄交接與「本 session 忽略」](../specs/2026-10-08-handoff-drop-design.md)（D17、D18）。**分支：** `feat/handoff-drop`（從合併後的 `main`，`37d9ed1`，開出）。

**每個 commit 前都要先問作者。** 下面標「Commit（先問作者）」的步驟，執行者要先停下來問，得到同意才下指令；前一次的同意不延續。commit 訊息結尾加 `Co-Authored-By: Claude Sonnet 5.5 <noreply@anthropic.com>`。

**測試指令：** 在 `plugins/handoff-mod` 目錄下執行 `claude plugin test .`（只吃資料夾，沒有單檔篩選，所以「跑單一測試」都是整批跑、看指定名稱的結果）。快速只看結果行：`claude plugin test . 2>&1 | grep -E "^\(fail\)| pass$| fail$"`。本機沒有 `tsc`，型別不會被檢查；每個任務結束前也跑 `claude plugin validate --strict .`（`plugin test` 看不出的 manifest 問題只有它抓得到）。

---

## 檔案結構

| 檔案 | 動作 | 責任 |
| --- | --- | --- |
| `hooks/i18n.js` | 修改 | `list.skip` 改名、`cmd.resume`、`cmd.resume.hint` 改文案；新增 `list.dropHint`、`drop.usage`、`drop.header`、`drop.claimed`、`drop.none` |
| `hooks/register.js` | 修改 | `abandon`、`dropCommand`、`/handoff-resume` handler、無參數與 `all` 輸出的提示行 |
| `tests/world.ts` | 修改 | 新增 `fiveFile(n)`，`fiveHandoffs` 改用它 |
| `tests/register.test.ts` | 修改 | 更新 4 個既有測試的行數；新增 drop、提示行、按鈕標籤的測試 |
| `.claude-plugin/plugin.json` | 修改 | 版號 0.1.2 → 0.1.3 |
| `docs/superpowers/specs/2026-10-06-handoff-mod-design.md` | 修改 | D17、D18；元件 3 的「按鈕」一行 |
| `README.md`、`README-en.md` | 修改 | 各補一句 |

`rank.js`、`types/index.d.ts` 不動（沒有新的 `$.state` atom，`abandoned` 本來就被排除）。

---

### Task 1：字串與按鈕標籤（D18）

**Files:**
- Modify: `hooks/i18n.js`（zh-TW 區塊與 en 區塊）
- Test: `tests/register.test.ts`（附加在 `skip hides the list for this session…` 測試之前）

- [ ] **Step 1：先跑基準**

Run: `cd plugins/handoff-mod && claude plugin test . 2>&1 | grep -E "^\(fail\)| pass$| fail$"`
Expected: `170 pass`、`0 fail`。若不是，先停下來告訴作者。

- [ ] **Step 2：寫會失敗的測試**

在 `tests/register.test.ts` 的 `test('skip hides the list for this session, and /handoff-resume still shows it'` 之前加：

```ts
test('the skip button says it only ignores the list for this session, and changes no state', async ($, on) => {
  const w = world(on, {files: twoHandoffs});
  await startSession($);
  await w.flush();
  const band = await mountBand($);
  expect((await band.find({key: 'skip'})).props.label).toBe('本 session 忽略');
  await band.press({key: 'skip'});
  expect(w.lastStatus()).toBe(undefined);
  expect([...w.store.keys()].some((key) => key.startsWith('state:'))).toBe(false);
});
```

- [ ] **Step 3：跑測試確認紅**

Run: `claude plugin test . 2>&1 | grep -E "^\(fail\)| pass$| fail$"`
Expected: 只有 `the skip button says it only ignores…` FAIL（標籤還是「略過」）。

- [ ] **Step 4：改 zh-TW 字串**

在 `hooks/i18n.js` zh-TW 區塊：

把 `'list.skip': '略過',` 改成：

```js
    'list.skip': '本 session 忽略',
```

把 `'cmd.resume': '列出未完成的交接；/handoff-resume <編號> 接續其中一筆',` 改成：

```js
    'cmd.resume': '列出未完成的交接；/handoff-resume <編號> 接續其中一筆；drop <編號|all> 放棄',
```

把 `'cmd.resume.hint': '[編號]',` 改成：

```js
    'cmd.resume.hint': '[編號|all|drop]',
```

在 `'list.bad': '沒有第 {n} 筆。',` 之後加：

```js
    'list.dropHint': '不要的可以放棄：/handoff-resume drop <編號|all>',
    'drop.usage': '用法：/handoff-resume drop <編號|all>',
    'drop.header': '已放棄 {count} 筆，剩下的編號已重排：',
    'drop.claimed': '另一個 session 正在接續，沒有放棄：{title}',
    'drop.none': '沒有可以放棄的交接。',
```

- [ ] **Step 5：改 en 字串**

en 區塊：

`'list.skip': 'Skip',` → `'list.skip': 'Ignore for this session',`

`'cmd.resume': 'List unfinished handoffs; "/handoff-resume <n>" resumes one',` →

```js
    'cmd.resume': 'List unfinished handoffs; "/handoff-resume <n>" resumes one; "drop <n|all>" abandons',
```

`'cmd.resume.hint': '[n]',` → `'cmd.resume.hint': '[n|all|drop]',`

在 `'list.bad': 'There is no item {n}.',` 之後加：

```js
    'list.dropHint': 'Not needed? Abandon them: /handoff-resume drop <n|all>',
    'drop.usage': 'Usage: /handoff-resume drop <n|all>',
    'drop.header': 'Abandoned {count}; the remaining items are renumbered:',
    'drop.claimed': 'Another session is resuming this, not abandoned: {title}',
    'drop.none': 'Nothing to abandon.',
```

- [ ] **Step 6：跑測試與 validate**

Run: `claude plugin test . 2>&1 | grep -E "^\(fail\)| pass$| fail$"` 與 `claude plugin validate --strict . 2>&1 | grep -E "✔|✘"`
Expected: `171 pass`、`0 fail`（基準 170 加這個新測試）；validate 通過。既有的「兩種語言 key 相同」「占位符相同」測試也要綠（`{count}`、`{title}` 兩邊都有）。

（這個任務先不 commit，Task 3 結束一起。）

---

### Task 2：無參數與 `all` 輸出的提示行

**Files:**
- Modify: `tests/register.test.ts`（更新 4 個既有測試、新增 1 個）
- Modify: `hooks/register.js`（`/handoff-resume` handler 的列表分支）

- [ ] **Step 1：更新既有測試的行數（先讓它們變紅）**

在 `tests/register.test.ts`：

1. `skip hides the list for this session…` 測試裡 `expect(w.rec.logs.length).toBe(3);` → `toBe(4);`
2. `/handoff-resume with folded items ends with a line saying how to list them all` 測試裡 `expect(w.rec.logs.length).toBe(5);` → `toBe(6);`（`logs[4]` 那行不變，仍是 `moreCmd`）
3. `/handoff-resume all lists every item, folded or not…` 測試裡 `expect(w.rec.logs.length).toBe(8);` → `toBe(9);`
4. `/handoff-resume all with nothing folded behaves like the plain command` 測試裡 `expect(w.rec.logs.length).toBe(3);` → `toBe(4);`

- [ ] **Step 2：新增提示行的測試**

附加在 `/handoff-resume all with nothing folded…` 測試之後：

```ts
test('/handoff-resume ends with a line saying how to abandon, after the "more" line when there is one', async ($, on) => {
  const w = world(on, {files: fiveHandoffs});
  await $.command.run({command: 'handoff-resume', args: ''});
  expect(w.rec.logs[4]).toBe('還有 2 筆，輸入 /handoff-resume all 全部列出');
  expect(w.rec.logs[5]).toBe('不要的可以放棄：/handoff-resume drop <編號|all>');
  w.rec.logs.length = 0;
  await $.command.run({command: 'handoff-resume', args: 'all'});
  expect(w.rec.logs[w.rec.logs.length - 1]).toBe('不要的可以放棄：/handoff-resume drop <編號|all>');
});
test('with no handoffs, /handoff-resume says so and has no abandon hint', async ($, on) => {
  const w = world(on);
  await $.command.run({command: 'handoff-resume', args: ''});
  expect(w.rec.logs).toEqual(['目前沒有未完成的交接。']);
});
```

- [ ] **Step 3：跑測試確認紅**

Run: `claude plugin test . 2>&1 | grep -E "^\(fail\)| pass$| fail$"`
Expected: 上面 4 個更新過行數的測試與第一個新測試 FAIL；`with no handoffs…` 通過（鎖住既有行為）。

- [ ] **Step 4：實作**

在 `hooks/register.js` 的 `/handoff-resume` handler 裡，把

```js
        if (list.total > list.items.length) $.ui.log(t(lang, 'list.moreCmd', {count: list.total - list.items.length}));
```

改成：

```js
        if (list.total > list.items.length) $.ui.log(t(lang, 'list.moreCmd', {count: list.total - list.items.length}));
        $.ui.log(t(lang, 'list.dropHint'));
```

- [ ] **Step 5：跑測試確認全綠**

Run: `claude plugin test . 2>&1 | grep -E "^\(fail\)| pass$| fail$"`
Expected: `173 pass`、`0 fail`（171 加上本任務新增的 2 個）。

---

### Task 3：`/handoff-resume drop`（D17）

**Files:**
- Modify: `tests/world.ts`（`fiveFile`）
- Modify: `tests/register.test.ts`（新增 drop 測試）
- Modify: `hooks/register.js`（`abandon`、`dropCommand`、handler）
- Modify: `.claude-plugin/plugin.json`（版號）

- [ ] **Step 1：`tests/world.ts` 新增 `fiveFile`**

把 `fiveHandoffs` 整段換成：

```ts
/** The path of the nth handoff in `fiveHandoffs`; task 1 is the newest. */
export const fiveFile = (n: number) => `${HANDOFF_DIR}/feat-n${n}--20261006-0${10 - n}0000.md`;
/** Five handoffs on five branches, all fresh; task 1 is the newest. */
export const fiveHandoffs: Record<string, string> = Object.fromEntries([1, 2, 3, 4, 5].map((n) => [
  fiveFile(n),
  handoffText({created: `2026-10-06T0${10 - n}:00:00Z`}).replace('task: 修正登入逾時', `task: 任務${n}`).replace('branch: feat/login-timeout', `branch: feat/n${n}`),
]));
```

並在 `tests/register.test.ts` 的 import 補上 `fiveFile`：

```ts
import {world, twoHandoffs, fiveHandoffs, fiveFile, autoNote, fileA,
```

（保留該行其餘內容不變，只在 `fiveHandoffs,` 之後插入 `fiveFile,`。）

- [ ] **Step 2：寫會失敗的測試**

附加在 Task 2 新增的測試之後：

```ts
const CLAIMED_BY_B = {sessionId: 'sess-B', at: NOW - 1000};

test('/handoff-resume drop <n> marks the item abandoned, reloads the list and says the numbers moved', async ($, on) => {
  const w = world(on, {files: fiveHandoffs});
  await $.command.run({command: 'handoff-resume', args: 'drop 2'});
  expect(w.store.get(`state:${fiveFile(2)}`)).toMatchObject({status: 'abandoned', sessionId: 'sess-A'});
  expect(w.rec.logs.length).toBe(2);
  expect(w.rec.logs[0]).toBe('已放棄 1 筆，剩下的編號已重排：');
  expect(w.rec.logs[1]).toContain('2. 任務2');
  w.rec.logs.length = 0;
  await $.command.run({command: 'handoff-resume', args: ''});
  expect(w.rec.logs[0]).toBe('有 4 筆未完成交接');
});
test('/handoff-resume drop <n> beyond the shown items expands first, then abandons', async ($, on) => {
  const w = world(on, {files: fiveHandoffs});
  await $.command.run({command: 'handoff-resume', args: 'drop 5'});
  expect(w.store.get(`state:${fiveFile(5)}`)).toMatchObject({status: 'abandoned'});
  expect(w.rec.logs[1]).toContain('5. 任務5');
});
test('/handoff-resume drop <n> leaves an item another session is resuming alone', async ($, on) => {
  const w = world(on, {files: fiveHandoffs, store: {[`claim:${fiveFile(1)}`]: CLAIMED_BY_B}});
  await $.command.run({command: 'handoff-resume', args: 'drop 1'});
  expect(w.store.get(`state:${fiveFile(1)}`)).toBe(undefined);
  expect(w.rec.logs.length).toBe(1);
  expect(w.rec.logs[0]).toContain('另一個 session 正在接續，沒有放棄：1. 任務1');
});
test('/handoff-resume drop all abandons everything listed, folded or not, except what another session is resuming', async ($, on) => {
  const w = world(on, {files: fiveHandoffs, store: {[`claim:${fiveFile(1)}`]: CLAIMED_BY_B}});
  await $.command.run({command: 'handoff-resume', args: 'drop all'});
  for (const n of [2, 3, 4, 5]) expect(w.store.get(`state:${fiveFile(n)}`)).toMatchObject({status: 'abandoned'});
  expect(w.store.get(`state:${fiveFile(1)}`)).toBe(undefined);
  expect(w.rec.logs[0]).toBe('已放棄 4 筆，剩下的編號已重排：');
  expect(w.rec.logs.length).toBe(6);
  expect(w.rec.logs[5]).toContain('另一個 session 正在接續，沒有放棄：1. 任務1');
  w.rec.logs.length = 0;
  await $.command.run({command: 'handoff-resume', args: ''});
  expect(w.rec.logs[0]).toBe('有 1 筆未完成交接');
});
test('/handoff-resume drop all with everything claimed abandons nothing and says so', async ($, on) => {
  const w = world(on, {files: twoHandoffs, store: {[`claim:${fileA}`]: CLAIMED_BY_B, [`claim:${fileB}`]: CLAIMED_BY_B}});
  await $.command.run({command: 'handoff-resume', args: 'drop all'});
  expect([...w.store.keys()].some((key) => key.startsWith('state:'))).toBe(false);
  expect(w.rec.logs.length).toBe(3);
  expect(w.rec.logs[2]).toBe('沒有可以放棄的交接。');
});
test('after dropping everything the band and the status line are gone', async ($, on) => {
  const w = world(on, {files: twoHandoffs});
  await startSession($);
  await w.flush();
  await $.command.run({command: 'handoff-resume', args: 'drop all'});
  await w.flush();
  expect(w.lastStatus()).toBe(undefined);
  expect(await (await mountBand($)).find({key: 'skip'})).toBeUndefined();
});
test('an abandoned handoff does not come back at the next start', async ($, on) => {
  const w = world(on, {files: twoHandoffs});
  await $.command.run({command: 'handoff-resume', args: 'drop 1'});
  await startSession($);
  await w.flush();
  expect(w.lastStatus()).toBe('有 1 筆未完成交接，輸入 /handoff-resume 查看');
});
test('/handoff-resume drop with no usable target prints the usage, and with a number out of range says there is no such item', async ($, on) => {
  const w = world(on, {files: fiveHandoffs});
  for (const args of ['drop', 'drop abc', 'drop 1.5', 'drop 0', 'drop -1', 'drop 99']) await $.command.run({command: 'handoff-resume', args});
  expect(w.rec.logs).toEqual([
    '用法：/handoff-resume drop <編號|all>', '用法：/handoff-resume drop <編號|all>', '用法：/handoff-resume drop <編號|all>',
    '沒有第 0 筆。', '沒有第 -1 筆。', '沒有第 99 筆。',
  ]);
  expect([...w.store.keys()].some((key) => key.startsWith('state:'))).toBe(false);
});
```

- [ ] **Step 3：跑測試確認紅**

Run: `claude plugin test . 2>&1 | grep -E "^\(fail\)| pass$| fail$"`
Expected: 上面 8 個新測試全部 FAIL（`drop` 目前被當成壞編號）。

- [ ] **Step 4：實作 `abandon` 與 `dropCommand`**

在 `hooks/register.js` 的 `resume` 函式之後（`/** A handoff run starts when the skill is expanded…` 註解之前）加：

```js
/** D17: mark a handoff abandoned on this machine. Only the store record changes; the file is never touched (invariant 6). */
async function abandon($, item, now, sessionId) {
  try {
    await $.store.set(`state:${item.id}`, {status: 'abandoned', at: now, sessionId});
    return true;
  } catch {
    return false;
  }
}

/** `/handoff-resume drop <n|all>`: abandon one listed item, or every listed item that no other session is resuming. */
async function dropCommand($, target) {
  const lang = config.lang;
  const isAll = target === 'all';
  const n = Number(target);
  if (!isAll && !(target !== undefined && Number.isInteger(n))) {
    $.ui.log(t(lang, 'drop.usage'));
    return;
  }
  if (!list) {
    $.ui.log(t(lang, 'list.none'));
    return;
  }
  // A number past the shown items may still be a folded one (D16): expand, then look again.
  if (!isAll && n > list.items.length && list.total > list.items.length) await expandList($);
  const picked = isAll ? [...list.items] : [list?.items[n - 1]].filter(Boolean);
  if (picked.length === 0) {
    $.ui.log(t(lang, 'list.bad', {n: target}));
    return;
  }
  const skipped = picked.filter((item) => item.claimed);
  if (!isAll && skipped.length) {
    $.ui.log(t(lang, 'drop.claimed', {title: skipped[0].title}));
    return;
  }
  const now = await $.clock.now();
  const sessionId = await $.session.id();
  const done = [];
  for (const item of picked) {
    if (!item.claimed && (await abandon($, item, now, sessionId))) done.push(item);
  }
  if (done.length === 0) {
    for (const item of skipped) $.ui.log(t(lang, 'drop.claimed', {title: item.title}));
    $.ui.log(t(lang, 'drop.none'));
    return;
  }
  await refreshList($, {force: true});
  $.ui.log(t(lang, 'drop.header', {count: done.length}));
  for (const item of done) $.ui.log(item.title);
  for (const item of skipped) $.ui.log(t(lang, 'drop.claimed', {title: item.title}));
}
```

- [ ] **Step 5：改 handler**

把 `/handoff-resume` handler 開頭

```js
      const arg = String(e.args ?? '').trim();
      if (arg === 'all') await update($, expanded, () => true);
      await refreshList($, {force: true});
      if (!list) {
```

換成：

```js
      const arg = String(e.args ?? '').trim();
      const words = arg === '' ? [] : arg.split(/\s+/);
      const dropping = words[0] === 'drop';
      if (arg === 'all' || (dropping && words[1] === 'all')) await update($, expanded, () => true);
      await refreshList($, {force: true});
      if (dropping) {
        await dropCommand($, words[1]);
      } else if (!list) {
```

（其餘分支不動；`else if (arg === '' || arg === 'all')` 與最後的 `else` 保持原樣。）

- [ ] **Step 6：跑測試與 validate**

Run: `claude plugin test . 2>&1 | grep -E "^\(fail\)| pass$| fail$"` 與 `claude plugin validate --strict . 2>&1 | grep -E "✔|✘"`
Expected: `181 pass`、`0 fail`（173 加上本任務新增的 8 個）；validate 通過。

- [ ] **Step 7：升版號**

`.claude-plugin/plugin.json` 的 `"version": "0.1.2"` 改成 `"0.1.3"`。（改了 hook 行為；版號沒變時 `plugin update` 不會拉新程式碼。）

Run: `grep '"version"' .claude-plugin/plugin.json`
Expected: `"version": "0.1.3",`

- [ ] **Step 8：Commit（先問作者）**

```bash
git add plugins/handoff-mod/.claude-plugin/plugin.json plugins/handoff-mod/hooks/i18n.js plugins/handoff-mod/hooks/register.js plugins/handoff-mod/tests/world.ts plugins/handoff-mod/tests/register.test.ts
git commit -m "feat(handoff-mod): add /handoff-resume drop and rename the skip button to say it is per session"
```

---

### Task 4：變異檢查

專案慣例：改接線時，弄壞一處、確認有測試變紅、還原。每一項都是**暫時改、跑測試、改回來**，不 commit。

**Files:** `hooks/register.js`（暫時修改；結束時內容必須與 Task 3 結束時相同）

- [ ] **Step 1：存一份乾淨副本**

Run: `cp hooks/register.js /private/tmp/register.js.clean`（用你的 scratchpad 目錄代替 `/private/tmp`）
Expected: 無輸出。

- [ ] **Step 2：逐項變異**，每項改完跑 `claude plugin test .`，確認指定測試變紅，再把該處改回：

| # | 暫時改動（舊 → 新） | 預期變紅的測試 |
| --- | --- | --- |
| 1 | `status: 'abandoned', at, sessionId` → `status: 'resumed', at, sessionId`（`abandon` 內） | `drop <n> marks the item abandoned…`、`drop all abandons everything listed…` |
| 2 | `if (!isAll && skipped.length) {` → `if (false) {` | `drop <n> leaves an item another session is resuming alone` |
| 3 | `if (!item.claimed && (await abandon(` → `if ((await abandon(` | `drop all abandons everything listed…`、`drop all with everything claimed…` |
| 4 | `if (arg === 'all' \|\| (dropping && words[1] === 'all'))` → `if (arg === 'all')` | `drop all abandons everything listed, folded or not…` |
| 5 | 把 `dropCommand` 裡 `await expandList($);` 改成 `/* mutated */` | `drop <n> beyond the shown items expands first, then abandons` |
| 6 | 把 `dropCommand` 裡 `await refreshList($, {force: true});` 那行刪掉 | `after dropping everything the band and the status line are gone` |
| 7 | 刪掉 handler 裡 `$.ui.log(t(lang, 'list.dropHint'));` | `ends with a line saying how to abandon…`、更新過行數的 4 個測試 |
| 8 | `if (!isAll && !(target !== undefined && Number.isInteger(n))) {` → `if (false) {` | `drop with no usable target prints the usage…` |

若某項**沒有**測試變紅，表示測試沒鎖住該行為：補測試，再重做該項。

- [ ] **Step 3：還原並確認**

Run: `diff hooks/register.js /private/tmp/register.js.clean && echo same`，再跑 `claude plugin test . 2>&1 | grep -E " pass$| fail$"`
Expected: `same`、`181 pass`、`0 fail`。

（這個任務不 commit。）

---

### Task 5：文件

**Files:**
- Modify: `docs/superpowers/specs/2026-10-06-handoff-mod-design.md`
- Modify: `README.md`、`README-en.md`

- [ ] **Step 1：設計主檔的決定紀錄補 D17、D18**

在 `| D16 |` 那一列之後加：

```markdown
| D17 | 一份不打算接續的交接，怎麼讓它不再出現 | **已決（Tom，2026-10-08）：** 指令 `/handoff-resume drop <編號>` 與 `drop all`，只在 `$.store` 寫 `state:<path>` = `{status: 'abandoned', ...}`，交接檔不動；必須打完整的 `all`、逐筆列出放棄了哪些、被別的 session 正在接續的不動；不做復原指令。詳見 [放棄交接與「本 session 忽略」](2026-10-08-handoff-drop-design.md) |
| D18 | 按鈕「略過」的名稱 | **已決（Tom，2026-10-08）：** 改名為「本 session 忽略」（英文 `Ignore for this session`），行為不變。原名讓人以為「別再提醒我」，實際上新 session 會重新出現 |
```

把第 4 行的 `（D15、D16 於 2026-10-08 增補，見 [啟動清單展開與自動筆記折疊](2026-10-08-handoff-list-expand-design.md)）` 改成：

```
（D15、D16 於 2026-10-08 增補，見 [啟動清單展開與自動筆記折疊](2026-10-08-handoff-list-expand-design.md)；D17、D18 見 [放棄交接與「本 session 忽略」](2026-10-08-handoff-drop-design.md)）
```

把元件 3 的 `- **按鈕：** 接續、略過。「略過」只對這個 session 有效，不改狀態。` 改成：

```
- **按鈕：** 接續、本 session 忽略（D18）。「本 session 忽略」只對這個 session 有效，不改狀態；要讓一份交接不再出現用 `/handoff-resume drop`（D17）。
```

- [ ] **Step 2：README（繁中）**

`README.md` 第 16 行，`同一個 branch 較舊的自動筆記預設折在裡面。` 之後、`接續只會…` 之前插入：

```
不要的交接可以用 `/handoff-resume drop <編號>`（或 `drop all`）放棄；清單上的「本 session 忽略」只對這個 session 有效，下次開 session 還會再出現。
```

- [ ] **Step 3：README（英文）**

`README-en.md` 第 16 行，`Older automatic notes on the same branch are folded there by default. ` 之後、`Resuming only fills` 之前插入：

```
Handoffs you no longer need can be abandoned with `/handoff-resume drop <n>` (or `drop all`); the "Ignore for this session" button only hides the list for this session, and the handoffs show up again at the next start. 
```

- [ ] **Step 4：確認公開 repo 規則**

Run: `grep -rn "/Users/" README.md README-en.md docs/superpowers/specs/2026-10-08-handoff-drop-design.md docs/superpowers/plans/2026-10-08-handoff-drop.md | grep -v "grep -rn"`
Expected: 沒有輸出（追蹤的檔案不放個人路徑）。

- [ ] **Step 5：Commit（先問作者）**

```bash
git add plugins/handoff-mod/README.md plugins/handoff-mod/README-en.md plugins/handoff-mod/docs
git commit -m "docs(handoff-mod): record D17 and D18, and document /handoff-resume drop"
```

> 設計文件（`2026-10-08-handoff-drop-design.md`）與本計畫都還沒 commit，上面的 `git add plugins/handoff-mod/docs` 會一併加入；加入前先問作者。

---

### Task 6：收尾驗證

- [ ] **Step 1：完整驗證**

Run: `claude plugin validate --strict .` 與 `claude plugin test .`
Expected: validate 通過；測試 `181 pass`、`0 fail`（0.1.2 的 170 加上本計畫新增的 11 個：Task 1 一個、Task 2 兩個、Task 3 八個）。

- [ ] **Step 2：實機驗證（作者的 macOS，不是 Cloud）**

用 `claude --plugin-dir "$PWD"` 載入（或走 marketplace 更新到 0.1.3），在有 4 筆以上未完成交接的專案開新 session，逐項試：

1. **按鈕標籤：** 清單底下的按鈕寫「本 session 忽略」；按下去清單收起，開新 session 同樣的交接會再出現（這是預期行為）。
2. **提示行：** `/handoff-resume` 輸出最後一行是「不要的可以放棄：/handoff-resume drop <編號|all>」。
3. **`drop <編號>`：** 放棄一份你不要的舊交接，輸出列出那一筆與「編號已重排」；開新 session 確認它沒有再出現。
4. **`drop <編號>` 超出顯示範圍：** 用折疊裡的編號，確認直接放棄、沒有回「沒有第 n 筆」。
5. **被認領的：** 在另一個 session 按一份交接的「接續」（12 小時內有效），回到這個 session 對它 `drop`，確認回「另一個 session 正在接續，沒有放棄」，且 `drop all` 會跳過它。
6. **`drop all`：** 最後再試，確認逐筆列出、清單與狀態列消失。

結果寫進 `docs/implementation-results.md`，**Cloud 與作者的 macOS 分開記**，沒親眼看到的不要寫成已驗證。

---

## 自我檢查

**規格對照：**

| 規格章節 | 對應任務 |
| --- | --- |
| D18 按鈕改名 | Task 1 |
| i18n 表（含 `cmd.resume`、`cmd.resume.hint`、新 key） | Task 1 |
| 無參數與 `all` 的提示行；既有測試行數要更新 | Task 2 |
| D17 `drop <n>`、`drop all`、編號超出範圍先展開 | Task 3 |
| 被別的 session 認領的不放棄（單筆回訊息、`all` 跳過） | Task 3 |
| 放棄後重建清單、輸出「編號已重排」、全放棄後 band 與狀態列消失 | Task 3 |
| 錯誤處理（用法、`list.bad`、store 寫入失敗、空清單） | Task 3 的 `dropCommand` 與 `abandon`；`list.none` 沿用既有分支 |
| 測試清單 | Task 1–3；變異檢查 Task 4 |
| 文件與版號 | Task 3 Step 7、Task 5 |
| 「不做」：復原指令、band 按鈕、放棄次數統計、延後提醒、改 7／14 天規則 | 沒有任務動到這些 |

**型別與名稱一致：** `abandon($, item, now, sessionId)` 回傳布林；`dropCommand($, target)`，`target` 是 `words[1]`；view 欄位 `claimed`、`title`、`id`（來自 0.1.2 的 `buildList`）；i18n key `list.dropHint`、`drop.usage`、`drop.header`、`drop.claimed`（占位符 `{title}`）、`drop.none`、`drop.header`（占位符 `{count}`）；測試輔助 `fiveFile(n)`。各任務用的名稱相同。

**已知需執行者留意的地方：**

- Task 3 的測試 `drop all with everything claimed` 預期輸出共 3 行：兩行 `drop.claimed` 加一行 `drop.none`（順序是先跳過的、最後 `drop.none`）。
- `drop` 沒給第二個字時，handler 仍會先 `refreshList`（多跑一次 git），這是為了維持「每個子指令都先刷新」的單純結構，不是遺漏。
- 本計畫新增的測試數是 Task 1 一個、Task 2 兩個、Task 3 八個，共 11 個；各任務結束的通過數（171、173、181）是以 0.1.2 的 170 為基準累加，若基準不同，以實際基準加上新增數為準。
