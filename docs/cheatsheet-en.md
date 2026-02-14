# Skills & Workflows Cheatsheet

## Development Workflow

### Full Feature Development (End-to-End)

```
brainstorming → sp-writing-plans → sp-test-driven-development → sp-executing-plans
    → sp-requesting-code-review → sp-receiving-code-review → sp-finishing-a-development-branch
```

| Scenario | Skill to Use |
|----------|-------------|
| New idea, not sure how to approach | `brainstorming` |
| Clear requirements, need implementation steps | `sp-writing-plans` |
| Ready to code (tests first) | `sp-test-driven-development` |
| Have a plan, execute with checkpoints | `sp-executing-plans` |
| Feature done, request review | `sp-requesting-code-review` |
| Received review feedback, need to process | `sp-receiving-code-review` |
| Branch complete, ready to merge / PR | `sp-finishing-a-development-branch` |

### Debugging

| Scenario | Skill to Use |
|----------|-------------|
| Bug or test failure encountered | `sp-systematic-debugging` |
| Fix applied, need to verify it's actually fixed | `verification-before-completion` |

### Parallel Work

| Scenario | Skill to Use |
|----------|-------------|
| Multiple independent tasks to run concurrently | `sp-dispatching-parallel-agents` |
| Plan has independent subtasks to delegate | `sp-subagent-driven-development` |
| Need isolated feature branch environment | `sp-using-git-worktrees` |

---

## Research Workflow

### Full Research (Multi-Source Decision Making)

```
critical-research + tech-feasibility → research-synthesis → Decision Document
```

| Scenario | Skill to Use |
|----------|-------------|
| Verify whether a claim is true | `critical-research` |
| Evaluate if a technology can solve a problem | `tech-feasibility` |
| Fact-check external articles or marketing copy | `narrative-auditor` |
| Verify documentation matches actual code | `codebase-audit` |
| Ran 2+ research skills, need unified conclusion | `research-synthesis` |

---

## Presentation Workflow

### From Topic to Finished Slides

```
presentation-planner → interactive-presentation-generator → Slide Files
```

| Scenario | Skill to Use |
|----------|-------------|
| Have a topic, need narrative strategy and outline | `presentation-planner` |
| Have a rough outline, need to refine structure | `presentation-planner` (Optimize mode) |
| Have a complete Slide Plan, generate slides | `interactive-presentation-generator` |
| Analyze existing UI design screenshots | `ui-design-analyzer` |

---

## Report Workflow

| Scenario | Skill to Use |
|----------|-------------|
| Generate weekly/monthly/project reports | `report-generator` |
| Query work logs, track TODOs | `work-log-analyzer` |
| Record current session activities (cross-session) | `activity-logger` |
| Understand code evolution history | `code-story-teller` |

---

## Code Review

| Scenario | Skill to Use |
|----------|-------------|
| Deep code review (default) | `code-review-gemini` |
| Quick review (< 50 lines changed) | `code-review-claude` |
| Review a pull request | `pr-review-assistant` |

---

## Meta / Skill Management

| Scenario | Skill to Use |
|----------|-------------|
| Create or edit a skill | `sp-writing-skills` |
| Audit skill quality (required after create/modify) | `skill-auditor` |
| Sync skills across AI tools | `skillshare` |

---

## Auto-Trigger Rules

These skills are automatically suggested or required under specific conditions:

| Trigger Condition | Auto-Triggered Skill |
|-------------------|---------------------|
| Before implementing new features | `brainstorming` (CLAUDE.md routing rule) |
| Before claiming work is complete | `verification-before-completion` |
| After creating/modifying a skill | `skill-auditor` |
| Brainstorming Phase 3: technical decision | `tech-feasibility` (required) |
| Brainstorming Phase 3: factual claim | `critical-research` (required) |
| After running 2+ research skills | `research-synthesis` (suggested) |
| After completing branch work | `report-generator` (suggested) |
| After querying work logs | `report-generator` (suggested) |
