# Skill Auditor Examples

This directory contains examples and templates to help you fix common skill audit issues.

## Files

### 📄 sample-audit-report.md
A complete example of a skill audit report showing:
- How findings are categorized
- Severity levels and scoring
- Specific recommendations
- Action plan for fixes
- Before/after comparison

**Use this to understand:**
- What a typical audit report looks like
- How to interpret findings
- How to prioritize fixes

### 📁 templates/

#### security-section-template.md
Ready-to-use template for adding Security Considerations section to your SKILL.md.

**Covers:**
- Input sanitization (HTML escaping, URL validation, path safety)
- Content safety (YAML parsing, file validation)
- External dependencies (CDN, APIs, tools)
- Sensitive information handling
- Security best practices
- Secure vs insecure code examples

**How to use:**
1. Copy relevant sections to your SKILL.md
2. Customize for your skill's specific needs
3. Remove sections that don't apply

#### error-handling-template.md
Ready-to-use template for adding Error Handling section to your SKILL.md.

**Covers:**
- File operation errors
- User input validation
- External dependency failures
- Generation errors
- Graceful degradation strategy
- Error message best practices
- Testing checklist

**How to use:**
1. Copy relevant sections to your SKILL.md
2. Adapt examples to your skill's use cases
3. Add skill-specific error scenarios

## Common Audit Failures & Quick Fixes

The Security and Error Handling findings below are Critical for `script-bearing`
skills. For `pure-instruction` skills, the auditor treats those sections as
informational because the skill has no I/O surface of its own.

### 🔴 Critical: Missing Security Section

**Quick Fix (2 minutes):**
```bash
# Add to your SKILL.md
cat templates/security-section-template.md >> my-skill/SKILL.md
```

Then customize for your skill's needs.

### 🔴 Critical: Missing Error Handling Section

**Quick Fix (2 minutes):**
```bash
# Add to your SKILL.md
cat templates/error-handling-template.md >> my-skill/SKILL.md
```

Then customize for your skill's needs.

### 🔴 Critical: Hardcoded Absolute Path

**Problem:**
```markdown
Style directory: /Users/tom_wang/Development/styles
```

**Quick Fix:**
```markdown
Style directory: $STYLE_DIR (default: ./styles/)

To use custom directory:
export STYLE_DIR="/your/path/to/styles"
```

### 🟡 Important: Ambiguous Terms

**Problem → Solution:**
- "simple" → "lightweight" or "straightforward (5-15 slides)"
- "complex" → "requiring >30 seconds to explain"
- "small" → "max 15 lines"
- "large" → "more than 50 lines"
- "fast" → "< 1 second response time"
- "slow" → "> 5 seconds"
- "appropriate" → "for data-heavy slides" or specific criteria
- "reasonable" → "standard values (16pt body, 40pt heading)"
- "good" → "high quality (1920x1080 resolution)"
- "bad" → "low quality (< 720p resolution)"

### 🟡 Important: Missing README.md

**Quick Fix (5 minutes):**

Create `README.md` with:
```markdown
# My Skill Name

Brief description of what this skill does.

## Quick Start

\`\`\`
Trigger phrase: "do something with my skill"
\`\`\`

## Features

- Feature 1
- Feature 2
- Feature 3

## Usage Examples

### Example 1
\`\`\`
User: "example command"
Output: expected result
\`\`\`

## Installation

Dependencies:
- tool1: `npm install -g tool1`
- tool2: `brew install tool2`

## Troubleshooting

### Issue: Common problem
**Solution**: How to fix it
```

## Workflow: From Audit to Production

### Step 1: Run Initial Audit
```bash
bash skill-auditor/scripts/audit_skill.sh my-skill
```

**Expected output:**
- Score: 40-60 (typical for new skills)
- Critical issues: 2-4
- Important issues: 5-10

### Step 2: Fix Critical Issues (30 min)

1. **Add Security section** (use template)
2. **Add Error Handling section** (use template)
3. **Fix hardcoded paths** (use environment variables)

### Step 3: Fix Important Issues (1 hour)

1. **Replace ambiguous terms** (use guide above)
2. **Create README.md** (use template)
3. **Add more examples** (aim for 3+)
4. **Add troubleshooting section**

### Step 4: Re-audit
```bash
bash skill-auditor/scripts/audit_skill.sh my-skill
```

**Target score rating:** 90+ for Excellent; evaluate Readiness separately.

### Step 5: Readiness Check ✅

When Readiness is `Ready` (0 Critical and 0 Important findings):
- Share with team
- Commit to repository
- Add to team's skill library

## Real-World Example

### Before Audit: branded-presentation

**Score**: 26/100 ❌
**Issues**:
- 🔴 No Security section
- 🔴 No Error Handling section
- 🔴 Missing README.md
- 🟡 Only 1 example

**Time to fix**: ~1 hour

### After Fixes

**Score**: 88/100 ⚠️ Good
**Issues**: 0 critical, 0 important, 1 suggestion
**Readiness**: Ready

**Changes made:**
- Added Security Considerations (15 min)
- Added Error Handling (15 min)
- Created README.md (20 min)
- Added 2 more examples (10 min)

## Tips for High Scores

### To reach `Ready`:
1. ✅ Resolve all Critical findings
2. ✅ Resolve all Important findings
3. ✅ Keep the score rating and Readiness as separate signals
4. ✅ No hardcoded paths
5. ✅ Clear workflow documentation

### To reach 90+:
1. All of the above, plus:
2. ✅ QUICKSTART.md or detailed quick start section
3. ✅ Troubleshooting section with 5+ scenarios
4. ✅ Integration documentation
5. ✅ Performance considerations
6. ✅ Examples directory with sample outputs

### Bonus Points:
- Scripts with comprehensive error handling
- Pre-commit hook example
- CI/CD integration guide
- Video demo or screenshots
- Comparison with similar tools

## Questions?

Run skill-auditor on your skill and see what it finds!

```bash
bash ~/.claude/skills/skill-auditor/scripts/audit_skill.sh YOUR_SKILL_DIR
```

Then use the templates here to quickly fix any issues.
