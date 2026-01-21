#!/bin/bash
set -euo pipefail

############################
# Configuration
############################

OUTPUT_FILE="${TMPDIR:-/tmp}/commit_msg_result.txt"

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
# Collect staged changes
############################

STAGED_FILES=$(git diff --cached --name-only)

if [[ -z "$STAGED_FILES" ]]; then
  echo "Error: No staged changes found." >&2
  echo "Please stage your changes first: git add <files>" >&2
  exit 1
fi

############################
# Get current branch
############################

CURRENT_BRANCH=$(git rev-parse --abbrev-ref HEAD)

############################
# Generate diff
############################

DIFF_FILE=$(mktemp)
git diff --cached --stat > "$DIFF_FILE"
echo "" >> "$DIFF_FILE"

# Limit diff size to avoid exceeding model context limits
# Exclude large generated files
git diff --cached -- . ':!package-lock.json' ':!yarn.lock' ':!pnpm-lock.yaml' ':!Gemfile.lock' | head -n 2000 >> "$DIFF_FILE"

############################
# Generate commit message
############################

PROMPT_FILE=$(mktemp)
cat > "$PROMPT_FILE" <<EOF
You are a git commit message expert. Generate a high-quality commit message following the Conventional Commits specification.

Guidelines:
1. Format: <type>(<scope>): <subject>

   <body>

   Co-Authored-By: Gemini AI <noreply@google.com>

   IMPORTANT: The Co-Authored-By line must have exactly this format with NO SPACES in the email.

2. Types:
   - feat: New feature
   - fix: Bug fix
   - docs: Documentation changes
   - style: Code style changes (formatting, no logic change)
   - refactor: Code refactoring
   - perf: Performance improvements
   - test: Adding or updating tests
   - chore: Maintenance tasks, dependencies, configs
   - ci: CI/CD changes
   - build: Build system changes

3. Scope: Optional, component or module name (e.g., api, ui, auth, db)

4. Subject:
   - Use imperative mood ("add" not "added" or "adds")
   - No period at the end
   - Maximum 50 characters
   - Start with lowercase

5. Body (optional):
   - Wrap at 72 characters
   - Explain WHAT and WHY, not HOW
   - Use bullet points for multiple changes
   - Leave blank line between subject and body

6. Language preference:
   - Subject and Body: English (unless code comments are primarily in another language)

Current branch: $CURRENT_BRANCH

Staged changes:
$(cat "$DIFF_FILE")

Please generate a commit message that:
- Accurately describes the changes
- Follows conventional commits format strictly
- Is concise but informative
- Uses appropriate type and scope

Return ONLY the commit message, no explanations or additional text.
EOF

gemini < "$PROMPT_FILE" > "$OUTPUT_FILE"

# Cleanup
rm -f "$DIFF_FILE" "$PROMPT_FILE"

############################
# Display result
############################

echo "================ Generated Commit Message ================"
cat "$OUTPUT_FILE"
echo ""
echo "=========================================================="
echo ""
echo "To use this message:"
echo "  git commit -F $OUTPUT_FILE"
echo ""
echo "Or copy and edit it manually."
