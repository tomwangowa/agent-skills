# Task 5：七包來源與資源清單

日期：2026-10-14。分支 `feat/skill-plugins`，基準 `69dfe5d`。尚未提交或部署。

`plugin-packages.json` 明確列出核准的七包與 38 個來源 skills，各新包版本為 0.1.0。平台選擇只排除不適用的 reviewer 與 Codex 的 Claude-only workflow designer，來源成員與 catalog 生命週期不變。依賴分為必要、條件及可選；目前完整流程的 `tested_versions` 保持空清單，不把舊 probe 看到 Superpowers 7.0.0 當成所有新流程的相容證據。

資源只從明確的檔案白名單收集，不將目錄遞迴結果直接當發佈內容。缺檔、私人 config、資料目錄、開發測試、repo 外路徑及 symlink 都拒絕。退役 reviewer 不能成為成員或依賴；說明退役的文字保留。MCP 的 source 與 lockfile 是產生器輸入，Task 6 才產生已編譯 server 與 production 依賴。

## 驗證

- 新增九項 package 行為測試：精確成員、生命週期、平台差異、依賴 schema、錯誤型別、實際資源、路徑拒絕及 plugin sync 的來源限制。已觀察 RED，再通過完整 Python **119／119**。
- 原有 `skill-sync/scripts/test-sync.sh` 通過；新增真實 shell fixture 驗證 plugin cache 拒絕作 source，明確 standalone source 的 dry-run 不建立 target、不修改任何 fixture 檔案。
- catalog `--check`、shell syntax、`git diff --check` 均退出 0。
- 唯讀 reference-application baseline 由 `69dfe5d` 取得，舊指示沒有 plugin 定位／缺技能狀態；新版場景確認 installed／available to install／unavailable、manual checkpoint、明確 sync source、外部 audit output 及實際 MCP ID。場景抓到 deferred discovery 殘留 legacy prefix filter，已修正並重新核對。

來源適配集中在 router、sync、auditor、日誌分析與 handoff；README 的舊安裝定位及個人範例路徑另作對應修正。同步仍限 standalone skills；安裝、更新與移除 plugin 由 host 管理。

## Audit 處置

| Skill | 分數 | Critical／Important | 處置 |
| --- | ---: | --- | --- |
| skill-router | 100 | 0／0 | 1 suggestion 保留 |
| skill-sync | 84 | 0／0 | 3 suggestions 保留 |
| skill-auditor | 92 | 0／0 | 1 suggestion 保留 |
| work-log-analyzer | 86 | 0／0 | 1 suggestion 保留 |
| handoff | 100 | 0／0 | 無 |
| code-review-claude | 89 | 0／1 | 舊 trigger 的 fast／quick 關鍵字誤報；本項只改 README 安裝說明，保留 trigger 與現有明確的時間說明 |

原始 reports 為同目錄的 `*-task-5-audit.md`。Suggestions 不阻擋來源適配；分數不代表完整 CLI 發佈驗收。

NOT VERIFIED：Task 6 的完整產物與 marketplaces、Task 7 的各流程依賴及模型路由、Task 8 的更新／遷移。Production 依賴的既有 15 項漏洞仍是發布阻擋。唯讀場景沒有執行 sync 或讀取正式活動資料。
