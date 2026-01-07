#!/bin/bash

# =============================================================================
# Code Review with Gemini CLI
# A robust script to perform code reviews using the Gemini CLI
# =============================================================================

set -o pipefail

# Configuration
MAX_DIFF_LINES=${MAX_DIFF_LINES:-5000}  # Maximum lines to send to Gemini
GEMINI_MODEL=${GEMINI_MODEL:-"gemini-3-pro"}  # Default model
OUTPUT_FILE="${TMPDIR:-/tmp}/gemini_review_result.txt"

# Color codes for output (only if terminal supports it)
if [ -t 2 ]; then
  RED='\033[0;31m'
  YELLOW='\033[1;33m'
  GREEN='\033[0;32m'
  NC='\033[0m' # No Color
else
  RED=''
  YELLOW=''
  GREEN=''
  NC=''
fi

# Logging functions
log_info() { echo -e "${GREEN}[INFO]${NC} $1" >&2; }
log_warn() { echo -e "${YELLOW}[WARN]${NC} $1" >&2; }
log_error() { echo -e "${RED}[ERROR]${NC} $1" >&2; }

# Cleanup function
cleanup() {
  [ -f "$DIFF_FILE" ] && rm -f "$DIFF_FILE"
  [ -f "$PROMPT_FILE" ] && rm -f "$PROMPT_FILE"
}
trap cleanup EXIT

# =============================================================================
# Pre-flight checks
# =============================================================================

# Check if we're in a git repository
check_git_repo() {
  if ! git rev-parse --is-inside-work-tree >/dev/null 2>&1; then
    log_error "Not inside a git repository."
    log_error "Please run this script from within a git repository."
    exit 1
  fi
}

# Check if gemini CLI is installed
check_gemini_cli() {
  if ! command -v gemini >/dev/null 2>&1; then
    log_error "Gemini CLI is not installed or not in PATH."
    log_error "Install it with: npm install -g @google/gemini-cli"
    exit 1
  fi
}

# Check if there are any commits
check_commits_exist() {
  if ! git rev-parse HEAD >/dev/null 2>&1; then
    log_error "No commits found in this repository."
    log_error "Please make at least one commit before running code review."
    exit 1
  fi
}

# =============================================================================
# Branch detection
# =============================================================================

# Function to detect the default/base branch
detect_base_branch() {
  local branch

  # 1. Check common branch names in order of preference
  for branch in main master develop development trunk; do
    if git rev-parse --verify "$branch" >/dev/null 2>&1; then
      echo "$branch"
      return 0
    fi
  done

  # 2. Try to get the default branch from remote origin
  local remote_branch
  remote_branch=$(git symbolic-ref refs/remotes/origin/HEAD 2>/dev/null | sed 's@^refs/remotes/origin/@@')
  if [ -n "$remote_branch" ] && git rev-parse --verify "$remote_branch" >/dev/null 2>&1; then
    echo "$remote_branch"
    return 0
  fi

  # 3. Try origin/main or origin/master directly
  for branch in origin/main origin/master; do
    if git rev-parse --verify "$branch" >/dev/null 2>&1; then
      echo "$branch"
      return 0
    fi
  done

  # 4. Use the first remote branch found
  local first_remote
  first_remote=$(git branch -r 2>/dev/null | grep -v 'HEAD' | head -n 1 | sed 's/^ *//')
  if [ -n "$first_remote" ]; then
    echo "$first_remote"
    return 0
  fi

  # No base branch found
  return 1
}

# Function to get the merge base between current branch and base branch
get_merge_base() {
  local base_branch="$1"
  local merge_base

  # Try three-dot syntax first (commits since branch diverged)
  merge_base=$(git merge-base "$base_branch" HEAD 2>/dev/null)
  if [ -n "$merge_base" ]; then
    echo "$merge_base"
    return 0
  fi

  return 1
}

# =============================================================================
# Diff generation
# =============================================================================

generate_diff() {
  local diff_file="$1"
  local base_branch
  local merge_base
  local current_branch

  current_branch=$(git rev-parse --abbrev-ref HEAD 2>/dev/null || echo "HEAD")

  # Strategy 1: Try to find a base branch and use three-dot diff
  base_branch=$(detect_base_branch)
  if [ -n "$base_branch" ]; then
    log_info "Detected base branch: $base_branch"

    # Check if current branch is the same as base branch
    if [ "$current_branch" = "$base_branch" ]; then
      log_warn "Currently on base branch ($base_branch). Using uncommitted changes."
      git diff HEAD > "$diff_file" 2>/dev/null
      if [ ! -s "$diff_file" ]; then
        # Try staged changes
        git diff --cached > "$diff_file" 2>/dev/null
      fi
      return 0
    fi

    # Try three-dot diff (changes since diverging from base)
    if git diff "$base_branch"...HEAD > "$diff_file" 2>/dev/null && [ -s "$diff_file" ]; then
      log_info "Using diff: $base_branch...HEAD"
      return 0
    fi

    # Try merge-base approach
    merge_base=$(get_merge_base "$base_branch")
    if [ -n "$merge_base" ] && git diff "$merge_base" HEAD > "$diff_file" 2>/dev/null && [ -s "$diff_file" ]; then
      log_info "Using diff from merge-base: ${merge_base:0:8}..HEAD"
      return 0
    fi

    # Try two-dot diff as fallback
    if git diff "$base_branch"..HEAD > "$diff_file" 2>/dev/null && [ -s "$diff_file" ]; then
      log_info "Using diff: $base_branch..HEAD"
      return 0
    fi
  fi

  # Strategy 2: Use uncommitted changes (staged + unstaged)
  log_warn "Could not diff against base branch. Trying uncommitted changes..."
  git diff HEAD > "$diff_file" 2>/dev/null
  if [ -s "$diff_file" ]; then
    log_info "Using uncommitted changes (staged + unstaged)"
    return 0
  fi

  # Strategy 3: Use staged changes only
  git diff --cached > "$diff_file" 2>/dev/null
  if [ -s "$diff_file" ]; then
    log_info "Using staged changes only"
    return 0
  fi

  # Strategy 4: Compare with previous commit
  if git diff HEAD~1 HEAD > "$diff_file" 2>/dev/null && [ -s "$diff_file" ]; then
    log_info "Using diff from last commit: HEAD~1..HEAD"
    return 0
  fi

  # No changes found
  return 1
}

# =============================================================================
# Main execution
# =============================================================================

main() {
  log_info "Starting code review with Gemini..."

  # Run pre-flight checks
  check_git_repo
  check_gemini_cli
  check_commits_exist

  # Create temporary files
  DIFF_FILE=$(mktemp) || { log_error "Failed to create temporary diff file"; exit 1; }
  PROMPT_FILE=$(mktemp) || { log_error "Failed to create temporary prompt file"; exit 1; }

  # Generate diff
  if ! generate_diff "$DIFF_FILE"; then
    log_warn "No changes found to review."
    echo "No changes found to review." > "$OUTPUT_FILE"
    cat "$OUTPUT_FILE"
    exit 0
  fi

  # Check diff size and truncate if necessary
  local diff_lines
  diff_lines=$(wc -l < "$DIFF_FILE" | tr -d ' ')
  if [ "$diff_lines" -gt "$MAX_DIFF_LINES" ]; then
    log_warn "Diff is very large ($diff_lines lines). Truncating to $MAX_DIFF_LINES lines."
    local temp_truncated
    temp_truncated=$(mktemp)
    head -n "$MAX_DIFF_LINES" "$DIFF_FILE" > "$temp_truncated"
    echo "" >> "$temp_truncated"
    echo "... [TRUNCATED: $(( diff_lines - MAX_DIFF_LINES )) more lines] ..." >> "$temp_truncated"
    mv "$temp_truncated" "$DIFF_FILE"
  fi

  log_info "Diff contains $diff_lines lines"

  # Create prompt file
  cat > "$PROMPT_FILE" << 'EOF'
Perform a detailed code review on the following diff. Focus on:
- Correctness and potential bugs
- Security vulnerabilities
- Code readability and maintainability
- Best practices
- Performance considerations

Provide a prioritized list of issues with:
1. High priority issues (bugs, security)
2. Medium priority issues (code quality, best practices)
3. Low priority issues (style, minor improvements)

For each issue, suggest specific fixes.

Here is the diff to review:

EOF

  cat "$DIFF_FILE" >> "$PROMPT_FILE"

  # Run Gemini CLI
  log_info "Calling Gemini CLI with model: $GEMINI_MODEL"

  local gemini_exit_code
  if gemini -m "$GEMINI_MODEL" < "$PROMPT_FILE" > "$OUTPUT_FILE" 2>&1; then
    gemini_exit_code=0
  else
    gemini_exit_code=$?
  fi

  # Check if Gemini produced output
  if [ ! -s "$OUTPUT_FILE" ]; then
    log_error "Gemini CLI produced no output (exit code: $gemini_exit_code)"
    echo "Error: Gemini CLI failed to produce output. Exit code: $gemini_exit_code" > "$OUTPUT_FILE"
    cat "$OUTPUT_FILE"
    exit 1
  fi

  # Check for common error patterns in output
  if grep -qi "error\|unauthorized\|authentication\|quota" "$OUTPUT_FILE" 2>/dev/null; then
    if ! grep -qi "review\|issue\|suggestion\|fix" "$OUTPUT_FILE" 2>/dev/null; then
      log_warn "Gemini output may contain errors. Please check the result."
    fi
  fi

  log_info "Code review complete. Results saved to $OUTPUT_FILE"

  # Output to stdout
  cat "$OUTPUT_FILE"
}

# Run main function
main "$@"
