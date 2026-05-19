# Design — repo-sync last-sync fix

**Date:** 2026-05-19
**Author:** Tom Wang (via Claude brainstorming)
**Status:** Approved
**Scope:** Single-file edit to `repo-sync/SKILL.md`

## Problem

`.memory/last-sync.txt` is written at the END of each sync with the current
UTC timestamp. `/repo-sync whats-new` then reads it as the `--since` for
`git log`. This breaks the common workflow "sync, then immediately ask
what was just pulled":

1. Sync at T finishes; writes T to `last-sync.txt`.
2. User runs `whats-new` 30 seconds later; SINCE = T → 0 commits shown.

Even fixing the write to happen at sync **start** doesn't fully solve it:
`git log --since=<T>` filters on commit author/committer dates, but pulled
commits are typically authored hours or days BEFORE the local sync. They
get excluded.

## Solution — pre-sync HEAD SHA

Replace the timestamp semantics with a git revision:

- At sync **start** (before pull), write current HEAD SHA to
  `.memory/last-sync.txt`.
- `whats-new` reads the file and uses `git log <sha>..HEAD` to show
  exactly what each pull brought in.

This is commit-graph-accurate and immune to author-date skew.

The semantic chosen for the SINCE boundary is **"what the most recent
sync brought in"** (confirmed in brainstorming Q1). Every sync overwrites
the boundary; `whats-new` always reflects the most recent sync.

## Changes to SKILL.md

### A. Operation 1 (Sync) — reorder steps

**Move the timestamp-write to BEFORE the pull, and change what's written:**

- Delete current "Step 5 — Record sync timestamp" (post-sync write).
- Insert new **Step 2 — Snapshot pre-sync HEAD** between current Step 1
  (branch check) and old Step 2 (working-tree preflight):

  ```
  Capture the current HEAD as the boundary for the next whats-new digest:
    mkdir -p .memory
    sha=$(git rev-parse HEAD 2>/dev/null) && [ -n "$sha" ] && printf '%s\n' "$sha" > .memory/last-sync.txt

  For read-only repos (no commit rights), prefer adding `.memory/` to
  `.git/info/exclude` instead of `.gitignore`.
  ```

  Empty-repo guard: `git rev-parse HEAD` fails on a repo with no commits;
  the `[ -n "$sha" ]` check avoids writing a corrupt/empty file in that case.

- Renumber the subsequent steps: old Step 2 → new Step 3 (preflight),
  old Step 3 → new Step 4 (fetch+pull), old Step 4 → new Step 5
  (submodules). Old Step 5 (record-timestamp) is **deleted**. Old Step 6
  (report) **stays as Step 6**.

### B. Operation 2 (Whats-new) — Step 1 redefined

Replace the current "Determine time window" with revision-spec logic:

```
Read `.memory/last-sync.txt`:

- If content matches `/^[0-9a-f]{40}$/`  → check reachability with
  `git merge-base --is-ancestor <sha> HEAD`. If reachable → use range
  form `git log <sha>..HEAD`. If NOT reachable (force-push, branch
  switch) → fall back to `--since="7 days ago"` and emit note
  "stale ref `<sha>`, falling back to 7-day window".
- If content matches `/^\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}Z$/` (legacy
  ISO timestamp) → use `--since=<timestamp>` and emit note "legacy
  timestamp format; will be replaced on next sync".
- If file missing or unrecognized → fall back to `--since="7 days ago"`.
```

### C. Window override (positional)

Extend `/repo-sync whats-new <arg>` parsing:

- If `<arg>` matches `^(\d+)([hd])$` (e.g., `24h`, `7d`) → treat as time
  window override; ignore `.memory/last-sync.txt` for this run and
  translate to git-friendly form:
    - `^(\d+)h$` → `--since="<N> hours ago"`
    - `^(\d+)d$` → `--since="<N> days ago"`
- Otherwise → treat as group filter (current behavior).
- Both can be combined: `/repo-sync whats-new 7d Backend` — window first,
  group second.

### D. Multi-repo whats-new output path

Change default output for cross-repo digest:

- From: `<parent-dir>/.memory/whats-new/<YYYY-MM-DD>.md`
- To:   `<parent-dir>/whats-new/<YYYY-MM-DD>.md`

Per-repo `.memory/last-sync.txt` is unchanged (skill internal state).
Single-repo whats-new output path is unchanged (already lives next to the
repo's own `.memory/`).

Same-day collision rule (`-<HHMM>` suffix) unchanged.

### E. Relax dirty-tree preflight

Current preflight blocks on any non-empty `git status --porcelain`,
including untracked-only output. Relax to:

- Block only when there are **modified or staged tracked files** (status
  codes M, A, D, R, C, U in either column).
- Untracked-only (`??`) lines do NOT block. Proceed silently.

Untracked files are not affected by `git pull --ff-only` and don't
warrant interruption.

## Backward compatibility / migration

- **Legacy `.memory/last-sync.txt`** containing ISO timestamps continues
  to work via the timestamp fallback path. First subsequent sync replaces
  the content with a SHA. No manual migration step.
- **Repos that have never been synced via this skill** behave identically
  to today: 7-days fallback for whats-new.
- **The 6 existing TrendLife repos** with timestamps from today's session:
  next sync auto-upgrades each one.

## Out of scope

- Changing per-repo `.memory/` naming or layout
- `/repo-sync --exclude <repo>` flag (today the user types it)
- Single-repo whats-new path change
- Conflict-resolution rewrite
- Sync history / telemetry
- I18N of skill text

## Verification

After applying:
1. Open `~/Development/TrendLife/`, run `/repo-sync` on a small repo (e.g.,
   `omni-channel`), confirm `.memory/last-sync.txt` contains a 40-char SHA.
2. Run `/repo-sync whats-new` — should show 0 commits if no new commits
   landed (boundary == HEAD), or the exact set of pulled commits if any.
3. Manually edit `.memory/last-sync.txt` back to an ISO timestamp; run
   `whats-new`; confirm legacy fallback message.
4. Delete `.memory/last-sync.txt`; run `whats-new`; confirm 7-day fallback.
5. Run `/repo-sync whats-new 24h` — confirm window override message and
   correct SINCE.

## Pre-mortem

**Scenario:** A team member who installed an earlier version of the skill
pulls the new version mid-workflow. Their `last-sync.txt` files have
timestamps from yesterday. They run `whats-new` first (before next sync).

**Mitigation:** Legacy timestamp fallback in §B handles this — they get
the same answer they would have gotten with the old skill. First sync
afterward upgrades them transparently.
