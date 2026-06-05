# git-status-tui — Design

**Date:** 2026-06-05
**Status:** Approved (brainstorming)
**Author:** Tom Wang

## What we're building

A read-only skill, `git-status-tui`, that renders a clear, panel-style snapshot
of the current git location for use inside an Agent CLI (Claude Code), where an
interactive ncurses TUI (lazygit/gitui) can't be driven by the agent. The skill
runs a single shell script (`scripts/git-status.sh`) that prints a box-drawing
dashboard with ANSI color (graceful symbol fallback when color is unavailable).

It is a static, refreshable snapshot — not interactive navigation. Every
invocation reprints a fresh panel.

## Trigger phrases

`git status` (enhanced), `git 狀態`, `gst`, `掃一下 git`, `repo 狀態`,
`哪個 repo 還沒乾淨`.

## Architecture

- **`SKILL.md`** — tells the agent when to run the script and how to read the
  output. Sole mutation surface of the skill is invoking the script (read-only).
- **`scripts/git-status.sh`** — does all git work and rendering. Pure stdout.
- **Entry detection** — reuse repo-sync's convention:
  `git rev-parse --is-inside-work-tree 2>/dev/null`.
  - prints `true` → **single-repo panel**
  - fails/empty → **parent-directory overview** (scan first-level sub-repos)

## Rendering

- Box-drawing frame (`┌─┐│└┘├┤`), aligned columns.
- Color: clean=green, dirty=red, ahead/behind=yellow.
- **Graceful degradation**: respect `NO_COLOR` and non-tty (`! -t 1`) →
  drop ANSI, use symbols `✓ ✗ ↑ ↓ ●`.
- **CJK / wide-path safety**: compute column widths by display width
  (CJK chars = width 2); truncate over-wide cells with `…`; abbreviate long
  paths with `~` and middle-truncation. (This is the #1 pre-mortem failure:
  misaligned frames on Chinese filenames or deep paths.)

### Single-repo panel (target layout)

```
┌─ git status ─────────────────────────────────────────┐
│ repo    skills              ~/.claude/skills          │
│ branch  main   ↑2 ↓0  →  origin/main                  │
│ head    ea64f74  feat(skills): add review converg…    │
├─ working tree ────────────────────────────────────────┤
│ ● staged      1                                       │
│ ● modified    1                                       │
│ ● untracked   3                                       │
│ ● stash       0                                       │
├─ changes ─────────────────────────────────────────────┤
│  M  code-review-claude/SKILL.md          (staged)     │
│  M  skill-sync/SKILL.md                  (modified)   │
│  ?? code-review-codex/                                │
│  … +2 more                                            │
└────────────────────────────────────────────────────────┘
```

- `changes` lists the first **10** entries; overflow shows `… +N more`.
- `submodules N (M dirty)` line appears only when submodules exist.

### Parent-directory overview (target layout)

```
┌─ repos in ~/work ──────────────────────────────────────────┐
│ REPO          BRANCH       STATE     AHEAD/BEHIND   STASH   │
│ api           main         ✗ dirty   ↑1 ↓0          1      │
│ web           feat/login   ✓ clean   ↑0 ↓3          0      │
│ infra         main         ✓ clean   —              0      │
└──────────────────────────────────────────────────────────────┘
3 repos · 1 dirty · 1 behind · scanned ~/work
```

## Data sources (read-only git commands)

- repo root / name: `git rev-parse --show-toplevel`
- branch / detached: `git symbolic-ref --short HEAD` (fallback `rev-parse --short HEAD`)
- upstream + ahead/behind: `git rev-list --left-right --count @{u}...HEAD` (guarded)
- head summary: `git log -1 --format='%h %s'`
- working tree: `git status --porcelain=v1` (parse staged/modified/untracked)
- stash count: `git stash list | wc -l`
- in-progress op: presence of `.git/MERGE_HEAD`, `rebase-merge/`, `rebase-apply/`, `CHERRY_PICK_HEAD`
- submodules: `git submodule status` (count + dirty)

## Edge cases

| Case | Behavior |
|------|----------|
| detached HEAD | branch field shows `HEAD detached @ <sha>`, no ahead/behind |
| no upstream set | show `no upstream` instead of `↑↓ → origin/…` |
| merge/rebase/cherry-pick in progress | red warning line at top: `⚠ rebase in progress` |
| empty repo (no commits) | head field shows `no commits yet` |
| parent mode, no sub-repos found | print a one-line notice, not an empty frame |
| no submodules | omit the submodules line entirely |

## Key decisions

- **Read-only.** Never add/commit/stash/checkout. Pure dashboard.
- **No auto-fetch.** ahead/behind reflects locally-known remote state; do not
  hit the network (avoids hangs/latency). For fresh remote state, use repo-sync
  to pull first. A `--fetch` flag is deferred (YAGNI).

## Out of scope

- Interactive navigation (rejected approach B — agent can't drive a live TUI).
- Mutating git state.
- Showing diff content.
- Auto fetch/pull (delegated to repo-sync).

## Pre-mortem

Most likely failure in 12 months: frame misalignment when filenames/paths
contain CJK or are very long. Mitigated by display-width-aware column sizing
and middle-truncation (see Rendering → CJK / wide-path safety).
