---
name: lesson
description: "Use when the user wants to record, list, retire, promote or migrate lessons learned (/lesson); when a bug is fixed, an assumption is disproved or the user corrects the agent and work reaches a natural pause; and at wrap-up together with activity-logger."
---

# Lesson

Capture lessons learned during design, coding and debugging, and make sure later sessions actually read them.

Each lesson is one markdown file with a one-line `rule` (loaded at session start) and a long background (for the user to read in a note tool). All deterministic work is done by `scripts/lesson.py`; this file only covers the judgment and conversation parts.

`<script>` below means `python3 <skill-dir>/scripts/lesson.py`, where `<skill-dir>` is the base directory shown when this skill loads.

## Always

- Never write, retire, promote or migrate without the user's explicit confirmation of the exact draft.
- Never store lesson data inside the skills repository. The lessons folder is set by `config.json` (gitignored); do not print or commit its path.
- Reply in the user's language. Lesson text follows the language the user used.
- Do not put secrets, tokens or customer data into a lesson. The script rejects obvious patterns; you still have to judge.

## Drafting a rule

A rule is one line, at most 120 characters, that says what to do or avoid and when it applies.

- A rule: `呼叫 X API 要檢查 body 的 error code，不能只看 HTTP status`
- Not a rule: `今天 debug 花了很久才發現 API 回 200 但其實失敗`（這是經過，放進背景）

If you cannot sharpen the draft into a rule, do not record it. Suggest keeping it as a note instead.

## `/lesson add`, or a proposal from the agent

1. Draft in one message: `rule`, scope (`global` or `project` plus which project), and one or two sentences of why.
2. Check it: `<script> add --json - --dry-run` with the entry JSON on stdin. Fix anything it rejects.
3. Wait for the user: 好 / 改 / 不記. Only after "好":
4. Write: `<script> add --json - <<'EOF'` … `EOF` with the entry JSON. Fields: `rule`, `scope`, `project` (only for project scope), `why`, `background`, `slug` (short English, `[a-z0-9-]`), `by` (`claude`, `codex`, `gemini` or `user`). Report the file name it prints.

Use the current project name from `git rev-parse --show-toplevel` (folder name), or the current folder name outside git.

## When to propose

Propose only at a natural pause (a bug fixed and verified, a task finished), never in the middle of a chase, and only for:

- a pitfall you hit and fixed,
- an assumption that turned out to be wrong,
- something the user corrected you on.

At most two proposals per pause; keep the ones that generalise best. Skip one-off situations.

At wrap-up, `activity-logger` includes lesson proposals in its own closing question so the user answers once (see that skill).

## Other commands

- `/lesson setup`: ask which folder to use (suggest `~/lessons`; any folder works, including one inside a note vault). Run `<script> setup --dir <path>` (add `--create` only if the user agrees to create it). Then run `<script> snippet` and show the result. For each agent entry file that exists (`~/.claude/CLAUDE.md`, `~/.codex/AGENTS.md`, `~/.gemini/GEMINI.md`), show the exact addition and append it only after the user confirms that file.
- `/lesson list [project]`: run `<script> list [--project NAME]` and show the result. Mention conflict copies and unparsable files if any.
- `/lesson retire <file> [reason]`: run `<script> retire <file> --reason "<reason>"` after the user confirms which lesson.
- `/lesson promote <file>`: only for project-scope lessons. Draft a de-identified version (remove personal paths, names, internal hostnames, customer details), show it, and append it to the project's own doc (default `docs/lessons.md`) only after the user confirms. De-identification is best effort, so tell the user to read it. The source lesson stays unchanged.
- `/lesson review`: run `list`, then propose merges, rewrites or retirements one at a time (duplicates, rules longer than they need to be, rules that no longer match how the project works). A merge is one `add` plus retiring the old files. Every change needs confirmation.
- `/lesson migrate --from <memory-dir>`:
  1. `<script> migrate --from <dir> --plan` lists `feedback` memory files as JSON.
  2. Draft a `rule` and a scope guess for each and show a table (original file, new rule, scope). Guesses only; the user decides.
  3. After the user edits and confirms, write the mapping JSON (`[{"file", "rule", "scope", "project"}]`) to a temporary file and run `<script> migrate --from <dir> --apply <mapping.json>`.
  4. Do not touch the original files. Tell the user they are still loaded by built-in memory until they are archived, and ask about archiving only after the digest is confirmed to load correctly.

## Session start

Agents run `<script> digest` as their first action (via the entry-file snippet) and quote its first line in the first reply. If that line starts with `lessons: ⚠` or says setup is missing, tell the user in one sentence and continue.

## Examples

### Example 1: The agent proposes a lesson after a fix

```text
Agent: 這個坑值得記嗎？
       rule：呼叫 X API 要檢查 body 的 error code，不能只看 HTTP status
       範圍：全域
       為什麼：這次 200 回應裡帶著失敗碼，只看 status 會漏掉。
User:  好
Agent: (runs the add command with the entry JSON on stdin)
       已寫入 2026-09-30-api-error-code.md
```

### Example 2: Migrating existing feedback memories

```text
User:  /lesson migrate --from ~/.claude/projects/<project>/memory
Agent: (runs migrate --plan, then shows a table: original file, new rule, scope guess)
User:  照這樣，第 2 條改成專案
Agent: (runs migrate --apply with the confirmed mapping)
       written: 9  skipped(already migrated): 0
       原檔沒有動。
```

## Error Handling

- `error: ...` on stderr from the script is a real failure. Show it to the user; do not retry with different input silently.
- No `config.json`: every command except `setup` stops and points to `/lesson setup`.
- Lessons folder missing or unreadable (a sync folder that is not mounted is the usual cause): `digest` prints `lessons: ⚠ 讀不到資料夾`, `add` exits with an error. Say so instead of creating a folder.
- Files that cannot be parsed (empty, half-synced, broken frontmatter): `digest` skips them and shows `⚠ 略過 N 個`. Report the count; do not try to repair them.
- Invalid entry (empty or multi-line rule, rule over 120 characters, missing project for project scope, secret-looking text): `add` exits with code 2 and a message. Fix the draft with the user, then run it again.
- `retire` on a missing or already-retired file, and `migrate` with a missing `--from` folder, exit with code 1 and a message.
- If the digest line starts with `lessons: ⚠` or says setup is missing, tell the user in one sentence and continue the session.

## Security Considerations

- **Data location**: lessons live in the folder named by `config.json`, never inside the skills repository. `config.json` is gitignored and may contain an account name in its path, so do not print or commit it.
- **Input safety**: entries arrive as JSON on stdin and are parsed with `json.loads` only. `add` validates every entry (single-line rule, length, scope, project) before it writes anything. Nothing is evaluated or interpolated into a shell command; pass entries through a quoted heredoc (`<<'EOF'`).
- **Secret scan**: `add` rejects text that matches common API key, token, password and private key patterns. The list is best effort, so still judge the text yourself.
- **File path safety**: `retire` accepts a bare `.md` file name and rejects anything containing `/` or `\`. `add` writes only inside the configured folder and never overwrites an existing file. `setup` will not replace an existing `config.json` without `--force`.
- **Frontmatter integrity**: values are quoted and escaped, so a rule containing quotes or colons cannot break the file structure.
- **Trust boundary**: `digest` output is loaded into the agent as instructions, so anyone who can write to the lessons folder can steer every session. Keep the folder private. `digest` cuts any rule longer than 120 characters, but it does not otherwise filter content.
- **Network**: the script makes no network calls and calls no external service.
- **Publishing**: `promote` copies content into a project document that may be public. Sanitize it first (remove personal paths, names, hostnames, customer details); this is best effort, so the user must read the draft before confirming.
