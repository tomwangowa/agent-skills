# Claude Code Skills

**English** | [繁體中文](./README.zh.md)

A collection of Claude Code skills grown out of real-world practice.

These skills aren't about showcasing what AI can do — they solve a specific problem: **as you delegate more work to AI, how do you ensure output quality doesn't degrade as trust increases?**

My approach is to embed engineering discipline into the AI workflow itself — using structured processes to counter cognitive blind spots shared by both AI and humans. Specifically:

- **Structured code review**: Any model over-rationalizes when reviewing its own output, so review is a skill-triggered step — not a verbal assurance. Generic review uses the active runtime's native reviewer: `code-review-claude` in Claude Code and `code-review-codex` in Codex. `code-review-gemini` is deprecated and never runs automatically.
- **Falsification-first**: Research skills require searching for counter-evidence before supporting evidence. This isn't pessimism — it's a systematic defense against confirmation bias.
- **Evidence before assertion**: Before claiming any work is "done", you must run verification commands and confirm the output. Saying "tests pass" requires actually running the tests.

These principles don't require you to agree with my approach — they're independent modules you can use separately. Pick just code review, just research, or just the presentation generator. Each skill is self-contained.

---

## Skills Catalog

The complete, generated inventory and its lifecycle/surface policy live in [SKILLS_CATALOG.md](./SKILLS_CATALOG.md). Use `skill-router` when you want a recommendation rather than a list.

### Skills Maintenance

`skills-catalog.json` is the governance source of truth for tracked top-level skills; `SKILLS_CATALOG.md` is generated from it. After changing the catalog, run `python3 scripts/validate_skills_catalog.py --write`; before committing, run `python3 scripts/validate_skills_catalog.py --check` to verify the catalog, router, both READMEs, sync excludes, and generated index agree.

For a sync preview that makes no filesystem changes, run `bash skill-sync/scripts/sync.sh --dry-run` (add `--no-delete` to preview additive mode). The regular sync command is interactive and may create configured target directories.

### Core Skills

<!-- core-skills:start -->
- [brainstorming](./brainstorming/SKILL.md) — explore a change before implementation.
- [code-review-claude](./code-review-claude/SKILL.md) — default code review.
- [code-review-codex](./code-review-codex/SKILL.md) — Codex-specific review path.
- [completion-gate](./completion-gate/SKILL.md) — verify before claiming completion.
- [handoff](./handoff/SKILL.md) — preserve a session handoff.
- [role-orchestrator](./role-orchestrator/SKILL.md) — coordinate PM → RD work.
- [skill-router](./skill-router/SKILL.md) — discover the right skill or workflow.
- [skill-sync](./skill-sync/SKILL.md) — sync skills to other agent surfaces.
- [tech-research-pipeline](./tech-research-pipeline/SKILL.md) — run a rigorous research workflow.
<!-- core-skills:end -->

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

## About the Layered Code Review Design

**Any model tends to over-rationalize existing structure when reviewing code it generated.** So this repo makes review an explicit, skill-triggered step — with an adversarial checklist and an assumptions list — instead of relying on "let Claude look it over."

### Native reviewers by runtime

- **Claude Code → `code-review-claude`** — Native Claude review with syntax verification, adversarial checks, and an assumptions list.
- **Codex → `code-review-codex`** — Native Codex review with the same local, findings-first discipline.
- **`code-review-gemini`** — Deprecated migration reference. Router, workflow, and pre-commit flows never invoke it.

> **Pre-commit auto-review** uses the native reviewer of the active runtime. Future RDSec endpoint reviewers require an explicit model choice and approval of the diff or data scope before anything is sent externally.

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

Gemini CLI is not used by any code-review flow: `code-review-gemini` is retired. Some unrelated opt-in skills may still use it; skip this section unless one of those skills asks for it.

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

### Code Review (native to the active runtime)

```bash
# 1. Stage your changes
git add src/app.js

# 2. Trigger with natural language in Claude Code
> review the staged files
> check code quality before commit
```

The default trigger invokes `code-review-claude` in Claude Code or `code-review-codex` in Codex. Both return a structured report with:
- 🔴 High / 🟡 Medium / 🟢 Low priority findings
- Language-specific checklist hits (Python / Shell / JS / TS / Java / PHP)
- **Adversarial quick check** — Assumption exposed / Mirror test / Suppression / What breaks this?
- **Assumptions Identified** — unvalidated contracts the code relies on
- **Refactored Patch** (optional, emitted when the diff is ≤ ~200 lines)

`code-review-gemini` is retired. A future RDSec endpoint reviewer will require you to choose the model and approve the exact diff or data scope first.

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
| code-review-gemini | Deprecated migration reference; not a supported review path |
| code-review-claude | No external dependencies |
| code-story-teller | Git |
| pr-review-assistant | [GitHub CLI](https://cli.github.com/), Git |
| ui-design-analyzer | No external dependencies (uses Claude's native multimodal capabilities) |
| interactive-presentation-generator | No external dependencies (20 built-in theme templates) |
| activity-logger | `jq`, Git |
| work-log-analyzer | `jq`, `date` (core functionality has no external dependencies) |
| skill-auditor | Bash 4.0+ (optional: Gemini CLI for semantic analysis) |
| newsletter-digest | Python 3 (bundled `parse_emls.py` script) |
| skills-query-server | Node.js, `tsx` (registered via `claude mcp add`) |
| pptx-to-md | Python 3 + `uv` or `pip` (for markitdown; `uvx` runs ephemerally with no install) |
| repo-sync | Git |
| skill-sync | `rsync` (preinstalled on macOS/Linux) |
| md-translate | No external dependencies |
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
