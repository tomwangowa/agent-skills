# Code Review with Gemini

Optional depth / refactored-patch code reviewer using Gemini CLI.

> **Role (effective 2026-04):** Not the default reviewer. `code-review-claude` is the default for any review request and for the pre-commit auto-review rule, because a 2026-04 n=6 benchmark found it produces broader finding coverage (2.3×–5.0×) and zero verified hallucinations, whereas this skill hallucinated P0/P1 syntax issues in 3/6 runs.
>
> **When to use this skill instead:** you want a fully worked refactored patch, or an external second-opinion pass after a `code-review-claude` review. Trigger words: "gemini review", "detailed review", "thorough review", "refactored patch".

## Overview

This skill performs a structured code review on staged changes by sending the diff to Gemini CLI. The output is a prioritized findings list plus a verdict — useful when you want a different model's perspective or need a ready-to-apply rewrite on a small file.

It covers:
- Security vulnerabilities (XSS, SQL injection, authentication issues)
- Logic errors and potential bugs
- Performance concerns
- Code quality and maintainability
- Best practice violations

Weaknesses (documented here so you can compensate): no syntax-checker verification of whitespace / regex / character-class findings (responsible for the 3/6 hallucination rate in the benchmark), no adversarial pass, no assumptions list. If those matter, run `code-review-claude` first and chain this skill only when you specifically want the patch or second opinion.

## Quick Start

### Prerequisites

1. **Gemini CLI**
   ```bash
   npm install -g @google/gemini-cli
   ```

2. **API Key**
   ```bash
   export GEMINI_API_KEY="your-api-key-here"
   ```

3. **Git Repository**
   - Must be run from within a git repository
   - Changes must be staged (`git add`)

### Basic Usage

1. **Stage your changes**
   ```bash
   git add src/auth.ts src/api.ts
   ```

2. **Trigger review**
   Tell Claude:
   ```
   "Review the staged files"
   "Check code quality before commit"
   "Analyze my changes"
   ```

3. **Get prioritized feedback**
   - 🔴 High priority: Security, bugs, crashes
   - 🟡 Medium priority: Design, performance
   - 🟢 Low priority: Style, naming

## Features

### Intelligent Analysis
- **Security-first**: Detects XSS, injection, auth vulnerabilities
- **Context-aware**: Understands code patterns and intent
- **Actionable**: Provides specific fixes, not just problems
- **Scoped**: Only reviews what you staged

### Smart Filtering
- Validates findings against actual staged files
- Filters out speculative suggestions
- Focuses on high-impact issues
- Provides line-specific references

### Configurable
- `MAX_DIFF_LINES`: Limit diff size (default: 5000)
- `GEMINI_MODEL`: Choose model (default: gemini-2.0-flash-exp)

## Usage Examples

### Example 1: Pre-commit Review
```bash
# Make changes
vim src/auth.ts

# Stage changes
git add src/auth.ts

# Review (via Claude)
"Review the staged files before I commit"

# Claude runs review and shows findings
# Fix issues, then commit
git commit -m "Fix auth vulnerabilities found in review"
```

### Example 2: Security-focused
```
"Review my authentication code for security issues"

Output includes:
- OAuth token handling validation
- SQL injection checks
- XSS prevention verification
- Session management review
```

### Example 3: Performance Check
```
"Check if my changes have performance issues"

Output includes:
- Algorithm complexity analysis
- Database query optimization
- Memory leak detection
- Caching opportunities
```

## Configuration

### Environment Variables

```bash
# Required
export GEMINI_API_KEY="your-api-key"

# Optional
export MAX_DIFF_LINES=5000        # Limit diff size
export GEMINI_MODEL="gemini-2.0-flash-exp"  # AI model
```

### Diff Size Limit

Large diffs are automatically truncated:
- Default limit: 5000 lines
- Prevents API quota exhaustion
- Warns when truncation occurs
- Recommendation: Review in smaller chunks

## Workflow Integration

### Pre-commit Hook

```bash
#!/bin/bash
# .git/hooks/pre-commit

echo "Running AI code review..."
claude-skill code-review-gemini

# Don't block commit (review is advisory)
exit 0
```

### CI/CD Pipeline

```yaml
# .github/workflows/review.yml
- name: AI Code Review
  run: |
    git add .
    claude-skill code-review-gemini
```

## Output Format

### Review Report Structure

```
================ Review Scope ================
Branch: feature-auth
Review target: Staged changes
Staged files:
  - src/auth.ts
  - src/middleware.ts
==============================================

[Gemini Analysis]

High Priority Issues (🔴):
1. SQL Injection Risk (src/auth.ts:42)
   - Issue: Unsanitized user input in query
   - Fix: Use parameterized queries

Medium Priority (🟡):
2. Missing Error Handling (src/middleware.ts:15)
   - Issue: No try-catch for async operation
   - Fix: Add error boundary

Low Priority (🟢):
3. Variable naming (src/auth.ts:10)
   - Suggestion: Use camelCase for consistency
```

## Troubleshooting

### Issue: "Gemini CLI not found"
**Solution:**
```bash
npm install -g @google/gemini-cli
```

### Issue: "GEMINI_API_KEY not set"
**Solution:**
```bash
# Get API key from https://aistudio.google.com/apikey
export GEMINI_API_KEY="your-api-key"

# Make permanent (add to ~/.zshrc or ~/.bashrc)
echo 'export GEMINI_API_KEY="your-api-key"' >> ~/.zshrc
```

### Issue: "No staged changes found"
**Solution:**
```bash
git add <files>  # Stage files first
```

### Issue: "Diff too large"
**Solution:**
- Review in smaller commits
- Increase MAX_DIFF_LINES if needed
- Split large refactoring into multiple PRs

### Issue: "API quota exceeded"
**Solution:**
- Wait for quota reset
- Upgrade API tier
- Use MAX_DIFF_LINES to reduce usage

## Best Practices

### 1. Stage Meaningful Chunks
- Review related changes together
- Don't mix refactoring with features
- Keep commits focused

### 2. Address High Priority First
- Fix security issues immediately
- Address bugs before style
- Prioritize based on impact

### 3. Use for Learning
- Understand why issues are flagged
- Learn best practices from suggestions
- Build better coding habits

### 4. Don't Over-rely
- AI review supplements, doesn't replace human review
- Critical code still needs peer review
- Use judgment on suggestions

## Limitations

- **AI-based**: May have false positives/negatives
- **Context-limited**: Only sees staged diff, not full codebase
- **Language-dependent**: Best for popular languages (JS, Python, Go, etc.)
- **API-dependent**: Requires network and API availability
- **Not a replacement**: Complements, doesn't replace human code review

## Integration with Other Skills

### Works well with:
- **code-review-claude** (the default reviewer) — Run that first; chain this skill only when you need a refactored patch or an external second opinion
- **pr-review-assistant** — PR-level review (also defaults to claude; this skill powers the keyword-triggered deep PR review path via `scripts/review_pr.sh`)

### Typical Workflow (2026-04 onward):
```
1. [Write code]
2. code-review-claude → Default review (broad coverage + adversarial + assumptions + syntax-verified)
3. (optional) code-review-gemini → Depth second opinion and/or refactored patch  ← This skill
4. [Commit with Conventional Commits format]
5. (for PRs) pr-review-assistant → PR-level review
```

## File Structure

```
code-review-gemini/
├── SKILL.md              # Skill definition and documentation
├── README.md             # This file
└── scripts/
    └── review_with_gemini.sh  # Review automation script
```

## Version

**1.0.0** - Stable release with comprehensive error handling and security

## Support

- Check SKILL.md for detailed workflow
- Review error messages for troubleshooting steps
- Test with small changes first
- Ensure API key is valid

## License

Part of Claude Code Skills library.
