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

# ── Build exclude args ─────────────────────────────────────────
exclude_args=(
    "--exclude=.git"
    "--exclude=.DS_Store"
    "--exclude=.skill-sync-targets"
    "--exclude=.skill-sync-ignore"
)
for skill in "${ignores[@]}"; do
    exclude_args+=("--exclude=${skill}/")
done

# ── Pre-flight ─────────────────────────────────────────────────
for target in "${targets[@]}"; do
    if [[ ! -d "$target" ]]; then
        echo "📁  Creating $target"
        mkdir -p "$target"
    fi
done

# ── Dry-run ────────────────────────────────────────────────────
echo ""
echo "🔍  Dry-run preview:"
echo "─────────────────────────────────────────"

all_dry_output=""
for target in "${targets[@]}"; do
    dry=$(rsync -avL --delete --dry-run "${exclude_args[@]}" "$SKILLS_DIR/" "$target/" 2>/dev/null \
        | grep -Ev '^(sending|sent|total size|\./)' | grep -v '^$' || true)
    if [[ -n "$dry" ]]; then
        echo "→ $target"
        echo "$dry"
        echo ""
        all_dry_output+="$dry"
    fi
done

if [[ -z "$all_dry_output" ]]; then
    echo "All targets already up to date."
    exit 0
fi

echo "─────────────────────────────────────────"
printf "Proceed with sync? (y/n) "
read -r confirm
if [[ "$(echo "$confirm" | tr '[:upper:]' '[:lower:]')" != "y" ]]; then
    echo "Sync cancelled."
    exit 0
fi

# ── Execute ────────────────────────────────────────────────────
echo ""
sync_targets=()
sync_statuses=()

for target in "${targets[@]}"; do
    sync_targets+=("$target")
    if rsync -aL --delete "${exclude_args[@]}" "$SKILLS_DIR/" "$target/" 2>/dev/null; then
        sync_statuses+=("✅ synced")
    else
        sync_statuses+=("❌ error")
    fi
done

# ── Summary ────────────────────────────────────────────────────
echo ""
echo "| Target | Status |"
echo "|--------|--------|"
i=0
while [[ $i -lt ${#sync_targets[@]} ]]; do
    printf "| %-50s | %s |\n" "${sync_targets[$i]}" "${sync_statuses[$i]}"
    i=$((i + 1))
done
