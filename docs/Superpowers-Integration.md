# Superpowers Plugin × 個人 Skills 整合對照

> **Document Status (2026-06-19):** 記錄 `superpowers` plugin 如何與本 repo 的自製 skills 整合運作。
> **權威來源仍是 `global/CLAUDE.md` 與本 repo 的 `CLAUDE.md`**；本文是它們的「整合視圖」快照，若兩者衝突以 CLAUDE.md 為準。
> 對照時的 plugin 版本：`superpowers@superpowers-dev` **v5.0.7**（commit `c4bbe65`）。

## 一句話總結

> superpowers 用一個 **SessionStart hook** 把 `using-superpowers` 注入每個 session 來「啟動」自己；其餘 13 個 skill 平時靠 `superpowers:` 命名空間按需調用。**真正的整合控制點在 CLAUDE.md**，它建立了一層 **user-skill-first 覆蓋**：有自製版的（brainstorming、completion-gate、code-review）一律走自製版，沒有的（TDD、debugging、plans 系列…）才落到 superpowers 版。

---

## 1. 安裝層

| 項目 | 值 |
|------|-----|
| Plugin | `superpowers@superpowers-dev` |
| 來源 | GitHub `obra/superpowers`（marketplace `superpowers-dev`） |
| 版本 | `5.0.7` |
| 安裝路徑 | `~/.claude/plugins/cache/superpowers-dev/superpowers/5.0.7/` |
| Scope | user |
| 啟用方式 | `~/.claude/settings.json` → `enabledPlugins["superpowers@superpowers-dev"] = true` |

**提供的內容**

- **Skills（14）**：`using-superpowers`、`brainstorming`、`test-driven-development`、`systematic-debugging`、`writing-plans`、`executing-plans`、`subagent-driven-development`、`dispatching-parallel-agents`、`using-git-worktrees`、`finishing-a-development-branch`、`requesting-code-review`、`receiving-code-review`、`verification-before-completion`、`writing-skills`
- **Commands（3）**：`/superpowers:brainstorm`、`/superpowers:write-plan`、`/superpowers:execute-plan`（皆已 deprecated，指向對應 skill）
- **Agent（1）**：`superpowers:code-reviewer`
- **Hook（1）**：SessionStart

---

## 2. 整合 / 啟動機制

`hooks/hooks.json` 註冊：

```
SessionStart (matcher: startup|clear|compact) → run-hook.cmd session-start
```

每次開新 session / `clear` / `compact` 時，這個 hook 會把 **`using-superpowers` skill 的完整內容注入 context 最前面**（即對話開頭的 `<EXTREMELY_IMPORTANT> … You have superpowers …` 區塊）。它強制「**回應前先檢查有沒有適用的 skill**」這條規則。

除了 `using-superpowers` 由 hook 自動注入，**其餘 superpowers skill 都不自動載入**，需要時透過 `Skill` tool 以 **`superpowers:skill-name`** 命名空間調用。

---

## 3. 優先序（來自 `using-superpowers` 本身）

1. **使用者明確指示（CLAUDE.md / 直接要求）** — 最高
2. **Superpowers skills** — 覆蓋預設行為
3. **預設 system prompt** — 最低

本 repo 的 CLAUDE.md 即是用第 1 層去**改寫** superpowers 的預設路由。

---

## 4. 覆蓋對照表 ⭐（核心）

原則：**凡是有自製版的一律走自製版；沒有對應版本的才用 superpowers 版。**

| 功能 | 實際路由到 | superpowers 對應 skill | 為什麼這樣路由 |
|------|-----------|------------------------|----------------|
| Brainstorming | **自製 `brainstorming`** | ❌ 不用 `superpowers:brainstorming` | 自製版是 superset：scope escalation（可 route 到 role-orchestrator）、pre-mortem、REQUIRED 串 tech-feasibility / critical-research、rationalization prevention 表、worked examples |
| 完成驗證 | **自製 `completion-gate`** | ❌ 不用 `superpowers:verification-before-completion` | 功能等價，已登記於 registry；保持 user-skill-first 一致性 |
| Code review | **依 runtime 的原生 reviewer**（Claude Code → `code-review-claude`；Codex → `code-review-codex`） | ❌ 不用 `superpowers:requesting-code-review`、`receiving-code-review`、`code-reviewer` agent | `code-review-gemini` 已退役；未來外部 reviewer 須明確選模型與確認 diff 範圍 |

> 為何不直接卸載 superpowers 的重複 skill？因為 `superpowers:brainstorming` 等**無法單獨卸載**（屬整包 plugin bundle）。對策是「不卸 plugin、用路由規則把 trigger 永遠導向自製版」。

---

## 5. 直接使用 superpowers 版的 skills

以下功能本 repo **沒有自製版**，故直接用 `superpowers:` 版（本 repo `CLAUDE.md` 已列為「由 superpowers plugin 提供」）：

| 觸發情境 | 調用 |
|----------|------|
| debug / error / 500 / stack trace / 「壞了」 | `superpowers:systematic-debugging`（global CLAUDE.md：MUST、BEFORE 任何分析） |
| 實作 feature / bugfix 前 | `superpowers:test-driven-development` |
| 有 spec 要寫多步驟計畫 | `superpowers:writing-plans` |
| 在另一 session 執行既有計畫 | `superpowers:executing-plans` |
| 當前 session 執行含獨立任務的計畫 | `superpowers:subagent-driven-development` |
| 2+ 個彼此獨立、無共享狀態的任務 | `superpowers:dispatching-parallel-agents` |
| 需與當前工作區隔離的 feature 工作 | `superpowers:using-git-worktrees` |
| 實作完成、要決定如何整合（merge/PR/cleanup） | `superpowers:finishing-a-development-branch` |
| 建立 / 編輯 / 驗證 skill | `superpowers:writing-skills` |

> 註：`requesting-code-review` / `receiving-code-review` 雖屬此類「無自製版」，但 generic code review 一律先走目前 runtime 的原生 reviewer（Claude Code → `code-review-claude`；Codex → `code-review-codex`），故實務上不主動調用。

---

## 6. 維護備註

- 本文是「整合視圖」，**不是**權威定義。新增 / 移除自製 skill 或調整路由時，先改 `global/CLAUDE.md` 與本 repo `CLAUDE.md`，再回頭更新此表。
- 升級 superpowers 版本後，若它新增了與自製 skill 重疊的功能，請在 §4 補一列覆蓋規則（預設立場：user-skill-first）。
- 驗證 plugin 現況：`cat ~/.claude/plugins/installed_plugins.json`、`ls ~/.claude/plugins/cache/superpowers-dev/superpowers/<version>/skills/`。
- `global/CLAUDE.md` 與 `global/AGENTS.md` 是**鏡像檔**：源頭分別是 `~/.claude/CLAUDE.md` 與 `~/.codex/AGENTS.md`。要改全域指示請先改源頭再重新鏡像，別只改 repo 內的鏡像（會漂移）。詳見 [`../global/README.md`](../global/README.md)。

---

## 🔗 Quick Links

- [Meta-Skills Design Pattern](./Meta-Skills-Pattern.md) — 多個相似 skill 的路由設計模式
- [docs/README](./README.md)
- [Back to Main README](../README.md)
