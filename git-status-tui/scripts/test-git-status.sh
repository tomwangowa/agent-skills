#!/usr/bin/env bash
# Dependency-free test harness for git-status.sh. Run: bash test-git-status.sh
set -u
HERE=$(cd "$(dirname "$0")" && pwd)
# shellcheck source=/dev/null
. "$HERE/git-status.sh"   # main is guarded → no side effects

# Results recorded to a file so assertions inside ( subshells ) still count.
RESULTS=$(mktemp); export RESULTS
assert_eq() { # label expected actual
  if [ "$2" = "$3" ]; then printf 'P\n' >>"$RESULTS"; else
    printf 'F\n' >>"$RESULTS"; printf 'FAIL %s\n  expected: [%s]\n  actual:   [%s]\n' "$1" "$2" "$3"; fi
}
assert_contains() { # label needle haystack
  case "$3" in *"$2"*) printf 'P\n' >>"$RESULTS";;
    *) printf 'F\n' >>"$RESULTS"; printf 'FAIL %s\n  missing: [%s]\n  in:\n%s\n' "$1" "$2" "$3";; esac
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

# --- Task 2: style ---
COLOR=1; assert_contains "paint on"  "$(printf '\033[31m')" "$(paint red X)"
COLOR=0; assert_eq       "paint off" "X" "$(paint red X)"
unset COLOR

# --- Task 3: box primitives ---
INNER=20
assert_eq "row width plain"   "24" "$(disp_width "$(row 'hi')")"
assert_eq "row width colored" "24" "$(disp_width "$(COLOR=1 row "$(COLOR=1 paint red dot)")")"
assert_eq "row width cjk"     "24" "$(disp_width "$(row '中文 狀態')")"
assert_eq "ttop width"        "24" "$(disp_width "$(ttop 'git status')")"
assert_eq "ftitle width"      "24" "$(disp_width "$(ftitle 'working tree')")"
assert_eq "fbot width"        "24" "$(disp_width "$(fbot)")"
assert_eq "cell pad"   "8" "$(disp_width "$(cell 'main' 8)")"
assert_eq "cell trunc" "8" "$(disp_width "$(cell 'feature/very-long-branch' 8)")"
unset INNER COLOR

# --- Task 4: git data helpers ---
( d=$(mk_repo); cd "$d"
  printf 'x\n' > f; git add f; git commit -qm init
  assert_eq "g_root"   "$(cd "$d" && pwd -P)" "$(g_root)"
  assert_eq "g_branch" "$(git symbolic-ref --short HEAD)" "$(g_branch_or_detached)"
  assert_contains "g_head" "init" "$(g_head)"
  assert_eq "g_upstream none" "no upstream" "$(g_upstream)"
  assert_eq "g_stash 0" "0" "$(g_stash)"
  assert_eq "g_inprogress none" "" "$(g_inprogress)"
  sha=$(git rev-parse --short HEAD); git checkout -q "$sha"
  assert_contains "g_detached" "detached" "$(g_branch_or_detached)"
  rm -rf "$d" )
( d=$(mk_repo); cd "$d"
  assert_contains "g_empty head" "no commits" "$(g_head)"
  rm -rf "$d" )

# --- Task 5: porcelain ---
SAMPLE=$(printf 'M  a\n M b\n?? c\nMM d\n')
assert_eq "counts" "2 2 1" "$(printf '%s\n' "$SAMPLE" | parse_counts)"
# change_lines emits "XY path<TAB>label"; the "(label)" wrapping is render_single's job.
assert_contains "cl staged"    "$(printf 'M  a\tstaged')"    "$(printf '%s\n' "$SAMPLE" | change_lines 10)"
assert_contains "cl modified"  "$(printf ' M b\tmodified')"  "$(printf '%s\n' "$SAMPLE" | change_lines 10)"
assert_contains "cl untracked" "$(printf '?? c\tuntracked')" "$(printf '%s\n' "$SAMPLE" | change_lines 10)"
BIG=$(for i in 1 2 3; do printf '?? f%s\n' "$i"; done)
assert_contains "cl overflow" "+1 more" "$(printf '%s\n' "$BIG" | change_lines 2)"
assert_eq "fmt_ab" "↑1 ↓0" "$(fmt_ab 0 1)"

# --- Task 6: render_single ---
( d=$(mk_repo); cd "$d"
  printf 'x\n' > a; git add a; git commit -qm "first commit"
  printf 'y\n' > a; printf 'z\n' > b
  out=$(COLOR=0 render_single)
  assert_contains "rs header"  "git status"    "$out"
  assert_contains "rs branch"  "$(git symbolic-ref --short HEAD)" "$out"
  assert_contains "rs head"    "first commit"  "$out"
  assert_contains "rs section" "working tree"  "$out"
  assert_contains "rs changes" "(untracked)"   "$out"
  assert_contains "rs noupstream" "no upstream" "$out"
  widths=$(printf '%s\n' "$out" | while IFS= read -r l; do disp_width "$l"; echo; done | sort -u | grep -c '')
  assert_eq "rs aligned" "1" "$widths"
  rm -rf "$d" )
( d=$(mk_repo); cd "$d"; printf 'x\n'>a; git add a; git commit -qm init
  assert_contains "rs clean" "clean" "$(COLOR=0 render_single)"; rm -rf "$d" )
( d=$(mk_repo); cd "$d"; printf 'x\n'>a; git add a; git commit -qm init
  printf 'y\n' > 中文檔名.txt   # untracked CJK filename must render literally, not octal-escaped
  out=$(COLOR=0 render_single)
  assert_contains "rs cjk literal"  "中文檔名.txt" "$out"
  assert_contains "rs cjk no-octal" "no-octal" "$(case "$out" in *'\3'*) echo octal;; *) echo no-octal;; esac)"
  rm -rf "$d" )
( d=$(mk_repo); cd "$d"; printf 'x\n'>a; git add a; git commit -qm init
  touch "$(git rev-parse --git-dir)/MERGE_HEAD"
  assert_contains "rs warn" "merge in progress" "$(COLOR=0 render_single)"; rm -rf "$d" )

# ---- test blocks are added by later tasks ----

# grep -c always prints a count (0 when no match) even though it exits 1 then.
PASS=$(grep -c '^P' "$RESULTS"); FAIL=$(grep -c '^F' "$RESULTS")
rm -f "$RESULTS"
printf '\n%d passed, %d failed\n' "$PASS" "$FAIL"
[ "$FAIL" -eq 0 ]
