# Skill Router Implementation Plan

> **For Claude:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task.

**Goal:** Create a unified skill discovery and routing entry point (`/skill-router`) with three modes: smart routing, category browse, and workflow browse.

**Architecture:** A single skill (`skill-router/SKILL.md`) reads a registry file (`skill-router/skill-registry.yaml`) containing all 44 skills organized into 10 categories with triggers and 6 preset workflow chains. No scripts — Claude's semantic matching does the routing.

**Tech Stack:** YAML (registry), Markdown (SKILL.md), Claude Code Skill system

---

### Task 1: Create skill-registry.yaml

**Files:**
- Create: `skill-router/skill-registry.yaml`

**Step 1: Create the registry file**

Write the full `skill-registry.yaml` with all 10 categories, 44 skills (each with `id` + `triggers` array), and 6 workflows. 

Categories and their skills:

```yaml
# Categories:
#   research (9): critical-research, tech-feasibility, tech-research-pipeline,
#                 research-cross-validator, assumption-extractor, micro-poc-validator,
#                 research-synthesis, codebase-audit, narrative-auditor
#   code-review (3): code-review-gemini, code-review-claude, pr-review-assistant
#   dev-process (7): brainstorming, sp-test-driven-development, sp-systematic-debugging,
#                    sp-writing-plans, sp-executing-plans, completion-gate,
#                    sp-using-git-worktrees
#   roles (3): role-orchestrator, role-pm, role-rd
#   delegation (2): sp-dispatching-parallel-agents, sp-subagent-driven-development
#   code-history (1): code-story-teller
#   presentation (3): presentation-planner, interactive-presentation-generator, report-generator
#   knowledge (5): activity-logger, work-log-analyzer, qa-to-notes, deep-reading, newsletter-digest
#   content (2): arxiv-digest, ai-weekly-insight
#   meta (2): skill-auditor, skillshare
```

Triggers should include both English keywords and Traditional Chinese equivalents that the user naturally types. Example:
```yaml
- id: tech-feasibility
  triggers: ["可行性", "能不能用", "should I use", "evaluate tech", "is X feasible", "技術評估"]
```

Workflows (from design doc):
```yaml
workflows:
  tech-evaluation:
    label: "技術評估（快速）"
    when: "評估一個技術方案是否可行，需要驗證假設"
    steps: [tech-feasibility, assumption-extractor, micro-poc-validator]
  full-research:
    label: "完整研究流程（8 階段）"
    when: "重大技術決策，需要嚴謹求證與多方交叉驗證"
    steps: [tech-research-pipeline]
  feature-dev:
    label: "功能開發全流程"
    when: "從需求探索到交付的完整開發週期"
    steps: [brainstorming, sp-writing-plans, sp-executing-plans, completion-gate, code-review-gemini]
  presentation:
    label: "簡報製作"
    when: "準備演講、分享、或任何簡報"
    steps: [presentation-planner, interactive-presentation-generator]
  post-implementation:
    label: "實作完成後驗收"
    when: "代碼寫完，準備 review 和合併"
    steps: [completion-gate, code-review-gemini, sp-finishing-a-development-branch]
  role-pipeline:
    label: "PM→RD 角色協作"
    when: "需要完整的需求分析到技術設計流程"
    steps: [role-orchestrator]
```

**Step 2: Verify YAML syntax**

Run: `python3 -c "import yaml; yaml.safe_load(open('skill-router/skill-registry.yaml')); print('OK')"`
Expected: `OK`

**Step 3: Commit**

```bash
git add skill-router/skill-registry.yaml
git commit -m "feat(skill-router): add skill registry with 44 skills and 6 workflows"
```

---

### Task 2: Create SKILL.md

**Files:**
- Create: `skill-router/SKILL.md`

**Step 1: Write the SKILL.md**

The SKILL.md needs:

1. **Frontmatter**: name "Skill Router", description covering all three modes and key trigger phrases (including Chinese: "有哪些 skill", "skill 列表", "我想做X但不知道用什麼")

2. **Instructions** for three modes, determined by ARGUMENTS:

   **Mode detection logic:**
   - Args = "list" → Mode 2 (category browse)
   - Args = "workflows" → Mode 2 (workflow browse)  
   - Args = anything else (or empty) → Mode 1 (smart routing)

   **Mode 1 — Smart Routing:**
   1. Read `skill-registry.yaml` from `~/.claude/skills/skill-router/skill-registry.yaml`
   2. Analyze the user's ARGUMENTS against workflow `when` fields first (prefer workflow match)
   3. If no workflow match, match against individual skill triggers
   4. Present recommendation in this format:
      ```
      🔍 建議路徑：
      
      1. **skill-name** — one-line what it does for this case
      2. **skill-name** — one-line what it does for this case
      
      > 💡 這對應預設 workflow「workflow-label」
      
      要啟動嗎？或者你想調整？
      ```
   5. Wait for user confirmation before invoking any skill
   6. On confirmation, invoke skills sequentially via Skill tool

   **Mode 2 — Category Browse (`list`):**
   1. Read `skill-registry.yaml`
   2. For each category, print:
      ```
      ## category-label（N 個）
      - **skill-id** — first trigger as short description
      ```
   3. After listing, ask: "想深入了解哪個分類，或直接告訴我你的需求？"

   **Mode 3 — Workflow Browse (`workflows`):**
   1. Read `skill-registry.yaml`
   2. For each workflow, print:
      ```
      ### workflow-label
      **適用情境：** when field
      **流程：** step1 → step2 → step3
      ```
   3. After listing, ask: "想啟動哪個 workflow？"

3. **Rules:**
   - NEVER auto-invoke without user confirmation
   - If no good match found, say so honestly and suggest `/skill-router list`
   - Keep output concise — one-line descriptions, not paragraphs

**Step 2: Commit**

```bash
git add skill-router/SKILL.md
git commit -m "feat(skill-router): add SKILL.md with 3 interaction modes"
```

---

### Task 3: Update CLAUDE.md routing rules

**Files:**
- Modify: `~/.claude/CLAUDE.md:19-25` (the `## Skill Routing` section)

**Step 1: Add 2 lines to Skill Routing section**

Append these 2 lines after the existing routing rules (after line 25):

```markdown
- **找不到 skill / 不確定用什麼**: 建議使用 `/skill-router`
- **使用者說「有哪些 skill」「skill 列表」「我的 skills」**: invoke skill-router list
```

**Step 2: Verify the edit**

Read back `~/.claude/CLAUDE.md` and confirm:
- The 2 new lines are at the end of `## Skill Routing`
- Existing 6 rules are untouched

**Step 3: Commit**

```bash
git add ~/.claude/CLAUDE.md
git commit -m "feat(skill-router): add routing rules to CLAUDE.md"
```

---

### Task 4: Update project CLAUDE.md skill listing

**Files:**
- Modify: `~/.claude/skills/CLAUDE.md` (the `## Available Skills` section)

**Step 1: Add skill-router to the Meta section**

In the `### Meta` subsection, add:
```markdown
- **skill-router** — Unified skill discovery and routing: smart match, category browse, workflow browse
```

**Step 2: Commit**

```bash
git add ~/.claude/skills/CLAUDE.md
git commit -m "docs: add skill-router to available skills listing"
```

---

### Task 5: Run skill-auditor

**Step 1: Invoke skill-auditor**

Run: `/skill-auditor skill-router`

**Step 2: Fix any issues flagged by the auditor**

Address each finding. Common issues to watch for:
- Description too long/short in frontmatter
- Missing trigger phrases
- Instructions unclear

**Step 3: Commit fixes if any**

```bash
git add skill-router/
git commit -m "fix(skill-router): address skill-auditor findings"
```

---

### Task 6: Smoke test

**Step 1: Test Mode 1 (smart routing)**

Run: `/skill-router 我想評估用 Redis 做 session store 可不可行`
Expected: Should recommend tech-evaluation workflow (tech-feasibility → assumption-extractor → micro-poc-validator)

**Step 2: Test Mode 2 (list)**

Run: `/skill-router list`
Expected: 10 categories with all skills listed, one-line each

**Step 3: Test Mode 3 (workflows)**

Run: `/skill-router workflows`
Expected: 6 workflows with scenario + steps

**Step 4: Test no-match case**

Run: `/skill-router 幫我訂午餐`
Expected: Honestly says no matching skill, suggests `/skill-router list`
