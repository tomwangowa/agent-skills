---
name: git-status-tui
description: Use when you want a clear, at-a-glance view of git state in the Agent CLI — "git status" (enhanced), "git 狀態", "gst", "掃一下 git", "repo 狀態", "哪個 repo 還沒乾淨". Renders a box-drawing panel of the current repo (branch, ahead/behind, staged/modified/untracked, stash, in-progress ops) or, from a parent directory, a one-line-per-repo overview. Read-only; never fetches.
compatibility: Designed for Claude Code. Requires git and perl.
allowed-tools: Bash
---

## git status TUI

Read-only git status dashboard. Two modes, auto-detected by CWD:

- **Inside a git repo** → detailed single-repo panel.
- **In a directory that is not a repo** → overview table of every first-level
  sub-repo (good for "which repo is still dirty?" before wrapping up).

### How to run

```bash
bash <skill-dir>/scripts/git-status.sh          # auto-detect mode
bash <skill-dir>/scripts/git-status.sh --help   # usage
```

Run the script and present its stdout to the user verbatim (it is already
formatted). Do not re-summarize the panel into prose unless asked.

### What it shows

**Single panel:** repo name + path, branch (or `HEAD detached @ sha`),
ahead/behind vs upstream (or `no upstream`), last commit, submodule summary,
counts for staged / modified / untracked / stash, an in-progress-operation
warning (`⚠ merge in progress`), and the first 10 changed paths (`… +N more`
when there are more).

**Overview:** one row per repo — name, branch, `✓ clean` / `✗ dirty`,
ahead/behind, stash — plus a summary line.

### Boundaries

- **Read-only.** Never stages, commits, stashes, checks out, fetches, or pulls.
- **No network.** Ahead/behind reflects locally-known remote state; run
  `repo-sync` first if you need fresh remote tracking.
- Color auto-degrades to symbols (`✓ ✗ ↑ ↓ ●`) when `NO_COLOR` is set or
  stdout is not a TTY.
- A non-repo directory nested inside an outer repo renders the **outer repo**
  (single mode), not an overview — same detection rule as `repo-sync`.
