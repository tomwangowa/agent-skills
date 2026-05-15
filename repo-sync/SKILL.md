---
name: repo-sync
description: Keep any git repo up-to-date by pulling the latest changes and optionally syncing submodules. Also generates a "What's New" digest of recent changes, grouped by top-level directory (or by custom roles defined in .claude/repo-sync-roles.yaml). Works in any repo — no hardcoded paths or team structure required. Use when asked to sync, pull latest, update repo, or show what changed.
compatibility: Designed for Claude Code. Requires git.
allowed-tools: Bash Read Write Edit Glob Grep
---

## Repo Sync & What's New

Two operations: **sync** (pull everything) and **whats-new** (digest of recent changes).

```
/repo-sync              → pull latest, sync submodules if present
/repo-sync whats-new    → digest grouped by component
/repo-sync whats-new <group>   → digest for one specific group only
```

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

### Step 2 — Fetch and pull

```bash
git fetch origin
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

### Step 3 — Sync submodules (if present)

Check whether this repo uses submodules:

```bash
[ -f .gitmodules ] && echo "has_submodules" || echo "none"
```

**If submodules exist:**
```bash
git submodule update --init
git submodule status
```

> **Do NOT use `--remote`** — that advances each submodule to its own latest HEAD, creating
> uncommitted changes in the parent repo. `--init` checks out the exact commit pinned by
> the parent repo, leaving a clean working tree.

**If no submodules**: skip this step silently.

### Step 4 — Record sync timestamp

Write the current UTC timestamp to `.memory/last-sync.txt`:
```
2026-05-15T10:00:00Z
```

Create `.memory/` if it does not exist. (`.memory/` should be in `.gitignore` — check and offer to add it if missing.)

### Step 5 — Report

Print a summary:

| Component | Status | Details |
|-----------|--------|---------|
| main repo | ✅ updated / ⚪ already up-to-date | `<hash> <subject>` |
| submodules | ✅ synced / ⚪ up-to-date / — not used | per-submodule rows if present |

---

## Operation 2 — What's New

Scan recent changes and produce a digest, grouped by component.

### Step 1 — Determine time window

Read `.memory/last-sync.txt` for the previous sync timestamp.
- If the file exists → use that date as `SINCE`
- If not → default to 7 days ago

### Step 2 — Collect recent commits

```bash
git log \
  --since="<SINCE>" \
  --name-only \
  --pretty=format:"COMMIT|%h|%ad|%s" \
  --date=short
```

Parse into a list of `{ hash, date, subject, files[] }` entries.

For each registered submodule (if any):
```bash
git -C <submodule-path> log \
  --since="<SINCE>" \
  --name-only \
  --pretty=format:"COMMIT|%h|%ad|%s" \
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

## Notes

- `.memory/` is local-only and should be gitignored. The skill will offer to add it to `.gitignore` if missing.
- On repos without submodules, the submodule step is silently skipped — no config needed.
- Never force-push or reset submodule HEADs.
- If the user asks to add a new submodule: `git submodule add <url> <path>` then `git submodule update --init`.
