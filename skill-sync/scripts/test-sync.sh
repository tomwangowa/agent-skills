#!/usr/bin/env bash
set -euo pipefail

REPO_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)"
FIXTURE_ROOT="$(mktemp -d)"
SOURCE_ROOT="$FIXTURE_ROOT/source"
EXISTING_TARGET="$FIXTURE_ROOT/targets/existing"
MISSING_TARGET="$FIXTURE_ROOT/targets/missing"
NON_DIRECTORY_TARGET="$FIXTURE_ROOT/targets/not-a-directory"
PREVIEW_DIFF_TARGET="$FIXTURE_ROOT/targets/preview-diff"
FAKE_BIN="$FIXTURE_ROOT/fake-bin"
EXPECTED_SENTINEL="$FIXTURE_ROOT/expected-keep.txt"
BYTECODE_PREVIEW_PATH="__pycache__/sample.cpython-313.pyc"
AUDIT_REPORT_PATH="skill-router-audit-report.md"
NESTED_AUDIT_SAMPLE_PATH="skill-auditor/examples/sample-audit-report.md"

cleanup() {
    rm -rf "$FIXTURE_ROOT"
}
trap cleanup EXIT

fail() {
    echo "FAIL: $*" >&2
    exit 1
}

assert_contains() {
    local haystack="$1"
    local needle="$2"
    [[ "$haystack" == *"$needle"* ]] || fail "expected output to contain: $needle"
}

assert_not_contains() {
    local haystack="$1"
    local needle="$2"
    [[ "$haystack" != *"$needle"* ]] || fail "output must not contain: $needle"
}

assert_skipped_target() {
    local output="$1"
    local target="$2"
    local line

    while IFS= read -r line; do
        [[ "$line" == *"$target"* && "$line" == *"skipped"* ]] && return
    done <<< "$output"

    fail "expected $target to be reported as skipped"
}

snapshot_target_tree() {
    local target="$1"

    {
        find "$target" -type d -print | LC_ALL=C sort
        find "$target" -type f -exec cksum {} \; | LC_ALL=C sort
    }
}

assert_dry_run_unchanged_targets() {
    cmp -s "$EXISTING_TARGET/keep.txt" "$EXPECTED_SENTINEL" \
        || fail "dry-run modified the existing target sentinel"
    [[ "$(snapshot_target_tree "$EXISTING_TARGET")" == "$INITIAL_TARGET_TREE" ]] \
        || fail "dry-run wrote additional files to the existing target"
    [[ ! -e "$MISSING_TARGET" ]] || fail "dry-run created the missing target"
}

run_dry_sync() {
    local output_var="$1"
    shift
    local output
    local status

    set +e
    output="$(bash "$SOURCE_ROOT/skill-sync/scripts/sync.sh" "$@" 2>&1)"
    status=$?
    set -e

    printf -v "$output_var" '%s' "$output"
    [[ $status -eq 0 ]] || fail "dry-run exited $status: $output"
}

run_dry_sync_with_failing_rsync() {
    local output_var="$1"
    shift
    local output
    local status

    set +e
    output="$(PATH="$FAKE_BIN:$PATH" bash "$SOURCE_ROOT/skill-sync/scripts/sync.sh" "$@" 2>&1)"
    status=$?
    set -e

    printf -v "$output_var" '%s' "$output"
    [[ $status -ne 0 ]] || fail "expected dry-run failure, got exit 0: $output"
}

run_dry_sync_expect_failure() {
    local output_var="$1"
    shift
    local output
    local status

    set +e
    output="$(bash "$SOURCE_ROOT/skill-sync/scripts/sync.sh" "$@" 2>&1)"
    status=$?
    set -e

    printf -v "$output_var" '%s' "$output"
    [[ $status -ne 0 ]] || fail "expected dry-run failure, got exit 0: $output"
}

run_interactive_sync_with_failing_preview() {
    local output_var="$1"
    shift
    local output
    local status

    set +e
    output="$(printf 'n\n' | PATH="$FAKE_BIN:$PATH" bash "$SOURCE_ROOT/skill-sync/scripts/sync.sh" "$@" 2>&1)"
    status=$?
    set -e

    printf -v "$output_var" '%s' "$output"
    [[ $status -eq 0 ]] || fail "interactive preview exited $status: $output"
}

run_interactive_sync_expect_failure() {
    local output_var="$1"
    shift
    local output
    local status

    set +e
    output="$(printf 'n\n' | bash "$SOURCE_ROOT/skill-sync/scripts/sync.sh" "$@" 2>&1)"
    status=$?
    set -e

    printf -v "$output_var" '%s' "$output"
    [[ $status -ne 0 ]] || fail "expected interactive failure, got exit 0: $output"
}

mkdir -p "$SOURCE_ROOT/skill-sync/scripts" "$SOURCE_ROOT/sample-skill" "$EXISTING_TARGET" "$PREVIEW_DIFF_TARGET" "$FAKE_BIN"
cp "$REPO_ROOT/skill-sync/scripts/sync.sh" "$SOURCE_ROOT/skill-sync/scripts/sync.sh"
chmod +x "$SOURCE_ROOT/skill-sync/scripts/sync.sh"
REAL_RSYNC="$(command -v rsync)"
printf '%s\n' '#!/usr/bin/env bash' "if [[ \"\${!#}\" == \"$EXISTING_TARGET/\" ]]; then" '    echo "simulated rsync dry-run failure" >&2' '    exit 23' 'fi' "exec \"$REAL_RSYNC\" \"\$@\"" > "$FAKE_BIN/rsync"
chmod +x "$FAKE_BIN/rsync"
printf '%s\n' '---' 'name: sample-skill' '---' > "$SOURCE_ROOT/sample-skill/SKILL.md"
mkdir -p "$SOURCE_ROOT/__pycache__"
printf 'fixture bytecode\n' > "$SOURCE_ROOT/$BYTECODE_PREVIEW_PATH"
printf 'fixture audit report\n' > "$SOURCE_ROOT/$AUDIT_REPORT_PATH"
mkdir -p "$(dirname "$SOURCE_ROOT/$NESTED_AUDIT_SAMPLE_PATH")"
printf 'fixture audit sample\n' > "$SOURCE_ROOT/$NESTED_AUDIT_SAMPLE_PATH"
printf 'keep this target unchanged\n' > "$EXISTING_TARGET/keep.txt"
cp "$EXISTING_TARGET/keep.txt" "$EXPECTED_SENTINEL"
printf '%s\n%s\n' "$EXISTING_TARGET" "$MISSING_TARGET" > "$SOURCE_ROOT/.skill-sync-targets"
printf 'skill-sync\n__pycache__/\n/*-audit-report.md\n' > "$SOURCE_ROOT/.skill-sync-ignore"
INITIAL_TARGET_TREE="$(snapshot_target_tree "$EXISTING_TARGET")"

run_dry_sync dry_output --dry-run
assert_skipped_target "$dry_output" "$MISSING_TARGET"
assert_contains "$dry_output" "deleting keep.txt"
assert_not_contains "$dry_output" "$BYTECODE_PREVIEW_PATH"
assert_not_contains "$dry_output" "$AUDIT_REPORT_PATH"
assert_contains "$dry_output" "$NESTED_AUDIT_SAMPLE_PATH"
assert_not_contains "$dry_output" "Proceed with sync?"
assert_dry_run_unchanged_targets

run_dry_sync additive_output --dry-run --no-delete
assert_contains "$additive_output" "mode: additive (--no-delete)"
assert_not_contains "$additive_output" "deleting keep.txt"
assert_not_contains "$additive_output" "$BYTECODE_PREVIEW_PATH"
assert_not_contains "$additive_output" "$AUDIT_REPORT_PATH"
assert_contains "$additive_output" "$NESTED_AUDIT_SAMPLE_PATH"
assert_not_contains "$additive_output" "Proceed with sync?"
assert_dry_run_unchanged_targets

run_dry_sync_with_failing_rsync failed_preview_output --dry-run
assert_contains "$failed_preview_output" "rsync error:"
assert_contains "$failed_preview_output" "simulated rsync dry-run failure"
assert_not_contains "$failed_preview_output" "All existing targets already up to date."
assert_dry_run_unchanged_targets

printf 'keep this preview target unchanged\n' > "$PREVIEW_DIFF_TARGET/keep.txt"
printf '%s\n%s\n' "$EXISTING_TARGET" "$PREVIEW_DIFF_TARGET" > "$SOURCE_ROOT/.skill-sync-targets"
run_interactive_sync_with_failing_preview interactive_preview_output
assert_contains "$interactive_preview_output" "simulated rsync dry-run failure"
assert_contains "$interactive_preview_output" "$PREVIEW_DIFF_TARGET"
assert_contains "$interactive_preview_output" "Proceed with sync?"
assert_contains "$interactive_preview_output" "Sync cancelled."
assert_dry_run_unchanged_targets

printf 'not a directory\n' > "$NON_DIRECTORY_TARGET"
printf '%s\n' "$NON_DIRECTORY_TARGET" > "$SOURCE_ROOT/.skill-sync-targets"
run_dry_sync_expect_failure non_directory_output --dry-run
assert_contains "$non_directory_output" "$NON_DIRECTORY_TARGET"
assert_contains "$non_directory_output" "not a directory"
assert_not_contains "$non_directory_output" "All existing targets already up to date."

run_interactive_sync_expect_failure normal_non_directory_output
assert_contains "$normal_non_directory_output" "Creating $NON_DIRECTORY_TARGET"
assert_not_contains "$normal_non_directory_output" "target error:"

echo "PASS: skill-sync --dry-run is read-only and reports preview failures"
