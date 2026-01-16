# PR Review Assistant

AI-powered pull request reviewer that provides comprehensive, structured feedback to help you review code faster and more thoroughly.

## Features

- **Comprehensive Analysis** - Checks correctness, security, performance, and code quality
- **Structured Feedback** - Organized by priority (blocking, important, minor)
- **Specific References** - Includes file names and line numbers
- **GitHub Integration** - Fetches PR data and can post reviews directly
- **Risk Assessment** - Evaluates merge risk level
- **Positive Recognition** - Acknowledges good practices
- **Bilingual Output** - Traditional Chinese descriptions with English code terms

## Dependencies

- [Gemini CLI](https://github.com/google-gemini/gemini-cli): `npm install -g @google/gemini-cli`
- [GitHub CLI](https://cli.github.com/): Install from https://cli.github.com/
- [jq](https://stedolan.github.io/jq/): JSON processor (`brew install jq` or `apt-get install jq`)
- Git repository with access to the PR
- `GEMINI_API_KEY` environment variable set

## Quick Start

### 1. Setup

```bash
# Install dependencies
npm install -g @google/gemini-cli
brew install gh  # or follow https://cli.github.com/

# Authenticate with GitHub
gh auth login

# Set Gemini API key
export GEMINI_API_KEY="your-api-key"
```

### 2. Review a PR

**Using Claude Code** (Recommended):

```
> Review PR #123
> Help me review https://github.com/myorg/myrepo/pull/456
> Check the code quality in this PR
```

**Direct script usage**:

```bash
cd /path/to/your/project
bash ~/.claude/skills/pr-review-assistant/scripts/review_pr.sh 123
```

### 3. Post the Review

After reviewing, post your feedback:

```bash
# As a comment
gh pr comment 123 --body-file /tmp/pr_review_result.txt

# As a review requesting changes
gh pr review 123 --request-changes --body-file /tmp/pr_review_result.txt

# As an approval
gh pr review 123 --approve --body-file /tmp/pr_review_result.txt
```

## Usage Examples

### Example 1: Daily PR Review

```bash
$ bash review_pr.sh 456

================ PR Review Analysis ================
Fetching PR #456 information...

Title: Add user authentication with JWT
Author: @john-doe
Branch: feature/auth → main
Changes: +342 -89 lines (8 files)
====================================================

Changed files:
  - src/api/auth.js
  - src/middleware/verify-token.js
  - src/models/user.js
  ...

Analyzing PR with AI...

================ PR Review Result ================

### Review Summary
- **Overall Verdict**: Request Changes
- **Risk Level**: Medium
- **Files Reviewed**: 8 files
- **Issues Found**: 12 total (2 blocking, 6 important, 4 minor)

### 🔴 Blocking Issues

1. **[Security] SQL injection vulnerability** - `src/api/auth.js:45`
   - 用戶輸入直接拼接到 SQL 查詢中，存在 SQL injection 風險
   - Why it's blocking: 可能導致資料庫被攻擊或資料洩漏
   - Suggested fix: 使用 parameterized queries 或 ORM
   ```javascript
   // Bad
   const query = `SELECT * FROM users WHERE email = '${email}'`;

   // Good
   const query = 'SELECT * FROM users WHERE email = ?';
   db.query(query, [email]);
   ```

2. **[Correctness] Missing null check** - `src/middleware/verify-token.js:23`
   - 未檢查 token 是否存在就直接使用
   - Why it's blocking: 會導致 runtime error
   - Suggested fix: 添加 null check
   ...

### 🟡 Important Issues

1. **[Performance] N+1 query problem** - `src/api/users.js:67`
   - 在循環中查詢資料庫，效能較差
   ...

### 🟢 Minor Issues

1. **[Style] Inconsistent naming** - `src/models/user.js:12`
   - 變數命名不一致 (camelCase vs snake_case)
   ...

### ✅ Positive Observations

- ✓ 完整的錯誤處理
- ✓ 適當的輸入驗證
- ✓ 清晰的函數命名

==================================================

Review saved to: /tmp/pr_review_result.txt

To post this review as a comment:
  gh pr comment 456 --body-file /tmp/pr_review_result.txt
```

### Example 2: Pre-Merge Safety Check

```bash
# Quick check before approving
$ bash review_pr.sh 789

# Review shows "Overall Verdict: Approve"
# Post approval
$ gh pr review 789 --approve --body-file /tmp/pr_review_result.txt
```

### Example 3: Large PR Review

```bash
# For a large PR (>2000 lines)
$ bash review_pr.sh 321

Warning: Diff is large (3542 lines). Truncating to 2000 lines for analysis.
Diff size: 2000 lines

# Still gets useful feedback on the first 2000 lines
# Review rest manually or by files
```

## Review Categories

### 🔴 Blocking Issues
**Must fix before merge**

- **Bugs & Logic Errors**
  - Null pointer exceptions
  - Logic errors
  - Edge cases not handled
  - Off-by-one errors

- **Security Vulnerabilities**
  - SQL injection
  - XSS (Cross-site scripting)
  - CSRF (Cross-site request forgery)
  - Authentication/authorization bypass
  - Sensitive data exposure

- **Data Loss Risks**
  - Missing database transactions
  - Improper error handling in critical paths
  - Race conditions

### 🟡 Important Issues
**Should address**

- **Design Problems**
  - Tight coupling
  - Violation of SOLID principles
  - Missing abstractions
  - Poor separation of concerns

- **Performance Concerns**
  - N+1 queries
  - Inefficient algorithms
  - Memory leaks
  - Missing indexes

- **Maintainability**
  - Code smells (long functions, deep nesting)
  - Missing error handling
  - Insufficient logging
  - Hard-coded values

### 🟢 Minor Issues
**Nice-to-have improvements**

- **Code Style**
  - Formatting inconsistencies
  - Naming conventions
  - Comment clarity

- **Readability**
  - Complex expressions
  - Magic numbers
  - Unclear variable names

- **Documentation**
  - Missing JSDoc/comments
  - Outdated comments
  - Unclear function purpose

## Workflow Integration

### Daily Workflow

```bash
# 1. Someone opens a PR
# 2. You get notified

# 3. Quick AI review
$ bash review_pr.sh <PR-number>

# 4. Add human insights
# - Check business logic
# - Verify requirements
# - Consider architecture

# 5. Post combined review
$ gh pr comment <PR-number> --body-file /tmp/pr_review_result.txt

# 6. Engage in discussion
# 7. Re-review after changes if needed
```

### Team Process

**For Code Authors:**
1. Create PR with good description
2. Self-review using the tool
3. Fix obvious issues before requesting review

**For Reviewers:**
1. Use AI assistant for initial scan
2. Focus human review on:
   - Business logic correctness
   - Architecture appropriateness
   - Team conventions
3. Combine AI and human insights
4. Provide constructive feedback

**For Team Leads:**
1. Use for consistency across reviews
2. Catch common issues automatically
3. Coach junior reviewers
4. Track recurring patterns

## Advanced Usage

### Review Specific Branch Comparison

```bash
# Review changes from a specific branch
$ git fetch origin
$ gh pr diff <PR-number> | head -n 2000 > /tmp/custom-diff.txt
# Then manually analyze with custom context
```

### Batch Review Multiple PRs

```bash
# Review all open PRs
$ for pr in $(gh pr list --json number -q '.[].number'); do
    echo "Reviewing PR #$pr"
    bash review_pr.sh "$pr"
    echo "---"
  done
```

### Custom Review Focus

Edit the script prompt to focus on specific aspects:
- Security-only review
- Performance-only review
- Style-only review

### Integration with CI/CD

```yaml
# .github/workflows/pr-review.yml
name: AI Code Review

on:
  pull_request:
    types: [opened, synchronize]

jobs:
  review:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v3
      - name: Setup Gemini
        run: npm install -g @google/gemini-cli
      - name: Run AI Review
        env:
          GEMINI_API_KEY: ${{ secrets.GEMINI_API_KEY }}
          GITHUB_TOKEN: ${{ secrets.GITHUB_TOKEN }}
        run: |
          bash scripts/review_pr.sh ${{ github.event.pull_request.number }}
      - name: Post Review
        run: gh pr comment ${{ github.event.pull_request.number }} --body-file /tmp/pr_review_result.txt
```

## Configuration

### Environment Variables

```bash
# Required
export GEMINI_API_KEY="your-api-key"

# Optional
export GEMINI_MODEL="gemini-2.0-flash-exp"  # Use different model
```

### Script Configuration

Edit `scripts/review_pr.sh`:

```bash
# Adjust max diff size (default: 2000 lines)
MAX_DIFF_LINES=5000

# Change output location
OUTPUT_FILE="$HOME/pr-reviews/review-$(date +%Y%m%d-%H%M%S).txt"
```

## Tips & Best Practices

### For Best Results

1. **Review promptly** - Fresh context helps
2. **Read the PR description** - Understand intent
3. **Check linked issues** - Know the requirements
4. **Review in chunks** - For large PRs, review by file
5. **Combine with testing** - AI doesn't run code
6. **Add context** - Your domain knowledge matters

### Common Patterns

**Good PR for AI Review:**
- Clear, focused changes
- Under 500 lines
- Well-structured commits
- Good PR description

**Challenging PR for AI:**
- Massive refactoring (>2000 lines)
- Requires deep domain knowledge
- Involves complex business logic
- Needs running/testing to verify

### Review Checklist

Before approving a PR, verify:

- [ ] AI found no blocking issues
- [ ] Business logic is correct
- [ ] Tests are adequate
- [ ] Documentation is updated
- [ ] No breaking changes (or properly handled)
- [ ] Performance is acceptable
- [ ] Security is considered
- [ ] Follows team conventions

## Troubleshooting

### "gh: command not found"

```bash
# Install GitHub CLI
brew install gh  # macOS
# Or: https://cli.github.com/

# Verify
gh --version
```

### "Failed to fetch PR"

```bash
# Authenticate
gh auth login

# Check access
gh pr list

# Verify PR exists
gh pr view <PR-number>
```

### "GEMINI_API_KEY not set"

```bash
# Set API key
export GEMINI_API_KEY="your-key"

# Or add to shell profile
echo 'export GEMINI_API_KEY="your-key"' >> ~/.zshrc
source ~/.zshrc
```

### "Permission denied" errors

```bash
# Make script executable
chmod +x ~/.claude/skills/pr-review-assistant/scripts/review_pr.sh
```

### Review is too generic

**Possible causes:**
- PR is too large (truncated)
- Changes are mostly boilerplate
- Insufficient context in diff

**Solutions:**
- Review smaller PRs or split large ones
- Add context in PR description
- Review specific files manually
- Combine with code-story-teller for history

### False positives

**Remember:**
- AI suggestions are not always correct
- Use human judgment
- Consider project-specific context
- Edit AI feedback before posting

## Comparison with Other Tools

### vs Manual Review
- ✅ Faster initial scan
- ✅ Catches common issues
- ✅ Consistent criteria
- ❌ Lacks business context
- ❌ Cannot run code
- ❌ No domain expertise

### vs Static Analyzers (ESLint, etc.)
- ✅ More context-aware
- ✅ Natural language feedback
- ✅ Explains "why"
- ❌ Slower
- ❌ Costs API usage
- ❌ Less precise

### vs code-review-gemini skill
- **PR Review Assistant**: Reviews entire PRs (multiple commits)
- **code-review-gemini**: Reviews staged changes (pre-commit)
- Use both in workflow: code-review-gemini for self-review, PR Review Assistant for team review

## Cost Considerations

Gemini API usage:
- ~2-5KB per small PR
- ~10-20KB per medium PR
- ~50KB per large PR (truncated)

Estimated cost: $0.01 - $0.05 per PR (depends on your API plan)

## Privacy & Security

⚠️ **Important**: PR diffs are sent to Gemini API

**Do NOT review PRs containing:**
- Credentials or API keys
- Private keys or certificates
- Proprietary algorithms
- PII (Personal Identifiable Information)
- Trade secrets

**Best practices:**
- Review public repos only, or
- Ensure sensitive data is never in PRs, or
- Use self-hosted AI if reviewing proprietary code

## FAQ

**Q: Can it replace human reviewers?**
A: No. It's an assistant, not a replacement. Human judgment is essential for business logic, architecture, and team context.

**Q: How accurate is it?**
A: Varies by PR complexity. Best for catching common issues. Always verify AI suggestions.

**Q: Can it review non-code files?**
A: Yes, but optimized for code. Can review docs, configs, etc.

**Q: What languages are supported?**
A: All programming languages. AI quality may vary by language popularity.

**Q: Can it access private repos?**
A: Yes, if your `gh` CLI is authenticated with appropriate permissions.

**Q: Does it remember previous reviews?**
A: No, each review is independent. No state is stored.

**Q: Can it learn our team's conventions?**
A: Not directly, but you can modify the prompt to include team guidelines.

## Related Skills

- **code-review-gemini** - Review staged changes before commit
- **commit-msg-generator** - Generate commit messages
- **code-story-teller** - Understand code evolution
- **pr-description-generator** - Create PR descriptions (coming soon)
- **pr-merge-readiness-checker** - Automated merge checks (coming soon)

## Contributing

Found ways to improve PR reviews? See [CONTRIBUTING.md](../CONTRIBUTING.md).

## License

MIT

---

**Happy reviewing! 🔍✨**
