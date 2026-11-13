# CLI Plugin 套件

七個共用套件可安裝在 Claude Code CLI 或 Codex CLI；Claude Code 另外提供專用的 `attention-mod` 和 `handoff-mod`。

## 套件用途

| 套件 | 常見用途 |
| --- | --- |
| quality-gates | 程式審查、驗證和品質檢查 |
| technical-decisions | 需求釐清、技術研究與方案比較 |
| repo-workflow | 理解 repo、建立隔離工作、交接與接續 |
| content-tools | 簡報、翻譯和文字整理 |
| work-journal | 記錄工作、查決定和整理報告 |
| session-preferences | 設定回應方式與後續選項 |
| skill-toolbox | 尋找與審查 skills |

更多任務範例請看[繁體中文使用指南](usage-examples-zh.md)或[英文使用指南](usage-examples-en.md)。Claude Code 專用的 `attention-mod` 與 `handoff-mod` 另見使用指南。

## 驗收與歷程

各宿主的 CLI 版本、平台、套件內容與已驗收行為見[plugin 驗收紀錄](../validation/skill-plugins/acceptance.json)。安裝器候選版本與歷史結果見[安裝器驗收索引](../validation/plugin-installer/README.md)。Codex 0.167.0 上的遠端 Git marketplace 更新另有[獨立證據](../validation/skill-plugins/codex-remote-marketplace-update-2026-11-13.json)。

安裝與遷移細節見[安裝與設定](installation.md)、[遷移與恢復](migration.md)及[Superpowers 相容性](superpowers-compatibility.md)。Plugins 從 main 的完整產物經 marketplace 發布；standalone skills 仍走 main→production→skill-sync 流程。Plugin tag 使用 `<plugin-name>-v<version>`。
