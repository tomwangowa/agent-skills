---
name: skill-sync
description: Sync ~/.claude/skills/ to other agent skill folders (codex, gemini, cursor, antigravity). One-way overwrite with dry-run preview before writing. Configure targets via .skill-sync-targets and excludes via .skill-sync-ignore; sensible defaults when files are absent. Use when syncing skills across AI tools, "sync skills", "skill-sync", "同步 skills", "push skills to other agents", "更新其他 agent 的 skills".
---

# Skill Sync

One-way sync of `~/.claude/skills/` to configured agent skill folders.
Always runs a dry-run preview first, then asks for confirmation before writing any files.

## When to Use

- "sync skills"
- "skill-sync"
- "同步 skills"
- "push skills to other agents"
- "更新其他 agent 的 skills"
- "sync to codex / gemini / cursor"

## Instructions

When triggered, run:

```bash
bash ~/.claude/skills/skill-sync/scripts/sync.sh
```

Present the dry-run output to the user. The script will prompt for confirmation — wait for the user's response (y/n). After sync completes, display the result summary table from the script output.

## Config Files (optional)

Both files live in `~/.claude/skills/`. If absent, defaults are used.

**`.skill-sync-targets`** — one target path per line (`~` is expanded):
```
~/.codex/skills
~/.gemini/skills
~/.cursor/skills
~/.gemini/antigravity/skills
```

**`.skill-sync-ignore`** — one skill directory name per line to exclude:
```
blog
cheatsheet
skills-query-server
```

**Defaults (when files are absent):**
- Targets: `~/.codex/skills`, `~/.gemini/skills`, `~/.cursor/skills`, `~/.gemini/antigravity/skills`
- Ignore: `blog`, `cheatsheet`, `skills-query-server`

Note: `.skill-sync-targets` is gitignored (contains personal local paths).
