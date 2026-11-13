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

## CLI Plugin Packages

Seven package definitions cover 48 source skills for Claude Code CLI and Codex CLI. The 2026-11-13 refresh used isolated macOS profiles with Claude Code CLI 2.1.323 and Codex CLI 0.167.0; the [acceptance record](docs/validation/skill-plugins/acceptance.json) gives current per-host results and artifact bindings. It revalidated installation, startup preference injection and preference-off behavior; nine other scenarios carry forward from 2026-11-12 because their behavior resources did not change. Claude's earlier packages were installed from the remote GitHub marketplace; the refresh installed both hosts from a local marketplace. A separate remote Git test verified the `session-preferences` 0.1.5 to 0.1.6 update on Codex CLI 0.167.0/macOS 26.6.2 arm64; other Codex versions and platforms remain untested. See the [remote update evidence](docs/validation/skill-plugins/codex-remote-marketplace-update-2026-11-13.json) and [plugin installation and migration](docs/plugins/README.md). Source lifecycle is unchanged. Standalone hooks and journal tools require the bundled runtime and external shared settings described below.

## macOS installer candidate

Build one archive for colleagues without downloading tools or rebuilding plugins:

```bash
python3 scripts/build_plugin_installer.py --output dist/agent-skills-installer-macos.zip
```

The newest validation report for an older archive is [R19](docs/validation/plugin-installer/candidate-r19.md); that archive predates later installer changes and is a historical record, not the current package. This branch updates `session-preferences` to 0.1.6 and builds a ZIP with only the macOS launcher. The Linux and Windows launchers remain in the source repository and are excluded from this ZIP. The local ZIP and release gate passed; the ZIP and plugin changes have not been published.

Extract the archive on macOS and open `install-macos.command` (or run `bash install-macos.command`). A real Python 3.11+ interpreter and an installed Claude Code CLI or Codex CLI are required; the launcher can propose Python installation through an existing supported manager. It does not install either host, a package manager, or credentials. See the [archive guide](installer/README.md) and [validation record](docs/validation/plugin-installer/README.md).

The menus preview source downloads, missing dependencies, plugin installation and optional journal settings at separate confirmation points. Applicable repo packages are checked by default; existing plugins are kept unless an update is selected. Superpowers is strongly recommended and unchecked. Cancel stops later work and retains earlier approved writes. Codex new installs on audited CLI 0.167.0 use the actual JSON receipt and exact installed bytes; existing Codex updates stay blocked. Superpowers prefers each CLI's official catalog: Claude `claude-plugins-official` (observed manifest `7.0.0`, pinned upstream Git payload), Codex `openai-curated` or native-selected `openai-api-curated` (observed manifest `6.3.0`, catalog-relative payload). Versions may differ. Any existing provider, including `7.0.2`, is retained without update, enable, duplicate install or downgrade. Codex official setup must be performed by the native `/plugins` flow; this installer does not seed managed state or add/refresh that reserved catalog. Missing payload hashes or exact CLI/platform/architecture acceptance disable only Superpowers and its dependency proposals. R7 capability records enable only the verified macOS arm64 Claude 2.1.322 official-catalog and Codex 0.167.0 API-curated routes; other environments remain withheld. Installation, exposed entries after restart and real workflow behavior are separate results; the latter two are unverified.

For colleagues already using a company AI endpoint without ChatGPT login, the R7 adapter follows the official catalog exposed by native Codex and preserves existing endpoint/authentication settings. Plugin download access is separate from model endpoint access. Offline tests and a [macOS Codex 0.167.0 native case](docs/validation/plugin-installer/codex-no-account-native-results.md) cover this route; the native case installed Superpowers without login while preserving a synthetic company provider. Actual company connectivity and other-platform acceptance remain unverified; R5 predates the adapter change. See the [company endpoint scenario](installer/README.md). Claude Code 2.1.322 on macOS arm64 also passed [separate logged-in and logged-out native Superpowers installations](docs/validation/plugin-installer/claude-login-matrix-results.md), both at manifest version 7.0.0. R7 incorporates these capability results and minimized evidence summaries; the unchanged ZIP subsequently passed [native first-install and rerun acceptance](docs/validation/plugin-installer/r7-native-acceptance-results.md) in all three macOS arm64 cases.

## Choose a workflow

R5 installation checks on macOS 26.6.2 arm64 / Claude Code 2.1.322 and Codex
0.167.0 cover all 16 own-package host/package pairs across separate cases:
nine Claude packages and seven Codex packages. See the [quality-gates cases](docs/validation/plugin-installer/macos-r5-native-results.md)
and [remaining packages](docs/validation/plugin-installer/macos-r5-remaining-results.md).
These verify installation and complete file contents; Superpowers, other
platforms and hooks/MCP/skill behavior remain unverified.

Examples below name the actual packaged entry points. `/package:skill` is for Claude Code; `$package:skill` is for Codex. An example that explicitly names an entry must be invoked by the person; routing to another package does not install it or count as manual invocation.

### Scenario: turn a vague request into a verified change

Use `technical-decisions`, Superpowers and `quality-gates` when a request such as “add a colleague onboarding flow” still needs decisions. Start with “Explore the requirements and alternatives before implementation; ask one question at a time.” Approve the design, then select a planning/execution method. Ask for a review of the resulting changes; the active host uses `code-review-claude` or `code-review-codex`. Expect an approved design, a task plan, reviewed changes and evidence with remaining gaps. Superpowers must be installed/verified separately for its steps; the other packages retain their independent research/review functions without it. Browsing, model calls and project tests follow the selected workflow's approval rules.

### Scenario: understand a repository and resume work later

Use `repo-workflow` before touching an unfamiliar module. Explicitly run `/repo-workflow:understand-repo <path>` or `$repo-workflow:understand-repo <path>`, then `/repo-workflow:task-bootstrap <task>` or `$repo-workflow:task-bootstrap <task>` to preview a new branch/worktree. Before leaving, explicitly invoke the package's `handoff`; next time invoke its `session-start`, as in `$repo-workflow:session-start`. Expect source-backed understanding, isolated work and a handoff whose premises are rechecked. Git is needed; branch creation and copying local files have their own previews. These manual entries do not run just because a workflow recommends them.

### Scenario: see progress during a long Claude Code session

Add `attention-mod` and `handoff-mod` to Claude Code. `/attention` opens the attention panel; `/handoff-mod:handoff` explicitly creates a handoff, and `/handoff-resume` lists resumable work. Expect a progress panel and a note for the next session. Attention summaries call `haiku` on conversation/tool excerpts and consume model tokens; the handoff mod itself makes no model call, while running its skill uses the session model. Automatic notes/store writes and redaction limits are explained in the [handoff guide](plugins/handoff-mod/README-en.md). Attention requires Claude Code 2.1.312+; both are prototypes and are not Codex options. These are separate from `repo-workflow`'s handoff/session-start entries.

### Scenario: turn work records into a weekly report

Use `work-journal`: “Record today's completed work and the documents actually consulted,” then “Summarize this week's work, with decisions and unfinished items.” Expect dated activity records and a source-backed report. First setup defaults records to `~/.agent-skills/activities`; adding your own notes folder lets `work-log-analyzer` search notes alongside those records. Notes are optional, existing settings are reused, and the installer does not move/read the contents. Journal queries need Node.js/Python and the declared command-line tools; restart the host after MCP registration changes. Add `content-tools` only when turning the report into a presentation.

### Scenario: explain technical work to another audience

Use `content-tools`: “Plan a ten-minute presentation for new colleagues from this outline,” or explicitly run `/content-tools:presentation-planner` / `$content-tools:presentation-planner` with the brief. Expect an audience-aware slide plan followed by the chosen presentation format. “Translate this Markdown to English and Traditional Chinese” uses `md-translate` and preserves code/links. Pair with `work-journal` for recorded evidence or `technical-decisions` for technical analysis. Office extraction can require markitdown and an approved dependency download; publishing and external services remain separate actions.

### Scenario: keep response rules consistent

Use `session-preferences` when you want a consistent language, explanation depth or return-of-control style. Explicitly invoke `/session-preferences:session-preferences` or `$session-preferences:session-preferences` to review/reapply rules, or propose a new preference. `control-return` governs how next steps are offered. Expect session instructions and a separately confirmed personal override when requested. External shared settings remain outside plugin caches; native Windows preference writes/migration are not supplied by this installer.

### Scenario: find a skill or inspect your own

Use `skill-toolbox`: “List my skills and distinguish installed, available and unavailable,” or `/skill-toolbox:skill-router list` / `$skill-toolbox:skill-router list`. For a skill you wrote, ask for a `skill-auditor` audit and expect findings plus explicit dispositions. A catalog entry does not prove installation. `skill-sync` is a separate, manual standalone mirror that can delete destination files; this installer never runs it. `claude-workflow-designer` is Claude-only and is omitted from the Codex package.

| Package | Scenario |
| --- | --- |
| `technical-decisions` | Vague request → design; technical analysis for content |
| Superpowers | Selected planning, TDD and execution steps; separate installation/verification |
| `quality-gates` | Review and verify changes |
| `repo-workflow` | Understand a repository, start work, hand off and resume |
| `attention-mod`, `handoff-mod` | Claude Code progress panel and session handoff |
| `work-journal` | Activity records and weekly reports |
| `content-tools` | Presentations, translation and outward-facing text |
| `session-preferences` | Response rules and next steps |
| `skill-toolbox` | Skill discovery and audits |

## Skills Catalog

The complete, generated inventory and its lifecycle/surface policy live in [SKILLS_CATALOG.md](./SKILLS_CATALOG.md). Use `skill-router` when you want a recommendation rather than a list.

### Manual Code Comprehension Skills

`understand-repo`, `understand-file`, and `understand-function` run only when explicitly invoked. Automatic invocation is disabled in both Claude Code and Codex; router recommendations do not invoke them.

| Scope | Claude Code | Codex |
|-------|-------------|-------|
| Repository | `/understand-repo` | `$understand-repo` |
| Source file | `/understand-file` | `$understand-file` |
| Function or method | `/understand-function` | `$understand-function` |

Include the repository path, file path, or function name after the command. For example: `/understand-file path/to/models.py` in Claude Code or `$understand-file path/to/models.py` in Codex.

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
# From a standalone clone, configure the selected data directories first.
# Review the preview; repeat without --preview to create missing settings.
export AGENT_SKILLS_CONFIG_DIR="$HOME/.config/agent-skills"
PYTHONPATH="$HOME/.claude/skills/runtime" python3 -m agent_skills_runtime.setup \
  --activities "/absolute/activities" --notes "/absolute/notes" --preview
npm --prefix "$HOME/.claude/skills/skills-query-server" ci
npm --prefix "$HOME/.claude/skills/skills-query-server" run build
claude mcp add -s user skills-query -- node "$HOME/.claude/skills/skills-query-server/dist/index.js"
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
- Python 3 for standalone hooks and journal scripts; [Node.js](https://nodejs.org/) for the journal MCP server
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
# First run: select data paths, review the preview, then repeat without --preview.
export AGENT_SKILLS_CONFIG_DIR="$HOME/.config/agent-skills"
PYTHONPATH="$HOME/.claude/skills/runtime" python3 -m agent_skills_runtime.setup \
  --activities "/absolute/activities" --notes "/absolute/notes" --preview

# Once shared settings exist, initialize the selected activity directory.
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

**Record locations**: `sources.activities` in the external `work-journal.json` (active), with `processed/` underneath (archived). `CLAUDE_ACTIVITIES_DIR` explicitly overrides the activity path; relative paths resolve from the settings root. Use the same environment for shell and MCP. Existing settings are preserved; setup does not move old records.

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
| activity-logger | Python 3, `jq`, Git, bundled runtime and external journal settings |
| lesson | Python 3 (standard library only), Git |
| work-log-analyzer | Python 3, `jq`, `date`, bundled runtime and external journal settings |
| skill-auditor | Bash 4.0+ (optional: Gemini CLI for semantic analysis) |
| newsletter-digest | Python 3 (bundled `parse_emls.py` script) |
| skills-query-server | Node.js; source builds need lockfile dependencies and TypeScript (see server README for the supported test toolchain) |
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

After the audit, review every finding, fix it or record an explicit disposition, and re-audit when needed. Package only the clean runtime skill after review. Audit reports and other validation artifacts are development records and should stay outside the production skill unless the skill explicitly needs them at runtime.

### Skill Directory Structure

```
skill-name/
├── SKILL.md           # Required: skill definition and instructions
├── references/        # Optional: on-demand runtime guidance
├── scripts/           # Optional: helper shell scripts
│   └── my_script.sh
└── other_files/       # Optional: runtime resources only
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
