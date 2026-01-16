#!/usr/bin/env bash

set -euo pipefail

# Colors for output
RED='\033[0;31m'
YELLOW='\033[1;33m'
GREEN='\033[0;32m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Audit score tracking
SCORE=0
MAX_SCORE=100
CRITICAL_ISSUES=0
IMPORTANT_ISSUES=0
SUGGESTIONS=0

# Output file
REPORT_FILE=""

# Usage
usage() {
    cat << EOF
Usage: $0 <skill-directory> [OPTIONS]

Audit a Claude Code skill for quality, security, and best practices.

Arguments:
  skill-directory    Path to the skill directory to audit

Options:
  -o, --output FILE  Save report to file (default: skill-audit-report.md)
  -v, --verbose      Show detailed progress
  -h, --help         Show this help message

Examples:
  $0 ~/.claude/skills/my-skill
  $0 ./interactive-presentation-generator -o audit.md
EOF
    exit 1
}

# Parse arguments
SKILL_DIR=""
VERBOSE=false

while [[ $# -gt 0 ]]; do
    case $1 in
        -h|--help)
            usage
            ;;
        -o|--output)
            REPORT_FILE="$2"
            shift 2
            ;;
        -v|--verbose)
            VERBOSE=true
            shift
            ;;
        -*)
            echo -e "${RED}Unknown option: $1${NC}"
            usage
            ;;
        *)
            SKILL_DIR="$1"
            shift
            ;;
    esac
done

# Validate skill directory
if [[ -z "$SKILL_DIR" ]]; then
    echo -e "${RED}Error: Skill directory is required${NC}"
    usage
fi

if [[ ! -d "$SKILL_DIR" ]]; then
    echo -e "${RED}Error: Skill directory not found: $SKILL_DIR${NC}"
    exit 1
fi

# Get absolute path
SKILL_DIR=$(cd "$SKILL_DIR" && pwd)
SKILL_NAME=$(basename "$SKILL_DIR")

# Set default report file
if [[ -z "$REPORT_FILE" ]]; then
    REPORT_FILE="$SKILL_NAME-audit-report.md"
fi

# Logging function
log_verbose() {
    if [[ "$VERBOSE" == true ]]; then
        echo -e "${BLUE}[INFO]${NC} $1"
    fi
}

log_check() {
    echo -e "${BLUE}ℹ️  $1${NC}"
}

# Initialize report
init_report() {
    cat > "$REPORT_FILE" << EOF
# Skill Audit Report: $SKILL_NAME

**Audit Date**: $(date +%Y-%m-%d)
**Skill Directory**: $SKILL_DIR
**Auditor**: Skill Auditor (Claude Code Meta-Skill)

---

## Executive Summary

EOF
}

# Check functions
check_yaml_frontmatter() {
    log_check "Checking YAML frontmatter..."
    local skill_md="$SKILL_DIR/SKILL.md"

    if [[ ! -f "$skill_md" ]]; then
        echo "❌ SKILL.md not found" >> "$REPORT_FILE"
        ((CRITICAL_ISSUES++))
        return 1
    fi

    # Check if YAML frontmatter exists
    if ! grep -q "^---$" "$skill_md"; then
        echo "❌ No YAML frontmatter found" >> "$REPORT_FILE"
        ((CRITICAL_ISSUES++))
        return 1
    fi

    # Extract frontmatter
    local yaml_content=$(sed -n '/^---$/,/^---$/p' "$skill_md" | sed '1d;$d')

    # Check required fields
    if ! echo "$yaml_content" | grep -q "^name:"; then
        echo "❌ Missing 'name' field in frontmatter" >> "$REPORT_FILE"
        ((CRITICAL_ISSUES++))
    else
        ((SCORE+=5))
    fi

    if ! echo "$yaml_content" | grep -q "^description:"; then
        echo "❌ Missing 'description' field in frontmatter" >> "$REPORT_FILE"
        ((CRITICAL_ISSUES++))
    else
        ((SCORE+=5))
    fi

    log_verbose "YAML frontmatter check complete"
}

check_required_sections() {
    log_check "Checking required sections..."
    local skill_md="$SKILL_DIR/SKILL.md"

    # Required sections
    local sections=("Workflow" "Instructions" "Example" "Error Handling" "Security")

    for section in "${sections[@]}"; do
        if grep -qi "##.*$section" "$skill_md"; then
            echo "✅ Found: $section section" >> "$REPORT_FILE"
            ((SCORE+=3))
        else
            if [[ "$section" == "Error Handling" ]] || [[ "$section" == "Security" ]]; then
                echo "❌ Missing critical section: $section" >> "$REPORT_FILE"
                ((CRITICAL_ISSUES++))
            else
                echo "⚠️  Missing recommended section: $section" >> "$REPORT_FILE"
                ((IMPORTANT_ISSUES++))
            fi
        fi
    done

    log_verbose "Required sections check complete"
}

check_hardcoded_paths() {
    log_check "Checking for hardcoded absolute paths..."
    local skill_md="$SKILL_DIR/SKILL.md"

    # Look for /Users/, /home/, C:\, etc.
    local hardcoded=$(grep -n "/Users/\|/home/\|C:\\\\" "$skill_md" 2>/dev/null || true)

    if [[ -n "$hardcoded" ]]; then
        echo "❌ Hardcoded absolute paths found:" >> "$REPORT_FILE"
        echo '```' >> "$REPORT_FILE"
        echo "$hardcoded" >> "$REPORT_FILE"
        echo '```' >> "$REPORT_FILE"
        echo "**Fix**: Use environment variables or relative paths" >> "$REPORT_FILE"
        ((CRITICAL_ISSUES++))
    else
        echo "✅ No hardcoded paths detected" >> "$REPORT_FILE"
        ((SCORE+=10))
    fi

    log_verbose "Hardcoded paths check complete"
}

check_security_keywords() {
    log_check "Checking security documentation..."
    local skill_md="$SKILL_DIR/SKILL.md"

    local security_keywords=("XSS" "sanitize" "validate" "escape" "security" "CSP")
    local found_keywords=0

    for keyword in "${security_keywords[@]}"; do
        if grep -qi "$keyword" "$skill_md"; then
            ((found_keywords++))
        fi
    done

    if [[ $found_keywords -ge 3 ]]; then
        echo "✅ Security considerations documented (found $found_keywords keywords)" >> "$REPORT_FILE"
        ((SCORE+=15))
    elif [[ $found_keywords -gt 0 ]]; then
        echo "⚠️  Limited security documentation (found $found_keywords keywords)" >> "$REPORT_FILE"
        ((IMPORTANT_ISSUES++))
        ((SCORE+=5))
    else
        echo "❌ No security documentation found" >> "$REPORT_FILE"
        ((CRITICAL_ISSUES++))
    fi

    log_verbose "Security keywords check complete"
}

check_ambiguous_terms() {
    log_check "Checking for ambiguous terminology..."
    local skill_md="$SKILL_DIR/SKILL.md"

    local ambiguous_terms=("simple" "complex" "appropriate" "reasonable" "good" "bad" "fast" "slow")
    local found_terms=()

    for term in "${ambiguous_terms[@]}"; do
        if grep -qi "\b$term\b" "$skill_md"; then
            local lines=$(grep -ni "\b$term\b" "$skill_md" | head -3)
            found_terms+=("$term")
        fi
    done

    if [[ ${#found_terms[@]} -eq 0 ]]; then
        echo "✅ No ambiguous terms detected" >> "$REPORT_FILE"
        ((SCORE+=10))
    else
        echo "⚠️  Ambiguous terms found: ${found_terms[*]}" >> "$REPORT_FILE"
        echo "**Recommendation**: Replace with specific metrics" >> "$REPORT_FILE"
        ((IMPORTANT_ISSUES++))
        ((SCORE+=3))
    fi

    log_verbose "Ambiguous terms check complete"
}

check_examples() {
    log_check "Checking for usage examples..."
    local skill_md="$SKILL_DIR/SKILL.md"

    local example_count=$(grep -ci "^###.*example\|^##.*example\|^#.*example" "$skill_md" 2>/dev/null || echo "0")
    example_count=$(echo "$example_count" | tr -d '\n' | tr -d ' ')

    if [[ $example_count -ge 2 ]]; then
        echo "✅ Sufficient examples ($example_count found)" >> "$REPORT_FILE"
        ((SCORE+=10))
    elif [[ $example_count -eq 1 ]]; then
        echo "⚠️  Only 1 example found, recommend at least 2" >> "$REPORT_FILE"
        ((IMPORTANT_ISSUES++))
        ((SCORE+=5))
    else
        echo "❌ No examples found" >> "$REPORT_FILE"
        ((IMPORTANT_ISSUES++))
    fi

    log_verbose "Examples check complete"
}

check_documentation() {
    log_check "Checking documentation files..."

    if [[ -f "$SKILL_DIR/README.md" ]]; then
        echo "✅ README.md exists" >> "$REPORT_FILE"
        ((SCORE+=5))
    else
        echo "⚠️  No README.md found" >> "$REPORT_FILE"
        ((SUGGESTIONS++))
    fi

    if [[ -f "$SKILL_DIR/QUICKSTART.md" ]] || grep -qi "quick.*start\|getting.*started" "$SKILL_DIR/SKILL.md"; then
        echo "✅ Quick start documentation found" >> "$REPORT_FILE"
        ((SCORE+=5))
    else
        echo "⚠️  No quick start guide" >> "$REPORT_FILE"
        ((SUGGESTIONS++))
    fi

    log_verbose "Documentation check complete"
}

check_scripts() {
    log_check "Checking scripts quality..."

    if [[ ! -d "$SKILL_DIR/scripts" ]]; then
        echo "ℹ️  No scripts directory (not required)" >> "$REPORT_FILE"
        return 0
    fi

    local script_count=$(find "$SKILL_DIR/scripts" -type f -name "*.sh" | wc -l | tr -d ' ')

    if [[ $script_count -eq 0 ]]; then
        return 0
    fi

    echo "Found $script_count shell scripts" >> "$REPORT_FILE"

    # Check each script
    find "$SKILL_DIR/scripts" -type f -name "*.sh" | while read -r script; do
        local script_name=$(basename "$script")

        # Check shebang
        if ! head -1 "$script" | grep -q "^#!"; then
            echo "⚠️  $script_name: Missing shebang" >> "$REPORT_FILE"
            ((IMPORTANT_ISSUES++))
        fi

        # Check error handling
        if ! grep -q "set -e" "$script"; then
            echo "⚠️  $script_name: Missing 'set -e' error handling" >> "$REPORT_FILE"
            ((IMPORTANT_ISSUES++))
        fi

        # Check executable permission
        if [[ ! -x "$script" ]]; then
            echo "⚠️  $script_name: Not executable (needs chmod +x)" >> "$REPORT_FILE"
            ((IMPORTANT_ISSUES++))
        fi
    done

    log_verbose "Scripts check complete"
}

# Generate final report
generate_report() {
    log_check "Generating final report..."

    # Calculate percentage
    local percentage=$((SCORE * 100 / MAX_SCORE))
    local status="❌ Critical Issues"

    if [[ $percentage -ge 90 ]]; then
        status="✅ Excellent"
    elif [[ $percentage -ge 75 ]]; then
        status="⚠️  Good"
    elif [[ $percentage -ge 60 ]]; then
        status="⚠️  Needs Improvement"
    fi

    # Update executive summary
    sed -i '' '/^## Executive Summary/,/^---/c\
## Executive Summary\
\
**Overall Score**: '"$SCORE"'/'"$MAX_SCORE"' ('"$percentage"'%) '"$status"'\
\
| Severity | Count |\
|----------|-------|\
| 🔴 Critical | '"$CRITICAL_ISSUES"' |\
| 🟡 Important | '"$IMPORTANT_ISSUES"' |\
| 🟢 Suggestions | '"$SUGGESTIONS"' |\
\
**Production Ready**: '"$([ $CRITICAL_ISSUES -eq 0 ] && echo "✅ Yes" || echo "❌ No - Fix critical issues first")"'\
\
---\
' "$REPORT_FILE" 2>/dev/null || {
        # If sed -i '' doesn't work (Linux), try without ''
        sed -i '/^## Executive Summary/,/^---/c\
## Executive Summary\
\
**Overall Score**: '"$SCORE"'/'"$MAX_SCORE"' ('"$percentage"'%) '"$status"'\
\
| Severity | Count |\
|----------|-------|\
| 🔴 Critical | '"$CRITICAL_ISSUES"' |\
| 🟡 Important | '"$IMPORTANT_ISSUES"' |\
| 🟢 Suggestions | '"$SUGGESTIONS"' |\
\
**Production Ready**: '"$([ $CRITICAL_ISSUES -eq 0 ] && echo "✅ Yes" || echo "❌ No - Fix critical issues first")"'\
\
---\
' "$REPORT_FILE"
    }

    # Add detailed sections
    {
        echo ""
        echo "## 1. Structure Integrity"
        echo ""
    } >> "$REPORT_FILE"

    {
        echo ""
        echo "## 2. Security Considerations"
        echo ""
    } >> "$REPORT_FILE"

    {
        echo ""
        echo "## 3. Error Handling"
        echo ""
    } >> "$REPORT_FILE"

    {
        echo ""
        echo "## 4. Portability"
        echo ""
    } >> "$REPORT_FILE"

    {
        echo ""
        echo "## 5. Quality & Clarity"
        echo ""
    } >> "$REPORT_FILE"

    {
        echo ""
        echo "## 6. Documentation"
        echo ""
    } >> "$REPORT_FILE"

    {
        echo ""
        echo "## Summary"
        echo ""
        echo "**Score Breakdown:**"
        echo "- Structure: Checked"
        echo "- Security: Checked"
        echo "- Error Handling: Checked"
        echo "- Portability: Checked"
        echo "- Quality: Checked"
        echo "- Documentation: Checked"
        echo ""
        echo "**Next Steps:**"
        if [[ $CRITICAL_ISSUES -gt 0 ]]; then
            echo "1. 🔴 Fix all $CRITICAL_ISSUES critical issues"
            echo "2. Review important issues"
            echo "3. Re-run audit"
        elif [[ $IMPORTANT_ISSUES -gt 0 ]]; then
            echo "1. 🟡 Consider fixing $IMPORTANT_ISSUES important issues"
            echo "2. Ready for production with minor improvements"
        else
            echo "1. ✅ Skill is production-ready!"
            echo "2. Consider suggestions for further improvement"
        fi
        echo ""
        echo "---"
        echo ""
        echo "**Generated by**: Skill Auditor"
        echo "**Report saved to**: $REPORT_FILE"
    } >> "$REPORT_FILE"
}

# Main execution
main() {
    echo -e "${BLUE}===================================================${NC}"
    echo -e "${BLUE}Skill Auditor${NC}"
    echo -e "${BLUE}===================================================${NC}"
    echo "Auditing skill: $SKILL_NAME"
    echo "Directory: $SKILL_DIR"
    echo ""

    init_report

    check_yaml_frontmatter
    check_required_sections
    check_hardcoded_paths
    check_security_keywords
    check_ambiguous_terms
    check_examples
    check_documentation
    check_scripts

    generate_report

    echo ""
    echo -e "${GREEN}✓${NC} Audit complete!"
    echo -e "${BLUE}Report saved to:${NC} $REPORT_FILE"
    echo ""
    echo "Summary:"
    echo "  Score: $SCORE/$MAX_SCORE ($((SCORE * 100 / MAX_SCORE))%)"
    echo "  Critical: $CRITICAL_ISSUES"
    echo "  Important: $IMPORTANT_ISSUES"
    echo "  Suggestions: $SUGGESTIONS"
    echo ""

    if [[ $CRITICAL_ISSUES -gt 0 ]]; then
        echo -e "${RED}⚠️  Critical issues found. Fix before sharing with team.${NC}"
        exit 1
    else
        echo -e "${GREEN}✅ No critical issues. Skill is production-ready!${NC}"
        exit 0
    fi
}

main
