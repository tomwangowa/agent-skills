#!/usr/bin/env bash
set -euo pipefail

SKILLS_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)"
TARGETS_FILE="$SKILLS_DIR/.skill-sync-targets"
IGNORE_FILE="$SKILLS_DIR/.skill-sync-ignore"

# Trim CR, inline comment, surrounding whitespace; echo cleaned line.
clean_line() {
    local s="$1"
    s="${s%$'\r'}"
    s="${s%%#*}"
    s="${s#"${s%%[![:space:]]*}"}"
    s="${s%"${s##*[![:space:]]}"}"
    printf '%s' "$s"
}

DEFAULT_TARGETS=(
    "$HOME/.codex/skills"
    "$HOME/.gemini/skills"
    "$HOME/.cursor/skills"
    "$HOME/.gemini/antigravity/skills"
)
DEFAULT_IGNORES=("blog" "cheatsheet" "skills-query-server" "skillshare" "spec-generator")

# ── Read targets ──────────────────────────────────────────────
targets=()
if [[ -f "$TARGETS_FILE" ]]; then
    while IFS= read -r line || [[ -n "$line" ]]; do
        line="$(clean_line "$line")"
        [[ -z "$line" ]] && continue
        targets+=("${line/#\~/$HOME}")
    done < "$TARGETS_FILE"
fi
if [[ ${#targets[@]} -eq 0 ]]; then
    echo "ℹ️  .skill-sync-targets missing or empty — using defaults"
    targets=("${DEFAULT_TARGETS[@]}")
fi

# ── Read ignore list ──────────────────────────────────────────
ignores=()
if [[ -f "$IGNORE_FILE" ]]; then
    while IFS= read -r line || [[ -n "$line" ]]; do
        line="$(clean_line "$line")"
        [[ -z "$line" ]] && continue
        ignores+=("$line")
    done < "$IGNORE_FILE"
fi
if [[ ${#ignores[@]} -eq 0 ]]; then
    echo "ℹ️  .skill-sync-ignore missing or empty — using defaults"
    ignores=("${DEFAULT_IGNORES[@]}")
fi

# ── Build exclude args ─────────────────────────────────────────
exclude_args=(
    "--exclude=.git"
    "--exclude=.DS_Store"
    "--exclude=.skill-sync-targets"
    "--exclude=.skill-sync-ignore"
)
for skill in "${ignores[@]}"; do
    exclude_args+=("--exclude=${skill}")
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
echo "🔍  Dry-run preview (⚠️  --delete is active: files in target not in source WILL be removed):"
echo "─────────────────────────────────────────"

all_dry_output=""
tmp_err="$(mktemp)"
trap 'rm -f "$tmp_err"' EXIT
for target in "${targets[@]}"; do
    if ! dry=$(rsync -avL --delete --dry-run "${exclude_args[@]}" "$SKILLS_DIR/" "$target/" 2>"$tmp_err"); then
        echo "→ $target  ⚠️  rsync error:"
        sed 's/^/    /' "$tmp_err"
        continue
    fi
    dry=$(printf '%s\n' "$dry" | grep -Ev '^(sending|sent|total size|Transfer starting|\./|$)' || true)
    if [[ -n "$dry" ]]; then
        del_count=$(printf '%s\n' "$dry" | grep -c '^deleting ' || true)
        echo "→ $target"
        if (( del_count > 0 )); then
            echo "   ⚠️  Will DELETE $del_count item(s) in target not present in source"
        fi
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
printf "Proceed with sync? (y/N) "
read -r confirm
if [[ ! "$confirm" =~ ^[Yy]([Ee][Ss])?$ ]]; then
    echo "Sync cancelled."
    exit 0
fi

# ── Execute ────────────────────────────────────────────────────
echo ""
sync_targets=()
sync_statuses=()

for target in "${targets[@]}"; do
    sync_targets+=("$target")
    if err=$(rsync -aL --delete "${exclude_args[@]}" "$SKILLS_DIR/" "$target/" 2>&1 >/dev/null); then
        sync_statuses+=("✅ synced")
        echo "✅ $target"
    else
        first_err_line="${err%%$'\n'*}"
        sync_statuses+=("❌ ${first_err_line}")
        echo "❌ $target — ${first_err_line}"
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
