# 面板三頁（即時、次要、Quick Notes）實作計畫

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** 面板分成三頁，即時頁與次要頁顯示唯讀資訊，Quick Notes 頁提供跨啟動保留的多行筆記，依 git 共用目錄分開保存。

**Architecture:** 頁碼與筆記狀態留在 `register.js` 的模組變數裡，與 `collapsed` 同規則。版面與狀態轉換寫成純函式（`view.js`、`notes.js`、`worktree.js`），方便單獨測試。`$.store` 的讀寫、計時器與事件掛鉤只在 `register.js`。

**Tech Stack:** Claude Code plugin function hooks（JavaScript ESM）、`claude-code/testing` 測試 kit、`$.store`、`$.session.model()`、`$.session.usage()`、`turn.step` hook。

**Spec:** `plugins/attention-mod/docs/superpowers/specs/2026-10-29-attention-mod-tab-pages-design.md`（決策紀錄：`plugins/attention-mod/docs/decisions/2026-10-29-quick-notes-store.md`）

## Global Constraints

- 版號：`plugin.json` 與 `hooks/meta.js` 同時改為 `0.6.0`。`package.json` 目前是 `0.4.0`，這是既有的不一致，本計畫不改它。
- Quick Notes 上限：32,768 個 code point（用 `[...text].length` 計算，不用 UTF-16 長度）。
- `$.store` 是整個插件共用的空間，超過 4 MiB 拒絕寫入。
- 存檔閒置門檻 1000 ms；寫入失敗後重試間隔 5000 ms；計時器每 1000 ms 執行一次。
- Quick Notes key：有 git 共用目錄時為 `notes:<共用目錄>`；不在 git 時為 `notes-cwd:<目錄>`。
- 頁籤 hotkey 為 `"1"`、`"2"`、`"3"`。`/attention` 只接受完整的 `1`、`2`、`3`（去除前後空白後）；其他值只開面板。
- `$.session.usage` 只能用 `{breakdown:'summary'}`。`full` 會送 token 計數請求，禁止使用。
- Quick Notes 輸入框不設 `autoFocus`；回饋表單的 `autoFocus` 拿掉。
- 頁碼規則與 `collapsed` 相同：模組變數，跨 `/clear` 與 resume 保留，只有插件 reload 重設。
- 改 `hooks/` 前先載入 `plugin-authoring` skill。
- 每個新回歸測試先寫、先看它失敗，再實作。
- 本計畫不含 commit 步驟。commit、push、開 PR 都要等 Tom 批准。
- 不增加身分列、不註冊 attachment／hook-context／compaction／tool-message／note 這幾種 door。

## Review Focus

1. **筆記長度剛好在上限邊界，且含 emoji 或其他代理對字元。** 預期：正好 32,768 個 code point 會存；32,769 個拒絕存並顯示「未存：超過上限」；不截斷。測試放在 Task 2（純函式）與 Task 7（存檔）。
2. **`$.store.get` 回傳非字串的髒資料（數字、物件）。** 預期：進入讀取失敗狀態，不存檔，不拋錯。`undefined` 代表空白筆記，是正常就緒狀態。測試放在 Task 6。
3. **`/attention` 參數的邊界。** `/attention 2 extra`、`/attention 0`、`/attention 04`、`/attention  2  `（前後有空白）。預期：只有去除空白後完全等於 `1`、`2`、`3` 才切頁；其他只開面板，頁碼不變。測試放在 Task 3。
4. **不在 git 的目錄，或空 repo（結束碼 128）。** 預期：工作樹列隱藏；Quick Notes 用 `notes-cwd:<目錄>`；不拋錯。測試放在 Task 1 與 Task 6。
5. **effort 是數字或缺席，rateLimits 是空陣列。** 預期：努力程度顯示「未知」（缺席）或數字的字串；額度顯示「尚無讀數」；不拋錯。測試放在 Task 5。

---

## Task 0：版本與 API 門檻確認（閘門）

**Files:** 無程式變更。

本機只安裝了 Claude Code 2.1.312（`claude --version`）。`CLAUDE.md` 寫的目標版本是 2.1.310。`$.store`、`$.session.model()`、`$.session.usage()`、`turn.step` 目前只在 2.1.312 的型別檔中查證過。

- [ ] **Step 1：查證 2.1.310 的 API**

  在可取得 2.1.310 型別的環境（或 Claude Code 2.1.310 的發行說明與型別檔）確認四個 API 存在且語意相同。查不到就不要猜。

- [ ] **Step 2：決定門檻**

  - 若 2.1.310 全部確認：不改門檻。
  - 若任一項無法確認：停下來問 Tom，是否把最低版本升到 2.1.312（需同步改 `plugins/attention-mod/.claude/CLAUDE.md`「目標版本」段落）。在 Tom 回答前，不進入 Task 1。

---

## Task 1：worktree 保留共用目錄

**Files:**
- Modify: `plugins/attention-mod/hooks/worktree.js`
- Test: `plugins/attention-mod/tests/worktree.test.ts`

**Interfaces:**
- Produces: `parseWorktree(stdout, exitCode)` 回傳 `{state, branch, detached, commonDir}`。`commonDir` 在 `linked` 與 `main` 時是絕對路徑字串，在 `not-git`、`unreadable` 時是 `null`。
- Produces: `FAILED_READ` 增加 `commonDir: null`。

- [ ] **Step 1：寫會失敗的測試**

  在 `tests/worktree.test.ts` 新增（既有的 `toEqual` 斷言要一起加上 `commonDir`）：
  - `parseWorktree(LINKED, 0).commonDir === '/repo/.git'`
  - `parseWorktree(MAIN, 0).commonDir === '/repo/.git'`
  - `parseWorktree('', 128)` 的 `state === 'not-git'` 且 `commonDir === null`
  - `FAILED_READ.commonDir === null`

- [ ] **Step 2：執行測試，確認失敗**

  Run: `claude plugin test .`（只有這個檔案會失敗；失敗訊息提到 `commonDir`）

- [ ] **Step 3：實作**

  `parseWorktree` 已經解出 `commonDir` 變數，只是沒有回傳。把它放進每個回傳值。

- [ ] **Step 4：執行測試，確認通過**

  Run: `claude plugin test .`
  Expected: `worktree.test.ts` 全部通過。

---

## Task 2：notes.js 純狀態機

**Files:**
- Create: `plugins/attention-mod/hooks/notes.js`
- Test: `plugins/attention-mod/tests/notes.test.ts`

**Interfaces:**
- Produces:
  - `NOTE_LIMIT = 32768`、`IDLE_MS = 1000`、`RETRY_MS = 5000`
  - `createNotes()` → `{status, key, text, dirty, lastEditAt, saving, saveError, retryAt}`；`status` 為 `'idle' | 'reading' | 'ready' | 'read-failed'`；`saveError` 為 `null | 'failed' | 'too-long'`
  - `keyFor(read)`：`read` 是 `{commonDir, cwd}` 或 `null`。回傳 `notes:<commonDir>`、`notes-cwd:<cwd>`，或 `null`（`read` 為 `null` 時）
  - `beginRead(notes, key)` → 新狀態：`status: 'reading'`，清空文字與旗標
  - `loaded(notes, key, value)`：`key` 與 `notes.key` 不符時原樣回傳。`value` 是字串 → `ready` 且文字為 `value`；`undefined` → `ready` 且文字為空；其他型別 → `read-failed`
  - `loadFailed(notes, key)` → `read-failed`（同樣檢查 key）
  - `edit(notes, text, now)` → 更新文字、`dirty: true`、`lastEditAt: now`
  - `nextSave(notes, now, force)` → `{action, value?}`，`action` 為 `'none' | 'save' | 'delete' | 'refuse'`
  - `saveStarted(notes, sentText)` → `saving: true`
  - `saveSettled(notes, sentText, ok, now)`：`ok` 且文字未變 → `dirty: false`；`ok` 且文字已變 → `dirty` 維持 `true`；`!ok` → `saveError: 'failed'`、`retryAt: now + RETRY_MS`
  - `switchKey(notes, nextKey)` → `{flush, notes}`；`flush` 是 `{key, text}` 或 `null`（只在 `dirty` 且有舊 key 時回傳）

- [ ] **Step 1：寫會失敗的測試**

  每一條斷言都要寫在 `tests/notes.test.ts`，用純函式直接呼叫，不需要 host：
  - `keyFor({commonDir:'/r/.git', cwd:'/x'}) === 'notes:/r/.git'`；`keyFor({commonDir:null, cwd:'/x'}) === 'notes-cwd:/x'`；`keyFor(null) === null`
  - 讀取中時 `nextSave` 回傳 `none`（即使 `dirty`）
  - `loaded` 收到 `undefined` → `ready`、文字為空；收到 `42` → `read-failed`
  - `loaded` 的 key 與目前 key 不符時狀態不變
  - `nextSave`：`now - lastEditAt` 為 999 → `none`；為 1000 → `save`
  - `nextSave`：`force: true` 不受門檻限制
  - 文字正好 32,768 個 code point（含一個代理對）→ `save`；32,769 → `refuse`，且 `saveError === 'too-long'`
  - 文字為空字串 → `delete`
  - `saving` 為 `true` 時 `nextSave` 回傳 `none`
  - `saveSettled(..., ok=false, now)` 之後 `nextSave` 在 `now + 4999` 回傳 `none`，在 `now + 5000` 回傳 `save`
  - `saveSettled` 時文字已變 → `dirty` 仍為 `true`
  - `switchKey` 在 `dirty` 時回傳 `flush: {key: 舊 key, text}`；不 `dirty` 時 `flush` 為 `null`

- [ ] **Step 2：執行測試，確認失敗**

  Run: `claude plugin test .`
  Expected: `notes.test.ts` 失敗，原因是 `notes.js` 不存在。

- [ ] **Step 3：實作 `hooks/notes.js`**

  純函式，不 import `$`。`[...text].length` 計算 code point。

- [ ] **Step 4：執行測試，確認通過**

  Run: `claude plugin test .`
  Expected: `notes.test.ts` 全部通過。

---

## Task 3：頁面分組與指令參數

**Files:**
- Modify: `plugins/attention-mod/hooks/view.js`
- Test: `plugins/attention-mod/tests/view.test.ts`

**Interfaces:**
- Produces:
  - `pageFromArgs(args)`：`args` 是字串。去除前後空白後完全等於 `'1'`、`'2'`、`'3'` 時回傳對應數字；其他回傳 `null`。
  - `pageSections(view, page)`：頁 1 回傳 id 為 `summary`、`live`、`agents`、`inputs` 的區塊（依序）；頁 2 回傳 `worktree`、`model`、`usage`；頁 3 回傳空陣列（頁 3 不用區塊）。
  - `paneRows(state, now, extras)` 的 `extras` 新增 `session`，形狀為 `{model, effort, rateLimits, skills, mcpServers}`，都可以是 `null`。
- 區塊 id `model` 的 rows：`模型`、`努力程度`。區塊 id `usage` 的 rows：`額度`（five_hour、seven_day 各一行）、`已載入 skill`、`MCP 伺服器`。

- [ ] **Step 1：寫會失敗的測試**

  在 `tests/view.test.ts`：
  - `pageFromArgs(' 2 ') === 2`；`pageFromArgs('2 extra') === null`；`pageFromArgs('0') === null`；`pageFromArgs('04') === null`；`pageFromArgs('') === null`
  - `pageSections` 頁 1 的 id 順序是 `['summary','live','agents','inputs']`，不含 `worktree`
  - `pageSections` 頁 2 包含 `worktree`，不包含 `summary`
  - `session.rateLimits === []` 時「額度」行顯示「尚無讀數」
  - `session.effort === null` 時「努力程度」行顯示「未知」；`effort === 'high'` 時顯示 `high`；`effort === 3` 時顯示 `3`（數字轉字串）

- [ ] **Step 2：執行測試，確認失敗**

  Run: `claude plugin test .`

- [ ] **Step 3：實作**

  rateLimits 的欄位名稱與百分比格式，先讀 `.claude-plugin/types/claude-code/index.d.ts` 的 `SessionRateLimit` 型別，不要猜。若型別檔不在本機，先用 `claude --plugin-dir "$PWD"` 產生（它會寫入 `.claude-plugin/types/`）。

- [ ] **Step 4：執行測試，確認通過**

  Run: `claude plugin test .`

---

## Task 4：頁碼、頁籤、指令、次要頁與回饋表單

**Files:**
- Modify: `plugins/attention-mod/hooks/register.js`（模組變數、`command.run`、`session.start` 的指令註冊描述、`ui.render` Pane、`drawFeedback`、`drawHeader`、`drawInline`、`drawDock`）
- Test: `plugins/attention-mod/tests/panel.test.ts`

**Interfaces:**
- Consumes: `pageFromArgs`、`pageSections`（Task 3）
- Produces: 模組變數 `page`（預設 `1`）。`command.run` 的 `e.args` 經 `pageFromArgs` 解析，非 `null` 時設定 `page`。

- [ ] **Step 1：寫會失敗的測試**

  - 面板預設在頁 1：渲染結果包含「摘要」、不包含「工作樹」。
  - `command.run` 收到 args `'2'` 之後，渲染結果包含「工作樹」，不包含「摘要」。
  - args `'9'` 不改變頁碼，只開面板。
  - 頁籤按鈕的 hotkey 依序為 `'1'`、`'2'`、`'3'`。
  - 回饋表單只出現在頁 2；頁 1 的渲染結果不包含「回饋」按鈕。
  - 回饋表單的 Input 不帶 `autoFocus`（檢查 Input 的 props）。
  - 既有「linked worktree 顯示路徑與分支」測試要改成先切到頁 2（它原本預設在單頁面板）。這是預期的行為變更，要在測試中註明。

- [ ] **Step 2：執行測試，確認失敗**

  Run: `claude plugin test .`

- [ ] **Step 3：實作**

  - 模組變數：`let page = 1;`，放在 `let collapsed = false;` 附近，註解說明規則與 `collapsed` 相同。
  - `command.run`：`const next = pageFromArgs(e.args ?? ''); if (next !== null) page = next;`，之後照原本的流程開面板。
  - 頁籤按鈕放在 `drawHeader` 的下一列，依序為「即時」「次要」「Quick Notes」，目前頁的標籤要能辨認。
  - 頁 1 呼叫 `drawInline`／`drawDock` 時用 `pageSections(view, 1)`；頁 2 用 `pageSections(view, 2)` 並加上 `drawFeedback`；頁 3 留給 Task 6、7。
  - 指令描述改為「開啟工作脈絡面板；/attention 1–3 切頁」。
  - `drawFeedback` 的 `Input` 移除 `autoFocus:true`。

- [ ] **Step 4：執行測試，確認通過**

  Run: `claude plugin test .`

---

## Task 5：唯讀資料（turn.step、模型、額度、skill 與 MCP）

**Files:**
- Modify: `plugins/attention-mod/hooks/register.js`
- Modify: `plugins/attention-mod/tests/fixtures.ts`（新增 `session.model`、`session.usage`、`turn.step` 的 stub）
- Test: `plugins/attention-mod/tests/panel.test.ts` 或新檔 `plugins/attention-mod/tests/session.test.ts`

**Interfaces:**
- Produces: 模組變數 `session = {model, effort, rateLimits, skills, mcpServers}`，每一欄預設 `null`。
- Produces: `turn.step` hook，`e.effort` 有值時寫入 `session.effort`；`session-reset` 時清回 `null`。
- Produces: `refreshSession($)`，在計時器裡每 5 次 tick 執行一次（5000 ms）。它呼叫 `$.session.model()` 與 `$.session.usage({breakdown:'summary'})`，把結果寫入 `session`；任一呼叫拋錯時該欄維持原值，不拋出。

- [ ] **Step 1：寫會失敗的測試**

  - 呼叫 `usage` 的每一次參數都是 `{breakdown:'summary'}`；記錄中不得出現 `full`。
  - `turn.step` 送 `effort: 'high'` 之後，次要頁顯示 `high`。
  - `turn.step` 送 `effort: 3` 之後，顯示 `3`。
  - 從未收到 `turn.step` 時，顯示「未知」。
  - `usage` 回傳的 `rateLimits` 為空陣列時，額度顯示「尚無讀數」。
  - `session.model()` 拋錯時，面板不崩潰，模型行顯示「未知」。

- [ ] **Step 2：執行測試，確認失敗**

  Run: `claude plugin test .`

- [ ] **Step 3：實作**

  `usage` 的 `skills` 與 `mcpServers` 欄位名稱，從型別檔 `SessionContextUsage` 與 breakdown 相關型別讀出（`summary` 模式的欄位）。型別檔沒有寫的欄位，不要推測；先停下來問 Tom。

- [ ] **Step 4：執行測試，確認通過**

  Run: `claude plugin test .`

---

## Task 6：Quick Notes 讀取與顯示狀態

**Files:**
- Modify: `plugins/attention-mod/hooks/register.js`
- Test: `plugins/attention-mod/tests/notes-panel.test.ts`（新檔）

**Interfaces:**
- Consumes: `createNotes`、`keyFor`、`beginRead`、`loaded`、`loadFailed`（Task 2）；`parseWorktree` 的 `commonDir`（Task 1）
- Produces: 模組變數 `notes`（`createNotes()`）、`keyRead`（`{cwd, commonDir}` 或 `null`）、`keyInFlight`。
- 獨立的 key 讀取：目錄改變時（計時器偵測到 `cwdNow !== keyRead.cwd`）執行一次 `GIT_ARGS` 讀取，只更新 `keyRead`，不改 `worktreeRead`。這樣 2026-10-26 的工作樹決定（目錄改變時顯示「待下一回合更新」）不變。
- 讀取結果：`parseWorktree` 的 `state === 'unreadable'` 時，`notes` 進入 `read-failed`，不退回 cwd key。`not-git` 才退回 `notes-cwd:` key。

- [ ] **Step 1：寫會失敗的測試（三條回歸測試先寫）**

  - **R1 讀不到就不寫：** `$.store.get` 拋錯；之後推進時間並編輯文字，`$.store.set` 的呼叫次數為 0。
  - **R2 key 切換先寫舊 key：** 在 A 目錄寫入文字未存，然後 `cwd` 改成 B 目錄；記錄中 `store.set(舊 key)` 出現在 `store.get(新 key)` 之前。
  - **R3 讀取完成前不掛載輸入框：** `store.get` 尚未回應時，渲染結果不含輸入框（用 Input 的 key `attention-notes` 判斷）。
  - 讀取到 `undefined` 之後進入就緒，顯示空白輸入框。
  - 讀取到數字 `42` 之後顯示「讀取失敗」與「重試」按鈕；按「重試」會再呼叫一次 `store.get`。
  - `unreadable`（git 讀取拋錯）時顯示「讀取失敗」，不呼叫 `store.get`。
  - 不在 git 時（`not-git`）使用 `notes-cwd:<目錄>` 作為 key。

- [ ] **Step 2：執行測試，確認失敗**

  Run: `claude plugin test .`

- [ ] **Step 3：實作**

  - `branchRead`（既有）同時設定 `keyRead`。
  - 計時器中加入：`cwdNow !== keyRead?.cwd && !keyInFlight` 時觸發 key 讀取。
  - 讀取的 key 與 `notes.key` 不同時，呼叫 `switchKey`（Task 7 的 flush 在那裡執行），再 `beginRead`，然後 `$.store.get(key)`，回來後 `loaded` 或 `loadFailed`。
  - 頁 3 的渲染：`reading` 顯示「讀取中」；`read-failed` 顯示「讀取失敗」與「重試」按鈕；`ready` 才掛載 `Input`（`key: 'attention-notes'`、`label: '筆記'`、`rows: 3`、`value: notes.text`，不設 `autoFocus`）。

- [ ] **Step 4：執行測試，確認通過**

  Run: `claude plugin test .`

---

## Task 7：Quick Notes 存檔

**Files:**
- Modify: `plugins/attention-mod/hooks/register.js`
- Test: `plugins/attention-mod/tests/notes-panel.test.ts`（延續 Task 6 的檔案）

**Interfaces:**
- Consumes: `edit`、`nextSave`、`saveStarted`、`saveSettled`、`switchKey`（Task 2）
- Produces: `persistNotes($, force)`：依 `nextSave` 的結果呼叫 `$.store.set` 或 `$.store.delete` 或設定 `too-long`，寫入完成後 `saveSettled`。
- 計時器每 1000 ms 呼叫一次 `persistNotes($, false)`。
- 輸入框 `onInput` → `edit`；`onSubmit` → `edit` 後呼叫 `persistNotes($, true)`。
- 切頁前（`page` 從 3 改成其他值時）呼叫 `persistNotes($, true)`。

- [ ] **Step 1：寫會失敗的測試**

  - 在 `mock.clock` 上推進 999 ms，`store.set` 呼叫為 0；推進到 1000 ms，呼叫為 1。
  - 按 Enter（`onSubmit`）立刻呼叫 `store.set`，不等計時器。
  - 文字正好 32,768 個 code point → 會存；32,769 → 不存，面板顯示「未存：超過上限」。
  - 寫入失敗（`store.set` 拋錯）→ 顯示「未存」；推進 4999 ms 不重試；推進到 5000 ms 重試。
  - 文字清空後 `store.delete` 被呼叫，`store.set` 不被呼叫。
  - 切頁前（從頁 3 按 `1`）有未存文字 → `store.set` 在切頁時被呼叫。
  - Review Focus 1 的 emoji 案例：`'😀'.repeat(32768)` 會存；多一個字元不存，不截斷。

- [ ] **Step 2：執行測試，確認失敗**

  Run: `claude plugin test .`

- [ ] **Step 3：實作**

  - `persistNotes` 不 await 在渲染路徑上；寫入的結果回來後呼叫 `redraw($)`。
  - 同一時間只跑一個寫入（`saving` 狀態）；寫入中又有編輯，下一次計時器再寫。
  - 寫入的文字是 `saveStarted` 傳入的 `sentText`，不是寫入完成時的 `notes.text`。

- [ ] **Step 4：執行測試，確認通過**

  Run: `claude plugin test .`

---

## Task 8：版號與文件

**Files:**
- Modify: `plugins/attention-mod/.claude-plugin/plugin.json`（`version` 改為 `0.6.0`）
- Modify: `plugins/attention-mod/hooks/meta.js`（`VERSION` 改為 `'0.6.0'`）
- Modify: `plugins/attention-mod/.claude/CLAUDE.md`（不變條件改成 spec「錯誤處理與不變條件」的草稿；開發段落的版號說明不需改）
- Modify: `plugins/attention-mod/docs/runtime-api.md`（新增 `$.store`、`$.session.model()`、`$.session.usage()`、`turn.step`）
- Modify: `plugins/attention-mod/README.md`（面板說明，若提到頁面結構）
- Modify: `plugins/attention-mod/docs/superpowers/specs/2026-10-29-attention-mod-tab-pages-design.md`（狀態行改為已實作）

- [ ] **Step 1：寫版號一致性的手動核對**

  `grep -n "0.6.0" plugins/attention-mod/.claude-plugin/plugin.json plugins/attention-mod/hooks/meta.js` 應該各出現一次。

- [ ] **Step 2：修改上述文件**

- [ ] **Step 3：驗證**

  Run: `claude plugin validate --strict .`（calls inventory 應列出新呼叫；列表中的名稱以 validate 輸出為準，不要照抄本計畫）
  Run: `claude plugin test .`

---

## Task 9：端到端與手動檢查

**Files:** 無程式變更。

- [ ] **Step 1：載入插件實測**

  Run: `claude --plugin-dir "$PWD"`，在 iTerm2 與 Warp 各試一次。

- [ ] **Step 2：逐項檢查 spec「尚未驗證」清單**

  - 按鈕怎麼用鍵盤進入輸入框。
  - Enter 後輸入框畫面是否清空；若清空，確認重繪後 `notes.text` 會放回輸入框。
  - 次要頁的回饋表單展開超過 18 列是否被裁切。
  - Warp 的數字鍵行為。
  - dock 的實際高度與三頁表現。
  - iTerm2 的貼上、Ctrl+J、Option+Enter。

  每一項的結果都寫回 spec 的「尚未驗證」段落，已驗證的移到「已查證」，不要把未實測的項目寫成已驗證。

- [ ] **Step 3：回報**

  把結果交給 Tom。不 commit。

---

## 範圍外

- 多份筆記、搜尋、匯出、同步、刪除單份筆記的介面。
- 摘要的 prompt、主對話提示、attachment／hook-context／compaction／tool-message／note 這幾種 door。
- 身分列。
- `$.session.usage({breakdown:'full'})`。
- `package.json` 版號的修正（既有不一致，另案處理）。

## Self-Review 結果

- **Spec 覆蓋：** 三頁內容（Task 3、4）、切頁與 `/attention`（Task 3、4）、頁碼規則（Task 4）、Quick Notes 存放與 key（Task 1、2、6）、讀取四種狀態（Task 6）、存檔時機與失敗（Task 7）、次要頁資料來源（Task 5）、版面與焦點（Task 4）、版號與文件（Task 8）、測試（每個 task）、範圍外（上節）。沒有遺漏。
- **型別一致：** `keyFor`、`notes` 狀態欄位、`pageFromArgs`、`pageSections`、`parseWorktree` 的 `commonDir` 在 Task 之間的名稱一致。
- **Review Focus：** 五項都有對應的測試（Task 1、2、3、5、6、7）。
- **需要 Tom 知道的設計決定（不在 spec 裡）：**
  1. 目錄改變時的 key 讀取獨立於工作樹讀取，所以工作樹列的「待下一回合更新」行為不變。
  2. git 讀取失敗（`unreadable`）時 Quick Notes 進入讀取失敗，不退回 cwd key，避免筆記被切散。
  3. `usage` 與 `model` 每 5 秒讀一次（我的選擇，spec 沒有指定）。
  4. 既有測試要改：工作樹測試改為先切到頁 2；工作樹「目錄改變」測試維持原斷言。

---

## 執行方式

Plan complete and saved to `plugins/attention-mod/docs/superpowers/plans/2026-10-29-attention-mod-tab-pages.md`. Please review the plan. Which execution approach would you prefer?

- **Subagent-driven** — 每個任務由新的 subagent 實作，每個任務完成後由新的 reviewer 檢查，最後再做整個分支的 review。最徹底，但每個任務和每次審查都要一份新的上下文。
- **Native** — 我在這個工作階段裡逐項實作，最後由一位新的 reviewer 用最強的模型檢查整個分支。最省，也最快；但中間沒有獨立審查。

**這份計畫我推薦 Native**，理由：Task 4 到 Task 7 都改同一個 `register.js` 的狀態與渲染，任務之間的依賴很深，分給 subagent 會重複讀取整個檔案，也容易互相覆寫；而計畫已經寫出各任務的介面與測試，足以讓單一執行者保持一致。這個插件是被動觀察者，最後的整體 review 能抓到大部分問題。

這份計畫的 Task 0 是閘門：若 2.1.310 無法確認 API，要先停下來問你。

請確認計畫內容是否符合你的想法，並選擇執行方式（Subagent-driven 或 Native）。
