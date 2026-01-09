---
name: Code Review with Gemini
description: Perform a code review on staged changes. Use this Skill when the user asks to review staged files, check code quality before committing, or analyze changes about to be committed.
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

---

**User:**
> Check the code quality of my staged changes.

**Expected behavior:**
- Same workflow as above
- Emphasize correctness and risk-related issues first
