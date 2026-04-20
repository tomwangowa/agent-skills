---
name: code-review-gemini
description: Perform deep, thorough code review using Gemini AI. Use this Skill when user explicitly requests 'gemini review', 'thorough review', 'detailed review', 'deep review', or a fully refactored patch. NOT the default reviewer and NOT the pre-commit reviewer — code-review-claude holds both roles as of 2026-04 (benchmark n=6 showed Claude's native reviewer has broader coverage and zero verified hallucinations; Gemini has value as an optional second-opinion pass or for generating ready-to-apply patches).
allowed-tools: Bash, Read, Edit, Write
---

# Code Review with Gemini

## Purpose

This Skill performs a structured code review by:
1. Determining what to review (auto-detect or user-specified scope)
2. Running an external review script that invokes the Gemini CLI
3. Summarizing the findings in a clear, prioritized manner

The Skill is designed to be deterministic, auditable, and flexible across different review scopes.

---

## Review Modes

The script supports five review modes, with smart auto-detection as default:

| Mode | Flag | Description |
|------|------|-------------|
| **Auto** | (default) | Staged → unstaged → error |
| **Staged** | `--staged` | Only `git diff --cached` |
| **Unstaged** | `--unstaged` | Only `git diff` (working directory) |
| **Files** | `--files FILE...` | Specific files — works for **untracked files** too |
| **Branch** | `--branch BASE` | Diff of `BASE...HEAD` |
| **Commit** | `--commit SHA` | A single commit's changes |

---

## Instructions

When the user expresses intent to review code, follow the steps below strictly.

### Step 0: Determine Review Scope

Parse the user's request to determine which mode to use:

| User says | Mode to use |
|-----------|-------------|
| "review staged changes" / "review before commit" | `--staged` |
| "review my changes" / "review what I changed" | (auto — no flag) |
| "review unstaged changes" / "review working directory" | `--unstaged` |
| "review foo.py and bar.js" / "review this file" | `--files foo.py bar.js` |
| "review changes vs main" / "review branch diff" | `--branch main` |
| "review commit abc123" / "review last commit" | `--commit abc123` (resolve "last commit" to HEAD) |
| Ambiguous or no scope specified | (auto — no flag) |

### Step 1: Run the Review Script

1. Determine the skill base directory from the skill invocation context.

2. Run: `<skill_base_directory>/scripts/review_with_gemini.sh [MODE] [ARGS...]`

   For example (where `$BASE` is the skill base directory):
   ```bash
   # Auto-detect
   $BASE/scripts/review_with_gemini.sh

   # Specific files
   $BASE/scripts/review_with_gemini.sh --files src/app.py tests/test_app.py

   # Branch diff
   $BASE/scripts/review_with_gemini.sh --branch main

   # Specific commit
   $BASE/scripts/review_with_gemini.sh --commit abc1234
   ```

   **Important**: Always use the full absolute path to the script (resolved from skill base directory),
   not a relative path, since the current working directory may be the user's project directory.

3. Observe the script output carefully. The script prints a **"Review Scope"** section that includes:
   - Current branch name
   - Review target (mode used)
   - List of files under review

### Step 2: Validate Findings

**Pay close attention to the "Review Scope" section** and ensure all findings align strictly with the listed files.

- If a finding does not clearly map to a file in the review scope, treat it as **low confidence**.
- Do not introduce issues, suggestions, or risks that are unrelated to the displayed diff/content.
- Avoid speculative or generalized advice that cannot be justified by the reviewed changes.

### Step 2.5: Adversarial Review Pass

After receiving Gemini's analysis, actively probe the diff with these four questions:

1. **"What input breaks this?"**
   For each function or branch in the diff, construct at least one concrete input that could cause unexpected behavior (nil, empty, overflow, concurrent, malformed). If no such input exists, state why.

2. **"What does this assume that is not validated?"**
   List every implicit assumption: input types, ordering guarantees, environment variables present, upstream behavior, "this error won't happen". Each is a finding unless explicitly validated in code.

3. **"Does the test actually test the claim?" (Mirror Test)**
   For every test in the diff, check whether deleting the implementation would still let the test pass. Specific checks:
   - Is the assertion on the **return value / side effect** of the code under test, or on a mock/stub?
   - Would replacing the function body with `return null` / `return []` / `pass` cause the test to fail?
   - Does the test assert on behavior, or merely on the absence of errors?

4. **"Is this a fix or a suppression?"**
   Check whether the change addresses the root cause or merely silences a symptom (e.g., catching and swallowing errors, adding `|| default` to mask nil, `@SuppressWarnings`, `# type: ignore`).

**Tagging rule:** Any issue discovered through this pass is tagged `[ADVERSARIAL]` in the output.

### Step 3: Prioritize and Summarize

Categorize by severity, provide specific line numbers and file references, suggest concrete fixes.

### Step 4: Present Results

Your final response must include:

- **High priority issues** — bugs, security risks, crashes, data loss
- **Medium priority concerns** — design, maintainability, performance
- **Low priority suggestions** — readability, naming, formatting
- **Adversarial findings** — tagged `[ADVERSARIAL]`, grouped separately
- **Assumptions identified** — implicit assumptions the code does not validate
- **Actionable next steps** — concrete recommendations

Do not repeat the full raw Gemini output verbatim unless explicitly asked.
Your role is to act as a senior reviewer who filters, validates, and prioritizes the findings.

---

## Constraints

- Only review code that appears in the provided diff or file content.
- Do not assume project architecture or conventions beyond what is visible in the changes.
- Do not suggest large-scale refactors unless a clear, high-risk issue justifies it.
- Prefer correctness and clarity over exhaustive commentary.

---

## Workflow

### Step 1: Determine Scope
Parse user intent → select mode (see Step 0 table above).

### Step 2: Execute Review
Run the review script with the appropriate mode and arguments.

### Step 3: Validate Findings
Cross-check all findings against the "Review Scope" section output.

### Step 4: Adversarial Pass
Apply the four adversarial questions to the diff/content.

### Step 5: Present Results
Deliver prioritized, scoped summary (High → Medium → Low → Adversarial → Assumptions → Next steps).

---

## Examples

### Example 1: Pre-commit review (staged)
**User:** "Review the staged files before I commit."
→ Run with `--staged`
→ Script shows staged file list, sends diff to Gemini, returns prioritized findings.

### Example 2: Review specific files (including untracked)
**User:** "Review src/api/handler.py and utils/new_helper.py"
→ Run with `--files src/api/handler.py utils/new_helper.py`
→ Works even if files are not git-tracked. Script reads file contents directly.

### Example 3: Branch diff review
**User:** "Review my changes compared to main"
→ Run with `--branch main`
→ Shows all commits since diverging from main.

### Example 4: Single commit review
**User:** "Review the last commit"
→ Resolve to HEAD, run with `--commit HEAD`

### Example 5: Auto-detect (no scope given)
**User:** "Review my code"
→ Run with no flags. Auto-detects: staged changes first, then unstaged.

---

## Security Considerations

### Input Handling
- Git diff content is sourced from local repository (trusted source)
- File content in `--files` mode is read from local filesystem only
- No user input directly injected into shell commands; file paths are passed as arguments, not interpolated into strings
- Script uses `set -euo pipefail` to fail fast on undefined variables or pipe errors

### Path Safety
- `--files` mode validates file existence before reading (`-f` check)
- No directory traversal risk: paths are resolved by the shell, not constructed from user input
- Temporary files created via `mktemp` and cleaned up after use

### Sensitive Information Handling
- **Warning**: Code sent to Gemini API is transmitted to an external service (Google). Do not review files containing secrets, API keys, passwords, or PII
- Review results saved to `$TMPDIR` only, not persisted
- No review output is committed to git

### External Dependencies
- **Gemini CLI**: Official Google tool, requires valid API key, communicates over HTTPS
- **Git**: Standard VCS tool, no remote operations performed (read-only local operations)

---

## Error Handling

The script handles errors for each mode:
- Missing git repo (for git-dependent modes)
- No changes detected (staged/unstaged)
- File not found (--files mode, skips with warning)
- Invalid branch or commit SHA
- Gemini CLI not installed

When Gemini CLI is unavailable, inform the user and suggest alternatives.
