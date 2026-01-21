#!/bin/bash
set -euo pipefail

############################
# Configuration
############################

OUTPUT_FILE="${TMPDIR:-/tmp}/code_story_result.txt"
MAX_COMMITS=20  # Limit commits to avoid context overflow
MAX_ANALYSIS_DEPTH=10  # Number of commits to analyze in detail
MAX_DIFF_LINES=30  # Lines to show per commit diff

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

if ! git rev-parse --is-inside-work-tree >/dev/null 2>&1; then
  echo "Error: Not inside a git repository." >&2
  exit 1
fi

############################
# Parse arguments
############################

FILE_PATH="${1:-}"

if [[ -z "$FILE_PATH" ]]; then
  echo "Error: No file path provided." >&2
  echo "Usage: $0 <file-path>" >&2
  echo "Example: $0 src/api/auth.js" >&2
  exit 1
fi

if [[ ! -f "$FILE_PATH" ]]; then
  echo "Error: File '$FILE_PATH' does not exist." >&2
  exit 1
fi

############################
# Collect git history
############################

echo "================ Code Story Analysis ================"
echo "File: $FILE_PATH"
echo "===================================================="
echo

# Check if file is tracked by git
if ! git ls-files --error-unmatch "$FILE_PATH" >/dev/null 2>&1; then
  echo "Error: File '$FILE_PATH' is not tracked by git." >&2
  exit 1
fi

# Get file history
HISTORY_FILE=$(mktemp)
echo "Collecting git history..."

# Get commit history with detailed information
git log --follow --format="%H|%an|%ae|%ad|%s" --date=short -n "$MAX_COMMITS" -- "$FILE_PATH" > "$HISTORY_FILE"

COMMIT_COUNT=$(wc -l < "$HISTORY_FILE" | tr -d ' ')

if [[ "$COMMIT_COUNT" -eq 0 ]]; then
  echo "Error: No commit history found for '$FILE_PATH'." >&2
  exit 1
fi

echo "Found $COMMIT_COUNT commits"
echo

############################
# Collect detailed changes
############################

CHANGES_FILE=$(mktemp)
echo "Analyzing changes..."

# Process each commit (limit to prevent context overflow)
COMMITS_TO_ANALYZE=$(head -n "$MAX_ANALYSIS_DEPTH" "$HISTORY_FILE")

while IFS='|' read -r hash author email date subject; do
  echo "----------------------------------------" >> "$CHANGES_FILE"
  echo "Commit: $hash" >> "$CHANGES_FILE"
  echo "Author: $author <$email>" >> "$CHANGES_FILE"
  echo "Date: $date" >> "$CHANGES_FILE"
  echo "Message: $subject" >> "$CHANGES_FILE"
  echo "" >> "$CHANGES_FILE"

  # Get the actual changes (limit output to avoid huge diffs)
  echo "Changes:" >> "$CHANGES_FILE"
  git show --format="" --stat "$hash" -- "$FILE_PATH" 2>/dev/null | head -n 5 >> "$CHANGES_FILE" || true
  echo "" >> "$CHANGES_FILE"

  # Get a snippet of the actual diff
  git show --format="" "$hash" -- "$FILE_PATH" 2>/dev/null | head -n "$MAX_DIFF_LINES" >> "$CHANGES_FILE" || true
  echo "" >> "$CHANGES_FILE"

done <<< "$COMMITS_TO_ANALYZE"

# Get current file statistics
echo "----------------------------------------" >> "$CHANGES_FILE"
echo "Current File Statistics:" >> "$CHANGES_FILE"
wc -l "$FILE_PATH" | awk '{print "Lines: " $1}' >> "$CHANGES_FILE"
echo "" >> "$CHANGES_FILE"

############################
# Get current file content (summary)
############################

CURRENT_CONTENT=$(mktemp)
echo "Current file structure:" > "$CURRENT_CONTENT"
# Get file outline (functions, classes, etc.)
if [[ "$FILE_PATH" =~ \.(js|ts|jsx|tsx)$ ]]; then
  grep -n "^function\|^const.*=.*function\|^class\|^export" "$FILE_PATH" | head -n 20 >> "$CURRENT_CONTENT" 2>/dev/null || echo "  (no functions/classes found)" >> "$CURRENT_CONTENT"
elif [[ "$FILE_PATH" =~ \.(py)$ ]]; then
  grep -n "^def\|^class" "$FILE_PATH" | head -n 20 >> "$CURRENT_CONTENT" 2>/dev/null || echo "  (no functions/classes found)" >> "$CURRENT_CONTENT"
elif [[ "$FILE_PATH" =~ \.(go)$ ]]; then
  grep -n "^func\|^type.*struct" "$FILE_PATH" | head -n 20 >> "$CURRENT_CONTENT" 2>/dev/null || echo "  (no functions/types found)" >> "$CURRENT_CONTENT"
else
  head -n 50 "$FILE_PATH" >> "$CURRENT_CONTENT"
fi

############################
# Generate story with Gemini
############################

echo "Generating code story..."

PROMPT_FILE=$(mktemp)

# Build prompt in sections to avoid variable expansion issues
cat > "$PROMPT_FILE" <<EOF
You are a senior software engineer and technical storyteller. Your task is to analyze the git history of a file and tell its story in an engaging, informative way.

File: $FILE_PATH
Total commits in history: $COMMIT_COUNT
Commits analyzed: $(echo "$COMMITS_TO_ANALYZE" | wc -l | tr -d ' ')

Here is the git history and changes:
EOF

cat "$CHANGES_FILE" >> "$PROMPT_FILE"

cat >> "$PROMPT_FILE" <<EOF

Current file structure:
EOF

cat "$CURRENT_CONTENT" >> "$PROMPT_FILE"

cat >> "$PROMPT_FILE" <<'EOF'

Please write a comprehensive "Code Story" that includes:

1. **Origin Story** (1-2 paragraphs)
   - When and why was this file created?
   - What was the original purpose?
   - Who was the original author?

2. **Evolution Timeline** (chronological)
   - Major milestones and turning points
   - Significant refactorings or redesigns
   - Key features added over time
   - Format each milestone as: "📅 YYYY-MM-DD: Brief description"

3. **Design Decisions** (bullet points)
   - What important architectural or design choices were made?
   - Why were they made (if evident from commits)?
   - What trade-offs were considered?

4. **Current State** (1 paragraph)
   - What is the file's current purpose and structure?
   - How has it evolved from its origins?

5. **Insights & Patterns** (bullet points)
   - What patterns emerge from the history?
   - Are there recurring themes (e.g., bug fixes, performance improvements)?
   - What does this tell us about the codebase's evolution?

6. **Notable Contributors**
   - List main contributors and their impact
   - Format: "Author Name - X commits, focus area"

Write in a clear, engaging narrative style. Use metaphors and storytelling techniques to make the technical history interesting. Focus on the "why" behind changes, not just the "what".

Use Traditional Chinese for the narrative, but keep code elements, dates, and technical terms in English.
EOF

if ! gemini < "$PROMPT_FILE" > "$OUTPUT_FILE"; then
  echo "Error: Failed to generate story from Gemini API." >&2
  echo "Check your API key and network connection." >&2
  exit 1
fi

# Cleanup
rm -f "$HISTORY_FILE" "$CHANGES_FILE" "$PROMPT_FILE" "$CURRENT_CONTENT"

############################
# Display result
############################

echo ""
echo "================ Code Story ================"
cat "$OUTPUT_FILE"
echo ""
echo "============================================"
echo ""
echo "Story saved to: $OUTPUT_FILE"
