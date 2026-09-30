# Lesson capture skill Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Add a `lesson` skill that records lessons learned (the user's and the agent's) as one-file-per-lesson markdown in a user-chosen folder, and loads a short, capped, scope-filtered digest at the start of every agent session.

**Architecture:** One Python 3 script (`lesson/scripts/lesson.py`, standard library only) does all deterministic work: validate, write, list, retire, migrate, digest. `SKILL.md` holds the judgment and conversation rules. Every agent (Claude and Codex; the user does not use Gemini) loads lessons the same way: its global entry file tells it to run `lesson.py digest` first and quote the status line. No hooks and no MCP in this version.

**Tech Stack:** Python 3 (standard library only), bash tests in the style of `activity-logger/tests`, Git, the existing `scripts/validate_skills_catalog.py`.

**Spec:** `docs/superpowers/specs/2026-09-30-lesson-capture-design.md`

## Global Constraints

- Run every command from the repository root (`~/.claude/skills`) unless a step says otherwise.
- Do not commit without explicit user approval. Steps marked **Checkpoint** propose a commit and stop; they never run `git commit`. Commit messages end with `Co-Authored-By: Claude Sonnet 5.5 <noreply@anthropic.com>`.
- This repository is public. No tracked file may contain a personal path, a note-vault path, an email address or a real project name. The real folder path lives only in the gitignored `lesson/config.json`.
- Lesson data never goes into this repository.
- Agent entry files outside the repo (`~/.claude/CLAUDE.md`, `~/.codex/AGENTS.md`) are edited only after a backup and after the user confirms each file separately.
- Claude settings files (`settings*.json`) are edited only after a backup and after the user confirms the exact rule.
- Original memory files are never modified or deleted by this plan.
- Known baseline failure, unrelated to this work: before any change, `python3 scripts/validate_skills_catalog.py --check` fails with `tracked skills missing from skills-catalog.json: control-return`, and so does `test_source_tree_enforces_user_only_runtime_gates`. The user decided to register `control-return` together with `lesson`; Task 6 does it and Task 10 reports it.

## File Structure

| Path | Action | Responsibility |
|---|---|---|
| `lesson/scripts/lesson.py` | Create | All deterministic behavior: digest, add, list, retire, migrate, setup, snippet |
| `lesson/tests/test_lesson.sh` | Create | Black-box tests using fixture folders |
| `lesson/templates/entry-snippet.md` | Create | Text added to each agent entry file; `{{SCRIPT}}` is filled by `snippet` |
| `lesson/config.example.json` | Create | Placeholder config; the real `lesson/config.json` is gitignored |
| `lesson/SKILL.md` | Create | Conversation and judgment rules |
| `lesson/README.md` | Create | Setup, commands and troubleshooting for people who install the skill |
| `.gitignore` | Modify | Ignore `lesson/config.json` |
| `skills-catalog.json`, `SKILLS_CATALOG.md` | Modify | Register the skill (the markdown is generated) |
| `skill-router/skill-registry.yaml` | Modify | Router entry and skill count |
| `CLAUDE.md`, `README.md` | Modify | Skill list line and dependency row |
| `activity-logger/SKILL.md` | Modify | Merge lesson proposals into the wrap-up question |
| `docs/superpowers/specs/2026-09-30-lesson-capture-design.md` | Modify | Record experiment results in section 12 |

---

### Task 1: Scaffold, ignore rule and templates

**Files:**
- Create: `lesson/config.example.json`
- Create: `lesson/templates/entry-snippet.md`
- Modify: `.gitignore`

- [x] **Step 1: Create the folders**

```bash
mkdir -p lesson/scripts lesson/tests lesson/templates
```

- [x] **Step 2: Create `lesson/config.example.json`**

````json
{
  "lessons_dir": "~/lessons",
  "cap_global": 20,
  "cap_project": 10
}
````

- [x] **Step 3: Create `lesson/templates/entry-snippet.md`**

````markdown
## Lessons
- 開工第一個動作：執行 `{{SCRIPT}} digest`，並在第一則回覆開頭原樣帶出輸出的第一行。輸出的規則本 session 都要遵守。
- 遇到「踩坑修好」「假設被推翻」「被使用者糾正」時，在自然停頓點提議記錄，一次最多兩條，使用者確認才寫（流程見 /lesson）。
- 沒有 /lesson 可用時，把 JSON（rule、scope、project、why、background、slug）用標準輸入傳給 `{{SCRIPT}} add --json -` 寫入；rule 限一行、不超過 120 字。
````

- [x] **Step 4: Append the ignore rule to `.gitignore`**

Add these lines after the `.skill-sync-targets` block at the top of the file:

```
# Lesson skill: per-user config (contains a personal folder path)
lesson/config.json
```

- [x] **Step 5: Verify the ignore rule**

Run: `git check-ignore -v lesson/config.json`
Expected: one line naming `.gitignore` and the pattern `lesson/config.json`.

- [x] **Step 6: Checkpoint** (no commit yet; Task 3 makes the folder usable)

---

### Task 2: Write the failing tests

**Files:**
- Create: `lesson/tests/test_lesson.sh`

- [x] **Step 1: Create the test file**

````bash
#!/usr/bin/env bash

set -euo pipefail

SCRIPT="$(cd "$(dirname "$0")/../scripts" && pwd)/lesson.py"
TMP_DIR="$(mktemp -d)"
trap 'rm -rf "$TMP_DIR"' EXIT

LESSONS="$TMP_DIR/lessons"
CFG="$TMP_DIR/config.json"
mkdir -p "$LESSONS"

assert_eq() {
    local actual="$1" expected="$2" message="${3:-assertion failed}"
    if [[ "$actual" != "$expected" ]]; then
        echo "$message: expected [$expected], got [$actual]" >&2
        exit 1
    fi
}

assert_contains() {
    local haystack="$1" needle="$2" message="${3:-assertion failed}"
    if [[ "$haystack" != *"$needle"* ]]; then
        echo "$message: [$needle] not found in [$haystack]" >&2
        exit 1
    fi
}

assert_not_contains() {
    local haystack="$1" needle="$2" message="${3:-assertion failed}"
    if [[ "$haystack" == *"$needle"* ]]; then
        echo "$message: [$needle] unexpectedly found in [$haystack]" >&2
        exit 1
    fi
}

lesson() { LESSON_CONFIG="$CFG" python3 "$SCRIPT" "$@"; }

write_config() {
    printf '{"lessons_dir": "%s", "cap_global": %s, "cap_project": %s}\n' \
        "$LESSONS" "${1:-20}" "${2:-10}" > "$CFG"
}

# fixture: name rule scope project status created
fixture() {
    local name="$1" rule="$2" scope="$3" project="$4" status="$5" created="$6"
    {
        echo "---"
        echo "rule: \"$rule\""
        echo "scope: $scope"
        [[ -n "$project" ]] && echo "project: \"$project\""
        echo "status: $status"
        echo "created: $created"
        echo "by: \"user\""
        echo "---"
        echo
        echo "## 背景"
    } > "$LESSONS/$name"
}

clear_lessons() { rm -f "$LESSONS"/*; }

# --- digest: not configured / unreadable
out=$(LESSON_CONFIG="$TMP_DIR/missing.json" python3 "$SCRIPT" digest)
assert_eq "$out" "lessons: 尚未設定，請執行 /lesson setup" "no config"

printf '{"lessons_dir": "%s"}\n' "$TMP_DIR/not-there" > "$CFG"
out=$(lesson digest --project demo)
assert_eq "$out" "lessons: ⚠ 讀不到資料夾" "missing folder"

# --- digest: scope filter, ordering, retired hidden
write_config
fixture 2026-01-01-a.md "global old" global "" active 2026-01-01
fixture 2026-02-01-b.md "global new" global "" active 2026-02-01
fixture 2026-01-05-c.md "demo rule" project demo active 2026-01-05
fixture 2026-01-06-d.md "other rule" project other active 2026-01-06
fixture 2026-01-07-e.md "gone rule" global "" retired 2026-01-07
out=$(lesson digest --project demo)
assert_eq "$(echo "$out" | head -n 1)" "lessons: 全域 2 條、專案 1 條" "status line"
assert_contains "$out" "- [全域] global new" "global shown"
assert_contains "$out" "- [專案] demo rule" "project shown"
assert_not_contains "$out" "other rule" "other project hidden"
assert_not_contains "$out" "gone rule" "retired hidden"
assert_eq "$(echo "$out" | sed -n 2p)" "- [全域] global new" "newest first"

# --- digest: cap and overflow warning
write_config 1 10
out=$(lesson digest --project demo)
assert_eq "$(echo "$out" | head -n 1)" \
    "lessons: 全域 1 條、專案 1 條 ⚠ 已超過上限，請執行 /lesson review" "cap warning"
assert_not_contains "$out" "global old" "older global dropped at cap"
write_config

# --- digest: unparsable and conflict copies
printf 'no frontmatter here\n' > "$LESSONS/broken.md"
: > "$LESSONS/empty.md"
fixture "2026-01-01-a (1).md" "dup rule" global "" active 2026-01-01
out=$(lesson digest --project demo)
assert_eq "$(echo "$out" | head -n 1)" \
    "lessons: 全域 2 條、專案 1 條 ⚠ 略過 2 個 ⚠ 略過 1 個疑似衝突副本" "warnings"
assert_not_contains "$out" "dup rule" "conflict copy skipped"

# --- digest: files exist but nothing active
clear_lessons
fixture 2026-01-07-e.md "gone rule" global "" retired 2026-01-07
out=$(lesson digest --project demo)
assert_eq "$out" "lessons: ⚠ 找到 1 個檔案，載入 0 條" "all retired"

# --- digest: empty folder is a normal state
clear_lessons
out=$(lesson digest --project demo)
assert_eq "$out" "lessons: 全域 0 條、專案 0 條" "empty folder"

# --- digest: an over-long rule (hand-edited or synced in) is cut at read time
fixture 2026-01-01-long.md "$(python3 -c 'print("x"*200)')" global "" active 2026-01-01
width=$(lesson digest --project demo | python3 -c "import sys; print(len(sys.stdin.read().splitlines()[1]))")
assert_eq "$width" "127" "long rule truncated at read time"
clear_lessons

# --- digest: project detected from git root name
GIT_REPO="$TMP_DIR/my-app"
mkdir -p "$GIT_REPO/sub"
git init --quiet "$GIT_REPO"
fixture 2026-01-05-c.md "my-app rule" project my-app active 2026-01-05
out=$(cd "$GIT_REPO/sub" && lesson digest)
assert_contains "$out" "- [專案] my-app rule" "git project detection"
clear_lessons

# --- add: validation and write
today="$(date +%F)"
path=$(echo '{"rule":"check body error code","scope":"global","why":"w","background":"b","slug":"api-error"}' | lesson add --json -)
assert_eq "$(basename "$path")" "$today-api-error.md" "file name"
out=$(lesson digest --project demo)
assert_contains "$out" "- [全域] check body error code" "added lesson loads"

path2=$(echo '{"rule":"second","scope":"global","slug":"api-error"}' | lesson add --json -)
assert_eq "$(basename "$path2")" "$today-api-error-2.md" "collision suffix"

# quotes and colons round-trip
echo '{"rule":"use \"x\": never y","scope":"global","slug":"quote"}' | lesson add --json - > /dev/null
out=$(lesson digest --project demo)
assert_contains "$out" '- [全域] use "x": never y' "round trip"

long=$(python3 -c 'print("x"*121)')
rc=0; err=$(echo "{\"rule\":\"$long\",\"scope\":\"global\"}" | lesson add --json - 2>&1) || rc=$?
assert_eq "$rc" "2" "long rule rejected"
assert_contains "$err" "limit is 120" "long rule message"

rc=0; err=$(echo '{"rule":"a\nb","scope":"global"}' | lesson add --json - 2>&1) || rc=$?
assert_eq "$rc" "2" "multi-line rule rejected"

rc=0; err=$(echo '{"rule":"set password=hunter2hunter2","scope":"global"}' | lesson add --json - 2>&1) || rc=$?
assert_eq "$rc" "2" "secret rejected"
assert_contains "$err" "secret" "secret message"

rc=0; err=$(echo '{"rule":"r","scope":"project"}' | lesson add --json - 2>&1) || rc=$?
assert_eq "$rc" "2" "project scope needs project"

rc=0; err=$(echo '[1,2]' | lesson add --json - 2>&1) || rc=$?
assert_eq "$rc" "2" "non-object entry rejected"
assert_contains "$err" "JSON object" "non-object entry message"

out=$(echo '{"rule":"dry","scope":"global"}' | lesson add --json - --dry-run)
assert_eq "$out" "ok" "dry run"
assert_not_contains "$(ls "$LESSONS")" "dry" "dry run writes nothing"

# add must not create a missing folder (unmounted sync folder)
printf '{"lessons_dir": "%s"}\n' "$TMP_DIR/not-mounted" > "$CFG"
rc=0; err=$(echo '{"rule":"r","scope":"global"}' | lesson add --json - 2>&1) || rc=$?
assert_eq "$rc" "2" "missing folder rejected"
assert_contains "$err" "is the sync folder mounted" "missing folder message"
[[ ! -e "$TMP_DIR/not-mounted" ]] || { echo "add created the folder" >&2; exit 1; }
write_config
clear_lessons

# --- retire
fixture 2026-01-01-a.md "to retire" global "" active 2026-01-01
lesson retire 2026-01-01-a.md --reason "superseded" > /dev/null
out=$(lesson digest --project demo)
assert_eq "$out" "lessons: ⚠ 找到 1 個檔案，載入 0 條" "retired hidden"
assert_contains "$(cat "$LESSONS/2026-01-01-a.md")" 'retired_reason: "superseded"' "reason kept"
rc=0; lesson retire 2026-01-01-a.md >/dev/null 2>&1 || rc=$?
assert_eq "$rc" "1" "double retire fails"
rc=0; lesson retire ../etc.md >/dev/null 2>&1 || rc=$?
assert_eq "$rc" "2" "path rejected"
clear_lessons

# --- migrate
MEM="$TMP_DIR/memory"
mkdir -p "$MEM"
cat > "$MEM/feedback_never_guess.md" <<'EOF'
---
name: never-guess
description: do not invent URLs
metadata:
  type: feedback
---

Do not fabricate URLs.

**Why:** it burned us once.
EOF
cat > "$MEM/project_status.md" <<'EOF'
---
name: status
description: wip
metadata:
  type: project
---
in progress
EOF
printf -- '- index\n' > "$MEM/MEMORY.md"

plan=$(lesson migrate --from "$MEM" --plan)
assert_contains "$plan" "feedback_never_guess.md" "plan lists feedback"
assert_not_contains "$plan" "project_status.md" "plan skips project"

echo '[{"file":"feedback_never_guess.md","rule":"do not guess URLs","scope":"global"}]' > "$TMP_DIR/map.json"
out=$(lesson migrate --from "$MEM" --apply "$TMP_DIR/map.json")
assert_contains "$out" "written: 1" "migrate writes"
migrated=$(ls "$LESSONS")
assert_contains "$(cat "$LESSONS/$migrated")" 'migrated_from: "feedback_never_guess.md"' "provenance"
assert_contains "$(cat "$LESSONS/$migrated")" "**Why:** it burned us once." "body verbatim"
out=$(lesson migrate --from "$MEM" --apply "$TMP_DIR/map.json")
assert_contains "$out" "written: 0" "rerun writes nothing"
assert_eq "$(ls "$LESSONS" | wc -l | tr -d ' ')" "1" "no duplicate"
assert_contains "$(lesson migrate --from "$MEM" --plan)" '"already_migrated": true' "plan marks done"

echo '[{"file":"feedback_never_guess.md","rule":"","scope":"global"}]' > "$TMP_DIR/bad.json"
clear_lessons
rc=0; lesson migrate --from "$MEM" --apply "$TMP_DIR/bad.json" >/dev/null 2>&1 || rc=$?
assert_eq "$rc" "2" "invalid mapping rejected"
assert_eq "$(ls "$LESSONS" | wc -l | tr -d ' ')" "0" "invalid mapping writes nothing"

echo '[1]' > "$TMP_DIR/notobj.json"
rc=0; err=$(lesson migrate --from "$MEM" --apply "$TMP_DIR/notobj.json" 2>&1) || rc=$?
assert_eq "$rc" "2" "non-object mapping row rejected"
assert_contains "$err" "not a JSON object" "non-object mapping row message"
echo 'not json' > "$TMP_DIR/notjson.json"
rc=0; err=$(lesson migrate --from "$MEM" --apply "$TMP_DIR/notjson.json" 2>&1) || rc=$?
assert_eq "$rc" "2" "invalid mapping JSON rejected"

rc=0; err=$(lesson migrate --from "$TMP_DIR/no-such-memory" --plan 2>&1) || rc=$?
assert_eq "$rc" "1" "missing migrate source rejected"
assert_contains "$err" "not a folder" "missing migrate source message"

# --- setup and snippet
REL_CFG="$TMP_DIR/rel-config.json"
(cd "$TMP_DIR" && LESSON_CONFIG="$REL_CFG" python3 "$SCRIPT" setup --dir rel-lessons --create >/dev/null)
stored=$(python3 -c "import json,sys; print(json.load(open(sys.argv[1]))['lessons_dir'])" "$REL_CFG")
assert_eq "${stored:0:1}" "/" "relative dir stored as absolute"
SETUP_CFG="$TMP_DIR/setup-config.json"
NEW_DIR="$TMP_DIR/new-lessons"
rc=0; LESSON_CONFIG="$SETUP_CFG" python3 "$SCRIPT" setup --dir "$NEW_DIR" >/dev/null 2>&1 || rc=$?
assert_eq "$rc" "1" "missing dir needs --create"
LESSON_CONFIG="$SETUP_CFG" python3 "$SCRIPT" setup --dir "$NEW_DIR" --create >/dev/null
[[ -d "$NEW_DIR" ]] || { echo "setup did not create dir" >&2; exit 1; }
rc=0; LESSON_CONFIG="$SETUP_CFG" python3 "$SCRIPT" setup --dir "$NEW_DIR" >/dev/null 2>&1 || rc=$?
assert_eq "$rc" "1" "no overwrite without --force"

snippet=$(python3 "$SCRIPT" snippet)
assert_contains "$snippet" "lesson.py" "snippet has script path"
assert_contains "$snippet" " digest" "snippet has digest command"
assert_contains "$snippet" " add --json -" "snippet has add command"
assert_not_contains "$snippet" "{{" "snippet fully rendered"

echo "PASS: test_lesson.sh"
````

- [x] **Step 2: Run it and confirm it fails because the script does not exist yet**

Run: `bash lesson/tests/test_lesson.sh; echo "exit=$?"`
Expected: a Python error such as `can't open file '.../lesson/scripts/lesson.py'` and a non-zero exit. It must not print `PASS`.

---

### Task 3: Implement `lesson.py`

**Files:**
- Create: `lesson/scripts/lesson.py`

- [x] **Step 1: Create the script**

````python
#!/usr/bin/env python3
"""lesson: capture and load lessons learned. Standard library only.

Deterministic half of the /lesson skill. Drafting and asking for
confirmation live in SKILL.md; this script validates, reads and writes files.
"""
import argparse
import json
import os
import re
import shlex
import subprocess
import sys
from datetime import date, datetime
from pathlib import Path

SKILL_DIR = Path(__file__).resolve().parent.parent
DEFAULT_CONFIG = SKILL_DIR / "config.json"
DEFAULTS = {"cap_global": 20, "cap_project": 10}
RULE_MAX = 120
CONFLICT_RE = re.compile(r"\(\d+\)|conflicted copy", re.IGNORECASE)
DATE_RE = re.compile(r"^\d{4}-\d{2}-\d{2}$")
SECRET_RES = [
    re.compile(r"AKIA[0-9A-Z]{16}"),
    re.compile(r"-----BEGIN [A-Z ]*PRIVATE KEY-----"),
    re.compile(r"\bsk-[A-Za-z0-9_-]{20,}"),
    re.compile(r"\bghp_[A-Za-z0-9]{30,}"),
    re.compile(r"\bxox[baprs]-[A-Za-z0-9-]{10,}"),
    re.compile(
        r"(api[_-]?key|secret|token|passwd|password)\s*[:=]\s*\S{8,}",
        re.IGNORECASE,
    ),
]


# ---------------------------------------------------------------- config

def config_path():
    return Path(os.environ.get("LESSON_CONFIG") or DEFAULT_CONFIG)


def load_config():
    """Return the merged config, or None when missing or unusable."""
    path = config_path()
    if not path.is_file():
        return None
    try:
        raw = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, ValueError):
        return None
    if not isinstance(raw, dict) or not raw.get("lessons_dir"):
        return None
    cfg = dict(DEFAULTS)
    cfg.update(raw)
    cfg["lessons_dir"] = Path(os.path.expanduser(str(raw["lessons_dir"])))
    for key in ("cap_global", "cap_project"):
        try:
            cfg[key] = int(cfg[key])
        except (TypeError, ValueError):
            cfg[key] = DEFAULTS[key]
    return cfg


def detect_project():
    """Git root folder name; the current folder name outside git."""
    try:
        out = subprocess.run(
            ["git", "rev-parse", "--show-toplevel"],
            capture_output=True, text=True, timeout=5,
        )
        if out.returncode == 0 and out.stdout.strip():
            return Path(out.stdout.strip()).name
    except (OSError, subprocess.SubprocessError):
        pass
    return Path.cwd().name


# ----------------------------------------------------------- frontmatter

def quote(value):
    return '"' + str(value).replace("\\", "\\\\").replace('"', '\\"') + '"'


def unquote(value):
    value = value.strip()
    if len(value) >= 2 and value[0] == '"' and value[-1] == '"':
        return re.sub(r"\\(.)", r"\1", value[1:-1])
    return value


def split_frontmatter(text):
    """Return (meta dict, body) or (None, text) when there is no block."""
    lines = text.splitlines()
    if not lines or lines[0].strip() != "---":
        return None, text
    meta = {}
    for index, line in enumerate(lines[1:], start=1):
        if line.strip() == "---":
            return meta, "\n".join(lines[index + 1:])
        if ":" in line:
            key, _, value = line.partition(":")
            meta[key.strip()] = unquote(value)
    return None, text


def valid_meta(meta):
    if not meta.get("rule"):
        return False
    if meta.get("scope") not in ("global", "project"):
        return False
    if meta.get("status") not in ("active", "retired"):
        return False
    if not DATE_RE.match(meta.get("created", "")):
        return False
    if meta["scope"] == "project" and not meta.get("project"):
        return False
    return True


def scan(lessons_dir):
    """Return (valid lessons, unparsable count, conflict-copy count)."""
    valid, bad, conflicts = [], 0, 0
    for path in sorted(lessons_dir.iterdir()):
        if not path.is_file() or path.suffix != ".md":
            continue
        if path.name.startswith((".", "_")):
            continue
        if CONFLICT_RE.search(path.name):
            conflicts += 1
            continue
        try:
            meta, _ = split_frontmatter(path.read_text(encoding="utf-8-sig"))
        except (OSError, UnicodeDecodeError):
            meta = None
        if meta is None or not valid_meta(meta):
            bad += 1
            continue
        meta["file"] = path.name
        valid.append(meta)
    return valid, bad, conflicts


# ------------------------------------------------------------ validation

def clip(rule):
    """Guard the session context against over-long hand-edited or synced rules."""
    return rule if len(rule) <= RULE_MAX else rule[:RULE_MAX - 1] + "…"


def slugify(text):
    slug = re.sub(r"[^a-z0-9]+", "-", str(text).lower()).strip("-")[:50]
    return slug.strip("-") or "lesson"


def validate_entry(entry):
    """Return a normalised entry dict or raise ValueError."""
    if not isinstance(entry, dict):
        raise ValueError("entry must be a JSON object")
    rule = str(entry.get("rule", "")).strip()
    if not rule:
        raise ValueError("rule is empty")
    if "\n" in rule or "\r" in rule:
        raise ValueError("rule must be a single line")
    if len(rule) > RULE_MAX:
        raise ValueError(f"rule is {len(rule)} chars; limit is {RULE_MAX}")
    scope = entry.get("scope")
    if scope not in ("global", "project"):
        raise ValueError("scope must be 'global' or 'project'")
    project = str(entry.get("project") or "").strip()
    if scope == "project" and not project:
        raise ValueError("project is required when scope is 'project'")
    if "\n" in project or "\r" in project:
        raise ValueError("project must be a single line")
    by = str(entry.get("by") or "claude")
    if not re.fullmatch(r"[a-z0-9-]+", by):
        raise ValueError("by must match [a-z0-9-]+")
    why = str(entry.get("why") or "")
    background = str(entry.get("background") or "")
    for field, text in (("rule", rule), ("why", why), ("background", background)):
        if any(rx.search(text) for rx in SECRET_RES):
            raise ValueError(f"{field} looks like it contains a secret")
    return {
        "rule": rule, "scope": scope,
        "project": project if scope == "project" else "",
        "by": by, "why": why, "background": background,
        "slug": entry.get("slug") or "",
    }


def render(entry, created, migrated_from=None):
    lines = ["---", f"rule: {quote(entry['rule'])}", f"scope: {entry['scope']}"]
    if entry["scope"] == "project":
        lines.append(f"project: {quote(entry['project'])}")
    lines += ["status: active", f"created: {created}", f"by: {quote(entry['by'])}"]
    if migrated_from:
        lines.append(f"migrated_from: {quote(migrated_from)}")
    lines += [
        "---", "",
        "## 為什麼", entry["why"], "",
        "## 背景", entry["background"], "",
    ]
    return "\n".join(lines)


def write_lesson(lessons_dir, entry, created, migrated_from=None):
    """Write a new lesson file; never overwrite, never create the folder."""
    if not lessons_dir.is_dir():
        raise ValueError(
            f"lessons_dir does not exist: {lessons_dir} "
            "(is the sync folder mounted?)"
        )
    text = render(entry, created, migrated_from)
    base = f"{created}-{slugify(entry['slug'])}"
    number = 1
    while True:
        name = f"{base}.md" if number == 1 else f"{base}-{number}.md"
        try:
            with open(lessons_dir / name, "x", encoding="utf-8") as handle:
                handle.write(text)
            return lessons_dir / name
        except FileExistsError:
            number += 1


def read_json(path):
    raw = sys.stdin.read() if path == "-" else Path(path).read_text(encoding="utf-8")
    return json.loads(raw)


def need_config():
    cfg = load_config()
    if cfg is None:
        print("lessons: 尚未設定，請執行 /lesson setup", file=sys.stderr)
        sys.exit(1)
    return cfg


# -------------------------------------------------------------- commands

def cmd_digest(args):
    try:
        return _digest(args)
    except Exception as exc:  # never break session start, never stay silent
        print(f"lessons: ⚠ 載入失敗（{type(exc).__name__}）")
        return 0


def _digest(args):
    cfg = load_config()
    if cfg is None:
        print("lessons: 尚未設定，請執行 /lesson setup")
        return 0
    try:
        valid, bad, conflicts = scan(cfg["lessons_dir"])
    except OSError:
        print("lessons: ⚠ 讀不到資料夾")
        return 0
    found = len(valid) + bad + conflicts
    active = [m for m in valid if m["status"] == "active"]
    if found and not active:
        print(f"lessons: ⚠ 找到 {found} 個檔案，載入 0 條")
        return 0

    project = args.project or detect_project()

    def pick(scope, cap):
        items = [
            m for m in active
            if m["scope"] == scope
            and (scope == "global" or m["project"] == project)
        ]
        items.sort(key=lambda m: (m["created"], m["file"]), reverse=True)
        return items[:cap], len(items) > cap

    globals_, g_over = pick("global", cfg["cap_global"])
    projects_, p_over = pick("project", cfg["cap_project"])

    parts = [f"lessons: 全域 {len(globals_)} 條、專案 {len(projects_)} 條"]
    if bad:
        parts.append(f"⚠ 略過 {bad} 個")
    if conflicts:
        parts.append(f"⚠ 略過 {conflicts} 個疑似衝突副本")
    if g_over or p_over:
        parts.append("⚠ 已超過上限，請執行 /lesson review")
    print(" ".join(parts))
    for item in globals_:
        print(f"- [全域] {clip(item['rule'])}")
    for item in projects_:
        print(f"- [專案] {clip(item['rule'])}")
    return 0


def cmd_add(args):
    cfg = need_config()
    try:
        entry = validate_entry(read_json(args.json))
        if args.dry_run:
            print("ok")
            return 0
        path = write_lesson(cfg["lessons_dir"], entry, date.today().isoformat())
    except (ValueError, OSError) as exc:
        print(f"error: {exc}", file=sys.stderr)
        return 2
    print(path)
    return 0


def cmd_list(args):
    cfg = need_config()
    try:
        valid, bad, conflicts = scan(cfg["lessons_dir"])
    except OSError as exc:
        print(f"error: {exc}", file=sys.stderr)
        return 1
    project = args.project or detect_project()
    active = [m for m in valid if m["status"] == "active"]
    retired = len(valid) - len(active)
    g = [m for m in active if m["scope"] == "global"]
    p = [m for m in active if m["scope"] == "project"]
    if args.project:
        p = [m for m in p if m["project"] == args.project]
    print(f"[全域] {len(g)}/{cfg['cap_global']}")
    for m in g:
        print(f"  {m['file']}  {m['rule']}")
    mine = [m for m in p if m["project"] == project]
    print(f"[專案:{project}] {len(mine)}/{cfg['cap_project']}")
    for m in p:
        print(f"  {m['file']}  ({m['project']}) {m['rule']}")
    print(f"retired: {retired}  unparsable: {bad}  conflict-copies: {conflicts}")
    return 0


def cmd_retire(args):
    cfg = need_config()
    name = args.file
    if "/" in name or "\\" in name or not name.endswith(".md"):
        print("error: give a lesson file name, not a path", file=sys.stderr)
        return 2
    path = cfg["lessons_dir"] / name
    if not path.is_file():
        print(f"error: no such lesson: {name}", file=sys.stderr)
        return 1
    lines = path.read_text(encoding="utf-8-sig").splitlines()
    if not lines or lines[0].strip() != "---":
        print("error: no frontmatter", file=sys.stderr)
        return 1
    end = next((i for i in range(1, len(lines)) if lines[i].strip() == "---"), None)
    status_at = next(
        (i for i in range(1, end or 0) if lines[i].startswith("status:")), None
    )
    if end is None or status_at is None:
        print("error: no status field", file=sys.stderr)
        return 1
    if unquote(lines[status_at].partition(":")[2]) == "retired":
        print("error: already retired", file=sys.stderr)
        return 1
    lines[status_at] = "status: retired"
    extra = [f"retired_at: {date.today().isoformat()}"]
    if args.reason:
        extra.append(f"retired_reason: {quote(args.reason.replace(chr(10), ' '))}")
    lines[end:end] = extra
    tmp = path.with_name(path.name + ".tmp")
    tmp.write_text("\n".join(lines) + "\n", encoding="utf-8")
    os.replace(tmp, path)
    print(f"retired: {name}")
    return 0


def memory_feedback_files(src):
    for path in sorted(Path(src).expanduser().glob("*.md")):
        if path.name == "MEMORY.md":
            continue
        try:
            meta, body = split_frontmatter(path.read_text(encoding="utf-8-sig"))
        except (OSError, UnicodeDecodeError):
            continue
        meta = meta or {}
        if path.name.startswith("feedback_") or meta.get("type") == "feedback":
            yield path, meta, body.strip()


def cmd_migrate(args):
    cfg = need_config()
    if not Path(args.src).expanduser().is_dir():
        print(f"error: --from is not a folder: {args.src}", file=sys.stderr)
        return 1
    lessons_dir = cfg["lessons_dir"]
    try:
        valid, _, _ = scan(lessons_dir)
    except OSError as exc:
        print(f"error: {exc}", file=sys.stderr)
        return 1
    done = {m.get("migrated_from") for m in valid if m.get("migrated_from")}
    sources = {p.name: (p, m, b) for p, m, b in memory_feedback_files(args.src)}

    if args.plan:
        rows = [
            {
                "file": name, "name": meta.get("name", ""),
                "description": meta.get("description", ""),
                "body": body, "already_migrated": name in done,
            }
            for name, (_, meta, body) in sources.items()
        ]
        print(json.dumps(rows, ensure_ascii=False, indent=2))
        return 0

    try:
        mapping = read_json(args.apply)
    except (ValueError, OSError) as exc:
        print(f"error: cannot read mapping: {exc}", file=sys.stderr)
        return 2
    if not isinstance(mapping, list):
        print("error: mapping must be a JSON list of objects", file=sys.stderr)
        return 2
    prepared, errors = [], []
    for position, row in enumerate(mapping, start=1):
        if not isinstance(row, dict):
            errors.append(f"row {position}: not a JSON object")
            continue
        name = row.get("file")
        if name not in sources:
            errors.append(f"{name}: not a feedback file in {args.src}")
            continue
        if name in done:
            continue
        _, meta, body = sources[name]
        try:
            entry = validate_entry({
                "rule": row.get("rule"), "scope": row.get("scope"),
                "project": row.get("project"), "by": "user",
                "why": meta.get("description", ""), "background": body,
                "slug": name.removesuffix(".md").removeprefix("feedback_")
                .replace("_", "-"),
            })
        except ValueError as exc:
            errors.append(f"{name}: {exc}")
            continue
        created = datetime.fromtimestamp(sources[name][0].stat().st_mtime)
        prepared.append((name, entry, created.date().isoformat()))
    if errors:
        print("nothing written:\n" + "\n".join(errors), file=sys.stderr)
        return 2
    try:
        for name, entry, created in prepared:
            write_lesson(lessons_dir, entry, created, migrated_from=name)
    except (ValueError, OSError) as exc:
        print(f"error: {exc}", file=sys.stderr)
        return 2
    print(f"written: {len(prepared)}  skipped(already migrated): "
          f"{len(mapping) - len(prepared)}")
    return 0


def cmd_setup(args):
    path = config_path()
    if path.exists() and not args.force:
        print(f"error: {path} already exists (use --force)", file=sys.stderr)
        return 1
    target = Path(os.path.expanduser(args.dir))
    if not target.is_dir():
        if not args.create:
            print(f"error: {target} does not exist (use --create)", file=sys.stderr)
            return 1
        target.mkdir(parents=True)
    stored = args.dir if args.dir.startswith("~") else os.path.abspath(args.dir)
    path.write_text(
        json.dumps({"lessons_dir": stored, **DEFAULTS}, ensure_ascii=False, indent=2)
        + "\n",
        encoding="utf-8",
    )
    print(f"configured: {path}")
    return 0


def cmd_snippet(_args):
    template = (SKILL_DIR / "templates" / "entry-snippet.md").read_text(encoding="utf-8")
    script = f"python3 {shlex.quote(str(Path(__file__).resolve()))}"
    print(template.replace("{{SCRIPT}}", script), end="")
    return 0


def build_parser():
    parser = argparse.ArgumentParser(prog="lesson")
    sub = parser.add_subparsers(dest="command", required=True)

    p = sub.add_parser("digest")
    p.add_argument("--project")
    p.set_defaults(func=cmd_digest)

    p = sub.add_parser("add")
    p.add_argument("--json", required=True, help="entry JSON file, or - for stdin")
    p.add_argument("--dry-run", action="store_true")
    p.set_defaults(func=cmd_add)

    p = sub.add_parser("list")
    p.add_argument("--project")
    p.set_defaults(func=cmd_list)

    p = sub.add_parser("retire")
    p.add_argument("file")
    p.add_argument("--reason")
    p.set_defaults(func=cmd_retire)

    p = sub.add_parser("migrate")
    p.add_argument("--from", dest="src", required=True)
    group = p.add_mutually_exclusive_group(required=True)
    group.add_argument("--plan", action="store_true")
    group.add_argument("--apply", metavar="MAPPING_JSON")
    p.set_defaults(func=cmd_migrate)

    p = sub.add_parser("setup")
    p.add_argument("--dir", required=True)
    p.add_argument("--create", action="store_true")
    p.add_argument("--force", action="store_true")
    p.set_defaults(func=cmd_setup)

    p = sub.add_parser("snippet")
    p.set_defaults(func=cmd_snippet)
    return parser


def main(argv=None):
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8")
    args = build_parser().parse_args(argv)
    return args.func(args)


if __name__ == "__main__":
    sys.exit(main())
````

- [x] **Step 2: Make it executable**

Run: `chmod +x lesson/scripts/lesson.py`

- [x] **Step 3: Run the tests**

Run: `bash lesson/tests/test_lesson.sh`
Expected: `PASS: test_lesson.sh`

- [x] **Step 4: Prove the tests can fail (mutation check)**

Each line below breaks one behavior, runs the tests, and restores the file (`sed -i ''` is the macOS form). Every `mut` line must print a failure message, and the last line must print `PASS`.

```bash
cp lesson/scripts/lesson.py /tmp/lesson.py.orig
run() { bash lesson/tests/test_lesson.sh 2>&1 | tail -1; }
sed -i '' 's/reverse=True/reverse=False/' lesson/scripts/lesson.py; echo "mut order:  $(run)"; cp /tmp/lesson.py.orig lesson/scripts/lesson.py
sed -i '' 's/RULE_MAX = 120/RULE_MAX = 999/' lesson/scripts/lesson.py; echo "mut length: $(run)"; cp /tmp/lesson.py.orig lesson/scripts/lesson.py
sed -i '' 's/if name in done:/if False:/' lesson/scripts/lesson.py; echo "mut rerun:  $(run)"; cp /tmp/lesson.py.orig lesson/scripts/lesson.py
sed -i '' 's/if not lessons_dir.is_dir():/if False:/' lesson/scripts/lesson.py; echo "mut mount:  $(run)"; cp /tmp/lesson.py.orig lesson/scripts/lesson.py
echo "restored:   $(run)"; rm /tmp/lesson.py.orig
```

Expected: four failure lines, then `restored:   PASS: test_lesson.sh`.

- [x] **Step 5: Smoke-test the CLI help**

Run: `python3 lesson/scripts/lesson.py --help`
Expected: usage listing `digest,add,list,retire,migrate,setup,snippet`.

- [x] **Step 6: Checkpoint** (do not commit; suggested message for later: `feat(lesson): add lesson script and tests`)

---

### Task 4: Verify the unverified assumptions (gate)

This task decides whether the design holds. It uses a scratch folder and project-level instruction files, so no global file is touched. It edits nothing in the repo except the spec's section 12.

**Files:**
- Modify: `docs/superpowers/specs/2026-09-30-lesson-capture-design.md` (section 12)

- [x] **Step 1: Build the scratch fixture**

```bash
ROOT="$PWD"; EXP="$(mktemp -d)"; echo "$EXP"
mkdir -p "$EXP/lessons" "$EXP/repo" && git init --quiet "$EXP/repo"
env LESSON_CONFIG="$EXP/config.json" python3 lesson/scripts/lesson.py setup --dir "$EXP/lessons"
env LESSON_CONFIG="$EXP/config.json" python3 lesson/scripts/lesson.py add --json - <<'EOF'
{"rule":"EXPERIMENT global rule: answer in plain language","scope":"global","slug":"exp-global"}
EOF
env LESSON_CONFIG="$EXP/config.json" python3 lesson/scripts/lesson.py add --json - <<'EOF'
{"rule":"EXPERIMENT project rule","scope":"project","project":"repo","slug":"exp-project"}
EOF
(cd "$EXP/repo" && env LESSON_CONFIG="$EXP/config.json" python3 "$ROOT/lesson/scripts/lesson.py" digest)
```

Expected last command output: `lessons: 全域 1 條、專案 1 條` followed by two `- [...]` lines. (The project rule appears only because the digest detects the git folder name `repo`.)

- [x] **Step 2: Put the snippet into project-level instruction files**

```bash
SNIP="$(python3 lesson/scripts/lesson.py snippet | sed "s#python3 #LESSON_CONFIG=$EXP/config.json python3 #g")"
for f in AGENTS.md CLAUDE.md; do printf '%s\n' "$SNIP" > "$EXP/repo/$f"; done
grep -c LESSON_CONFIG "$EXP/repo/AGENTS.md"
```

Expected: `2`.

- [x] **Step 3: Run each agent three times and record what happens**

Before running, tell the user this launches six external agent sessions (three Codex, three Claude) and wait for a yes. Gemini is skipped because the user does not use it.

Do not pre-approve tools with flags such as `--allowedTools`: the point is to see what the user's real sessions do. Facts checked when this plan was written: the main `settings.json` uses `bypassPermissions`, the Codex config uses `approval_policy = "never"` with full access, and the profile `settings-C4E.json` is in default mode with no rule covering `python3`, so it would prompt. A permission denial or prompt is a harness result: record it separately and do not count it as the agent skipping the instruction.

```bash
cd "$EXP/repo"
for i in 1 2 3; do codex exec -o "$EXP/codex-$i.txt" "What is 2+2?" >/dev/null 2>&1; echo "--- codex $i"; head -3 "$EXP/codex-$i.txt"; done
for i in 1 2 3; do echo "--- claude $i"; claude -p "What is 2+2?" 2>&1 | head -3; done
cd - >/dev/null
```

For each run, note: (a) did the first reply line start with `lessons: 全域 1 條、專案 1 條`; (b) did a sandbox or permission prompt block reading the lessons folder (the real folder will live outside any project directory, so this matters); (c) did the agent ignore the instruction.


- [x] **Step 4: Check the sync-folder read behavior** (result: not applicable. The user's Drive is in mirror mode, so files stay local. An attempt to set a test file to online-only did not take effect; streaming mode stays unverified, and the digest warns instead of failing silently.)

Ask the user for the note-vault or sync-folder location they intend to use, and for permission to create a folder named `lesson-experiment` inside it. Then:

```bash
REAL="<sync-folder>/lesson-experiment"   # value supplied by the user; never write it into a tracked file
mkdir -p "$REAL"
env LESSON_CONFIG="$EXP/real.json" python3 lesson/scripts/lesson.py setup --dir "$REAL"
env LESSON_CONFIG="$EXP/real.json" python3 lesson/scripts/lesson.py add --json - <<'EOF'
{"rule":"EXPERIMENT sync rule","scope":"global","slug":"exp-sync"}
EOF
```

Ask the user to set that file to online-only (cloud-only) in their sync client, and wait until they confirm. Then:

```bash
time env LESSON_CONFIG="$EXP/real.json" python3 lesson/scripts/lesson.py digest --project repo
```

Pass condition: the first line always describes reality: either `全域 1 條` (the client downloaded the file on read) or a `⚠` warning. A first line that says `全域 0 條` without a warning while the file exists is a failure. Record how long the read took.

- [x] **Step 5: Remove the experiment files** (scratch fixture removed; the sync-folder experiment folder is still to remove after Step 4)

Ask the user to confirm, then delete `"$REAL"` and `"$EXP"`. Do not delete anything else.

- [x] **Step 6: Record the results in the spec** (agent results recorded; add the sync-folder line after Step 4)

In `docs/superpowers/specs/2026-09-30-lesson-capture-design.md`, under section 12, add a `### Results (2026-09-30)` block with one line per item: Codex N/3, Claude N/3 (with any approval or sandbox note), Gemini skipped, and the sync-folder outcome with timing.

- [x] **Step 7: Gate decision** (agent part passed: Codex 3/3, Claude 3/3; the sync-folder check is still open)

If any agent quoted the status line in fewer than 2 of 3 runs, or a sandbox blocked reading the lessons folder, **stop and report to the user** with the evidence. Options to offer: stronger entry-file wording, moving that agent's read path, or adding a hook for that agent. Do not continue to Task 5 until the user decides. Otherwise continue.

---

### Task 5: Write `SKILL.md`

**Files:**
- Create: `lesson/SKILL.md`
- Create: `lesson/README.md`

- [x] **Step 1: Create the file**

````markdown
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
````

- [x] **Step 2: Create `lesson/README.md`** (added after the first skill-auditor run, which asked for a quick start for public users)

````markdown
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
````

- [x] **Step 3: Check the frontmatter and that nothing personal leaked**

```bash
head -4 lesson/SKILL.md
grep -rnE "/Users/|/home/|@gmail|CloudStorage" lesson/ || echo "clean"
```

Expected: the frontmatter shows `name: lesson`; the grep prints `clean`.

- [x] **Step 4: Checkpoint** (suggested message later: `feat(lesson): add lesson skill instructions`)

---

### Task 6: Register the skill

**Files:**
- Modify: `skills-catalog.json` (`lesson` and `control-return`)
- Modify: `skill-router/skill-registry.yaml` (`lesson` and `control-return`)
- Modify: `CLAUDE.md`
- Modify: `README.md`
- Regenerate: `SKILLS_CATALOG.md`

- [x] **Step 1: Add the catalog entry in alphabetical position**

In `skills-catalog.json`, insert this line immediately before the line that starts with `{"id":"md-translate"`:

```json
    {"id":"lesson","category":"productivity-tracking","lifecycle":"experimental","invocation_intent":"model","surfaces":{"routable":true,"listed_in_readme":false,"sync":true}},
```

It is `model` because agents must be able to invoke the proposal step at a pause and during wrap-up. No `agents/openai.yaml` is needed for a model-invocable skill (`activity-logger` has none).

- [x] **Step 2: Add the router entry**

In `skill-router/skill-registry.yaml`, in the 知識管理 category, add after the `activity-logger` block (keep the blank line between entries):

```yaml
      - id: lesson
        triggers:
          - "lesson"
          - "記下這個教訓"
          - "lesson learned"
          - "記錄經驗"
          - "踩坑記錄"
```

Then change the header line `# 48 skills · 10 categories · 6 workflows` to `# 49 skills · 10 categories · 6 workflows`.

- [x] **Step 3: Add the skill list line to `CLAUDE.md`**

Under `### Productivity & Analysis`, after the `activity-logger` line:

```
- **lesson** — Record lessons learned (yours and the agent's) as one-file-per-lesson notes and load a short capped digest at session start across agents
```

- [x] **Step 4: Add the dependency row to `README.md`**

In the dependency table, after the `activity-logger` row:

```
| lesson | Python 3 (standard library only), Git |
```

- [x] **Step 5: Make the new skill visible to the validator and check**

The validator reads Git's index, so mark the folder as intent-to-add (this stages nothing for commit):

```bash
git add -N lesson
python3 scripts/validate_skills_catalog.py --check
```

Expected: the complaint mentions **only** `control-return` (the known baseline problem, fixed in Step 7) and does not mention `lesson`. If it mentions `lesson`, fix that first; common causes are a router id mismatch or catalog order.

- [x] **Step 6: Run the validator's tests**

Run: `python3 -m unittest tests.test_validate_skills_catalog 2>&1 | tail -4`
Expected: exactly one failure, `test_source_tree_enforces_user_only_runtime_gates`, with the `control-return` message (it disappears after Step 7). Any other failure is caused by this task.

- [x] **Step 7: Register `control-return` (decided by the user on 2026-09-30: register it together with `lesson`)**

`--write` validates first and refuses to run while `control-return` is missing from the catalog, so it must be registered before `SKILLS_CATALOG.md` can be regenerated. It is a user-only skill, so mirror `session-preferences`:

1. In `skills-catalog.json`, insert this line in alphabetical position (right after the `code-review-*` entries, before the next id that sorts after `control-return`):

```json
    {"id":"control-return","category":"tools-meta","lifecycle":"experimental","invocation_intent":"user","surfaces":{"routable":true,"listed_in_readme":false,"sync":true}},
```

2. In `skill-router/skill-registry.yaml`, add a router entry in the same category and style as `session-preferences` (user-only skills must be routable). Use triggers taken from `control-return/SKILL.md` (its description mentions `$control-return`, `/control-return`, and "three next steps"), for example `"control return"`, `"三個下一步"`, `"下一步選項"`. Then change the header count to `# 50 skills · 10 categories · 6 workflows`.
3. Run:

```bash
python3 scripts/validate_skills_catalog.py --write
python3 scripts/validate_skills_catalog.py --check
python3 -m unittest tests.test_validate_skills_catalog 2>&1 | tail -3
```

Expected: `--check` is clean, the unit tests all pass (the baseline failure is gone), and `git diff SKILLS_CATALOG.md` adds exactly two rows, `control-return` and `lesson`. If the validator reports anything else about `control-return` (for example a missing runtime gate), fix that file only as far as the message requires and tell the user.

- [x] **Step 8: Checkpoint** (suggested message later: `feat(lesson): register lesson skill in catalog and router`)

---

### Task 7: Merge lesson proposals into the `activity-logger` wrap-up

**Files:**
- Modify: `activity-logger/SKILL.md`

- [x] **Step 1: Add a subsection before `## Activity Record Format`**

Replace the line `## Activity Record Format` with:

```markdown
### Lesson proposals (optional)

If the `lesson` skill is installed and configured (`lesson/config.json` exists) and this session hit a lesson-worthy event (a pitfall fixed, an assumption disproved, or the user correcting the agent), draft at most two lessons following the `lesson` skill's capture flow and include them in the same closing message as the activity summary, so the user answers once. Write a lesson only after the user confirms it. If the `lesson` skill is missing or not configured, skip this step without comment.

## Activity Record Format
```

- [x] **Step 2: Add the optional dependency**

Under `### Optional`, add a bullet:

```
- `lesson` skill - when installed and configured, wrap-up also offers lesson proposals (see "Lesson proposals")
```

- [x] **Step 3: Verify the existing activity-logger test still passes**

Run: `bash activity-logger/tests/test_reference_logging.sh; echo "exit=$?"`
Expected: `exit=0`.

- [x] **Step 4: Checkpoint** (suggested message later: `feat(activity-logger): offer lesson proposals at wrap-up`)

---

### Task 8: Configure for real and migrate the existing feedback memories

This task needs the user in the loop. Nothing here is committed and no original file is touched.

- [x] **Step 1: Ask for the lessons folder**

Ask the user for the folder (a subfolder of their note vault, per the design). Do not guess the path. If it does not exist, ask whether to create it.

- [x] **Step 2: Configure**

```bash
python3 lesson/scripts/lesson.py setup --dir "<folder from the user>"      # add --create only if the user agreed
git status --short lesson/config.json
```

Expected: `setup` prints `configured: .../lesson/config.json`; `git status` prints nothing for that file (it is ignored).

- [x] **Step 3: List the migration candidates**

The source is the current project's memory folder, `~/.claude/projects/<encoded-project-path>/memory`.

```bash
python3 lesson/scripts/lesson.py migrate --from "<memory folder>" --plan | python3 -c "import json,sys; [print(r['file'], '| migrated' if r['already_migrated'] else '') for r in json.load(sys.stdin)]"
```

Expected: one line per `feedback` memory (9 at the time of the spec) and no `project_*` or `reference_*` files.

- [x] **Step 4: Draft the mapping with the user**

For each file draft a `rule` (one line, at most 120 characters, actionable, in the memory's own language) and guess a scope. Show a table with columns original file, new rule, scope. Let the user edit any row. Rules that only make sense for one repository get `scope: project` and that project's folder name. Do not decide scope for the user.

- [x] **Step 5: Apply**

Write the confirmed mapping to a temporary file (`[{"file": "...", "rule": "...", "scope": "global"}]`, plus `"project"` for project rows) and run:

```bash
python3 lesson/scripts/lesson.py migrate --from "<memory folder>" --apply "<mapping file>"
```

Expected: `written: N  skipped(already migrated): 0`. Running it a second time must print `written: 0`.

- [x] **Step 6: Verify**

```bash
python3 lesson/scripts/lesson.py digest --project "$(basename "$PWD")"
python3 lesson/scripts/lesson.py list
```

Expected: the status line counts match the mapping (global rows and project rows for this project), every rule appears, and `list` shows no unparsable files or conflict copies. Open one migrated file and confirm its 背景 section contains the original body verbatim.

- [x] **Step 7: Leave the originals alone**

Tell the user the originals still load through built-in memory, so rules appear twice until they are archived, and that archiving (move to a backup folder, not delete, because `~/.claude/projects` is not under Git) is a separate decision after Task 9 confirms the digest loads.

---

### Task 9: Add the snippet to the agent entry files

Only after the user confirms each file separately.

- [x] **Step 1: Render the snippet**

Run: `python3 lesson/scripts/lesson.py snippet`
Expected: the three-line Lessons section with the real script path filled in.

- [x] **Step 2: For each of `~/.claude/CLAUDE.md` and `~/.codex/AGENTS.md`**

1. Show the user the exact text to append and ask for a yes for this file.
2. Back it up: `cp <file> <file>.bak-lesson`
3. Append a blank line and the rendered snippet.
4. Show `diff <file>.bak-lesson <file>`; it must show only the added lines.

Do not touch omp, Cursor or Gemini files (out of scope). The existing "Session 結束前" rule in `CLAUDE.md` and `AGENTS.md` stays unchanged; `activity-logger` now handles the merged question.

- [x] **Step 3: Verify in fresh sessions**

From a scratch git repo that has no project-level instruction files:

```bash
SCRATCH="$(mktemp -d)"; git init --quiet "$SCRATCH"; cd "$SCRATCH"
codex exec "What is 2+2?" 2>&1 | tail -5
claude -p "What is 2+2?" 2>&1 | head -3
cd - >/dev/null; rm -rf "$SCRATCH"
```

Expected for each agent: the reply starts with `lessons: 全域 N 條、專案 0 條` using the real counts. Record which agents did not, and tell the user.

- [x] **Step 4: Check permission prompts for every Claude profile the user launches with**

An entry-file instruction that triggers a permission prompt at every session start defeats the purpose. Ask which settings profiles the user starts Claude with (the main `settings.json` and the profile files next to it). For each, read `permissions.defaultMode` and `permissions.allow`:

```bash
python3 - <<'PYEND'
import json, glob, os
for f in sorted(glob.glob(os.path.expanduser("~/.claude/settings*.json"))):
    p = json.load(open(f)).get("permissions", {})
    allow = [a for a in p.get("allow", []) if "python" in a.lower()]
    print(os.path.basename(f), "| mode:", p.get("defaultMode"), "| python rules:", allow or "none")
PYEND
```

A profile is fine if its mode is `bypassPermissions` or it already allows the digest command. Checked when this plan was written: the main file and two of the profiles use `bypassPermissions`; one profile (`settings-C4E.json`) is in default mode with no python rule; one (`settings-RDSec.json`) already allows `Bash(python3:*)`. For each profile that would prompt, propose one exact allow rule for the digest command (the `python3 <script path> digest` form printed by `snippet`), show the user the diff, back up the file, and edit only after a yes. Then run one Claude check under that profile, interactively or with that profile's settings, and confirm no prompt appears. (Outcome: the user does not use `settings-C4E.json`, so no settings file was changed.)

- [x] **Step 5: Note the follow-up**

Tell the user to watch the first line of the first reply for two weeks. A missing line means that agent skipped the command, which is the trigger for adding a hook (out of scope for this version).

---

### Task 10: Quality gates and hand-off

- [x] **Step 1: Run the skill audit**

Invoke the `skill-auditor` skill on `lesson/` and `activity-logger/` (the repo's rule after any skill change). Fix findings that are real; report the rest.

- [x] **Step 2: Privacy scan of everything that could be tracked**

```bash
grep -rnE "/Users/|/home/|@gmail|CloudStorage" lesson docs/superpowers/specs/2026-09-30-lesson-capture-design.md || echo "clean"
# Then grep for the user's own username and vault folder name. Ask the user for both, put them in shell variables, and never write them into a tracked file.
grep -rnF -e "${USERNAME_TO_CHECK:?ask the user}" -e "${VAULT_NAME_TO_CHECK:?ask the user}" lesson docs/superpowers/specs/2026-09-30-lesson-capture-design.md docs/superpowers/plans/2026-09-30-lesson-capture.md || echo "clean"
git status --short
```

Expected: `clean`; `git status` shows no `lesson/config.json` and no lesson data files.

- [x] **Step 3: Run all checks once more**

```bash
bash lesson/tests/test_lesson.sh
bash activity-logger/tests/test_reference_logging.sh && echo activity-logger-ok
python3 scripts/validate_skills_catalog.py --check 2>&1 | tail -1
```

Expected: `PASS: test_lesson.sh`, `activity-logger-ok`, and a clean validator (Task 6 Step 7 registered `control-return`).

- [x] **Step 4: Native review**

Risk tier L1 (new behavior in a script plus an edit to an existing skill, nothing touching auth or data stores). Invoke `code-review-claude` once on the diff (`git diff` plus the new `lesson/` files). Apply real findings, then re-run Step 3. (Outcome: five defects found by probing the script, each reproduced first, fixed with a new test, and confirmed by a mutation check: non-object JSON in `add`, non-object rows and invalid JSON in `migrate --apply`, `setup` storing a relative folder, and over-long rules printed unclipped. A trust-boundary note was added to `SKILL.md`.)

- [x] **Step 5: Completion gate**

Apply `completion-gate` and report VERIFIED / NOT VERIFIED per item, including the Task 4 results, the Task 9 fresh-session results and the pre-existing `control-return` failure.

- [ ] **Step 6: Ask the user for commit approval**

Do not commit. Propose two commits and wait:

1. `docs(specs): add lesson capture design and plan`
2. `feat(lesson): add lesson capture skill` (includes `lesson/`, catalog, router, `CLAUDE.md`, `README.md`, `activity-logger/SKILL.md`, `.gitignore`)

Remind the user that running `skill-sync` afterwards mirrors the skill to the other agent folders; the entry-file commands use the absolute script path, so they work either way.
