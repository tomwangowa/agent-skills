# 本機 API 契約

取得方式：以最小空 Mod 啟動 `claude --plugin-dir .`，未提交模型提示。
本機產生檔：`.claude-plugin/types/claude-code/index.d.ts`，第一行標示 2.1.288。`agent.list`、`process.run`、`session.cwd` 依 2.1.310 的型別檔整理（見下）；`$.store`、`$.session.model()`、`$.session.usage()`、`turn.step` 依 2.1.312 的型別檔整理（目標版本 2.1.312，見 CLAUDE.md）。2.1.288 未確認有這些項目。

- `model.complete(request, { signal? })`：回傳 `ModelCompleteResult`；成功有 `isAnswered/text/usage`，失敗有 `isAnswered: false/reason/usage`。可設定 `maxTokens/timeoutMs`；拒絕送出的請求可能 reject。
- `session.messages()`：主對話的 `role/text/toolUses/toolResults?`，沒有穩定 row id；初次重建產生本地來源識別。即時 `session.append` 有 `uuid/door/origin/agentId?/message.content`，可識別追加列與子代理。
- `tool.call`：工具參數在事件頂層，帶 `tool_use_id` 與可選 `agentId`；結果有 `deny` 或 `result/text?/isError?`。拒絕與一般工具失敗須分開；無結構化取消訊號時，不能從錯誤文字自信判定取消。
- `session.end`：帶 reason、sessionId、resume。`clear/resume` 後程序仍存活；不能假設 `session.start` 再次執行。0.4.7 起不用 `classic.SessionStart`：有 managed settings 的機器上，內建 `cc-plugin-sec-default` 會讓 `classic.*` 繞過使用者裝的 plugin（2.1.304 起實際看到）。改以 `$.session.id()` 是否變動判斷新對話：`session.end` 之後等 id 換掉；沒有 `session.end` 而 id 換了（fork）就重設。
- `$.session.cwd()`：回傳目前工作目錄的字串（型別 `string`）。
- `$.process.run(argv, init?)`：回傳 `{ exitCode, stdout, stderr }`；`init` 可帶 `cwd`、`env`、`stdin`、`timeoutMs`。本外掛只跑一個唯讀指令 `git --no-optional-locks rev-parse --path-format=absolute --git-dir --git-common-dir --abbrev-ref HEAD`，`timeoutMs` 為 2000。目錄輸出若不是絕對路徑，面板顯示「無法讀取」，不猜測。
- `$.agent.list()`：回傳 `AgentInfo[]`，欄位有 `id`、`type`、`description`、`status`；沒有時間欄位。`status` 為 pending、running、waiting、idle、completed、failed、killed 其中之一。
- `$.store`：Quick Notes 用的 `get`、`set`、`delete`。key 是 `notes:<git 共用目錄>`；不在 git 裡時是 `notes-cwd:<目錄>`。值是字串；`get` 沒有資料時回傳 undefined（視為空筆記），非字串視為讀取失敗、不覆寫。整個 store 上限 4 MiB。實機讀寫尚未驗證（第 9 項）。
- `$.session.model()`：回傳目前模型字串。讀取失敗時保留上次的值，不清空。
- `$.session.usage({ breakdown: 'summary' })`：回傳 `rateLimits` 與 `context.breakdown`。本外掛讀 `breakdown.skills`（`includedSkills`／`totalSkills`）與 `breakdown.mcpTools`；`mcpTools` 每個工具一筆，所以計數是工具數，不是伺服器數。每五個計時 tick 讀一次，失敗保留上次讀數。
- `turn.step`：`async function*` 的 hook，先 `yield* next(e)` 原樣傳遞。主迴圈的步驟把 `e.effort ?? null` 記入 `session.effort`；帶 `agentId` 的子代理步驟不改動主 effort。實機的 effort 值尚未驗證（第 9 項）。
- 測試 kit：host 對 `$` 的回答要包成 `{ value }`，`process.run` 也一樣；裸物件會讓 hook 被跳過（`returned neither { value } nor { deny }`）。`tests/fixtures.ts` 的 `host()` 已包好。
- `clock.after/every` 回傳有 cancel 方法的計時器；模型呼叫僅從背景 callback 開始。
- `ui.open` 回傳 isPlaced 與可選 reason，不保證自動面板已放置；不傳 focus: true。`ui.render` Pane 的 requestId 對應面板 id。
- `ui.render` AskUserQuestion 確認問題已呈現；`tool.call` 結束時解除對應等待。權限路由 ask 不能直接視為人工等待，只標「等待狀態不明」。0.4.7 起不再聽 `classic.Notification`（理由同上），所以不會再標成「有權限通知」。

VERIFIED：版本、上述宣告及最小 Mod 成功載入；觀察器測試已確認缺少 hook 時失敗。
真實背景摘要、窄終端機面板、clear 與啟動時 resume 已實測；詳細範圍見 [原型結果](prototype-results.md)。NOT VERIFIED：完整人工授權流程、執行中 /resume、Desktop 實際繪製。原生驗證／測試不等同 tsc 編譯。
