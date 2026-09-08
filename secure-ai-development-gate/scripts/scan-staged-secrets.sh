#!/usr/bin/env bash

set -euo pipefail

EXIT_OK=0
EXIT_FINDING=2
EXIT_ERROR=3

if ! git rev-parse --is-inside-work-tree >/dev/null 2>&1; then
  echo "ERROR: current directory is not a Git repository."
  exit "$EXIT_ERROR"
fi

if git diff --cached --quiet; then
  echo "PASS: no staged changes."
  exit "$EXIT_OK"
fi

echo "== Secure AI Development Gate =="
echo "Scanning staged changes for secrets..."
echo

TMP_DIR="$(mktemp -d)"
trap 'rm -rf "$TMP_DIR"' EXIT

PATCH_FILE="$TMP_DIR/staged.patch"

git diff --cached \
  --no-ext-diff \
  --unified=0 >"$PATCH_FILE"

if command -v gitleaks >/dev/null 2>&1; then
  echo "[scanner] gitleaks"

  set +e
  git diff --cached --no-ext-diff | \
    gitleaks protect \
      --stdin \
      --redact \
      --no-banner
  rc=$?
  set -e

  if [[ "$rc" -eq 0 ]]; then
    echo
    echo "PASS: staged changes passed gitleaks."
    exit "$EXIT_OK"
  fi

  if [[ "$rc" -eq 1 ]]; then
    echo
    echo "BLOCKED: potential secret detected in staged changes."
    echo "Secret value suppressed."
    exit "$EXIT_FINDING"
  fi

  echo
  echo "WARNING: gitleaks staged scan failed; using fallback detection."
fi

PATTERN='(-----BEGIN[[:space:]]+(RSA|EC|OPENSSH|DSA|PGP)[[:space:]]+PRIVATE[[:space:]]+KEY-----|AKIA[0-9A-Z]{16}|ASIA[0-9A-Z]{16}|AIza[0-9A-Za-z_-]{30,}|gh[pousr]_[0-9A-Za-z]{20,}|github_pat_[0-9A-Za-z_]{20,}|xox[baprs]-[0-9A-Za-z-]{10,}|sk-[0-9A-Za-z_-]{20,}|Bearer[[:space:]]+[0-9A-Za-z._~+/-]{20,}|(password|passwd|pwd|secret|token|api[_-]?key|access[_-]?key|client[_-]?secret)[[:space:]]*[:=][[:space:]]*["'\'']?[0-9A-Za-z._~+/@$%^&*(){}:;,-]{8,})'

ADDED_LINES="$TMP_DIR/added-lines.txt"

grep '^+' "$PATCH_FILE" \
  | grep -v '^+++' \
  | sed 's/^+//' \
  >"$ADDED_LINES" || true

if [[ ! -s "$ADDED_LINES" ]]; then
  echo "PASS: no added staged content to scan."
  exit "$EXIT_OK"
fi

set +e
grep -En "$PATTERN" "$ADDED_LINES" >"$TMP_DIR/findings.txt"
rc=$?
set -e

if [[ "$rc" -gt 1 ]]; then
  echo "ERROR: fallback secret scan failed."
  exit "$EXIT_ERROR"
fi

if [[ -s "$TMP_DIR/findings.txt" ]]; then
  echo "BLOCKED: potential secret-like content detected in staged changes."
  echo
  echo "Matched secret values are intentionally not displayed."
  echo
  echo "Review staged changes with:"
  echo
  echo "  git diff --cached"
  echo
  exit "$EXIT_FINDING"
fi

echo "PASS: no common secret patterns detected in staged additions."
echo "NOTE: fallback pattern scanner was used."
exit "$EXIT_OK"
