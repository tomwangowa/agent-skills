# Attention Mod Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [x]`) syntax for tracking.

**Goal:** 在目前 Claude Code 工作階段提供側邊摘要，讓 Tom 回來瞄一眼就接回工作脈絡。

**Architecture:** 入口檔觀察事件，將原事件及結果照常傳遞。純資料模組負責即時狀態、素材快照、摘要驗證及排程判斷；背景模型只更新文字摘要，面板同時呈現即時動作及摘要快照時間。

**Tech Stack:** Claude Code 2.1.288；JavaScript ES modules＋公開函式 JSDoc；原生 `claude plugin validate`、`claude plugin test`；背景摘要預設 `haiku`。不新增執行期套件。

**Spec:** [已確認的設計](../specs/2026-10-03-attention-mod-design.md)。執行前讀取規格及本計畫。

## Global Constraints

- 素材含來源／省略標記最多 8,000 字元，按 Unicode code point 計算；目標、脈絡、證據各最多 160 字元。
- 模型呼叫開始至少相隔 60 秒，同時最多一個；單次最多 512 個輸出 tokens，15 秒逾時。
- 摘要只讀既有對話／工具事件，資料只存記憶體；不寫 `$.store`，不額外讀工作區，不啟動主對話新回合。
- 面板標題「你到底在忙什麼」；不搶焦點，關閉後不自動重開；`/attention` 只開面板。
- 只對明確人工等待顯示待處理；`tool.check` 的 `ask` 不單獨當作等待證據，訊號不足顯示「等待狀態不明」。
- 新使用者提示令舊摘要失效；清除／切換令舊工具、素材、等待及摘要失效；兩者均不提前釋放模型呼叫鎖或繞過頻率限制。
- 使用者已選定設計，並選擇 A：由目前代理在本對話實作。本計畫推薦由目前代理在本對話逐項實作；只有 Tom 選擇子代理方式後才派出子代理。
- 目錄目前不是 Git repository。不把初始化、commit、push 或發布放入自動步驟；每次 commit／push／發布須另外取得 Tom 同意。
- 若準備提議 commit，依 `completion-gate` 分級；此 Mod 改動工作階段狀態，預期 L2，跑完整 gate 及一次 `code-review-codex`。不呼叫其他 runtime 或外部 reviewer。

## Review Focus

- 超長繁體中文、emoji 與省略標記：序列化後仍不超過 8,000 code points。Task 3。
- 同一工作階段新提示、清除及 resume 與在途模型交錯：舊摘要不回填，鎖與 60 秒限制不被重設。Task 4。
- 清除後舊工具晚到、呼叫識別重複：舊工具完成不清掉新工作階段的活動。Task 2。
- 工具資料含指令或模型回傳合法來源但錯誤敘述：結構驗證不冒充語意驗證，真實抽查涵蓋這類輸入。Task 3／5。
- 沒有可用摘要模型、API 拒絕或面板尚未放置：主工具照常執行，摘要明示缺失，焦點及輸入不受影響。Task 1／4／5。

## 檔案與介面

| 檔案 | 責任 |
|---|---|
| `.claude-plugin/plugin.json`、`hooks/hooks.json` | Plugin `attention-mod`，入口 `hooks/register.js` |
| `hooks/register.js` | 所有 `$` API 呼叫、事件欄位轉換、計時器與面板接線；`register(on)` |
| `hooks/state.js` | 純資料狀態、工具並行、等待訊號、世代與重設 |
| `hooks/snapshot.js` | 有來源的素材選擇、節錄與 8,000 字元上限 |
| `hooks/summary.js` | 摘要提示、JSON 驗證、160 字元及來源限制 |
| `hooks/scheduler.js` | 跨世代的模型呼叫鎖、頻率與已嘗試素材版本 |
| `hooks/view.js` | 由狀態與時間產生面板文字，不執行模型呼叫 |
| `tests/fixtures.ts`、`tests/*.test.ts` | 正規化資料、受控時間與原生事件／面板測試 |
| `docs/runtime-api.md`、`docs/prototype-results.md`、`README.md` | 本機 API 對照、原型結果、使用方法 |

共用資料契約在 `state.js` 用 JSDoc 定義並由測試引用：`Source = { id, role, text, at }`；`Activity = { id, epoch, agentId: string|null, tool, label, startedAt, status }`；`State = { sessionId, epoch, revision, sources, activities, waits, summary, summaryError, snapshotAt, turnStatus, enabled }`。

`Snapshot = { sessionId, epoch, revision, capturedAt, prompt, sourceIds, sourceRoles }` 在 `snapshot.js` 定義；`Summary = { goal, context, evidence }` 在 `summary.js` 定義，每個欄位是 `{ text, sources: string[] }` 或 null。工具／等待識別均含世代，來源識別不得在新世代重用。`revision` 隨素材變化遞增；事件狀態不能被摘要覆寫。

API 方法的完整名稱與事件名稱須直接寫在入口檔。不把 `$` 或 namespace 指派別名，不把 `$` 傳給匯入函式；純資料模組不接收 `$`。公開函式用 JSDoc，程式註解與測試輸出用英文，產品文字沿用已確認的繁體中文。

## Task 1：可載入的觀察器與本機 API 契約

**Files:** 建立 metadata、`hooks/register.js`、`tests/runtime.test.ts`、`docs/runtime-api.md`；CLI 產生 `.claude-plugin/types/` 及適用的 `tsconfig.json`。

**Interfaces:** 產出 `register(on): void`；`docs/runtime-api.md` 列出本機事件的輸入／結果與方法型別，Task 2／4／5 以此接線，不採用公開 2.1.277 型別。

- [x] 建立最小 metadata 與空入口。用已安裝的 `claude --plugin-dir .` 載入；不送模型提示。確認版本、產生的型別位置及 hooks 載入後退出。若無法啟動，保留原始診斷並先解決原生載入；不靠猜測繼續接線。
- [x] 讀本機型別並記錄 `model.complete`、`session.messages/id`、`clock`、`ui.open/resolve`、`tool.call`、回合、`session.end` 與 `classic.SessionStart`；找出可確認的人工等待開始／解除事件。缺少可靠等待訊號時採規格的未知狀態，不能用權限路由代替。
- [x] 寫 `runtime.test.ts`，註冊所有 stub 後才第一次呼叫測試的 `$`；證明入口有執行，且事件／結果不改寫。`observedCalls` 只在觀察器為工具取時間的 `clock.now` stub 遞增，不能在核心 `tool.call` stub 遞增，否則刪掉 Mod 仍會通過。測試 `observer passes through the tool result` 的核心斷言：

```ts
const result = await $.tool.call({ tool: 'Bash', command: 'echo fixture' });
expect(observedCalls).toBe(1);
expect(result).toEqual({ result: 'fixture-output' });
expect(promptSubmissions).toEqual([]);
```

- [x] 跑 `claude plugin test .`，確認先因缺少觀察器行為而失敗；stub 的計數與形狀按本機契約設定，不實際執行 Bash。
- [x] 實作最小觀察接線與 JSDoc；跑 `claude plugin validate --strict .`、`claude plugin test .`，要求退出碼 0、0 fail、至少一個測試執行。原生驗證不等同 `tsc`；目前無 `tsc`，不得宣稱型別編譯通過。

## Task 2：即時狀態、並行工具與世代

**Files:** 建立 `hooks/state.js`、`tests/fixtures.ts`、`tests/state.test.ts`；修改入口。

**Interfaces:** `createState(sessionId: string): State`；`reduceState(state: State, event: NormalizedEvent): State`。事件 union 為 `source`、`tool-start`、`tool-end`、`wait-start`、`wait-end`、`new-prompt`、`session-reset`、`turn-end`，各帶 `at` 與需要的 `epoch`／識別；入口只負責把已查證的 runtime 欄位轉換為此契約。

- [x] 寫 `parallel tools finish independently`、`old epoch completion does not remove new activity`、`new prompt invalidates summary but preserves live tools`、`explicit waits are released`；核心斷言：

```ts
expect(afterFirstCompletion.activities.map(a => a.id)).toEqual(['second']);
expect(afterOldCompletion.activities.map(a => a.id)).toEqual(['new']);
expect(afterNewPrompt.summary).toBe(null);
expect(afterNewPrompt.activities.length).toBe(1);
expect(afterAnswer.waits.length).toBe(0);
```

- [x] 跑原生測試並讀取預期失敗，再實作 reducer、來源識別及實際事件接線。輸入 state 不原地變更。工程預設保留最多 64 則來源，每則 text 最多 8,000 code points；保留目前目標的已知來源，其餘淘汰最舊者，節錄加標記。工具／等待只保留執行中項目及有限節錄，不另存原始巨型參數或結果；測試 1,000 則輸入後來源數仍不超過 64，目標來源未被一般工具紀錄淘汰。
- [x] 加 `ask route is not a confirmed human wait`、子代理不覆蓋主動作、工具成功／失敗／拒絕／取消、回合結束不等同任務完成的事件測試；再次執行原生驗證及所有目前測試，要求 0 fail。

## Task 3：有限素材與可追查摘要

**Files:** 建立 `hooks/snapshot.js`、`hooks/summary.js`、`tests/snapshot.test.ts`、`tests/summary.test.ts`。

**Interfaces:** `buildSnapshot(state: State, messages: Source[], now: number): Snapshot|null`；`summarySystemPrompt(): string`；`parseSummary(raw: string, snapshot: Snapshot): Summary|null`。`prompt` 是序列化素材含來源與省略標記；固定 system prompt 不混入素材來源，大小另由程式固定。

- [x] 寫 `snapshot bounds serialized Unicode data`、`snapshot retains goal source and recent changes`、`unknown source rejects the whole summary`、`unsupported field is null`；測試核心：

```ts
expect(Array.from(snapshot.prompt).length <= 8000).toBe(true);
expect(snapshot.prompt).toContain('truncated');
expect(parseSummary(JSON.stringify(badReference), snapshot)).toBe(null);
expect(parseSummary(JSON.stringify(validWithNull), snapshot)?.context).toBe(null);
```

- [x] 跑測試確認失敗。實作先保留目前目標來源，再納入較新素材，過長來源保留頭尾並標記節錄；最終以 code points 檢查完整序列化字串，必要時繼續裁切來源。空素材回傳 null，不用上一份摘要補洞。
- [x] 實作固定 JSON schema：只容許 `goal/context/evidence` 三欄，非 null 值只有 `text/sources`；文字非空且最多 160 code points，sources 非空、不可重複且全在快照內。非法 JSON、額外欄位與任何無效值整份拒絕。
- [x] 測試 emoji、單一超長目標、只有工具結果、160／161 字元、指令型工具資料及未提供的權限／動作欄位；指令型文字必須留在資料區塊，不能升格成 system prompt。驗證結構不證明語意安全，Task 5 另做真實抽查。跑原生測試與驗證，要求 0 fail。

## Task 4：背景模型、頻率、失敗與重建

**Files:** 建立 `hooks/scheduler.js`、`tests/scheduler.test.ts`、`tests/lifecycle.test.ts`；修改入口。

**Interfaces:** `createSchedule(): Schedule`；`claimSnapshot(schedule: Schedule, snapshot: Snapshot, now: number): RequestToken|null`；`settleRequest(schedule: Schedule, token: RequestToken): void`。`Schedule` 保留 lastStartedAt、inFlight、最近已嘗試的世代／素材版本；`RequestToken` 含唯一 requestId 與快照。重設 State 不重設 Schedule。

- [x] 寫 `new data respects 60000 ms between starts`、`old request keeps the lock through reset`、`a failed revision is not retried forever`，由 fixture 提供新 revision；斷言：

```ts
expect(claimSnapshot(schedule, nextSnapshot, 59999)).toBe(null);
expect(claimSnapshot(schedule, nextSnapshot, 60000)).toBeDefined();
expect(claimSnapshot(pendingSchedule, resetSnapshot, 60000)).toBe(null);
expect(claimSnapshot(failedSchedule, failedSnapshot, 120000)).toBe(null);
```

- [x] 跑測試確認失敗後實作排程判斷。首次有效素材可立即排程，後續以模型開始時間計算間隔；最後都在 finally 釋放對應 token，不能釋放另一請求的鎖。
- [x] 在入口的頂層本地 helper 接上 `$.clock`、`$.session.messages`、`$.model.complete`，設定 `model: 'haiku'`、`maxTokens: 512`、`timeoutMs: 15000`；以本機回傳型別處理回答／拒絕／例外。所有 API 呼叫仍在入口，工具及 render hook 不 await 模型。
- [x] 用 `mock.clock(on)` 與 deferred 模型 stub 測試：模型未回答時工具已完成、原結果不變；資料讀取期間出現新提示須拒絕過時快照；舊回應不能改新世代，較新動作不被摘要覆蓋；摘要時間等於 capturedAt。
- [x] 用真實原生事件名稱測試 `session.end` 後的 `classic.SessionStart` clear／resume 重建，不再次呼叫 `session.start`；終止時取消計時器，切換則保留節流與在途鎖。型別若不支持預期事件，記錄替代生命週期或停止該部分接線，不捏造事件。
- [x] 加無素材、API 拒絕、格式錯誤、逾時保留舊摘要與 timestamp、記憶體有界測試；跑原生驗證與全部測試，要求 0 fail。

## Task 5：面板與真實原型

**Files:** 建立 `hooks/view.js`、`tests/view.test.ts`、`tests/integration.test.ts`、`README.md`、`docs/prototype-results.md`；修改入口。

**Interfaces:** `paneLines(state: State, now: number): string[]`；入口註冊 immediate `/attention`，只呼叫 `$.ui.open`。Pane 的 id 為 `attention-mod`，只處理對應 requestId；不取代其他面板。

- [x] 寫 `pane shows snapshot age rather than arrival age`、`closing pane does not reopen on updates`、`attention command opens without prompt submission`；檢查 `paneLines(state, capturedAt + 20000)` 包含 `脈絡與證據更新：20 秒前`，其他面板走原 `next`，ui.open 沒有 `focus: true`。
- [x] 跑測試確認失敗後實作面板；用 `$.ui.resolve(e)` 的原生 Box／Text，有限長文字可換行與原生捲動。若自動開啟尚未放置，不搶焦點、不循環重開；使用者可用 `/attention` 開啟。關閉只影響可見性，背景頻率維持規格。
- [x] 用 `$.ui.mount` 測試 terminal／desktop 及 dock／inline tree；加一次包含事件、慢模型、新活動、失敗、切換的整合案例，檢查呈現的是觀察器狀態及經驗證摘要，而非只斷言 stub 回傳值。
- [x] 跑 `claude plugin validate --strict .`、`claude plugin test .`，確認 0 fail 且每個 test 檔實際執行；檢查 calls inventory 不含 prompt.submit／store／process／http 等未授權能力。不要把程式碼靜態檢查當成真實執行證據。
- [x] 在 `claude --plugin-dir .` 跑合成的小型工作：正常工具、故意失敗的測試及一次新任務；在主工作執行中觀察至少一次背景摘要。只用合成資料，不執行破壞性操作。記錄實際版本、面板寬窄／焦點、clear／resume、來源對照、摘要呼叫數與可取得用量；無法觀察的項目標成 NOT VERIFIED，不自行填估計值。
- [x] 在 prototype-results 記錄已知缺口與判準結果，README 說明 `claude --plugin-dir .`、`/attention`、用量來源、資料只在記憶體及未知等待狀態。若摘要阻塞主工作或捏造證據，依規格停止擴充，修正並重驗原場景後再評估。
- [x] 以 `completion-gate` 核對規格覆蓋與實際輸出；若準備提議 commit，按 L2 做一次 `code-review-codex` 與相關回歸驗證，先展示可審閱結果再問 Tom。未取得同意不得 commit、push 或發布。

## 執行與驗證界限

本計畫選擇先釐清本機 API，接著建立可離線驗證的資料／排程核心，最後接面板與真實模型。每個任務均先寫行為測試、確認失敗，再實作及確認通過；不以 missing stub 或 skipped hook 假裝已證明預期失敗。

已取得 2.1.288 本機型別並執行五項任務；實際證據與未驗證範圍見 prototype-results.md。等待訊號不足仍依規格降級。2026-10-04 Tom 核准完整、單一 JSON code block 的外框轉換；新增來源身分驗證、原生工作階段識別變化復原，以及排除原生本機指令輸出。

建議由目前代理逐項實作：五個任務共用狀態、世代與快照契約，先保持同一份上下文比較合適。若 Tom 選子代理方式，再載入 `subagent-driven-development`，每個實作任務都做規格與程式品質審查；不在目前規劃階段派出代理。

參考：[原生測試文件](https://code.claude.com/docs/en/plugins/mods/test)、[本機型別生成](https://code.claude.com/docs/en/plugins/mods/create)、[Mod 靜態分析與事件](https://code.claude.com/docs/en/plugins/mods/reference)。CLI 指令已用本機 `--help` 核對，執行成功與功能正確仍待實作驗證。
