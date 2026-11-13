# agent-skills CLI plugins 使用範例

以下情境整理自實際工作紀錄中反覆出現的需求：釐清任務、審查修改、接續工作、記錄進度、製作簡報和維護 skills。公開範例已省略專案名稱與私人內容。

多數時候直接用白話描述需求即可。範例若列出明確指令，就要由你親自輸入。安裝套件會讓其中的 skills 可供使用，不會自動執行每一個 skill。

## 1. 把模糊需求整理成雙方確認的設計

**套件：** `technical-decisions`、`quality-gates`；Superpowers 可另外安裝。

**可以這樣說：**

> 我想改善［功能］。先不要改檔，一次問我一個問題。比較實際可行的方向，列出假設和還沒決定的事，再整理成一份短設計讓我確認。

設計確認後再說：

> 把核准的設計拆成工作計畫並完成修改。檢查改動，告訴我實際跑過哪些檢查，以及還有哪些地方沒有驗證。

**預期結果：** 先取得清楚的設計，再進入實作；完成後有審查結果和驗證證據。Superpowers 提供額外的規劃與實作流程，需要另外安裝。

## 2. 看懂陌生的 repo，準備開始新任務

**套件：** `repo-workflow`；結束前需要審查時再加 `quality-gates`。

先要求 agent 根據程式碼說明相關模組，再預覽隔離工作環境。明確呼叫入口時：

- Claude Code：`/repo-workflow:understand-repo <path>`
- Codex：`$repo-workflow:understand-repo <path>`

接著可以要求它替指定任務預覽分支與 worktree（隔離工作目錄）。明確呼叫 `/repo-workflow:handoff` 或 `$repo-workflow:handoff` 記錄目前狀態；下次開始時，呼叫 `/repo-workflow:session-start` 或 `$repo-workflow:session-start`，重新確認交接中的前提。

**預期結果：** 看懂相關程式、開始前先看到隔離工作安排，並留下下一個 session 能核對的交接。

## 3. 合併前先檢查修改

**套件：** `quality-gates`。

**可以這樣說：**

> 審查目前的改動，找出錯誤、安全問題和回歸風險。不要改檔。先列出可處理的發現並附檔案與行號，再說明實際執行過哪些檢查，以及那些檢查沒有涵蓋什麼。

**預期結果：** 每個發現都對應實際改動，並清楚交代驗證範圍。審查不會取代專案本身要求的檢查。

## 4. 用證據比較技術選項

**套件：** `technical-decisions`。

**可以這樣說：**

> 依照［限制］比較［方案 A］和［方案 B］。先找最有力的反面證據，盡量使用原始文件；把已確認的事實和推論分開，提出建議並列出仍要驗證的地方。

**預期結果：** 一份看得出依據的決策整理，包含反面證據、取捨和未知事項。

## 5. 使用公司 AI endpoint 的 Codex

**情境：** 透過公司 AI endpoint（公司提供的模型服務網址）使用 Codex，但沒有 ChatGPT 帳號登入。

保留原有 endpoint 和認證設定即可；安裝器不會設定或測試它們。下載 plugin 還是需要連得到所選 marketplace 或 GitHub 來源。

**驗收範圍：** macOS 的 Codex CLI 0.167.0 測試在未登入帳號時完成安裝，並保留一份模擬的公司 provider 設定；真實公司 endpoint 連線、其他 CLI 版本與其他平台尚未驗收。驗收證據見[公司 endpoint 測試紀錄](../../docs/validation/plugin-installer/codex-no-account-native-results.md)，操作細節見[安裝器說明](../../installer/README.zh.md)。

## 6. 記錄工作，整理每週進度

**套件：** `work-journal`。

**可以這樣說：**

> 記錄我今天完成的工作，以及實際參考過的文件。

之後再問：

> 整理本週完成事項、決定和未完成工作；可以的話，替每一點附上對應的活動紀錄。

**預期結果：** 有日期的工作紀錄，以及能回查來源的摘要。新設定預設把活動紀錄放在 `~/.agent-skills/activities`。筆記資料夾可以之後再加；加入後，查詢也能搜尋自己的筆記。

## 7. 把技術工作整理成簡報或翻譯文件

**套件：** `content-tools`；若內容要根據已記錄的工作，再加 `work-journal`。

**可以這樣說：**

> 根據這份工作摘要，替新同事規劃一場十分鐘簡報。保留重要主張和決定，並標出還要確認的內容。

或：

> 把這份 Markdown 翻成英文和繁體中文。保留程式碼、連結和識別字。

**預期結果：** 按聽眾安排的簡報大綱，或保留技術內容的翻譯。分享前先檢查成品。

## 8. 讓回應偏好在不同 session 維持一致

**套件：** `session-preferences`。

**可以這樣說：**

> 列出我目前對回應語言、說明深度和後續選項的偏好。建議一份簡潔的繁體中文設定，並在需要時解釋不熟悉的詞。等我確認後再儲存。

**預期結果：** 先檢視目前 session 規則；若要改個人設定，會另行確認。

## 9. 找到適合的 skill，或改善自己寫的 skill

**套件：** `skill-toolbox`。

**可以這樣說：**

> 找出適合［任務］的 skills，分別標出已安裝、可以安裝和目前無法取得的項目。

要檢查自製 skill 時：

> 審查這個 skill 的觸發條件、步驟、安全指示和範例；逐項列出問題與建議修改方式。

**預期結果：** 一份可用的候選清單，或附有具體問題的審查結果。目錄中看得到名稱，不代表已安裝。

## 10. 讓長時間的 Claude Code 工作比較容易接續

**僅限 Claude Code：** 加裝 `attention-mod` 和 `handoff-mod`。

用 `/attention` 開啟注意事項面板，`/handoff-mod:handoff` 建立交接，再用 `/handoff-resume` 查看可接續的工作。

**預期結果：** 快速查看 session 內容，並為下次留下交接。Attention 摘要會把對話／工具節錄交給 Haiku，並使用模型 token；這和通用的 `repo-workflow` 交接是兩套功能。

## 套件用途速查

| 套件 | 適合處理 |
| --- | --- |
| `technical-decisions` | 需求、研究和技術選擇 |
| `quality-gates` | 程式審查和完成前的驗證 |
| `repo-workflow` | 理解 repo、開新工作、接續未完成任務 |
| `work-journal` | 記錄工作、查決定和未完成事項 |
| `content-tools` | 簡報、翻譯和文字整理 |
| `session-preferences` | 回應語言、說明深度和交接方式 |
| `skill-toolbox` | 尋找 skills、審查 skill 品質 |
| `attention-mod`、`handoff-mod` | Claude Code 的進度查看與交接 |
| Superpowers | 選用的規劃與實作流程，需另外安裝 |

更多套件項目見[完整清單](../../SKILLS_CATALOG.md)，安裝步驟見[安裝器說明](../../installer/README.zh.md)。
