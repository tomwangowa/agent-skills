---
name: Code Review with Gemini
description: Perform a code review on staged changes. Use this Skill when the user asks to review staged files, check code quality before committing, or analyze changes about to be committed.
id: tm-code-review-gemini
namespace: tm
domain: code
action: review
qualifier: gemini
version: "1.0.0"
updated: "2026-01-17"
---

# Code Review with Gemini

## Purpose

This Skill performs a structured code review on staged changes by:
1. Collecting the git diff of staged changes (`git diff --cached`)
2. Running an external review script that invokes the Gemini CLI
3. Summarizing the findings in a clear, prioritized manner

The Skill is designed to be deterministic, auditable, and suitable for pre-commit workflows.

---

## Instructions

When the user expresses intent to review staged changes (for example: reviewing staged files, checking code before commit, or analyzing changes about to be committed), follow the steps below strictly.
Please note that do not specify the gemini model in the instructions, as it will be handled in the script.

### Execution steps

1. Run the script `scripts/review_with_gemini.sh`.

2. Observe the script output carefully.
   The script will first print a **"Review Scope"** section that includes:
   - Current branch name
   - Review target (Staged changes)
   - List of staged files

3. Before summarizing the review, **pay close attention to the "Review Scope" section** and ensure that all findings align strictly with the listed staged files.

   - If a finding does not clearly map to a file in the review scope, treat it as **low confidence**.
   - Do not introduce issues, suggestions, or risks that are unrelated to the displayed diff.
   - Avoid speculative or generalized advice that cannot be justified by the reviewed changes.

4. After verifying alignment with the review scope, summarize the Gemini review results for the user.

### Output requirements

Your final response should be structured and concise, and must include:

- **High priority issues**  
  Issues that may cause bugs, security risks, crashes, or data loss.

- **Medium priority concerns**  
  Design issues, maintainability problems, or potential performance risks.

- **Low priority or stylistic suggestions**  
  Readability, naming, formatting, or minor best-practice improvements.

- **Actionable next steps**  
  Concrete recommendations that the developer can realistically act on.

Do not repeat the full raw Gemini output verbatim unless explicitly asked.  
Your role is to act as a senior reviewer who filters, validates, and prioritizes the findings.

id: tm-code-review-gemini
namespace: tm
domain: code
action: review
qualifier: gemini
version: "1.0.0"
updated: "2026-01-17"
---

## Constraints

- Only review code that appears in the provided diff.
- Do not assume project architecture or conventions beyond what is visible in the changes.
- Do not suggest large-scale refactors unless a clear, high-risk issue justifies it.
- Prefer correctness and clarity over exhaustive commentary.

---

## Examples

**User:**
> Review the staged files before I commit.

**Expected behavior:**
- Run `review_with_gemini.sh`
- Read the "Review Scope" section
- Validate that review findings match the staged files
- Respond with a prioritized, scoped code review summary

id: tm-code-review-gemini
namespace: tm
domain: code
action: review
qualifier: gemini
version: "1.0.0"
updated: "2026-01-17"
---

**User:**
> Check the code quality of my staged changes.

**Expected behavior:**
- Same workflow as above
- Emphasize correctness and risk-related issues first

---

## Workflow

### Step 1: Collect Staged Changes
1. Run `scripts/review_with_gemini.sh`
2. Script executes `git diff --cached` to get staged changes
3. Script displays "Review Scope" with branch name and staged files

### Step 2: Review Analysis
1. Script sends diff to Gemini CLI for analysis
2. Gemini reviews code for:
   - Security vulnerabilities (XSS, injection, auth issues)
   - Logic errors and potential bugs
   - Performance concerns
   - Code quality and maintainability
   - Best practice violations

### Step 3: Validate Findings
1. Read the "Review Scope" section
2. Verify all findings map to staged files
3. Filter out speculative or unrelated suggestions
4. Treat unmapped findings as low confidence

### Step 4: Prioritize and Summarize
1. Categorize by severity: High, Medium, Low
2. Focus on actionable items
3. Provide specific line numbers and file references
4. Suggest concrete fixes

### Step 5: Present Results
1. High priority issues first (security, bugs, crashes)
2. Medium priority concerns (design, performance)
3. Low priority suggestions (style, naming)
4. Actionable next steps

id: tm-code-review-gemini
namespace: tm
domain: code
action: review
qualifier: gemini
version: "1.0.0"
updated: "2026-01-17"
---

## Security Considerations

### Input Handling
1. **Git Diff Content**
   - The diff is sourced from local git repository (trusted source)
   - No user input directly injected into commands
   - Diff size is limited by MAX_DIFF_LINES environment variable (default: 5000)

2. **Script Execution Safety**
   - review_with_gemini.sh validates environment before execution
   - Checks for required tools (git, Gemini CLI)
   - Uses `set -euo pipefail` for proper error handling
   - No arbitrary command execution from user input

3. **Gemini API Security**
   - Requires valid API key (GEMINI_API_KEY environment variable)
   - API calls are made over HTTPS
   - No sensitive code should be in diff (user responsibility)
   - Review results are saved locally only

### Sensitive Information Handling
1. **Code Content**
   - Warn users not to commit secrets, API keys, passwords in code
   - Review process may expose sensitive logic to Gemini API
   - Users should be aware code is sent to external AI service
   - Consider using `.gitignore` for sensitive files

2. **Review Results**
   - Saved to local file: `gemini_review_result.txt`
   - Contains code snippets from diff
   - Should not be committed to git (add to .gitignore)
   - May contain security findings that should be handled carefully

### External Dependencies
1. **Gemini CLI**
   - Official Google tool, regularly updated
   - Requires API key for authentication
   - Network connectivity required
   - API quota limits apply

2. **Git**
   - Standard version control tool
   - Trusted system dependency
   - No remote operations performed

---

## Error Handling

### Pre-execution Validation
1. **Git Repository Check**
   - Error if not in a git repository
   - Message: "Not a git repository. Please run from within a git project."
   - Action: Change directory to git project root

2. **Staged Changes Check**
   - Error if no staged changes found
   - Message: "No staged changes found. Use 'git add' to stage files first."
   - Action: User should stage files with `git add`

3. **Gemini CLI Check**
   - Error if Gemini CLI not installed
   - Message: "Gemini CLI not found. Install: npm install -g @google/gemini-cli"
   - Provide installation link: https://www.npmjs.com/package/@google/gemini-cli

4. **API Key Check**
   - Error if GEMINI_API_KEY not set
   - Message: "GEMINI_API_KEY environment variable not set. Please configure your API key."
   - Action: Guide user to set environment variable

### Execution Errors
1. **Diff Too Large**
   - If diff exceeds MAX_DIFF_LINES (default: 5000)
   - Warning: "Diff is too large (X lines). Only first 5000 lines will be reviewed."
   - Action: Review proceeds with truncated diff
   - Recommendation: "Consider reviewing in smaller commits"

2. **Gemini API Failures**
   - Network timeout or API errors
   - Error: "Gemini API request failed: [error details]"
   - Action: Check network connection and API key
   - Fallback: Suggest manual review or retry

3. **Script Execution Failures**
   - If review_with_gemini.sh fails
   - Capture stderr output
   - Display error to user with context
   - Provide troubleshooting steps

### Output Handling
1. **Empty Review Results**
   - If Gemini returns no findings
   - Message: "No issues found in the staged changes. Code looks good!"
   - Clarify: This doesn't guarantee bug-free code, just no obvious issues detected

2. **Malformed Output**
   - If review result file is corrupted or empty
   - Error: "Failed to parse review results. Please try again."
   - Action: Check gemini_review_result.txt for details

3. **File Write Errors**
   - If cannot write gemini_review_result.txt
   - Error: "Cannot write to output file. Check disk space and permissions."
   - Action: Verify write permissions in current directory

### Graceful Degradation
When Gemini CLI is unavailable:
- Inform user that external AI review is not available
- Suggest alternatives: manual review, code-review-assistant (if exists)
- Do not fail the commit workflow (review is advisory, not blocking)

id: tm-code-review-gemini
namespace: tm
domain: code
action: review
qualifier: gemini
version: "1.0.0"
updated: "2026-01-17"
---

## Additional Examples

### Example 3: Security-focused review
```
User: "Review my authentication code for security issues"

Expected behavior:
- Run review_with_gemini.sh
- Focus on security aspects in the summary
- Highlight: SQL injection, XSS, auth bypass, token handling
- Provide security-specific recommendations
```

### Example 4: Performance review
```
User: "Check if my changes have performance issues"

Expected behavior:
- Run review_with_gemini.sh
- Emphasize performance concerns in summary
- Identify: N+1 queries, memory leaks, inefficient algorithms
- Suggest optimizations with benchmarks
```

### Example 5: Before major refactoring
```
User: "I'm about to refactor the database layer, review the changes"

Expected behavior:
- Run review_with_gemini.sh on staged refactoring
- Check for: breaking changes, data migration needs, backward compatibility
- Validate: test coverage, error handling, rollback strategy
- Confirm architectural alignment
```
