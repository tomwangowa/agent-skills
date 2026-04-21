# Claude Code Skills

**English** | [繁體中文](./README.zh.md)

A collection of Claude Code skills grown out of real-world practice.

These skills aren't about showcasing what AI can do — they solve a specific problem: **as you delegate more work to AI, how do you ensure output quality doesn't degrade as trust increases?**

My approach is to embed engineering discipline into the AI workflow itself — using structured processes to counter cognitive blind spots shared by both AI and humans. Specifically:

- **Structured code review**: Any model over-rationalizes when reviewing its own output, so review is a skill-triggered step — not a verbal assurance. As of 2026-04, `code-review-claude` is the default (broad coverage + adversarial + assumptions + syntax verification, 0/6 hallucinations in benchmark); `code-review-gemini` is optional when you want a fully applied refactored patch or an external second opinion.
- **Falsification-first**: Research skills require searching for counter-evidence before supporting evidence. This isn't pessimism — it's a systematic defense against confirmation bias.
- **Evidence before assertion**: Before claiming any work is "done", you must run verification commands and confirm the output. Saying "tests pass" requires actually running the tests.

These principles don't require you to agree with my approach — they're independent modules you can use separately. Pick just code review, just research, or just the presentation generator. Each skill is self-contained.

---

## Skills Overview

Currently **34 custom skills** organized into 7 categories.

### Quality Gates (5)

Embed review and verification into the development workflow, not as an afterthought.

| Skill | Description |
|-------|-------------|
| [code-review-claude](./code-review-claude/) | Native code review by Claude (< 30s). Adversarial pass + assumptions list + optional refactored patch. **Default reviewer** (2026-04 benchmark: broader coverage, 0/6 verified hallucinations). |
| [code-review-gemini](./code-review-gemini/) | Deep code review using Gemini CLI. Use for final validation, or when a fully worked refactored patch is required. Also the reviewer required by the pre-commit auto-review rule in CLAUDE.md. |
| [pr-review-assistant](./pr-review-assistant/) | Structured pull request review. Analyzes diffs, assesses risk, provides improvement suggestions. |
| [codebase-audit](./codebase-audit/) | Claims-first codebase audit: extracts claims from documentation, verifies each against source code. Confirms whether docs and code are consistent. |
| [completion-gate](./completion-gate/) | Evidence gate before completion. Forces running verification commands and confirming output before claiming "done" or "passing". |

### Research & Critical Thinking (9)

When AI does research for you, don't just collect evidence that supports your ideas.

| Skill | Description |
|-------|-------------|
| [tech-research-pipeline](./tech-research-pipeline/) | **Full research pipeline orchestrator**. Chains 8 skills with 2 gates, triggering a complete workflow from scoping to decision document. For major technical decisions. |
| [deep-reading](./deep-reading/) | Systematic knowledge extraction from document sets. Identifies core mental models, expert disagreements, knowledge gaps, and teachable frameworks. For understanding, not just summarizing. |
| [tech-feasibility](./tech-feasibility/) | Technical feasibility assessment. 8-step structured process answering "can technology X solve problem Y?" before committing to a POC. |
| [assumption-extractor](./assumption-extractor/) | Systematically extracts explicit and implicit assumptions from technical documents. Classifies risk levels (CRITICAL → LOW), produces an Assumption Registry with dependency graphs. |
| [micro-poc-validator](./micro-poc-validator/) | Empirically validates technical assumptions with minimal code (≤ 30 lines). Time-boxed 5-30 minute experiments producing PASS/FAIL/PARTIAL results. |
| [critical-research](./critical-research/) | Falsification-first research: searches for counter-evidence before supporting evidence. Systematically eliminates confirmation bias. |
| [narrative-auditor](./narrative-auditor/) | Narrative audit: cross-references articles, marketing copy, and technical claims against primary sources. Can also act as your AI proxy. |
| [research-cross-validator](./research-cross-validator/) | Cross-validates technical claims using 2-3 independent strategies (official docs, counter-evidence search, source code inspection) to prevent single-source bias. |
| [research-synthesis](./research-synthesis/) | Multi-source research synthesis. After running 2+ research skills, consolidates findings into an ADR-style decision document. |

### Multi-Agent Roles (3)

Simulate team-based collaboration with isolated PM and RD roles, each running in its own subagent.

| Skill | Description |
|-------|-------------|
| [role-orchestrator](./role-orchestrator/) | **Pipeline coordinator.** Dispatches PM → RD subagents with approval gates between phases. Reads `project-profile.yaml` to calibrate output depth by project size (small/medium/large). For medium and large projects. |
| [role-pm](./role-pm/) | PM role: translates goals into size-calibrated requirements artifacts (bullet + AC → user stories → full PRD). |
| [role-rd](./role-rd/) | RD role: translates PM requirements into size-calibrated design artifacts (code plan → design doc → architecture doc). |

### Design & Planning (3)

Think before you build.

| Skill | Description |
|-------|-------------|
| [brainstorming](./brainstorming/) | Socratic design dialogue. Explores requirements one question at a time, proposes 2-3 approaches with trade-offs, produces a design document. Auto-escalates to `role-orchestrator` for medium/large projects. |
| [spec-gap-finder](./spec-gap-finder/) | Pre-dev spec/wireframe review from an RD perspective. Runs a 10-category, 60+ item checklist to find gaps, ambiguities, and undefined edge cases. Outputs a prioritized question list for a single alignment meeting with PM/Designer. |
| [ui-design-analyzer](./ui-design-analyzer/) | UI/UX screenshot analysis. Evaluates interface design across 6 dimensions including usability, accessibility, and visual design. |

### Content Generation (5)

Standardize repetitive documentation, presentation, and note-taking work.

| Skill | Description |
|-------|-------------|
| [presentation-planner](./presentation-planner/) | Presentation narrative strategy planning. Completes audience analysis, storyline design, and per-slide content planning before creating slides. |
| [interactive-presentation-generator](./interactive-presentation-generator/) | Interactive presentation generator. Supports reveal.js / Marp / Slidev with 20 built-in professional themes. |
| [qa-to-notes](./qa-to-notes/) | Save Claude Code conversations as Obsidian notes (Standard / Direct write), or rewrite fact-checks into a shareable "extended analysis" format for Teams (Teams publish). Three modes, unified note management. |
| [report-generator](./report-generator/) | Generate structured reports from activity logs and git history. Supports weekly, monthly, project summary, retrospective, and more. |
| [ai-weekly-insight](./ai-weekly-insight/) | Weekly or daily AI news deep-analysis for TrendLife AI Taskforce. Weekly: top 5 news; Daily: top 3 news. Three-dimension analysis (tech/business/competitive), outputs to Obsidian + Confluence or ai_news repo. Supports `--dest` and `daily` mode. |
| [arxiv-digest](./arxiv-digest/) | Digest arXiv AI papers into engineer-friendly shareable formats for Taskforce meetings. Supports URL, search, and multi-paper comparison modes. |

### Productivity & Tracking (3)

Cross-session work logging and historical analysis.

| Skill | Description |
|-------|-------------|
| [activity-logger](./activity-logger/) | Log work activities from the current session for cross-session aggregation and report generation. |
| [work-log-analyzer](./work-log-analyzer/) | Analyze work logs. Track task progress, query project history, understand decision evolution. Supports activity aggregation, timeline, TODO, decision tracing, and general search. |
| [code-story-teller](./code-story-teller/) | Analyze git history to tell the story of code evolution. Understand the context behind design decisions. |

### MCP Server

Structures skill data query capabilities as MCP tools, letting Claude Code directly query your work history.

| Server | Description |
|--------|-------------|
| [skills-query-server](./skills-query-server/) | Provides 7 structured query tools: activity queries, full-text search, activity logging, timeline tracking, TODO extraction, decision tracing, and work dashboard. Integrates data from activity-logger, work-log-analyzer, and qa-to-notes (activity logs + QA knowledge notes) via MCP protocol for direct Claude access. |

**Quick setup:**

```bash
cd ~/.claude/skills/skills-query-server && npm install
claude mcp add -s user skills-query -- npx tsx ~/.claude/skills/skills-query-server/src/index.ts
```

See [skills-query-server/README.md](./skills-query-server/README.md) for details.

### Tools & Meta-skills (2)

Tools for managing skills themselves.

| Skill | Description |
|-------|-------------|
| [skill-auditor](./skill-auditor/) | Audit skills for quality, security, and best practices. Use after creating or modifying a skill. |
| [skillshare](https://github.com/runkids/skillshare) | Sync skills across AI CLI tools (Claude Code, Cursor, Windsurf, etc.). Single source of truth, used everywhere. |

---

## About the Layered Code Review Design

**Any model tends to over-rationalize existing structure when reviewing code it generated.** So this repo makes review an explicit, skill-triggered step — with an adversarial checklist and an assumptions list — instead of relying on "let Claude look it over."

### Two reviewers, two roles (effective 2026-04)

- **`code-review-claude` (default)** — Native Claude review in under 30 s. Includes Step 3.3 syntax-checker verification (eliminates whitespace/regex/character-class hallucinations), Step 3.4 language-specific checklists, Step 3.5 adversarial quick check (Assumption exposed / Mirror test / Suppression / What breaks this?), Step 3.6 Assumptions Identified list, and an optional Step 4.5 Refactored Patch. In a 2026-04 n=6 benchmark across Java / Python / JS / TS / PHP / Shell HTTP retry clients, this skill's finding coverage was 2.3×–5.0× that of Gemini, with 0/6 verified hallucinations.
- **`code-review-gemini` (optional)** — External Gemini CLI review. Useful when you want a fully applied refactored patch or an external second opinion after the claude review. Not the default anymore, but retained as a patch generator and cross-check tool.

> **Pre-commit auto-review** also defaults to `code-review-claude`. Pre-commit is the highest-cost scenario for hallucinations, so it uses the benchmark-most-reliable reviewer.

---

## About the Research Pipeline

When AI helps with technical evaluation, the most common failure mode isn't insufficient analysis — it's **unverified assumptions packaged as conclusions**. A seemingly thorough feasibility report might rest on 3 untested implicit assumptions — only discovered during implementation when the foundation doesn't hold.

The research pipeline (`tech-research-pipeline`) solves this problem. It chains 8 research skills into a complete verification pipeline, where each stage's output becomes the next stage's input:

```
brainstorming → tech-feasibility → assumption-extractor → micro-poc-validator
    → GATE A → critical-research → narrative-auditor → research-cross-validator
    → GATE B → research-synthesis → Decision Document
```

The two gates are key design elements:

- **Gate A** (after micro-poc): If a BLOCKING assumption is empirically disproven, **the entire pipeline stops** — no wasting time continuing research on a failed foundation.
- **Gate B** (after cross-validation): Checks whether findings from all stages converge consistently. If key claims contradict each other across verification strategies, they're marked DISPUTED rather than forced into a conclusion.

This pipeline's design came from a painful lesson: in a ScraperAPI migration project, a seemingly complete feasibility report missed an implicit assumption (nodriver doesn't support WSS connections), only discovered weeks into implementation when the entire architecture proved unviable. Had the pipeline been run, Phase 3's micro-PoC would have caught this in 5 minutes on Day 1.

You don't need to run the full pipeline every time. Each skill works independently — but when the cost of a decision is high enough, the full pipeline helps you find those "unknown unknowns" before committing to implementation.

---

## About Superpowers Plugin Skills

Superpowers plugin skills (writing-plans, executing-plans, systematic-debugging, TDD, etc.) are loaded from the [superpowers](https://github.com/obra/superpowers) plugin. They appear as `superpowers:skill-name` in your session (e.g., `superpowers:writing-plans`, `superpowers:systematic-debugging`). No local copies or symlinks needed.

---

## Quick Start

### Prerequisites

- [Claude Code CLI](https://docs.anthropic.com/en/docs/claude-code)
- [Node.js](https://nodejs.org/) (only if you want to use Gemini-powered skills)
- Git

### Installation

**Option 1: Clone directly to the skills directory (recommended)**

```bash
git clone https://github.com/tomwangowa/agent-skills.git ~/.claude/skills
```

**Option 2: Symlink an existing clone**

```bash
ln -s /path/to/cloned/repo ~/.claude/skills
```

### Set Up Slash Commands

Slash commands live in `~/.claude/commands/`, a separate directory from skills. After the main install, symlink the bundled commands into place:

```bash
mkdir -p ~/.claude/commands
ln -s ~/.claude/skills/commands/sos.md ~/.claude/commands/sos.md
```

Without this step, typing `/sos` in Claude Code returns "command not found" even though the backing `claude-workflow-designer` skill is installed.

### Set Up Gemini CLI (optional)

The default reviewer `code-review-claude` is native Claude and requires no Gemini setup. Gemini CLI is only used by `code-review-gemini` (optional depth reviewer / refactored-patch generator) and the keyword-triggered Gemini path of `pr-review-assistant` (opt-in). You can skip this section if you only run the default flow.

```bash
# Install Gemini CLI
npm install -g @google/gemini-cli

# Set API key (get one from https://aistudio.google.com/app/apikey)
export GEMINI_API_KEY="your-api-key-here"

# Write to shell profile for persistence
echo 'export GEMINI_API_KEY="your-api-key-here"' >> ~/.zshrc  # or ~/.bashrc
```

### Verify Installation

```bash
# Confirm Claude Code can see the skills
ls ~/.claude/skills/

# Test Gemini CLI (only if you installed Gemini-powered skills)
gemini "Hello, test"
```

---

## Usage Examples

### Code Review (default: Claude)

```bash
# 1. Stage your changes
git add src/app.js

# 2. Trigger with natural language in Claude Code
> review the staged files
> check code quality before commit
```

The default trigger invokes `code-review-claude`, which returns a structured report in under 30 seconds:
- 🔴 High / 🟡 Medium / 🟢 Low priority findings
- Language-specific checklist hits (Python / Shell / JS / TS / Java / PHP)
- **Adversarial quick check** — Assumption exposed / Mirror test / Suppression / What breaks this?
- **Assumptions Identified** — unvalidated contracts the code relies on
- **Refactored Patch** (optional, emitted when the diff is ≤ ~200 lines)

Want an external second opinion or a fully worked refactored patch? Chain a Gemini review afterwards:

```
> gemini review these changes and give me a refactored patch
> detailed review with gemini
```

### Activity Logger

```bash
# Initialize (first time)
~/.claude/skills/activity-logger/scripts/init_activities.sh init

# Log via Claude Code
> log this activity
> record what I just did

# Or use CLI directly
~/.claude/skills/activity-logger/scripts/log_activity.sh \
  -d "Implemented user authentication" \
  -t task_completed \
  -c "Added OAuth2 support" \
  --tags "security,auth"

# Manage activity records
~/.claude/skills/activity-logger/scripts/init_activities.sh info    # View session info
~/.claude/skills/activity-logger/scripts/init_activities.sh list    # List all records
~/.claude/skills/activity-logger/scripts/init_activities.sh stats   # Stats by type
~/.claude/skills/activity-logger/scripts/init_activities.sh archive 30  # Archive records older than 30 days
```

**Activity types**: `task_completed`, `bug_fixed`, `refactoring`, `research`, `documentation`, `review`

**Record locations**: `~/.claude/activities/` (active), `~/.claude/activities/processed/` (archived)

Activity records can be used with `work-log-analyzer` for cross-project and cross-session aggregation analysis.

---

## Skill Dependencies

| Skill | Dependencies |
|-------|-------------|
| code-review-gemini | [Gemini CLI](https://github.com/google-gemini/gemini-cli), Git |
| code-review-claude | No external dependencies |
| code-story-teller | Git |
| pr-review-assistant | [GitHub CLI](https://cli.github.com/), Git; [Gemini CLI](https://github.com/google-gemini/gemini-cli) (opt-in deep path only) |
| ui-design-analyzer | No external dependencies (uses Claude's native multimodal capabilities) |
| interactive-presentation-generator | No external dependencies (20 built-in theme templates) |
| activity-logger | `jq`, Git |
| work-log-analyzer | `jq`, `date` (core functionality has no external dependencies) |
| skill-auditor | Bash 4.0+ (optional: Gemini CLI for semantic analysis) |
| skills-query-server | Node.js, `tsx` (registered via `claude mcp add`) |
| All other skills | No external dependencies |

---

## Creating a New Skill

```bash
# 1. Create directory
mkdir my-skill

# 2. Create SKILL.md
cat > my-skill/SKILL.md << 'EOF'
---
name: My Skill Name
description: Brief description of when to use this skill.
---

# My Skill Name

## Instructions
Describe when and how Claude should use this skill.

## Examples
Provide example trigger phrases and expected behavior.
EOF

# 3. (Optional) Add helper scripts
mkdir my-skill/scripts

# 4. Validate with skill-auditor
> audit my-skill
```

### Skill Directory Structure

```
skill-name/
├── SKILL.md           # Required: skill definition and instructions
├── scripts/           # Optional: helper shell scripts
│   └── my_script.sh
└── other_files/       # Optional: other resources
```

---

## Troubleshooting

| Error | Likely Cause | Quick Fix |
|-------|-------------|-----------|
| `command not found: gemini` | Gemini CLI not installed | `npm install -g @google/gemini-cli` |
| `GEMINI_API_KEY not set` | API key not configured | `export GEMINI_API_KEY="..."` |
| `No staged changes` | No staged files | `git add <files>` |
| `permission denied` | Script lacks execute permission | `chmod +x *.sh` |
| `429 Resource exhausted` | API quota depleted | Wait for reset or upgrade plan |
| `401 Unauthorized` | Invalid API key | Regenerate key |

---

## More Documentation

- **[SKILLS_ROADMAP.md](./SKILLS_ROADMAP.md)** — Skills development roadmap
- **[Cheatsheet (EN)](./cheatsheet/cheatsheet-en.md)** · **[速查表 (中文)](./cheatsheet/cheatsheet-zh.md)** — Quick reference

---

## License

MIT
