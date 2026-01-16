#!/usr/bin/env bash

###############################################################################
# Skill Namespace Migration Script
#
# Migrates skills from legacy naming (e.g., code-review-gemini) to
# namespaced naming (e.g., tm-code-review-gemini).
#
# Usage:
#   ./migrate_skill_names.sh [--dry-run] [--namespace PREFIX] [--no-symlinks]
#
# Options:
#   --dry-run         Preview changes without executing them
#   --namespace PREFIX Use custom namespace (default: tm)
#   --no-symlinks     Skip creating backward-compatible symlinks
#   --help            Show this help message
#
# Author: Tom Wang
# Date: 2025-01-17
###############################################################################

set -euo pipefail

# Color codes for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
CYAN='\033[0;36m'
NC='\033[0m' # No Color

# Default configuration
NAMESPACE="tm"
DRY_RUN=false
CREATE_SYMLINKS=true
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
SKILLS_DIR="$(dirname "$SCRIPT_DIR")"
MIGRATION_LOG="${SKILLS_DIR}/migration_$(date +%Y%m%d_%H%M%S).log"

# Migration mapping: old_name -> new_name
# Using parallel arrays for bash 3.2 compatibility
SKILL_OLD_NAMES=(
    "ui-design-analyzer"
    "activity-logger"
    "code-review-gemini"
    "code-story-teller"
    "commit-msg-generator"
    "interactive-presentation-generator"
    "skill-auditor"
    "pr-review-assistant"
    "spec-generator"
    "spec-review-assistant"
    "work-log-analyzer"
)

SKILL_NEW_NAMES=(
    "tm-ui-design-analyzer"
    "tm-activity-logger"
    "tm-code-review-gemini"
    "tm-code-story-teller"
    "tm-commit-msg-generator"
    "tm-interactive-presentation-generator"
    "tm-skill-auditor"
    "tm-pr-review-assistant"
    "tm-spec-generator"
    "tm-spec-review-assistant"
    "tm-work-log-analyzer"
)

###############################################################################
# Helper Functions
###############################################################################

log() {
    echo -e "${GREEN}[INFO]${NC} $*" | tee -a "$MIGRATION_LOG"
}

warn() {
    echo -e "${YELLOW}[WARN]${NC} $*" | tee -a "$MIGRATION_LOG"
}

error() {
    echo -e "${RED}[ERROR]${NC} $*" | tee -a "$MIGRATION_LOG"
}

debug() {
    echo -e "${CYAN}[DEBUG]${NC} $*" | tee -a "$MIGRATION_LOG"
}

show_help() {
    cat << EOF
${BLUE}Skill Namespace Migration Script${NC}

Migrates skills from legacy naming to namespaced naming.

${YELLOW}Usage:${NC}
  ./migrate_skill_names.sh [OPTIONS]

${YELLOW}Options:${NC}
  --dry-run         Preview changes without executing them
  --namespace PREFIX Use custom namespace (default: tm)
  --no-symlinks     Skip creating backward-compatible symlinks
  --help            Show this help message

${YELLOW}Examples:${NC}
  # Preview migration
  ./migrate_skill_names.sh --dry-run

  # Execute migration with default namespace (tm)
  ./migrate_skill_names.sh

  # Execute migration with custom namespace
  ./migrate_skill_names.sh --namespace myteam

  # Migrate without creating symlinks
  ./migrate_skill_names.sh --no-symlinks

${YELLOW}What it does:${NC}
  1. Renames skill directories (adds namespace prefix)
  2. Updates SKILL.md frontmatter with new metadata
  3. Creates symlinks for backward compatibility (optional)
  4. Generates migration report

${YELLOW}Output:${NC}
  - Migration log: ${SKILLS_DIR}/migration_YYYYMMDD_HHMMSS.log
  - Backup: ${SKILLS_DIR}/backup_YYYYMMDD_HHMMSS/

EOF
}

###############################################################################
# Parse command line arguments
###############################################################################

parse_args() {
    while [[ $# -gt 0 ]]; do
        case $1 in
            --dry-run)
                DRY_RUN=true
                shift
                ;;
            --namespace)
                NAMESPACE="$2"
                shift 2
                ;;
            --no-symlinks)
                CREATE_SYMLINKS=false
                shift
                ;;
            --help|-h)
                show_help
                exit 0
                ;;
            *)
                error "Unknown option: $1"
                show_help
                exit 1
                ;;
        esac
    done
}

###############################################################################
# Update SKILL.md frontmatter
###############################################################################

update_skill_frontmatter() {
    local skill_md="$1"
    local old_name="$2"
    local new_name="$3"
    local namespace="$4"

    if [[ ! -f "$skill_md" ]]; then
        warn "SKILL.md not found: $skill_md"
        return 1
    fi

    debug "Updating frontmatter: $skill_md"

    # Extract domain, action, qualifier from new name
    # Format: tm-<domain>-<action>[-<qualifier>]
    local name_parts="${new_name#$namespace-}"  # Remove namespace prefix
    local domain action qualifier

    # Simple parsing: split by dash
    IFS='-' read -ra PARTS <<< "$name_parts"
    domain="${PARTS[0]}"
    action="${PARTS[1]:-unknown}"
    qualifier="${PARTS[2]:-}"

    # Read existing frontmatter
    local has_frontmatter=false
    if head -n 1 "$skill_md" | grep -q "^---"; then
        has_frontmatter=true
    fi

    if [[ "$DRY_RUN" == true ]]; then
        log "  [DRY-RUN] Would update frontmatter in: $skill_md"
        log "    - id: $new_name"
        log "    - namespace: $namespace"
        log "    - domain: $domain"
        log "    - action: $action"
        [[ -n "$qualifier" ]] && log "    - qualifier: $qualifier"
        return 0
    fi

    # Create temporary file
    local temp_file
    temp_file=$(mktemp)

    if [[ "$has_frontmatter" == true ]]; then
        # Update existing frontmatter
        awk -v new_id="$new_name" \
            -v ns="$namespace" \
            -v dom="$domain" \
            -v act="$action" \
            -v qual="$qualifier" \
            -v updated="$(date +%Y-%m-%d)" '
        BEGIN { in_fm=0; fm_ended=0; id_found=0; ns_found=0; dom_found=0; act_found=0; qual_found=0; ver_found=0; upd_found=0 }
        /^---$/ {
            if (in_fm == 0) {
                in_fm=1; print; next
            } else {
                # End of frontmatter - add missing fields
                if (!id_found) print "id: " new_id
                if (!ns_found) print "namespace: " ns
                if (!dom_found) print "domain: " dom
                if (!act_found) print "action: " act
                if (qual != "" && !qual_found) print "qualifier: " qual
                if (!ver_found) print "version: \"1.0.0\""
                if (!upd_found) print "updated: \"" updated "\""
                fm_ended=1; in_fm=0; print; next
            }
        }
        in_fm == 1 {
            if (/^id:/ || /^name:.*\(id:/) { print "id: " new_id; id_found=1; next }
            if (/^namespace:/) { print "namespace: " ns; ns_found=1; next }
            if (/^domain:/) { print "domain: " dom; dom_found=1; next }
            if (/^action:/) { print "action: " act; act_found=1; next }
            if (/^qualifier:/ && qual != "") { print "qualifier: " qual; qual_found=1; next }
            if (/^version:/) { ver_found=1 }
            if (/^updated:/) { print "updated: \"" updated "\""; upd_found=1; next }
            print
            next
        }
        { print }
        ' "$skill_md" > "$temp_file"
    else
        # Add new frontmatter
        {
            echo "---"
            echo "name: \"$(basename "$new_name" | sed 's/-/ /g' | awk '{for(i=1;i<=NF;i++) $i=toupper(substr($i,1,1)) tolower(substr($i,2));}1')\""
            echo "id: $new_name"
            echo "description: \"TODO: Add description\""
            echo "version: \"1.0.0\""
            echo "namespace: $namespace"
            echo "domain: $domain"
            echo "action: $action"
            [[ -n "$qualifier" ]] && echo "qualifier: $qualifier"
            echo "updated: \"$(date +%Y-%m-%d)\""
            echo "---"
            echo ""
            cat "$skill_md"
        } > "$temp_file"
    fi

    # Replace original file
    mv "$temp_file" "$skill_md"
    log "  ✓ Updated frontmatter: $skill_md"
}

###############################################################################
# Migrate a single skill
###############################################################################

migrate_skill() {
    local old_name="$1"
    local new_name="$2"

    local old_path="${SKILLS_DIR}/${old_name}"
    local new_path="${SKILLS_DIR}/${new_name}"

    log ""
    log "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
    log "Migrating: ${BLUE}${old_name}${NC} → ${GREEN}${new_name}${NC}"
    log "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"

    # Check if old path exists
    if [[ ! -d "$old_path" ]]; then
        warn "Skill directory not found: $old_path (already migrated?)"
        return 0
    fi

    # Check if new path already exists
    if [[ -d "$new_path" ]]; then
        error "Target directory already exists: $new_path"
        return 1
    fi

    # Rename directory
    if [[ "$DRY_RUN" == true ]]; then
        log "[DRY-RUN] Would rename: $old_path → $new_path"
    else
        mv "$old_path" "$new_path"
        log "✓ Renamed directory"
    fi

    # Update SKILL.md frontmatter
    update_skill_frontmatter "${new_path}/SKILL.md" "$old_name" "$new_name" "$NAMESPACE"

    # Create symlink for backward compatibility
    if [[ "$CREATE_SYMLINKS" == true ]]; then
        if [[ "$DRY_RUN" == true ]]; then
            log "[DRY-RUN] Would create symlink: $old_name → $new_name"
        else
            ln -s "$new_name" "$old_path"
            log "✓ Created symlink: $old_name → $new_name"
        fi
    fi

    log "✓ Migration completed: $new_name"
}

###############################################################################
# Main migration process
###############################################################################

main() {
    parse_args "$@"

    echo -e "${BLUE}"
    cat << "EOF"
╔═══════════════════════════════════════════════════════════════╗
║                                                               ║
║         Skill Namespace Migration Tool                       ║
║                                                               ║
╚═══════════════════════════════════════════════════════════════╝
EOF
    echo -e "${NC}"

    log "Migration started at: $(date)"
    log "Skills directory: $SKILLS_DIR"
    log "Namespace: $NAMESPACE"
    log "Dry-run mode: $DRY_RUN"
    log "Create symlinks: $CREATE_SYMLINKS"
    log "Migration log: $MIGRATION_LOG"
    log ""

    # Update mapping with custom namespace if provided
    if [[ "$NAMESPACE" != "tm" ]]; then
        log "Using custom namespace: $NAMESPACE"
        for i in "${!SKILL_OLD_NAMES[@]}"; do
            SKILL_NEW_NAMES[$i]="${NAMESPACE}-${SKILL_OLD_NAMES[$i]}"
        done
    fi

    # Create backup if not dry-run
    if [[ "$DRY_RUN" == false ]]; then
        local backup_dir="${SKILLS_DIR}/backup_$(date +%Y%m%d_%H%M%S)"
        log "Creating backup: $backup_dir"
        mkdir -p "$backup_dir"

        for old_name in "${SKILL_OLD_NAMES[@]}"; do
            local old_path="${SKILLS_DIR}/${old_name}"
            if [[ -d "$old_path" ]]; then
                cp -r "$old_path" "$backup_dir/"
                debug "Backed up: $old_name"
            fi
        done

        log "✓ Backup completed"
    fi

    # Migrate each skill
    local success_count=0
    local fail_count=0
    local skip_count=0

    for i in "${!SKILL_OLD_NAMES[@]}"; do
        local old_name="${SKILL_OLD_NAMES[$i]}"
        local new_name="${SKILL_NEW_NAMES[$i]}"

        if migrate_skill "$old_name" "$new_name"; then
            ((success_count++))
        else
            ((fail_count++))
        fi
    done

    # Summary
    log ""
    log "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
    log "${GREEN}Migration Summary${NC}"
    log "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
    log "Total skills: ${#SKILL_OLD_NAMES[@]}"
    log "Successful: ${GREEN}${success_count}${NC}"
    log "Failed: ${RED}${fail_count}${NC}"
    log "Skipped: ${YELLOW}${skip_count}${NC}"
    log ""

    if [[ "$DRY_RUN" == true ]]; then
        log "${YELLOW}This was a dry-run. No changes were made.${NC}"
        log "Run without --dry-run to execute the migration."
    else
        log "${GREEN}Migration completed!${NC}"
        log ""
        log "Next steps:"
        log "  1. Review the changes"
        log "  2. Test the migrated skills"
        log "  3. Update documentation (README.md, etc.)"
        log "  4. Commit the changes"
        log ""
        log "If something went wrong, restore from backup:"
        log "  ${CYAN}rm -rf ${SKILLS_DIR}/tm-*${NC}"
        log "  ${CYAN}cp -r ${SKILLS_DIR}/backup_*/* ${SKILLS_DIR}/${NC}"
    fi

    log ""
    log "Migration log saved to: $MIGRATION_LOG"
    log "Completed at: $(date)"
}

# Run main function
main "$@"
