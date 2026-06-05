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
