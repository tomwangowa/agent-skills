#!/usr/bin/env bash
set -euo pipefail

SKILLS_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)"
TARGETS_FILE="$SKILLS_DIR/.skill-sync-targets"
IGNORE_FILE="$SKILLS_DIR/.skill-sync-ignore"

# ── Parse args ─────────────────────────────────────────────────
# Default is mirror mode (rsync --delete). --no-delete switches to
# additive mode: source skills are synced in, but target-only files
# are preserved (never removed). delete_args stays empty in additive
# mode and is expanded with the set -u-safe ${arr[@]+"${arr[@]}"} idiom.
delete_args=("--delete")
dry_run=false
for arg in "$@"; do
    case "$arg" in
        --no-delete)
            delete_args=()
            ;;
        --dry-run)
            dry_run=true
            ;;
        -h|--help)
            cat <<'EOF'
Usage: sync.sh [--dry-run] [--no-delete]

Mirror ~/.claude/skills/ to configured agent skill folders.

  (default)     Mirror mode: rsync --delete removes target-side files
                that are not present in the source.
  --no-delete   Additive mode: sync source skills into targets but
                PRESERVE target-only files (no deletion).
  --dry-run     Read-only preview: never creates target directories,
                prompts, or writes files. Missing targets are skipped.

Targets:  .skill-sync-targets  (falls back to built-in defaults)
Excludes: .skill-sync-ignore   (falls back to built-in defaults)
EOF
            exit 0
            ;;
        *)
            echo "Unknown argument: $arg" >&2
            echo "Run 'bash sync.sh --help' for usage." >&2
            exit 2
            ;;
    esac
done

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
DEFAULT_IGNORES=("blog" "cheatsheet" "skills-query-server" "spec-generator")

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
if [[ "$dry_run" == false ]]; then
    for target in "${targets[@]}"; do
        if [[ ! -d "$target" ]]; then
            echo "📁  Creating $target"
            mkdir -p "$target"
        fi
    done
fi

# ── Dry-run ────────────────────────────────────────────────────
echo ""
if [[ ${#delete_args[@]} -gt 0 ]]; then
    if [[ "$dry_run" == true ]]; then
        echo "🔍  Read-only dry-run — mode: mirror"
    else
        echo "🔍  Dry-run preview — mode: mirror"
    fi
    echo "    ⚠️  --delete is active: files in target not in source WILL be removed."
else
    if [[ "$dry_run" == true ]]; then
        echo "🔍  Read-only dry-run — mode: additive (--no-delete)"
    else
        echo "🔍  Dry-run preview — mode: additive (--no-delete)"
    fi
    echo "    ✅  target-only files are preserved; nothing in targets will be deleted."
fi
if [[ "$dry_run" == true ]]; then
    echo "    ✅  No directories or files will be created, changed, or removed."
fi
echo "─────────────────────────────────────────"

all_dry_output=""
preview_failures=0
tmp_err=""
if [[ "$dry_run" == false ]]; then
    tmp_err="$(mktemp)"
    trap 'rm -f "$tmp_err"' EXIT
fi
for target in "${targets[@]}"; do
    if [[ "$dry_run" == true && ! -e "$target" ]]; then
        echo "→ $target  skipped (target directory does not exist; read-only preview will not create it)"
        continue
    fi
    if [[ -e "$target" && ! -d "$target" ]]; then
        if [[ "$dry_run" == true ]]; then
            echo "→ $target  ⚠️  target error: path exists but is not a directory"
            preview_failures=$((preview_failures + 1))
            continue
        fi
    fi
    if [[ "$dry_run" == true ]]; then
        if ! dry=$(rsync -avL ${delete_args[@]+"${delete_args[@]}"} --dry-run "${exclude_args[@]}" "$SKILLS_DIR/" "$target/" 2>&1); then
            echo "→ $target  ⚠️  rsync error:"
            printf '%s\n' "$dry" | sed 's/^/    /'
            preview_failures=$((preview_failures + 1))
            continue
        fi
    elif ! dry=$(rsync -avL ${delete_args[@]+"${delete_args[@]}"} --dry-run "${exclude_args[@]}" "$SKILLS_DIR/" "$target/" 2>"$tmp_err"); then
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

if [[ "$dry_run" == true ]]; then
    if (( preview_failures > 0 )); then
        echo "Dry-run preview failed for $preview_failures target(s)."
        exit 1
    fi
    if [[ -z "$all_dry_output" ]]; then
        echo "All existing targets already up to date."
    fi
    exit 0
fi

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
    if err=$(rsync -aL ${delete_args[@]+"${delete_args[@]}"} "${exclude_args[@]}" "$SKILLS_DIR/" "$target/" 2>&1 >/dev/null); then
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
