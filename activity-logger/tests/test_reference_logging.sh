#!/usr/bin/env bash

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "$0")/../scripts" && pwd)"
SCRIPT="$SCRIPT_DIR/log_activity.sh"
TMP_DIR="$(mktemp -d)"
trap 'rm -rf "$TMP_DIR"' EXIT

assert_eq() {
    local actual="$1"
    local expected="$2"
    local message="${3:-assertion failed}"
    if [[ "$actual" != "$expected" ]]; then
        echo "$message: expected [$expected], got [$actual]" >&2
        exit 1
    fi
}

init_fixture_repo() {
    local path="$1"
    mkdir -p "$path"
    git init --quiet "$path"
    git -C "$path" config user.name "Activity Fixture"
    git -C "$path" config user.email "activity-fixture@example.com"
}

CURRENT_REPO="$TMP_DIR/current-repo"
REFERENCE_REPO="$TMP_DIR/reference-repo"
NON_GIT_DIR="$TMP_DIR/non-git"
ACTIVITIES_DIR="$TMP_DIR/activities"

init_fixture_repo "$CURRENT_REPO"
init_fixture_repo "$REFERENCE_REPO"
mkdir -p "$REFERENCE_REPO/docs" "$NON_GIT_DIR"
printf 'current fixture\n' > "$CURRENT_REPO/README.md"
git -C "$CURRENT_REPO" add README.md
git -C "$CURRENT_REPO" commit --quiet -m "current fixture"
printf 'private-reference-content\n' > "$REFERENCE_REPO/docs/reference.md"
git -C "$REFERENCE_REPO" add docs/reference.md
git -C "$REFERENCE_REPO" commit --quiet -m "reference fixture"
printf 'private-non-git-content\n' > "$NON_GIT_DIR/notes.md"

run_log() {
    local session_id="$1"
    shift
    (
        cd "$CURRENT_REPO"
        CLAUDE_ACTIVITIES_DIR="$ACTIVITIES_DIR" \
        CLAUDE_SESSION_ID="$session_id" \
            bash "$SCRIPT" -d "fixture $session_id" "$@" >/dev/null
    )
    find "$ACTIVITIES_DIR" -maxdepth 1 -type f \
        -name "${session_id}_*.json" -print | head -n 1
}

record=$(run_log clean \
    --reference "../reference-repo/docs/reference.md" \
    --reference "$REFERENCE_REPO/docs/reference.md")
jq empty "$record"
assert_eq "$(jq -r '.activities[0].references | length' "$record")" "2"
assert_eq "$(jq -r '.activities[0].references[1].relative_path' "$record")" "docs/reference.md"
assert_eq "$(jq -r '.activities[0].references[1].tracked_at_log_time' "$record")" "true"
assert_eq "$(jq -r '.activities[0].references[1].working_tree_status' "$record")" "clean"
assert_eq "$(jq -r '.activities[0].references[1].path_status' "$record")" "tracked"

record_without_references=$(run_log no_references)
assert_eq "$(jq -r '.activities[0].references | length' "$record_without_references")" "0"

printf 'modified-reference-content\n' > "$REFERENCE_REPO/docs/reference.md"
record=$(run_log modified --reference "$REFERENCE_REPO/docs/reference.md")
assert_eq "$(jq -r '.activities[0].references[0].tracked_at_log_time' "$record")" "true"
assert_eq "$(jq -r '.activities[0].references[0].working_tree_status' "$record")" "modified"

printf 'untracked-reference-content\n' > "$REFERENCE_REPO/docs/untracked.md"
record=$(run_log untracked --reference "$REFERENCE_REPO/docs/untracked.md")
assert_eq "$(jq -r '.activities[0].references[0].tracked_at_log_time' "$record")" "false"
assert_eq "$(jq -r '.activities[0].references[0].working_tree_status' "$record")" "untracked"

record=$(run_log missing --reference "$REFERENCE_REPO/docs/missing.md")
assert_eq "$(jq -r '.activities[0].references[0].relative_path' "$record")" "docs/missing.md"
assert_eq "$(jq -r '.activities[0].references[0].working_tree_status' "$record")" "missing"

record=$(run_log non_git --reference "$NON_GIT_DIR/notes.md")
assert_eq "$(jq -r '.activities[0].references[0].repo_root' "$record")" "null"
assert_eq "$(jq -r '.activities[0].references[0].path_status' "$record")" "not-git"

if (
    cd "$CURRENT_REPO"
    CLAUDE_ACTIVITIES_DIR="$ACTIVITIES_DIR" CLAUDE_SESSION_ID="missing-value" \
        bash "$SCRIPT" -d "missing reference value" --reference
) >/dev/null 2>&1; then
    echo "--reference without a value unexpectedly succeeded" >&2
    exit 1
fi

for record in "$ACTIVITIES_DIR"/*.json; do
    jq empty "$record"
    if jq -e --arg secret "private-reference-content" \
        'tostring | contains($secret)' "$record" >/dev/null; then
        echo "reference document content was copied into $record" >&2
        exit 1
    fi
done

echo "reference logging fixture tests passed"
