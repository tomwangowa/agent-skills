---
name: PR Review Assistant
description: Assist in reviewing pull requests by analyzing diffs and providing structured feedback. Use this Skill when the user asks to review a PR, analyze pull request changes, check code quality in PRs, or help with code review.
---

# PR Review Assistant

## Purpose

This Skill assists in reviewing pull requests by:
1. Fetching PR information and diff using GitHub CLI
2. Analyzing code changes comprehensively with Gemini AI
3. Identifying bugs, security issues, and code quality problems
4. Providing structured, prioritized feedback
5. Generating actionable review comments

The Skill helps developers:
- Review PRs faster and more thoroughly
- Catch issues that might be missed in manual review
- Maintain consistent review standards
- Learn from AI-suggested best practices
- Provide constructive feedback to teammates

---

## Instructions

When the user expresses intent to review a PR (for example: "review PR #123", "help me review this pull request", "analyze this PR"), follow the steps below strictly.

### Execution steps

1. **Identify the PR** to review
   - If user provides PR number: use it directly
   - If user provides PR URL: extract the number
   - If unclear, ask for clarification

2. **Run the script** `scripts/review_pr.sh <PR-number|PR-URL>`
   - The script will fetch PR details using GitHub CLI
   - It will analyze the diff with Gemini AI
   - It will generate a structured review

3. **Present the review** to the user:
   - Summarize the overall verdict and risk level
   - Highlight blocking issues first (if any)
   - Explain important issues
   - Mention minor suggestions
   - Note positive observations

4. **Offer follow-up actions**:
   - Post review as PR comment
   - Dive deeper into specific issues
   - Review related files
   - Suggest fixes for identified problems

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
- Requires Gemini CLI and API key
- Large PRs (>2000 lines) are truncated for analysis
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

- **code-review-gemini** - Review staged changes before committing
- **commit-msg-generator** - Generate commit messages
- **code-story-teller** - Understand code evolution
- **pr-description-generator** - Create PR descriptions (coming soon)

---

## Security Note

⚠️ **The PR diff is sent to the Gemini API for analysis.**

**Never review PRs containing:**
- API keys, tokens, or passwords
- Private keys or certificates
- Personal identifiable information (PII)
- Proprietary algorithms or trade secrets
- Other sensitive data

Always check what's in the PR before running the review.
