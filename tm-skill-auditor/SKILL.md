---
name: skill-auditor
description: Audit Claude Code skills for quality, security, and best practices. Use when reviewing SKILL.md files, ensuring skill quality standards, or before sharing skills with team.
id: tm-skill-auditor
namespace: tm
domain: skill
action: auditor
version: "1.0.0"
updated: "2026-01-17"
---

# Skill Auditor

Comprehensive quality audit for Claude Code skills to ensure they meet security, portability, and documentation standards.

## Background & Context

### The Problem
As teams create more Claude Code skills, quality inconsistencies emerge:
- Skills with hardcoded paths that don't work on other machines
- Missing security considerations leading to vulnerabilities
- Inadequate error handling causing poor user experience
- Ambiguous documentation making skills hard to use
- Inconsistent quality standards across team members

### The Solution
Skill Auditor provides automated and AI-powered quality checks to ensure every skill meets production standards before sharing with the team.

### Scope
- **Target**: SKILL.md files and associated scripts
- **Coverage**: Security, portability, quality, documentation
- **Output**: Scored audit report with actionable recommendations
- **Integration**: Works with existing review workflows (spec-review, code-review)

## Requirements

### Functional Requirements
1. **Automated Pattern-Based Checks**: Detect hardcoded paths, missing sections, security keywords
2. **Scoring System**: 100-point scale with weighted categories (Security 30%, Error Handling 20%, etc.)
3. **Report Generation**: Structured markdown with severity levels and line numbers
4. **Actionable Recommendations**: Specific fixes, not just problem identification
5. **Batch Auditing**: Support auditing multiple skills

### Non-Functional Requirements
1. **Performance**: Complete audit in < 5 seconds for typical skill
2. **Portability**: Work on macOS and Linux without modification
3. **Reliability**: < 5% false positive rate on well-formed skills
4. **Usability**: Reports readable without technical knowledge

### Dependencies
- **Required**: bash 4.0+, grep, sed, find, mktemp
- **Optional**: Gemini CLI (for AI-powered semantic analysis)
- **Environment**: Unix-like system (macOS, Linux, WSL)

## Purpose

A meta-skill that audits other skills to ensure they are:
- **Secure**: Free from security vulnerabilities and risks
- **Portable**: Work across different environments and machines
- **Well-documented**: Clear usage instructions and examples
- **High-quality**: Follow best practices and standards
- **Team-ready**: Safe to share with colleagues

## When to Use

**Automatic triggers:**
- After creating a new skill
- Before committing skill changes
- Before sharing skills with team
- During skill maintenance/updates

**Manual triggers:**
- "audit this skill"
- "review the skill quality"
- "check if this skill is production-ready"
- "validate skill standards"

## Audit Checklist (50+ Items)

### 1. Structure Integrity (Critical)

#### YAML Frontmatter
- [ ] YAML frontmatter exists and is valid
- [ ] `name` field present and follows naming convention (lowercase, hyphens)
- [ ] `description` field present and clear (describes when to use)
- [ ] No syntax errors in YAML

#### File Structure
- [ ] SKILL.md exists in skill directory
- [ ] Directory name matches skill name
- [ ] If has scripts/, they are in scripts/ subdirectory
- [ ] README.md exists (recommended)

#### Required Sections
- [ ] **Workflow** or **Instructions** section exists
- [ ] **Examples** section with at least 2 usage examples
- [ ] **Trigger phrases** or **When to Use** clearly defined

### 2. Security Considerations (Critical)

#### Security Documentation
- [ ] **Security Considerations** section exists
- [ ] XSS prevention mentioned (if handles user input)
- [ ] Input sanitization guidelines provided
- [ ] URL validation mentioned (if uses URLs)
- [ ] File path safety mentioned (if reads/writes files)
- [ ] Dangerous protocols rejected (javascript:, data:, vbscript:)

#### Specific Security Checks
- [ ] HTML entity escaping for user content (`<`, `>`, `&`, `"`, `'`)
- [ ] No raw `<script>` tag injection from user input
- [ ] Directory traversal prevention (`../`, `..\\`)
- [ ] API key/credential handling mentioned (if applicable)
- [ ] CSP or security headers mentioned (if generates HTML)

#### External Dependencies
- [ ] CDN resources use HTTPS only
- [ ] Third-party API risks documented
- [ ] Dependency versions specified
- [ ] Fallback options for external failures

### 3. Error Handling (Critical)

#### Error Handling Documentation
- [ ] **Error Handling** section exists
- [ ] File operation errors covered
- [ ] User input validation covered
- [ ] Network/API failures handled (if applicable)
- [ ] Clear error messages provided

#### Specific Error Handling
- [ ] Missing file handling
- [ ] Invalid input handling
- [ ] Empty/null value handling
- [ ] Timeout handling (if long-running)
- [ ] Graceful degradation strategy

### 4. Portability & Environment (Critical)

#### Path Handling
- [ ] **No hardcoded absolute paths** (e.g., full paths to specific user directories)
- [ ] Uses environment variables for configurable paths
- [ ] Relative paths used where needed
- [ ] Path configuration documented

#### Cross-platform Compatibility
- [ ] Works on macOS, Linux, Windows (or limitations documented)
- [ ] Shell scripts use portable commands
- [ ] No platform-specific dependencies (or alternatives provided)
- [ ] Line endings handled (CRLF vs LF)

#### Dependencies
- [ ] All dependencies listed
- [ ] Installation instructions provided
- [ ] Version requirements specified
- [ ] Optional vs required dependencies clear

### 5. Quality & Clarity (Important)

#### Clear Language
- [ ] No ambiguous terms (avoid: vague adjectives without metrics)
- [ ] Specific metrics provided (e.g., "max 15 lines" instead of "small")
- [ ] Quantifiable criteria (e.g., ">30 seconds" instead of vague terms)
- [ ] Technical terms defined

#### Workflow Clarity
- [ ] Step-by-step workflow provided
- [ ] Each step is actionable
- [ ] Decision points clearly marked
- [ ] Expected inputs/outputs defined

#### Code Examples
- [ ] At least 2 usage examples
- [ ] Examples show actual commands/prompts
- [ ] Expected outputs shown
- [ ] Edge cases covered

### 6. Documentation (Important)

#### Essential Documentation
- [ ] README.md exists
- [ ] Installation/setup instructions
- [ ] Quick start guide
- [ ] Troubleshooting section
- [ ] Examples directory (if skill has multiple use cases or scripts)

#### Technical Documentation
- [ ] Tool dependencies listed with versions
- [ ] API usage documented (if applicable)
- [ ] Configuration options explained
- [ ] Environment variables documented

### 7. Script Quality (If Applicable)

#### Shell Script Best Practices
- [ ] Shebang present (`#!/bin/bash` or `#!/usr/bin/env bash`)
- [ ] Error handling (`set -e`, `set -u`, `set -o pipefail`)
- [ ] Parameter validation
- [ ] `--help` flag implemented
- [ ] Executable permissions set (`chmod +x`)
- [ ] No hardcoded paths in scripts
- [ ] Proper quoting of variables

#### Script Security
- [ ] No `eval` usage without validation
- [ ] Input sanitization
- [ ] Safe temporary file handling
- [ ] No secrets in scripts

### 8. Integration & Collaboration

#### Integration Points
- [ ] Integration with other skills documented
- [ ] Skill dependencies noted
- [ ] Conflicts with other skills addressed

#### Team Sharing
- [ ] Skill is self-contained
- [ ] No personal/sensitive information
- [ ] Works without custom setup
- [ ] License information (if applicable)

### 9. Best Practices Compliance

#### Skill Design
- [ ] Single Responsibility Principle (does one thing well)
- [ ] Name is descriptive and unique
- [ ] Description accurately reflects functionality
- [ ] Trigger conditions are specific

#### User Experience
- [ ] Clear feedback to user
- [ ] Progress indicators (for long operations)
- [ ] Confirmation for destructive actions
- [ ] Helpful error messages

---

## Instructions

Follow this workflow to audit a skill for production readiness.

## Workflow

### Step 1: Locate Skill to Audit

1. If user provides skill name or path, use that
2. If not specified, ask which skill to audit
3. Verify skill directory exists
4. Check for SKILL.md file

### Step 2: Run Automated Checks

Execute automated audit script:
```bash
bash scripts/audit_skill.sh <skill-directory>
```

The script will:
- Parse YAML frontmatter
- Scan for required sections
- Check for security keywords
- Detect hardcoded paths
- Validate markdown syntax
- Count examples
- Check for ambiguous terms

### Step 3: Manual Review (AI-Powered)

Use Gemini or Claude to:
1. Read SKILL.md content
2. Assess clarity and completeness
3. Identify potential security issues
4. Check for logical inconsistencies
5. Evaluate documentation quality

### Step 4: Generate Audit Report

Create structured report with:

**Executive Summary:**
- Overall score (0-100)
- Critical issues count
- Important issues count
- Suggestions count
- Ready for production? (Yes/No)

**Detailed Findings:**
- Categorized by severity (Critical, Important, Suggestion)
- Line numbers referenced
- Specific recommendations
- Code examples for fixes

**Checklist Status:**
- ✅ Passed items (green)
- ⚠️ Warning items (yellow)
- ❌ Failed items (red)

### Step 5: Provide Actionable Recommendations

For each issue:
1. Explain why it matters
2. Provide specific fix
3. Show code example if applicable
4. Link to best practices documentation

### Step 6: Offer Auto-fix (Optional)

For straightforward issues (e.g., missing sections, ambiguous terms):
- Offer to automatically add missing sections
- Suggest specific replacements for ambiguous terms
- Generate security/error handling templates

id: tm-skill-auditor
namespace: tm
domain: skill
action: auditor
version: "1.0.0"
updated: "2026-01-17"
---

## Report Format

```markdown
# Skill Audit Report: {skill-name}

**Audit Date**: 2026-01-15
**Skill Version**: {version if available}
**Auditor**: Skill Auditor (Claude Code Meta-Skill)

---

## Executive Summary

**Overall Score**: 75/100 ⚠️
**Status**: Needs Improvement

| Severity | Count |
|----------|-------|
| 🔴 Critical | 3 |
| 🟡 Important | 7 |
| 🟢 Suggestions | 5 |

**Production Ready**: ❌ No - Address critical issues first

id: tm-skill-auditor
namespace: tm
domain: skill
action: auditor
version: "1.0.0"
updated: "2026-01-17"
---

## 1. Structure Integrity

### ✅ Passed
- YAML frontmatter valid
- Required sections present
- Markdown syntax correct

### ❌ Critical Issues
1. **Missing Error Handling Section**
   - Line: N/A
   - Impact: Users won't know how to handle failures
   - Fix: Add "## Error Handling" section with file ops, validation, generation errors

---

## 2. Security Considerations

### ❌ Critical Issues
1. **No Security Section** (Line: N/A)
   - Risk: Security vulnerabilities not documented
   - Fix: Add "## Security Considerations" with XSS, input validation, URL safety

2. **Hardcoded Absolute Path** (Line: 45)
   - Found: Absolute path in skill definition (example placeholder)
   - Risk: Skill won't work on other machines
   - Fix: Use `$STYLE_YAML_DIR` environment variable or relative paths

id: tm-skill-auditor
namespace: tm
domain: skill
action: auditor
version: "1.0.0"
updated: "2026-01-17"
---

## 3. Error Handling

### ⚠️ Important Issues
1. **Missing File Operation Error Handling** (Line: N/A)
   - Missing: How to handle file read/write failures
   - Fix: Document error messages and fallback strategies

---

## 4. Portability

### ✅ Passed
- No platform-specific commands detected

### ❌ Critical Issues
1. **Hardcoded Paths** (already mentioned above)

id: tm-skill-auditor
namespace: tm
domain: skill
action: auditor
version: "1.0.0"
updated: "2026-01-17"
---

## 5. Quality & Clarity

### ⚠️ Important Issues
1. **Ambiguous Term: vague adjective** (Line: 16)
   - Found: Vague descriptor without specific metrics
   - Fix: Replace with "Lightweight markdown" or "Straightforward (5-15 slides)"

2. **Ambiguous Term: vague descriptor** (Line: 276)
   - Found: Vague term without measurable criteria
   - Fix: Replace with "requiring >30 seconds to explain" or specific threshold

---

## 6. Documentation

### ✅ Passed
- README.md exists
- Examples provided

### ⚠️ Important Issues
1. **Missing Troubleshooting Section**
   - Fix: Add common issues and solutions

id: tm-skill-auditor
namespace: tm
domain: skill
action: auditor
version: "1.0.0"
updated: "2026-01-17"
---

## Summary of Recommendations

### 🔴 Critical (Must Fix)
1. Add Security Considerations section
2. Add Error Handling section
3. Remove hardcoded paths, use environment variables

### 🟡 Important (Should Fix)
1. Replace ambiguous terms with specific metrics
2. Add troubleshooting section
3. Document all dependencies with versions

### 🟢 Suggestions (Nice to Have)
1. Add more usage examples
2. Include performance considerations
3. Add integration tests

---

**Next Steps:**
1. Address all critical issues
2. Fix important issues
3. Re-run audit to verify
4. Ready for production ✅

id: tm-skill-auditor
namespace: tm
domain: skill
action: auditor
version: "1.0.0"
updated: "2026-01-17"
---

**Generated by**: Skill Auditor
**Powered by**: Gemini AI + Claude Code
```

---

## Audit Categories & Scoring

| Category | Weight | Max Score |
|----------|--------|-----------|
| Structure Integrity | 15% | 15 |
| Security | 30% | 30 |
| Error Handling | 20% | 20 |
| Portability | 15% | 15 |
| Quality & Clarity | 10% | 10 |
| Documentation | 10% | 10 |

**Total**: 100 points

**Scoring:**
- 90-100: Excellent ✅
- 75-89: Good ⚠️
- 60-74: Needs Improvement ⚠️
- <60: Critical Issues ❌

id: tm-skill-auditor
namespace: tm
domain: skill
action: auditor
version: "1.0.0"
updated: "2026-01-17"
---

## Technical Design

### Architecture

```
User Request → Claude (Main Agent)
                  ↓
          Skill Auditor Triggered
                  ↓
          ┌───────────────────┐
          │  Audit Pipeline   │
          ├───────────────────┤
          │ 1. Parse SKILL.md │
          │ 2. Run Checks     │
          │ 3. Score/Classify │
          │ 4. Generate Report│
          └───────────────────┘
                  ↓
          Structured Report → User
```

### Components

1. **audit_skill.sh** (Shell Script)
   - Automated pattern-based checks
   - File system validation
   - Report generation engine
   - Scoring calculator

2. **SKILL.md** (This File)
   - Audit workflow definition
   - Checklist documentation
   - Integration guidelines

3. **Templates** (examples/templates/)
   - Security section template
   - Error handling template
   - Quick-fix references

### Check Categories & Weights

| Category | Weight | Max Points | Check Type |
|----------|--------|------------|------------|
| Structure Integrity | 15% | 15 | Automated |
| Security | 30% | 30 | Automated + AI |
| Error Handling | 20% | 20 | Automated + AI |
| Portability | 15% | 15 | Automated |
| Quality & Clarity | 10% | 10 | Automated + AI |
| Documentation | 10% | 10 | Automated |

**Total**: 100 points

### Data Flow

```
SKILL.md → audit_skill.sh → Checks → BODY_FILE (temp)
                                            ↓
                            REPORT_FILE ← generate_report() ← Scoring
```

**Key Design Decision**: Use temporary file buffering to ensure correct report structure and avoid sed portability issues.

## Testing Strategy

### Unit Tests (Automated Checks)

Test each check function independently:

**Test Cases:**
1. **YAML Frontmatter**
   - Valid YAML → Pass
   - Missing name field → Fail (Critical)
   - Missing description → Fail (Critical)
   - No frontmatter → Fail (Critical)

2. **Hardcoded Paths**
   - Absolute user-specific paths → Fail (Critical)
   - `$HOME/...` or `~/...` → Pass (resolves at runtime)
   - `./relative/path` → Pass
   - Environment variables → Pass

3. **Security Keywords**
   - 0-1 keywords → Fail (Critical)
   - 2-3 keywords → Warning (Important)
   - 4+ keywords → Pass

4. **Ambiguous Terms**
   - Contains "simple" → Warning with line number
   - Contains "fast" → Warning with line number
   - No ambiguous terms → Pass

### Integration Tests

1. **Test on High-Quality Skill**
   - Input: interactive-presentation-generator (expected score: 75+)
   - Expected: 0 critical issues, production-ready status

2. **Test on Problematic Skill**
   - Input: Skill with hardcoded paths, missing security section
   - Expected: 2+ critical issues, not production-ready status

3. **Self-Audit**
   - Input: skill-auditor itself
   - Expected: Score 85+, pass own standards

### Acceptance Criteria

- [ ] Audit completes in < 5 seconds
- [ ] Reports are well-structured (sections in correct order)
- [ ] Score calculation is accurate
- [ ] All critical issues are detected
- [ ] False positive rate < 5%
- [ ] Works on both macOS and Linux

## Integration with Existing Skills

### Relationship with spec-review-assistant

**spec-review-assistant:**
- Reviews **specification documents** (design docs, requirements)
- Checks completeness, feasibility, clarity of **requirements**
- Focus: Pre-implementation planning

**skill-auditor:**
- Reviews **SKILL.md files** (skill definitions)
- Checks security, portability, quality of **skills themselves**
- Focus: Skill quality and production-readiness

**Both skills complement each other but serve different purposes.**

---

## Usage Examples

### Example 1: Audit a specific skill
```
User: "audit the interactive-presentation-generator skill"

Expected behavior:
1. Locate skill directory
2. Read SKILL.md and related files
3. Run automated checks
4. Generate audit report
5. Present findings with severity levels
6. Offer to auto-fix straightforward issues (missing sections, ambiguous terms)
```

### Example 2: Audit before sharing
```
User: "I want to share my custom skill with the team, can you audit it first?"

Expected behavior:
1. Ask for skill name/path
2. Run comprehensive audit
3. Check for hardcoded paths, personal info
4. Verify security and error handling
5. Provide go/no-go recommendation
```

### Example 3: Audit all skills
```
User: "audit all skills in my skills directory"

Expected behavior:
1. Find all skills in ~/.claude/skills/
2. Audit each one
3. Generate summary report
4. Highlight skills with critical issues
```

id: tm-skill-auditor
namespace: tm
domain: skill
action: auditor
version: "1.0.0"
updated: "2026-01-17"
---

## Notes

- This skill uses Gemini CLI for semantic analysis (similar to spec-review-assistant)
- Automated checks complete in < 5 seconds, AI review provides thorough semantic analysis
- Reports are saved to `~/.claude/audits/` for reference
- Can be integrated into CI/CD or pre-commit hooks
- Follows same reporting format as spec-review-assistant for consistency
- Critical issues must be fixed before sharing skills with team
- This skill itself should pass its own audit (meta-validation)

---

## Error Handling

### Skill Not Found
- Clear error message: "Skill directory not found at [path]"
- Suggest checking skill name or path
- List available skills for reference

### Invalid SKILL.md
- Report YAML parsing errors with line numbers
- Continue with partial audit if possible
- Note missing sections clearly

### Script Execution Failures
- Log error details
- Fallback to manual review only
- Inform user of reduced audit coverage

id: tm-skill-auditor
namespace: tm
domain: skill
action: auditor
version: "1.0.0"
updated: "2026-01-17"
---

## Security Considerations

### Auditing Process Safety
- Read-only operations (no modifications without user consent)
- No execution of audited skill's scripts during audit
- Validate file paths before reading
- Sanitize output in audit reports

### Sensitive Information Detection
- Check for API keys, passwords, tokens in SKILL.md
- Warn if personal information found (email, names in examples)
- Flag hardcoded credentials in scripts

---

## Best Practices

### For Skill Authors
1. Run skill-auditor before committing
2. Fix all critical issues
3. Consider important issues seriously
4. Use audit report as quality checklist

### For Teams
1. Establish minimum audit score requirement (e.g., 80/100)
2. Require all critical issues fixed before merge
3. Use as part of skill review process
4. Share audit reports with skill submissions

id: tm-skill-auditor
namespace: tm
domain: skill
action: auditor
version: "1.0.0"
updated: "2026-01-17"
---

## Integration Points

### With Other Skills
- **spec-review-assistant**: Review skill's specification/design
- **code-review-gemini**: Review skill's scripts (if any)
- **commit-msg-generator**: Generate commit message after fixes

### With Git Workflow
```bash
# Pre-commit hook example
if [[ -f SKILL.md ]]; then
  claude-skill skill-auditor .
fi
```

---

## Limitations

- Cannot detect all security issues (manual review still needed)
- Semantic analysis depends on AI quality
- Some checks require human judgment
- Script-based checks are pattern-matching only

id: tm-skill-auditor
namespace: tm
domain: skill
action: auditor
version: "1.0.0"
updated: "2026-01-17"
---

## Future Enhancements

- Auto-fix capability for common issues
- Integration with GitHub Actions
- Skill quality badges
- Historical audit tracking
- Comparative analysis between skills
- Automated security scanning with dedicated tools
