#!/bin/bash
set -euo pipefail

############################
# Configuration
############################

DEFAULT_BASE_BRANCH="main"
REVIEW_OUTPUT="gemini_review_result.txt"

############################
# Detect current branch
############################

CURRENT_BRANCH=$(git rev-parse --abbrev-ref HEAD)
HEAD_COMMIT=$(git rev-parse --short HEAD)

############################
# Determine base commit
############################

if [[ "$CURRENT_BRANCH" != "$DEFAULT_BASE_BRANCH" ]]; then
  BASE_COMMIT=$(git merge-base "$DEFAULT_BASE_BRANCH" HEAD)
else
  # Check if HEAD~1 exists (not the first commit)
  if git rev-parse --verify HEAD~1 >/dev/null 2>&1; then
    BASE_COMMIT=$(git rev-parse HEAD~1)
  else
    # First commit: use git's empty tree hash
    BASE_COMMIT=$(git hash-object -t tree /dev/null)
  fi
fi

BASE_COMMIT_SHORT=$(git rev-parse --short "$BASE_COMMIT" 2>/dev/null || echo "initial")

############################
# Collect changed files
############################

CHANGED_FILES=$(git diff --name-only "$BASE_COMMIT"...HEAD)

############################
# Preview review scope
############################

echo "================ Review Scope ================"
echo "Branch        : $CURRENT_BRANCH"
echo "Base commit   : $BASE_COMMIT_SHORT"
echo "Head commit   : $HEAD_COMMIT"
echo
echo "Changed files :"
if [[ -z "$CHANGED_FILES" ]]; then
  echo "  (none)"
else
  echo "$CHANGED_FILES" | sed 's/^/  - /'
fi
echo "=============================================="
echo

if [[ -z "$CHANGED_FILES" ]]; then
  echo "No changes detected. Skipping code review."
  exit 0
fi

############################
# Generate diff
############################

DIFF_FILE=$(mktemp)
git diff "$BASE_COMMIT"...HEAD > "$DIFF_FILE"

############################
# Run Gemini review
############################

REVIEW_PROMPT="You are reviewing changes from commit $BASE_COMMIT_SHORT to $HEAD_COMMIT on branch $CURRENT_BRANCH.
Perform a detailed code review on the following diff. Focus on correctness, security, readability, best practices, and provide a prioritized list of issues and suggested fixes.

Here is the diff:
$(cat "$DIFF_FILE")"

gemini "$REVIEW_PROMPT" > "$REVIEW_OUTPUT"

############################
# Output result
############################

cat "$REVIEW_OUTPUT"
