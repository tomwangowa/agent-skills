#!/bin/bash

# Activity Logger Initialization Script
# Sets up directory structure and provides utility functions

set -euo pipefail

# Configuration
ACTIVITIES_DIR="${CLAUDE_ACTIVITIES_DIR:-$HOME/.claude/activities}"
SESSION_FILE="$ACTIVITIES_DIR/.session_id"
PROCESSED_DIR="$ACTIVITIES_DIR/processed"
CONFIG_DIR="$HOME/.claude/config"
CONFIG_FILE="$CONFIG_DIR/activity-config.json"

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Helper functions
log_info() {
    echo -e "${GREEN}[INFO]${NC} $1"
}

log_warn() {
    echo -e "${YELLOW}[WARN]${NC} $1"
}

log_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

log_header() {
    echo -e "${BLUE}=== $1 ===${NC}"
}

# Check for jq dependency (required for list, stats commands)
check_jq() {
    if ! command -v jq &> /dev/null; then
        log_error "jq is required for this command but not installed"
        echo "Install: brew install jq (macOS) or apt-get install jq (Ubuntu)"
        exit 1
    fi
}

# Initialize directory structure
init_dirs() {
    log_header "Initializing Activity Logger"

    # Create directories
    mkdir -p "$ACTIVITIES_DIR" "$PROCESSED_DIR" "$CONFIG_DIR"
    log_info "Created directory structure"

    # Create default config if it doesn't exist
    if [[ ! -f "$CONFIG_FILE" ]]; then
        cat > "$CONFIG_FILE" <<EOF
{
  "activities_dir": "$ACTIVITIES_DIR",
  "auto_archive_days": 30,
  "default_activity_type": "task_completed",
  "tracked_projects": []
}
EOF
        log_info "Created default configuration: $CONFIG_FILE"
    fi

    log_info "Initialization complete"
}

# Get current session ID
get_session_id() {
    if [[ -f "$SESSION_FILE" ]]; then
        cat "$SESSION_FILE"
    else
        echo "No active session"
    fi
}

# List all activities
list_activities() {
    check_jq
    log_header "Activity Records"

    if [[ -d "$ACTIVITIES_DIR" ]] && compgen -G "$ACTIVITIES_DIR/*.json" > /dev/null 2>&1; then
        # Use find to avoid ARG_MAX issues with large numbers of files
        local count=0
        while IFS=$'\t' read -r timestamp project desc; do
            count=$((count + 1))
            printf "%3d. %s | %s | %s\n" "$count" "$timestamp" "$project" "$desc"
        done < <(find "$ACTIVITIES_DIR" -maxdepth 1 -name "*.json" -exec jq -r '[.timestamp, .project_name, (.activities[0].description // "No description")] | @tsv' {} + 2>/dev/null)

        if [[ $count -eq 0 ]]; then
            log_info "No activity records found"
        else
            log_info "Total: $count activity record(s)"
        fi
    else
        log_info "No activity records found"
    fi
}

# Show session info
show_session_info() {
    log_header "Current Session Information"

    local session_id
    session_id=$(get_session_id)
    echo "Session ID: $session_id"

    if [[ -f "$SESSION_FILE" ]]; then
        local created
        created=$(stat -f "%Sm" -t "%Y-%m-%d %H:%M:%S" "$SESSION_FILE" 2>/dev/null || stat -c "%y" "$SESSION_FILE" 2>/dev/null || echo "Unknown")
        echo "Session Started: $created"
    fi

    echo "Activities Dir: $ACTIVITIES_DIR"

    # Count activities in this session efficiently
    local session_count=0
    if [[ "$session_id" != "No active session" ]]; then
        session_count=$(find "$ACTIVITIES_DIR" -maxdepth 1 -name "${session_id}*.json" 2>/dev/null | wc -l | tr -d ' ')
    fi
    echo "Activities in this session: $session_count"
}

# Reset session
reset_session() {
    if [[ -f "$SESSION_FILE" ]]; then
        rm "$SESSION_FILE"
        log_info "Session reset. A new session ID will be generated on next activity log."
    else
        log_warn "No active session to reset"
    fi
}

# Archive old activities
archive_activities() {
    local days="${1:-30}"
    log_header "Archiving activities older than $days days"

    local count=0
    local cutoff_date
    cutoff_date=$(date -v -"${days}"d +%s 2>/dev/null || date -d "$days days ago" +%s)

    if [[ -d "$ACTIVITIES_DIR" ]]; then
        for file in "$ACTIVITIES_DIR"/*.json; do
            [[ -f "$file" ]] || continue

            local file_date
            file_date=$(stat -f %m "$file" 2>/dev/null || stat -c %Y "$file" 2>/dev/null || echo "0")

            if [[ "$file_date" -lt "$cutoff_date" ]]; then
                mv "$file" "$PROCESSED_DIR/"
                count=$((count + 1))
            fi
        done
    fi

    if [[ $count -eq 0 ]]; then
        log_info "No activities to archive"
    else
        log_info "Archived $count activity record(s)"
    fi
}

# Show statistics
show_stats() {
    check_jq
    log_header "Activity Statistics"

    local total=0

    if [[ -d "$ACTIVITIES_DIR" ]] && compgen -G "$ACTIVITIES_DIR/*.json" > /dev/null 2>&1; then
        # Count total files efficiently using find to avoid ARG_MAX issues
        total=$(find "$ACTIVITIES_DIR" -maxdepth 1 -name "*.json" 2>/dev/null | wc -l | tr -d ' ')

        echo "Total Activities: $total"

        if [[ $total -gt 0 ]]; then
            echo ""
            echo "By Type:"
            # Extract all types in one pass and aggregate using find
            find "$ACTIVITIES_DIR" -maxdepth 1 -name "*.json" -exec jq -r '.activities[0].type // "unknown"' {} + 2>/dev/null | \
            sort | uniq -c | while read -r count type; do
                printf "  %-20s: %d\n" "$type" "$count"
            done
        fi
    else
        echo "Total Activities: 0"
    fi

    # Count processed activities efficiently
    local processed=0
    if [[ -d "$PROCESSED_DIR" ]]; then
        processed=$(find "$PROCESSED_DIR" -maxdepth 1 -name "*.json" 2>/dev/null | wc -l | tr -d ' ')
    fi
    echo ""
    echo "Processed Activities: $processed"
}

# Main function
main() {
    local command="${1:-init}"

    case "$command" in
        init)
            init_dirs
            ;;
        info)
            show_session_info
            ;;
        list)
            list_activities
            ;;
        reset)
            reset_session
            ;;
        archive)
            archive_activities "${2:-30}"
            ;;
        stats)
            show_stats
            ;;
        help|--help|-h)
            cat <<HELP
Activity Logger Initialization and Management

Usage: init_activities.sh [COMMAND] [OPTIONS]

Commands:
  init              Initialize directory structure (default)
  info              Show current session information
  list              List all activity records
  reset             Reset current session ID
  archive [DAYS]    Archive activities older than DAYS (default: 30)
  stats             Show activity statistics
  help              Show this help message

Environment Variables:
  CLAUDE_ACTIVITIES_DIR   Override activities directory (default: ~/.claude/activities)

Examples:
  init_activities.sh init              # Initialize directories
  init_activities.sh info              # Show session info
  init_activities.sh list              # List all activities
  init_activities.sh archive 60        # Archive activities older than 60 days
HELP
            ;;
        *)
            log_error "Unknown command: $command"
            echo "Use 'help' for usage information"
            exit 1
            ;;
    esac
}

# Run main function
main "$@"
