#!/bin/bash
set -euo pipefail

############################
# Configuration
############################

OUTPUT_FILE="${TMPDIR:-/tmp}/pr_review_result.txt"
MAX_DIFF_LINES=2000  # Limit diff size to avoid context overflow

############################
# Pre-flight checks
############################

if ! command -v gemini >/dev/null 2>&1; then
  echo "Error: 'gemini' CLI is not installed." >&2
  echo "Install it with: npm install -g @google/gemini-cli" >&2
  exit 1
fi

if [[ -z "${GEMINI_API_KEY:-}" ]]; then
  echo "Error: GEMINI_API_KEY environment variable is not set." >&2
  echo "Get your API key from: https://aistudio.google.com/app/apikey" >&2
  exit 1
fi

if ! command -v gh >/dev/null 2>&1; then
  echo "Error: GitHub CLI 'gh' is not installed." >&2
  echo "Install it from: https://cli.github.com/" >&2
  exit 1
fi

if ! command -v jq >/dev/null 2>&1; then
  echo "Error: 'jq' is not installed." >&2
  echo "Install it via your package manager (brew install jq, apt-get install jq, etc.)." >&2
  exit 1
fi

if ! git rev-parse --is-inside-work-tree >/dev/null 2>&1; then
  echo "Error: Not inside a git repository." >&2
  exit 1
fi

############################
# Cleanup handler
############################

# Create temp files
PR_INFO_FILE=$(mktemp)
DIFF_FILE=$(mktemp)
PROMPT_FILE=$(mktemp)

# Ensure cleanup on exit
cleanup() {
  rm -f "$PR_INFO_FILE" "$DIFF_FILE" "$PROMPT_FILE"
}
trap cleanup EXIT

############################
# Parse arguments
############################

PR_IDENTIFIER="${1:-}"

if [[ -z "$PR_IDENTIFIER" ]]; then
  echo "Error: No PR identifier provided." >&2
  echo "Usage: $0 <PR-number|PR-URL>" >&2
  echo "Examples:" >&2
  echo "  $0 123" >&2
  echo "  $0 https://github.com/owner/repo/pull/123" >&2
  exit 1
fi

# Extract PR number from URL if provided
if [[ "$PR_IDENTIFIER" =~ ^https?:// ]]; then
  PR_NUMBER=$(echo "$PR_IDENTIFIER" | grep -oE '[0-9]+$' || echo "")
  if [[ -z "$PR_NUMBER" ]]; then
    echo "Error: Could not extract PR number from URL: $PR_IDENTIFIER" >&2
    exit 1
  fi
else
  PR_NUMBER="$PR_IDENTIFIER"
fi

############################
# Fetch PR information
############################

echo "================ PR Review Analysis ================"
echo "Fetching PR #$PR_NUMBER information..."
echo

# Get PR details
if ! gh pr view "$PR_NUMBER" --json title,body,author,headRefName,baseRefName,additions,deletions,files > "$PR_INFO_FILE" 2>&1; then
  echo "Error: Failed to fetch PR #$PR_NUMBER" >&2
  echo "Make sure you have access to this repository and the PR exists." >&2
  exit 1
fi

# Parse PR info
PR_TITLE=$(jq -r '.title' "$PR_INFO_FILE")
PR_AUTHOR=$(jq -r '.author.login' "$PR_INFO_FILE")
PR_HEAD=$(jq -r '.headRefName' "$PR_INFO_FILE")
PR_BASE=$(jq -r '.baseRefName' "$PR_INFO_FILE")
PR_ADDITIONS=$(jq -r '.additions' "$PR_INFO_FILE")
PR_DELETIONS=$(jq -r '.deletions' "$PR_INFO_FILE")
FILE_COUNT=$(jq -r '.files | length' "$PR_INFO_FILE")

echo "Title: $PR_TITLE"
echo "Author: @$PR_AUTHOR"
echo "Branch: $PR_HEAD → $PR_BASE"
echo "Changes: +$PR_ADDITIONS -$PR_DELETIONS lines ($FILE_COUNT files)"
echo "======================================================"
echo

# Get changed files list
CHANGED_FILES=$(jq -r '.files[].path' "$PR_INFO_FILE")
echo "Changed files:"
echo "$CHANGED_FILES" | sed 's/^/  - /'
echo

############################
# Get PR diff
############################

echo "Fetching PR diff..."

if ! gh pr diff "$PR_NUMBER" > "$DIFF_FILE" 2>&1; then
  echo "Error: Failed to fetch PR diff" >&2
  exit 1
fi

# Check diff size and truncate if needed
DIFF_LINES=$(wc -l < "$DIFF_FILE" | tr -d ' ')
if [[ "$DIFF_LINES" -gt "$MAX_DIFF_LINES" ]]; then
  echo "Warning: Diff is large ($DIFF_LINES lines). Truncating to $MAX_DIFF_LINES lines for analysis." >&2
  TRUNCATED_DIFF=$(mktemp)
  head -n "$MAX_DIFF_LINES" "$DIFF_FILE" > "$TRUNCATED_DIFF"
  echo "" >> "$TRUNCATED_DIFF"
  echo "... [TRUNCATED: $((DIFF_LINES - MAX_DIFF_LINES)) more lines not shown] ..." >> "$TRUNCATED_DIFF"
  mv "$TRUNCATED_DIFF" "$DIFF_FILE"
fi

echo "Diff size: $DIFF_LINES lines"
echo

############################
# Generate review with Gemini
############################

echo "Analyzing PR with AI..."

# Build prompt
cat > "$PROMPT_FILE" <<EOF
You are a senior software engineer performing a thorough code review. You have been asked to review the following pull request.

## PR Information
- Title: $PR_TITLE
- Author: @$PR_AUTHOR
- Branch: $PR_HEAD → $PR_BASE
- Changes: +$PR_ADDITIONS -$PR_DELETIONS lines
- Files changed: $FILE_COUNT

## Changed Files
EOF

echo "$CHANGED_FILES" | sed 's/^/- /' >> "$PROMPT_FILE"

cat >> "$PROMPT_FILE" <<'EOF'

## PR Diff
<diff_content>
EOF

cat "$DIFF_FILE" >> "$PROMPT_FILE"

cat >> "$PROMPT_FILE" <<'EOF'
</diff_content>

## Your Task

Perform a comprehensive code review focusing on:

1. **Correctness & Logic**
   - Bugs or logic errors
   - Edge cases not handled
   - Potential null/undefined errors
   - Off-by-one errors

2. **Security**
   - SQL injection, XSS, CSRF vulnerabilities
   - Authentication/authorization issues
   - Sensitive data exposure
   - Input validation problems

3. **Performance**
   - Inefficient algorithms (O(n²) where O(n) possible)
   - Database query optimization
   - Memory leaks
   - Unnecessary computations

4. **Code Quality**
   - Readability and maintainability
   - Code smells (long functions, deep nesting, etc.)
   - Naming conventions
   - Code duplication

5. **Best Practices**
   - Error handling
   - Testing coverage
   - Documentation
   - API design
   - Separation of concerns

## Output Format

Provide your review in the following structured format:

### Review Summary
- **Overall Verdict**: [Approve | Request Changes | Comment]
- **Risk Level**: [Low | Medium | High]
- **Files Reviewed**: X files
- **Issues Found**: X total (Y blocking, Z important, W minor)

### 🔴 Blocking Issues
Issues that MUST be fixed before merging (bugs, security vulnerabilities, data loss risks):

1. **[Category] Issue Title** - `filename:line`
   - Description of the problem
   - Why it's blocking
   - Suggested fix

(If none, write "None found")

### 🟡 Important Issues
Issues that should be addressed (design problems, maintainability, performance):

1. **[Category] Issue Title** - `filename:line`
   - Description
   - Impact
   - Suggestion

(If none, write "None found")

### 🟢 Minor Issues & Suggestions
Nice-to-have improvements (style, readability, naming):

1. **[Category] Issue Title** - `filename:line`
   - Suggestion

(If none, write "None found")

### ✅ Positive Observations
Things done well (good practices, clean code, etc.):

- Observation 1
- Observation 2

### 📝 Additional Notes
Any other comments, questions for the author, or context needed.

---

**IMPORTANT Guidelines:**
- Be specific with file names and line numbers when possible
- Prioritize correctly - blocking issues must be actual bugs or security problems
- Be constructive and respectful
- Focus on "what" and "why", not just "what"
- If you suggest a fix, provide concrete code examples
- Use Traditional Chinese for descriptions and explanations
- Keep technical terms, file names, and code in English

Generate your code review now:
EOF

# Use custom model if specified
MODEL_ARGS=""
if [[ -n "${GEMINI_MODEL:-}" ]]; then
  MODEL_ARGS="-m $GEMINI_MODEL"
fi

if ! gemini $MODEL_ARGS < "$PROMPT_FILE" > "$OUTPUT_FILE" 2>&1; then
  echo "Error: Failed to generate review from Gemini API." >&2
  echo "Check your API key and network connection." >&2
  exit 1
fi

# Cleanup happens automatically via trap

############################
# Display result
############################

echo ""
echo "================ PR Review Result ================"
cat "$OUTPUT_FILE"
echo ""
echo "=================================================="
echo ""
echo "Review saved to: $OUTPUT_FILE"
echo ""
echo "To post this review as a comment:"
echo "  gh pr comment $PR_NUMBER --body-file $OUTPUT_FILE"
