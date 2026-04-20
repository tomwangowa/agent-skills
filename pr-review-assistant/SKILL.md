---
name: pr-review-assistant
description: Assist in reviewing pull requests by analyzing diffs and providing structured feedback. Use this Skill when the user asks to review a PR, analyze pull request changes, check code quality in PRs, or help with code review.
---

# PR Review Assistant

## Purpose

This Skill orchestrates a PR-level review workflow:
1. Fetches PR metadata and diff via GitHub CLI
2. Runs the `code-review-claude` workflow natively on the diff (default) — or delegates to Gemini CLI for a deep pass (opt-in)
3. Produces a prioritized, actionable findings list
4. Helps the user post the review back to GitHub

> **Default reviewer (as of 2026-04):** `code-review-claude`. Pre-2026-04 this skill defaulted to Gemini; the switch is documented in the "Why claude is the default PR reviewer" section below.

---

## Instructions

When the user expresses intent to review a PR (e.g., "review PR #123", "analyze this pull request", "help me review this PR"), route between two paths based on keywords:

- **Default path** — no Gemini keyword → native Claude review via `code-review-claude` workflow
- **Opt-in deep path** — "gemini review", "deep PR review", "refactored patch" → Gemini CLI via `scripts/review_pr.sh`

Both paths use `gh` CLI to fetch PR metadata + diff, then produce a prioritized findings list and offer to post the review back to GitHub.

### Workflow overview

```
PR identifier (number or URL)
    ↓
gh pr view + gh pr diff (common)
    ↓
Default path: run code-review-claude workflow natively
OR
Opt-in path: run scripts/review_pr.sh (Gemini CLI)
    ↓
Present structured findings to user
    ↓
Offer to post via gh pr comment / gh pr review
```

---

## Default path: native Claude PR review

Use this path when the user says "review PR #42", "check the code in this PR", "PR review", etc. — no Gemini keyword.

### Execution steps (default)

1. **Identify the PR** to review.
   - User provides PR number → use directly.
   - User provides PR URL → extract number from the trailing `/pull/<N>`.
   - Unclear → ask.

2. **Fetch PR metadata** with `gh`:
   ```bash
   gh pr view <PR-number> --json title,body,author,headRefName,baseRefName,additions,deletions,files
   ```

3. **Fetch the diff** with `gh`:
   ```bash
   gh pr diff <PR-number>
   ```

   If the diff exceeds ~2000 lines, note the size; review file-by-file (use `gh pr diff --name-only` to list files, then fetch per-file diffs as needed). Do **not** silently truncate — tell the user and ask how to proceed.

4. **Run the `code-review-claude` workflow** on the fetched diff:
   - Apply Step 0 (self-review detection — usually N/A for teammate PRs; flag if the current session authored any of the PR's files).
   - Apply Steps 3.1–3.6 (severity-prioritized findings, Step 3.3 syntax-checker verification, Step 3.4 language checklists, Step 3.5 adversarial, Step 3.6 assumptions list).
   - Label findings with file path + line number from the diff context.
   - Emit Step 4.5 Refactored Patch **only** if the PR is small (≤ ~200 lines / ≤ 3 files) and the user asked for it; PRs usually span multiple files so skip by default.

5. **Present to the user** in this order:
   - Review summary: verdict (Approve / Request changes / Comment), risk level, counts
   - 🔴 Blocking issues (with file:line + concrete fix)
   - 🟡 Important issues
   - 🟢 Minor suggestions
   - `[ADVERSARIAL]` findings
   - Assumptions Identified
   - ✅ Positive observations (sparingly — only when genuinely noteworthy)

6. **Offer follow-up actions**:
   - Post as PR comment: `gh pr comment <N> --body-file <file>`
   - Post as review with status: `gh pr review <N> --request-changes|--approve|--comment --body-file <file>`
   - Deep dive into a specific finding
   - Run the optional deep Gemini path (see below)

## Opt-in deep path: Gemini PR review

Use this path only when the user explicitly asks — trigger words: "gemini review this PR", "deep PR review", "detailed PR review", or "give me a refactored patch for this PR".

### Execution steps (deep / gemini)

1. Determine the skill base directory from the skill invocation context.
2. Run the script: `<skill_base_directory>/scripts/review_pr.sh <PR-number|PR-URL>`.
   - The script uses `gh` to fetch PR info + diff, sends the prompt to `gemini` CLI, and writes the result to `${TMPDIR:-/tmp}/pr_review_result.txt`.
   - Requires `gemini` CLI + `GEMINI_API_KEY`. If either is missing, the script exits with an actionable error; in that case fall back to the default Claude-native path.
3. Present the Gemini output to the user. Note explicitly that this review did **not** go through Step 3.3 syntax-checker verification — the user should sanity-check any syntax/regex/whitespace findings before acting on them.
4. Offer to post the review back to the PR via `gh pr comment` / `gh pr review`.

## Why claude is the default PR reviewer (2026-04)

A 2026-04 n=6 benchmark comparing `code-review-claude` and `code-review-gemini` on the same source code (HTTP retry clients in Java / Python / JS / TS / PHP / Shell) found:

- **Finding coverage**: Claude produced 2.3×–5.0× as many valid findings as Gemini across all six languages.
- **Hallucinations**: Claude 0/6. Gemini 3/6, all P0/P1-labelled, all in whitespace/regex/character-class category (e.g., falsely flagging `[^\s@]` as "space inside character class").
- **Adversarial + assumptions**: Claude's workflow includes these by default; Gemini's prompt (in `scripts/review_pr.sh`) does not.

PR reviews are higher-stakes than staged-diff reviews because findings often get posted publicly and consumed by another engineer. Hallucinated findings are expensive — they either erode trust in AI review or, worse, prompt the author to "fix" working code. So the default routes to the reviewer with the lowest verified-hallucination rate and the broadest coverage in the benchmark.

Gemini remains valuable as the opt-in deep path when the user specifically wants a different model's perspective or a fully applied refactored patch.

### Output requirements

Your response should include:

- **Review Summary**
  Overall verdict, risk level, and issue counts

- **Critical Findings**
  Blocking and important issues with clear explanations

- **Suggestions**
  Minor improvements and positive observations

- **Next Steps**
  How to post the review or take action

---

## Constraints

- Requires GitHub CLI (`gh`) installed and authenticated
- PR must be accessible with current GitHub credentials
- **Default path**: no external dependencies beyond `gh` — uses native Claude review
- **Deep / Gemini path**: additionally requires `gemini` CLI + `GEMINI_API_KEY`
- Large PRs (>2000 lines): default path asks how to proceed; deep path truncates via the script's `MAX_DIFF_LINES`
- File-specific context may be limited for very large PRs

---

## Examples

**User:**
> Review PR #456

**Expected behavior:**
- Run `review_pr.sh 456`
- Wait for GitHub API and Gemini analysis
- Present structured review with priorities
- Suggest posting the review as a comment

---

**User:**
> Help me review https://github.com/myorg/myrepo/pull/789

**Expected behavior:**
- Extract PR number (789) from URL
- Run review script
- Present findings organized by severity
- Highlight any blocking issues immediately

---

**User:**
> Can you check the code quality in PR #42?

**Expected behavior:**
- Run PR review focusing on code quality aspects
- Present findings with emphasis on maintainability
- Suggest improvements
- Note any positive patterns

---

**User:**
> Review this PR and tell me if it's safe to merge

**Expected behavior:**
- Ask for PR number if not provided
- Run comprehensive review
- Focus on blocking issues and risks
- Provide clear merge recommendation
- List any prerequisites for safe merge

---

## Use Cases

### Daily PR Reviews
When reviewing teammates' PRs:
- Get AI assistance to catch issues
- Ensure consistent review quality
- Save time on routine checks
- Focus human review on architecture and design

### Pre-Merge Safety Check
Before approving a PR:
- Verify no critical bugs
- Check security vulnerabilities
- Confirm best practices followed
- Assess merge risk

### Learning & Mentoring
For junior developers:
- Learn what to look for in reviews
- Understand common issues
- See examples of good feedback
- Build review skills

### Large PR Analysis
When PRs are too big to review easily:
- Get AI help to organize findings
- Identify high-priority issues first
- Break down review into manageable parts
- Ensure nothing is missed

---

## Review Output Structure

The generated review includes:

### Review Summary
- Overall verdict (Approve/Request Changes/Comment)
- Risk level (Low/Medium/High)
- Statistics (files, issues by category)

### 🔴 Blocking Issues
Must-fix before merge:
- Bugs and logic errors
- Security vulnerabilities
- Data loss risks
- Breaking changes without mitigation

### 🟡 Important Issues
Should address:
- Design problems
- Performance concerns
- Maintainability issues
- Missing error handling

### 🟢 Minor Issues
Nice-to-have:
- Code style improvements
- Naming suggestions
- Readability enhancements
- Documentation additions

### ✅ Positive Observations
Things done well:
- Good practices followed
- Clean code patterns
- Appropriate testing
- Clear documentation

### 📝 Additional Notes
- Questions for the author
- Context requests
- Deployment considerations
- Related PRs or issues

---

## Tips for Users

### Before Reviewing
1. **Understand the context**: Read the PR description
2. **Check the scope**: Note files and lines changed
3. **Know the codebase**: Familiarize with affected areas

### During Review
1. **Trust but verify**: AI is helpful but not perfect
2. **Add human judgment**: Consider business logic and team context
3. **Be constructive**: Frame feedback positively
4. **Ask questions**: If something is unclear

### After Review
1. **Post thoughtfully**: Edit AI suggestions as needed
2. **Follow up**: Engage in PR discussion
3. **Track issues**: Ensure blocking issues are resolved
4. **Learn**: Note patterns for future reviews

### Best Practices
1. **Review promptly**: Don't let PRs sit
2. **Focus on impact**: Prioritize high-risk changes
3. **Be specific**: Reference file names and line numbers
4. **Suggest solutions**: Don't just point out problems
5. **Acknowledge good work**: Note positive aspects

---

## Integration with GitHub

### Posting Reviews

**As a comment:**
```bash
gh pr comment <PR-number> --body-file /tmp/pr_review_result.txt
```

**As a review (with status):**
```bash
# Request changes
gh pr review <PR-number> --request-changes --body-file /tmp/pr_review_result.txt

# Approve
gh pr review <PR-number> --approve --body-file /tmp/pr_review_result.txt

# Comment only
gh pr review <PR-number> --comment --body-file /tmp/pr_review_result.txt
```

### Inline Comments

For specific line feedback, manually add comments:
```bash
gh pr comment <PR-number> --body "Comment text" --file path/to/file.js --line 42
```

---

## Limitations

### What AI Reviews Well
- Syntax errors and obvious bugs
- Common security vulnerabilities
- Code style and formatting
- Basic best practices
- Performance anti-patterns

### What Needs Human Review
- Business logic correctness
- Architecture decisions
- UX/product requirements
- Team-specific conventions
- Subjective trade-offs
- Historical context

### Known Limitations
- Cannot run or test code
- Limited context for very large PRs
- May miss domain-specific issues
- Cannot access linked issues/docs
- No access to CI/CD results

---

## Troubleshooting

### "gh: command not found"

**Solution:** Install GitHub CLI
```bash
# macOS
brew install gh

# Or from: https://cli.github.com/
```

### "Failed to fetch PR"

**Causes:**
- Not authenticated with GitHub
- PR doesn't exist
- No access to repository

**Solution:**
```bash
# Authenticate
gh auth login

# Verify access
gh pr list
```

### "Diff too large"

**Solution:** The script automatically truncates large diffs. For comprehensive review:
1. Review smaller chunks manually
2. Focus on specific files
3. Review commits individually

### Review quality issues

**If the review is too generic:**
- Ensure the PR has meaningful changes
- Check if diff was truncated
- Provide additional context to the AI

**If the review misses obvious issues:**
- Human review is still essential
- AI assists but doesn't replace human judgment
- Add your own findings to the review

---

## Related Skills

- **code-review-claude** (default) — Staged-diff reviewer; powers this skill's default PR-review path
- **code-review-gemini** — Optional depth / refactored-patch reviewer; powers this skill's keyword-triggered Gemini PR-review path via `scripts/review_pr.sh`
- **code-story-teller** — Understand code evolution
- **pr-description-generator** — Create PR descriptions (coming soon)

---

## Security Note

⚠️ **Default Claude-native path:** The PR diff stays inside the Claude Code session — no external API besides GitHub (`gh`). Use this path for PRs that might contain sensitive data.

⚠️ **Deep / Gemini path:** The PR diff **is** sent to the Gemini API for analysis. **Never run this path on PRs containing:**
- API keys, tokens, or passwords
- Private keys or certificates
- Personal identifiable information (PII)
- Proprietary algorithms or trade secrets
- Other sensitive data

Always check what's in the PR before choosing the deep path.
