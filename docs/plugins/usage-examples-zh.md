# agent-skills CLI plugins 使用範例

以下情境整理自實際工作紀錄中反覆出現的需求：釐清任務、審查修改、接續工作、記錄進度、製作簡報和維護 skills。公開範例已省略專案名稱與私人內容。

多數時候直接用白話描述需求即可。範例若列出明確指令，就要由你親自輸入。安裝套件會讓其中的 skills 可供使用，不會自動執行每一個 skill。

## 1. 把模糊需求整理成雙方確認的設計

**套件：** `technical-decisions`、`quality-gates`；Superpowers 可另外安裝。

**可以這樣說：**

> 我想改善［功能］，先跟我討論怎麼做，確認方向後再動手。

設計確認後再說：

> 照剛剛討論的方向做，完成後幫我檢查，也告訴我哪些地方還沒驗證。

**預期結果：** 先取得清楚的設計，再進入實作；完成後有審查結果和驗證證據。Superpowers 提供額外的規劃與實作流程，需要另外安裝。

## 2. 看懂陌生的 repo，準備開始新任務

**套件：** `repo-workflow`；結束前需要審查時再加 `quality-gates`。

可以先說：

> 幫我看懂這個 repo，我想開始做［任務］。

也可以自己呼叫指定的 skill：

- Claude Code：`/repo-workflow:understand-repo <path>`
- Codex：`$repo-workflow:understand-repo <path>`

接著可以要求它替指定任務預覽分支與 worktree（隔離工作目錄）。明確呼叫 `/repo-workflow:handoff` 或 `$repo-workflow:handoff` 記錄目前狀態；下次開始時，呼叫 `/repo-workflow:session-start` 或 `$repo-workflow:session-start`，重新確認交接中的前提。

**預期結果：** 看懂相關程式、開始前先看到隔離工作安排，並留下下一個 session 能核對的交接。

## 3. 合併前先檢查修改

**套件：** `quality-gates`。

**可以這樣說：**

> 幫我 review 這次的改動，看看有沒有問題；先告訴我發現了什麼，不要直接改。

**預期結果：** 每個發現都對應實際改動，並清楚交代驗證範圍。審查不會取代專案本身要求的檢查。

## 4. 用證據比較技術選項

**套件：** `technical-decisions`。

**可以這樣說：**

> 我們在［限制］下，該選［方案 A］還是［方案 B］？幫我查證一下，也看看各自有什麼風險。

**預期結果：** 一份看得出依據的決策整理，包含反面證據、取捨和未知事項。

## 5. 記錄工作，整理每週進度

**套件：** `work-journal`。

**可以這樣說：**

> 幫我記錄今天做了什麼，也附上參考過的文件。

之後再問：

> 幫我整理這週完成了什麼、做了哪些決定，還有什麼沒做完。

**預期結果：** 有日期的工作紀錄，以及能回查來源的摘要。新設定預設把活動紀錄放在 `~/.agent-skills/activities`。筆記資料夾可以之後再加；加入後，查詢也能搜尋自己的筆記。

## 6. 把技術工作整理成簡報或翻譯文件

**套件：** `content-tools`；若內容要根據已記錄的工作，再加 `work-journal`。

**可以這樣說：**

> 根據這份工作摘要，幫我做一份給新同事看的十分鐘簡報。

或：

> 幫我把這份 Markdown 翻成英文和繁體中文，程式碼和連結保持原樣。

**預期結果：** 按聽眾安排的簡報大綱，或保留技術內容的翻譯。分享前先檢查成品。

## 7. 讓回應偏好在不同 session 維持一致

**套件：** `session-preferences`。

**可以這樣說：**

> 我想讓你以後都用繁體中文回答，說明清楚一點。先讓我看看設定內容，確認後再存。

**預期結果：** 先看到建議的設定內容，確認後才儲存。

## 8. 找到適合的 skill，或改善自己寫的 skill

**套件：** `skill-toolbox`。

**可以這樣說：**

> 我想做［任務］，有什麼 skill 可以用？

要檢查自製 skill 時：

> 幫我看看這個 skill 寫得怎麼樣，有哪些地方需要改？

**預期結果：** 一份可用的候選清單，或附有具體問題的審查結果。目錄中看得到名稱，不代表已安裝。

## 9. 讓長時間的 Claude Code 工作比較容易接續

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
