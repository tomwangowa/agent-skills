# Skill Auditor

Comprehensive quality audit tool for Claude Code skills to ensure they meet production standards.

## Overview

Skill Auditor is a meta-skill that reviews other skills for:
- **Security**: XSS prevention, input validation, safe URL/path handling
- **Portability**: No hardcoded paths, cross-platform compatibility
- **Quality**: Clear documentation, specific metrics, examples
- **Error Handling**: Comprehensive error coverage
- **Team Readiness**: Safe to share, no personal information

## Features

### Automated Checks
- ✅ YAML frontmatter validation
- ✅ Required sections detection
- ✅ Hardcoded path detection
- ✅ Security keyword scanning
- ✅ Ambiguous terminology detection
- ✅ Example count verification
- ✅ Documentation completeness
- ✅ Script quality checks

### Scoring System
- **100-point scale** with weighted categories
- **Severity levels**: Critical, Important, Suggestions
- **Production readiness** assessment
- **Actionable recommendations** for each issue

### Report Generation
- Markdown format for easy sharing
- Categorized findings
- Line number references
- Specific fix recommendations
- Pass/fail determination

## Quick Start

### Audit a Skill

```bash
# Basic audit
bash scripts/audit_skill.sh /path/to/skill

# Save report to specific file
bash scripts/audit_skill.sh ~/.claude/skills/my-skill -o my-skill-audit.md

# Verbose mode
bash scripts/audit_skill.sh ./my-skill -v
```

### Via Claude

```
"Audit the interactive-presentation-generator skill"
```

Claude will:
1. Run the audit script
2. Analyze findings
3. Present prioritized issues
4. Offer to help fix problems

## Audit Categories

### 1. Structure Integrity (15 points)
- YAML frontmatter valid
- Required fields present (name, description)
- Essential sections exist
- Markdown syntax correct

### 2. Security (30 points)
- Security Considerations section
- XSS prevention documented
- Input validation guidelines
- URL/path safety measures
- Credential handling
- External dependency risks

### 3. Error Handling (20 points)
- Error Handling section exists
- File operation errors covered
- Input validation errors
- Network failures (if applicable)
- Clear error messages

### 4. Portability (15 points)
- No hardcoded absolute paths
- Environment variable usage
- Cross-platform compatibility
- Dependency documentation

### 5. Quality & Clarity (10 points)
- No ambiguous terminology
- Specific metrics provided
- Clear workflow steps
- Consistent terminology

### 6. Documentation (10 points)
- README exists
- Quick start guide
- Usage examples
- Troubleshooting section

## Scoring

| Score | Rating | Status |
|-------|--------|--------|
| 90-100 | Excellent ✅ | Production-ready |
| 75-89 | Good ⚠️ | Minor improvements recommended |
| 60-74 | Needs Work ⚠️ | Address important issues |
| <60 | Critical Issues ❌ | Not ready for production |

## Example Output

```markdown
# Skill Audit Report: my-skill

**Audit Date**: 2026-01-15
**Overall Score**: 82/100 (82%) ⚠️ Good

| Severity | Count |
|----------|-------|
| 🔴 Critical | 0 |
| 🟡 Important | 3 |
| 🟢 Suggestions | 2 |

**Production Ready**: ✅ Yes (with minor improvements)

---

## Findings

### 2. Security Considerations
✅ Security keywords found (XSS, validate, sanitize)

### 4. Portability
❌ Hardcoded path found (Line 45): /Users/tom_wang/...
**Fix**: Use $MY_VAR environment variable

### 5. Quality & Clarity
⚠️ Ambiguous term: "simple" (Line 16)
**Fix**: Replace with "lightweight" or specific criteria

---

## Summary
Fix hardcoded paths, then ready for team sharing.
```

## Common Issues & Fixes

### Issue: Hardcoded Paths
**Example**: `/Users/tom_wang/Development/styles`

**Fix**:
```markdown
# In SKILL.md
Style directory: $STYLE_DIR (default: ./styles/)

# In README.md
export STYLE_DIR="/path/to/styles"
```

### Issue: Missing Security Section
**Fix**: Add to SKILL.md:
```markdown
## Security Considerations

### Input Sanitization
- Escape HTML entities: < > & " '
- Validate URLs: Allow only http:, https:, file:
- Sanitize file paths: No ../ traversal

### Content Safety
- No raw <script> injection
- Validate all user inputs
- Use CSP headers (if generating HTML)
```

### Issue: Missing Error Handling
**Fix**: Add to SKILL.md:
```markdown
## Error Handling

### File Operations
- Check file existence before reading
- Handle file read/write errors
- Provide fallback options

### User Input
- Validate required fields
- Check format/type
- Provide clear error messages
```

### Issue: Ambiguous Terms
**Examples**:
- "simple" → "lightweight" or "5-15 slides"
- "complex" → "requiring >30 seconds to explain"
- "appropriate" → "for data-heavy slides"
- "reasonable" → "standard values (16pt body, 40pt heading)"

## Integration with Workflow

### Pre-commit Hook

```bash
#!/bin/bash
# .git/hooks/pre-commit

CHANGED_SKILLS=$(git diff --staged --name-only | grep "SKILL.md" | sed 's|/SKILL.md||')

for skill in $CHANGED_SKILLS; do
    if [[ -f "$skill/SKILL.md" ]]; then
        echo "Auditing $skill..."
        bash ~/.claude/skills/skill-auditor/scripts/audit_skill.sh "$skill"

        if [[ $? -ne 0 ]]; then
            echo "❌ Skill audit failed. Fix critical issues before committing."
            exit 1
        fi
    fi
done
```

### CI/CD Integration

```yaml
# .github/workflows/audit-skills.yml
name: Audit Skills

on: [push, pull_request]

jobs:
  audit:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v2
      - name: Audit all skills
        run: |
          for skill in */SKILL.md; do
            bash skill-auditor/scripts/audit_skill.sh "$(dirname $skill)"
          done
```

## Use Cases

### 1. Before Sharing with Team
```
User: "I created a new skill, is it ready to share?"
Claude: [Runs skill-auditor]
        "Found 2 critical issues:
         1. Hardcoded path at line 23
         2. Missing security section
         Would you like me to help fix these?"
```

### 2. Quality Gate
```
User: "Audit all my skills"
Claude: [Audits each skill]
        "Summary:
         - 5 skills production-ready ✅
         - 2 skills need security improvements ⚠️
         - 1 skill has critical issues ❌"
```

### 3. Continuous Improvement
```
User: "Has my skill improved since last audit?"
Claude: [Compares with previous audit]
        "Score improved from 65 to 85!
         Fixed: hardcoded paths, added security section
         Remaining: 2 ambiguous terms"
```

## Checklist Reference

### Critical Checks (Must Pass)
- [ ] No hardcoded absolute paths
- [ ] Security Considerations section exists
- [ ] Error Handling section exists
- [ ] YAML frontmatter valid
- [ ] No credentials/secrets in files

### Important Checks (Should Pass)
- [ ] At least 2 usage examples
- [ ] README.md exists
- [ ] No ambiguous terms
- [ ] Dependencies documented
- [ ] Scripts have error handling

### Suggestions (Nice to Have)
- [ ] QUICKSTART.md or quick start section
- [ ] Troubleshooting section
- [ ] Integration with other skills documented
- [ ] Performance considerations mentioned

## Limitations

- Cannot detect all security vulnerabilities (manual review still needed)
- Pattern-based detection may have false positives/negatives
- Semantic analysis depends on AI capabilities
- Some checks require human judgment

## Related Skills

- **spec-review-assistant**: Reviews specification documents
- **code-review-gemini**: Reviews code changes
- **commit-msg-generator**: Generates commit messages

**skill-auditor** reviews the skills themselves, ensuring meta-quality.

## Best Practices for Skill Authors

### 1. Run Audit Early and Often
- After creating initial SKILL.md
- Before each commit
- After major changes
- Before sharing with team

### 2. Fix Critical Issues First
- Security vulnerabilities
- Hardcoded paths
- Missing error handling

### 3. Address Important Issues
- Documentation gaps
- Ambiguous language
- Missing examples

### 4. Use Audit as Checklist
- Reference audit report while developing
- Proactively add required sections
- Follow security/error handling templates

### 5. Aim for 85+ Score
- 85+ ensures production quality
- Demonstrates professional standards
- Safe for team collaboration

## Contributing

Found a new check that should be added? Issues with false positives?

1. Update the checklist in SKILL.md
2. Add detection logic to audit_skill.sh
3. Test on existing skills
4. Submit improvement

## License

Part of Claude Code Skills library.

## Version

**1.0.0** - Initial release with 50+ audit checks
