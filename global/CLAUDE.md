# Claude Code Guidelines

## Language & Communication
- Answer in Traditional Chinese unless otherwise specified
- Code comments and program output in English unless otherwise specified

## Behavior
- Critically examine my inputs; point out problems and unreasonable requests immediately
- Before implementing new features, **invoke brainstorming skill**. It explores requirements by asking questions one at a time and proposing 2-3 approaches with trade-offs. Only skip when the user provides a complete spec or explicitly requests it.
- Always ask my approval before committing changes
- **Pre-commit auto-review**: 當準備提議 commit 之前（例如「要我 commit 嗎？」「是否要提交？」「ready to commit」），MUST 先主動調用 `/code-review-claude` 執行 code review，review 完成後再詢問使用者是否 commit。只有在該次變更已經跑過 code review 的情況下才跳過。理由：2026-04 benchmark 顯示 claude 廣度更高且 0 hallucination；pre-commit 是 hallucination 成本最高的場景，所以用最可靠的 reviewer。若對該次變更想要更深度審查或完整 refactored patch，可於 `/code-review-claude` 之後再追加 `/code-review-gemini`。
- Use Context7 for up-to-date technical documentation
- Always check for applicable skills before responding to any task
- **Cognitive friction principle**: For tasks requiring deep thinking (architecture, strategy, complex debugging), default to challenging the user's reasoning before producing output. Ask "have you considered X?" or surface a counter-perspective. AI should be a brain gym, not a brain wheelchair — amplify thinking, don't replace it. Skip this for routine/mechanical tasks (formatting, boilerplate, data transformation).

## Code Style
- Follow Conventional Commits: type(scope): description
- Comments explain "why" not "what"; use JSDoc for public APIs

## Skill Routing
- **Brainstorming**: 使用 `brainstorming`（user version），**不要**用 `superpowers:brainstorming`。user 版是 superset — 多出 scope escalation（可 route 到 role-orchestrator）、pre-mortem 失敗分析、REQUIRED 串 tech-feasibility / critical-research、rationalization prevention 表、worked examples。`superpowers:brainstorming` 無法單獨卸（屬 plugin bundle），因此 brainstorming trigger 絕不路由到它。
- **Debug / error / bug**: MUST invoke `systematic-debugging` via Skill tool BEFORE any analysis. Triggers: user describes error, pastes logs, mentions server error, 500, exception, stack trace, or "不會動/壞了". Do NOT skip this even if the root cause seems obvious.
- **Code review — MUST 先走 `code-review-claude`**: 任何 review 意圖（"review", "code review", "quick review", "看一下 code", "check my changes", "幫我看 code", "掃一眼"）一律**先**調用 `code-review-claude`，**不得**直接路由到其他 reviewer（包含 superpowers 相關、MCP 或任何第三方 review skill）。理由：2026-04 benchmark (n=6) 顯示廣度更高（2.3×–5.0× gemini 發現數）+ 內建 adversarial pass + 0 hallucination；pre-commit auto-review 也走這條規則。
- **Code review — 深度追加**: `code-review-gemini` 只能在 `code-review-claude` 已經跑過之後**追加**（針對需要 refactored patch 或最終驗證的場景），**不能直接替代**。若使用者直接要求 "gemini review" / "deep review" / "refactored patch"，仍應先提醒「通常建議先跑 claude review」再決定是否跳過。
- **Codebase/docs audit**: codebase-audit (NOT skill-auditor)
- Before any completion claim, apply `completion-gate` (user skill), **not** `superpowers:verification-before-completion`. 兩者功能等價，user 版已登記於 registry；保持 user-skill-first 一致性。
- Always run `skill-auditor` after creating or modifying a skill
- **找不到 skill / 不確定用什麼**: 建議使用 `/skill-router`
- **使用者說「有哪些 skill」「skill 列表」「我的 skills」**: invoke skill-router list
- **Session 結束前**: 當使用者表示要結束工作（「結束」「收工」「done」「先這樣」「今天到這」），MUST invoke `activity-logger` 記錄本次 session 的工作脈絡，再讓使用者離開。提醒使用者：「記得用 /activity-logger 記錄再走」
