---
name: skill-sync
description: >-
  Use when syncing ~/.claude/skills/ to other agent skill folders (codex, gemini, cursor, antigravity). One-way mirror with --delete (target-side files not in source are removed) — always shown in a dry-run preview before any write. Configure targets via .skill-sync-targets and excludes via .skill-sync-ignore; sensible defaults when files are absent. Triggers: "sync skills", "skill-sync", "同步 skills", "push skills to other agents", "更新其他 agent 的 skills".
---

# Skill Sync

One-way mirror of `~/.claude/skills/` to configured agent skill folders.
Always runs a dry-run preview first, then asks for confirmation before writing any files.

## ⚠️ Important: This is a Mirror, Not Additive Sync

- **`--delete` is active.** Files in target folders that don't exist in the source will be **deleted**. If you keep an agent-specific skill only in `~/.codex/skills/` (and not in `~/.claude/skills/`), it will be removed on first sync. Add it to source first if you want to keep it.
- **Symlinks in source are dereferenced (`rsync -L`)** so the actual content (not the link) is copied. To avoid leaking content from symlinked-in paths (e.g., `~/.config/...`), add those entries to `.skill-sync-ignore`. The defaults already exclude `spec-generator` for this reason.
- The **dry-run preview always runs first** and explicitly counts deletions per target before asking for confirmation.

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

Present the dry-run output to the user. The script will prompt for confirmation — wait for the user's response (`y`/`yes` to proceed, anything else cancels; default is `N`). After sync completes, display the result summary table from the script output.

## Examples

### Example 1: First-time sync with defaults

```
User: "sync skills"
```

Expected behavior:

1. Script reads `.skill-sync-ignore` (committed file) and falls back to default targets (`~/.codex/skills`, `~/.gemini/skills`, `~/.cursor/skills`, `~/.gemini/antigravity/skills`) because no `.skill-sync-targets` exists yet.
2. Pre-flight: any missing target directories are created.
3. Dry-run preview shows the file list per target with a `⚠️  Will DELETE N item(s)` count if any target-side files would be removed.
4. Prompt: `Proceed with sync? (y/N)` — typing `y` or `yes` proceeds; any other input cancels.
5. After sync, the summary table reports `✅ synced` or `❌ <error>` per target.

### Example 2: Selective sync via custom targets

```
User: "sync skills to codex only"
```

The user (or assistant) writes a temporary `.skill-sync-targets`:

```
~/.codex/skills
```

Then runs the same `sync.sh`. Only the listed target is synced. The file is gitignored so the customization is local-only.

### Example 3: Cancelling on unexpected deletions

```
User: "sync skills"
```

The dry-run reports:

```
→ ~/.codex/skills
   ⚠️  Will DELETE 3 item(s) in target not present in source
deleting my-codex-experiment/SKILL.md
deleting my-codex-experiment/
deleting legacy-skill.md
```

The user spots that `my-codex-experiment` is something they want to keep. They type `n` to cancel, then either (a) copy `my-codex-experiment/` into `~/.claude/skills/` so future syncs preserve it, or (b) add `my-codex-experiment` to `.skill-sync-ignore`.

## Config Files (optional)

Both files live in `~/.claude/skills/`. If absent **or empty/comments-only**, defaults are used.

**`.skill-sync-targets`** — one target path per line (`~` is expanded, `#` starts a comment):
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
spec-generator
```

**Defaults (when files are absent or empty):**
- Targets: `~/.codex/skills`, `~/.gemini/skills`, `~/.cursor/skills`, `~/.gemini/antigravity/skills`
- Ignore: `blog`, `cheatsheet`, `skills-query-server`, `spec-generator`

Note: `.skill-sync-targets` is gitignored (contains personal local paths). `.skill-sync-ignore` is committed because the defaults (including the symlink protection for `spec-generator`) should be the same for everyone.

## Error Handling

The script uses `set -euo pipefail`. Failures surface in two places:

- **Dry-run errors** — if `rsync --dry-run` fails for a target (e.g., permission denied, target path invalid), the script prints `→ <target>  ⚠️  rsync error:` followed by indented stderr and continues with the next target. No write happens; the user can fix the issue and re-run.
- **Real sync errors** — stderr from `rsync` is captured per target. On failure, the summary row shows `❌ <first error line>` instead of `✅ synced`. Other targets are still attempted.

Other failure modes the script handles cleanly:

| Situation | Behavior |
|---|---|
| `.skill-sync-targets` exists but is empty or comments-only | Falls back to defaults with a `ℹ️` notice |
| `.skill-sync-ignore` exists but is empty or comments-only | Falls back to defaults with a `ℹ️` notice |
| Config file lacks a trailing newline | Last line is still captured (`read \|\| [[ -n "$line" ]]` pattern) |
| Target directory does not exist | Created via `mkdir -p` in pre-flight |
| User answers anything other than `y`/`yes`/`Y`/`Yes` at the prompt | Script exits with `Sync cancelled.` and zero changes |
| `mktemp` for stderr capture leaks | Cleaned up via `trap … EXIT` |

What the script does **not** do: it does not roll back a partially completed sync. If `rsync` aborts halfway through a single target (rare with `--delete`), that target may be in a mixed state. Re-run after fixing the underlying issue.

## Security Considerations

**Scope of risk.** This skill writes to and deletes from filesystem paths the user configures via `.skill-sync-targets`. It does not make network calls, generate HTML, evaluate user input as code, or read credentials. The destructive filesystem side is the relevant attack surface; web-side concerns (XSS, CSP) are not applicable.

### Destructive Behavior — `--delete`

- `rsync --delete` removes target-side files not present in the source. The dry-run preview surfaces this with a `⚠️  Will DELETE N item(s)` count before asking for confirmation.
- The confirmation prompt defaults to `N`: blank input, `n`, `no`, and any unrecognized input cancel. Only `y` / `yes` / `Y` / `Yes` proceeds, which is enforced via a `^[Yy]([Ee][Ss])?$` regex (no fuzzy matches accepted).
- Users keeping agent-specific skills only in a target folder must add them to the source or to `.skill-sync-ignore` before running, otherwise they will be deleted.

### Input Sanitization & Validation

- **Config file lines** are sanitized before use: CR (`\r`) is stripped to handle CRLF editors, inline `#` comments are removed, and surrounding whitespace is trimmed. Empty results are skipped silently. This prevents accidental misinterpretation of well-meaning but messy edits.
- **Path validation is intentionally minimal**: the file is user-owned and gitignored, so the threat model assumes the user trusts their own config. The script will not validate that target paths are "sensible" — if you write `/`, it will try to mirror to `/`. Treat the file as you would treat a shell script you wrote yourself.
- **No directory-traversal sanitization** is applied to target paths. `../` segments and absolute paths are passed through. Again: user-owned config, user-trusted.
- **Shell escaping**: all expansions (`"$target"`, `"$SKILLS_DIR/"`, `"${exclude_args[@]}"`) are quoted to escape paths containing spaces or special characters. The script does not use `eval` and does not pass user input through `bash -c`.

### Symlink Following — `rsync -L`

- `-L` dereferences symlinks in the source tree, copying the *content* of the link target into each sync destination.
- This can leak content from outside `~/.claude/skills/` (e.g., a symlink pointing into `~/.config/`) into every target folder.
- Mitigation: the default `.skill-sync-ignore` excludes `spec-generator` because it is a known symlink pointing outside the source tree. Add any new such symlink names to `.skill-sync-ignore` before running.

### Path Handling

- Target paths from `.skill-sync-targets` are expanded for a leading `~`/`~/` only. Other users' `~user` are not expanded — paths must be absolute or use the current user's home.
- `mkdir -p` is used for missing targets; it does not follow into existing files masquerading as directories. The script aborts via `set -e` if `mkdir` fails.

### Public-Repo Hygiene

- `.skill-sync-targets` is **gitignored**; it contains personal local paths and must never be committed. The repo at `github.com/tomwangowa/agent-skills` is public.
- `.skill-sync-ignore` **is** committed because the defaults (especially the symlink-protection entries) should be shared across all users of this skill.
- No credentials, tokens, or API keys are read or written by this skill. If a user keeps such material inside `~/.claude/skills/` (which they should not), this skill will dutifully replicate it to every target. Audit the source folder periodically with `grep -r -E 'AKIA|SECRET|TOKEN' ~/.claude/skills/`.

### What This Skill Will Not Do

- It will not run any code from the synced skills.
- It will not modify the source folder.
- It will not write outside the user-configured target paths.
- It will not bypass the dry-run preview — every run shows the preview before the prompt.

### Non-Applicable Threats

- **XSS / CSP / HTML escaping** — not applicable; this skill produces no HTML or web output.
- **API credential validation** — not applicable; no external services are called.
- **Network MitM** — not applicable; all I/O is local filesystem.
