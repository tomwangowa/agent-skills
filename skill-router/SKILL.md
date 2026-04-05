---
name: "Skill Router"
description: "Unified skill discovery and routing. Use when unsure which skill to use, want to browse available skills, or need workflow recommendations. Triggers: '有哪些 skill', 'skill 列表', '我的 skills', '不知道用什麼', 'which skill', 'find skill', 'skill-router list', 'skill-router workflows'"
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

### Steps

1. Read the registry file at `~/.claude/skills/skill-router/skill-registry.yaml`.
2. Take the user's ARGUMENTS as the search query.
3. **Prefer workflow matches first**: compare the query against each workflow's `when` field. If the query aligns with a workflow scenario, recommend that workflow.
4. **Fall back to individual skill matches**: if no workflow matches, compare the query against each skill's `triggers` list and `description`.
5. Present recommendations in this format:

```
🔍 建議路徑：

1. **skill-name** — what it does for this specific need
2. **skill-name** — what it does for this specific need

> 這對應預設 workflow「workflow-label」（if a workflow matched）

要啟動嗎？或者想調整？
```

6. **WAIT for user confirmation** — do NOT auto-invoke any skill.
7. On confirmation, invoke the first recommended skill via the Skill tool. If it is part of a workflow, after that skill completes, prompt the user: "下一步是 **next-skill-name**，要繼續嗎？"

### When nothing matches

If no skill or workflow is a good fit, respond honestly:

```
找不到完全匹配的 skill。你可以：
- `/skill-router list` 瀏覽所有分類
- `/skill-router workflows` 看預設工作流程
- 或換個方式描述你的需求
```

---

## Mode 2 — Category Browse (`list`)

Use this mode when the user wants to see all available skills organized by category.

### Steps

1. Read the registry file at `~/.claude/skills/skill-router/skill-registry.yaml`.
2. For each category in the registry, print a compact table:

```
## [category label]（N 個）

| Skill | 說明 |
|-------|------|
| skill-id | one-line description derived from triggers and context |
```

3. End the listing with:

```
想深入了解哪個分類，或直接告訴我你的需求？
```

---

## Mode 3 — Workflow Browse (`workflows`)

Use this mode when the user wants to see predefined multi-skill workflows.

### Steps

1. Read the registry file at `~/.claude/skills/skill-router/skill-registry.yaml`.
2. For each workflow in the registry, print:

```
### [workflow label]
**適用情境：** the workflow's `when` field
**流程：** step1 → step2 → step3
```

3. End the listing with:

```
想啟動哪個 workflow？或描述你的需求讓我推薦。
```

---

## Rules

- **NEVER auto-invoke skills without explicit user confirmation.** Always present recommendations and wait.
- If no match is found, say so honestly and suggest `/skill-router list` for browsing.
- Keep descriptions concise — one line per skill, not paragraphs.
- When presenting workflows, highlight the one most relevant to the query.
- If the user confirms a workflow, invoke the **first** skill in the chain via the Skill tool. After it completes, prompt whether to continue to the next step. Do NOT invoke the entire chain at once.
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
- **No user input passed to shell**: All matching is done by Claude's semantic analysis, not by shell commands. No risk of injection.
- **Registry file trust**: The registry is a local YAML file maintained by the user. No external data sources are used.
