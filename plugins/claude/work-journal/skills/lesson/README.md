# lesson

Record lessons learned (yours and your coding agent's) as one small markdown file each, and load a short, capped digest of them at the start of every agent session.

- A lesson has a one-line `rule` that agents load, and a long background that you read in any notes tool.
- Lessons are stored in a folder you choose, never inside this repository.
- Shipped in the work-journal plugin. In Claude Code and Codex the plugin's session-start hook loads the digest; other agents run `digest` from their global instruction file.

## Requirements

- Python 3 (standard library only)
- Git (used to detect the current project name)

## Quick Start

Install the work-journal plugin, then ask your agent to run `/lesson setup`, or run these from this skill's folder:

```bash
# 1. Choose where lessons live (any folder, for example one inside a notes vault).
#    This writes lesson.json to the agent-skills settings root (~/.config/agent-skills by default).
python3 scripts/lesson.py setup --dir ~/lessons --create

# 2. Check the result
python3 scripts/lesson.py digest
```

The next Claude Code or Codex session loads the digest by itself. Codex runs a new or changed plugin hook only after you approve it in `/hooks`, so approve the work-journal hook once after installing or updating. Until `lesson.json` exists, the hook prints nothing. A `lesson.json` that cannot be used, or a settings root that cannot be resolved (which also stops work-journal), gives a `lesson digest not loaded` message instead.

For an agent without plugin hooks, use a standalone copy of this folder (for example one that skill-sync mirrors) and add the output of its `python3 scripts/lesson.py snippet` to the agent's global instruction file. Do not run `snippet` from the plugin: the plugin folder carries the version in its path and an update replaces it, so `snippet` warns there. A standalone copy reads the same `lesson.json`.

## Commands

| Command | What it does |
|---|---|
| `/lesson setup` | Choose the folder; print the instruction-file snippet only for agents without plugin hooks |
| `/lesson add` | Draft, confirm, then write one lesson |
| `/lesson list [project]` | Show active lessons and how much of the cap is used |
| `/lesson retire <file>` | Stop loading a lesson; the file stays for history |
| `/lesson promote <file>` | Copy a project lesson into a project document, de-identified |
| `/lesson review` | Find duplicates and stale lessons |
| `/lesson migrate --from <dir>` | Import `feedback` memory files |

## Troubleshooting

| First line of the digest | Meaning and fix |
|---|---|
| `lessons: 尚未設定，請執行 /lesson setup` | No `lesson.json` in the settings root yet; run `setup` |
| `lessons: 尚未設定；找到舊的 config.json…` | This copy was set up before `lesson.json`; run `setup --dir` with the folder from the old `config.json`, then delete the old file |
| `lessons: ⚠ lesson.json 無法讀取…` | `lesson.json` is not valid JSON or has no `lessons_dir`; fix it or run `setup --force` |
| `lessons: ⚠ 找不到設定位置（…）` | `AGENT_SKILLS_CONFIG_DIR` or `XDG_CONFIG_HOME` is relative or inside a plugin folder |
| `lessons: ⚠ 讀不到資料夾` | The lessons folder is missing or a sync folder is not mounted |
| `lessons: ⚠ 找到 N 個檔案，載入 0 條` | Every file is retired or unparsable; check with `list` |
| `⚠ 略過 N 個` | Some files could not be parsed (empty or half-synced files are common) |
| `⚠ 已超過上限，請執行 /lesson review` | More lessons than the cap (default 50 global, 20 per project); merge or retire some |

## Tests

```bash
bash tests/test_lesson.sh
```
