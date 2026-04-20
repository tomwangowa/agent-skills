# Skills & Workflows Cheatsheet

> **Note:** Skills prefixed with `superpowers:` are provided by the [superpowers](https://github.com/obra/superpowers) plugin. The `brainstorming` skill has a personal override that shadows the superpowers version.

## Development Workflow

### Full Feature Development (End-to-End)

```
Small projects:
  brainstorming → superpowers:writing-plans → superpowers:test-driven-development → superpowers:executing-plans
      → superpowers:requesting-code-review → superpowers:receiving-code-review → superpowers:finishing-a-development-branch

Medium/Large projects:
  role-orchestrator (PM → RD) → superpowers:writing-plans → superpowers:subagent-driven-development
      → superpowers:requesting-code-review → superpowers:receiving-code-review → superpowers:finishing-a-development-branch
```

| Scenario | Skill to Use | Example |
|----------|-------------|---------|
| Medium/large project needing structured PM→RD pipeline | `role-orchestrator` | "Start role pipeline for building an e-commerce checkout system" |
| Only need PM requirements analysis | `role-pm` | "PM analysis for building a notification system" |
| Only need RD technical design | `role-rd` | "RD design for this set of requirements" |
| New idea, not sure how to approach | `brainstorming` | "I want to add a notification system but not sure about the architecture" |
| Have PM spec/wireframe, need to find gaps before coding | `spec-gap-finder` | "Review this spec for gaps before I start implementing" |
| Clear requirements, need implementation steps | `superpowers:writing-plans` | "Write a plan for adding JWT auth to the API" |
| Ready to code (tests first) | `superpowers:test-driven-development` | "Implement the login endpoint using TDD" |
| Have a plan, execute with checkpoints | `superpowers:executing-plans` | "Execute the auth implementation plan from plan.md" |
| Feature done, request review | `superpowers:requesting-code-review` | "Review my auth feature before merging" |
| Received review feedback, need to process | `superpowers:receiving-code-review` | "Process the review comments on PR #42" |
| Branch complete, ready to merge / PR | `superpowers:finishing-a-development-branch` | "Branch is done, help me create a PR" |

### Debugging

| Scenario | Skill to Use | Example |
|----------|-------------|---------|
| Bug or test failure encountered | `superpowers:systematic-debugging` | "Tests fail with 'undefined is not a function' in auth.ts" |
| Fix applied, need to verify it's actually fixed | `completion-gate` | "I fixed the auth bug, verify it's actually resolved" |

### Parallel Work

| Scenario | Skill to Use | Example |
|----------|-------------|---------|
| Multiple independent tasks to run concurrently | `superpowers:dispatching-parallel-agents` | "Run linting, tests, and type-check in parallel" |
| Plan has independent subtasks to delegate | `superpowers:subagent-driven-development` | "Execute steps 2, 3, 5 from the plan simultaneously" |
| Need isolated feature branch environment | `superpowers:using-git-worktrees` | "Create a worktree for the payment-refactor feature" |

---

## Research Workflow

### Full Research Pipeline (8-Phase Rigorous Evaluation)

```
tech-research-pipeline (one-shot trigger for full workflow):
  brainstorming → tech-feasibility → assumption-extractor → micro-poc-validator
    → GATE A → critical-research → narrative-auditor → research-cross-validator
    → GATE B → research-synthesis → Decision Document
```

| Scenario | Skill to Use | Example |
|----------|-------------|---------|
| Major tech decision requiring rigorous multi-angle evaluation | `tech-research-pipeline` | "Run full research pipeline to evaluate migrating from nodriver to Playwright" |
| Evaluate if a technology can solve a problem | `tech-feasibility` | "Can Bun replace Node.js for our production API?" |
| Extract hidden assumptions from a technical document | `assumption-extractor` | "Extract all assumptions from this design document" |
| Empirically validate a technical assumption (5-30 min) | `micro-poc-validator` | "Validate whether nodriver can connect to wss:// URLs" |
| Verify whether a claim is true | `critical-research` | "Is it true that React Server Components can't use hooks?" |
| Fact-check external articles or marketing copy | `narrative-auditor` | "Fact-check this blog post about Redis vs Memcached" |
| Cross-validate technical claims via multiple strategies | `research-cross-validator` | "Cross-validate the key claims in this feasibility report" |
| Verify documentation matches actual code | `codebase-audit` | "Audit whether the README claims match the actual API" |
| Ran 2+ research skills, need unified conclusion | `research-synthesis` | "Synthesize the database options research into a decision doc" |

### Narrative Auditor Full Workflow

```
narrative-auditor (fact-check + commentary)
    → qa-to-notes "save as notes" (save fact-check + commentary)
    → qa-to-notes "rewrite for Teams" (Teams version, appended to same note)
```

| Step | What to Say | What Happens |
|------|------------|--------------|
| 1. Fact-check | `/narrative-auditor` + paste article URL | Produces fact-check report |
| 2. Commentary | "Write a short commentary" | Produces shareable commentary |
| 3. Save | "Save as notes" or `/qa-to-notes` | Saves fact-check + commentary as Obsidian note |
| 4. Teams ver. | "Rewrite for Teams" or `/qa-to-notes publish` | Toned-down rewrite, appended to same note, also displayed for copying |

**Teams version auto-transformation:**
- Strips verdict labels (ACCURATE/MISLEADING/FALSE), severity levels, confidence tags
- Strips owner name, TrendLife brand, 🦤 Dodo persona markers
- Reframes negative findings as "also worth knowing"
- Always includes a "💡 Thesis" section with concrete scenario examples
- Original sharer placeholder `@_____` (fill in manually)

---

## Knowledge Management

### Newsletter Digest

| Scenario | Skill to Use | Example |
|----------|-------------|---------|
| Digest an entire folder of newsletters | `newsletter-digest` | "Digest the newsletters in ~/Downloads/newsletters" |
| Recursively process subfolders | `newsletter-digest` (recursive mode) | "~/Mail/subscriptions has many subfolders, digest them all" |
| Digest only a specific date range | `newsletter-digest` (date filter) | "Only digest this week's newsletters" |

> **Design philosophy:** Transforms scattered `.eml` files into structured knowledge. Auto-clusters by topic, each topic gets a synthesized summary (not per-article paste), and each article gets a standalone overview so you can grasp ~80% without reading the original. Warm conversational tone — like a colleague sharing observations, not an AI generating a report.

### qa-to-notes Three Modes

| Mode | Trigger | Behavior | Output |
|------|---------|----------|--------|
| **Standard** | "save as notes" | Restructure into encyclopedia-style article | Write to file |
| **Direct write** | "save as-is" "save raw" | Preserve verbatim | Write to file |
| **Teams publish** | "rewrite for Teams" "publish" | Tone-down rewrite for corporate group sharing | Display + append to note file |

| Scenario | Mode | Example |
|----------|------|---------|
| Conversation has knowledge worth keeping | Standard | "Save this React hooks discussion as a note" |
| Fact-check report to preserve as-is | Direct write | "Save this fact-check as-is" |
| Saved fact-check needs a shareable version | Teams publish | "Rewrite for Teams" |
| Append content to existing note | Standard / Direct write | "Append this to the OpenClaw note" |

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
| Produce weekly AI news deep-analysis | `ai-weekly-insight` | "AI 週報" or `/ai-weekly-insight` |
| Produce daily AI news deep-analysis | `ai-weekly-insight` (daily mode) | "AI 日報" or `/ai-weekly-insight daily` |
| Specify publish destination (Confluence or repo) | `ai-weekly-insight --dest` | `/ai-weekly-insight --dest repo` |
| Digest arXiv papers for meeting sharing | `arxiv-digest` | "paper digest" or `/arxiv-digest <url>` |
| Generate weekly/monthly/project reports | `report-generator` | "Generate a weekly report for this sprint" |
| Query work logs, track TODOs | `work-log-analyzer` | "What TODOs are still open from last week?" |
| Record current session activities (cross-session) | `activity-logger` | "Log today's work: refactored auth module, fixed 3 bugs" |
| Understand code evolution history | `code-story-teller` | "Tell the story of how auth.ts evolved over time" |

---

## Code Review

| Scenario | Skill to Use | Example |
|----------|-------------|---------|
| Any code review (default) | `code-review-claude` | "Review the changes in src/auth/" |
| Deep review / need a refactored patch / pre-commit validation | `code-review-gemini` | "Gemini review this module, give me a refactored patch" |
| Review a pull request | `pr-review-assistant` | "Review PR #42" |

> **Review skill routing guide:**
> - **During daily development:** Use `/code-review-gemini` (deep) or `/code-review-claude` (quick) directly
> - **Before merging major features:** Use `/superpowers:requesting-code-review` for dual-layer review (auto-dispatches subagent + gemini, merges results)
> - **When receiving review feedback:** `/superpowers:receiving-code-review` prevents blind agreement — requires technical verification before implementing changes

---

## Meta / Skill Management

| Scenario | Skill to Use | Example |
|----------|-------------|---------|
| Not sure which skill to use | `skill-router` | "/skill-router I want to evaluate using Redis for session store" |
| Browse all available skills by category | `skill-router list` | "/skill-router list" |
| View predefined multi-skill workflows | `skill-router workflows` | "/skill-router workflows" |
| Create or edit a skill | `superpowers:writing-skills` | "Create a new skill for database migration" |
| Audit skill quality (required after create/modify) | `skill-auditor` | "Audit the new db-migrator skill" |
| Sync skills across AI tools | `skillshare` | "Sync my skills to Cursor and Windsurf" |

> **skill-router design philosophy:** With 30+ skills, remembering each one's purpose and trigger phrases becomes impractical. skill-router is the unified entry point — describe your need and it semantically matches the best skill or workflow from its registry, but **never auto-executes** — always waits for confirmation. Three modes: smart routing (default), category browse, and workflow browse.

---

## Auto-Trigger Rules

These skills are automatically suggested or required under specific conditions:

| Trigger Condition | Auto-Triggered Skill |
|-------------------|---------------------|
| Before implementing new features | `brainstorming` (CLAUDE.md routing rule) |
| RD receives PM spec / wireframe | `spec-gap-finder` (suggested) |
| brainstorming detects medium/large scope | `role-orchestrator` (suggested escalation) |
| Before claiming work is complete | `completion-gate` |
| After creating/modifying a skill | `skill-auditor` |
| Brainstorming Phase 3: technical decision | `tech-feasibility` (required) |
| Brainstorming Phase 3: factual claim | `critical-research` (required) |
| After tech-feasibility produces a report | `assumption-extractor` (suggested) |
| After assumption-extractor finds CRITICAL assumptions | `micro-poc-validator` (suggested) |
| After running 2+ research skills | `research-synthesis` (suggested) |
| Major tech decision requiring rigorous evaluation | `tech-research-pipeline` (suggested) |
| After completing branch work | `report-generator` (suggested) |
| After querying work logs | `report-generator` (suggested) |
