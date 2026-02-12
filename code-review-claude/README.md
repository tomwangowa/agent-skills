# Native Code Review with Claude

<div align="center">

**⚡ Lightning-fast code review using Claude Code's native capabilities**

[![Production Ready](https://img.shields.io/badge/status-production%20ready-brightgreen)]()
[![Audit Score](https://img.shields.io/badge/audit%20score-93%2F100-brightgreen)]()
[![No Dependencies](https://img.shields.io/badge/dependencies-none-blue)]()
[![Speed](https://img.shields.io/badge/speed-%3C%2030%20seconds-blue)]()

</div>

---

## 🎯 Purpose

A lightweight, fast code review skill that provides immediate feedback during development without external dependencies or API keys. Designed as a complementary tool to `code-review-gemini` for rapid validation checks.

### When to Use This Skill

✅ **Perfect for:**
- Quick sanity checks during active development
- Immediate feedback on small changes (1-3 files)
- Rapid validation before staging changes
- Learning and code quality improvement
- No-setup code review (zero configuration)

❌ **Use `code-review-gemini` instead for:**
- Comprehensive security analysis
- Production release validation
- Deep architectural reviews
- Compliance-required audits

---

## Quick Start

### Prerequisites

**None!** This skill uses only Claude Code's built-in capabilities.

### Usage

Simply use one of these trigger phrases:

```
"quick review"
"native review"
"fast code check"
"review with claude"
```

### Example

```
User: "Quick review of my staged changes"

Claude:
## Review Scope
- src/auth.ts (67 lines reviewed)
- src/utils.ts (23 lines reviewed)

## 🔴 High Priority Issues
1. **src/auth.ts:45** - Missing null check on user object
   - **Fix**: Add `if (!user) throw new Error('User not found')`

## 🟡 Medium Priority Issues
1. **src/utils.ts:12** - Function name too generic
   - **Fix**: Rename to `validateEmailFormat`

## Summary
Total files: 2 | High: 1 | Medium: 1 | Low: 0
```

---

## 🚀 Features

### Speed
- ⚡ **< 30 seconds** for typical reviews (1-3 files, ~200 lines)
- No external API calls or network latency
- Instant feedback during development

### Zero Configuration
- 📦 **No dependencies** - works out of the box
- 🔑 **No API keys** required
- 🛠️ **No installation** or setup needed

### Smart Analysis
- 🔍 **Logic errors**: Off-by-one, wrong conditions, edge cases
- 🛡️ **Basic security**: Input validation, error handling
- 📚 **Code quality**: Naming, structure, maintainability
- 🧪 **Testability**: Design issues affecting testing

### Production Ready
- ✅ **Audit score: 93/100**
- ✅ **Zero critical issues**
- ✅ **Comprehensive security documentation**
- ✅ **Well-tested workflow**

---

## 📖 Usage Guide

### Review Staged Changes

```
"Quick review of my staged changes"
```

This reviews all files staged with `git add`. Most common use case.

### Review Specific File

```
"Native review of src/components/Auth.tsx"
```

Reviews a single file, providing targeted feedback.

### Review Last Commit

```
"Quick review of my last commit"
```

Reviews the most recent commit for quality checks.

### Review Code Snippet

```
I just wrote this function, quick review:

function processData(items) {
  return items.map(item => item.value * 2)
              .filter(val => val > 0);
}
```

Reviews provided code directly without file operations.

---

## 🎭 Comparison with tm-code-review-gemini

| Feature | tm-code-review-claude | tm-code-review-gemini |
|---------|----------------------|----------------------|
| **Speed** | ⚡ Immediate (< 30 sec) | 🐢 Slower (1-3 min) |
| **Depth** | 🔍 Rapid validation | 🔬 Comprehensive analysis |
| **Dependencies** | None | Gemini CLI + API key |
| **Setup** | Zero configuration | Requires API setup |
| **Use Case** | Development checks | Pre-commit reviews |
| **Security Focus** | Basic | Advanced |
| **Best For** | Quick iterations | Final validation |
| **Trigger Words** | "quick", "native", "fast" | "detailed", "comprehensive", "gemini" |

### Which One to Use?

**Use `tm-code-review-claude` when:**
- You want immediate feedback (< 30 seconds)
- Working on small changes (1-3 files)
- Don't want to set up external tools
- Doing rapid iteration during development

**Use `tm-code-review-gemini` when:**
- You need comprehensive security analysis
- Preparing for production deployment
- Want deep architectural insights
- Have time for thorough review (1-3 minutes)

**Pro Tip:** Use both sequentially!
1. `quick review` during development for fast feedback
2. `detailed review with gemini` before committing for comprehensive analysis

---

## 📋 Review Categories

### 🔴 High Priority (Must Fix)
- Logic errors (off-by-one, wrong conditions)
- Missing null/undefined checks
- Security issues (XSS, injection, auth bypass)
- Data corruption risks
- Incorrect error handling

### 🟡 Medium Priority (Should Fix)
- Code duplication (DRY violations)
- Poor naming (unclear variables/functions)
- Missing input validation
- Performance concerns (N+1 queries)
- Testability issues

### 🟢 Low Priority (Nice to Have)
- Style consistency
- Comment clarity
- Minor refactoring opportunities
- Documentation improvements

---

## 🛡️ Security Considerations

### What This Skill Does
- ✅ Read-only operations (no code execution)
- ✅ Local analysis (no external API calls)
- ✅ Validates file paths and git commands
- ✅ Sanitizes output to prevent injection

### What This Skill Doesn't Do
- ❌ Execute or evaluate code
- ❌ Store or persist reviewed code
- ❌ Share data with external services
- ❌ Modify files without explicit consent

### Privacy
- All processing happens locally within Claude Code session
- No telemetry or logging of reviewed code
- User maintains full control over code visibility

### Limitations
⚠️ **Important:**
- Provides **suggestions**, not guarantees
- Basic security review - use `tm-code-review-gemini` for comprehensive security
- Does not replace human code review or security audits
- Cannot detect all types of vulnerabilities

---

## 🔧 Troubleshooting

### Issue: Review seems incomplete

**Symptom:** Review doesn't cover all changes or misses obvious issues

**Solution:**
- Be specific about what to review
  - ✅ `"Quick review of src/auth.ts"`
  - ✅ `"Native check on my authentication logic"`
  - ❌ `"Review everything"` (too broad)
- Break large changes into smaller chunks
- Use `detailed review with gemini` for comprehensive analysis

### Issue: No staged changes found

**Symptom:** Error message "No staged changes found"

**Solution:**
```bash
# Stage files first
git add <files>

# Or specify files directly
"Quick review of src/file.ts"
```

### Issue: Want more thorough analysis

**Symptom:** Review is too high-level or misses details

**Solution:**
- Use `tm-code-review-gemini` instead:
  - `"Detailed review with gemini"`
  - `"Comprehensive code review"`
- For specific concerns, ask directly:
  - `"Check security issues in auth.ts"`
  - `"Review performance of data processing logic"`

### Issue: Conflicts with other review skills

**Symptom:** Wrong skill gets triggered

**Solution:**
Use specific trigger words:
- For this skill: `"quick review"` (< 30 sec), `"native review"`
- For Gemini: `"detailed review"` (1-3 min), `"gemini review"`

### Issue: Large changeset warning

**Symptom:** "⚠️ Large changeset detected (>1000 lines)"

**Solution:**
1. Review in smaller chunks - specify individual files
2. Use `tm-code-review-gemini` for large changes
3. Split into multiple commits for easier review

---

## 📊 Review Scope Guidelines

| Change Size | Files | Lines | Fit | Recommended Action |
|-------------|-------|-------|-----|-------------------|
| Small | 1-3 | < 200 | ✅ Perfect | Use tm-code-review-claude |
| Medium | 4-10 | 200-500 | ✅ Good | Use tm-code-review-claude |
| Large | 10+ | 500-1000 | ⚠️ Acceptable | Consider splitting or use gemini |
| Very Large | 10+ | > 1000 | ❌ Too big | Split into smaller commits |

---

## 🎓 Examples

### Example 1: Quick Review Before Staging

```
User: "I just modified auth.ts, can you do a quick review?"

Claude: [Reads src/auth.ts]

## Review Scope
- src/auth.ts (78 lines reviewed)

## 🔴 High Priority Issues
1. **src/auth.ts:45** - Password comparison using `==` instead of secure compare
   - **Risk**: Timing attack vulnerability
   - **Fix**: Use `crypto.timingSafeEqual()` or bcrypt.compare()

## 🟡 Medium Priority Issues
1. **src/auth.ts:67** - Hard-coded token expiry time
   - **Fix**: Move to environment variable `TOKEN_EXPIRY_MS`

## Summary
Total files: 1 | High: 1 | Medium: 1 | Low: 0

## Next Steps
1. Fix password comparison (critical security issue)
2. Extract token expiry to config
```

### Example 2: Review Code Snippet

```
User: "Quick review of this validator:

function validateEmail(email) {
  return email.includes('@');
}
"

Claude:

## 🔴 High Priority Issues
1. **Validation too weak** - Only checks for '@' presence
   - **Risk**: Accepts invalid emails like "@@", "test@", "@domain"
   - **Fix**: Use proper regex or email validation library

   ```javascript
   function validateEmail(email) {
     const emailRegex = /^[^\s@]+@[^\s@]+\.[^\s@]+$/;
     return emailRegex.test(email);
   }
   ```

## 🟡 Medium Priority Issues
1. **No type checking** - Crashes if email is not a string
   - **Fix**: Add type validation:

   ```javascript
   if (typeof email !== 'string') return false;
   ```

## Summary
High: 1 | Medium: 1

This validation is insufficient for production use. Consider using a library like `validator.js` or `email-validator` for robust validation.
```

### Example 3: Review Staged Changes

```
User: "Quick review before I commit"

Claude: [Runs git diff --cached]

## Review Scope
- src/api/users.ts (45 lines changed)
- src/api/auth.ts (23 lines changed)
- tests/api.test.ts (34 lines changed)

## 🔴 High Priority Issues
1. **src/api/users.ts:67** - SQL injection vulnerability
   - Query uses string concatenation: `SELECT * FROM users WHERE id = ${userId}`
   - **Fix**: Use parameterized query: `SELECT * FROM users WHERE id = ?`

## 🟡 Medium Priority Issues
1. **tests/api.test.ts:12** - Test doesn't verify error response format
   - **Fix**: Add assertion for error structure

## 🟢 Low Priority Suggestions
1. **src/api/auth.ts:34** - Consider extracting magic number 3600 to constant
   - **Fix**: `const TOKEN_EXPIRY_SECONDS = 3600`

## Summary
Total files: 3 | High: 1 | Medium: 1 | Low: 1

⚠️ **Do not commit** until SQL injection issue is fixed.
```

---

## 🔗 Related Skills

- **code-review-gemini**: Comprehensive external AI code review
- **pr-review-assistant**: Review pull requests before merging
- **code-story-teller**: Understand code history and evolution

---

## 📈 Roadmap

### Current Version: 1.0.0

**Implemented:**
- ✅ Rapid code review (< 30 seconds)
- ✅ Zero external dependencies
- ✅ Comprehensive security documentation
- ✅ Production-ready quality (93/100 audit score)

**Future Enhancements:**
- 🔄 Auto-fix suggestions with code patches
- 🔄 Integration with git hooks (pre-commit)
- 🔄 Customizable review rules
- 🔄 Review history tracking
- 🔄 Team-shared review templates

---

## 🤝 Contributing

### Feedback

Found an issue or have a suggestion? Please provide feedback on:
- Review quality and accuracy
- Speed and responsiveness
- Output format and clarity
- Missing features or checks

### Reporting Issues

When reporting issues, please include:
1. The trigger phrase used
2. File size and complexity
3. Expected vs actual behavior
4. Example code (if applicable)

---

## 📄 License

Part of the Claude Code Skills repository.

---

## 📚 Documentation

- **Full Skill Definition**: See [SKILL.md](./SKILL.md)
- **Naming Conventions**: See [../NAMING_CONVENTIONS.md](../NAMING_CONVENTIONS.md)
- **Skill Auditor**: Use `tm-skill-auditor` to validate quality

---

## 🏆 Quality Metrics

- **Audit Score**: 93/100 (Excellent)
- **Critical Issues**: 0
- **Production Ready**: ✅ Yes
- **Security Documentation**: ✅ Comprehensive
- **Test Coverage**: ✅ Validated with tm-skill-auditor

---

**Maintainer:** Tom Wang
**Created:** 2026-01-20
**Last Updated:** 2026-01-20
**Version:** 1.0.0

---

<div align="center">

**⚡ Fast • 📦 Zero Dependencies • 🛡️ Secure • 🎯 Production Ready**

</div>
