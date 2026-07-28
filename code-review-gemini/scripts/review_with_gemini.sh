#!/bin/bash
set -euo pipefail

echo "code-review-gemini is retired; no diff was sent to Gemini." >&2
echo "Use code-review-claude in Claude Code or code-review-codex in Codex." >&2
exit 1

############################
# Configuration
############################

REVIEW_OUTPUT="${TMPDIR:-/tmp}/gemini_review_result.txt"

############################
# Usage
############################

usage() {
  cat <<EOF
Usage: $(basename "$0") [MODE] [ARGS...]

Modes:
  --staged              Review staged changes (default)
  --unstaged            Review unstaged working directory changes
  --files FILE...       Review specific files (works for untracked files)
  --branch BASE         Review diff of HEAD vs BASE branch
  --commit SHA          Review a specific commit
  --auto                Auto-detect: staged > unstaged > error (default when no mode given)

Examples:
  $(basename "$0")                          # auto-detect
  $(basename "$0") --staged                 # staged changes only
  $(basename "$0") --unstaged               # unstaged changes only
  $(basename "$0") --files foo.py bar.js    # specific files (git-tracked or not)
  $(basename "$0") --branch main            # diff HEAD vs main
  $(basename "$0") --commit abc1234         # single commit
EOF
  exit 0
}

############################
# Pre-flight checks
############################

if ! command -v gemini >/dev/null 2>&1; then
  echo "Error: 'gemini' CLI is not installed." >&2
  echo "Install it with: npm install -g @google/gemini-cli" >&2
  exit 1
fi

############################
# Parse arguments
############################

MODE=""
MODE_ARGS=()

if [[ $# -eq 0 ]]; then
  MODE="auto"
else
  case "$1" in
    --staged)   MODE="staged" ;;
    --unstaged) MODE="unstaged" ;;
    --files)    MODE="files"; shift; MODE_ARGS=("$@") ;;
    --branch)   MODE="branch"; shift; MODE_ARGS=("${1:-}") ;;
    --commit)   MODE="commit"; shift; MODE_ARGS=("${1:-}") ;;
    --auto)     MODE="auto" ;;
    --help|-h)  usage ;;
    *)
      # Treat bare args as files
      MODE="files"
      MODE_ARGS=("$@")
      ;;
  esac
fi

############################
# Detect current branch
############################

CURRENT_BRANCH="(not a git repo)"
IS_GIT_REPO=false
if git rev-parse --is-inside-work-tree >/dev/null 2>&1; then
  CURRENT_BRANCH=$(git rev-parse --abbrev-ref HEAD)
  IS_GIT_REPO=true
fi

############################
# Auto-detect mode
############################

if [[ "$MODE" == "auto" ]]; then
  if [[ "$IS_GIT_REPO" == false ]]; then
    echo "Error: Not in a git repository. Use --files to review specific files." >&2
    exit 1
  fi
  if [[ -n "$(git diff --cached --name-only 2>/dev/null)" ]]; then
    MODE="staged"
  elif [[ -n "$(git diff --name-only 2>/dev/null)" ]]; then
    MODE="unstaged"
  else
    echo "No staged or unstaged changes detected." >&2
    echo "Use --files, --branch, or --commit to specify review scope." >&2
    exit 0
  fi
fi

############################
# Collect review content
############################

DIFF_CONTENT=""
REVIEW_TARGET=""
FILE_LIST=""

case "$MODE" in
  staged)
    if [[ "$IS_GIT_REPO" == false ]]; then
      echo "Error: --staged requires a git repository." >&2; exit 1
    fi
    FILE_LIST=$(git diff --cached --name-only)
    if [[ -z "$FILE_LIST" ]]; then
      echo "No staged changes found. Use 'git add' to stage files first." >&2; exit 0
    fi
    DIFF_CONTENT=$(git diff --cached)
    REVIEW_TARGET="Staged changes"
    ;;

  unstaged)
    if [[ "$IS_GIT_REPO" == false ]]; then
      echo "Error: --unstaged requires a git repository." >&2; exit 1
    fi
    FILE_LIST=$(git diff --name-only)
    if [[ -z "$FILE_LIST" ]]; then
      echo "No unstaged changes found." >&2; exit 0
    fi
    DIFF_CONTENT=$(git diff)
    REVIEW_TARGET="Unstaged changes"
    ;;

  files)
    if [[ ${#MODE_ARGS[@]} -eq 0 ]]; then
      echo "Error: --files requires at least one file path." >&2; exit 1
    fi
    REVIEW_TARGET="Specific files"
    FILE_CONTENTS=""
    for f in "${MODE_ARGS[@]}"; do
      if [[ ! -f "$f" ]]; then
        echo "Warning: File not found: $f (skipping)" >&2
        continue
      fi
      FILE_LIST="${FILE_LIST:+$FILE_LIST
}$f"
      FILE_CONTENTS="${FILE_CONTENTS}
===== File: $f =====
$(cat "$f")
"
    done
    if [[ -z "$FILE_LIST" ]]; then
      echo "Error: No valid files to review." >&2; exit 1
    fi
    DIFF_CONTENT="$FILE_CONTENTS"
    ;;

  branch)
    if [[ "$IS_GIT_REPO" == false ]]; then
      echo "Error: --branch requires a git repository." >&2; exit 1
    fi
    BASE="${MODE_ARGS[0]:-}"
    if [[ -z "$BASE" ]]; then
      echo "Error: --branch requires a base branch name." >&2; exit 1
    fi
    if ! git rev-parse --verify "$BASE" >/dev/null 2>&1; then
      echo "Error: Branch '$BASE' not found." >&2; exit 1
    fi
    FILE_LIST=$(git diff "${BASE}...HEAD" --name-only)
    if [[ -z "$FILE_LIST" ]]; then
      echo "No differences found between $BASE and HEAD." >&2; exit 0
    fi
    DIFF_CONTENT=$(git diff "${BASE}...HEAD")
    REVIEW_TARGET="Changes: $BASE...HEAD"
    ;;

  commit)
    if [[ "$IS_GIT_REPO" == false ]]; then
      echo "Error: --commit requires a git repository." >&2; exit 1
    fi
    SHA="${MODE_ARGS[0]:-}"
    if [[ -z "$SHA" ]]; then
      echo "Error: --commit requires a commit SHA." >&2; exit 1
    fi
    if ! git rev-parse --verify "$SHA" >/dev/null 2>&1; then
      echo "Error: Commit '$SHA' not found." >&2; exit 1
    fi
    FILE_LIST=$(git diff-tree --no-commit-id --name-only -r "$SHA")
    DIFF_CONTENT=$(git show "$SHA" --format="" -p)
    REVIEW_TARGET="Commit $SHA"
    ;;
esac

############################
# Preview review scope
############################

echo "================ Review Scope ================"
echo "Branch        : $CURRENT_BRANCH"
echo "Review target : $REVIEW_TARGET"
echo
echo "Files         :"
if [[ -z "$FILE_LIST" ]]; then
  echo "  (none)"
else
  echo "$FILE_LIST" | sed 's/^/  - /'
fi
echo "=============================================="
echo

############################
# Run Gemini review
############################

PROMPT_FILE=$(mktemp)

if [[ "$MODE" == "files" ]]; then
  cat > "$PROMPT_FILE" <<EOF
You are reviewing specific files on branch $CURRENT_BRANCH.
Perform a detailed code review on the following file contents. Focus on correctness, security, readability, best practices, and provide a prioritized list of issues and suggested fixes.

$DIFF_CONTENT
EOF
else
  cat > "$PROMPT_FILE" <<EOF
You are reviewing changes on branch $CURRENT_BRANCH.
Review target: $REVIEW_TARGET
Perform a detailed code review on the following diff. Focus on correctness, security, readability, best practices, and provide a prioritized list of issues and suggested fixes.

Here is the diff:
$DIFF_CONTENT
EOF
fi

gemini < "$PROMPT_FILE" > "$REVIEW_OUTPUT"

# Cleanup
rm -f "$PROMPT_FILE"

############################
# Output result
############################

cat "$REVIEW_OUTPUT"
