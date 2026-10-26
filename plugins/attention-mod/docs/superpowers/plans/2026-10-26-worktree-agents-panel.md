# 工作樹與子代理面板實作計畫

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** 面板新增「工作樹」小節（只在連結的 worktree 顯示完整路徑與分支）與「子代理」小節（收起顯示執行中數量，展開列出執行中與最近結束的列），版本升到 0.5.0。

**Architecture:** 兩個純函式模組 `hooks/worktree.js`、`hooks/agents.js` 負責解析與摘要；`hooks/view.js` 新增 `worktree`、`agents` 兩個區塊；`hooks/register.js` 只做接線。分支讀取在 `turn.start` 發出但不 await；cwd 與子代理列表由每秒計時器更新。讀取函式以參數注入，測試時換成假函式。

**Tech Stack:** 原生 ES module（`.js`）、`claude-code/testing` 測試 kit（`claude plugin test .`）、`claude plugin validate --strict .`。本機沒有 `tsc`。

**Spec:** `docs/superpowers/specs/2026-10-26-worktree-agents-panel-design.md`（commit `0fce83f`）

## Global Constraints

- 最低版本 Claude Code 2.1.310（spec「決定」）。
- 版號 `0.5.0`，`.claude-plugin/plugin.json` 與 `hooks/meta.js` 同時改。
- 面板維持 `rows: 18`、`columns: 48`。
- 唯一允許的 process 指令：`git --no-optional-locks rev-parse --git-dir --git-common-dir --abbrev-ref HEAD`，`timeoutMs: 2000`。不用檔案、store、http。
- 子代理用既有 `$.clock.every(1000)` 輪詢；子代理事件不影響「動作」與「需要你」。
- 收起數字只算 `running` 與 `waiting`；已結束的列最多 5 筆。
- 固定字串逐字使用：`工作樹`、`路徑`、`分支`、`待下一回合更新`、`分離 HEAD`、`無法讀取`、`子代理：N 個執行中`、`子代理：無法讀取`。
- 追蹤檔與測試不寫個人路徑或 email。測試使用 `/repo/worktrees/feat-x` 這類假路徑。
- 每個 commit 都要 Tom 同意才執行（`CLAUDE.md`）。程式碼變更依 `completion-gate` 至少走 L1，commit 前呼叫一次 `code-review-claude`。

## Review Focus

1. 含中文或空白的路徑、含 `/` 的分支名（`feat/x`）折行後仍完整可見 → Task 4 繪製測試。
2. git 輸出末尾多一個換行 → `parseWorktree` 仍正確 → Task 2 測試。
3. `agent.list()` 在 session 中途丟出錯誤 → 子代理小節顯示「子代理：無法讀取」，不沿用舊列表 → Task 5 測試。
4. session 換掉後才回來的分支讀取結果 → 丟棄 → Task 5 測試。
5. git 讀取卡住 → 同時最多一個讀取在途，`turn.start` 不被阻擋 → Task 5 測試。

## 計畫時做的決定（spec 沒寫的部分）

- **D1 inline 版面（Tom 已決定：採建議做法）**：inline（`rows: 18`）的工作樹為一行 `工作樹：<路徑>（<分支>）`，放在「需要你」之後，不放在標題下，讓「需要你」維持在 0.2.0 的位置；子代理為一行 `子代理：N 個執行中`，放在工作樹之後，不展開。dock 的版面照 spec 不變。
- **D2 dock 展開**：dock 的子代理小節有一個按鈕「展開子代理／收起子代理」，狀態存在記憶體、預設收起，和 `collapsed` 一樣不隨 session-reset 重設。
- **D3 cwd 非同步**：`$.session.cwd()` 回傳 `Promise<string>`，`ui.render` 是同步 hook，所以 cwd 由每秒計時器讀取後存入 `cwdNow`。spec 寫的「重繪時呼叫」改為「計時器讀取、重繪使用」。
- **D4 結束時間**：`AgentInfo` 沒有時間欄位。計時器第一次看到某個子代理為已結束時記下時間（`endedAt`），「新的排前面」依此排序；同一輪發現的列依列表順序由後往前。
- **D5 狀態分類**：`running`、`waiting` 計入 N；`pending`、`idle` 與未知狀態列為執行中（全部列出），但不計入 N；`completed`、`failed`、`killed` 為已結束。
- **D6 隱藏條件**：第一次分支讀取完成前、或 cwd 讀不到時，工作樹小節隱藏。
- **D7 宿主缺 API**：若 `$.process.run` 或 `$.agent.list` 不存在（測試環境），對應小節隱藏，不顯示「無法讀取」。既有測試的版面因此不變。
- **D8 注入方式**：由 Task 0 決定。

## spec 需要修正的地方（Task 8 前請 Tom 確認）

- 外部輸入上限是 3 筆（`hooks/state.js:45` 的 `.slice(-3)`），不是 spec 寫的 5 筆。回歸測試的最壞情況改用 3 筆。
- spec 的「最壞情況仍在 18 行內」無法在測試套件證明：`drawn()` 回傳元素樹，不含折行後的實際高度。而且 0.2.0 的平面版面在摘要滿長（160 字，CJK 約 2 欄）時本來就可能超過 18 行。面板是可捲動視窗（`scroll.bodyRows`），超出的部分可以捲動，不會被截斷。改為驗收條件：新區塊不會讓「需要你」在不捲動時看不到（做不到就要回到 D1）。實機量測見 Task 9。
- `hooks/meta.js` 的註解寫「tests/meta.test.ts fails if the two drift」，但 `tests/` 沒有這個檔，而且測試不能讀取 `plugin.json`。Task 8 改成指向 `CLAUDE.md` 的手動核對。

## Task 0: 測試 kit 三項探針（不改 repo）

**目的：** 決定 D8，並確認 Task 5、6 的測試手法能用。

**Files:** 無。在 scratchpad 複製一份 `attention-mod`，加一個探針測試，用完刪除。

- [ ] **Step 1: 探測 options 能否傳入函式**

探針測試以 `test(name, {options:{probe: () => 42}}, fn)` 宣告，`register(on, options)` 內記下 `typeof options?.probe`。

Expected: `'function'`。若是 `'undefined'` 或其他型別，D8 改用模組 setter：`hooks/readers.js` 匯出 `setReaders()`，測試直接 import。這時要再加一個探針，確認 setter 對註冊的 instance 生效。

- [ ] **Step 2: 探測 `prompt()` 會不會觸發 `turn.start`**

探針的 `register` 裡數 `turn.start` 次數，測試呼叫既有的 `prompt($, 'x')`。Expected: 次數 ≥ 1。若為 0，查 `claude-code.d.ts` 裡 `turn.start` 的觸發條件，改用對應的觸發方式。

- [ ] **Step 3: 探測 Button 的 `onPress` 能否從繪製樹呼叫**

探針自己註冊 `ui.render` 的 Pane，放一個有 `key` 的 Button，從 `drawn()` 找到該節點，呼叫 `props.onPress()`。Expected: `onPress` 執行並改變狀態。

- [ ] **Step 4: 記錄結果**

D8 與 Step 2、3 的結果記入 Task 8 的 `docs/prototype-results.md`。

**Verification:** 三項結果都有輸出。任何一項失敗，停下來回報，不要繼續 Task 1。

## Task 1: 先修規則文件（放寬 process 之前）

放寬 process 之前，`.claude/CLAUDE.md` 第 40 行的規則必須先改，否則程式會違反當時的規則。

**Files:**
- Modify: `.claude/CLAUDE.md`（第 40 行「被動觀察」）
- Create: `docs/decisions/2026-10-26-worktree-agents-process.md`

**Interfaces:**
- Produces: 新的允許清單（`agent.list`、`process.run` 限定 git 指令、`session.cwd`）。之後的程式碼與 validate 都以此為準。

- [ ] **Step 1: 讀第 40 行與既有決策紀錄的格式**

讀 `docs/decisions/2026-10-07-feedback.md`，新檔案照此格式。

- [ ] **Step 2: 改第 40 行**

允許的 API 加上：`$.agent.list`（每秒，唯讀）、`$.session.cwd`（唯讀）、`$.process.run`（只限 Global Constraints 那一條 git 指令，timeout 2000 ms）。仍然不用 store、檔案、http，也不提交主對話提示。

- [ ] **Step 3: 新增決策紀錄**

寫明：為什麼放寬（2026-10-26 使用者決定；實機探測結果）、放寬的範圍（同上）、不變的部分、尚未驗證的項目（Team／Enterprise 的 sec-default、`/clear` 後的 `agent.list`）。

- [ ] **Step 4: 核對**

`grep -n "process" .claude/CLAUDE.md` 應看到新的允許範圍與唯一指令；`grep -n "不用 store、檔案、http、process" .claude/CLAUDE.md` 應無結果。

- [ ] **Step 5: Commit（要 Tom 同意）**

`docs(attention-mod): allow read-only git and agent.list under the passive rule`

## Task 2: `worktree.js` 純函式

**Files:**
- Create: `hooks/worktree.js`
- Test: `tests/worktree.test.ts`

**Interfaces:**
- Produces:
  - `GIT_ARGS`：`['git','--no-optional-locks','rev-parse','--git-dir','--git-common-dir','--abbrev-ref','HEAD']`
  - `GIT_TIMEOUT_MS = 2000`
  - `FAILED_READ = {state:'unreadable', branch:null, detached:false}`
  - `parseWorktree(stdout: string, exitCode: number) → {state, branch, detached}`，`state` 為 `'linked' | 'main' | 'not-git' | 'unreadable'`
  - `worktreeView(read, currentCwd) → {path, branch} | null`，`read` 為 `{cwd, state, branch, detached} | null`

- [ ] **Step 1: 寫失敗的測試**

`parseWorktree` 的每一列：

| 輸入 | 結果 |
|---|---|
| exit 0；第一行 `/repo/.git/worktrees/x`，第二行 `/repo/.git`，第三行 `feat/x` | `linked`，branch `feat/x`，detached false |
| exit 0；前兩行相同（`/repo/.git`），第三行 `main` | `main` |
| exit 0；linked，第三行 `HEAD` | `linked`，branch null，detached true |
| exit 0，末尾多一個換行 | 同第一列（只看前三行） |
| exit 0，只有兩行 | `unreadable` |
| exit 128 | `not-git` |
| exit 1（其他非零值） | `unreadable` |

`worktreeView` 的每一列：

| read | currentCwd | 結果 |
|---|---|---|
| null | 任何 | null |
| 任何 | null | null |
| cwd 不同 | `/repo/worktrees/y` | `{path:'/repo/worktrees/y', branch:'待下一回合更新'}` |
| linked，branch `feat/x` | 同 cwd | `{path, branch:'feat/x'}` |
| linked，detached | 同 cwd | `{path, branch:'分離 HEAD'}` |
| unreadable | 同 cwd | `{path, branch:'無法讀取'}` |
| main 或 not-git | 同 cwd | null |

- [ ] **Step 2: 跑測試，確認失敗**

`claude plugin test .`。預期新測試失敗（模組不存在），既有 107 個不受影響。

- [ ] **Step 3: 實作**

`parseWorktree` 只取前三行；前兩行不同即為 linked。常數放在模組頂部，註解寫為什麼要這樣做。

- [ ] **Step 4: 跑測試，確認通過**

`claude plugin test .`。預期 107 加新增測試，0 失敗。

- [ ] **Step 5: Commit（要 Tom 同意）**

`feat(attention-mod): parse worktree state from git rev-parse`

## Task 3: `agents.js` 純函式

**Files:**
- Create: `hooks/agents.js`
- Test: `tests/agents.test.ts`

**Interfaces:**
- Produces:
  - `ENDED_LIMIT = 5`
  - `noteEnded(endedAt: Map<string,number>, list: AgentInfo[], now: number) → Map`：對每個已結束且尚未記錄的 id 記下 `now`；移除列表中已不存在的 id；回傳新的 Map（不修改傳入的）。
  - `summarizeAgents(list, now, endedAt) → {runningCount, rows}`；每列為 `{id, type, description, status, live}`。
  - `agentsView(read, now, endedAt)`：`read` 為 `null`（隱藏）、`{failed:true}`，或 `{list}`；回傳 `null`、`{failed:true}`，或 `summarizeAgents` 的結果。

- [ ] **Step 1: 寫失敗的測試**

- 執行中的列全部保留，不因數量被截斷。
- `runningCount` 只算 `running`、`waiting`；`pending`、`idle` 不計。
- 已結束的列超過 5 筆時，只留最近 5 筆（依 `endedAt` 由新到舊）。
- 排序依 `noteEnded` 記下的時間，不依列表位置。
- 未知狀態（例如 `'paused'`）視為執行中：列出，不計入。
- 空列表：`{runningCount:0, rows:[]}`。
- `noteEnded` 不修改傳入的 Map；列表中消失的 id 會被移除。

- [ ] **Step 2: 跑測試，確認失敗**
- [ ] **Step 3: 實作**
- [ ] **Step 4: 跑測試，確認通過**
- [ ] **Step 5: Commit（要 Tom 同意）**

`feat(attention-mod): summarize subagents with a capped ended list`

## Task 4: `view.js` 新增兩個區塊

**Files:**
- Modify: `hooks/view.js`（`paneRows` 第 48–71 行、`inlineFields` 第 89–97 行、`paneLines` 第 107–112 行）
- Test: `tests/view.test.ts`（新增案例，不改既有案例）

**Interfaces:**
- Consumes: `agentsView` 的結果（Task 3）；worktree 的 `{path, branch} | null`（Task 2）。
- Produces: `paneRows(state, now, extras = {})`，`extras` 為 `{worktree, agents, agentsExpanded}`，缺省時行為與現在一致。
  - 區塊順序：`worktree`（只在非 null 時出現）、`summary`、`live`、`agents`（只在非 null 時出現）、`inputs`。
  - `worktree` 區塊：`{id:'worktree', label:'工作樹', tone:'muted', meta:null, notes:[], rows:[{label:'路徑', text:path}, {label:'分支', text:branch}]}`。
  - `agents` 區塊：`{id:'agents', label:'子代理', tone:'muted', meta:null, expandable:true, summary, notes:[{text:'子代理：'+summary, tone:'muted'}], rows}`。`summary` 為 `'N 個執行中'` 或 `'無法讀取'`。`rows` 只在 `agentsExpanded` 為真時有內容，每列為 `{label:type, text:'描述（狀態）'}`。
  - `inlineFields(view)`：固定順序為目標、脈絡、動作、證據、需要你；有 worktree 時，加在「需要你」之後 `{label:'工作樹', text:'路徑（分支）', tone:'muted'}`；有 agents 時，再加在工作樹之後 `{label:'子代理', text:summary, tone:'muted'}`。
  - `paneLines` 用 `inlineFields`，自動包含新欄位。

- [ ] **Step 1: 寫失敗的測試**

- 沒有 extras：`view.sections` 的 label 仍是 `['摘要','即時','外部輸入']`（既有測試已覆蓋，確認沒有改動）。
- 有 worktree：區塊順序為 `['工作樹','摘要','即時','外部輸入']`，rows 的 label 是 `路徑`、`分支`。
- 有 agents（running 2、waiting 1）：`summary` 為 `'3 個執行中'`；`notes[0].text` 為 `'子代理：3 個執行中'`；`agentsExpanded` 為假時 rows 為空陣列。
- `agentsExpanded` 為真時 rows 有內容。
- `agents` 為 `{failed:true}`：`summary` 為 `'無法讀取'`。
- `inlineFields` 的 label 順序，兩個區塊都有時為 `['目標','脈絡','動作','證據','需要你','工作樹','子代理']`。

- [ ] **Step 2: 跑測試，確認失敗**
- [ ] **Step 3: 實作**
- [ ] **Step 4: 跑測試，確認通過**
- [ ] **Step 5: Commit（要 Tom 同意）**

`feat(attention-mod): add worktree and subagent sections to the pane model`

## Task 5: `register.js` 接線與讀取

**Files:**
- Modify: `hooks/register.js`
  - 模組變數（第 11–31 行）：新增 `worktreeRead`、`cwdNow`、`agentsRead`、`endedAt`、`agentsExpanded`、`branchInFlight`、`panelInFlight`。
  - `session.start`（第 154–167 行）：在 `startTimer` 之後呼叫 `void readBranch($)`。
  - `turn.start`（第 248–252 行）：在 `apply(turn-start)` 之後呼叫 `void readBranch($)`，不 await。
  - `rebind`（第 130–148 行）：session-reset 之後呼叫 `void readBranch($)`（`/clear` 不會再觸發 `session.start`）。
  - `startTimer`（第 108–117 行）：tick 內呼叫 `void refreshPanel($)`。
  - `ui.render`（第 269–282 行）：`paneRows(state, now, {worktree: worktreeView(worktreeRead, cwdNow), agents: agentsView(agentsRead, now, endedAt), agentsExpanded})`。
- Create: `tests/panel.test.ts`
- Modify: `tests/fixtures.ts`：新增 `panelReaders(overrides)`，回傳預設的假讀取函式。

**Interfaces:**
- Consumes: Task 0 的 D8；Task 2、3、4 的函式。
- Produces（`register.js` 內部）：
  - `readers`：`{...defaultReaders, ...(options?.readers ?? {})}`，在 `register(on, options)` 時組好。
  - `defaultReaders`，每個都先做功能偵測：
    - `cwd($)`：`typeof $.session?.cwd === 'function'` 才呼叫 `$.session.cwd()`，否則回傳 `null`。
    - `git($, cwd)`：`typeof $.process?.run === 'function'` 才呼叫 `$.process.run(GIT_ARGS, {cwd, timeoutMs: GIT_TIMEOUT_MS})`，否則回傳 `null`。
    - `agents($)`：`typeof $.agent?.list === 'function'` 才呼叫 `$.agent.list()`，否則回傳 `null`。
  - `readBranch($)` 的行為：
    1. `branchInFlight` 為真就直接返回（同時最多一個）。
    2. 記下 `epoch`、`sessionId`，讀 cwd。cwd 為 `null` → `worktreeRead = null`。
    3. 呼叫 git reader。回傳 `null` → `worktreeRead = null`。reject 或 throw → `{cwd, ...FAILED_READ}`。否則 `{cwd, ...parseWorktree(stdout, exitCode)}`。
    4. 寫入前檢查 `state.epoch`、`sessionId` 是否仍相同；不同就丟掉結果，不改 `worktreeRead`。
    5. `finally` 清除 `branchInFlight` 並 `redraw($)`。
  - `refreshPanel($)`：`panelInFlight` 保護。`cwdNow` 取 cwd reader 的結果（失敗為 `null`）。agents reader 回傳 `null` → `agentsRead = null`；回傳陣列 → `endedAt = noteEnded(endedAt, list, now)`、`agentsRead = {list}`；丟錯 → `agentsRead = {failed:true}`。全部包在 try/catch 裡，不影響 tick。

- [ ] **Step 1: 寫失敗的測試（`tests/panel.test.ts`）**

用 `host(on)`，並以 `{options:{readers: panelReaders({...})}}` 宣告測試。案例：

1. 連結的 worktree 在 dock 中顯示完整路徑與分支（假路徑 `/repo/worktrees/feat-x`，分支 `feat/x`）。
2. 主 checkout 不顯示「工作樹」。
3. git reader reject：小節仍顯示路徑，分支欄為「無法讀取」。
4. 讀取後 cwd 改變：顯示「待下一回合更新」，不顯示舊分支。
5. detached HEAD：顯示「分離 HEAD」。
6. 過期結果被丟棄（Review Focus 4）：用 deferred promise 讓 git 讀取在 epoch 0 卡住；觸發 session.end 加新 session id；resolve 之後，面板不顯示舊分支。
7. 卡住的讀取（Review Focus 5）：git reader 回傳永不 resolve 的 promise；觸發兩次 `turn.start`，git reader 只被呼叫一次，而且 `turn.start` 能即時返回。
8. 子代理：`running` 2、`waiting` 1、`pending` 1、`completed` 2。收起時顯示「子代理：3 個執行中」；按下 `toggle-agents` 後列出執行中與最近結束的列（已結束最多 5 筆）。
9. `agent.list` 第一次成功、第二次丟錯（Review Focus 3）：顯示「子代理：無法讀取」，不沿用舊列表。
10. 子代理事件（`tool.call` 帶 `agentId`）不改變「動作」。
11. 預設 readers（沒有 `readers` option）：不出現「工作樹」與「子代理」（D7）。

- [ ] **Step 2: 跑測試，確認失敗**
- [ ] **Step 3: 實作**
- [ ] **Step 4: 跑測試，確認通過**
- [ ] **Step 5: Commit（要 Tom 同意）**

`feat(attention-mod): read worktree and subagent state into the pane`

## Task 6: dock 子代理展開按鈕

**Files:**
- Modify: `hooks/register.js` 的 `drawDock`（第 348–361 行）。`drawDock` 需要 `$` 才能呼叫 `redraw($)`，把 `$` 傳進來。
- Test: `tests/panel.test.ts`

- [ ] **Step 1: 寫失敗的測試**

dock 的子代理區塊有 key 為 `toggle-agents` 的 Button，label 為「展開子代理」；按下後變為「收起子代理」，並列出列；inline 沒有這個按鈕。

- [ ] **Step 2–4：失敗 → 實作 → 通過**

按鈕只在 `section.expandable` 時畫。

- [ ] **Step 5: Commit（要 Tom 同意）**

`feat(attention-mod): expand the subagent list from the dock`

## Task 7: 行數回歸測試（邏輯版）

**Files:**
- Modify: `tests/panel.test.ts`

這個測試只能證明結構，不能證明折行後的高度（見上方 spec 修正）。

- [ ] **Step 1: 寫測試**

inline，最壞情況：路徑 120 字、3 筆外部輸入、5 筆子代理。斷言：「需要你」列存在，位於「即時」之後、外部輸入之前；繪製樹的子節點數等於預期公式。

- [ ] **Step 2–4：失敗 → 實作（如需要）→ 通過**
- [ ] **Step 5: Commit（要 Tom 同意）**

實機高度量測放在 Task 9。

## Task 8: 發版與文件

**Files:**
- Modify: `hooks/meta.js`（`VERSION` 改為 `0.5.0`；註解改為指向 `CLAUDE.md` 的手動核對）
- Modify: `.claude-plugin/plugin.json`（`version` 改為 `0.5.0`）
- Modify: `tests/view.test.ts:22`、`tests/integration.test.ts:91,126,336`（`v0.4.8` → `v0.5.0`）
- Modify: `README.md:7`（`2.1.288` → `2.1.310`）
- Modify: `.claude/CLAUDE.md`：第 7 行目標版本、架構段落（新增 `worktree.js`、`agents.js` 與兩個區塊）、第 45 行子代理規則。
- Modify: `docs/runtime-api.md`：加入 `$.agent.list`、`$.process.run`、`$.session.cwd`（依 2.1.310 型別）。
- Modify: `docs/prototype-results.md`：記下 H5（不等待 49 ms，3 次；等待 2032 ms，1 次）、H6（測試 kit 沒有 `process`、`agent`）、Task 0 的結果，以及 NOT VERIFIED 清單。
- 若 Tom 同意，修正 spec（外部輸入 3 筆、cwd 讀取方式、18 行的驗收條件）。

- [ ] **Step 1: 改版號與註解，更新測試中的版號字串**
- [ ] **Step 2: 更新文件**
- [ ] **Step 3: 完整測試**

`claude plugin test .`，預期 0 失敗，數字為 107 加新增測試數。

- [ ] **Step 4: validate**

`claude plugin validate --strict .` 通過，calls inventory 列出 `$.process.run`、`$.agent.list`、`$.session.cwd`。

- [ ] **Step 5: 核對**

`grep -rn "v0.4.8" tests hooks` 無結果；`grep -rn "2.1.288" README.md .claude` 只剩歷史說明。

- [ ] **Step 6: Commit（要 Tom 同意）**

`chore(attention-mod): release 0.5.0 with worktree and subagent panel`

## Task 9: 實機驗證（發版前，需要 Tom 操作）

每一項由 Tom 在真實 session 裡操作，我記錄結果到 `docs/prototype-results.md`。

1. 在連結的 worktree 開 session，派一個子代理：確認收起數字與展開列。
2. 在主 checkout 開 session：工作樹小節隱藏。
3. session 裡 `cd` 到其他目錄：路徑跟著變，分支顯示「待下一回合更新」。
4. 48 欄 inline，最壞情況（摘要 160 字、路徑 120 字、3 筆外部輸入、5 筆子代理）：「需要你」在不捲動時是否看得到。**如果看不到，停下來，回到 D1 讓 Tom 決定，不發版。**
5. 不宣稱已驗證：Team／Enterprise 的 sec-default、`/clear` 後的 `agent.list`、2.1.310 以外的版本。

發版後（另外要 Tom 同意）：開 PR、打 tag `attention-mod-v0.5.0`，然後執行 `claude plugin marketplace update tomwangowa` 與 `claude plugin update attention-mod@tomwangowa`。

## Self-Review

**Spec coverage**

- 工作樹小節（只在連結的 worktree、完整路徑、分支、`cwd`、git 指令、啟動與 turn.start 讀取、待下一回合更新、分離 HEAD、位置）→ Task 2、4、5。
- 子代理小節（位於即時下方、列內容、收起一行、展開上限 5、每秒輪詢、不影響動作與需要你）→ Task 3、4、5、6。
- 讀不到時（128 隱藏、啟動失敗顯示無法讀取、逾時視為無法讀取、agent.list 失敗一行）→ Task 2、5。
- 版號 0.5.0 → Task 8。
- 錯誤處理（epoch/sessionId、try/catch、只允許一條 git 指令、子代理不影響主狀態）→ Task 1、5。
- 測試（單元、繪製、行數回歸、注入）→ Task 2–7。
- 實機驗證 → Task 9。
- 同步文件（decisions、runtime-api、prototype-results、CLAUDE.md）→ Task 1、8。
- 技術可行性 H5、H6 → 已有結果，記入 Task 8；H7 → 最低版本 2.1.310。

**Type consistency:** `GIT_ARGS`、`GIT_TIMEOUT_MS`、`FAILED_READ`、`parseWorktree`、`worktreeView`、`noteEnded`、`summarizeAgents`、`agentsView`、`paneRows(state, now, extras)`，以及區塊 id `worktree` 與 `agents`，在各 task 中一致。

**Review Focus:** 五項各有對應測試（見上方 Review Focus）。

**Proportion:** 本計畫約為 spec 的兩倍，主要是測試案例與介面清單，沒有完整程式碼實作。

## Execution Handoff

計畫已存到 `plugins/attention-mod/docs/superpowers/plans/2026-10-26-worktree-agents-panel.md`。請審閱計畫，特別是 D1–D8 與 spec 修正的部分。

Which execution approach would you prefer?

- **Subagent-driven**：每個 task 由新的 subagent 實作，接著由新的 reviewer 檢查，再進下一個 task；最後整個分支再審一次。最完整，但每個 task 與每次 review 都要新的 context。
- **Native**：我在這個 session 逐個實作，最後由一個新的 reviewer（最強模型）審整個分支。較便宜、較快，但中間沒有獨立 review。

我建議 **Native**。原因：task 之間透過 `view.js` 的 `paneRows` 簽章與 `register.js` 的模組變數緊密相連，subagent 每次都要重新讀完整脈絡，成本高；每個 commit 前又會跑 `code-review-claude`，中間已有 review。

計畫是否符合你的想法？要用哪一種執行方式？
