#!/usr/bin/env bash
set -euo pipefail

SKILLS_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)"
TARGETS_FILE="$SKILLS_DIR/.skill-sync-targets"
IGNORE_FILE="$SKILLS_DIR/.skill-sync-ignore"

# ── Read targets ──────────────────────────────────────────────
targets=()
if [[ -f "$TARGETS_FILE" ]]; then
    while IFS= read -r line; do
        [[ "$line" =~ ^#.*$ || -z "${line// }" ]] && continue
        targets+=("${line/#\~/$HOME}")
    done < "$TARGETS_FILE"
else
    echo "ℹ️  .skill-sync-targets not found — using defaults"
    targets=(
        "$HOME/.codex/skills"
        "$HOME/.gemini/skills"
        "$HOME/.cursor/skills"
        "$HOME/.gemini/antigravity/skills"
    )
fi

# ── Read ignore list ──────────────────────────────────────────
ignores=()
if [[ -f "$IGNORE_FILE" ]]; then
    while IFS= read -r line; do
        [[ "$line" =~ ^#.*$ || -z "${line// }" ]] && continue
        ignores+=("$line")
    done < "$IGNORE_FILE"
else
    echo "ℹ️  .skill-sync-ignore not found — using defaults"
    ignores=("blog" "cheatsheet" "skills-query-server")
fi

echo "Targets  : ${targets[*]}"
echo "Ignoring : ${ignores[*]}"
