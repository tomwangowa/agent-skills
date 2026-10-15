# Task 4：共用日誌設定驗證

日期：2026-10-14。來源分支 `feat/skill-plugins`，基準 `69dfe5d`。本項來源整合已驗證，尚未提交或部署。

## 已驗證的行為

正式 MCP 啟動入口、logger、initializer 與 aggregator 都從共用 runtime 解析外部 `work-journal.json`。相對資料路徑以設定根目錄為準，與啟動 cwd 無關；缺少設定、空 notes list、不可寫或不可搜尋的活動目錄會明確失敗。設定讀取不回退到 server 旁的私人 `config.json`。來源開發保留明確的 `--config` 入口。

真實 SDK client 啟動已編譯的 stdio server，確認七個原有工具，並完成寫入／查詢。另一項測試由 shell logger 寫入，再由 MCP 讀回同一字串，包含相對環境變數覆寫、空白與非 ASCII 路徑，以及不同 cwd。舊資料格式與 reference locator 保留；index 測試已改用一次性資料，沒有缺私人設定就 early return 的成功案例。

| 檢查 | 結果 |
| --- | --- |
| Python 完整回歸 | 110／110 |
| Vitest（含五項真實 stdio 整合） | 49／49 |
| Node 原生測試 | 8／8 |
| logger reference／共用設定 shell 測試 | 退出 0 |
| TypeScript build、三份 shell syntax、catalog check、diff check | 退出 0 |
| lockfile production 安裝後的真實 smoke | 七工具，roundTrip=true；沒有 tsx、TypeScript 或私人 config |

RED、GREEN、完整回歸及 production 安裝紀錄存於本計畫的 ignored `.superpowers/sdd/2026-10-13-skill-plugins/task-4-*`。Production smoke 驗證後另加目錄搜尋權限檢查；最新版已由完整 build 與五項 stdio 整合測試驗證。

## 稽核與實作判定

`activity-logger-audit.md` 為 84／100，`work-log-analyzer-audit.md` 為 86／100；兩者均 0 critical、0 important。README、quick-start、長文件拆分共四項 suggestions 保留，不以增加無關文件取得評分。

Aggregator 雖未列在計畫的修改檔名中，仍改用同一 resolver，避免 skill 查詢另一份資料。單獨 reference finder 的歷史預設保留；skill 指示必須明確傳入已解析的活動目錄。

## 測試事故與限制

首次 RED 測試錯誤假設舊腳本會讀取新的設定環境變數，實際在正式活動目錄產生兩筆合成測試紀錄。已核對獨有 session IDs、描述與測試 project path，只刪除這兩筆；既有資料及 legacy metadata 保留。後續 shell 與 stdio fixtures 在呼叫腳本前加入 mkdir guard，拒絕暫存目錄之外的建立目錄操作；不覆寫 HOME 或 CODEX_HOME。這個 guard 是本測試入口的保護，不宣稱可以限制任何任意程式的所有檔案操作。

歷史快照：當時 Production 依賴掃描有 15 項漏洞（1 critical、10 high、3 moderate、1 low），新版 CLI 驗收也尚未進行。這些狀態已由 Task 8 後續驗收取代：目前 production/development audit 為零項漏洞，七包原生驗收限於列出的 macOS CLI 與 fixture 範圍；其他平台仍未驗證。

本項未修改正式 hooks 或 MCP 設定，未執行同步、安裝、commit 或發布。下一項為 Task 5 的七包定義及來源可攜性。
