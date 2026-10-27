# 決策：放寬被動觀察，允許唯讀 git 讀取與子代理列表

日期：2026-10-26  
狀態：Tom 於 2026-10-26 選定；實作版本 0.5.0（尚未實作、尚未發版）。

## 脈絡

worktree 與子代理面板需要的資訊，目前的被動觀察規則無法提供：要知道 session 在哪個 worktree、分支是什麼，以及子代理的類型與狀態。規則原本只允許 clock、model、session、command、ui，不允許 process。

2.1.310 的 `$.process.run`、`$.agent.list`、`$.session.cwd` 可以提供這些資訊。2026-10-26 在 managed 機器上實測：`process.run` 能執行 git 並讀到分支與工作樹資訊；`agent.list` 連續 22 次 tick 沒有錯誤，並列出已完成的 Explore 子代理。

## 決策

- 允許一條 process 指令：`git --no-optional-locks rev-parse --path-format=absolute --git-dir --git-common-dir --abbrev-ref HEAD`，`timeoutMs: 2000`。只讀，不寫檔。`--path-format=absolute` 讓兩個目錄都是絕對路徑：在主 checkout 的子目錄，git 會把 common dir 印成相對的 `../.git`，直接比較會把主 checkout 誤判成連結的工作樹。
- 允許 `$.agent.list()`（每秒輪詢）與 `$.session.cwd()`。兩者都是唯讀。
- 不允許其他 process 指令、寫檔、store、http。
- 子代理事件不影響「動作」與「需要你」。

## 不變的部分

- 不改寫提示、工具結果或權限決定；觀察失敗包在 `try/catch` 裡。
- 不提交主對話提示。

## 尚未驗證

- Team／Enterprise 組織的 sec-default 是否會擋 `process.run` 與 `agent.list`。目前只在 managed 個人機器上測過。
- `/clear` 之後 `agent.list` 是否清空。
- 最低版本定為 2.1.310；2.1.288 是否有這兩個 API 尚未確認。

## 考慮過但未採用

| 方案 | 未採用原因 |
|---|---|
| 維持不用 process | 沒有其他來源可以可靠取得分支；Agent 工具的結果也不含 worktree 路徑（見設計稿） |
| 允許任意 git 子命令 | 目前只需要一條；範圍越小，審查越容易 |
| 用 store 記錄狀態 | 違反「不用 store」 |
