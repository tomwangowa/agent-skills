# Task 3：個人偏好覆寫驗證

日期：2026-10-14。工作分支：`feat/skill-plugins`。本項來源實作完成，尚未提交或部署；Task 4–8 仍待完成。

## 行為與證據

| 行為 | 實測結果 |
| --- | --- |
| 同名個人模組整份取代、新模組追加 | 以臨時預設與個人目錄驗證；不修改套件預設 |
| 按需讀取的 reference | 指向有效個人路徑，不把內容提前注入或加入必讀 INDEX |
| 部分損壞 | 無效 UTF-8、空檔、錯誤 INDEX 或 symlink 回報未載入；其他有效模組保留 |
| control-return | 完整個人規則取代預設 Rule block；不進 session-preferences INDEX |
| 停用 | 兩個 hooks 在 `AGENT_SESSION_PREFS=off` 時輸出為空 |
| 預覽後內容變更 | SHA-256 不符就拒絕寫入，要求新預覽與新確認 |
| 並行修改 | 兩個真實程序使用相同舊 hash，只有一個寫入成功，另一個回報衝突 |
| 更新 | 原始 base hash 保留；預設變更由 doctor 提示，不修改個人副本；移除副本後不產生過時提示 |
| 原始目錄與搬移後的 plugin | 只讀本包 runtime；缺少 runtime 時警告，不能借用父目錄的另一份 runtime |
| 實際操作入口 | CLI load／save 在測試設定目錄執行；含空白與非 ASCII 路徑 |

本輪完整 Python 回歸為 **110／110**；Vitest 為 **44／44**，Node 原生 stdio 測試為 **8／8**。TypeScript 編譯、catalog `--check` 與 `git diff --check` 均退出 0。基準是 Python 87／87，新增 23 項偏好行為測試。失敗與通過紀錄保存在該計畫的 `.superpowers/sdd/2026-10-13-skill-plugins/`，不進發佈包。

## Skill 稽核處置

已對兩份修改後的 SKILL 執行 `skill-auditor`，原始報告為 `session-preferences-audit.md` 與 `control-return-audit.md`。自動評分分別為 80／100、76／100，兩者均為 0 critical、1 important；這是自動工具原始結果，不以分數當作發布證明。

兩份 important 均來自「六個 HTML 安全關鍵字只出現三個」的密度檢查。人工檢視確認這兩個 hooks 只輸出 JSON，不渲染 HTML 或讀取 URL；檔名驗證、symlink 拒絕、舊內容雜湊、JSON 編碼及局部錯誤回報已有實作與行為測試。因此將該項列為不適用的啟發式誤報，不增加無關的 XSS／CSP 文字來取得分數。

保留的三項 suggestions：session-preferences 缺少工具可辨識的 quick-start 檔；control-return 缺少 README 與 quick-start 檔。現有 SKILL 有操作與錯誤說明，這三項不阻擋本次來源整合。

`writing-skills` 的唯讀場景先確認舊指示缺少個人載入與舊預覽處理，再核對新版手動載入、確認後寫入與完整 CLI 參數。最後場景確認損壞的個人 control-return 不會退回預設，也不會回覆已啟用。未測量多模型、多次取樣的遵守率。

## 實作判定與限制

- 寫入採 POSIX 排他鎖與個別檔案的原子替換，持續保留鎖檔 inode，避免兩個程序持有不同鎖。已在本機 macOS 測試；Linux／WSL 未實測，原生 Windows 寫入尚不支援。
- 新的 probe 版本為 `0.0.4`，因 hooks 行為與包內 runtime 已變更。保留的 `0.0.2`／`0.0.3` 原生 CLI 證據不代表新版已通過原生驗收。
- NOT VERIFIED：新版兩個 CLI 的原生安裝與 hooks 信任、Task 8 更新／遷移流程、程序在多檔替換途中異常終止的整體恢復。每個檔案原子替換不等於跨檔案交易。
- runtime 已執行 fallback 憑證樣式掃描，未命中常見樣式；這不等於完整專用 secret scanner。
- 本輪未修改全域 hooks、個人正式設定、`main` 的 `GEMINI.md`，也未提交、推送、同步或發布。

下一項工作為 Task 4：讓正式 MCP server 與 logger 使用 Task 2 的同一份資料設定。
