#!/usr/bin/env bash

set -euo pipefail

TARGET="${1:-.}"

EXIT_OK=0
EXIT_FINDING=2
EXIT_ERROR=3

if [[ ! -e "$TARGET" ]]; then
  echo "ERROR: target does not exist: $TARGET"
  exit "$EXIT_ERROR"
fi

echo "== Secure AI Development Gate =="
echo "Secret scan target: $TARGET"
echo

run_gitleaks() {
  echo "[scanner] gitleaks"

  local report
  report="$(mktemp)"

  set +e
  gitleaks detect \
    --source "$TARGET" \
    --no-banner \
    --redact \
    --report-format json \
    --report-path "$report"
  local rc=$?
  set -e

  case "$rc" in
    0)
      echo "PASS: no secret findings detected by gitleaks."
      rm -f "$report"
      return "$EXIT_OK"
      ;;
    1)
      echo "BLOCKED: potential secret(s) detected by gitleaks."
      echo
      echo "Finding summary:"

      if command -v jq >/dev/null 2>&1; then
        jq -r '
          .[] |
          "- rule=\(.RuleID // "unknown") file=\(.File // "unknown") line=\(.StartLine // "?") secret=[REDACTED]"
        ' "$report"
      else
        echo "- See gitleaks report. Secret values have not been printed."
      fi

      rm -f "$report"
      return "$EXIT_FINDING"
      ;;
    *)
      echo "WARNING: gitleaks failed with exit code $rc."
      rm -f "$report"
      return "$EXIT_ERROR"
      ;;
  esac
}

run_trufflehog() {
  echo "[scanner] trufflehog"

  local output
  output="$(mktemp)"

  set +e

  if [[ -d "$TARGET/.git" ]]; then
    trufflehog git \
      "file://$(cd "$TARGET" && pwd)" \
      --json \
      --no-update \
      >"$output" 2>/dev/null
  else
    trufflehog filesystem \
      "$TARGET" \
      --json \
      --no-update \
      >"$output" 2>/dev/null
  fi

  local rc=$?
  set -e

  if [[ -s "$output" ]]; then
    echo "BLOCKED: potential secret(s) detected by trufflehog."
    echo
    echo "Finding summary:"

    if command -v jq >/dev/null 2>&1; then
      jq -r '
        "- detector=\(.DetectorName // "unknown") file=\(.SourceMetadata.Data.Filesystem.file // .SourceMetadata.Data.Git.file // "unknown") secret=[REDACTED]"
      ' "$output" 2>/dev/null || \
        echo "- Potential secret detected. Raw secret value suppressed."
    else
      echo "- Potential secret detected. Raw secret value suppressed."
    fi

    rm -f "$output"
    return "$EXIT_FINDING"
  fi

  if [[ "$rc" -ne 0 ]]; then
    echo "WARNING: trufflehog exited with code $rc."
    rm -f "$output"
    return "$EXIT_ERROR"
  fi

  echo "PASS: no secret findings detected by trufflehog."
  rm -f "$output"
  return "$EXIT_OK"
}

run_fallback_scan() {
  echo "[scanner] fallback pattern scan"
  echo "WARNING: no approved secret scanner found."
  echo "This fallback detects common credential patterns only."
  echo

  local findings
  findings="$(mktemp)"

  local grep_cmd

  if command -v rg >/dev/null 2>&1; then
    grep_cmd="rg"
  elif command -v grep >/dev/null 2>&1; then
    grep_cmd="grep"
  else
    echo "ERROR: neither rg nor grep is available."
    rm -f "$findings"
    return "$EXIT_ERROR"
  fi

PATTERN='(-----BEGIN[[:space:]]+(RSA|EC|OPENSSH|DSA|PGP)[[:space:]]+PRIVATE[[:space:]]+KEY-----|AKIA[0-9A-Z]{16}|ASIA[0-9A-Z]{16}|AIza[0-9A-Za-z_-]{30,}|gh[pousr]_[0-9A-Za-z]{20,}|github_pat_[0-9A-Za-z_]{20,}|xox[baprs]-[0-9A-Za-z-]{10,}|sk-[0-9A-Za-z_-]{20,}|Bearer[[:space:]]+[0-9A-Za-z._~+/-]{20,}|(password|passwd|pwd|secret|token|api[_-]?key|access[_-]?key|client[_-]?secret)[[:space:]]*[:=][[:space:]]*["'\'']?[0-9A-Za-z._~+/@$%^&*(){}:;,-]{8,})'

  if [[ "$grep_cmd" == "rg" ]]; then
    set +e
    rg \
      --hidden \
      --line-number \
      --no-heading \
      --glob '!.git/**' \
      --glob '!node_modules/**' \
      --glob '!vendor/**' \
      --glob '!dist/**' \
      --glob '!build/**' \
      --glob '!*.lock' \
      -e "$PATTERN" \
      "$TARGET" \
      >"$findings"
    local rc=$?
    set -e

    if [[ "$rc" -gt 1 ]]; then
      echo "ERROR: fallback scan failed."
      rm -f "$findings"
      return "$EXIT_ERROR"
    fi
  else
    set +e
    grep \
      -RInE \
      --exclude-dir=.git \
      --exclude-dir=node_modules \
      --exclude-dir=vendor \
      --exclude-dir=dist \
      --exclude-dir=build \
      "$PATTERN" \
      "$TARGET" \
      >"$findings"
    local rc=$?
    set -e

    if [[ "$rc" -gt 1 ]]; then
      echo "ERROR: fallback scan failed."
      rm -f "$findings"
      return "$EXIT_ERROR"
    fi
  fi

  if [[ -s "$findings" ]]; then
    echo "NEEDS_REVIEW: credential-like patterns detected."
    echo

    awk -F: '
      {
        if (NF >= 2) {
          print "- " $1 ":" $2 " potential credential-like content [REDACTED]"
        } else {
          print "- potential credential-like content [REDACTED]"
        }
      }
    ' "$findings" | sort -u

    rm -f "$findings"
    return "$EXIT_FINDING"
  fi

  rm -f "$findings"

  echo "PASS: no common secret patterns detected."
  echo "NOTE: this was a fallback scan, not a full secret scanner."
  return "$EXIT_OK"
}

if command -v gitleaks >/dev/null 2>&1; then
  run_gitleaks
  exit $?
fi

if command -v trufflehog >/dev/null 2>&1; then
  run_trufflehog
  exit $?
fi

run_fallback_scan
exit $?
