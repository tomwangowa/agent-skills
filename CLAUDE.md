# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Repository Overview

This is a Claude Code Skills repository containing custom skills that extend Claude Code's capabilities. Skills are user-defined prompts that can be triggered by specific phrases.

## Skill Structure

Each skill resides in its own directory with the following structure:
```
skill-name/
├── SKILL.md           # Skill definition (name, description, instructions)
└── scripts/           # Supporting scripts (optional)
```

### SKILL.md Format

The `SKILL.md` file uses YAML frontmatter for metadata:
```yaml
---
name: Skill Name
description: Brief description of when to use this skill
---
```

Followed by markdown content containing:
- Instructions for when and how to activate the skill
- Examples of trigger phrases
- Step-by-step workflow

## Available Skills

### Code Review

- **code-review-claude** — Default reviewer: native code review with adversarial pass, assumptions list, and optional refactored patch. Broader coverage, zero hallucination (2026-04 benchmark: 2.3×–5.0× gemini's findings across 6 demos)
- **code-review-gemini** — Optional depth / final-validation reviewer (Gemini CLI). Useful when a fully worked refactored patch is needed, or as a second-opinion pass after code-review-claude

### Multi-Agent Roles

- **role-orchestrator** — Orchestrate PM → RD pipeline with subagent dispatch, project profile calibration, and user-approval gates
- **role-pm** — PM role: produce size-calibrated requirements artifacts (bullets → user stories → full PRD)
- **role-rd** — RD role: produce size-calibrated design artifacts (code plan → design doc → architecture doc)

### Design & Development Process

- **brainstorming** — Socratic design dialogue before any implementation; produces approved design doc
- The following skills are provided by the **superpowers plugin** (use `superpowers:skill-name` format): `test-driven-development`, `systematic-debugging`, `writing-plans`, `executing-plans`, `dispatching-parallel-agents`, `subagent-driven-development`, `requesting-code-review`, `receiving-code-review`, `finishing-a-development-branch`, `using-git-worktrees`, `writing-skills`

### Productivity & Analysis

- **activity-logger** — Record work activities for cross-session aggregation
- **work-log-analyzer** — Query work logs and project history
- **code-story-teller** — Analyze git history to tell code evolution stories
- **pr-review-assistant** — Review pull requests with structured feedback
- **critical-research** — Falsification-first research that seeks counter-evidence before supporting evidence
- **tech-feasibility** — Evaluate whether a technology can solve a specific problem before committing to implementation
- **assumption-extractor** — Extract explicit and implicit assumptions from technical documents, classify by risk and verification status
- **micro-poc-validator** — Empirically validate technical assumptions through minimal code experiments (5-30 min spikes)
- **research-cross-validator** — Cross-validate technical claims using multiple independent strategies (docs, counter-evidence, source code)
- **tech-research-pipeline** — Orchestrate full 8-phase research workflow chaining all research skills with gate checks
- **research-synthesis** — Synthesize findings from multiple research skills into ADR-style decision documents
- **codebase-audit** — Claims-first audit: extract documentation claims and verify against code
- **narrative-auditor** — Audit external narratives against primary sources, or speak as user's AI proxy
- **report-generator** — Generate status reports, project summaries, and retrospectives from activity logs and git history
- **completion-gate** — Evidence-based verification + adversarial self-check before claiming done

### Content Generation

- **presentation-planner** — Narrative strategy and slide planning before presentation generation
- **interactive-presentation-generator** — Generate Marp/Slidev/reveal.js presentations
- **ui-design-analyzer** — Analyze UI/UX design from screenshots
- **md-translate** — Translate markdown files to English and Traditional Chinese; auto-detects source language; generates `-en.md` and `-zh.md`
- **pptx-to-md** — Convert PPTX/DOCX/XLSX/PDF to Markdown via Microsoft markitdown; supports single file, batch, and print-only modes
- **repo-sync** — Pull latest + submodule sync for any repo; generates What's New digest grouped by top-level directory or custom `.claude/repo-sync-roles.yaml`
- **git-status-tui** — Read-only git status dashboard rendered as a box-drawing TUI panel; single-repo detail or parent-directory multi-repo overview. CJK-aware alignment, auto-degrades color to symbols, never fetches.
- **deai-voice-rewrite** — On-demand de-AI-ify + plain-language + Tom's-voice rewriter for outward-facing content (slides/blog/newsletter/posts). Two hard guards: fact-freeze (numbers/ports/filenames/identifiers never change) and flag-don't-fix (suspicious terms flagged for the user, not silently edited). Output = rewrite + fact-freeze checklist + flagged-terms list. Companion output-style `deai-tom` (tracked in this repo at `output-styles/deai-tom.md`, symlinked to `~/.claude/output-styles/`, toggled via `/config`) regulates ongoing responses using the same rules; SKILL.md is the single source of truth.

### Meta

- **skill-sync** — one-way **mirror** of `~/.claude/skills/` to other agent folders (codex, gemini, cursor, antigravity) via `rsync --delete` (target files not in source are removed); dry-run preview shows deletion count before `y/N` confirmation (defaults N); configurable via `.skill-sync-targets` (gitignored) and `.skill-sync-ignore` (committed, defaults include symlink protection for `spec-generator`)
- **skill-auditor** — Audit skills for quality, security, and best practices
- **skill-router** — Unified skill discovery and routing: smart match, category browse, workflow browse

## Creating New Skills

1. Create a new directory with a descriptive kebab-case name
   - Example: `api-tester`, `db-migrator`, `doc-generator`

2. Add a `SKILL.md` with YAML frontmatter:
   ```yaml
   ---
   name: "Skill Display Name"
   description: "Brief description of when to use this skill"
   ---
   ```

3. Add any supporting scripts in a `scripts/` subdirectory

4. Run `skill-auditor` to validate the new skill before committing
