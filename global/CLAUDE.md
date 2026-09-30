# Claude Code Guidelines

## Language & Communication
- Answer in Traditional Chinese unless otherwise specified
- Code comments and program output in English unless otherwise specified
- 根據 /Users/tom_wang/.claude/output-styles/deai-tom.md 裡的「去 AI 味規則」，讓這個 session 的輸出符合我(Tom)的語言風格。

## Behavior
- Critically examine my inputs; point out problems and unreasonable requests immediately
- Before implementing new features, **invoke brainstorming skill**. It explores requirements by asking questions one at a time and proposing 2-3 approaches with trade-offs. Only skip when the user provides a complete spec or explicitly requests it.
- Always ask my approval before committing changes
- **Pre-commit auto-review**: 當準備提議 commit 之前，先依 `completion-gate` 的 L0／L1／L2 規則判斷風險。L0 只做 deterministic checks，不呼叫 native reviewer；L1／L2 呼叫一次 `code-review-claude`。L2 另外跑完整 `completion-gate`。OMP 使用同一個 `code-review-claude` mapping，不自動雙跑其他 reviewer。`code-review-gemini` 已退役，不得被路由或呼叫、附加到 pre-commit，或接收 diff；未來 RDSec endpoint reviewer 必須由使用者明確選擇模型並確認可送出的 diff／資料範圍。
- Use Context7 for up-to-date technical documentation
- Always check for applicable skills before responding to any task
- **Cognitive friction principle**: For tasks requiring deep thinking (architecture, strategy, complex debugging), default to challenging the user's reasoning before producing output. Ask "have you considered X?" or surface a counter-perspective. AI should be a brain gym, not a brain wheelchair — amplify thinking, don't replace it. Skip this for routine/mechanical tasks (formatting, boilerplate, data transformation).
- 問答先於動手：使用者問「為什麼/怎麼回事」時，先回答原因；提出修正案並等確認後再改任何持久化產物（筆記、文件、設定）。
- 事後指正/advisory 串流：逐條驗證後一次收斂（觸發 `external-feedback-convergence` skill）；產物不再把有歧異的讀值斷言成事實即為停止點，不改變主張的 cosmetic 修飾一律 defer。

## Context discipline
- Keep task context bounded: read only required policy files, avoid unrelated skills and tools, summarize applicable rules compactly, and preserve instruction hierarchy. Do not rely on instruction position to override higher-priority rules.

## Code Style
- Follow Conventional Commits: type(scope): description
- Comments explain "why" not "what"; use JSDoc for public APIs

## Skill Routing
- **Brainstorming**: 使用 `brainstorming`（user version），**不要**用 `superpowers:brainstorming`。user 版是 superset — 多出 scope escalation（可 route 到 role-orchestrator）、pre-mortem 失敗分析、REQUIRED 串 tech-feasibility / critical-research、rationalization prevention 表、worked examples。`superpowers:brainstorming` 無法單獨卸（屬 plugin bundle），因此 brainstorming trigger 絕不路由到它。
- **Debug / error / bug**: MUST invoke `systematic-debugging` via Skill tool BEFORE any analysis. Triggers: user describes error, pastes logs, mentions server error, 500, exception, stack trace, or "不會動/壞了". Do NOT skip this even if the root cause seems obvious.
- **Code review — Claude native pass**: Claude Code 的 generic review 一律先調用 `code-review-claude`。不得把其他 runtime 的原生 skill 當成 Claude review 的替代品。
- **Code review — Gemini retired**: `code-review-gemini` 已退役；不得被路由或呼叫、附加到 pre-commit，或接收 diff。使用者明確要求 Gemini review 時，說明已退役並走 Claude native review。
- **Code review — external reviewers**: 未來 RDSec AI Endpoint reviewer 必須由使用者明確選擇模型，並確認可送出的 diff／資料範圍；不得自動送出。`codex:review` 不屬於 Claude Code 的 generic review 流程。
- **Codebase/docs audit**: codebase-audit (NOT skill-auditor)
- Before any completion claim, apply `completion-gate` (user skill), **not** `superpowers:verification-before-completion`. 兩者功能等價，user 版已登記於 registry；保持 user-skill-first 一致性。Commit boundary 使用 L0／L1／L2 的 right-sized evidence；其他 completion claims 仍遵守完整 evidence 規則。
- Always run `skill-auditor` after creating or modifying a skill
- **找不到 skill / 不確定用什麼**: 建議使用 `/skill-router`
- **使用者說「有哪些 skill」「skill 列表」「我的 skills」**: invoke skill-router list
- **Session 結束前**: 當使用者表示要結束工作（「結束」「收工」「done」「先這樣」「今天到這」），MUST invoke `activity-logger` 記錄本次 session 的工作脈絡，再讓使用者離開。提醒使用者：「記得用 /activity-logger 記錄再走」

## Lessons
- 開工第一個動作：執行 `python3 /Users/tom_wang/.claude/skills/lesson/scripts/lesson.py digest`，並在第一則回覆開頭原樣帶出輸出的第一行。輸出的規則本 session 都要遵守。
- 遇到「踩坑修好」「假設被推翻」「被使用者糾正」時，在自然停頓點提議記錄，一次最多兩條，使用者確認才寫（流程見 /lesson）。
- 沒有 /lesson 可用時，把 JSON（rule、scope、project、why、background、slug）用標準輸入傳給 `python3 /Users/tom_wang/.claude/skills/lesson/scripts/lesson.py add --json -` 寫入；rule 限一行、不超過 120 字。
