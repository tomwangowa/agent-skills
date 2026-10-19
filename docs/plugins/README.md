# 七包 CLI plugins

這組產物仍是未發布草稿。來源與暫存資料測試已有證據，2026-10-15 已在 macOS 隔離 fixture 以 Claude Code 2.1.300、Codex 0.162.1 完成兩個 CLI 的原生驗收，檢查項目與限制見 `docs/validation/skill-plugins/acceptance.json`；`session-preferences`、`work-journal`、`repo-workflow` 與 `skill-toolbox` 在那之後有修改，發布前需要重新進行原生驗收。依賴安全檢查與原生驗收是兩個獨立門檻。不要把 artifact checker 通過當成可以發布。

| 套件 | 用途範例 |
| --- | --- |
| quality-gates | 「看一下這份 diff」；「確認測試結果再說完成」 |
| technical-decisions | 「先釐清這個功能需求」；「評估技術可行性」；手動啟動 PM→RD |
| repo-workflow | 「這段程式怎麼演變的」；「同步 repo」；手動交接未完成工作；開工時接手交接 |
| content-tools | 「規劃分享簡報」；「翻譯 markdown」；「把文章改自然一點」 |
| work-journal | 「記錄本次工作」；「查本週決策與 TODO」 |
| session-preferences | 手動自訂 session 語氣、說明深度與歸還控制權規則 |
| skill-toolbox | 「找適合的 skill」；「檢查 skill 品質」；手動同步 standalone skills |

Claude 品質包含 code-review-claude，Codex 含 code-review-codex。Claude-only workflow designer 不進 Codex toolbox。來源共 39 個成員，各平台按用途排除不適用入口；原 catalog 生命週期保留。User-only skill 仍需明確手動呼叫，安裝 plugin 不代表授權自動執行每個入口。

使用前讀 [安裝與設定](installation.md)、[遷移與恢復](migration.md)、[Superpowers 相容性](superpowers-compatibility.md)。團隊可採用 [指示範本](team-instructions.md)，再保留自己的審查與批准規則。

Plugins 從 main 的完整產物經 marketplace 發布；standalone skills 仍走原本 main→production→skill-sync 流程。發布 tag 採 `<plugin-name>-v<version>`。Commit、push、發布各自需要維護者批准；此文件沒有執行這些動作。
