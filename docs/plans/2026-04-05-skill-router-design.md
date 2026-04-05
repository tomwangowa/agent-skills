# Skill Router Design

**Date**: 2026-04-05
**Status**: Approved

## Problem

44 custom skills with only 4 explicit routing rules in CLAUDE.md. Users experience:
1. **Inaccurate auto-routing** — Claude misses or picks wrong skills
2. **Discovery gap** — can't remember what skills are available
3. **Workflow opacity** — multi-step chains exist but aren't discoverable

## Solution

A new `skill-router` skill providing a unified entry point with three modes:

### Mode 1: Smart Routing (default)
```
/skill-router <natural language description>
```
Analyzes prompt against registry, recommends skill or workflow chain, waits for user confirmation before executing.

### Mode 2: Category Browse
```
/skill-router list
```
Lists all skills grouped by category with one-line descriptions.

### Mode 3: Workflow Browse
```
/skill-router workflows
```
Lists preset workflow chains with usage scenarios.

## File Structure

```
skill-router/
├── SKILL.md              # Skill definition + instructions for 3 modes
└── skill-registry.yaml   # Categories, triggers, workflows
```

## Registry Structure

```yaml
categories:
  <category-id>:
    label: "Display Name"
    skills:
      - id: <skill-name>
        triggers: ["keyword1", "keyword2", ...]
      # ...

workflows:
  <workflow-id>:
    label: "Display Name"
    when: "Usage scenario description"
    steps: [skill-a, skill-b, skill-c]
```

### Categories (10)
1. **research** — 研究與驗證 (9 skills)
2. **code-review** — 程式碼審查 (3 skills)
3. **dev-process** — 開發流程 (7 skills)
4. **roles** — 角色協作 (3 skills)
5. **delegation** — 平行執行 (2 skills)
6. **code-history** — 程式碼歷史 (1 skill)
7. **presentation** — 簡報與溝通 (3 skills)
8. **knowledge** — 知識管理 (5 skills)
9. **content** — 內容策展 (2 skills)
10. **meta** — 工具與維護 (2 skills)

### Preset Workflows (6)
1. **tech-evaluation** — quick feasibility: tech-feasibility → assumption-extractor → micro-poc-validator
2. **full-research** — rigorous 8-phase: tech-research-pipeline
3. **feature-dev** — full cycle: brainstorming → sp-writing-plans → sp-executing-plans → verification-before-completion → code-review-gemini
4. **presentation** — slides: presentation-planner → interactive-presentation-generator
5. **post-implementation** — merge prep: verification-before-completion → code-review-gemini → sp-finishing-a-development-branch
6. **role-pipeline** — PM→RD: role-orchestrator (dispatches role-pm + role-rd)

## Routing Logic

Inside SKILL.md instructions (no scripts):
1. Read `skill-registry.yaml`
2. Match user prompt against triggers + skill descriptions
3. Prefer workflow match over individual skill match
4. Present recommendation with rationale → wait for confirmation → invoke sequentially

## CLAUDE.md Changes

Add 2 lines to existing `## Skill Routing` section:
```markdown
- **找不到 skill / 不確定用什麼**: 建議使用 `/skill-router`
- **使用者說「有哪些 skill」「skill 列表」**: invoke skill-router list
```

## Relationship with sp-using-superpowers

- `sp-using-superpowers` remains as the baseline behavioral rule (auto-trigger on 1% match)
- `skill-router` is the **user-initiated entry point** for fuzzy/uncertain cases
- No conflict: clear intent → superpowers auto-routes; unclear intent → `/skill-router`

## Scope

### In Scope
- 3 interaction modes (smart route / list / workflows)
- skill-registry.yaml covering all 44 skills
- 6 preset workflow chains
- 2 lines added to CLAUDE.md

### Explicitly Out of Scope
- No scripts — pure SKILL.md instructions + YAML data
- No usage analytics or auto-learning
- No modifications to existing skills
- No fuzzy search scripts — Claude's semantic understanding is the matcher
