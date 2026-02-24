# Claude Code Skills

**English** | [繁體中文](./README.zh.md)

A collection of Claude Code skills grown out of real-world practice.

These skills aren't about showcasing what AI can do — they solve a specific problem: **as you delegate more work to AI, how do you ensure output quality doesn't degrade as trust increases?**

My approach is to embed engineering discipline into the AI workflow itself — using structured processes to counter cognitive blind spots shared by both AI and humans. Specifically:

- **Dual-AI Review**: Claude develops, Gemini reviews independently. Not for the sake of adding another AI, but because any model tends to over-rationalize when reviewing its own output.
- **Falsification-first**: Research skills require searching for counter-evidence before supporting evidence. This isn't pessimism — it's a systematic defense against confirmation bias.
- **Evidence before assertion**: Before claiming any work is "done", you must run verification commands and confirm the output. Saying "tests pass" requires actually running the tests.

These principles don't require you to agree with my approach — they're independent modules you can use separately. Pick just code review, just research, or just the presentation generator. Each skill is self-contained.

---

## Skills Overview

Currently **24 custom skills** organized into 6 categories.

### Quality Gates (5)

Embed review and verification into the development workflow, not as an afterthought.

| Skill | Description |
|-------|-------------|
| [code-review-gemini](./code-review-gemini/) | Deep code review using Gemini CLI. Analyzes staged changes, produces structured reports. **Default reviewer.** |
| [code-review-claude](./code-review-claude/) | Fast native code review by Claude (< 30s). Best for changes under 50 lines. |
| [pr-review-assistant](./pr-review-assistant/) | Structured pull request review. Analyzes diffs, assesses risk, provides improvement suggestions. |
| [codebase-audit](./codebase-audit/) | Claims-first codebase audit: extracts claims from documentation, verifies each against source code. Confirms whether docs and code are consistent. |
| [verification-before-completion](./verification-before-completion/) | Evidence gate before completion. Forces running verification commands and confirming output before claiming "done" or "passing". |

### Research & Critical Thinking (8)

When AI does research for you, don't just collect evidence that supports your ideas.

| Skill | Description |
|-------|-------------|
| [tech-research-pipeline](./tech-research-pipeline/) | **Full research pipeline orchestrator**. Chains 8 skills with 2 gates, triggering a complete workflow from scoping to decision document. For major technical decisions. |
| [tech-feasibility](./tech-feasibility/) | Technical feasibility assessment. 8-step structured process answering "can technology X solve problem Y?" before committing to a POC. |
| [assumption-extractor](./assumption-extractor/) | Systematically extracts explicit and implicit assumptions from technical documents. Classifies risk levels (CRITICAL → LOW), produces an Assumption Registry with dependency graphs. |
| [micro-poc-validator](./micro-poc-validator/) | Empirically validates technical assumptions with minimal code (≤ 30 lines). Time-boxed 5-30 minute experiments producing PASS/FAIL/PARTIAL results. |
| [critical-research](./critical-research/) | Falsification-first research: searches for counter-evidence before supporting evidence. Systematically eliminates confirmation bias. |
| [narrative-auditor](./narrative-auditor/) | Narrative audit: cross-references articles, marketing copy, and technical claims against primary sources. Can also act as your AI proxy. |
| [research-cross-validator](./research-cross-validator/) | Cross-validates technical claims using 2-3 independent strategies (official docs, counter-evidence search, source code inspection) to prevent single-source bias. |
| [research-synthesis](./research-synthesis/) | Multi-source research synthesis. After running 2+ research skills, consolidates findings into an ADR-style decision document. |

### Design & Planning (2)

Think before you build.

| Skill | Description |
|-------|-------------|
| [brainstorming](./brainstorming/) | Socratic design dialogue. Explores requirements one question at a time, proposes 2-3 approaches with trade-offs, produces a design document. |
| [ui-design-analyzer](./ui-design-analyzer/) | UI/UX screenshot analysis. Evaluates interface design across 6 dimensions including usability, accessibility, and visual design. |

### Content Generation (4)

Standardize repetitive documentation, presentation, and note-taking work.

| Skill | Description |
|-------|-------------|
| [presentation-planner](./presentation-planner/) | Presentation narrative strategy planning. Completes audience analysis, storyline design, and per-slide content planning before creating slides. |
| [interactive-presentation-generator](./interactive-presentation-generator/) | Interactive presentation generator. Supports reveal.js / Marp / Slidev with 20 built-in professional themes. |
| [qa-to-notes](./qa-to-notes/) | Save Claude Code conversations as Obsidian notes (Standard / Direct write), or rewrite fact-checks into a shareable "extended analysis" format for Teams (Teams publish). Three modes, unified note management. |
| [report-generator](./report-generator/) | Generate structured reports from activity logs and git history. Supports weekly, monthly, project summary, retrospective, and more. |

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
| [skillshare](./skillshare/) | Sync skills across AI CLI tools (Claude Code, Cursor, Windsurf, etc.). Single source of truth, used everywhere. |

---

## About Dual-AI Review

This repo has a design that might seem odd: code review defaults to Gemini, not Claude itself.

The reason is simple — **any model tends to over-rationalize existing structure when reviewing code it generated**. Claude handles development and context understanding; Gemini plays the relatively conservative reviewer, particularly good at catching logic gaps, edge cases, and insufficient defensive coding.

This simulates the "author vs. reviewer separation" found in real teams. The current approach automatically invokes Gemini review after each small task, iterating on feedback until fully approved. The value isn't in adding another AI — it's in shifting review earlier and systematizing it, catching issues before risk accumulates.

If you don't use Gemini, `code-review-claude` provides a Claude-native fast review alternative.

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

## About Standard Procedures (sp-*)

Beyond the 24 skills above, this repo integrates 13 **Standard Procedures** via symlinks — behavioral protocols embedded in the development workflow (e.g., TDD, systematic debugging, plan-then-execute), from the [superpowers](https://github.com/obra/superpowers) project.

They're not standalone tools but process protocols defining "what to do in which context." For example, `sp-systematic-debugging` requires collecting symptoms, forming hypotheses, then attempting fixes when you encounter a bug — rather than jumping straight to modifying code.

See [EXTERNAL_SKILLS.md](./EXTERNAL_SKILLS.md) for details.

---

## Quick Start

### Prerequisites

- [Claude Code CLI](https://docs.anthropic.com/en/docs/claude-code)
- [Node.js](https://nodejs.org/) (for Gemini CLI)
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

### Set Up Gemini CLI

Gemini CLI is used by code-review-gemini, code-story-teller, pr-review-assistant, and other skills that require external review.

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

# Test Gemini CLI
gemini "Hello, test"
```

---

## Usage Examples

### Code Review (Gemini)

```bash
# 1. Stage your changes
git add src/app.js

# 2. Trigger with natural language in Claude Code
> review the staged files
> check code quality before commit
```

Claude will invoke Gemini to analyze your changes, producing a structured report covering:
- Potential bugs or security issues
- Code quality and best practices
- Readability and maintainability
- Improvement suggestions

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
| code-story-teller | [Gemini CLI](https://github.com/google-gemini/gemini-cli), Git |
| pr-review-assistant | [Gemini CLI](https://github.com/google-gemini/gemini-cli), [GitHub CLI](https://cli.github.com/), Git |
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

- **[EXTERNAL_SKILLS.md](./EXTERNAL_SKILLS.md)** — External skills management (sp-* series)
- **[SKILLS_ROADMAP.md](./SKILLS_ROADMAP.md)** — Skills development roadmap
- **[Cheatsheet (EN)](./cheatsheet/cheatsheet-en.md)** · **[速查表 (中文)](./cheatsheet/cheatsheet-zh.md)** — Quick reference

---

## License

MIT
