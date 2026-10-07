# 決策：attention-mod 只在 agent-skills 開發，不再使用 subtree

日期：2026-10-07  
狀態：Tom 於 2026-10-07 決定；採用單一 repo。

## 脈絡

attention-mod 原本在獨立的本機 repo `你在忙什麼` 開發（沒有 remote），再用 `git subtree pull` 同步進 agent-skills（`feat(plugins): add attention-mod via subtree` 與其後的更新）。0.4.0 的回饋功能直接寫在 agent-skills，來源 repo 沒有這些內容，兩份開始分岔。

## 決策

- 從此只在 agent-skills 的 `plugins/attention-mod/` 開發、測試與發佈。
- 不再執行 `git subtree pull`／`push`；`docs/superpowers/` 下舊的計畫與規格裡提到的 subtree 步驟是歷史紀錄，不再適用。
- 不帶來源 repo 的 commit 歷史；內容以 agent-skills 現有檔案為準。

## 搬移前的核對

2026-10-07 把來源 repo（推到 `tomwangowa/attention-mod-source`，HEAD `6b685fe chore(attention): bump to 0.3.2`）與 agent-skills `main` 的 `plugins/attention-mod`（0.3.2）逐檔比對：36 個檔案、檔案清單一致，`diff -ru`（排除 `.git`、`node_modules`、`types`、`.superpowers`）沒有任何差異。所以沒有來源獨有的內容需要搬進來。

## 後續

- 來源 repo 保留為唯讀備份，何時封存或刪除由 Tom 決定；內容已完整存在於 agent-skills 的 git 歷史（`f82ee94` 起）。
- 之後發佈的流程：在 agent-skills 提 PR、合併後執行 `claude plugin update attention-mod@tomwangowa` 並重新啟動 Claude Code。
