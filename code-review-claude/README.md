# Claude Code Native Review

<div align="center">

**⚡ Claude Code native reviewer — adversarial pass and syntax verification**

[![Production Ready](https://img.shields.io/badge/status-default%20reviewer-brightgreen)]()
[![Benchmark](https://img.shields.io/badge/2026--04%20benchmark-n%3D6-blue)]()
[![Hallucinations](https://img.shields.io/badge/hallucinations-0%2F6-brightgreen)]()
[![Speed](https://img.shields.io/badge/speed-%3C%2030%20seconds-blue)]()

</div>

---

## 🎯 Purpose

Native code reviewer for Claude Code. Runs inside the Claude Code session — no API keys or external calls — and produces a structured findings report with an adversarial quick check and an assumptions list. In Codex, use `code-review-codex` instead.

### When to Use This Skill

✅ **Use in Claude Code:**
- Daily development review of staged / unstaged changes
- Pre-commit auto-review in Claude Code
- Specific file, recent commit, or pasted snippet
- Self-review after writing code (Step 0 auto-detects self-review bias)

For security- or compliance-critical code, obtain qualified specialist review. `code-review-gemini` is deprecated and must not be used.

---

## Quick Start

### Prerequisites

**None.** This skill uses only Claude Code's built-in Read / Grep / Bash tools.

### Usage

Trigger phrases route to this skill by default:

```
"review"
"code review"
"review my changes"
"quick review"
"native review"
```

In Codex, generic review routes to `code-review-codex`. A future external reviewer requires an explicit model choice and approval of the exact diff or data scope.

### Example

```
User: "review my staged changes"

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

## [ADVERSARIAL] Findings
1. **src/auth.ts:45** - [ADVERSARIAL] What breaks this? —
   calling with `user=undefined` crashes before reaching the null check

## Assumptions Identified
- `user` is never null when `getProfile` is called
- `config.tokenExpiry` is a positive integer

## Summary
Files: 2 | High: 1 | Medium: 1 | Adversarial: 1 | Assumptions: 2
```

---

## 🚀 What it does

### Workflow (see SKILL.md for the exact steps)

- **Step 0 — Self-review detection** — If this session just edited files in the review scope, it either asks how to proceed (fresh session / subagent / warning-and-continue) or, under the pre-commit auto-review rule, silently prepends a bias warning and continues.
- **Step 3.3 — Hallucination guard** — Before claiming any syntax / whitespace / regex / character-class finding, mandatorily runs a language-matched syntax checker (`python3 -c ast.parse`, `bash -n`, `node --check`, `php -l`, `gofmt -e`, `ruby -c`, `jq empty`, …). If the checker passes, the finding is dropped or reclassified. If Bash is unavailable, syntax-class findings get `[UNVERIFIED-SYNTAX]` and capped severity.
- **Step 3.4 — Language-specific checklists** — Consults `references/language-checklists.md` for known-gap patterns the benchmark exposed (Python `body` dispatch, JS socket-idle vs overall timeout, Shell `&& true` suppression, etc.).
- **Step 3.5 — Adversarial quick check** — Applies a 4-item checklist per function / change: Assumption exposed? / Mirror test? / Suppression not fix? / What breaks this?
- **Step 3.6 — Assumptions Identified** — Emits the unvalidated contracts the code relies on (input shape, ordering, size limits).
- **Step 4.5 — Refactored Patch (optional)** — Diff ≤ ~200 lines / ≤ 3 files → ready-to-apply rewrite. Never applies `[UNVERIFIED-SYNTAX]` findings.

### Zero configuration

- 📦 No external dependencies
- 🔑 No API keys
- 🛠️ No installation beyond having the skill file in `~/.claude/skills/`

---

## 📖 Usage Guide

### Review staged changes

```
"review my staged changes"
```

Reviews all files staged with `git add`. This is the default pre-commit auto-review path.

### Review a specific file

```
"review src/components/Auth.tsx"
```

### Review a recent commit

```
"review the last commit"
```

### Review a pasted snippet

```
I just wrote this function, review it:

function processData(items) {
  return items.map(item => item.value * 2)
              .filter(val => val > 0);
}
```

---

## 🎭 Historical benchmark context

| Feature | code-review-claude (this skill) | code-review-gemini (retired) |
|---|---|---|
| **Role** | **Claude Code native reviewer** | Historical external reviewer |
| **Speed** | < 30 s (native, no API) | 1–2 min (external Gemini CLI) |
| **Dependencies** | None | Gemini CLI + `GEMINI_API_KEY` |
| **Finding coverage (2026-04 benchmark)** | **2.3×–5.0× Gemini's count** across 6 language demos | Baseline |
| **Verified hallucinations (2026-04 benchmark)** | **0 / 6** | 3 / 6, all P0/P1, all in whitespace / char-class |
| **Syntax-checker verification** | ✅ Mandatory Step 3.3 | ❌ None — source of the hallucination rate |
| **Adversarial quick check** | ✅ Step 3.5 | ❌ |
| **Assumptions list** | ✅ Step 3.6 | ❌ |
| **Language-specific checklists** | ✅ `references/language-checklists.md` | ❌ |
| **Refactored patch** | ✅ Optional Step 4.5, size-gated | ✅ Always emitted |
| **Status** | Active in Claude Code | Deprecated; do not invoke |

### Benchmark context (2026-04, n=6)

Six HTTP retry clients in Java / Python / JS / TS / PHP / Shell were reviewed by both skills head-to-head. Claude produced broader finding coverage in all six languages with zero verified hallucinations; Gemini hallucinated P0/P1 syntax issues in three of six runs (whitespace-in-regex false positives), each of which would have broken working code if trusted. Not a guarantee for all future runs — but enough evidence to flip the default.

### Which one, when?

| Situation | Use |
|---|---|
| Generic review in Claude Code | `code-review-claude` |
| Generic review in Codex | `code-review-codex` |
| Pre-commit auto-review | Native reviewer of the active runtime |
| Compliance / security-critical last-mile check | Qualified human or specialist review |

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

### `[ADVERSARIAL]` Findings
Findings surfaced by the Step 3.5 checklist. Often catch the "code looks right but assumes X" bugs that don't fall into the standard categories.

### Assumptions Identified
Unvalidated contracts the code relies on — useful even when no concrete exploit is named, because they tell the next maintainer where the implicit ground is.

---

## 🛡️ Security Considerations

### What This Skill Does
- ✅ Read-only operations — never executes the code being reviewed
- ✅ Local analysis — no external API calls, no network
- ✅ Validates file paths and uses read-only git commands
- ✅ Sanitizes output to prevent injection

### Limitations
⚠️ Provides **suggestions**, not guarantees. Benchmark n=6 is encouraging but not a universal proof. Security-critical code still warrants qualified human review.

---

## 🔧 Troubleshooting

### Review seems incomplete

**Solution:** Be specific about scope. `"review src/auth.ts"` is better than `"review everything"`.

### No staged changes found

```bash
git add <files>          # stage first
# or
"review src/file.ts"     # specify file directly
```

### Want a refactored patch on a single file

`code-review-claude` emits a Refactored Patch only when the diff is ≤ ~200 lines and ≤ 3 files. For larger changes, split the review scope or obtain qualified specialist review.

### Large changeset warning

```
⚠️ Large changeset detected (>1000 lines)
```

**Solution:** split the commits, review files individually, or obtain qualified specialist review for a hot-spot file.

---

## 📊 Review Scope Guidelines

| Change size | Files | Lines | Fit | Action |
|---|---|---|---|---|
| Small | 1–3 | < 200 | ✅ Perfect | Use as-is; Refactored Patch emitted |
| Medium | 4–10 | 200–500 | ✅ Good | Findings reliable; patch switches to per-file diff or skipped |
| Large | 10+ | 500–1000 | ⚠️ OK | Consider splitting or qualified specialist review |
| Very Large | 10+ | > 1000 | ❌ Too big | Split into smaller commits |

---

## 🎓 Examples

### Example 1: Pre-staging sanity check

```
User: "review src/auth.ts before I stage it"

Claude:
## Review Scope
- src/auth.ts (78 lines reviewed)

## 🔴 High Priority Issues
1. **src/auth.ts:45** - Password compared with `==`
   - **Risk**: Timing attack
   - **Fix**: `crypto.timingSafeEqual()` or `bcrypt.compare()`

## 🟡 Medium Priority Issues
1. **src/auth.ts:67** - Hard-coded token expiry
   - **Fix**: Move to `TOKEN_EXPIRY_MS` env var

## [ADVERSARIAL] Findings
1. **src/auth.ts:45** - [ADVERSARIAL] Mirror test? — all three auth tests still pass
   if `comparePasswords` becomes `() => true`

## Assumptions Identified
- Incoming passwords are always non-empty strings
- `bcrypt.hash` is the only source of stored hashes

## Summary
Files: 1 | High: 1 | Medium: 1 | Adversarial: 1 | Assumptions: 2
```

### Example 2: Snippet review with hallucination guard

```
User: "review this validator:

function validateEmail(email) {
  const re = /^[^\s@]+@[^\s@]+\.[^\s@]+$/;
  return re.test(email);
}"

Claude:
## Review Scope
- Inline snippet (4 lines reviewed)

## 🟡 Medium Priority Issues
1. **snippet:3** - No type check; crashes when `email` is not a string
   - **Fix**: `if (typeof email !== 'string') return false;`

## Adversarial quick check: no issues found.

## Assumptions Identified
- `email` is a string

## Note
Earlier Gemini runs on similar code flagged `[^\s@]` as "space inside character class" —
Step 3.3 verified this regex parses correctly (`re.test('a@b.c') === true`), so no
[UNVERIFIED-SYNTAX] finding was emitted.
```

---

## 🔗 Related Skills

- **code-review-codex** — Native review path for Codex
- **pr-review-assistant** — PR-level review using the active runtime's native reviewer
- **code-story-teller** — Understand code evolution history

---

## 📄 License

Part of the Claude Code Skills repository.

---

**Maintainer:** Tom Wang
**Created:** 2026-01-20
**Last Updated:** 2026-04-20
**Version:** 2.0.0 (promoted to default reviewer 2026-04)

---

<div align="center">

**⚡ Default • 🎯 Adversarial • 📝 Assumptions List • 🛡️ Syntax-Checker-Verified**

</div>
