---
name: code-review-claude
description: Perform native code review (< 30 seconds) using Claude Code's built-in capabilities without external dependencies. Use for rapid validation checks during development. Triggered by 'quick review', 'native review', or 'fast code check'.
id: code-review-claude
version: "1.0.0"
tags:
  - code-quality
  - fast-review
  - native
  - validation
dependencies: []
author: "Tom Wang"
created: "2026-01-20"
updated: "2026-01-20"
---

# Native Code Review with Claude

## Overview

This skill provides immediate, native code review using Claude Code's built-in capabilities. Unlike external AI-based reviews, this skill requires no external dependencies, API keys, or network calls. It's designed for rapid validation checks (< 30 seconds) during active development.

**Key Differences from tm-code-review-gemini:**
- ⚡ **Speed**: Immediate (< 30 seconds) - no external API calls
- 📦 **Dependencies**: None - uses Claude Code's native capabilities
- 🎯 **Use Case**: Rapid checks during development vs. comprehensive pre-commit analysis
- 🔑 **Setup**: Zero configuration required

---

## When to Use

Use this skill when you want:
- **Rapid validation** (< 30 seconds) of code changes during active development
- **Immediate feedback** without waiting for external API calls
- **Code review without setup** - no API keys or external tools needed
- **Instant insights** on logic, structure, and potential issues
- **Lightweight checks** before running more comprehensive reviews

**Don't use this skill when you need:**
- Comprehensive security analysis (use `tm-code-review-gemini` instead)
- Deep architectural review (use `tm-code-review-gemini` instead)
- Detailed performance profiling (use `tm-code-review-gemini` instead)

---

## Trigger Phrases

This skill responds to these natural language phrases:
- "quick review"
- "native review"
- "fast code check"
- "quick code review"
- "review with claude"
- "claude code review"
- "check my changes quickly"
- "fast validation"

**Note:** Generic phrases like "review the code" or "check code quality" will default to `tm-code-review-gemini` for more comprehensive analysis.

---

## Instructions

When the user requests a native/quick code review, follow this workflow strictly:

### Step 1: Identify Review Scope
1. Ask user what to review if not specified:
   - Staged changes? (default)
   - Specific file(s)?
   - Recent commit(s)?
   - Working directory changes?

2. Use the corresponding tool to identify files:
   ```bash
   git diff --cached --name-only  # for staged changes
   git diff HEAD~1 --name-only    # for last commit
   ```

### Step 2: Collect Code Context
1. **Read each file** in the review scope using the Read tool
2. **Note line numbers** for reference in findings
3. **Search for patterns** if needed using Grep:
   - Error handling patterns
   - Security-sensitive functions (auth, validation)
   - Common anti-patterns

### Step 3: Analyze Code Quality
Review the code for these aspects in priority order:

**🔴 High Priority (Must Fix):**
- Logic errors (off-by-one, wrong conditions, null pointer)
- Missing null/undefined checks
- Incorrect error handling or missing try-catch
- Security issues (XSS, injection, auth bypass)
- Data corruption risks

**🟡 Medium Priority (Should Fix):**
- Code duplication (DRY violations)
- Poor naming (unclear variable/function names)
- Missing input validation
- Performance concerns (N+1 queries, memory leaks)
- Testability issues

**🟢 Low Priority (Nice to Have):**
- Style consistency
- Comment clarity
- Minor refactoring opportunities
- Documentation improvements

### Step 4: Generate Review Output
Present findings in this exact format:

```markdown
## Review Scope
- file1.ts (123 lines reviewed)
- file2.ts (45 lines reviewed)

## 🔴 High Priority Issues
1. **file1.ts:67** - Missing null check on `user` object before accessing `user.email`
   - **Fix**: Add `if (!user) throw new Error('User not found')`

## 🟡 Medium Priority Issues
1. **file2.ts:34** - Function name `process` is too generic
   - **Fix**: Rename to `processUserData` for clarity

## 🟢 Low Priority Suggestions
1. **file1.ts:45** - Consider extracting validation logic to separate function
   - **Fix**: Create `validateUserInput(input)` helper

## Summary
- Total files reviewed: 2
- High priority issues: 1
- Medium priority issues: 1
- Low priority suggestions: 1

## Actionable Next Steps
1. Fix null check in file1.ts:67
2. Rename function in file2.ts:34
3. Optional: Extract validation logic
```

### Step 5: Validate Output
Before presenting to user:
- ✅ All line numbers are accurate
- ✅ All file paths are correct
- ✅ All issues map to reviewed code
- ✅ Fixes are specific and actionable
- ✅ No speculative or unrelated suggestions

---

## Workflow Summary

### Step 1: Identify Changes
1. Determine what code to review:
   - Staged changes (`git diff --cached`)
   - Recent commits
   - Specific files mentioned by user
   - Working directory changes

### Step 2: Read and Analyze
1. Use Read tool to examine the changed files
2. Use Grep/Glob to understand context if needed
3. Analyze code for:
   - **Logic errors**: Off-by-one errors, wrong conditions, edge cases
   - **Code structure**: Readability, naming, organization
   - **Best practices**: Language-specific conventions
   - **Potential bugs**: Null checks, error handling, type issues
   - **Maintainability**: Duplication, complexity, testability

### Step 3: Prioritize Findings
Categorize findings by severity:
- **🔴 High Priority**: Logic errors, potential crashes, data corruption
- **🟡 Medium Priority**: Code smells, maintainability issues, minor bugs
- **🟢 Low Priority**: Style suggestions, naming improvements, minor refactoring

### Step 4: Present Results
1. Show **Review Scope** (files and lines reviewed)
2. List findings by priority
3. Provide specific line references (file_path:line_number)
4. Suggest concrete fixes
5. Keep response concise and actionable

---

## Requirements

### Dependencies
**None** - This skill uses only Claude Code's native tools:
- Read tool (for file content)
- Grep/Glob tools (for code search)
- Bash tool (for git commands)

### Environment
- Must be in a git repository (for staged changes review)
- No API keys or external tools required

---

## Examples

### Example 1: Quick Review of Staged Changes

**User Input:**
```
Quick review of my staged changes
```

**Expected Behavior:**
1. Run `git diff --cached` to see staged files
2. Read each staged file
3. Analyze changes for logic errors, code quality issues
4. Present prioritized findings:

```
Review Scope: 3 files staged
- src/auth/login.ts (45 lines changed)
- src/utils/validator.ts (12 lines changed)
- tests/auth.test.ts (28 lines changed)

🔴 High Priority Issues:
1. src/auth/login.ts:67 - Missing null check on user object before accessing user.email
2. src/utils/validator.ts:34 - Regex pattern allows empty strings, should validate length

🟡 Medium Priority:
1. src/auth/login.ts:45 - Error not logged before throwing, may be hard to debug
2. tests/auth.test.ts:12 - Test case missing assertion for error message

🟢 Low Priority:
1. src/utils/validator.ts:22 - Function name 'validate' is too generic, consider 'validateEmail'

Actionable Next Steps:
1. Add null check: if (!user) throw new Error('User not found')
2. Update regex: /^.+@.+\..+$/ and add length validation
3. Add error logging before throw statements
```

### Example 2: Fast Check on Specific File

**User Input:**
```
Native review of src/api/handler.ts
```

**Expected Behavior:**
1. Read `src/api/handler.ts`
2. Analyze the file content
3. Provide quick feedback on code quality, potential issues

### Example 3: Quick Validation During Development

**User Input:**
```
I just wrote this function, can you do a fast code check?

function processData(data) {
  const result = data.map(item => item.value * 2);
  return result.filter(val => val > 0);
}
```

**Expected Behavior:**
1. Analyze the provided code snippet
2. Identify issues:
   - Missing type safety
   - No error handling for invalid data
   - No validation that `item.value` exists
3. Suggest improvements with examples

---

## Comparison with tm-code-review-gemini

| Feature | tm-code-review-claude | tm-code-review-gemini |
|---------|----------------------|----------------------|
| **Speed** | ⚡ Immediate (< 30 seconds) | 🐢 Slower (1-3 minutes, API calls) |
| **Depth** | 🔍 Rapid validation | 🔬 Comprehensive analysis |
| **Dependencies** | None | Gemini CLI + API key |
| **Use Case** | Development checks | Pre-commit reviews |
| **Security Focus** | Basic | Advanced |
| **Best For** | Quick iterations | Final validation |
| **Trigger Words** | "quick", "native", "fast" | "detailed", "comprehensive", "gemini" |

---

## Output Format

### Standard Output Structure

```markdown
## Review Scope
- File 1 (X lines reviewed)
- File 2 (Y lines reviewed)

## 🔴 High Priority Issues
1. [file:line] - Description and suggested fix

## 🟡 Medium Priority Issues
1. [file:line] - Description and suggested fix

## 🟢 Low Priority Suggestions
1. [file:line] - Description and suggested fix

## Summary
- Total files reviewed: X
- High priority issues: Y
- Medium priority issues: Z
- Low priority suggestions: W

## Actionable Next Steps
1. Fix critical issue at [location]
2. Consider improving [aspect]
3. Optional: [enhancement]
```

---

## Best Practices

### When to Use This Skill
✅ **Use for:**
- Rapid sanity checks during development (< 30 seconds)
- Immediate validation of small changes (1-3 files)
- Instant feedback on code logic
- Learning and improving code quality
- Pre-staging validation (before `git add`)

❌ **Don't use for:**
- Security-critical code (use `tm-code-review-gemini`)
- Production release validation (use `tm-code-review-gemini`)
- Large-scale architectural reviews involving >10 files or >500 lines (use manual review or `tm-code-review-gemini`)
- Compliance-required audits (use `tm-code-review-gemini`)

### Review Scope Guidelines
- **Small changes** (1-3 files, <200 lines): Perfect fit
- **Medium changes** (4-10 files, 200-500 lines): Well-suited for this skill
- **Large changes** (>10 files, >500 lines): Consider splitting or using `tm-code-review-gemini`

---

## Constraints

### What This Skill Will Do
- Analyze code logic and structure
- Identify common bugs and anti-patterns
- Suggest improvements for readability and maintainability
- Check for basic error handling issues
- Validate best practices for the language

### What This Skill Won't Do
- Deep security vulnerability analysis (use `tm-code-review-gemini`)
- Performance profiling or benchmarking
- Automated testing or test generation
- Large-scale architectural review
- Guarantee bug-free code

---

## Security Considerations

### Code Review Safety

This skill performs read-only operations during code review:
- **No code execution**: Never executes the code being reviewed
- **No external API calls**: All analysis happens locally within Claude Code
- **No data persistence**: Review results are only shown to the user, not stored
- **No file modifications**: Cannot alter code without explicit user consent

### Input Handling

1. **File Path Validation**
   - Validates all file paths before reading
   - Rejects paths with directory traversal patterns (`../`, `..\\`)
   - Only reads files within the git repository boundary
   - No symbolic link following outside repository

2. **Git Command Safety**
   - Uses read-only git commands (`git diff`, `git log`, `git status`)
   - No destructive operations (`git reset`, `git clean`, `git push --force`)
   - All git commands executed with proper shell quoting
   - Validates git repository before executing commands

3. **Code Content Analysis**
   - Reviews code patterns and logic without execution
   - Does not evaluate or run user-provided code snippets
   - Sanitizes code excerpts in output (no script injection)
   - No `eval()` or dynamic code execution

### Sensitive Information Handling

1. **Credentials and Secrets**
   - Warns if API keys, passwords, or tokens detected in code
   - Recommends using environment variables instead of hardcoded secrets
   - Suggests adding sensitive files to `.gitignore`
   - Does not store or transmit sensitive information

2. **Personal Information**
   - Does not persist any personal information from code
   - Review results are ephemeral (user session only)
   - No telemetry or logging of reviewed code

3. **Privacy**
   - All processing happens locally within Claude Code session
   - No external data sharing or API calls
   - User maintains full control over code visibility

### XSS and Injection Prevention

1. **Output Sanitization**
   - All code snippets in review output are properly escaped
   - No raw HTML injection in markdown output
   - Line numbers and file paths validated before display
   - No script tags or dangerous protocols in output

2. **Command Injection Prevention**
   - All shell commands use proper quoting and escaping
   - No user input directly interpolated into bash commands
   - Git commands use `--` separator for path arguments
   - No `eval` or dynamic command construction

### Limitations and Disclaimers

⚠️ **Important Disclaimers:**
- This skill provides **suggestions**, not guarantees of bug-free code
- Security review is **basic** - use `tm-code-review-gemini` for comprehensive security analysis
- Does not replace human code review or security audits
- Cannot detect all types of vulnerabilities or logic errors
- No warranty or liability for missed issues

### Safe Usage Guidelines

✅ **Safe to review:**
- Local development code
- Open source projects
- Team collaboration repositories
- Educational or learning projects

⚠️ **Use caution with:**
- Security-critical authentication/authorization code (use `tm-code-review-gemini`)
- Cryptographic implementations (requires specialized review)
- Payment processing logic (requires compliance review)
- Production-critical systems (requires comprehensive audit)

❌ **Do not rely solely on this skill for:**
- Security vulnerability assessment
- Compliance audits (SOC2, HIPAA, PCI-DSS)
- Production deployment approvals
- Legal or regulatory code reviews

---

## Error Handling

### No Staged Changes
If user requests review of staged changes but none exist:
```
No staged changes found.

Options:
1. Stage files: git add <files>
2. Review specific files: "quick review of src/file.ts"
3. Review recent commits: "quick review of last commit"
```

### File Not Found
If user specifies a file that doesn't exist:
```
File not found: src/missing.ts

Did you mean:
- src/missing-file.ts
- src/components/missing.tsx
```

### Large Changeset
If changes exceed recommended scope (>1000 lines):
```
⚠️ Large changeset detected (1500 lines across 15 files)

Recommendations:
1. Review in smaller chunks: specify individual files
2. Use detailed review: invoke tm-code-review-gemini
3. Split into multiple commits for easier review
```

---

## Troubleshooting

### Issue: Review seems incomplete
**Solution:** Be specific about what to review:
- ✅ "Quick review of src/auth.ts"
- ✅ "Native check on my authentication logic"
- ❌ "Review everything" (too broad)

### Issue: Want more thorough analysis
**Solution:** Use `tm-code-review-gemini` instead:
- "Detailed review with gemini"
- "Comprehensive code review"

### Issue: Conflicts with other review skills
**Solution:** Use specific trigger words:
- For this skill: "quick review" (< 30 sec), "native review"
- For Gemini: "detailed review" (1-3 min), "gemini review"

---

## Related Skills

- **code-review-gemini**: Comprehensive external AI code review
- **pr-review-assistant**: Review pull requests before merging

---

## Feedback and Improvements

This skill is designed to be lightweight and fast. If you need:
- More thorough security analysis → Use `tm-code-review-gemini`
- Architectural review → Use manual review or specialized tools
- Performance profiling → Use language-specific profilers

**Want to improve this skill?** Provide feedback on:
- Review quality and accuracy
- Speed and responsiveness
- Output format and clarity
- Missing features or checks

---

## Version History

| Version | Date | Changes |
|---------|------|---------|
| 1.0.0 | 2026-01-20 | Initial release |
|  |  | Fast native code review using Claude Code |
|  |  | Zero external dependencies |
|  |  | Complementary to tm-code-review-gemini |

---

**Maintainer:** Tom Wang
**Created:** 2026-01-20
**Last Updated:** 2026-01-20
