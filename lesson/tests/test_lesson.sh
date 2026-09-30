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
