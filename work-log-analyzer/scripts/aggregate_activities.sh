#!/bin/bash

# Activity Aggregator Script
# Aggregates activity records from activity-logger into readable work logs

set -euo pipefail

# Configuration
ACTIVITIES_DIR="${CLAUDE_ACTIVITIES_DIR:-$HOME/.claude/activities}"

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Helper functions
log_info() {
    echo -e "${GREEN}[INFO]${NC} $1" >&2
}

log_error() {
    echo -e "${RED}[ERROR]${NC} $1" >&2
}

# Check dependencies
check_dependencies() {
    local missing=()

    for cmd in jq date; do
        if ! command -v "$cmd" &> /dev/null; then
            missing+=("$cmd")
        fi
    done

    if [[ ${#missing[@]} -gt 0 ]]; then
        log_error "Missing required dependencies: ${missing[*]}"
        exit 1
    fi
}

# Get date range in seconds since epoch
get_date_range() {
    local range="$1"
    local now
    now=$(date +%s)

    case "$range" in
        today)
            local today_start
            # BSD date (macOS)
            today_start=$(date -j -f "%Y-%m-%d %H:%M:%S" "$(date +%Y-%m-%d) 00:00:00" +%s 2>/dev/null || date -d "$(date +%Y-%m-%d) 00:00:00" +%s)
            echo "$today_start|$now"
            ;;
        yesterday)
            local yesterday_start yesterday_end
            # Yesterday 00:00:00 to today 00:00:00
            yesterday_start=$(date -j -v-1d -f "%Y-%m-%d %H:%M:%S" "$(date +%Y-%m-%d) 00:00:00" +%s 2>/dev/null || date -d "yesterday 00:00:00" +%s)
            yesterday_end=$(date -j -f "%Y-%m-%d %H:%M:%S" "$(date +%Y-%m-%d) 00:00:00" +%s 2>/dev/null || date -d "today 00:00:00" +%s)
            echo "$yesterday_start|$yesterday_end"
            ;;
        this-week)
            local week_start day_of_week
            # Get day of week (1=Monday, 7=Sunday)
            day_of_week=$(date +%u 2>/dev/null || date +%w | awk '{print ($1 == 0) ? 7 : $1}')
            # Calculate days since Monday (0 if today is Monday)
            local days_since_monday=$((day_of_week - 1))

            # BSD date (macOS)
            if date -j -v-1d &>/dev/null 2>&1; then
                week_start=$(date -j -v-${days_since_monday}d -v0H -v0M -v0S +%s)
            else
                # GNU date (Linux)
                week_start=$(date -d "$days_since_monday days ago 00:00:00" +%s)
            fi
            echo "$week_start|$now"
            ;;
        last-week)
            local last_week_start last_week_end day_of_week
            # Get day of week
            day_of_week=$(date +%u 2>/dev/null || date +%w | awk '{print ($1 == 0) ? 7 : $1}')
            local days_since_monday=$((day_of_week - 1))
            local days_to_last_monday=$((days_since_monday + 7))

            # BSD date (macOS)
            if date -j -v-1d &>/dev/null 2>&1; then
                last_week_start=$(date -j -v-${days_to_last_monday}d -v0H -v0M -v0S +%s)
                last_week_end=$(date -j -v-${days_since_monday}d -v0H -v0M -v0S +%s)
            else
                # GNU date (Linux)
                last_week_start=$(date -d "$days_to_last_monday days ago 00:00:00" +%s)
                last_week_end=$(date -d "$days_since_monday days ago 00:00:00" +%s)
            fi
            echo "$last_week_start|$last_week_end"
            ;;
        this-month)
            local month_start
            # First day of month at 00:00:00
            month_start=$(date -j -f "%Y-%m-%d %H:%M:%S" "$(date +%Y-%m-01) 00:00:00" +%s 2>/dev/null || date -d "$(date +%Y-%m-01) 00:00:00" +%s)
            echo "$month_start|$now"
            ;;
        all)
            echo "0|$now"
            ;;
        *)
            log_error "Unknown date range: $range"
            exit 1
            ;;
    esac
}

# Convert ISO timestamp to epoch
iso_to_epoch() {
    local iso="$1"
    date -j -f "%Y-%m-%dT%H:%M:%SZ" "$iso" +%s 2>/dev/null || date -d "$iso" +%s 2>/dev/null || echo "0"
}

# Aggregate activities
aggregate_activities() {
    local mode="${1:-by-date}"
    local date_range="${2:-all}"
    local project_filter="${3:-}"
    local type_filter="${4:-}"
    local tag_filter="${5:-}"

    check_dependencies

    if [[ ! -d "$ACTIVITIES_DIR" ]]; then
        log_error "Activities directory not found: $ACTIVITIES_DIR"
        exit 1
    fi

    # Get date range
    local date_range_str
    date_range_str=$(get_date_range "$date_range")
    IFS='|' read -r start_time end_time <<< "$date_range_str"

    # Collect and filter activities
    local activities=()

    while IFS= read -r file; do
        [[ -f "$file" ]] || continue

        # Extract data
        local timestamp project_name activity_type tags
        timestamp=$(jq -r '.timestamp' "$file" 2>/dev/null || echo "")
        project_name=$(jq -r '.project_name' "$file" 2>/dev/null || echo "")
        activity_type=$(jq -r '.activities[0].type' "$file" 2>/dev/null || echo "")
        tags=$(jq -r '.tags // [] | .[]' "$file" 2>/dev/null | tr '\n' ',' || echo "")

        [[ -z "$timestamp" ]] && continue

        # Convert timestamp to epoch for comparison
        local epoch
        epoch=$(iso_to_epoch "$timestamp")

        # Apply filters
        [[ $epoch -lt $start_time ]] && continue
        [[ $epoch -gt $end_time ]] && continue
        [[ -n "$project_filter" && "$project_name" != "$project_filter" ]] && continue
        [[ -n "$type_filter" && "$activity_type" != "$type_filter" ]] && continue
        [[ -n "$tag_filter" && ! "$tags" =~ $tag_filter ]] && continue

        activities+=("$file")
    done < <(find "$ACTIVITIES_DIR" -maxdepth 1 -name "*.json" 2>/dev/null)

    if [[ ${#activities[@]} -eq 0 ]]; then
        log_info "No activities found matching criteria"
        return
    fi

    log_info "Found ${#activities[@]} activities"

    # Output based on mode
    case "$mode" in
        by-date)
            output_by_date "${activities[@]}"
            ;;
        by-project)
            output_by_project "${activities[@]}"
            ;;
        by-type)
            output_by_type "${activities[@]}"
            ;;
        json)
            output_json "${activities[@]}"
            ;;
        *)
            log_error "Unknown mode: $mode"
            exit 1
            ;;
    esac
}

# Output activities grouped by date
output_by_date() {
    local files=("$@")

    echo "# Activity Report"
    echo ""
    echo "Generated: $(date '+%Y-%m-%d %H:%M:%S')"
    echo ""

    # Sort files by timestamp
    local sorted_files=()
    while IFS= read -r file; do
        sorted_files+=("$file")
    done < <(
        for file in "${files[@]}"; do
            local ts
            ts=$(jq -r '.timestamp' "$file" 2>/dev/null || echo "")
            echo "$ts|$file"
        done | sort -r | cut -d'|' -f2
    )

    local current_date=""
    for file in "${sorted_files[@]}"; do
        local data
        data=$(jq -r '. as $root | .timestamp as $ts | ($ts | split("T")[0]) as $date | {
            date: $date,
            time: ($ts | split("T")[1] | split("Z")[0] | split(":")[0:2] | join(":")),
            project: .project_name,
            type: .activities[0].type,
            description: .activities[0].description,
            context: .context,
            tags: .tags,
            files: .activities[0].files_changed,
            branch: .git_branch
        }' "$file" 2>/dev/null)

        local date time project type desc context tags files branch
        date=$(echo "$data" | jq -r '.date')
        time=$(echo "$data" | jq -r '.time')
        project=$(echo "$data" | jq -r '.project')
        type=$(echo "$data" | jq -r '.type')
        desc=$(echo "$data" | jq -r '.description')
        context=$(echo "$data" | jq -r '.context')
        tags=$(echo "$data" | jq -r '.tags[]' 2>/dev/null | tr '\n' ', ' | sed 's/,$//')
        files=$(echo "$data" | jq -r '.files[]' 2>/dev/null | wc -l | tr -d ' ')
        branch=$(echo "$data" | jq -r '.branch')

        if [[ "$date" != "$current_date" ]]; then
            [[ -n "$current_date" ]] && echo ""
            echo "## $date"
            echo ""
            current_date="$date"
        fi

        echo "### $time - [$type] $project"
        echo ""
        echo "**$desc**"
        [[ -n "$context" && "$context" != "null" ]] && echo ""
        [[ -n "$context" && "$context" != "null" ]] && echo "$context"
        [[ -n "$branch" && "$branch" != "null" ]] && echo ""
        [[ -n "$branch" && "$branch" != "null" ]] && echo "- Branch: \`$branch\`"
        [[ "$files" != "0" ]] && echo "- Files changed: $files"
        [[ -n "$tags" ]] && echo "- Tags: $tags"
        echo ""
    done
}

# Output activities grouped by project
output_by_project() {
    local files=("$@")

    echo "# Activity Report - By Project"
    echo ""
    echo "Generated: $(date '+%Y-%m-%d %H:%M:%S')"
    echo ""

    # Get unique projects
    local projects=()
    for file in "${files[@]}"; do
        local project
        project=$(jq -r '.project_name' "$file" 2>/dev/null || echo "unknown")
        projects+=("$project")
    done

    # Get unique sorted projects
    local unique_projects
    unique_projects=$(printf '%s\n' "${projects[@]}" | sort -u)

    # Output each project
    while IFS= read -r project; do
        [[ -z "$project" ]] && continue

        echo "## $project"
        echo ""

        # Find files for this project and sort
        local sorted_files=()
        while IFS= read -r file; do
            sorted_files+=("$file")
        done < <(
            for file in "${files[@]}"; do
                local proj
                proj=$(jq -r '.project_name' "$file" 2>/dev/null || echo "unknown")
                if [[ "$proj" == "$project" ]]; then
                    local ts
                    ts=$(jq -r '.timestamp' "$file" 2>/dev/null || echo "")
                    echo "$ts|$file"
                fi
            done | sort -r | cut -d'|' -f2
        )

        for file in "${sorted_files[@]}"; do
            local data
            data=$(jq -r '{
                timestamp: .timestamp,
                type: .activities[0].type,
                description: .activities[0].description,
                tags: .tags
            }' "$file" 2>/dev/null)

            local timestamp type desc tags
            timestamp=$(echo "$data" | jq -r '.timestamp | split("T") | "\(.[0]) \(.[1] | split("Z")[0] | split(":")[0:2] | join(":"))"')
            type=$(echo "$data" | jq -r '.type')
            desc=$(echo "$data" | jq -r '.description')
            tags=$(echo "$data" | jq -r '.tags // [] | .[]' 2>/dev/null | tr '\n' ', ' | sed 's/,$//')

            echo "- **$timestamp** [$type] $desc"
            [[ -n "$tags" ]] && echo "  - Tags: $tags"
        done

        echo ""
    done <<< "$unique_projects"
}

# Output activities grouped by type
output_by_type() {
    local files=("$@")

    echo "# Activity Report - By Type"
    echo ""
    echo "Generated: $(date '+%Y-%m-%d %H:%M:%S')"
    echo ""

    # Get unique types
    local types=()
    for file in "${files[@]}"; do
        local type
        type=$(jq -r '.activities[0].type' "$file" 2>/dev/null || echo "unknown")
        types+=("$type")
    done

    # Get unique sorted types
    local unique_types
    unique_types=$(printf '%s\n' "${types[@]}" | sort -u)

    # Output each type
    while IFS= read -r type; do
        [[ -z "$type" ]] && continue

        local type_label
        case "$type" in
            task_completed) type_label="✅ Tasks Completed" ;;
            bug_fixed) type_label="🐛 Bugs Fixed" ;;
            refactoring) type_label="♻️  Refactoring" ;;
            research) type_label="🔍 Research" ;;
            documentation) type_label="📝 Documentation" ;;
            review) type_label="👀 Code Review" ;;
            *) type_label="📌 $type" ;;
        esac

        echo "## $type_label"
        echo ""

        # Find files for this type
        for file in "${files[@]}"; do
            local file_type
            file_type=$(jq -r '.activities[0].type' "$file" 2>/dev/null || echo "unknown")

            if [[ "$file_type" == "$type" ]]; then
                local data
                data=$(jq -r '{
                    timestamp: .timestamp,
                    project: .project_name,
                    description: .activities[0].description
                }' "$file" 2>/dev/null)

                local timestamp project desc
                timestamp=$(echo "$data" | jq -r '.timestamp | split("T") | "\(.[0]) \(.[1] | split("Z")[0] | split(":")[0:2] | join(":"))"')
                project=$(echo "$data" | jq -r '.project')
                desc=$(echo "$data" | jq -r '.description')

                echo "- **$timestamp** [$project] $desc"
            fi
        done

        echo ""
    done <<< "$unique_types"
}

# Output raw JSON
output_json() {
    local files=("$@")

    echo "["
    local first=true
    for file in "${files[@]}"; do
        [[ "$first" == true ]] && first=false || echo ","
        jq -c '.' "$file" 2>/dev/null
    done
    echo "]"
}

# Show help
show_help() {
    cat <<HELP
Activity Aggregator - Aggregate activity records into work logs

Usage: $(basename "$0") [OPTIONS]

Options:
  -m, --mode MODE          Output mode (default: by-date)
                           Modes: by-date, by-project, by-type, json
  -r, --range RANGE        Date range (default: all)
                           Ranges: today, yesterday, this-week, last-week, this-month, all
  -p, --project PROJECT    Filter by project name
  -t, --type TYPE          Filter by activity type
                           Types: task_completed, bug_fixed, refactoring, research, documentation, review
  --tag TAG                Filter by tag
  -h, --help               Show this help message

Examples:
  # Show all activities by date
  $(basename "$0")

  # Show today's activities
  $(basename "$0") -r today

  # Show this week's activities for a specific project
  $(basename "$0") -r this-week -p my-project

  # Show all bug fixes
  $(basename "$0") -t bug_fixed

  # Show activities by project
  $(basename "$0") -m by-project -r this-month

  # Export as JSON
  $(basename "$0") -m json -r today
HELP
}

# Main function
main() {
    local mode="by-date"
    local date_range="all"
    local project_filter=""
    local type_filter=""
    local tag_filter=""

    while [[ $# -gt 0 ]]; do
        case $1 in
            -m|--mode)
                [[ $# -lt 2 ]] && { log_error "Missing value for $1"; exit 1; }
                mode="$2"
                shift 2
                ;;
            -r|--range)
                [[ $# -lt 2 ]] && { log_error "Missing value for $1"; exit 1; }
                date_range="$2"
                shift 2
                ;;
            -p|--project)
                [[ $# -lt 2 ]] && { log_error "Missing value for $1"; exit 1; }
                project_filter="$2"
                shift 2
                ;;
            -t|--type)
                [[ $# -lt 2 ]] && { log_error "Missing value for $1"; exit 1; }
                type_filter="$2"
                shift 2
                ;;
            --tag)
                [[ $# -lt 2 ]] && { log_error "Missing value for $1"; exit 1; }
                tag_filter="$2"
                shift 2
                ;;
            -h|--help)
                show_help
                exit 0
                ;;
            *)
                log_error "Unknown option: $1"
                echo "Use -h or --help for usage information"
                exit 1
                ;;
        esac
    done

    aggregate_activities "$mode" "$date_range" "$project_filter" "$type_filter" "$tag_filter"
}

# Run main function
main "$@"
