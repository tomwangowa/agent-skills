# git-status-tui Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** A read-only skill that renders a box-drawing panel of the current git location (single repo) or a one-line-per-repo overview (parent directory of repos), legible inside an Agent CLI.

**Architecture:** One bash script `git-status.sh` (functions + a guarded `main`, so it is source-able with zero side effects for testing). All git access is read-only. Unicode display-width + truncation is delegated to a single inlined `perl` helper (`_udisp`) — bash 3.2 cannot slice UTF-8 safely. A dependency-free bash harness `test-git-status.sh` sources the script and runs unit + temp-repo integration tests.

**Tech Stack:** bash 3.2-compatible, `git`, `perl` (both universal on macOS/Linux). No bats, no shellcheck (not installed).

---

## Design source

Implements `docs/specs/2026-06-05-git-status-tui-design.md`. Read it first.

## Invariants (load-bearing — every task must preserve these)

1. **`git-status.sh` is side-effect-free when sourced.** Put `set -e`/`set -u` *inside* `main()`, never at file scope, or sourcing aborts the test harness. The file ends with:
   ```bash
   if [ "${BASH_SOURCE[0]:-$0}" = "${0}" ]; then main "$@"; fi
   ```
2. **`disp_width` strips ANSI before measuring** (`s/\x1b\[[0-9;]*m//g`). Therefore painted strings measure by *visible* width and column alignment survives color.
3. **`trunc_end`/`trunc_mid` receive PLAIN text only — never painted text.** Painting wraps the *result* of truncation. `row()` only pads (never truncates); callers truncate plain values first, then optionally paint.
4. **Entry detection:** inside a git work tree → single-repo mode; otherwise → parent-overview mode. (Same rule as repo-sync. A non-repo dir nested inside an outer repo therefore renders the outer repo — documented behavior, not a bug.)

## File Structure

- Create: `git-status-tui/SKILL.md` — when to run the script, how to read output, declares `git + perl` requirement.
- Create: `git-status-tui/scripts/git-status.sh` — all logic + rendering. `main` guarded.
- Create: `git-status-tui/scripts/test-git-status.sh` — dependency-free assertion harness; sources the script.
- Modify: `CLAUDE.md` — add the skill to "Available Skills".

## Geometry (fixed)

- Single panel inner content width `INNER=58`. Row = `│ ` + content padded to 58 + ` │` → outer 62; titled/plain borders span `INNER+2`=60 between corners.
- Overview `INNER=66`. Columns (left-aligned, 2-space gaps): REPO 16, BRANCH 16, STATE 8, AHEAD/BEHIND 12, STASH 6 (= 64 + gaps).

---

### Task 0: Scaffold + green harness

**Files:**
- Create: `git-status-tui/scripts/git-status.sh`
- Create: `git-status-tui/scripts/test-git-status.sh`

- [ ] **Step 1: Create the script skeleton (source-safe, empty main)**

`git-status-tui/scripts/git-status.sh`:
```bash
#!/usr/bin/env bash
# git-status.sh — read-only git status dashboard (single repo) / overview (parent dir).
# Requires: git, perl. bash 3.2 compatible. Source-safe (main is guarded).

# ---- functions are added by later tasks ----

main() {
  set -u
  printf 'git-status.sh: not yet implemented\n' >&2
  return 0
}

if [ "${BASH_SOURCE[0]:-$0}" = "${0}" ]; then main "$@"; fi
```

- [ ] **Step 2: Create the test harness**

`git-status-tui/scripts/test-git-status.sh`:
```bash
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
```

- [ ] **Step 3: Run the harness — verify it is green with zero tests**

Run: `bash git-status-tui/scripts/test-git-status.sh; echo "exit=$?"`
Expected: `0 passed, 0 failed` then `exit=0`

- [ ] **Step 4: Commit**

```bash
git add git-status-tui/scripts/git-status.sh git-status-tui/scripts/test-git-status.sh
git commit -m "feat(git-status-tui): scaffold script + test harness"
```

---

### Task 1: Unicode width + truncation (`_udisp`, `disp_width`, `trunc_end`, `trunc_mid`, `abbrev_path`)

**Files:**
- Modify: `git-status-tui/scripts/git-status.sh`
- Modify: `git-status-tui/scripts/test-git-status.sh`

- [ ] **Step 1: Add failing tests** (insert before the summary `printf` in the harness)

```bash
# --- Task 1: width / truncation ---
assert_eq "width ascii"  "3" "$(disp_width abc)"
assert_eq "width cjk"    "4" "$(disp_width 中文)"
assert_eq "width mixed"  "3" "$(disp_width a中)"
assert_eq "width empty"  "0" "$(disp_width '')"
assert_eq "width ansi-stripped" "7" "$(disp_width "$(printf '\033[31m● dirty\033[0m')")"
assert_eq "trunc none"   "短"  "$(trunc_end 短 18)"
assert_eq "trunc end"    "code-review-claud…" "$(trunc_end 'code-review-claude/SKILL.md' 18)"
# CJK end-truncate must stay within display width
assert_eq "trunc cjk width" "7" "$(disp_width "$(trunc_end '中文檔名測試很長很長' 8)")"
assert_contains "trunc mid" "…" "$(trunc_mid '/Users/tom_wang/.claude/skills/git-status-tui/scripts' 30)"
assert_eq "abbrev home" "~/x" "$(HOME=/home/u abbrev_path /home/u/x 40)"
```

- [ ] **Step 2: Run harness — verify failures**

Run: `bash git-status-tui/scripts/test-git-status.sh; echo "exit=$?"`
Expected: multiple `FAIL` lines (functions undefined), `exit=1`

- [ ] **Step 3: Implement** (add to `git-status.sh` above `main`)

```bash
# _udisp <mode> [max]  — reads string on STDIN. mode: width | trunc_end | trunc_mid.
# ANSI escapes are stripped before measuring so visible width is used.
_udisp() {
  perl -CSDA -se '
    my $s = do { local $/; <STDIN> };
    $s =~ s/\x1b\[[0-9;]*m//g;
    my $wide = qr/[\x{1100}-\x{115F}\x{2E80}-\x{A4CF}\x{AC00}-\x{D7A3}\x{F900}-\x{FAFF}\x{FE30}-\x{FE4F}\x{FF00}-\x{FF60}\x{FFE0}-\x{FFE6}]/;
    my $cw = sub { $_[0] =~ $wide ? 2 : 1 };
    my @c = split //, $s;
    my $tot = 0; $tot += $cw->($_) for @c;
    if ($mode eq "width") { print $tot; exit; }
    if ($tot <= $max) { print $s; exit; }
    if ($mode eq "trunc_end") {
      my $lim = $max - 1; my ($o, $w) = ("", 0);
      for my $ch (@c) { my $x = $cw->($ch); last if $w + $x > $lim; $o .= $ch; $w += $x; }
      print $o . "\x{2026}"; exit;
    }
    if ($mode eq "trunc_mid") {
      my $b = $max - 1; my $h = int($b / 2); my $t = $b - $h;
      my ($hs, $hw) = ("", 0); for my $ch (@c) { my $x = $cw->($ch); last if $hw + $x > $h; $hs .= $ch; $hw += $x; }
      my ($ts, $tw) = ("", 0); for my $ch (reverse @c) { my $x = $cw->($ch); last if $tw + $x > $t; $ts = $ch . $ts; $tw += $x; }
      print $hs . "\x{2026}" . $ts; exit;
    }
  ' -- -mode="$1" -max="${2:-0}"
}

disp_width() { [ -z "${1:-}" ] && { printf '0'; return; }; printf '%s' "$1" | _udisp width; }
trunc_end()  { printf '%s' "$1" | _udisp trunc_end "$2"; }
trunc_mid()  { printf '%s' "$1" | _udisp trunc_mid "$2"; }

# abbrev_path <path> <maxwidth>  — replace $HOME with ~, middle-truncate if too wide.
abbrev_path() {
  local p="$1"
  case "$p" in
    "$HOME") p="~";;
    "$HOME"/*) p="~${p#"$HOME"}";;
  esac
  if [ "$(disp_width "$p")" -le "$2" ]; then printf '%s' "$p"; else trunc_mid "$p" "$2"; fi
}
```

- [ ] **Step 4: Run harness — verify pass**

Run: `bash git-status-tui/scripts/test-git-status.sh; echo "exit=$?"`
Expected: all Task 1 assertions pass, `exit=0`

- [ ] **Step 5: Commit**

```bash
git add git-status-tui/scripts/git-status.sh git-status-tui/scripts/test-git-status.sh
git commit -m "feat(git-status-tui): unicode width + truncation helpers"
```

---

### Task 2: Color / symbol style (`init_style`, `paint`)

**Files:** modify `git-status.sh`, `test-git-status.sh`

- [ ] **Step 1: Add failing tests**

```bash
# --- Task 2: style ---
COLOR=1; assert_contains "paint on"  "$(printf '\033[31m')" "$(paint red X)"
COLOR=0; assert_eq       "paint off" "X" "$(paint red X)"
unset COLOR
```

- [ ] **Step 2: Run harness — verify failures**

Run: `bash git-status-tui/scripts/test-git-status.sh`
Expected: `FAIL paint on` / `FAIL paint off` (function undefined)

- [ ] **Step 3: Implement** (add above `main`)

```bash
# init_style — sets global COLOR=1 unless NO_COLOR set or stdout is not a TTY.
init_style() {
  if [ -n "${NO_COLOR:-}" ] || [ ! -t 1 ]; then COLOR=0; else COLOR=1; fi
}
# paint <name> <text> — wraps text in ANSI when COLOR=1, else returns text unchanged.
paint() {
  if [ "${COLOR:-0}" = "1" ]; then
    local code
    case "$1" in red) code=31;; green) code=32;; yellow) code=33;; *) code=0;; esac
    printf '\033[%sm%s\033[0m' "$code" "$2"
  else
    printf '%s' "$2"
  fi
}
```

- [ ] **Step 4: Run harness — verify pass**

Run: `bash git-status-tui/scripts/test-git-status.sh; echo "exit=$?"`
Expected: Task 2 passes, `exit=0`

- [ ] **Step 5: Commit**

```bash
git add git-status-tui/scripts/git-status.sh git-status-tui/scripts/test-git-status.sh
git commit -m "feat(git-status-tui): color/symbol style helpers"
```

---

### Task 3: Box primitives (`bar`, `ttop`, `ftitle`, `fbot`, `row`, `cell`)

**Files:** modify `git-status.sh`, `test-git-status.sh`

- [ ] **Step 1: Add failing tests** (alignment = every line same display width)

```bash
# --- Task 3: box primitives ---
INNER=20
# plain padded row, colored row, and CJK row must all be the same display width
assert_eq "row width plain"   "24" "$(disp_width "$(row 'hi')")"
assert_eq "row width colored" "24" "$(disp_width "$(COLOR=1 row "$(COLOR=1 paint red dot)")")"
assert_eq "row width cjk"      "24" "$(disp_width "$(row '中文 狀態')")"
assert_eq "ttop width"        "24" "$(disp_width "$(ttop 'git status')")"
assert_eq "ftitle width"      "24" "$(disp_width "$(ftitle 'working tree')")"
assert_eq "fbot width"        "24" "$(disp_width "$(fbot)")"
# cell truncates+pads to exact column width
assert_eq "cell pad"  "8" "$(disp_width "$(cell 'main' 8)")"
assert_eq "cell trunc" "8" "$(disp_width "$(cell 'feature/very-long-branch' 8)")"
unset INNER COLOR
```

> Note: outer width = `INNER + 4` (`│ ` + 20 + ` │` = 24). All frame lines span `INNER+2` between corners.

- [ ] **Step 2: Run harness — verify failures**

Run: `bash git-status-tui/scripts/test-git-status.sh`
Expected: Task 3 assertions FAIL (functions undefined)

- [ ] **Step 3: Implement** (add above `main`; relies on global `INNER`)

```bash
# bar <n> — print n box-drawing horizontal chars.
bar() { local n="$1" i=0 s=""; while [ "$i" -lt "$n" ]; do s="$s─"; i=$((i+1)); done; printf '%s' "$s"; }

# titled top corner: ┌─ title ───────┐
ttop() { local t="$1" w k; w=$(disp_width "$t"); k=$((INNER-1-w)); [ "$k" -lt 0 ] && k=0
  printf '┌─ %s ' "$t"; bar "$k"; printf '┐'; }

# titled separator: ├─ title ───────┤
ftitle() { local t="$1" w k; w=$(disp_width "$t"); k=$((INNER-1-w)); [ "$k" -lt 0 ] && k=0
  printf '├─ %s ' "$t"; bar "$k"; printf '┤'; }

# bottom corner
fbot() { printf '└'; bar $((INNER+2)); printf '┘'; }

# content row, padded to INNER (ANSI-aware). Caller must pre-fit content (no truncation here).
row() { local c="$1" w pad; w=$(disp_width "$c"); pad=$((INNER-w)); [ "$pad" -lt 0 ] && pad=0
  printf '│ %s%*s │' "$c" "$pad" ""; }

# cell <plain-text> <width> — truncate (plain) then left-pad to exact display width.
cell() { local t w pad; t=$(trunc_end "$1" "$2"); w=$(disp_width "$t"); pad=$(($2-w)); [ "$pad" -lt 0 ] && pad=0
  printf '%s%*s' "$t" "$pad" ""; }
```

> `ttop`/`ftitle`/`fbot`/`row` print without trailing newline; callers use them in `$(...)` within an output list that adds newlines (Task 6/7). For direct printing, append `\n`.

- [ ] **Step 4: Run harness — verify pass**

Run: `bash git-status-tui/scripts/test-git-status.sh; echo "exit=$?"`
Expected: Task 3 passes, `exit=0`

- [ ] **Step 5: Commit**

```bash
git add git-status-tui/scripts/git-status.sh git-status-tui/scripts/test-git-status.sh
git commit -m "feat(git-status-tui): box-drawing primitives"
```

---

### Task 4: Read-only git data helpers

**Files:** modify `git-status.sh`, `test-git-status.sh`

Each helper runs `git` in CWD and prints one value (empty on absence). No network.

- [ ] **Step 1: Add failing integration tests** (use `mk_repo`)

```bash
# --- Task 4: git data helpers ---
( d=$(mk_repo); cd "$d"
  printf 'x\n' > f; git add f; git commit -qm init
  assert_eq "g_root"   "$d" "$(g_root)"
  assert_eq "g_branch" "$(git symbolic-ref --short HEAD)" "$(g_branch_or_detached)"
  assert_contains "g_head" "init" "$(g_head)"
  assert_eq "g_upstream none" "no upstream" "$(g_upstream)"
  assert_eq "g_stash 0" "0" "$(g_stash)"
  assert_eq "g_inprogress none" "" "$(g_inprogress)"
  # detached HEAD
  sha=$(git rev-parse --short HEAD); git checkout -q "$sha"
  assert_contains "g_detached" "detached" "$(g_branch_or_detached)"
  rm -rf "$d" )
# empty repo: branch resolves but head says no commits
( d=$(mk_repo); cd "$d"
  assert_contains "g_empty head" "no commits" "$(g_head)"
  rm -rf "$d" )
```

- [ ] **Step 2: Run harness — verify failures**

Run: `bash git-status-tui/scripts/test-git-status.sh`
Expected: Task 4 assertions FAIL (functions undefined)

- [ ] **Step 3: Implement** (add above `main`)

```bash
g_root() { git rev-parse --show-toplevel 2>/dev/null; }

g_branch_or_detached() {
  local b; b=$(git symbolic-ref --short -q HEAD 2>/dev/null)
  if [ -n "$b" ]; then printf '%s' "$b"
  else printf 'HEAD detached @ %s' "$(git rev-parse --short HEAD 2>/dev/null)"; fi
}

g_head() {
  local h; h=$(git log -1 --format='%h %s' 2>/dev/null)
  if [ -n "$h" ]; then printf '%s' "$h"; else printf 'no commits yet'; fi
}

g_upstream() { git rev-parse --abbrev-ref --symbolic-full-name '@{u}' 2>/dev/null || printf 'no upstream'; }

# prints "<behind>\t<ahead>" or empty when no upstream
g_aheadbehind() { git rev-list --left-right --count '@{u}...HEAD' 2>/dev/null; }

g_stash() { git stash list 2>/dev/null | grep -c '' | tr -d ' '; }

# prints a marker name if a merge/rebase/cherry-pick/revert is in progress, else empty
g_inprogress() {
  local gd; gd=$(git rev-parse --git-dir 2>/dev/null) || return 0
  if   [ -d "$gd/rebase-merge" ] || [ -d "$gd/rebase-apply" ]; then printf 'rebase'
  elif [ -f "$gd/MERGE_HEAD" ];       then printf 'merge'
  elif [ -f "$gd/CHERRY_PICK_HEAD" ]; then printf 'cherry-pick'
  elif [ -f "$gd/REVERT_HEAD" ];      then printf 'revert'; fi
}

# prints "N M" = submodule count, dirty count (empty when none)
g_submodules() {
  local s; s=$(git submodule status 2>/dev/null)
  [ -z "$s" ] && return 0
  local n dirty
  n=$(printf '%s\n' "$s" | grep -c '')
  dirty=$(printf '%s\n' "$s" | grep -c '^+')
  printf '%s %s' "$n" "$dirty"
}
```

> `grep -c ''` counts lines portably (avoids `wc -l` whitespace). On empty input it prints `0`.

- [ ] **Step 4: Run harness — verify pass**

Run: `bash git-status-tui/scripts/test-git-status.sh; echo "exit=$?"`
Expected: Task 4 passes, `exit=0`

- [ ] **Step 5: Commit**

```bash
git add git-status-tui/scripts/git-status.sh git-status-tui/scripts/test-git-status.sh
git commit -m "feat(git-status-tui): read-only git data helpers"
```

---

### Task 5: Porcelain parsing (`parse_counts`, `change_lines`, `fmt_ab`)

**Files:** modify `git-status.sh`, `test-git-status.sh`

- [ ] **Step 1: Add failing tests**

```bash
# --- Task 5: porcelain ---
SAMPLE=$(printf 'M  a\n M b\n?? c\nMM d\n')
assert_eq "counts" "2 2 1" "$(printf '%s\n' "$SAMPLE" | parse_counts)"
# change_lines: label classification + leading XY
assert_contains "cl staged"    "(staged)"    "$(printf '%s\n' "$SAMPLE" | change_lines 10)"
assert_contains "cl modified"  "(modified)"  "$(printf '%s\n' "$SAMPLE" | change_lines 10)"
assert_contains "cl untracked" "(untracked)" "$(printf '%s\n' "$SAMPLE" | change_lines 10)"
# overflow marker
BIG=$(for i in 1 2 3; do printf '?? f%s\n' "$i"; done)
assert_contains "cl overflow" "+1 more" "$(printf '%s\n' "$BIG" | change_lines 2)"
assert_eq "fmt_ab" "↑1 ↓0" "$(fmt_ab 0 1)"
```

- [ ] **Step 2: Run harness — verify failures**

Run: `bash git-status-tui/scripts/test-git-status.sh`
Expected: Task 5 assertions FAIL

- [ ] **Step 3: Implement** (add above `main`)

```bash
# parse_counts — reads `git status --porcelain=v1` on STDIN, prints "STAGED MODIFIED UNTRACKED".
parse_counts() {
  awk '
    /^\?\?/ { u++; next }
    { x = substr($0,1,1); y = substr($0,2,1) }
    (x != " " && x != "?") { s++ }
    (y == "M" || y == "D") { m++ }
    END { printf "%d %d %d", s+0, m+0, u+0 }
  '
}

# change_lines <limit> — reads porcelain on STDIN, prints up to <limit> formatted rows
# (plain text; caller wraps each in row()). Appends "… +N more" when truncated.
change_lines() {
  local limit="$1"
  awk -v lim="$limit" '
    { total++; lines[total] = $0 }
    END {
      shown = (total < lim) ? total : lim
      for (i = 1; i <= shown; i++) {
        xy = substr(lines[i],1,2); path = substr(lines[i],4)
        if (xy ~ /^\?\?/)            lbl = "untracked"
        else if (substr(xy,1,1) != " ") lbl = "staged"
        else                          lbl = "modified"
        printf "%s %s\t%s\n", xy, path, lbl
      }
      if (total > shown) printf "… +%d more\n", total - shown
    }
  '
}

# fmt_ab <behind> <ahead> — "↑ahead ↓behind"
fmt_ab() { printf '↑%s ↓%s' "$2" "$1"; }
```

> `change_lines` emits `XY path<TAB>label`; the renderer (Task 6) formats the tab into the aligned `(label)` suffix and truncates the path to fit `INNER`.

- [ ] **Step 4: Run harness — verify pass**

Run: `bash git-status-tui/scripts/test-git-status.sh; echo "exit=$?"`
Expected: Task 5 passes, `exit=0`

- [ ] **Step 5: Commit**

```bash
git add git-status-tui/scripts/git-status.sh git-status-tui/scripts/test-git-status.sh
git commit -m "feat(git-status-tui): porcelain parsing + ahead/behind format"
```

---

### Task 6: Single-repo panel (`render_single`)

**Files:** modify `git-status.sh`, `test-git-status.sh`

- [ ] **Step 1: Add failing integration tests**

```bash
# --- Task 6: render_single ---
( d=$(mk_repo); cd "$d"
  printf 'x\n' > a; git add a; git commit -qm "first commit"
  printf 'y\n' > a; printf 'z\n' > b   # a modified, b untracked
  out=$(COLOR=0 render_single)
  assert_contains "rs header"  "git status"    "$out"
  assert_contains "rs branch"  "$(git symbolic-ref --short HEAD)" "$out"
  assert_contains "rs head"    "first commit"  "$out"
  assert_contains "rs section" "working tree"  "$out"
  assert_contains "rs changes" "(untracked)"   "$out"
  assert_contains "rs noupstream" "no upstream" "$out"
  # frame alignment: every line is the same display width
  widths=$(printf '%s\n' "$out" | while IFS= read -r l; do disp_width "$l"; echo; done | sort -u | grep -c '')
  assert_eq "rs aligned" "1" "$widths"
  rm -rf "$d" )
# clean repo shows clean note
( d=$(mk_repo); cd "$d"; printf 'x\n'>a; git add a; git commit -qm init
  assert_contains "rs clean" "clean" "$(COLOR=0 render_single)"; rm -rf "$d" )
# in-progress warning
( d=$(mk_repo); cd "$d"; printf 'x\n'>a; git add a; git commit -qm init
  touch "$(git rev-parse --git-dir)/MERGE_HEAD"
  assert_contains "rs warn" "merge in progress" "$(COLOR=0 render_single)"; rm -rf "$d" )
```

- [ ] **Step 2: Run harness — verify failures**

Run: `bash git-status-tui/scripts/test-git-status.sh`
Expected: Task 6 assertions FAIL

- [ ] **Step 3: Implement** (add above `main`)

```bash
# render_single — prints the single-repo panel for CWD's repo. Read-only.
render_single() {
  INNER=58
  local root name branch head up ab inprog porc counts s m u subs
  root=$(g_root); name=$(basename "$root")
  branch=$(g_branch_or_detached); head=$(g_head); up=$(g_upstream)
  inprog=$(g_inprogress)
  porc=$(git status --porcelain=v1 2>/dev/null)
  counts=$(printf '%s\n' "$porc" | parse_counts); set -- $counts; s=$1; m=$2; u=$3

  ttop 'git status'; printf '\n'

  if [ -n "$inprog" ]; then row "$(paint red "⚠ $inprog in progress")"; printf '\n'; fi

  row "$(trunc_end "repo    $name    $(abbrev_path "$root" 36)" "$INNER")"; printf '\n'

  case "$branch" in
    *detached*) row "branch  $branch";;
    *) if [ "$up" = "no upstream" ]; then row "branch  $branch   $(paint yellow 'no upstream')"
       else ab=$(g_aheadbehind); set -- $ab
         row "branch  $branch   $(paint yellow "$(fmt_ab "${1:-0}" "${2:-0}")")  →  $up"; fi;;
  esac
  printf '\n'

  row "$(trunc_end "head    $head" "$INNER")"; printf '\n'

  subs=$(g_submodules)
  [ -n "$subs" ] && { set -- $subs; row "submod  $1 ($2 dirty)"; printf '\n'; }

  ftitle 'working tree'; printf '\n'
  local dot
  dot=$([ "$s" -gt 0 ] && paint yellow '●' || paint green '●'); row "$dot staged     $s"; printf '\n'
  dot=$([ "$m" -gt 0 ] && paint red '●'    || paint green '●'); row "$dot modified   $m"; printf '\n'
  dot=$([ "$u" -gt 0 ] && paint red '●'    || paint green '●'); row "$dot untracked  $u"; printf '\n'
  row "$(paint green '●') stash      $(g_stash)"; printf '\n'

  if [ -n "$porc" ]; then
    ftitle 'changes'; printf '\n'
    printf '%s\n' "$porc" | change_lines 10 | while IFS=$'\t' read -r left label; do
      if [ -n "$label" ]; then
        # left = "XY path"; fit "XY path  (label)" into INNER
        local suffix="  ($label)" body
        body=$(trunc_end "$left" $((INNER - $(disp_width "$suffix"))))
        row "$body$suffix"
      else
        row "$left"   # the "… +N more" line (no tab)
      fi
      printf '\n'
    done
  else
    ftitle 'changes'; printf '\n'; row "$(paint green '(clean working tree)')"; printf '\n'
  fi

  fbot; printf '\n'
}
```

- [ ] **Step 4: Run harness — verify pass**

Run: `bash git-status-tui/scripts/test-git-status.sh; echo "exit=$?"`
Expected: Task 6 passes, `exit=0`

- [ ] **Step 5: Commit**

```bash
git add git-status-tui/scripts/git-status.sh git-status-tui/scripts/test-git-status.sh
git commit -m "feat(git-status-tui): single-repo panel renderer"
```

---

### Task 7: Parent-directory overview (`scan_repos`, `render_overview`)

**Files:** modify `git-status.sh`, `test-git-status.sh`

- [ ] **Step 1: Add failing integration tests**

```bash
# --- Task 7: overview ---
( parent=$(mktemp -d); cd "$parent"
  for r in api web; do ( d="$parent/$r"; mkdir "$d"; git -C "$d" init -q
    git -C "$d" config user.email t@t; git -C "$d" config user.name t
    printf 'x\n' > "$d/f"; git -C "$d" add f; git -C "$d" commit -qm init ); done
  printf 'y\n' >> "$parent/api/f"   # api dirty
  mkdir "$parent/notarepo"
  out=$(COLOR=0 render_overview "$parent")
  assert_contains "ov header" "repos in" "$out"
  assert_contains "ov api"    "api"      "$out"
  assert_contains "ov web"    "web"      "$out"
  assert_contains "ov dirty"  "dirty"    "$out"
  assert_contains "ov skip-nonrepo-absent" "notarepo" "$(printf '%s' "$out" | grep notarepo || echo notarepo)"
  assert_contains "ov summary" "2 repos" "$out"
  widths=$(printf '%s\n' "$out" | grep '^[┌│└]' | while IFS= read -r l; do disp_width "$l"; echo; done | sort -u | grep -c '')
  assert_eq "ov aligned" "1" "$widths"
  rm -rf "$parent" )
# empty parent → notice, not an empty frame
( parent=$(mktemp -d)
  assert_contains "ov empty" "no git repos" "$(COLOR=0 render_overview "$parent")"; rm -rf "$parent" )
```

> `ov skip-nonrepo-absent` asserts `notarepo` is NOT listed (the `grep || echo` makes the needle present only when grep finds nothing).

- [ ] **Step 2: Run harness — verify failures**

Run: `bash git-status-tui/scripts/test-git-status.sh`
Expected: Task 7 assertions FAIL

- [ ] **Step 3: Implement** (add above `main`)

```bash
# scan_repos <dir> — prints one line per first-level git repo: "name<TAB>branch<TAB>state<TAB>ab<TAB>stash"
scan_repos() {
  local base="$1" d name branch porc state ab abtxt stash behind ahead
  for d in "$base"/*/; do
    d=${d%/}
    git -C "$d" rev-parse --is-inside-work-tree >/dev/null 2>&1 || continue
    name=$(basename "$d")
    branch=$(git -C "$d" symbolic-ref --short -q HEAD 2>/dev/null || echo 'DETACHED')
    porc=$(git -C "$d" status --porcelain=v1 2>/dev/null)
    state=$([ -n "$porc" ] && echo '✗ dirty' || echo '✓ clean')
    ab=$(git -C "$d" rev-list --left-right --count '@{u}...HEAD' 2>/dev/null)
    if [ -n "$ab" ]; then set -- $ab; behind=$1; ahead=$2; abtxt="↑$ahead ↓$behind"; else abtxt='—'; fi
    stash=$(git -C "$d" stash list 2>/dev/null | grep -c '' | tr -d ' ')
    printf '%s\t%s\t%s\t%s\t%s\n' "$name" "$branch" "$state" "$abtxt" "$stash"
  done
}

# render_overview <dir> — prints the multi-repo overview table.
render_overview() {
  INNER=66
  local base="$1" rows n dirty
  rows=$(scan_repos "$base")
  ttop "repos in $(abbrev_path "$base" 48)"; printf '\n'
  if [ -z "$rows" ]; then
    row "$(paint yellow 'no git repos found here')"; printf '\n'; fbot; printf '\n'; return 0
  fi
  row "$(cell REPO 16)  $(cell BRANCH 16)  $(cell STATE 8)  $(cell AHEAD/BEHIND 12)  $(cell STASH 6)"; printf '\n'
  printf '%s\n' "$rows" | while IFS=$'\t' read -r name br st ab stash; do
    local stcell; stcell=$(cell "$st" 8)
    case "$st" in *dirty*) stcell=$(paint red "$stcell");; *) stcell=$(paint green "$stcell");; esac
    row "$(cell "$name" 16)  $(cell "$br" 16)  $stcell  $(cell "$ab" 12)  $(cell "$stash" 6)"; printf '\n'
  done
  fbot; printf '\n'
  n=$(printf '%s\n' "$rows" | grep -c '')
  dirty=$(printf '%s\n' "$rows" | grep -c 'dirty')
  printf '%s repos · %s dirty · scanned %s\n' "$n" "$dirty" "$(abbrev_path "$base" 48)"
}
```

- [ ] **Step 4: Run harness — verify pass**

Run: `bash git-status-tui/scripts/test-git-status.sh; echo "exit=$?"`
Expected: Task 7 passes, `exit=0`

- [ ] **Step 5: Commit**

```bash
git add git-status-tui/scripts/git-status.sh git-status-tui/scripts/test-git-status.sh
git commit -m "feat(git-status-tui): parent-directory overview renderer"
```

---

### Task 8: Dispatch + entry detection (`main`)

**Files:** modify `git-status.sh`, `test-git-status.sh`

- [ ] **Step 1: Add failing integration tests** (call the script as an executable, not sourced)

```bash
# --- Task 8: main dispatch ---
SCRIPT="$HERE/git-status.sh"
( d=$(mk_repo); cd "$d"; printf 'x\n'>a; git add a; git commit -qm init
  assert_contains "main single" "git status" "$(bash "$SCRIPT")"; rm -rf "$d" )
( parent=$(mktemp -d)
  ( d="$parent/r"; mkdir "$d"; git -C "$d" init -q; git -C "$d" config user.email t@t
    git -C "$d" config user.name t; printf 'x\n'>"$d/f"; git -C "$d" add f; git -C "$d" commit -qm init )
  cd "$parent"
  assert_contains "main overview" "repos in" "$(bash "$SCRIPT")"; rm -rf "$parent" )
assert_contains "main help" "Usage" "$(bash "$SCRIPT" --help)"
```

- [ ] **Step 2: Run harness — verify failures**

Run: `bash git-status-tui/scripts/test-git-status.sh`
Expected: Task 8 assertions FAIL (main still prints "not yet implemented")

- [ ] **Step 3: Implement** — replace the placeholder `main` with:

```bash
main() {
  set -u
  case "${1:-}" in
    -h|--help)
      printf 'Usage: git-status.sh\n'
      printf '  Inside a git repo  → detailed single-repo status panel.\n'
      printf '  In a non-repo dir  → one-line overview of first-level git repos.\n'
      printf '  Read-only; never fetches. NO_COLOR honored; color off when not a TTY.\n'
      return 0;;
  esac
  init_style
  if git rev-parse --is-inside-work-tree >/dev/null 2>&1; then
    render_single
  else
    render_overview "$(pwd)"
  fi
}
```

- [ ] **Step 4: Run harness — verify pass + manual smoke**

Run: `bash git-status-tui/scripts/test-git-status.sh; echo "exit=$?"`
Expected: all tasks pass, `exit=0`

Run (real smoke, this repo is dirty): `bash git-status-tui/scripts/git-status.sh`
Expected: a single-repo panel showing branch `main`, the staged/modified/untracked counts, and a `changes` section.

- [ ] **Step 5: Commit**

```bash
git add git-status-tui/scripts/git-status.sh git-status-tui/scripts/test-git-status.sh
git commit -m "feat(git-status-tui): entry detection + dispatch"
```

---

### Task 9: SKILL.md

**Files:** Create `git-status-tui/SKILL.md`

- [ ] **Step 1: Write SKILL.md**

```markdown
---
name: git-status-tui
description: Use when you want a clear, at-a-glance view of git state in the Agent CLI — "git status" (enhanced), "git 狀態", "gst", "掃一下 git", "repo 狀態", "哪個 repo 還沒乾淨". Renders a box-drawing panel of the current repo (branch, ahead/behind, staged/modified/untracked, stash, in-progress ops) or, from a parent directory, a one-line-per-repo overview. Read-only; never fetches.
compatibility: Designed for Claude Code. Requires git and perl.
allowed-tools: Bash
---

## git status TUI

Read-only git status dashboard. Two modes, auto-detected by CWD:

- **Inside a git repo** → detailed single-repo panel.
- **In a directory that is not a repo** → overview table of every first-level sub-repo (good for "which repo is still dirty?" before wrapping up).

### How to run

```bash
bash <skill-dir>/scripts/git-status.sh          # auto-detect mode
bash <skill-dir>/scripts/git-status.sh --help   # usage
```

Run the script and present its stdout to the user verbatim (it is already
formatted). Do not re-summarize the panel into prose unless asked.

### What it shows

Single panel: repo name + path, branch (or `HEAD detached @ sha`),
ahead/behind vs upstream (or `no upstream`), last commit, submodule summary,
counts for staged / modified / untracked / stash, an in-progress-operation
warning (`⚠ merge in progress`), and the first 10 changed paths (`… +N more`
when there are more).

Overview: one row per repo — name, branch, `✓ clean` / `✗ dirty`, ahead/behind,
stash — plus a summary line.

### Boundaries

- **Read-only.** Never stages, commits, stashes, checks out, fetches, or pulls.
- **No network.** Ahead/behind reflects locally-known remote state; run
  `repo-sync` first if you need fresh remote tracking.
- Color auto-degrades to symbols (`✓ ✗ ↑ ↓ ●`) when `NO_COLOR` is set or
  stdout is not a TTY.
```

- [ ] **Step 2: Commit**

```bash
git add git-status-tui/SKILL.md
git commit -m "docs(git-status-tui): add SKILL.md"
```

---

### Task 10: Register in CLAUDE.md + audit

**Files:** Modify `CLAUDE.md`

- [ ] **Step 1: Add the skill to the "Productivity & Analysis" list in `CLAUDE.md`**

Insert after the `repo-sync` bullet:
```markdown
- **git-status-tui** — Read-only git status dashboard rendered as a box-drawing TUI panel; single-repo detail or parent-directory multi-repo overview. Auto-degrades color to symbols; never fetches.
```

- [ ] **Step 2: Run skill-auditor** (user global rule: always audit after creating/modifying a skill)

Invoke the `skill-auditor` skill on `git-status-tui/`. Fix any HIGH/MEDIUM findings inline; re-run until clean.

- [ ] **Step 3: Commit**

```bash
git add CLAUDE.md git-status-tui/
git commit -m "docs(skills): register git-status-tui"
```

---

## Self-Review

**Spec coverage:**
- Single-repo panel (repo/branch/ahead-behind/head/working-tree/stash/changes/submodules/in-progress) → Tasks 4–6. ✓
- Parent-directory overview + summary → Task 7. ✓
- Entry detection (single vs overview) → Task 8. ✓
- Box-drawing + ANSI color with symbol fallback → Tasks 2–3 (`paint`/`init_style`) + symbols in overview. ✓
- CJK / wide-path alignment (pre-mortem mitigation) → Task 1 (`_udisp`) + Task 3 alignment tests. ✓
- Read-only, no auto-fetch → enforced by helper command choice; stated in SKILL.md + `--help`. ✓
- Edge cases: detached / no-upstream / empty / in-progress / no-sub-repos → Tasks 4, 6, 7 tests. ✓
- Out of scope (no interaction, no mutation, no diff, no fetch) → nothing in the plan implements these. ✓

**Placeholder scan:** none — every step has runnable code/commands and expected output.

**Type/name consistency:** helper names used in Tasks 6–8 (`g_root`, `g_branch_or_detached`, `g_head`, `g_upstream`, `g_aheadbehind`, `g_stash`, `g_inprogress`, `g_submodules`, `parse_counts`, `change_lines`, `fmt_ab`, `cell`, `row`, `ttop`, `ftitle`, `fbot`, `paint`, `init_style`, `abbrev_path`) all match their Task 1–5 definitions. Global `INNER` set by each renderer before drawing.
