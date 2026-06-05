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
  sub-repo — useful for spotting "which repo is still dirty?" before wrapping up.

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

## Examples

### Example 1: Status of the current repo

```
User: 掃一下 git
→ bash <skill-dir>/scripts/git-status.sh
```

Sample output (single-repo mode):

```
┌─ git status ───────────────────────────────────────────────┐
│ repo    skills    ~/.claude/skills                         │
│ branch  main   ↑2 ↓0  →  origin/main                       │
│ head    b66b1e7 docs(specs): add git-status-tui design     │
├─ working tree ─────────────────────────────────────────────┤
│ ● staged     1                                             │
│ ● modified   1                                             │
│ ● untracked  3                                             │
│ ● stash      0                                             │
├─ changes ──────────────────────────────────────────────────┤
│  M code-review-claude/SKILL.md  (modified)                 │
│ ?? code-review-codex/  (untracked)                         │
└────────────────────────────────────────────────────────────┘
```

### Example 2: Overview of all repos under a parent directory

```
User: 哪個 repo 還沒乾淨   (run from ~/work, which is not itself a repo)
→ bash <skill-dir>/scripts/git-status.sh
```

Sample output (overview mode):

```
┌─ repos in ~/work ──────────────────────────────────────────┐
│ REPO          BRANCH       STATE     AHEAD/BEHIND   STASH   │
│ api           main         ✗ dirty   ↑1 ↓0          1      │
│ web           feat/login   ✓ clean   ↑0 ↓3          0      │
└──────────────────────────────────────────────────────────────┘
2 repos · 1 dirty · scanned ~/work
```

## Error Handling

The script is defensive by construction — every git lookup is guarded and
degrades to a readable placeholder instead of failing:

- **Not a git repo / no sub-repos** — auto-switches to overview mode; an empty
  parent prints `no git repos found here` rather than an empty frame.
- **Empty repo (no commits)** — `head` shows `no commits yet`.
- **Detached HEAD** — `branch` shows `HEAD detached @ <sha>`; ahead/behind omitted.
- **No upstream** — shows `no upstream` instead of ahead/behind.
- **In-progress merge/rebase/cherry-pick/revert** — a `⚠ … in progress` warning
  line is shown at the top of the panel.
- **Missing `perl`** — width/truncation helpers fail; install perl (preinstalled
  on macOS/Linux). The script does not attempt to self-install dependencies.
- **`set -e` is intentionally NOT used.** Many steps rely on non-zero exits being
  normal (`grep -c` with no match, `[ -n "$x" ] && …`). `set -u` is scoped inside
  `main()` only, so the script stays safe to `source` for testing.

## Security Considerations

- **Read-only.** The script only runs read-only git plumbing/porcelain commands
  (`rev-parse`, `status`, `log`, `rev-list`, `stash list`, `submodule status`).
  It never stages, commits, checks out, fetches, pushes, or deletes.
- **No `eval`, no shelling out to untrusted input.** Filenames from
  `git status` are treated purely as display strings (truncated/padded), never
  executed or re-interpreted.
- **No network.** It never contacts a remote, so it cannot leak credentials or
  hang on network I/O.
- **No file writes.** Output goes to stdout only; the script creates no files.
- **Path display safety.** `$HOME` is abbreviated to `~`; long paths are
  middle-truncated for display only — no path is opened or written.
- **Web-security concerns do not apply.** The skill emits terminal text, not
  HTML, so XSS and CSP are out of scope. Filenames from git are deliberately
  not sanitized or HTML-escaped because they are never interpreted — they are
  inert display strings. The only input validated is whether the current
  directory is inside a git work tree (entry detection).
