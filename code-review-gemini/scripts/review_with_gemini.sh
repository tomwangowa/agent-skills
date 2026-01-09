#!/bin/bash
set -euo pipefail

############################
# Configuration
############################

REVIEW_OUTPUT="${TMPDIR:-/tmp}/gemini_review_result.txt"

############################
# Pre-flight checks
############################

if ! command -v gemini >/dev/null 2>&1; then
  echo "Error: 'gemini' CLI is not installed." >&2
  echo "Install it with: npm install -g @google/gemini-cli" >&2
  exit 1
fi

############################
# Detect current branch
############################

CURRENT_BRANCH=$(git rev-parse --abbrev-ref HEAD)

############################
# Collect staged files
############################

STAGED_FILES=$(git diff --cached --name-only)

############################
# Preview review scope
############################

echo "================ Review Scope ================"
echo "Branch        : $CURRENT_BRANCH"
echo "Review target : Staged changes"
echo
echo "Staged files  :"
if [[ -z "$STAGED_FILES" ]]; then
  echo "  (none)"
else
  echo "$STAGED_FILES" | sed 's/^/  - /'
fi
echo "=============================================="
echo

if [[ -z "$STAGED_FILES" ]]; then
  echo "No staged changes detected. Skipping code review."
  exit 0
fi

############################
# Generate diff
############################

DIFF_FILE=$(mktemp)
git diff --cached > "$DIFF_FILE"

############################
# Run Gemini review
############################

PROMPT_FILE=$(mktemp)
cat > "$PROMPT_FILE" <<EOF
You are reviewing staged changes on branch $CURRENT_BRANCH.
Perform a detailed code review on the following diff. Focus on correctness, security, readability, best practices, and provide a prioritized list of issues and suggested fixes.

Here is the diff:
$(cat "$DIFF_FILE")
EOF

gemini < "$PROMPT_FILE" > "$REVIEW_OUTPUT"

# Cleanup
rm -f "$DIFF_FILE" "$PROMPT_FILE"

############################
# Output result
############################

cat "$REVIEW_OUTPUT"
