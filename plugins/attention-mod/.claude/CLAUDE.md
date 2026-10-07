# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## 這是什麼

`attention-mod`：Claude Code Mod（function hooks plugin）的本機原型。在目前工作階段旁開一個面板「你到底在忙什麼」，顯示目標、Claude 的工作脈絡、正在執行的工具、最近證據與待回答訊號。目標版本是 Claude Code 2.1.288。

改 `hooks/` 之前先載入 `plugin-authoring` skill，Mod 的 hook 介面、熱重載和除錯方式在那裡。

## 指令

```sh
claude plugin validate --strict .   # npm run validate；含 calls inventory
claude plugin test .                # npm test；跑 tests/ 下所有 *.test.ts
claude --plugin-dir "$PWD"          # 實際載入 Mod 試用，面板沒出現就輸入 /attention
```

- `claude plugin test` 只吃資料夾參數，沒有單檔或單一測試的篩選選項。
- 本機沒有 `tsc`，型別只在編輯器裡檢查；validate／test 通過不代表型別編譯通過。
- `.claude-plugin/types/` 是 Claude Code 啟動 `--plugin-dir` 時在本機產生的型別（已 gitignore）。API 形狀以這份為準，公開 GitHub 上的型別檔版本較舊，跟本機不同。

## 架構

`hooks/hooks.json` 只載入 `hooks/register.js`。它持有所有可變狀態並接上事件；其他模組都是純函式，方便單獨測試：

- `state.js`：`reduceState(state, event)`，immutable reducer。處理 source、tool-start/end、wait、turn、new-prompt、session-reset、external-input；外部輸入放在 `inputs`／`inputsSince`，跟 `sources` 分開。`session-reset` 換到新 session 時，只保留目前 epoch、而且 sessionId 是 `UNKNOWN_SESSION`／`BETWEEN_SESSIONS` 或已是新 id 的列（`reconnect()` 可能先換 id 再 reset）。`boundedText` 以 Unicode code point 截斷並插入 `[truncated]` 標記。
- `snapshot.js`：從 sources 挑出目標來源、goal context、近期 user 提示，再補其他新素材，序列化後整份 prompt 不超過 8,000 code points（JSON escaping 也算在內）。
- `summary.js`：固定的 system prompt，加上 `parseSummary` 嚴格驗證。只接受 `goal/context/evidence` 三個 key，每欄 null 或 `{text, sources}`，text 最多 160 code points，引用的來源必須存在於快照。`context` 只能引用 `assistant`，`evidence` 只能引用 `tool`／`tool-success`／`tool-error`／`tool-denied`／`tool-cancelled`。`unwrapSummaryJson` 只拆掉完整、單一的 ```` ```json ```` 外框。
- `scheduler.js`：同一份 `sessionId:epoch:revision` 只試一次（失敗不重試），開始時間相隔至少 60 秒，同時最多一個呼叫。
- `view.js`：`paneRows` 把狀態轉成三個區塊（摘要、即時、外部輸入），只帶語意色調不帶顏色；`liveTone` 決定即時區塊色調、`actionDot` 決定「動作」的點（「需要你」的點在 `paneRows` 裡依有無等待決定）；`inlineFields`／`footerNotes` 還原 0.2.0 的平面順序；`paneLines` 是純文字版本。不呼叫模型。`sectionById(view, id)` 讓兩種版面都依 id 取區塊，不依位置。
- `theme.js`：`colorFor(tone)` 把色調對應到終端機具名色，未知色調回傳 undefined。`register.js` 依 `e.props.placement` 呼叫 `drawDock`（圓角框）或 `drawInline`（平面）。
- `feedback.js`：`buildTeamsLink(raw, recipient)` 把使用者輸入轉成 Teams 聊天 deep link（只含輸入文字與分類標籤，長度上限 `LINK_LIMIT`，超過以 code point 截斷並標 `[truncated]`；回傳的 `message` 永遠是完整純文字，供複製），`parseFeedback` 解析 `bug:`／`idea:` 前綴，`parseRecipient` 把收件人限制成單一 email，避免夾帶額外參數。收件人來自 `userConfig.feedbackRecipient`，程式碼與測試不得出現真實地址（repo 是公開的，測試用 `example.com`）。表單狀態 `feedback` 是 `register.js` 的記憶體變數，`drawFeedback` 負責畫出；沒設定收件人時只提供複製內容。
- `inputs.js`：`entryFromAppend(e, result)` 把 `session.append` 的列分類成外部輸入或 null；`NOISE` 黑名單每項附原因，沒列的種類照樣顯示；被拒絕的 append（`result.deny`）不算。外部輸入只進 `state.inputs`，不進 `sources`，所以不會進摘要快照。測試 kit 無法端到端觸發 `session.append`，分類邏輯要放在這個純函式裡測。

資料流：事件 hook 先 `await next(e)` 拿原結果，再把觀察寫進 state，最後原樣回傳。`clock.every(1000)` 背景計時器負責 redraw 並呼叫 `summarize()`，後者建快照、claim 排程，再呼叫 `$.model.complete({model:'haiku', maxTokens:512, timeoutMs:15000})`。

改程式時要守住的不變條件（設計理由見 spec）：

- **被動觀察**：不改寫提示、工具結果或權限決定；觀察失敗包在 `try/catch` 裡，不能影響呼叫端。只用 clock、model.complete、session.id/messages、command.register、ui（含回饋表單的 `ui.copy`）；不用 store、檔案、http、process，也不提交主對話提示。validate 的 calls inventory 會反映這點。
- **世代保護**：`epoch` 在 new-prompt 和 session-reset 時加一。模型回應寫回前要核對 `sessionId` 和 `epoch`，晚到的舊回應直接丟掉。排程鎖跨 reset 仍然有效，不能因為世代失效就提早釋放。
- **事件與模型分工**：「動作」「需要你」只由事件產生；「目標」「脈絡」「證據」只來自摘要，不能互相覆寫。`tool.check` 的 `ask` 只算「等待狀態不明」；`AskUserQuestion` 實際 render 才算等你回答；`permission_prompt` 只有在剛好一個執行中工具時才對應成權限等待。
- **clear／resume**：實測不會再觸發 `session.start`，也不保證有 `classic.SessionStart`。`session.end` 記下 `endingSessionId` 後停用，由計時器在 `reconnect()` 輪詢 `session.id()`，看到 ID 改變才恢復並 `restore()`。
- **重建素材**：`restore()` 從 `session.messages()` 重建（沒有穩定 row id，所以自己產生 `e{epoch}-s{n}` 識別），並排除 `<command-name>`／`<local-command>`／`<system-reminder>` 開頭的訊息。
- 子代理事件（帶 `agentId`／`agent_id`）不影響主工作的動作與等待。

## 測試

測試用 `claude-code/testing` kit。`tests/fixtures.ts` 的 `host(on, options)` 把原生 host 全部 stub 掉，搭配 `mock.clock`，並在 `record` 收集 `models`／`opens`／`prompts`／`commands`；`options.model`、`options.tool`、`options.readMessages` 可注入慢回應、失敗或特定對話。測試不會真的呼叫模型或執行 Bash。

既有慣例：斷言實際行為，例如模型請求數與時間、`JSON.parse(request.prompt)` 裡的 sources、`mounted.drawn()` 的畫面，不只比對 mock 的回傳字串。新回歸案例先寫出會失敗的測試再修。

## 文件

- `docs/superpowers/specs/2026-10-03-attention-mod-design.md`：Tom 確認過的規格，是實作依據。
- `docs/decisions/`：決策紀錄。例如 2026-10-04 Tom 選擇只拆 JSON 外框，驗證不放寬；要改驗證規則、上限或範圍，先問 Tom。
- `docs/prototype-results.md`：VERIFIED／NOT VERIFIED 清單與真實用量。不要把 NOT VERIFIED 的項目（寬終端機側邊 dock、Desktop 繪製、完整人工授權流程、工作中 `/resume`）講成已驗證。
- `docs/runtime-api.md`：從本機型別整理的 API 契約。
