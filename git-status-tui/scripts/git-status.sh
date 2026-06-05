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
