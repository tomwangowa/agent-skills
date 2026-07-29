---
name: "skill-router"
description: "Use when unsure which skill to use, want to browse available skills, or need workflow recommendations. Unified skill discovery and routing with disambiguation for ambiguous queries. Triggers: '有哪些 skill', 'skill 列表', '我的 skills', '不知道用什麼', 'which skill', 'find skill', 'skill-router list', 'skill-router workflows'"
disable-model-invocation: true
---

# Skill Router

A unified entry point for discovering, browsing, and invoking skills. Reads from a central registry to recommend skills and workflows based on user intent.

## Mode Detection

Determine the mode from ARGUMENTS:

- ARGUMENTS contains **"list"** → **Mode 2 (Category Browse)**
- ARGUMENTS contains **"workflows"** or **"workflow"** → **Mode 3 (Workflow Browse)**
- ARGUMENTS is **anything else or empty** → **Mode 1 (Smart Routing)**

---

## Mode 1 — Smart Routing (default)

Use this mode when the user describes a need, problem, or goal and wants a skill recommendation.

### Native review gate

Before matching workflows or registry triggers, handle every code-review intent
except an explicit GitHub PR review as follows:

1. Treat generic review, `deep review`, `thorough review`, `detailed review`,
   and `refactored patch` as requests for the current runtime's native review.
2. A request for Gemini review is a request for a retired skill. Say that
   `code-review-gemini` is deprecated and recommend the current runtime's
   native reviewer instead. Do not run Gemini or send a diff to an external
   endpoint.
3. If a request names the other runtime's native reviewer, explain the runtime
   boundary and route to the current runtime's native reviewer instead.
4. Select the native reviewer before any
   workflow match: Claude Code uses `code-review-claude`; Codex uses
   `code-review-codex`.
5. If the runtime is unknown, ask which runtime is active rather than guessing.
6. A future external reviewer is never automatic: the user must explicitly
   choose its model and approve the diff or data scope before anything leaves
   the local environment.

### Steps

1. Read the registry file at `~/.claude/skills/skill-router/skill-registry.yaml` and
   `~/.claude/skills/skills-catalog.json`. The catalog is authoritative for a local
   skill's `invocation_intent`; registry membership only makes it discoverable.
2. Take the user's ARGUMENTS as the search query.
3. **Prefer workflow matches first**: compare the query against each workflow's `when` field. If the query aligns with a workflow scenario, recommend that workflow.
4. **Fall back to individual skill matches**: if no workflow matches, compare the query against each skill's `triggers` list and `description`.
5. **Branch by match count**:
   - **Exactly 1 match** → go to step 6 (direct recommendation).
   - **2+ matches** → go to step 5a (disambiguation tree).
   - **0 matches** → go to step 5b (guided discovery tree).

### Step 5a — Disambiguation Tree (2+ matches)

When multiple skills match, do NOT list them all and let the user guess. Instead, ask **one** disambiguating question with structured select options (2-4 choices). Each option maps to one skill.

Use the disambiguation groups below. If the matched skills span multiple groups, ask the highest-priority group's question first.

**Disambiguation groups (ordered by priority):**

**驗證類**（critical-research, research-cross-validator, narrative-auditor, completion-gate, codebase-audit）
> **你要驗證的是什麼？**
> 1. 一篇外部文章或說法的真實性 → `narrative-auditor`
> 2. 技術方案的假設，需要多方交叉求證 → `research-cross-validator`
> 3. 自己剛做完的工作，確認結果正確 → `completion-gate`
> 4. 一個觀點有沒有反例，falsification-first → `critical-research`
> 5. 文件跟程式碼是否一致 → `codebase-audit`

**研究類**（tech-feasibility, tech-research-pipeline, critical-research, research-synthesis）
> **你的研究需求有多深？**
> 1. 快速判斷一個技術方案可不可行 → `tech-feasibility`
> 2. 需要嚴謹的多階段深度研究 → `tech-research-pipeline`
> 3. 想針對一個說法找反證 → `critical-research`
> 4. 已經做了多項研究，需要整合結論 → `research-synthesis`

**Review 類**（code-review-codex, code-review-claude, pr-review-assistant）
> **你要 review 什麼？**
> 1. 一般程式碼 review → 依目前 runtime：Claude Code 用 `code-review-claude`；Codex 用 `code-review-codex`
> 2. 審查一個 GitHub PR → `pr-review-assistant`

**設計類**（brainstorming, superpowers:writing-plans, role-pm, role-rd）
> **你在哪個階段？**
> 1. 還在想要做什麼，需要探索需求 → `brainstorming`
> 2. 已經知道要做什麼，需要拆解步驟 → `superpowers:writing-plans`
> 3. 需要完整的需求文件（PRD / user story） → `role-pm`
> 4. 需要技術設計文件（architecture / design doc） → `role-rd`

**平行執行類**（superpowers:dispatching-parallel-agents, superpowers:subagent-driven-development）
> **你的任務是什麼狀態？**
> 1. 有多個獨立任務想同時跑 → `superpowers:dispatching-parallel-agents`
> 2. 有一份實作計畫，裡面的子任務可以分派 → `superpowers:subagent-driven-development`

**簡報類**（presentation-planner, interactive-presentation-generator）
> **你到了哪一步？**
> 1. 還沒有大綱，需要先規劃內容策略 → `presentation-planner`
> 2. 已經有大綱或內容，要產生投影片 → `interactive-presentation-generator`

After the user selects an option, present the recommendation (step 6) for the selected skill.

If the matched skills don't fall into any predefined group, fall back to listing them with one-line descriptions and asking the user to pick.

### Step 5b — Guided Discovery Tree (0 matches)

When nothing matches, do NOT just say "找不到". Instead, ask one question to narrow down:

> **你想做的事比較接近哪一類？**
> 1. 寫程式 / 開發功能 / debug → 開發流程類
> 2. 審查 / review 代碼 → 程式碼審查類
> 3. 研究 / 調查 / 求證 → 研究與驗證類
> 4. 整理資料 / 筆記 / 報告 → 知識管理類
> 5. 做簡報 / 演講準備 → 簡報與溝通類
> 6. 以上都不是 → `/skill-router list` 瀏覽全部

Based on the user's selection, list the skills in that category and ask which one fits.

### Step 6 — Present recommendation

6. For every local recommended skill, look up its `invocation_intent` in the
   catalog before presenting it. A registry match never overrides this value.
   An external namespaced skill has no local catalog row and keeps the normal
   confirmation flow.
7. For a `model` skill, present the recommendation in this format:

```
🔍 建議路徑：

1. **skill-name** — what it does for this specific need
2. **skill-name** — what it does for this specific need (if workflow matched)

> 這對應預設 workflow「workflow-label」（if a workflow matched）

要啟動嗎？或者想調整？
```

8. **WAIT for user confirmation** — do NOT auto-invoke any skill. For a model
   skill, confirmation permits invoking the first recommended skill. If it is
   part of a workflow, after that skill completes, prompt the user: "下一步是
   **next-skill-name**，要繼續嗎？"
9. For a `user` skill, present it as a manual checkpoint instead:

```
🔍 建議路徑：

1. **$skill-name** — what it does for this specific need

> manual checkpoint：這是 user-only skill。請直接輸入 `$skill-name` 或
> `/skill-name` 才會啟動。
```

   This requires an explicit user invocation. A reply such as「好」、「開始」or
   「繼續」does not invoke the skill; do not invoke it on that reply. Stop after
   presenting this checkpoint.
10. For a workflow, inspect every local step's catalog entry before presenting
    the chain. Render every `user` step as `$skill-name（manual checkpoint）`.
    Confirmation can start a leading `model` step only. When execution reaches a
    user step, stop and require that explicit user invocation; never convert a
    general workflow confirmation into permission for that step.

---

## Mode 2 — Category Browse (`list`)

Use this mode when the user wants to see all available skills organized by category.

### Steps

1. Read both sources:
   - `~/.claude/skills/skill-router/skill-registry.yaml` for skills that can be automatically routed and their router categories.
   - `~/.claude/skills/skills-catalog.json` for the complete local skill inventory and its lifecycle/surface policy.
2. List every non-deprecated local catalog entry. Keep the router categories as the main tables, including the active external skills already registered there. Then add a separate table for catalog entries with `routable: false` that are not already shown. These skills are available when named directly, but must not be recommended by smart routing.
3. For each table, print a compact table:

```
## [category label]（N 個）

| Skill | Invocation | 說明 |
|-------|------------|------|
| skill-id | model / user / external | one-line description derived from triggers and context |
```

Use the catalog `invocation_intent` for local skills. Mark namespaced skills as
`external`. For `user`, show the display name as `$skill-name` and add a short
note below the table: it is discoverable, but requires explicit user invocation.
Use the same table shape for the non-routable table.

Derive a non-routable skill's description from its `SKILL.md` frontmatter or opening context, not from the router registry that intentionally omits it.

Do not list lifecycle `deprecated` skills as available. If relevant, mention that a named deprecated skill is retained only as a migration reference.

4. End the listing with:

```
想深入了解哪個分類，或直接告訴我你的需求？
```

---

## Mode 3 — Workflow Browse (`workflows`)

Use this mode when the user wants to see predefined multi-skill workflows.

### Steps

1. Read the registry file at `~/.claude/skills/skill-router/skill-registry.yaml`
   and `~/.claude/skills/skills-catalog.json`.
2. For each workflow in the registry, look up every local step's
   `invocation_intent`. Print a user-only step as `$skill-name`（manual
   checkpoint；需 explicit user invocation）; retain a model step as its normal
   skill name. For example, `full-research` and `role-pipeline` stay visible as
   discovery entry points, but their user-only first steps remain manual.
3. For each workflow in the registry, print:

```
### [workflow label]
**適用情境：** the workflow's `when` field
**流程：** step1 → step2 → step3
```

4. End the listing with:

```
想啟動哪個 workflow？或描述你的需求讓我推薦。
```

---

## Rules

- **NEVER auto-invoke skills without explicit user confirmation.** Always present recommendations and wait.
- Do not recommend or invoke `code-review-gemini`; it is deprecated. For a
  future external reviewer, require an explicit model choice and approval of
  the diff or data scope first.
- If no match is found, say so honestly and suggest `/skill-router list` for browsing.
- Keep descriptions concise — one line per skill, not paragraphs.
- When presenting workflows, highlight the one most relevant to the query.
- If the user confirms a workflow, invoke only its first `model` skill. A
  `user` step is a manual checkpoint: show `$skill-name` and wait for that
  explicit user invocation. Do NOT invoke the entire chain at once, and do not
  treat a general confirmation as authorization for a user-only skill.
- All output should be in Traditional Chinese (per global CLAUDE.md guidelines), except skill names and technical terms which remain in English.

---

## Examples

### Example 1: Smart Routing
```
User: /skill-router 我想評估用 Redis 做 session store 可不可行
```
→ Recommends **tech-evaluation** workflow (tech-feasibility → assumption-extractor → micro-poc-validator), waits for confirmation.

### Example 2: Category Browse
```
User: /skill-router list
```
→ Lists all 10 categories with skills in compact tables, then asks what the user needs.

### Example 3: Workflow Browse
```
User: /skill-router workflows
```
→ Lists 6 preset workflows with scenarios and steps, then asks which to launch.

---

## Error Handling

- **Registry file not found**: If `skill-registry.yaml` cannot be read, inform the user: "Registry 檔案無法讀取，請確認 `~/.claude/skills/skill-router/skill-registry.yaml` 存在。" and fall back to listing skills from memory.
- **No match found**: Present the no-match message with alternative actions (list, workflows, rephrase).
- **Invalid ARGUMENTS**: If arguments cannot be parsed, default to Mode 1 (smart routing) with the raw text as query.
- **Skill invocation failure**: If a recommended skill fails to invoke, report the error and suggest trying the next skill in the chain or using `/skill-router list` to find alternatives.

---

## Security Considerations

- **Read-only operation**: This skill only reads the registry YAML and presents information. It does not modify files, execute scripts, or access external services.
- **No user input passed to shell**: All matching is done by Claude's semantic analysis, not by shell commands. No risk of command injection or directory traversal.
- **Input sanitization**: User query text is used only for semantic comparison against registry entries. No raw input is interpolated into file paths, URLs, or shell commands.
- **Registry file trust**: The registry is a local YAML file maintained by the user. No external data sources or network requests are used.
- **No sensitive data exposure**: The skill does not access, store, or transmit API keys, credentials, or personal information.
