---
name: handoff
description: Write a handoff note for the next session — what is done, what is not, the next step, and what was actually verified. Use when the user says "handoff", "收工", "交接", "留交接", or is about to stop, clear the conversation or switch sessions.
disable-model-invocation: true
---

# handoff

Write a handoff for the next session. It is **not a diary**: it holds what the next person needs to know before continuing, and that must still be true when they read it. The file goes into the project's `.claude/handoffs/` directory, and the next session lists it at start-up.

The configured language is `${user_config.lang}`. If it is `zh-TW`, write the headings and the prose in Traditional Chinese (Taiwan usage); if it is `en`, write them in English. If that value is neither `zh-TW` nor `en` (for example it still looks like a template placeholder because the setting was never saved), use `zh-TW`. Use the headings in the table below exactly, because the next session finds the "next step" by its heading.

| Section | `zh-TW` heading | `en` heading |
| --- | --- | --- |
| task | `## 任務` | `## Task` |
| done | `## 已完成` | `## Done` |
| remaining | `## 未完成` | `## Remaining` |
| next step | `## 下一步` | `## Next` |
| premises | `## 前提（人工確認）` | `## Premises` |
| rules | `## 規矩（不能違反）` | `## Rules` |
| verified | `## 已驗證／未驗證（AI 自述）` | `## Verified` |

## Steps

### 1. Collect (read-only)

Run these and use the output, not memory:

```bash
git rev-parse --show-toplevel
git branch --show-current
git rev-parse --short HEAD
git status --short --branch
git log --oneline --max-count=10
```

If the directory is not a git repository, say so, use the current directory as the root, and omit `repo`, `branch` and `head` below.

### 2. Draft

Write the draft following the sections above. Be brief and accurate; do not paste the whole conversation.

- **Next step:** one concrete first action the next session can take.
- **Premises:** things that must still hold (for example "the decision from yesterday was not reversed"). The next session re-checks them before acting.
- **Verified / not verified:** this is **your own report**, and it must say so.
  - List under *Verified* only what you **ran or read in this turn**, and name the command or the file for each. If you want to call something verified, run the command now.
  - Do **not** write "I reviewed the diff" unless you ran `git diff` in this turn.
  - Everything else goes under *Not verified*, including things you believe are true.
- **Never write** keys, tokens, passwords, connection strings or customer data. Describe them ("the API token in the environment") instead.

### 3. Review gate

Show the **complete draft** and ask: `這樣對嗎？要調整哪裡？` (zh-TW) or `Is this right? What should change?` (en). **Do not write any file until the user confirms.** This gate exists to stop unverified claims from being recorded as verified.

### 4. Write

After the user confirms:

1. Path: `<git root>/.claude/handoffs/<branch>--<YYYYMMDD-HHMMSS>.md`. Use the git root from step 1, or the current directory when there is no git. In `<branch>`, replace every character outside `A-Z a-z 0-9 . _ -` with `-`, and use `no-branch` when there is no branch. Take the timestamp from `date +%Y%m%d-%H%M%S` (local time). Create the directory if needed.
2. Content starts with this frontmatter. The `branch` value is the real name, not the sanitized one. Omit `repo`, `branch` and `head` when there is no git.

```markdown
---
schema: 1
root: <absolute project root>
repo: <absolute git root>
branch: <real branch name>
head: <short commit>
created: <ISO 8601 with time zone, e.g. 2026-10-07T18:30:00+08:00>
task: <one line>
status: in-progress
---
```

   `status` is `in-progress`, `blocked` or `ready-for-review`.
3. Write only this one file. Do not edit other files and do not run `git add` or `git commit`.
4. Report the full path of the file.
