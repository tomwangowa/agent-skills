#!/usr/bin/env bash
# Dependency-free test harness for git-status.sh. Run: bash test-git-status.sh
set -u
HERE=$(cd "$(dirname "$0")" && pwd)
# shellcheck source=/dev/null
. "$HERE/git-status.sh"   # main is guarded → no side effects

PASS=0; FAIL=0
assert_eq() { # label expected actual
  if [ "$2" = "$3" ]; then PASS=$((PASS+1)); else
    FAIL=$((FAIL+1)); printf 'FAIL %s\n  expected: [%s]\n  actual:   [%s]\n' "$1" "$2" "$3"; fi
}
assert_contains() { # label needle haystack
  case "$3" in *"$2"*) PASS=$((PASS+1));;
    *) FAIL=$((FAIL+1)); printf 'FAIL %s\n  missing: [%s]\n  in:\n%s\n' "$1" "$2" "$3";; esac
}
# A throwaway git repo in a temp dir; echoes its path. Caller cd's into it.
mk_repo() {
  local d; d=$(mktemp -d)
  git -C "$d" init -q
  git -C "$d" config user.email t@t; git -C "$d" config user.name t
  printf '%s' "$d"
}

# --- Task 1: width / truncation ---
assert_eq "width ascii"  "3" "$(disp_width abc)"
assert_eq "width cjk"    "4" "$(disp_width 中文)"
assert_eq "width mixed"  "3" "$(disp_width a中)"
assert_eq "width empty"  "0" "$(disp_width '')"
assert_eq "width ansi-stripped" "7" "$(disp_width "$(printf '\033[31m● dirty\033[0m')")"
assert_eq "trunc none"   "短"  "$(trunc_end 短 18)"
assert_eq "trunc end"    "code-review-claud…" "$(trunc_end 'code-review-claude/SKILL.md' 18)"
assert_eq "trunc cjk width" "7" "$(disp_width "$(trunc_end '中文檔名測試很長很長' 8)")"
assert_contains "trunc mid" "…" "$(trunc_mid '/Users/tom_wang/.claude/skills/git-status-tui/scripts' 30)"
assert_eq "abbrev home" "~/x" "$(HOME=/home/u abbrev_path /home/u/x 40)"

# ---- test blocks are added by later tasks ----

printf '\n%d passed, %d failed\n' "$PASS" "$FAIL"
[ "$FAIL" -eq 0 ]
