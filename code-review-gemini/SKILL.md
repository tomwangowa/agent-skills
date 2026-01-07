---
name: Code Review with Gemini
description: Review changed code with an external code review script using the Gemini CLI. Use when the user asks to review code changes, analyze diffs, find issues in the changed files, suggest improvements, or improve quality.
---

# Code Review with Gemini

## Instructions

This Skill helps with performing a code review of recently changed files using an external script and the Gemini CLI.

When the user **expresses intent to review code**, especially phrases such as:

- "review the changed files"
- "analyze the code changes"
- "check for issues in the diffs"
- "give me a code review"
- "find problems in recent commits"

then:

1. Run the attached shell script `scripts/review_with_gemini.sh` to generate a full code review report.
   The script will:
   - Collect a diff of changed files (`git diff main...HEAD`)
   - Call `gemini` CLI to generate a review summary
   - Save output to `$TMPDIR/gemini_review_result.txt` (or `/tmp/gemini_review_result.txt`)

2. After the script runs, read the content of the output file from the temporary directory.

3. Summarize the findings to the user, including:
   - High priority issues
   - Medium or stylistic suggestions
   - Actionable improvement steps
   - Optionally ask follow-ups to clarify scope

## Examples

User says:
> Please review the changed files and highlight issues.

Expected Skill activation:
- Run `review_with_gemini.sh`
- Read the output file from temporary directory
- Respond with structured review summary

User says:
> I want a code quality review of my recent commits.

Expected Skill activation:
- Same workflow above
