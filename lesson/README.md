# lesson

Record lessons learned (yours and your coding agent's) as one small markdown file each, and load a short, capped digest of them at the start of every agent session.

- A lesson has a one-line `rule` that agents load, and a long background that you read in any notes tool.
- Lessons are stored in a folder you choose, never inside this repository.
- The same script serves every agent: each agent's global instruction file tells it to run `digest` first.

## Requirements

- Python 3 (standard library only)
- Git (used to detect the current project name)

## Quick Start

Run these from this skill's folder, or ask your agent to run `/lesson setup`.

```bash
# 1. Choose where lessons live (any folder, for example one inside a notes vault)
python3 scripts/lesson.py setup --dir ~/lessons --create

# 2. Print the text to add to each agent's global instruction file
python3 scripts/lesson.py snippet

# 3. Check the result
python3 scripts/lesson.py digest
```

Add the text from step 2 to the global instruction file of each agent you use (for example `~/.claude/CLAUDE.md` or `~/.codex/AGENTS.md`).

## Commands

| Command | What it does |
|---|---|
| `/lesson setup` | Choose the folder and print the instruction-file snippet |
| `/lesson add` | Draft, confirm, then write one lesson |
| `/lesson list [project]` | Show active lessons and how much of the cap is used |
| `/lesson retire <file>` | Stop loading a lesson; the file stays for history |
| `/lesson promote <file>` | Copy a project lesson into a project document, de-identified |
| `/lesson review` | Find duplicates and stale lessons |
| `/lesson migrate --from <dir>` | Import `feedback` memory files |

## Troubleshooting

| First line of the digest | Meaning and fix |
|---|---|
| `lessons: 尚未設定，請執行 /lesson setup` | No `config.json` yet; run `setup` |
| `lessons: ⚠ 讀不到資料夾` | The lessons folder is missing or a sync folder is not mounted |
| `lessons: ⚠ 找到 N 個檔案，載入 0 條` | Every file is retired or unparsable; check with `list` |
| `⚠ 略過 N 個` | Some files could not be parsed (empty or half-synced files are common) |
| `⚠ 已超過上限，請執行 /lesson review` | More lessons than the cap (default 20 global, 10 per project); merge or retire some |

## Tests

```bash
bash tests/test_lesson.sh
```
