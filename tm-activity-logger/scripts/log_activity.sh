#!/bin/bash

# Activity Logger Script
# Records current session activities to ~/.claude/activities/

set -euo pipefail

# Configuration
ACTIVITIES_DIR="${CLAUDE_ACTIVITIES_DIR:-$HOME/.claude/activities}"
SESSION_FILE="$ACTIVITIES_DIR/.session_id"
PROCESSED_DIR="$ACTIVITIES_DIR/processed"

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
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

# Check required dependencies
check_dependencies() {
    local missing=()

    for cmd in jq git; do
        if ! command -v "$cmd" &> /dev/null; then
            missing+=("$cmd")
        fi
    done

    if [[ ${#missing[@]} -gt 0 ]]; then
        log_error "Missing required dependencies: ${missing[*]}"
        echo "Please install the missing tools:"
        for cmd in "${missing[@]}"; do
            case "$cmd" in
                jq)
                    echo "  - jq: brew install jq (macOS) or apt-get install jq (Ubuntu)"
                    ;;
                git)
                    echo "  - git: https://git-scm.com/downloads"
                    ;;
            esac
        done
        exit 1
    fi
}

# Initialize directory structure
init_dirs() {
    mkdir -p "$ACTIVITIES_DIR" "$PROCESSED_DIR"
}

# Generate random hex string (with fallback)
generate_random_hex() {
    if command -v openssl &> /dev/null; then
        openssl rand -hex 4
    elif [[ -r /dev/urandom ]]; then
        od -An -N4 -tx1 /dev/urandom | tr -d ' \n'
    else
        # Fallback to bash RANDOM (less secure but works)
        printf '%04x%04x' $RANDOM $RANDOM
    fi
}

# Generate or get session ID
get_session_id() {
    if [[ -n "${CLAUDE_SESSION_ID:-}" ]]; then
        echo "$CLAUDE_SESSION_ID"
    elif [[ -f "$SESSION_FILE" ]]; then
        cat "$SESSION_FILE"
    else
        # Generate new session ID: timestamp + random string
        local random_hex
        random_hex=$(generate_random_hex)
        local session_id="session_$(date +%Y%m%d_%H%M%S)_${random_hex}"

        # Atomic write to prevent race condition
        echo "$session_id" > "${SESSION_FILE}.tmp"
        mv "${SESSION_FILE}.tmp" "$SESSION_FILE"

        echo "$session_id"
    fi
}

# Get project information
get_project_info() {
    local project_path
    local project_name
    local git_branch=""
    local git_remote=""

    # Try to get project name from git repo
    if git rev-parse --git-dir > /dev/null 2>&1; then
        # Use git root as project path for consistency with file paths
        project_path=$(git rev-parse --show-toplevel)
        project_name=$(basename "$project_path")
        git_branch=$(git rev-parse --abbrev-ref HEAD 2>/dev/null || echo "")
        git_remote=$(git config --get remote.origin.url 2>/dev/null || echo "")

        # Strip credentials from remote URL for security
        if [[ -n "$git_remote" ]]; then
            # Remove embedded credentials (scheme://user:pass@host -> scheme://host)
            git_remote=$(echo "$git_remote" | sed -E 's|^(https?://)[^@]+@|\1|')
        fi
    else
        # Fall back to current directory if not in git repo
        project_path="$PWD"
        project_name=$(basename "$PWD")
    fi

    echo "$project_path|$project_name|$git_branch|$git_remote"
}

# Get changed files
get_changed_files() {
    local files=()

    if git rev-parse --git-dir > /dev/null 2>&1; then
        local git_root
        git_root=$(git rev-parse --show-toplevel 2>/dev/null)

        if [[ -n "$git_root" ]]; then
            # Change to git root to ensure consistent path handling
            if ! pushd "$git_root" > /dev/null 2>&1; then
                # Return empty array but don't fail - allow logging to continue
                echo "[]"
                return 0
            fi

            # Use git status --porcelain for reliable file detection
            # Works in all git states including fresh repos without HEAD
            while IFS= read -r line; do
                # Extract filename from status (skip first 3 chars: XY<space>)
                local file="${line:3}"
                # Remove surrounding quotes if present (git quotes filenames with spaces)
                file="${file%\"}"
                file="${file#\"}"
                [[ -n "$file" ]] && files+=("$file")
            done < <(git status --porcelain 2>/dev/null || true)

            if ! popd > /dev/null 2>&1; then
                # Still return the files we collected even if popd fails
                # Don't fail - allow logging to continue
                if [[ ${#files[@]} -gt 0 ]]; then
                    printf '%s\n' "${files[@]}" | sort -u | jq -R . | jq -s .
                else
                    echo "[]"
                fi
                return 0
            fi
        fi
    fi

    # Remove duplicates and print as JSON array
    if [[ ${#files[@]} -gt 0 ]]; then
        printf '%s\n' "${files[@]}" | sort -u | jq -R . | jq -s .
    else
        echo "[]"
    fi
}

# Get recent commits
get_recent_commits() {
    local commits=()

    if git rev-parse --git-dir > /dev/null 2>&1; then
        # Get last 5 commits on current branch
        while IFS= read -r commit; do
            [[ -n "$commit" ]] && commits+=("$commit")
        done < <(git log -5 --pretty=format:"%H" 2>/dev/null || true)
    fi

    # Print as JSON array
    if [[ ${#commits[@]} -gt 0 ]]; then
        printf '%s\n' "${commits[@]}" | jq -R . | jq -s .
    else
        echo "[]"
    fi
}

# Escape JSON string
json_escape() {
    echo -n "$1" | jq -Rs .
}

# Main logging function
log_activity() {
    local description="$1"
    local activity_type="${2:-task_completed}"
    local context="${3:-}"
    local tags="${4:-}"

    init_dirs

    local session_id
    session_id=$(get_session_id)

    local timestamp
    timestamp=$(date -u +"%Y-%m-%dT%H:%M:%SZ")

    # Get project info
    local project_info
    project_info=$(get_project_info)
    IFS='|' read -r project_path project_name git_branch git_remote <<< "$project_info"

    # Get files and commits
    local files_json
    files_json=$(get_changed_files)

    local commits_json
    commits_json=$(get_recent_commits)

    # Parse tags into JSON array
    local tags_json="[]"
    if [[ -n "$tags" ]]; then
        IFS=',' read -ra tag_array <<< "$tags"
        # Trim whitespace from each tag
        for i in "${!tag_array[@]}"; do
            tag_array[$i]=$(echo "${tag_array[$i]}" | xargs)
        done
        tags_json=$(printf '%s\n' "${tag_array[@]}" | jq -R . | jq -s .)
    fi

    # Create activity record
    local activity_file="$ACTIVITIES_DIR/${session_id}_${timestamp//[:]/}.json"

    # Build JSON structure
    cat > "$activity_file" <<EOF
{
  "session_id": $(json_escape "$session_id"),
  "timestamp": $(json_escape "$timestamp"),
  "project_path": $(json_escape "$project_path"),
  "project_name": $(json_escape "$project_name"),
  "git_branch": $(json_escape "$git_branch"),
  "git_remote": $(json_escape "$git_remote"),
  "activities": [
    {
      "type": $(json_escape "$activity_type"),
      "description": $(json_escape "$description"),
      "files_changed": $files_json,
      "commits": $commits_json
    }
  ],
  "context": $(json_escape "$context"),
  "tags": $tags_json
}
EOF

    # Validate JSON
    if ! jq empty "$activity_file" 2>/dev/null; then
        log_error "Failed to create valid JSON"
        rm -f "$activity_file"
        return 1
    fi

    log_info "Activity logged successfully"
    echo "$activity_file"
}

# Parse command line arguments
main() {
    # Check dependencies first
    check_dependencies

    local description=""
    local activity_type="task_completed"
    local context=""
    local tags=""

    while [[ $# -gt 0 ]]; do
        case $1 in
            -d|--description)
                if [[ $# -lt 2 ]] || [[ -z "${2:-}" ]]; then
                    log_error "Missing value for $1"
                    exit 1
                fi
                description="$2"
                shift 2
                ;;
            -t|--type)
                if [[ $# -lt 2 ]] || [[ -z "${2:-}" ]]; then
                    log_error "Missing value for $1"
                    exit 1
                fi
                activity_type="$2"
                shift 2
                ;;
            -c|--context)
                if [[ $# -lt 2 ]] || [[ -z "${2:-}" ]]; then
                    log_error "Missing value for $1"
                    exit 1
                fi
                context="$2"
                shift 2
                ;;
            --tags)
                if [[ $# -lt 2 ]] || [[ -z "${2:-}" ]]; then
                    log_error "Missing value for $1"
                    exit 1
                fi
                tags="$2"
                shift 2
                ;;
            -h|--help)
                cat <<HELP
Usage: log_activity.sh [OPTIONS]

Options:
  -d, --description TEXT   Activity description (required)
  -t, --type TEXT         Activity type (default: task_completed)
                          Types: task_completed, bug_fixed, refactoring,
                                research, documentation, review
  -c, --context TEXT      Additional context
  --tags TEXT             Comma-separated tags
  -h, --help              Show this help message

Environment Variables:
  CLAUDE_ACTIVITIES_DIR   Override activities directory (default: ~/.claude/activities)
  CLAUDE_SESSION_ID       Use custom session ID

Examples:
  log_activity.sh -d "Implemented OAuth2 login"
  log_activity.sh -d "Fixed memory leak" -t bug_fixed --tags "performance,bug"
  log_activity.sh -d "Refactored auth module" -t refactoring -c "Improved testability"
HELP
                exit 0
                ;;
            *)
                log_error "Unknown option: $1"
                echo "Use -h or --help for usage information"
                exit 1
                ;;
        esac
    done

    # Check required arguments
    if [[ -z "$description" ]]; then
        log_error "Description is required"
        echo "Use -h or --help for usage information"
        exit 1
    fi

    log_activity "$description" "$activity_type" "$context" "$tags"
}

# Run main function
main "$@"
