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

**Note:** All skills use the `tm-` namespace prefix as of 2025-01-17. Legacy names (without `tm-` prefix) are supported via symlinks for backward compatibility.

### tm-code-review-gemini

Performs code review using the Gemini CLI.

**Trigger phrases:** "review the changed files", "analyze the code changes", "give me a code review"

**Workflow:**
1. Runs `scripts/review_with_gemini.sh`
2. Reads output from `gemini_review_result.txt`
3. Summarizes findings to the user

**Dependencies:**
- Gemini CLI (`npm install -g @google/gemini-cli`)
- Git repository with commits

**Environment variables:**
- `MAX_DIFF_LINES` - Maximum lines to send to Gemini (default: 5000)
- `GEMINI_MODEL` - Model to use (default: gemini-3-pro)

**Related Documentation:**
- See [NAMING_CONVENTIONS.md](./NAMING_CONVENTIONS.md) for naming standards
- See [MIGRATION.md](./MIGRATION.md) for migration details

## Creating New Skills

**Important:** All new skills must follow the naming conventions defined in [NAMING_CONVENTIONS.md](./NAMING_CONVENTIONS.md).

1. Create a new directory following the naming pattern: `tm-<domain>-<action>[-<qualifier>]`
   - Example: `tm-api-tester`, `tm-db-migrator`, `tm-doc-generator`

2. Add a `SKILL.md` with proper YAML frontmatter:
   ```yaml
   ---
   name: "Skill Display Name"
   id: tm-skill-id
   description: "Brief description..."
   version: "1.0.0"
   namespace: tm
   domain: <domain>
   action: <action>
   qualifier: <qualifier>  # optional
   ---
   ```

3. Add any supporting scripts in a `scripts/` subdirectory

4. Follow the file structure defined in NAMING_CONVENTIONS.md

5. Run `tm-skill-auditor` to validate the new skill before committing
