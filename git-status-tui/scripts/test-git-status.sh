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

# ---- test blocks are added by later tasks ----

printf '\n%d passed, %d failed\n' "$PASS" "$FAIL"
[ "$FAIL" -eq 0 ]
