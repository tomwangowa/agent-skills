# 「外部輸入」欄位設計

日期：2026-10-04  
狀態：Tom 已於 2026-10-04 確認書面規格，可作為實作依據。  
上層設計：[Attention Mod 設計](2026-10-03-attention-mod-design.md)。本文件只擴充面板，不改變上層設計的範圍與摘要規則。

## 目的

主 Claude 突然轉彎時，讓 Tom 在面板上一眼看到「最近有哪些不是他打的內容進了 context」。notice 也一併列出，雖然它只顯示在畫面上、model 讀不到，但可以幫忙對照時間。對話紀錄 JSONL 本來就保存每一列的時間，所以本欄位只負責即時顯示，事後追查仍然看 JSONL。

## 已確認的決定

1. 即時顯示，只存在 Mod 記憶體，不寫檔。
2. 黑名單篩選：非 Tom 輸入的列都顯示，只濾掉已知的系統雜訊；沒見過的種類照樣顯示。漏掉一筆輸入比多一行雜訊嚴重。
3. 只顯示，不餵給背景摘要。外部輸入不得進入 `sources` 或摘要快照。
4. 每筆記錄時間、種類、來源，以及節錄（第一個有內容的行，換行顯示）。
5. 跨回合保留最近 5 筆；`/clear`、resume、重載才清空。原本每筆標「本回合／前幾回合」，2026-10-05 第二次實機發現提示邊界會標錯、行尾也常被截掉，Tom 決定拿掉，只靠時間與排序對照。
6. 重載後不補舊資料，從空白開始，並顯示起算時間。
7. 最新 2 筆顯示節錄，較舊的 3 筆只顯示標題行，唯一例外是 door 為 `note` 的列：它的標籤只有 door 原名，看不出內容，所以任何位置都帶節錄（2026-10-05 Tom 選定）。面板 `rows` 從 12 調到 18。標題行和節錄行都換行顯示，不截斷。

## 收錄範圍

`session.append` 中符合下列條件的列：

- 沒有 `agentId`。子代理內部的列不會進主 context，回報會經由主對話的 delivery 或工具結果另外出現。
- door 是 `delivery`、`attachment`、`hook-context`、`notice`、`note`、`compaction`、`tool-message` 其中之一。其中 `notice`（`type:'system'`）只顯示在畫面上，model 不會讀到；slash command 的輸出（subtype `local_command`）也會以 notice 出現，要不要排除，等實機看過再決定。
- 不收 `prompt`、`response`、`tool-result`，因為面板已經有對應欄位；也不收 `command`，那是 Tom 自己觸發的。
- door 是 `attachment` 時，`message.name` 不在黑名單中。
- 內容不是空的。content 是空陣列、或全部都是空白文字的列，model 讀不到任何東西，不可能讓 Claude 轉彎，一律不列；只要有其他區塊（文字、媒體、`tool_result`、沒見過的區塊類型）就照常顯示。這是依內容判斷，不是依種類；畸形列（沒有 message、content 不是陣列）也視為空的。2026-10-05 Tom 依實機結果確認：Warp 的終端機通知 hook 在每次工具呼叫都會經 `hook-context` door 留下一列內容為空的 `hook_success`，會把 5 個位子洗掉。

### 黑名單初始內容

依 2026-10-04 這個 session 的 JSONL 實際出現的附件種類整理。這些是引擎自己產生的環境或工具清單資訊，不是外部文字：

| name | 列入原因 |
| --- | --- |
| `total_tokens_reminder` | 每回合的 token 餘額提醒 |
| `environment` | 工作目錄、平台等環境快照 |
| `model` | 模型身分 |
| `date` | 日期 |
| `deferred_tools_delta`、`deferred_tools_record` | 延後載入的工具清單與 schema |
| `agent_listing_delta`、`skill_listing` | 可用的 agent 與 skill 清單 |
| `advisor_tool`、`auto_mode` | 工具或模式開關 |
| `prompt_snapshot` | 系統提示快照 |
| `command_permissions` | 指令允許的工具清單 |
| `remote_session_change` | 遠端 session 與 commit 署名設定 |
| `instructions`、`session_context` | 每個 session 第一個提示都會附上的 CLAUDE.md 與固定脈絡（2026-10-05 實機後加入） |

刻意**不**列入、會照常顯示的種類：`hook_additional_context`（hook 注入）、`file`（`@` 附檔）、`edited_text_file`（Tom 在磁碟上改了檔案）、`mcp_instructions_delta`（MCP 伺服器帶進來的說明文字，中途連上的伺服器會帶進新的外部文字）、`silent_turn_reminder`、`hook_success`。`hook_success` 沒有輸出時會被上面的「內容是空的就不列」規則擋掉；其餘可能偏吵的，實機用過一陣子後再決定要不要移進黑名單。

## 元件與資料流

```text
session.append
  ├─ await next(e)                 原樣放行，不改寫
  ├─ entryFromAppend(e, result)    hooks/inputs.js，純函式，不依賴 $
  │     → null 或 {id, door, kind, origin, excerpt}
  ├─ apply({type:'external-input', entry, sessionId, epoch, at})
  └─ 既有的摘要素材流程（register.js 的 response／tool-result 過濾）不動
```

- `kind`：hook 注入顯示「hook 注入」，附件顯示「附件 `message.name`」，其他 door 用 `message.name`，沒有的話用 door 名稱。
- `origin`：依 `origin.kind` 轉成中文標籤，沒見過的種類直接顯示原字串。
- `excerpt`：取自 `result.message.content`（model 實際讀到的版本），依序找第一個非空白、而且不只是單一包裝標籤（例如 `<system-reminder>`）的行；全部都是標籤時退回第一個非空白行。只有媒體時顯示「[圖片]」，沒有文字時顯示「[無文字內容]」。
- 長度上限：種類、來源各 40 字，節錄 120 字，都按 Unicode code point 計算。2026-10-05 Tom 選定，原本是 24／24／40，面板窄所以兩行節錄與標題都改成換行顯示、不再截斷。
- `state.inputs` 保留最近 5 筆，同一個 uuid 只記第一次；`state.inputsSince` 記錄起算時間。

面板範例：

```text
外部輸入：14:05 附件 file · 引擎
            「Claude Code Mods.md」
          13:40 hook 注入 · hook（SessionStart）
            「Run lesson.py digest first…」
          13:12 附件 edited_text_file · 引擎
          11:02 local_command · 引擎
          09:58 hook 注入 · hook（SessionStart）
```

沒有資料時顯示：`外部輸入：尚無（14:20 起記錄）`。

## 生命週期

`/clear` 或 resume 時，`session.end` 會先重設成 `'between-sessions'`，接著 `classic.SessionStart` 在 `await next(e)` 之後再重設一次。SessionStart hook 注入的那一列可能剛好落在兩次重設之間，第二次重設時會被清掉。

處理方式：每筆記下收到時的 `state.sessionId`。

- 重設成 `'between-sessions'`：清空 `inputs`。
- 重設成實際的新 session id：只保留目前 epoch 的列，而且 sessionId 是 `'between-sessions'`、初始值，或已經是這個新 id（`reconnect()` 可能先把 id 換成新的、還沒重設），並把它們的 epoch 改成新值。epoch 條件讓空窗期留下的舊列，不會在之後被帶進不相干的 session。
- `external-input` 不檢查 `state.enabled`，空窗期也照收。

注入那一列實際在 `next(e)` 之前、之中還是之後 append，目前是 **NOT VERIFIED**；上面的規則三種順序都適用。

`entryFromAppend` 或節錄出錯時，在 try/catch 裡跳過該列，`next` 的結果照常回傳。

## 測試

自動化（`claude plugin test`）：

- `inputs.test.ts`：排除的 door 與 `agentId`；黑名單附件回傳 null；**沒見過的附件種類必須回傳一筆**；來源標籤、節錄長度、只有媒體、沒有文字、沒見過的 origin 種類；只有空內容才不列；開場的 `instructions`／`session_context` 不列而 `mcp_instructions_delta` 照列；節錄跳過包裝標籤行。
- `state.test.ts`：最多 5 筆、uuid 不重複、`new-prompt` 後保留、`'between-sessions'` 重設時清空、新 session 重設時保留空窗期的幾筆並改 epoch、`enabled:false` 時照收。
- `state.test.ts` 另外鎖住：**摘要快照中找不到任何外部輸入的文字**；`reconnect()` 先換 id 時注入列仍保留；空窗期的舊列不會被帶進之後的 session。
- `integration.test.ts`：面板標籤、`rows:18`、空白狀態。測試 kit 無法端到端觸發 `session.append`（2026-10-04 實測回報 `no implementation for session.append`），所以「`next` 結果原樣回傳」與「分類出錯不影響主流程」由程式碼審查與實機驗證確認。
- `view.test.ts`：起算時間、時間格式、最新 2 筆有節錄而較舊 3 筆沒有（`note` 例外，任何位置都有）；`inputRowNodes` 兩行都用 wrap，節錄縮排多 2 格。

實機驗證，結果記入 [原型結果](../../prototype-results.md)：

1. 設定會注入文字的 SessionStart hook，執行 `/clear` 後確認該筆留在面板上。
2. 用 `@` 帶入檔案，記錄 door 與 `name`。
3. 執行背景工作，確認回報是否走 `delivery`；同時在 Claude 工作中途打字，確認 Tom 自己輸入的內容是否被誤列為外部輸入（可能走 `delivery`，origin 為 `composer`，或附件 `queued_command`）。
4. 窄終端機下 `rows:18` 的面板不搶輸入焦點。

2026-10-04 一度因 hooks modules 開關未更新而無法執行 `claude plugin test .`；Tom 重新啟動一次 `claude` 後已恢復。

## 不做的事

寫檔保存、重載後補回、餵給背景摘要、點選展開、跨 session 總覽、改寫或遮蔽內容、通知、子代理內部的列、`command` door。
