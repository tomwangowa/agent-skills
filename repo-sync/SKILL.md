---
name: repo-sync
description: Use when asked to sync, pull latest, update a repo, or show what changed recently. Keeps any git repo up-to-date by pulling the latest changes and optionally syncing submodules. Also generates a "What's New" digest of recent changes. Works in a single repo OR from a non-git parent directory to batch-sync all first-level sub-repos.
compatibility: Designed for Claude Code. Requires git.
allowed-tools: Bash Read Write Edit Glob Grep
---

## Repo Sync & What's New

Two operations: **sync** (pull everything) and **whats-new** (digest of recent changes).

```
/repo-sync                     → pull latest (single repo, or all sub-repos if CWD is not a git repo)
/repo-sync whats-new           → digest grouped by component (single or multi-repo)
/repo-sync whats-new <group>   → digest for one specific group only
```

---

## Entry Detection

**Run this check before every operation.**

Detect whether CWD is inside a git repo:

```bash
git rev-parse --is-inside-work-tree 2>/dev/null
```

| Result | Action |
|--------|--------|
| Prints `true` | CWD is a git repo → proceed to Operation 1 (sync) or Operation 2 (whats-new) as normal |
| Command fails / empty output | CWD is NOT a git repo → switch to **Operation 0 — Multi-Repo mode** |

---

## Operation 0 — Multi-Repo Sync

Used automatically when CWD is not a git repo. Scans first-level subdirectories and batch-pulls all git repos found.

### Step 1 — Scan first-level subdirectories

```bash
for d in */; do [ -d "$d/.git" ] && echo "$d"; done
```

Collect all directories that contain a `.git` folder. Non-git directories are silently skipped.

If **no git repos found**, stop and tell the user:
> No git repositories found in the current directory. Nothing to sync.

### Step 2 — Collect branch info

For each discovered repo, read its current branch:

```bash
git -C <repo-dir> rev-parse --abbrev-ref HEAD 2>/dev/null
```

Also detect the main branch name:

```bash
git -C <repo-dir> symbolic-ref refs/remotes/origin/HEAD 2>/dev/null | sed 's|refs/remotes/origin/||'
```

If that returns empty, fall back:

```bash
git -C <repo-dir> branch -r | grep -E 'origin/(main|master)' | head -1 | sed 's|.*origin/||'
```

Flag any repo whose current branch ≠ main branch with `⚠️`.

### Step 3 — List repos and confirm

Print the discovered repos and prompt for confirmation:

```
Found N git repos:
  • <repo-name>   (main)
  • <repo-name>   (main)
  • <repo-name>   (feature/xyz)  ⚠️ not on main branch

Will pull all repos. Continue? (y/n)
```

Wait for user confirmation. If **n** or cancel → stop. Nothing changes.

### Step 4 — Batch execute

For each repo **in order**, apply the full **Operation 1** logic (Steps 1–6) using `git -C <repo-dir>` for all git commands. That means:
- Check branch → if non-main, present Options A/B/Cancel **for that repo**, wait for response, then continue to next repo
- Check working tree → if dirty, present Options A/B/Cancel **for that repo**, wait for response, then continue to next repo
- Fetch and pull (`--ff-only`; if diverged → present Options A/B/Cancel for that repo)
- Sync submodules if present
- Write `.memory/last-sync.txt` inside that repo

**Pause behavior:** Any problem with a repo (non-main branch, dirty tree, diverged commits) pauses execution for that repo only. Describe the issue clearly, wait for the user's instruction, then continue to the next repo regardless of what the user chose.

**Never abort the entire batch** due to a single repo's problem.

**Skip Operation 1 Step 6** (single-repo report) for each individual repo — the consolidated summary is printed in Step 5 below instead.

### Step 5 — Print summary table

After all repos have been processed, print:

```
| Repo                  | Status        | Details                      |
|-----------------------|---------------|------------------------------|
| Omni-Mobile-Platform  | ✅ updated    | abc1234 fix: auth token      |
| REI-Project           | ⚪ up-to-date |                              |
| hie-rei               | ⚠️ skipped   | stayed on feature/xyz branch |
| kaleida-ai-agent      | ✅ updated    | def5678 feat: new agent      |
```

Status values:
- `✅ updated` — pull succeeded and brought in new commits
- `⚪ up-to-date` — already at latest, nothing to pull
- `⚠️ skipped` — user chose to skip or cancel for this repo
- `❌ error` — unexpected git error (show error message in Details)

---

## Operation 1 — Sync

Pull the latest state of the repo.

### Step 1 — Check current branch

```bash
git rev-parse --abbrev-ref HEAD
```

Detect the main branch name (offline, no network required):
```bash
git symbolic-ref refs/remotes/origin/HEAD 2>/dev/null | sed 's|refs/remotes/origin/||'
```
If that returns empty (HEAD ref not set), fall back to checking for `main` then `master`:
```bash
git branch -r | grep -E 'origin/(main|master)' | head -1 | sed 's|.*origin/||'
```

If **not on the main branch**, present a proposal:

> **Branch mismatch detected**
> You are currently on branch `<name>`. Syncing usually targets the main branch.
>
> **Options:**
> - **A** — Switch to `<main>` first, then pull
> - **B** — Pull into current branch `<name>` instead
> - **Cancel**

Wait for user choice before continuing.

### Step 2 — Preflight: check working tree

Before any pull/rebase/reset, verify the working tree is clean:

```bash
git status --porcelain
```

If output is non-empty (uncommitted changes exist), stop and present:

> **Uncommitted changes detected.** Pulling may conflict or `reset --hard` will discard them.
>
> **Options:**
> - **A** — Stash changes first (`git stash`), then continue
> - **B** — Abort — let me handle my changes first
> - **Cancel**

- **A**: run `git stash`, proceed with pull, then offer `git stash pop` at the end.
- **B / Cancel**: stop. Nothing changes.

If working tree is clean, proceed silently.

### Step 3 — Fetch and pull

```bash
git fetch origin
```

Resolve the pull target:
- If the current branch has a tracking upstream (`git rev-parse --abbrev-ref @{u}` succeeds) → pull from that upstream.
- If no upstream exists (local-only branch) → pull from `origin/<main-branch>` and note: "This branch has no remote upstream — pulling from `origin/<main>` instead."

```bash
git pull --ff-only origin <branch>
```

**If `--ff-only` fails (local branch has diverged)** — collect diverged commits silently:

```bash
git log origin/<branch>..HEAD --oneline
```

Then present a clear proposal:

> **Your local branch has diverged from the remote.**
> These local commits are not on the remote yet:
> - `<hash>` — `<subject>`
>
> **Option A — Keep your commits (recommended)**
> Your commits will be replayed on top of the latest remote changes.
>
> **Option B — Discard your local commits and match the remote exactly**
> Use this only if those commits were accidental or already merged elsewhere.
>
> **Which would you like? (A / B / cancel)**

- **A**: run `git rebase origin/<branch>`. If conflicts → go to [Conflict Resolution](#conflict-resolution).
- **B**: Before resetting, automatically create a safety backup branch:
  ```bash
  git branch backup/<branch>-<YYYYMMDD-HHMMSS>
  ```
  Tell the user: "Created backup branch `backup/<branch>-<timestamp>` — your commits are safe there if you change your mind."
  Then run `git reset --hard origin/<branch>`.
- **cancel**: stop. Nothing changes.

### Step 4 — Sync submodules (if present)

Check whether this repo uses submodules:

```bash
[ -f .gitmodules ] && echo "has_submodules" || echo "none"
```

**If submodules exist:**
```bash
git submodule sync --recursive
git submodule update --init --recursive
git submodule status
```

> **Do NOT use `--remote`** — that advances each submodule to its own latest HEAD, creating
> uncommitted changes in the parent repo. `--init --recursive` checks out the exact commit pinned by
> the parent repo (including nested submodules), leaving a clean working tree.

**If no submodules**: skip this step silently.

### Step 5 — Record sync timestamp

Write the current UTC timestamp to `.memory/last-sync.txt`:
```
2026-05-15T10:00:00Z
```

Create `.memory/` if it does not exist. (`.memory/` should be in `.gitignore` — check and offer to add it if missing.)

### Step 6 — Report

Print a summary:

| Component | Status | Details |
|-----------|--------|---------|
| main repo | ✅ updated / ⚪ already up-to-date | `<hash> <subject>` |
| submodules | ✅ synced / ⚪ up-to-date / — not used | per-submodule rows if present |

---

## Operation 2 — What's New

Scan recent changes and produce a digest, grouped by component.

### Multi-Repo Mode

If Entry Detection determined CWD is **not** a git repo, run the following multi-repo flow instead of the single-repo steps below.

**Step M1 — Scan repos**

Same as Operation 0 Step 1: find all first-level subdirectories containing `.git`.

If no repos found:
> No git repositories found in the current directory.

**Step M2 — Collect digests**

For each repo, apply the single-repo Operation 2 logic (Steps 1–4) using `git -C <repo-dir>` for all git commands. Each repo reads its own `.memory/last-sync.txt` for the time window. Collect the resulting digest data in memory — do not write individual repo digest files.

**Step M3 — Merge and write cross-repo report**

Combine all repos' digest data into a single report. Write to:

```
<parent-dir>/.memory/whats-new/<YYYY-MM-DD>.md
```

Create `<parent-dir>/.memory/whats-new/` if it does not exist. Apply the same same-day collision rule (append `-<HHMM>` suffix) as the single-repo operation.

**Output format:**

```markdown
# What's New — <DATE>
> Changes across N repos since earliest last-sync (or 7 days ago)

## Summary
| Repo                 | Commits | Files changed |
|----------------------|---------|---------------|
| Omni-Mobile-Platform | 4       | 12            |
| REI-Project          | 0       | —             |
| kaleida-ai-agent     | 7       | 23            |

---

## <Repo Name>

> Since <SINCE for this repo>

### Key changes
<1–2 sentence narrative>

### Commits
| Date | Hash | Description |
|------|------|-------------|
| 2026-05-14 | `a1b2c3` | fix(api): correct auth token expiry |

### Changed files
<grouped by subfolder, bullet list>

---

## <Next Repo>
...
```

If a repo has zero commits in its window:
> No changes in `<repo>` since `<SINCE>`.

**If `/repo-sync whats-new <group>` is called in multi-repo mode**, filter each repo's digest to only the matching group. Repos with no matching group changes are still listed in the Summary table with 0 commits.

---

### Step 1 — Determine time window

Read `.memory/last-sync.txt` for the previous sync timestamp.
- If the file exists → use that date as `SINCE`
- If not → default to 7 days ago

### Step 2 — Collect recent commits

```bash
git log \
  --since="<SINCE>" \
  --name-only \
  --pretty=format:"COMMIT%x00%h%x00%ad%x00%s" \
  --date=short
```

Use NUL (`%x00`) as the field delimiter — commit subjects may contain `|`, which would corrupt a pipe-delimited format. Split each `COMMIT…` line on NUL bytes to extract `{ hash, date, subject }`, then collect the following non-empty lines as `files[]` until the next `COMMIT…` marker.

For each registered submodule (if any):
```bash
git -C <submodule-path> log \
  --since="<SINCE>" \
  --name-only \
  --pretty=format:"COMMIT%x00%h%x00%ad%x00%s" \
  --date=short
```

### Step 3 — Determine grouping

**Check for a custom roles config** at `.claude/repo-sync-roles.yaml`:

```yaml
# Example: .claude/repo-sync-roles.yaml
groups:
  Backend:
    - backend/
    - scripts/
  Frontend:
    - frontend/
  Infrastructure:
    - deploy/
    - docker-compose*.yml
    - Makefile
  Documentation:
    - docs/
    - "*.md"
```

**If the file exists** → use those path prefixes to assign each changed file to a group. Files matching no group go into an "Other" bucket.

**If the file does not exist** → fall back to **auto-grouping**: extract the top-level directory of each changed file path and use it as the group name. Root-level files (no directory) are grouped under "root".

> Auto-grouping works well for most repos. Create `.claude/repo-sync-roles.yaml` only if you
> want to merge directories, rename groups, or map glob patterns to logical team names.

### Step 4 — Generate digest

Ensure the output directory exists before writing:
```bash
mkdir -p .memory/whats-new
```

Write to `.memory/whats-new/<YYYY-MM-DD>.md` and also print to the conversation.

**Same-day collision**: if `.memory/whats-new/<YYYY-MM-DD>.md` already exists, append a time suffix instead: `.memory/whats-new/<YYYY-MM-DD>-<HHMM>.md`. Never silently overwrite an existing digest.

```markdown
# What's New — <DATE>
> Changes since <SINCE>

## Summary
| Group | Commits | Files changed |
|-------|---------|---------------|
| Backend | 4 | 12 |
| Frontend | 2 | 5 |
| ... | | |

---

## <Group Name>

### Key changes
<1–2 sentence narrative of the most impactful changes>

### Commits
| Date | Hash | Description |
|------|------|-------------|
| 2026-05-14 | `a1b2c3` | fix(api): correct auth token expiry |

### Changed files
<grouped by subfolder, bullet list>

---

## <Next Group>
...
```

If a specific group was requested (`/repo-sync whats-new Backend`), only output that group's section.

If a group has zero changes:
> No changes in `<group>` since `<SINCE>`.

---

## Conflict Resolution

When rebase stops due to conflicts:

### 1. Identify conflicted files (silently)

```bash
git status --short
git diff --diff-filter=U
```

### 2. Propose a resolution for each file — one at a time

Read each conflicted file with the Read tool. Parse conflict markers internally — never show raw `<<<<<<<` markers to the user.

> **Conflict in `<file-path>`**
>
> **Your version:** `<plain description of your change>`
> **Remote version:** `<plain description of incoming change>`
>
> **Proposed resolution:** `<clean resolved content or description>`
> Reason: `<why this makes sense>`
>
> **Confirm? (yes / no / show me both versions)**

- **yes** → apply with Edit tool, run `git add <file>` internally, move to next file
- **no** → ask what to keep: your version, incoming version, or custom
- **show me both** → display each as plain text, then re-ask

### 3. Continue or abort

After all files resolved:
```bash
git rebase --continue
```

If another conflict round appears, repeat Step 2 for each file. Tell the user which commit is being replayed.

At any point, offer:
> **Want to cancel and return to your previous state? (yes / no)**

If yes → `git rebase --abort`.

---

## Custom Roles Config Reference

Place `.claude/repo-sync-roles.yaml` in the repo root to override auto-grouping:

```yaml
groups:
  <Group Name>:
    - path/prefix/          # matches files under this directory
    - "*.md"                # glob pattern (quote if it starts with *)
    - specific-file.txt     # exact filename
```

Rules:
- First matching group wins — order matters
- Unmatched files fall into "Other"
- Submodule paths can be included as prefixes
- The config is optional; auto-grouping works for most repos without it

---

## Examples

### Example 1: Sync a single repo
```
# Inside a git repo
/repo-sync
```
Expected: pulls latest from origin, syncs submodules if present, prints summary table.

### Example 2: Batch-sync all sub-repos from a parent directory
```
# CWD is ~/Development/MyOrg (not a git repo itself)
/repo-sync
```
Expected: scans first-level subdirectories, lists all git repos with branch info, asks "Continue? (y/n)", batch-pulls all, prints cross-repo summary table.

### Example 3: Cross-repo What's New digest
```
# CWD is ~/Development/MyOrg (not a git repo itself)
/repo-sync whats-new
```
Expected: collects git log from each sub-repo since last sync, generates a combined digest saved to `.memory/whats-new/<date>.md`.

---

## Notes

- `.memory/` is local-only and should be gitignored. The skill will offer to add it to `.gitignore` if missing.
- On repos without submodules, the submodule step is silently skipped — no config needed.
- Never force-push or reset submodule HEADs.
- If the user asks to add a new submodule: `git submodule add <url> <path>` then `git submodule update --init`.
- In multi-repo mode, `.memory/` for the cross-repo whats-new report is created in the **parent directory** (CWD), not inside individual repos.
- In multi-repo mode, each repo's own `.memory/last-sync.txt` is updated independently after sync.
- Non-git subdirectories in CWD are silently skipped — no warning is printed unless zero git repos are found.
