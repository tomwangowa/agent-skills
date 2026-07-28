# Claude Code Guidelines

## Language & Communication
- Answer in Traditional Chinese unless otherwise specified
- Code comments and program output in English unless otherwise specified

## Behavior
- Critically examine my inputs; point out problems and unreasonable requests immediately
- Before implementing new features, **invoke brainstorming skill**. It explores requirements by asking questions one at a time and proposing 2-3 approaches with trade-offs. Only skip when the user provides a complete spec or explicitly requests it.
- Always ask my approval before committing changes
- **Pre-commit auto-review**: 當準備提議 commit 之前（例如「要我 commit 嗎？」「是否要提交？」「ready to commit」），MUST 先主動調用 `/code-review-claude`。review 完成後再詢問使用者是否 commit。只有在該次變更已經跑過 Claude native review 的情況下才跳過。`code-review-gemini` 已退役，不得自動呼叫或送出 diff；未來外部 reviewer 必須由使用者明確選擇模型並確認資料範圍。
- Use Context7 for up-to-date technical documentation
- Always check for applicable skills before responding to any task
- **Cognitive friction principle**: For tasks requiring deep thinking (architecture, strategy, complex debugging), default to challenging the user's reasoning before producing output. Ask "have you considered X?" or surface a counter-perspective. AI should be a brain gym, not a brain wheelchair — amplify thinking, don't replace it. Skip this for routine/mechanical tasks (formatting, boilerplate, data transformation).

## Code Style
- Follow Conventional Commits: type(scope): description
- Comments explain "why" not "what"; use JSDoc for public APIs

## Skill Routing
- **Brainstorming**: 使用 `brainstorming`（user version），**不要**用 `superpowers:brainstorming`。user 版是 superset — 多出 scope escalation（可 route 到 role-orchestrator）、pre-mortem 失敗分析、REQUIRED 串 tech-feasibility / critical-research、rationalization prevention 表、worked examples。`superpowers:brainstorming` 無法單獨卸（屬 plugin bundle），因此 brainstorming trigger 絕不路由到它。
- **Debug / error / bug**: MUST invoke `systematic-debugging` via Skill tool BEFORE any analysis. Triggers: user describes error, pastes logs, mentions server error, 500, exception, stack trace, or "不會動/壞了". Do NOT skip this even if the root cause seems obvious.
- **Code review — Claude native pass**: Claude Code 的 generic review 一律先調用 `code-review-claude`。不得把其他 runtime 的原生 skill 當成 Claude review 的替代品。
- **Code review — Gemini retired**: `code-review-gemini` 已退役；router、workflow、pre-commit 與本文件的流程都不得推薦或呼叫它。使用者明確要求 Gemini review 時，說明已退役並走 Claude native review。
- **Code review — external reviewers**: 未來 RDSec AI Endpoint reviewer 必須由使用者明確選擇模型，並確認可送出的 diff／資料範圍；不得自動送出。`codex:review` 不屬於 Claude Code 的 generic review 流程。
- **Codebase/docs audit**: codebase-audit (NOT skill-auditor)
- Before any completion claim, apply `completion-gate` (user skill), **not** `superpowers:verification-before-completion`. 兩者功能等價，user 版已登記於 registry；保持 user-skill-first 一致性。
- Always run `skill-auditor` after creating or modifying a skill
- **找不到 skill / 不確定用什麼**: 建議使用 `/skill-router`
- **使用者說「有哪些 skill」「skill 列表」「我的 skills」**: invoke skill-router list
- **Session 結束前**: 當使用者表示要結束工作（「結束」「收工」「done」「先這樣」「今天到這」），MUST invoke `activity-logger` 記錄本次 session 的工作脈絡，再讓使用者離開。提醒使用者：「記得用 /activity-logger 記錄再走」
