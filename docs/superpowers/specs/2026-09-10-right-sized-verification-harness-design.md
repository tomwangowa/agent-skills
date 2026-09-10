---
title: Right-sized commit verification harness
date: 2026-09-10
status: approved
---

# Right-sized commit verification harness

## 1. Goal

讓 commit 前的驗證強度跟變更風險走，避免文件 typo 也跑完整 code review 與 completion 驗收，同時保留高風險修改需要的證據。

本設計只處理 commit boundary，不改開發中的 debug、測試或任務編排流程。

## 2. Confirmed decisions

- 使用三層風險模型：L0、L1、L2。
- agent 根據任務描述與 diff 自動判斷；無法判斷時升一級，最高到 L2。
- L0／L1／L2 的政策由既有 gate 管理，不新增 `right-sized-harness` skill、CLI 或 hook。
- 預設不雙跑 Codex 與 Claude reviewer。
- Codex 使用 `code-review-codex`。
- Claude Code 與 OMP 使用 `code-review-claude`。
- L1 不額外展開完整 `completion-gate`；但既有 commit boundary 的自動 gate 仍保留。

## 3. Risk tiers and minimum evidence

### L0 — low risk

適用於只改文件文字、格式、註解或其他非執行資產的變更。

最低驗證：

- 確認 diff 只包含預期檔案與內容。
- 執行適用的格式、Markdown render、拼字或連結檢查。
- 不呼叫 native reviewer。
- 不展開完整 `completion-gate` 驗收。

### L1 — normal risk

適用於會改變程式行為、API 回應、UI 行為、設定預設值或建置結果，但沒有命中 L2 硬升級條件的變更。

最低驗證：

- 執行受影響範圍的測試、lint 或型別檢查。
- 呼叫一次目前 runtime 的 native reviewer。
- 確認 diff 範圍。
- 不額外展開完整 `completion-gate`。

若找不到相關測試，或 reviewer 留下未解決疑慮，升級到 L2。

### L2 — high risk

命中下列任一條件時直接進入 L2：

- 身分驗證、session 或權限。
- 可能造成資料遺失或損壞。
- 生產環境設定、部署或 rollback。
- 已發生的生產事故或重大回歸。

最低驗證：

- 執行針對性測試。
- 執行相關回歸測試；涉及 auth、session、權限或資料流程時，再加對應 smoke test。
- 呼叫一次目前 runtime 的 native reviewer。
- 展開完整 `completion-gate` 驗收。

## 4. Runtime policy and ownership

`completion-gate/SKILL.md` 是風險矩陣、升級規則與最低證據的唯一政策來源。

runtime policy 檔只保留各自的 commit 觸發規則與 reviewer mapping：

- `global/AGENTS.md`
- `~/.codex/AGENTS.md`
- `global/CLAUDE.md`
- `~/.claude/CLAUDE.md`

`skill-router/skill-registry.yaml` 只負責 discovery 與 workflow 描述，不重複整張矩陣。`skills-catalog.json` 不新增風險邏輯。

目前 `global/AGENTS.md` 與 `~/.codex/AGENTS.md` 相同；`global/CLAUDE.md` 與 `~/.claude/CLAUDE.md` 有兩條差異，更新時必須保留實際檔案中的額外規則。

## 5. Commit-boundary flow

```text
commit boundary
  -> read task context and diff
  -> check L2 hard escalators
  -> otherwise classify L0 or L1
  -> run minimum evidence for the tier
  -> escalate when evidence is missing or review uncertainty remains
  -> report VERIFIED, NOT VERIFIED, tier, and escalation reason
```

風險判斷以影響範圍、可逆性與安全／資料邊界為主，不以 diff 行數、檔案副檔名或資料夾名稱單獨決定。

## 6. Reporting contract

每次 commit-boundary 驗證都應回報：

```text
RISK: L1
REASON: changed executable behavior

CHECKS:
- targeted tests: passed
- native review: code-review-codex

ESCALATED: no

NOT VERIFIED:
- concurrency behavior
- production deployment behavior
```

L0 不需要列 native reviewer；L2 必須列出 `completion-gate`。

## 7. Failure and exception handling

- 必要檢查失敗：停止 commit 流程並回報失敗原因。
- 找不到相關測試：L1 升 L2。
- L2 仍沒有可執行的驗證方式：保留 `NOT VERIFIED`，不得宣稱可以安全提交。
- native reviewer 無法執行：不自動改跑另一個 runtime 的 reviewer，回報 blocker。
- 風險無法判斷：升一級，最高到 L2。
- 非必要檢查不可用：記錄為 `NOT VERIFIED`，不阻擋低風險修改。

## 8. Policy validation cases

第一版只需要用固定案例 dry run 驗證政策：

| Case | Expected tier | Expected evidence |
|---|---:|---|
| 文件 typo | L0 | diff + applicable deterministic checks |
| Markdown 結構或連結修改 | L0 | render/link checks |
| 一般 bug fix | L1 | targeted checks + native review |
| API 行為修改 | L1 | targeted checks + native review |
| login／session／權限修改 | L2 | targeted + regression/smoke + native review + completion gate |
| 可能刪除資料的 migration | L2 | targeted + regression/smoke + native review + completion gate |
| L1 找不到相關測試 | L2 | escalated L2 evidence |
| reviewer 留下未解決疑慮 | L2 | escalated L2 evidence |
| 無法判斷風險 | next higher tier | escalation reason |

另外確認：

- L0 不呼叫 native reviewer。
- L1 不額外展開完整 `completion-gate`。
- 四份 runtime policy 檔的對應規則一致。
- `~/.claude/CLAUDE.md` 的兩條額外規則沒有被覆蓋。

## 9. Out of scope

- 開發過程中的即時測試或 debug 路由。
- 依 diff 行數、歷史資料或模型成本自動計分。
- 新增 `right-sized-harness` skill。
- 新增 pre-commit hook、CLI 或外部服務。
- 自動平行執行 Codex 與 Claude reviewer。
- 讓使用者任意配置風險規則。
- 修改 `completion-gate` 的全域觸發時機；只調整各風險層級的驗證深度。

## 10. Planned change surface

實作階段預計只會碰到：

- `completion-gate/SKILL.md`
- `global/AGENTS.md`
- `~/.codex/AGENTS.md`
- `global/CLAUDE.md`
- `~/.claude/CLAUDE.md`

除非驗證時發現 discovery 描述需要同步，否則不修改 `skill-router/skill-registry.yaml` 或 `skills-catalog.json`。
