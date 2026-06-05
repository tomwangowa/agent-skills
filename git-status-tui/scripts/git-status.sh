#!/usr/bin/env bash
# git-status.sh — read-only git status dashboard (single repo) / overview (parent dir).
# Requires: git, perl. bash 3.2 compatible. Source-safe (main is guarded).

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

main() {
  set -u
  printf 'git-status.sh: not yet implemented\n' >&2
  return 0
}

# bar <n> — print n box-drawing horizontal chars.
# Print directly; do NOT accumulate the multibyte char into a quoted var
# (`s="$s─"`) — that trips a bash 3.2 set -u parser bug in subshells.
bar() { local n="$1" i=0; while [ "$i" -lt "$n" ]; do printf '─'; i=$((i+1)); done; }

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
        if (xy ~ /^\?\?/)                lbl = "untracked"
        else if (substr(xy,1,1) != " ")  lbl = "staged"
        else                             lbl = "modified"
        printf "%s %s\t%s\n", xy, path, lbl
      }
      if (total > shown) printf "… +%d more\n", total - shown
    }
  '
}

# fmt_ab <behind> <ahead> — "↑ahead ↓behind"
fmt_ab() { printf '↑%s ↓%s' "$2" "$1"; }

# render_single — prints the single-repo panel for CWD's repo. Read-only.
render_single() {
  INNER=58
  local root name branch head up ab inprog porc counts s m u subs dot
  root=$(g_root); name=$(basename "$root")
  branch=$(g_branch_or_detached); head=$(g_head); up=$(g_upstream)
  inprog=$(g_inprogress)
  # -c core.quotePath=false so CJK/UTF-8 filenames show literally (not "\3xx" octal).
  porc=$(git -c core.quotePath=false status --porcelain=v1 2>/dev/null)
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
  dot=$([ "$s" -gt 0 ] && paint yellow '●' || paint green '●'); row "$dot staged     $s"; printf '\n'
  dot=$([ "$m" -gt 0 ] && paint red '●'    || paint green '●'); row "$dot modified   $m"; printf '\n'
  dot=$([ "$u" -gt 0 ] && paint red '●'    || paint green '●'); row "$dot untracked  $u"; printf '\n'
  row "$(paint green '●') stash      $(g_stash)"; printf '\n'

  ftitle 'changes'; printf '\n'
  if [ -n "$porc" ]; then
    printf '%s\n' "$porc" | change_lines 10 | while IFS=$'\t' read -r left label; do
      if [ -n "$label" ]; then
        suffix="  ($label)"
        body=$(trunc_end "$left" $((INNER - $(disp_width "$suffix"))))
        row "$body$suffix"
      else
        row "$left"
      fi
      printf '\n'
    done
  else
    row "$(paint green '(clean working tree)')"; printf '\n'
  fi

  fbot; printf '\n'
}

# scan_repos <dir> — prints one line per first-level git repo:
# "name<TAB>branch<TAB>state<TAB>ab<TAB>stash"
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
  local base="$1" rows n dirty stcell
  rows=$(scan_repos "$base")
  ttop "repos in $(abbrev_path "$base" 48)"; printf '\n'
  if [ -z "$rows" ]; then
    row "$(paint yellow 'no git repos found here')"; printf '\n'; fbot; printf '\n'; return 0
  fi
  row "$(cell REPO 16)  $(cell BRANCH 16)  $(cell STATE 8)  $(cell AHEAD/BEHIND 12)  $(cell STASH 6)"; printf '\n'
  printf '%s\n' "$rows" | while IFS=$'\t' read -r name br st ab stash; do
    stcell=$(cell "$st" 8)
    case "$st" in *dirty*) stcell=$(paint red "$stcell");; *) stcell=$(paint green "$stcell");; esac
    row "$(cell "$name" 16)  $(cell "$br" 16)  $stcell  $(cell "$ab" 12)  $(cell "$stash" 6)"; printf '\n'
  done
  fbot; printf '\n'
  n=$(printf '%s\n' "$rows" | grep -c '')
  dirty=$(printf '%s\n' "$rows" | grep -c 'dirty')
  printf '%s repos · %s dirty · scanned %s\n' "$n" "$dirty" "$(abbrev_path "$base" 48)"
}

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

if [ "${BASH_SOURCE[0]:-$0}" = "${0}" ]; then main "$@"; fi
