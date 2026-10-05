# 本機 API 契約

取得方式：以最小空 Mod 啟動 `claude --plugin-dir .`，未提交模型提示。
本機產生檔：`.claude-plugin/types/claude-code/index.d.ts`，第一行標示 2.1.288。

- `model.complete(request, { signal? })`：回傳 `ModelCompleteResult`；成功有 `isAnswered/text/usage`，失敗有 `isAnswered: false/reason/usage`。可設定 `maxTokens/timeoutMs`；拒絕送出的請求可能 reject。
- `session.messages()`：主對話的 `role/text/toolUses/toolResults?`，沒有穩定 row id；初次重建產生本地來源識別。即時 `session.append` 有 `uuid/door/origin/agentId?/message.content`，可識別追加列與子代理。
- `tool.call`：工具參數在事件頂層，帶 `tool_use_id` 與可選 `agentId`；結果有 `deny` 或 `result/text?/isError?`。拒絕與一般工具失敗須分開；無結構化取消訊號時，不能從錯誤文字自信判定取消。
- `session.end`：帶 reason、sessionId、resume。`clear/resume` 後程序仍存活；`classic.SessionStart` 的 source 可用於重建；不能假設 `session.start` 再次執行。
- `clock.after/every` 回傳有 cancel 方法的計時器；模型呼叫僅從背景 callback 開始。
- `ui.open` 回傳 isPlaced 與可選 reason，不保證自動面板已放置；不傳 focus: true。`ui.render` Pane 的 requestId 對應面板 id。
- `ui.render` AskUserQuestion 確認問題已呈現；`tool.call` 結束時解除對應等待。權限路由 ask 不能直接視為人工等待。Notification permission_prompt 只在能對應單一主工作活動時標成權限通知，其餘仍未知。

VERIFIED：版本、上述宣告及最小 Mod 成功載入；觀察器測試已確認缺少 hook 時失敗。
真實背景摘要、窄終端機面板、clear 與啟動時 resume 已實測；詳細範圍見 [原型結果](prototype-results.md)。NOT VERIFIED：完整人工授權流程、執行中 /resume、Desktop 實際繪製。原生驗證／測試不等同 tsc 編譯。
