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

### code-review-gemini

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

## Creating New Skills

1. Create a new directory under the skills folder
2. Add a `SKILL.md` with frontmatter and instructions
3. Add any supporting scripts in a `scripts/` subdirectory
