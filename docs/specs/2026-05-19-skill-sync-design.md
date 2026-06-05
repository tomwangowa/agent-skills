# Design: skill-sync

**Date:** 2026-05-19
**Status:** Approved — pending implementation

---

## What We're Building

A Claude Code skill that syncs `~/.claude/skills/` one-way to multiple agent skill folders (codex, gemini, cursor, antigravity). Default dry-run preview shows what would change; user confirms before any files are written. Configurable via two plain-text files; sensible defaults when either is absent.

---

## File Structure

```
~/.claude/skills/
├── skill-sync/
│   ├── SKILL.md
│   └── scripts/
│       └── sync.sh
├── .skill-sync-targets     # user-maintained, gitignored (contains personal paths)
└── .skill-sync-ignore      # user-maintained, can be committed
```

### `.skill-sync-targets` format
One target path per line. `~` is expanded at runtime.
```
~/.codex/skills
~/.gemini/skills
~/.cursor/skills
~/.gemini/antigravity/skills
```

### `.skill-sync-ignore` format
One skill directory name per line (exact match).
```
blog
cheatsheet
skills-query-server
```

**Defaults (used when config file is absent):**

| File | Default value |
|------|--------------|
| `.skill-sync-targets` | `~/.codex/skills`, `~/.gemini/skills`, `~/.cursor/skills`, `~/.gemini/antigravity/skills` |
| `.skill-sync-ignore` | `blog`, `cheatsheet`, `skills-query-server` |

`.skill-sync-targets` must be added to `.gitignore` (repo is public; paths are personal).

---

## Data Flow

```
Trigger skill-sync
      ↓
Read .skill-sync-targets  →  absent? use defaults, print notice
      ↓
Read .skill-sync-ignore   →  absent? use defaults, print notice
      ↓
Pre-flight per target:
  - Expand ~ to absolute path
  - mkdir -p if path doesn't exist
      ↓
Build rsync exclude args:
  --exclude='.git' --exclude='.DS_Store' --exclude='.skill-sync-targets'
  + one --exclude per entry in ignore list
      ↓
rsync --dry-run --delete source/ → each target
Summarise: N added / N updated / N deleted
      ↓
0 changes? → "All targets already up to date." Stop.
      ↓
"Proceed with sync? (y/n)"
  → n: "Sync cancelled." Stop.
  → y: rsync (real) per target
      ↓
Print result table
```

---

## rsync Command

```bash
rsync -av --delete \
  --exclude='.git' \
  --exclude='.DS_Store' \
  --exclude='.skill-sync-targets' \
  [--exclude=skill1 --exclude=skill2 ...] \
  ~/.claude/skills/ \
  <target>/
```

`--delete` keeps targets in exact sync with source — skills removed from source are removed from targets.

---

## Trigger Phrases

- "sync skills"
- "skill-sync"
- "同步 skills"
- "push skills to other agents"
- "更新其他 agent 的 skills"

---

## Error Handling

| Situation | Behaviour |
|-----------|-----------|
| `.skill-sync-targets` absent | Use defaults; print "Using default targets: ..." |
| `.skill-sync-ignore` absent | Use defaults; print "Using default ignore: ..." |
| Target path doesn't exist | `mkdir -p`; continue |
| dry-run shows 0 changes | Print "All targets already up to date."; no confirmation prompt |
| User answers n at confirmation | Print "Sync cancelled."; no files touched |
| rsync fails on one target | Continue remaining targets; mark failed target ❌ in summary |

---

## Result Summary (example)

```
| Target                          | Status     | Changes        |
|---------------------------------|------------|----------------|
| ~/.codex/skills                 | ✅ synced  | +3 ~1 -0       |
| ~/.gemini/skills                | ✅ synced  | +3 ~1 -0       |
| ~/.cursor/skills                | ✅ synced  | +3 ~1 -0       |
| ~/.gemini/antigravity/skills    | ⚪ no change|               |
```

---

## Out of Scope

- Reverse sync (target → source)
- Project-level mode (`.skillshare/` per-repo)
- Content transformation for agent-specific SKILL.md format differences
- Selective per-target ignore lists

---

## .gitignore Update Required

Add to `~/.claude/skills/.gitignore`:
```
.skill-sync-targets
```
