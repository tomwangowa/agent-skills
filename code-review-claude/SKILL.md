---
name: code-review-claude
description: Use when the user asks for any code review, 'review', 'code review', 'quick review', 'native review', or a fast code check — this is the default reviewer as of 2026-04. Runs native (< 30 s) line-by-line analysis with adversarial pass, assumptions list, syntax-checker-verified syntax findings, and an optional ready-to-apply Refactored Patch. In a 2026-04 benchmark (n=6) this skill produced broader finding coverage than code-review-gemini with 0 verified hallucinations across 6 demos — not a guarantee for future runs.
id: code-review-claude
version: "2.0.0"
tags:
  - code-quality
  - default-reviewer
  - native
  - adversarial
  - refactored-patch
dependencies: []
author: "Tom Wang"
created: "2026-01-20"
updated: "2026-04-20"
---

# Native Code Review with Claude

## Overview

This skill provides immediate, native code review using Claude Code's built-in capabilities. Unlike external AI-based reviews, this skill requires no external dependencies, API keys, or network calls. It's designed for rapid validation checks (< 30 seconds) during active development.

**Key differences from `code-review-gemini`:**
- 🎯 **Role**: Default reviewer (this skill, including pre-commit auto-review) vs. depth / fully-worked refactored-patch (gemini)
- ⚡ **Speed**: Immediate (< 30 seconds) — no external API calls
- 📦 **Dependencies**: None — uses Claude Code's native tools
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
- A fully-worked refactored patch on a small single file (use `code-review-gemini`)
- A second externally-hosted reviewer for cross-checking a claude-review finding

---

## Session Hygiene — Fresh Session vs Same Session

The reviewer's own session context can bias the review. Three known failure modes:

- **Commitment bias** — if the reviewer (you, or a prior Claude turn in this session) just argued for the design, the reviewer is motivated to find it correct.
- **Recency bias** — phrases and numbers already in the current context are disproportionately "available" when generating findings.
- **Framing bias** — the task description that led to the code under review has already anchored the reviewer's frame.

### Decision table

| Scenario | Recommended |
|---|---|
| **Self-review** — reviewing code / docs the current session just produced | **New session.** Bias cost outweighs re-read cost. |
| Reviewing another author's PR, or unrelated code | Same session is fine. |
| Mechanical checks (typos, syntax, obvious bugs) | Same session is fine. Step 3.3 syntax guard is session-independent. |
| High-stakes decision (merge blocker, security-sensitive) | New session **and** also run `code-review-gemini` for cross-check. |

### Middle ground — subagent review in the same session

If a fresh session is too expensive (re-reading the whole repo, re-establishing context), use the `Agent` tool to dispatch a subagent reviewer. The subagent has its own context window and does not see the current session's reasoning chain, but it still inherits the task framing the caller provides. Rank: fresh session > subagent review > direct same-session review.

### Recommended invocation when self-reviewing

When invoking the skill from the same session that produced the code, **state the bias up front** in the prompt to the subagent (or in your own working notes), e.g.:

> "Review the changes to `X.md` below. I just wrote them, so treat my framing with suspicion. Prioritize what I might be over-claiming."

This does not eliminate bias, but it primes the reviewer to apply the adversarial pass (Step 3.5) against the framing, not just against the code.

---

## Trigger Phrases

This skill responds to these natural language phrases:
- "review" (the bare word — routes here as default as of 2026-04)
- "code review" (generic — routes here as default)
- "quick review"
- "native review"
- "fast code check"
- "quick code review"
- "review with claude"
- "claude code review"
- "check my changes quickly"
- "fast validation"

**Note:** As of 2026-04, the bare word "review" and generic "code review" default to THIS skill (including pre-commit auto-review). Route to `code-review-gemini` with "gemini review", "thorough review", "deep review", "detailed review", or "refactored patch".

---

## Instructions

When the user requests a native/quick code review, follow this workflow strictly:

### Step 0: Self-Review Detection

**Before identifying review scope, check for self-review bias.**

Scan the current conversation history for `Edit` / `Write` / `NotebookEdit` tool calls. If any of those calls targeted a file that will fall within the review scope (determined in Step 1 below — for staged/working-tree reviews, any edited file in the session almost certainly qualifies), **this is a self-review** and the three bias modes in the "Session Hygiene" section above apply.

**When self-review is detected, STOP and state:**

```
⚠️ SELF-REVIEW DETECTED

This session already edited files in the review scope:
  - <file 1>
  - <file 2>
  ...

Reviewing in the same context risks commitment / recency / framing bias.
How would you like to proceed?

  (a) Open a fresh session and re-invoke — recommended for non-trivial self-review
  (b) Dispatch a subagent to run the review in an isolated context — middle ground
  (c) Continue in this session with an explicit bias warning attached to findings
```

**Wait for the user's choice before continuing.** Do not assume (c) as default.

**Exemption — pre-commit auto-review context.** When this skill is invoked as part of the pre-commit auto-review rule (user's preceding message asked to commit, or the invocation was triggered automatically by the CLAUDE.md pre-commit rule — signals include "commit", "commit and push", "ready to commit", "要 commit 嗎", "是否要提交"), **do not ask for choice (a)/(b)/(c)**. Auto-select (c) silently: prepend the bias warning to the final report and proceed to Step 1. Reason: a pre-commit review is almost always self-review by definition (the user just wrote the code they're about to commit); asking every time creates friction without new information. The bias warning in the report is sufficient disclosure.

- On **(a)**: end the skill invocation; the user will open a fresh session themselves.
- On **(b)**: invoke the `Agent` tool (subagent_type: `general-purpose`) with a self-contained prompt containing the review scope, the SKILL.md rules, and instruction: "You are reviewing code produced in another session. Treat the author's framing with suspicion. Prioritize what they might be over-claiming." Return the subagent's findings directly.
- On **(c)**: proceed with Step 1, and prepend to the final report: "⚠️ Self-review in same session — commitment / recency / framing bias not controlled."

**When no self-review is detected,** skip this disclosure and proceed to Step 1 silently.

**Edge cases:**
- Session started with files already modified (e.g. user passed a diff in the opening message and edits came from a different AI / human): no Edit/Write tool calls from this session → not flagged. This is correct behavior; bias only applies to authorship within the current reasoning chain.
- User is reviewing someone else's code that they happened to open and read: Read-only traffic does not trigger detection.
- Review scope is narrower than what was edited (e.g. edited 5 files, user asks to review only 1 unchanged file): check intersection, not the full edit set.

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

### Step 3.3: Hallucination Guard for Syntax / Whitespace / Character-class Findings

**MANDATORY before claiming any of the following finding types:**

- "Syntax error" / "will not run" / "will not parse" / "invalid syntax"
- "Indentation error" / "wrong leading whitespace"
- Extra/missing whitespace inside an identifier, string, regex, or parameter expansion
- Regex character class reading (e.g., `[^\s@]` misread as `\s` + `@`)
- "Malformed" / "fatal" / "critical" claims about tokens the human eye easily misreads

**Why this step exists:** A 6-language benchmark (2026-04) found that 3/6 runs of an external reviewer produced P0/P1 hallucinations in exactly these categories — all three would have caused the developer to break working code if trusted. This guard eliminates that failure mode for code-review-claude.

**Procedure — for each candidate finding of the above types, do ALL of the following before listing it:**

0. **Check Bash availability first.** If the Bash tool has been denied, unavailable, or returns a permission error in this session, stop — mark every syntax-class candidate finding `[UNVERIFIED-SYNTAX]` and downgrade severity to Medium. Do not continue to steps 1-5 below for those findings. State in the output: "Bash unavailable in this session — syntax-class findings not checker-verified."

1. **Re-read the exact line** with the Read tool, noting the *character-level* contents (not your memory of it).
2. **Run the language-matched syntax checker** via Bash. Do not skip this step; do not substitute "I looked carefully":

   | Language / File | Verification command |
   |-----------------|----------------------|
   | Python (`.py`) | `python3 -c "import ast; ast.parse(open('FILE').read())"` |
   | Bash / Shell (`.sh`, `.bash`) | `bash -n FILE` |
   | JavaScript / Node (`.js`, `.mjs`, `.cjs`) | `node --check FILE` |
   | TypeScript / TSX (`.ts`, `.tsx`) | `npx --no tsc --noEmit --allowJs FILE` (or skip if no TS toolchain; fall back to careful Read) |
   | Java (`.java`) | `javac -d /tmp FILE` (or fall back to Read if no JDK) |
   | PHP (`.php`) | `php -l FILE` |
   | Go (`.go`) | `gofmt -e FILE >/dev/null` |
   | Ruby (`.rb`) | `ruby -c FILE` |
   | JSON | `python3 -m json.tool FILE >/dev/null` or `jq empty FILE` |
   | YAML | `python3 -c "import yaml,sys; yaml.safe_load(open('FILE'))"` |

   If the language has no quick local checker available, state that explicitly and downgrade severity to "potential" instead of "will not run".

3. **Regex-class findings** — if claiming a regex has an unintended space or broken class:
   - Print the exact bytes: `python3 -c "import sys; s=open('FILE').read().split('\n')[LINE-1]; print(repr(s))"`
   - Verify the character class with Python's `re` module, e.g., `python3 -c "import re; print(re.match(r'PATTERN', 'TEST_STRING'))"`.

4. **Only list the finding if the checker fails AND the failure reason matches your claim.** If the checker passes, either drop the finding entirely or reclassify it (e.g., "style concern" instead of "syntax error").

5. **If listed, append the verification evidence inline**, e.g.:
   > `bash -n fetch_with_retry.sh` → exit code 2: `syntax error near unexpected token '&&'`

**Downgrade rule:** If step 2 fails to run (toolchain missing), cap severity of syntax-class findings at Medium, and mark them with `[UNVERIFIED-SYNTAX]` so the reader knows they are not checker-confirmed.

### Step 3.4: Language-specific Checklist Sweep

Before running Step 3.5 (Adversarial), consult `references/language-checklists.md` (in this skill directory) for checks specific to the primary language(s) of the diff. These checklists encode known gaps that are easy to miss (e.g., Python `body` param dispatch, JS socket-idle timeout vs overall timeout, Shell `&& true` suppression). Apply relevant items as additional findings. Skip items that clearly don't apply.

### Step 3.5: Adversarial Quick Check

After categorizing findings, run this 4-item checklist against every function or change in the diff:

- [ ] **Assumption exposed?** — Does the code assume something about input, environment, or ordering that is not validated? If yes, note the assumption.
- [ ] **Mirror test?** — Would any test in the diff still pass if the implementation were deleted or replaced with a no-op? If yes, the test is a tautology.
- [ ] **Suppression, not fix?** — Does the change silence an error rather than address its root cause (e.g., catch-and-swallow, `|| default`, `@SuppressWarnings`)?
- [ ] **What breaks this?** — Can you name one concrete input or state that would cause unexpected behavior?

If any item triggers, add it as an `[ADVERSARIAL]` finding. If none trigger, state: "Adversarial quick check: no issues found."

### Step 3.6: Assumptions List

After the adversarial pass, emit an **Assumptions Identified** list — explicit or implicit contracts the code relies on but does not validate (e.g., "`body` is `dict | str | None`, not `bytes`"; "`max_retries >= 0`"; "`fetch` response body fits in memory"). This complements the adversarial findings by making risks visible even when no concrete exploit was named.

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

## [ADVERSARIAL] Findings
1. **file1.ts:67** - [ADVERSARIAL] What breaks this? — concrete input causing unexpected behavior

## Assumptions Identified
- Input `user` is never null
- `data` array is non-empty

## Summary
- Total files reviewed: 2
- High priority issues: 1
- Medium priority issues: 1
- Low priority suggestions: 1
- Adversarial findings: 1
- Assumptions: 2

## Actionable Next Steps
1. Fix null check in file1.ts:67
2. Rename function in file2.ts:34
3. Optional: Extract validation logic
```

### Step 4.5: Refactored Patch (optional, at end)

After the findings block, emit a **Refactored Patch** section — a ready-to-apply rewrite of the reviewed code that addresses the High and Medium findings. This compensates for the historical gap where external reviewers were the only ones producing patches.

**Rules:**

- **Only when the diff fits the review budget.** Emit a patch when the total reviewed content is ≤ ~200 lines or ≤ 3 files. For larger scopes, emit a per-file patch only for the file with the highest High-severity count and note "patches for other files available on request".
- **Only fix what was listed.** Do not introduce new features, new abstractions, or stylistic changes unrelated to findings.
- **Use the same language, version, imports, and style** as the original file.
- **Do not include Low-priority or speculative changes** unless trivial (one-token renames, etc.).
- **If Step 3.3 flagged any finding as `[UNVERIFIED-SYNTAX]`, do NOT apply that change in the patch** — keep it in the findings list only.
- **Label the block clearly** so readers know it is optional.

Format:

```markdown
## Refactored Patch (optional)

> Applies the High + Medium findings above. Review before accepting; does not implement Low-priority suggestions.

### `path/to/file.ext` — full revised file

```<LANG>
<complete revised source, preserving license headers, import style, indentation convention>
```
```

For diff-style patches on larger files, use unified-diff format instead of full rewrites.

**Skip conditions:** skill invoked with `patch=no`, or reviewing a snippet (not a file), or reviewing code the user explicitly said "don't change yet" / "read-only review".

### Step 5: Validate Output
Before presenting to user:
- ✅ All line numbers are accurate (verified against the file content you read)
- ✅ All file paths are correct
- ✅ All issues map to reviewed code
- ✅ Fixes are specific and actionable
- ✅ No speculative or unrelated suggestions
- ✅ **Every syntax-error-class claim was checker-verified per Step 3.3** (or labeled `[UNVERIFIED-SYNTAX]` + downgraded)
- ✅ Adversarial + Assumptions sections present (or explicitly stated "no issues found")
- ✅ Refactored Patch (if emitted) only implements listed findings; does not add new features; does not apply any `[UNVERIFIED-SYNTAX]` changes

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

## Comparison with code-review-gemini

Based on a 6-language benchmark (2026-04) comparing both reviewers on the same HTTP retry client in Java, TypeScript, PHP, JavaScript, Python, and Shell:

| Feature | code-review-claude (this skill) | code-review-gemini |
|---------|---------------------------------|--------------------|
| **Role** | **Default reviewer** (incl. pre-commit auto-review) | Depth + fully-worked refactored patch |
| **Speed** | ⚡ < 30 seconds | 🐢 1–2 minutes (external API) |
| **Dependencies** | None (native Claude tools) | Gemini CLI + API key |
| **Finding count** | **2.3×–5.0× gemini's count** across 6 demos | baseline |
| **Hallucination rate** | 0/6 (zero verified) | 3/6 = 50%, all P0/P1, all in whitespace/char-class |
| **Adversarial pass** | ✅ Built in (4-check adversarial + assumptions list) | ❌ Not included |
| **Assumptions list** | ✅ Emitted after adversarial pass | ❌ Not included |
| **Refactored patch** | ✅ Optional Step 4.5, size-gated | ✅ Always emitted |
| **Syntax-claim guard** | ✅ Mandatory syntax-checker verification (Step 3.3) | ❌ None — source of the 50% hallucination rate |
| **Language-specific checklists** | ✅ `references/language-checklists.md` | ❌ Generic prompt |
| **Best for** | Default use; broad discovery; any iteration; **pre-commit auto-review (per CLAUDE.md)** | Depth pass / second opinion; when a fully-written patch is required |
| **Trigger words** | "review", "code review", "quick", "native", "fast" | "detailed", "thorough", "gemini", "deep review", "refactored patch" |

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

## [ADVERSARIAL] Findings
1. [file:line] - [ADVERSARIAL] Assumption exposed / Suppression / Mirror test / What breaks this?
   (or: "Adversarial quick check: no issues found.")

## Assumptions Identified
- [Unvalidated contract 1]
- [Unvalidated contract 2]

## Summary
- Files reviewed: X
- High: Y, Medium: Z, Low: W, Adversarial: A, Assumptions: B

## Actionable Next Steps
1. Fix critical issue at [location]
2. Consider improving [aspect]
3. Optional: [enhancement]

## Refactored Patch (optional — only if diff ≤ ~200 lines / ≤ 3 files)
> Applies High + Medium findings above. Skipped if `[UNVERIFIED-SYNTAX]` findings would be touched, or if the user requested read-only review.

### `path/to/file.ext` — full revised file
```<LANG>
<complete revised source>
```
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
- Security-critical code (use `code-review-gemini`)
- Production release validation (use `code-review-gemini`)
- Large-scale architectural reviews involving >10 files or >500 lines (use manual review or `code-review-gemini`)
- Compliance-required audits (use `code-review-gemini`)

### Review Scope Guidelines
- **Small changes** (1-3 files, <200 lines): Perfect fit; Refactored Patch block will be emitted
- **Medium changes** (4-10 files, 200-500 lines): Findings are still reliable; patch block switches to per-file diffs or is skipped
- **Large changes** (>10 files, >500 lines): Findings remain useful but consider splitting the review scope or running `code-review-gemini` in parallel for a fully worked patch on a single hot-spot file

---

## Constraints

### What This Skill Will Do
- Analyze code logic and structure
- Identify common bugs and anti-patterns
- Suggest improvements for readability and maintainability
- Check for basic error handling issues
- Validate best practices for the language

### What This Skill Won't Do
- Deep security vulnerability analysis (use `code-review-gemini`)
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
- Security review is **basic** - use `code-review-gemini` for comprehensive security analysis
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
- Security-critical authentication/authorization code (use `code-review-gemini`)
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
2. Use detailed review: invoke code-review-gemini
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
**Solution:** Use `code-review-gemini` instead:
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
- More thorough security analysis → Use `code-review-gemini`
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
|  |  | Complementary to code-review-gemini |

---

**Maintainer:** Tom Wang
**Created:** 2026-01-20
**Last Updated:** 2026-01-20
