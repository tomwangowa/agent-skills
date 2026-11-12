# 七包 CLI plugins

2026-11-12 已在 macOS 隔離設定完成 Claude Code CLI 2.1.322 與 Codex CLI 0.167.0 的原生驗收紀錄；兩個宿主的七包安裝都綁定到精確的套件內容。Claude 套件從遠端 GitHub marketplace 安裝，Codex 套件從隔離的本機 marketplace 安裝；Codex 遠端 Git marketplace 路徑仍未驗證。驗收項目、逐包結果與限制見[原生驗收紀錄](../validation/skill-plugins/acceptance.json)。其他版本、作業系統，以及 Claude 一般設定下的自動 MCP 探索仍未驗證。依賴安全檢查與原生安裝驗收是不同項目，需分別核對。

| 套件 | 用途範例 |
| --- | --- |
| quality-gates | 「看一下這份 diff」；「確認測試結果再說完成」 |
| technical-decisions | 「先釐清這個功能需求」；「評估技術可行性」；手動啟動 PM→RD |
| repo-workflow | 「這段程式怎麼演變的」；「同步 repo」；手動交接未完成工作；開工時接手交接；開新任務時建分支與 worktree |
| content-tools | 「規劃分享簡報」；「翻譯 markdown」；「把文章改自然一點」 |
| work-journal | 「記錄本次工作」；「查本週決策與 TODO」 |
| session-preferences | 手動自訂 session 語氣、說明深度與歸還控制權規則 |
| skill-toolbox | 「找適合的 skill」；「檢查 skill 品質」；手動同步 standalone skills |

Claude 品質包含 code-review-claude，Codex 含 code-review-codex。Claude-only workflow designer 不進 Codex toolbox。來源共 48 個成員，各平台按用途排除不適用入口；原 catalog 生命週期保留。User-only skill 仍需明確手動呼叫，安裝 plugin 不代表授權自動執行每個入口。

使用前讀 [安裝與設定](installation.md)、[遷移與恢復](migration.md)、[Superpowers 相容性](superpowers-compatibility.md)。團隊可採用 [指示範本](team-instructions.md)，再保留自己的審查與批准規則。

Plugins 從 main 的完整產物經 marketplace 發布；standalone skills 仍走原本 main→production→skill-sync 流程。發布 tag 採 `<plugin-name>-v<version>`。Commit、push、發布各自需要維護者批准；此文件沒有執行這些動作。
