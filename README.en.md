# Claude Code Skills

[繁體中文](./README.md) | **English**

A collection of Claude Code skills grown from real-world practice.

These skills aren't about showcasing what AI can do. They address a specific problem: **as you delegate more work to AI, how do you ensure output quality doesn't degrade as trust increases?**

My approach is to embed engineering discipline into the AI workflow itself — using structured processes to counter the cognitive blind spots shared by both AI and humans. Specifically:

- **Dual-AI Review**: Claude develops, Gemini reviews independently. Not for the sake of having two AIs, but because any model tends to over-rationalize its own output when reviewing it.
- **Falsification-first**: Research skills search for counter-evidence before supporting evidence. This isn't pessimism — it's a systematic defense against confirmation bias.
- **Evidence before assertion**: Before claiming any work is "done," you must run verification commands and confirm the output. Saying "tests pass" requires actually having run the tests.

You don't need to agree with my approach to use these — they're independent modules you can adopt separately. Use just the code review, just the research, or just the presentation generator. Each skill is self-contained.

---

## Skills Overview

Currently **34 custom skills** organized into 7 categories.

### Quality Gates (5)

Embed review and verification into the development flow, not as an afterthought.

| Skill | Description |
|-------|-------------|
| [code-review-gemini](./code-review-gemini/) | Deep code review using Gemini CLI. Analyzes staged changes, produces structured reports. **Default reviewer.** |
| [code-review-claude](./code-review-claude/) | Fast native code review using Claude (< 30 seconds). Best for changes under 50 lines. |
| [pr-review-assistant](./pr-review-assistant/) | Structured pull request review. Analyzes diffs, assesses risk, provides improvement suggestions. |
| [codebase-audit](./codebase-audit/) | Claims-first codebase audit: extracts claims from documentation, verifies each against source code. Confirms whether docs and code actually match. |
| [completion-gate](./completion-gate/) | Evidence gate before completion. Forces running verification commands and confirming output before any claim of "done" or "passing." |

### Research & Critical Thinking (8)

When AI does research for you, it shouldn't just collect evidence that supports your hypothesis.

| Skill | Description |
|-------|-------------|
| [tech-research-pipeline](./tech-research-pipeline/) | **Full research pipeline orchestrator.** Chains 8 skills with 2 gate checks into a single workflow — from scope definition to decision document. For high-stakes technical decisions. |
| [tech-feasibility](./tech-feasibility/) | Technology feasibility assessment. 8-step structured process to answer "can technology X solve problem Y?" before committing to a POC. |
| [assumption-extractor](./assumption-extractor/) | Systematically extracts explicit and implicit assumptions from technical documents. Classifies by risk level (CRITICAL → LOW), produces an Assumption Registry with dependency graphs. |
| [micro-poc-validator](./micro-poc-validator/) | Empirically validates technical assumptions with minimal code (≤ 30 lines). Time-boxed experiments (5-30 min) producing PASS/FAIL/PARTIAL results. |
| [critical-research](./critical-research/) | Falsification-first research: seeks counter-evidence before supporting evidence. Systematically eliminates confirmation bias. |
| [narrative-auditor](./narrative-auditor/) | Narrative auditing: cross-references articles, marketing copy, and technical claims against primary sources. Can also serve as your AI proxy for public responses. |
| [research-cross-validator](./research-cross-validator/) | Cross-validates technical claims using 2-3 independent strategies (official docs, counter-evidence search, source code inspection, etc.) to prevent single-source bias. |
| [research-synthesis](./research-synthesis/) | Multi-source research synthesis. After running 2+ research skills, integrates findings into an ADR-style decision document. |

### Multi-Agent Roles (3)

Simulate team-based collaboration with isolated PM and RD roles, each running in its own subagent.

| Skill | Description |
|-------|-------------|
| [role-orchestrator](./role-orchestrator/) | **Pipeline coordinator.** Dispatches PM → RD subagents with approval gates between phases. Reads `project-profile.yaml` to calibrate output depth by project size (small/medium/large). For medium and large projects. |
| [role-pm](./role-pm/) | PM role: translates goals into size-calibrated requirements artifacts (bullet + AC → user stories → full PRD). |
| [role-rd](./role-rd/) | RD role: translates PM requirements into size-calibrated design artifacts (code plan → design doc → architecture doc). |

### Design & Planning (2)

Think before you build.

| Skill | Description |
|-------|-------------|
| [brainstorming](./brainstorming/) | Socratic design dialogue. Explores requirements one question at a time, proposes 2-3 approaches with trade-offs, produces a design document. Auto-escalates to `role-orchestrator` for medium/large projects. |
| [ui-design-analyzer](./ui-design-analyzer/) | UI/UX screenshot analysis. Evaluates interface design across 6 dimensions including usability, accessibility, and visual design. |

### Content Generation (5)

Standardize repetitive documentation, presentations, and note-taking.

| Skill | Description |
|-------|-------------|
| [presentation-planner](./presentation-planner/) | Presentation narrative strategy. Before making slides, completes audience analysis, storyline design, and per-slide content planning. |
| [interactive-presentation-generator](./interactive-presentation-generator/) | Interactive presentation generator. Supports reveal.js / Marp / Slidev with 20 built-in professional styles. |
| [qa-to-notes](./qa-to-notes/) | Saves Claude Code conversations as Obsidian notes (Standard / Direct write), or rewrites fact-checks into a corporate-friendly "extended analysis" format for team sharing (Teams publish). Three modes, one unified note file. |
| [report-generator](./report-generator/) | Generates structured reports from activity logs and git history. Supports weekly, monthly, project summary, and retrospective formats. |
| [newsletter-digest](./newsletter-digest/) | Batch newsletter digestion. Reads all `.eml` files from a folder, auto-clusters by topic, and produces a structured digest with topic summaries, per-article overviews, and deep-read recommendations. Supports recursive subfolders and date filtering. |

### Productivity & Tracking (3)

Cross-session work logging and history analysis.

| Skill | Description |
|-------|-------------|
| [activity-logger](./activity-logger/) | Records work activities from the current session for cross-session aggregation and report generation. |
| [work-log-analyzer](./work-log-analyzer/) | Analyzes work logs. Tracks task progress, queries project history, and traces how decisions evolved. Supports activity aggregation, timeline, TODO, decision tracking, and general search queries. |
| [code-story-teller](./code-story-teller/) | Analyzes git history to tell the evolutionary story of code. Understands the context behind design decisions. |

### MCP Server

Structured data querying capabilities exposed as MCP tools, letting Claude Code directly access your work history.

| Server | Description |
|--------|-------------|
| [skills-query-server](./skills-query-server/) | Provides 7 structured query tools: activity queries, full-text search, activity logging, timeline tracking, TODO extraction, decision tracing, and a work dashboard. Integrates data sources from activity-logger, work-log-analyzer, and qa-to-notes (activity records + QA knowledge notes) via the MCP protocol for direct Claude access. |

**Quick setup:**

```bash
cd ~/.claude/skills/skills-query-server && npm install
claude mcp add -s user skills-query -- npx tsx ~/.claude/skills/skills-query-server/src/index.ts
```

See [skills-query-server/README.md](./skills-query-server/README.md) for details.

### Tooling & Meta-Skills (3)

Tools for managing skills themselves.

| Skill | Description |
|-------|-------------|
| [skill-auditor](./skill-auditor/) | Audits skills for quality, security, and best practices. Use after creating or modifying a skill. |
| [skillshare](./skillshare/) | Syncs skills across AI CLI tools (Claude Code, Cursor, Windsurf, etc.). Single source of truth, used everywhere. |
| [skill-router](./skill-router/) | **Skill discovery and routing hub.** Three modes: smart routing (describe your need, get a skill recommendation), category browse (list all skills), and workflow browse (view predefined multi-skill chains). Your first stop when unsure which skill to use. |

---

## About Dual-AI Review

This repo has a design choice that might look unusual: code review defaults to Gemini, not Claude itself.

The reason is simple — **any model reviewing its own output tends to over-rationalize existing structure**. Claude handles development and context understanding; Gemini plays the conservative reviewer, particularly good at catching logic gaps, edge cases, and insufficient defensive coding.

This simulates the "author vs. reviewer separation" in real teams. The current workflow automatically invokes Gemini review after each small task, iterating on feedback until fully approved. The value isn't in having another AI — it's in shifting review left, making it systematic, and catching issues before they accumulate.

If you don't use Gemini, `code-review-claude` provides a Claude-native fast review alternative.

---

## About the Research Pipeline

When AI helps you evaluate technology, the most common failure mode isn't lack of analytical capability — it's **unverified assumptions packaged as conclusions**. A seemingly thorough feasibility report can rest on 3 implicit assumptions that were never tested, only to collapse during implementation.

The research pipeline (`tech-research-pipeline`) solves this by chaining 8 research skills into a complete verification workflow, where each phase's output becomes the next phase's input:

```
brainstorming → tech-feasibility → assumption-extractor → micro-poc-validator
    → GATE A → critical-research → narrative-auditor → research-cross-validator
    → GATE B → research-synthesis → Decision Document
```

The two gates are the key design decisions:

- **Gate A** (after micro-PoC): If a BLOCKING assumption is empirically disproven, **the entire pipeline stops** — no wasting time researching on top of a failed foundation.
- **Gate B** (after cross-validation): Checks whether all phases' findings converge. If critical claims are contradicted by different verification strategies, they're flagged as DISPUTED rather than forcing a conclusion.

This pipeline was born from a painful lesson: in a ScraperAPI migration project, an apparently thorough feasibility report missed an implicit assumption (nodriver doesn't support WSS connections), which wasn't discovered until weeks into implementation when the entire architecture proved unviable. Had the pipeline existed, Phase 3's micro-PoC would have caught this in 5 minutes on Day 1.

You don't need to run the full pipeline every time. Each skill works standalone — but when the cost of a wrong decision is high enough, the full pipeline helps you find the "unknown unknowns" before committing to implementation.

---

## About Superpowers Plugin Skills

Superpowers plugin skills (writing-plans, executing-plans, systematic-debugging, TDD, etc.) are loaded from the [superpowers](https://github.com/obra/superpowers) plugin. They appear as `superpowers:skill-name` in your session (e.g., `superpowers:writing-plans`, `superpowers:systematic-debugging`). No local copies or symlinks needed.

---

## Quick Start

### Prerequisites

- [Claude Code CLI](https://docs.anthropic.com/en/docs/claude-code)
- [Node.js](https://nodejs.org/) (for Gemini CLI)
- Git

### Installation

**Option 1: Clone directly to skills directory (Recommended)**

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

# Set your API key (get it from https://aistudio.google.com/app/apikey)
export GEMINI_API_KEY="your-api-key-here"

# Make it permanent
echo 'export GEMINI_API_KEY="your-api-key-here"' >> ~/.zshrc  # or ~/.bashrc
```

### Verify Installation

```bash
# Check that Claude Code can see your skills
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

# 2. Trigger the review using natural language in Claude Code
> review the staged files
> check code quality before commit
> do a thorough review
```

Claude will invoke Gemini to analyze your changes and produce a structured report covering:
- Potential bugs or security issues
- Code quality and best practices
- Readability and maintainability
- Improvement suggestions

### Activity Logger

```bash
# Initialize (first time only)
~/.claude/skills/activity-logger/scripts/init_activities.sh init

# Log via Claude Code
> log this activity
> record what I just did

# Or use the CLI directly
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

Activity records can be used with `work-log-analyzer` for cross-project and cross-session aggregation and analysis.

---

## Skill Dependencies

| Skill | Dependencies |
|-------|-------------|
| code-review-gemini | [Gemini CLI](https://github.com/google-gemini/gemini-cli), Git |
| code-review-claude | None |
| code-story-teller | [Gemini CLI](https://github.com/google-gemini/gemini-cli), Git |
| pr-review-assistant | [Gemini CLI](https://github.com/google-gemini/gemini-cli), [GitHub CLI](https://cli.github.com/), Git |
| ui-design-analyzer | None (uses Claude's native multimodal capabilities) |
| interactive-presentation-generator | None (20 style templates bundled) |
| activity-logger | `jq`, Git |
| work-log-analyzer | `jq`, `date` (core features have no external dependencies) |
| skill-auditor | Bash 4.0+ (optional: Gemini CLI for semantic analysis) |
| newsletter-digest | Python 3 (bundled `parse_emls.py` script) |
| skills-query-server | Node.js, `tsx` (registered via `claude mcp add`) |
| All other skills | None |

---

## Creating a New Skill

```bash
# 1. Create a directory
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

# 3. (Optional) Add supporting scripts
mkdir my-skill/scripts

# 4. Validate quality with skill-auditor
> audit my-skill
```

### Skill Directory Structure

```
skill-name/
├── SKILL.md           # Required: skill definition and instructions
├── scripts/           # Optional: supporting shell scripts
│   └── my_script.sh
└── other_files/       # Optional: other resources
```

---

## Troubleshooting

| Error | Likely Cause | Quick Fix |
|-------|--------------|-----------|
| `command not found: gemini` | Gemini CLI not installed | `npm install -g @google/gemini-cli` |
| `GEMINI_API_KEY not set` | API key not configured | `export GEMINI_API_KEY="..."` |
| `No staged changes` | Nothing staged | `git add <files>` |
| `permission denied` | Script not executable | `chmod +x *.sh` |
| `429 Resource exhausted` | API quota exceeded | Wait or upgrade plan |
| `401 Unauthorized` | Invalid API key | Generate new key |

---

## More Documentation

- **[SKILLS_ROADMAP.md](./SKILLS_ROADMAP.md)** — Skills development roadmap
- **[Cheatsheet (EN)](./cheatsheet/cheatsheet-en.md)** · **[速查表 (中文)](./cheatsheet/cheatsheet-zh.md)** — Quick reference

---

## License

MIT
