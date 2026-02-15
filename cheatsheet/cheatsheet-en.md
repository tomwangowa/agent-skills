# Skills & Workflows Cheatsheet

> **Note:** Skills prefixed with `sp-` are adapted from the open-source [superpowers](https://github.com/claude-did-this/skills) project.

## Development Workflow

### Full Feature Development (End-to-End)

```
brainstorming → sp-writing-plans → sp-test-driven-development → sp-executing-plans
    → sp-requesting-code-review → sp-receiving-code-review → sp-finishing-a-development-branch
```

| Scenario | Skill to Use | Example |
|----------|-------------|---------|
| New idea, not sure how to approach | `brainstorming` | "I want to add a notification system but not sure about the architecture" |
| Clear requirements, need implementation steps | `sp-writing-plans` | "Write a plan for adding JWT auth to the API" |
| Ready to code (tests first) | `sp-test-driven-development` | "Implement the login endpoint using TDD" |
| Have a plan, execute with checkpoints | `sp-executing-plans` | "Execute the auth implementation plan from plan.md" |
| Feature done, request review | `sp-requesting-code-review` | "Review my auth feature before merging" |
| Received review feedback, need to process | `sp-receiving-code-review` | "Process the review comments on PR #42" |
| Branch complete, ready to merge / PR | `sp-finishing-a-development-branch` | "Branch is done, help me create a PR" |

### Debugging

| Scenario | Skill to Use | Example |
|----------|-------------|---------|
| Bug or test failure encountered | `sp-systematic-debugging` | "Tests fail with 'undefined is not a function' in auth.ts" |
| Fix applied, need to verify it's actually fixed | `verification-before-completion` | "I fixed the auth bug, verify it's actually resolved" |

### Parallel Work

| Scenario | Skill to Use | Example |
|----------|-------------|---------|
| Multiple independent tasks to run concurrently | `sp-dispatching-parallel-agents` | "Run linting, tests, and type-check in parallel" |
| Plan has independent subtasks to delegate | `sp-subagent-driven-development` | "Execute steps 2, 3, 5 from the plan simultaneously" |
| Need isolated feature branch environment | `sp-using-git-worktrees` | "Create a worktree for the payment-refactor feature" |

---

## Research Workflow

### Full Research (Multi-Source Decision Making)

```
critical-research + tech-feasibility → research-synthesis → Decision Document
```

| Scenario | Skill to Use | Example |
|----------|-------------|---------|
| Verify whether a claim is true | `critical-research` | "Is it true that React Server Components can't use hooks?" |
| Evaluate if a technology can solve a problem | `tech-feasibility` | "Can Bun replace Node.js for our production API?" |
| Fact-check external articles or marketing copy | `narrative-auditor` | "Fact-check this blog post about Redis vs Memcached" |
| Verify documentation matches actual code | `codebase-audit` | "Audit whether the README claims match the actual API" |
| Ran 2+ research skills, need unified conclusion | `research-synthesis` | "Synthesize the database options research into a decision doc" |

---

## Presentation Workflow

### From Topic to Finished Slides

```
presentation-planner → interactive-presentation-generator → Slide Files
```

| Scenario | Skill to Use | Example |
|----------|-------------|---------|
| Have a topic, need narrative strategy and outline | `presentation-planner` | "Plan a presentation on 'Why We're Migrating to TypeScript'" |
| Have a rough outline, need to refine structure | `presentation-planner` (Optimize mode) | "Optimize this outline to have better narrative flow" |
| Have a complete Slide Plan, generate slides | `interactive-presentation-generator` | "Generate Marp slides from the approved Slide Plan" |
| Analyze existing UI design screenshots | `ui-design-analyzer` | "Analyze this dashboard screenshot for UX issues" |

---

## Report Workflow

| Scenario | Skill to Use | Example |
|----------|-------------|---------|
| Generate weekly/monthly/project reports | `report-generator` | "Generate a weekly report for this sprint" |
| Query work logs, track TODOs | `work-log-analyzer` | "What TODOs are still open from last week?" |
| Record current session activities (cross-session) | `activity-logger` | "Log today's work: refactored auth module, fixed 3 bugs" |
| Understand code evolution history | `code-story-teller` | "Tell the story of how auth.ts evolved over time" |

---

## Code Review

| Scenario | Skill to Use | Example |
|----------|-------------|---------|
| Deep code review (default) | `code-review-gemini` | "Do a thorough review of the changes in src/auth/" |
| Quick review (< 50 lines changed) | `code-review-claude` | "Quick review this small fix in utils.ts" |
| Review a pull request | `pr-review-assistant` | "Review PR #42" |

---

## Meta / Skill Management

| Scenario | Skill to Use | Example |
|----------|-------------|---------|
| Create or edit a skill | `sp-writing-skills` | "Create a new skill for database migration" |
| Audit skill quality (required after create/modify) | `skill-auditor` | "Audit the new db-migrator skill" |
| Sync skills across AI tools | `skillshare` | "Sync my skills to Cursor and Windsurf" |

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
