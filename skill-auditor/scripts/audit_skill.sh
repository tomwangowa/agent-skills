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
MAX_SCORE=125
CRITICAL_ISSUES=0
IMPORTANT_ISSUES=0
SUGGESTIONS=0

# Skill archetype — detected from SKILL_DIR layout. See detect_archetype().
# Determines which checks apply and the score ceiling.
SKILL_ARCHETYPE="unknown"

# Output files
REPORT_FILE=""
BODY_FILE=""

# Cleanup temp files on exit
cleanup() {
    if [[ -n "$BODY_FILE" ]] && [[ -f "$BODY_FILE" ]]; then
        rm -f "$BODY_FILE"
    fi
}
trap cleanup EXIT

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

# Create temp file for body
BODY_FILE=$(mktemp)

# Logging functions
log_verbose() {
    if [[ "$VERBOSE" == true ]]; then
        echo -e "${BLUE}[INFO]${NC} $1"
    fi
}

log_check() {
    echo -e "${BLUE}ℹ️  $1${NC}"
}

# Detect skill archetype based on directory layout. Skills come in two flavors
# with very different audit needs:
#   - script-bearing: has executable scripts under scripts/ — needs Security,
#     Error Handling, README, etc. (full audit).
#   - pure-instruction: prompt-only — no I/O, no error surface of its own.
#     Security/Error Handling checks are category errors here; SKILL.md
#     itself serves as the README.
detect_archetype() {
    if [[ -d "$SKILL_DIR/scripts" ]]; then
        local script_count
        # Any non-hidden regular file in scripts/ counts. Broader than an
        # extension whitelist so .rb, .go, .php, extension-less scripts, etc.
        # don't slip past as pure-instruction and miss security/error-handling audit.
        script_count=$(find "$SKILL_DIR/scripts" -type f ! -name '.*' 2>/dev/null | wc -l | tr -d ' ')
        if [[ "$script_count" -gt 0 ]]; then
            SKILL_ARCHETYPE="script-bearing"
            MAX_SCORE=125
            return
        fi
    fi
    SKILL_ARCHETYPE="pure-instruction"
    # Pure-instruction skills can't earn points from checks that don't apply
    # to them. Subtract the inapplicable checks from the ceiling so the
    # percentage stays comparable across archetypes:
    #   - Error Handling section pass:        -10
    #   - Security section pass:              -10
    #   - Security keyword density (4+ kw):   -20
    #   - README.md present:                   -5
    #   - Quick start guide:                   -5
    #   - Script quality (no scripts):        -10
    MAX_SCORE=65
}

write_archetype_section() {
    echo "## Skill Archetype" >> "$BODY_FILE"
    echo "" >> "$BODY_FILE"
    if [[ "$SKILL_ARCHETYPE" == "script-bearing" ]]; then
        echo "**Detected**: \`script-bearing\` — has executable scripts under \`scripts/\`" >> "$BODY_FILE"
        echo "" >> "$BODY_FILE"
        echo "All checks apply (Security, Error Handling, Script Quality, README, etc.)." >> "$BODY_FILE"
    else
        echo "**Detected**: \`pure-instruction\` — no executable scripts" >> "$BODY_FILE"
        echo "" >> "$BODY_FILE"
        echo "Checks tailored for prompt-only skills:" >> "$BODY_FILE"
        echo "- Skipped: Security keyword density, README.md, Quick Start (SKILL.md serves as README)" >> "$BODY_FILE"
        echo "- Informational: missing Error Handling / Security sections (no I/O surface to document)" >> "$BODY_FILE"
    fi
    echo "" >> "$BODY_FILE"
}

# Check functions
check_yaml_frontmatter() {
    log_check "Checking YAML frontmatter..."
    echo "" >> "$BODY_FILE"
    echo "## 1. Structure Integrity" >> "$BODY_FILE"
    echo "" >> "$BODY_FILE"

    local skill_md="$SKILL_DIR/SKILL.md"

    if [[ ! -f "$skill_md" ]]; then
        echo "❌ **CRITICAL**: SKILL.md not found" >> "$BODY_FILE"
        ((CRITICAL_ISSUES++))
        return 1
    fi

    # Check if YAML frontmatter exists
    if ! grep -q "^---$" "$skill_md"; then
        echo "❌ **CRITICAL**: No YAML frontmatter found" >> "$BODY_FILE"
        ((CRITICAL_ISSUES++))
        return 1
    fi

    # Extract frontmatter
    local yaml_content=$(sed -n '/^---$/,/^---$/p' "$skill_md" | sed '1d;$d')

    # Check required fields
    if ! echo "$yaml_content" | grep -q "^name:"; then
        echo "❌ **CRITICAL**: Missing 'name' field in frontmatter" >> "$BODY_FILE"
        ((CRITICAL_ISSUES++))
    else
        # Extract name value (strip quotes and whitespace)
        local name_value=$(echo "$yaml_content" | grep "^name:" | sed 's/^name:[[:space:]]*//' | sed 's/^["'"'"']//' | sed 's/["'"'"']$//' | tr -d '[:space:]')

        # Validate name is kebab-case (lowercase letters, digits, hyphens only)
        if ! echo "$name_value" | grep -qE '^[a-z][a-z0-9]*(-[a-z0-9]+)*$'; then
            echo "❌ **CRITICAL**: 'name' field must be kebab-case (lowercase, hyphens). Found: \"$name_value\"" >> "$BODY_FILE"
            echo "**Fix**: Use lowercase words separated by hyphens (e.g., \"my-skill-name\")" >> "$BODY_FILE"
            ((CRITICAL_ISSUES++))
        # Validate name matches directory name
        elif [[ "$name_value" != "$SKILL_NAME" ]]; then
            echo "❌ **CRITICAL**: 'name' field (\"$name_value\") does not match directory name (\"$SKILL_NAME\")" >> "$BODY_FILE"
            echo "**Fix**: Rename to \"$SKILL_NAME\" to match the directory" >> "$BODY_FILE"
            ((CRITICAL_ISSUES++))
        else
            echo "✅ 'name' field present and valid (\"$name_value\")" >> "$BODY_FILE"
            ((SCORE+=5))
        fi
    fi

    if ! echo "$yaml_content" | grep -q "^description:"; then
        echo "❌ **CRITICAL**: Missing 'description' field in frontmatter" >> "$BODY_FILE"
        ((CRITICAL_ISSUES++))
    else
        echo "✅ 'description' field present" >> "$BODY_FILE"
        ((SCORE+=5))
    fi

    echo "" >> "$BODY_FILE"
    log_verbose "YAML frontmatter check complete"
}

check_description_voice() {
    log_check "Checking description voice..."
    echo "" >> "$BODY_FILE"
    echo "## 8. Description Voice" >> "$BODY_FILE"
    echo "" >> "$BODY_FILE"

    local skill_md="$SKILL_DIR/SKILL.md"

    # Extract frontmatter block (lines between the two --- delimiters)
    local frontmatter
    frontmatter=$(awk '/^---$/{if(found){exit}else{found=1;next}} found{print}' "$skill_md" 2>/dev/null || true)

    # Try to get first line of description value
    # Handle multiline (description: |) and single-line (description: text)
    local desc_first_line=""

    # Single-line: description: some text
    local single
    single=$(echo "$frontmatter" | grep "^description:" | sed 's/^description:[[:space:]]*//' | tr -d '"'"'" | head -1)
    if [[ -n "$single" ]] && [[ "$single" != "|" ]] && [[ "$single" != ">" ]]; then
        desc_first_line="$single"
    else
        # Multi-line: lines indented after description: |
        desc_first_line=$(echo "$frontmatter" | awk '/^description:/{found=1;next} found && /^[a-z]/{exit} found{print}' | \
            grep -v "^[[:space:]]*$" | head -1 | sed 's/^[[:space:]]*//')
    fi

    if [[ -z "$desc_first_line" ]]; then
        echo "ℹ️  Description field empty or missing (already flagged above)" >> "$BODY_FILE"
        echo "" >> "$BODY_FILE"
        log_verbose "Description voice check complete"
        return 0
    fi

    if echo "$desc_first_line" | grep -qiE "^(Use when|This skill[[:space:]])"; then
        echo "✅ Description uses correct third-person voice" >> "$BODY_FILE"
        ((SCORE+=5))
    else
        echo "⚠️  **IMPORTANT**: Description should start with \"Use when...\" or \"This skill...\"" >> "$BODY_FILE"
        echo "**Found**: \"$desc_first_line\"" >> "$BODY_FILE"
        echo "**Fix**: Rewrite description opening line to \"Use when [trigger conditions]\" or \"This skill [does X] when [conditions]\"" >> "$BODY_FILE"
        ((IMPORTANT_ISSUES++))
    fi

    echo "" >> "$BODY_FILE"
    log_verbose "Description voice check complete"
}

check_writing_style() {
    log_check "Checking writing style..."
    echo "" >> "$BODY_FILE"
    echo "## 9. Writing Style" >> "$BODY_FILE"
    echo "" >> "$BODY_FILE"

    local skill_md="$SKILL_DIR/SKILL.md"

    # Extract body: everything after the second --- (closing frontmatter)
    local body
    body=$(awk 'BEGIN{found=0} /^---$/{found++; if(found==2){skip=1; next}} skip{print}' "$skill_md" 2>/dev/null || true)

    if [[ -z "$body" ]]; then
        echo "ℹ️  Writing style: skipped (no frontmatter body found)" >> "$BODY_FILE"
        echo "" >> "$BODY_FILE"
        log_verbose "Writing style check complete"
        return 0
    fi

    # Count second-person phrases (case-insensitive)
    # grep exits 1 when no match; || true prevents set -e from aborting
    local count
    count=$(echo "$body" | { grep -oiE "you should|you can|you need to|you must|you will" 2>/dev/null || true; } | wc -l | tr -d '[:space:]')

    if [[ "$count" -le 3 ]]; then
        echo "✅ Writing style: imperative/third-person (second-person phrases: $count)" >> "$BODY_FILE"
        ((SCORE+=5))
    else
        echo "⚠️  **IMPORTANT**: Excessive second-person language detected ($count occurrences)" >> "$BODY_FILE"
        echo "**Fix**: Replace second-person with imperative form:" >> "$BODY_FILE"
        echo "- \"You should run...\" → \"Run...\"" >> "$BODY_FILE"
        echo "- \"You can use...\" → \"Use... or To use...\"" >> "$BODY_FILE"
        echo "- \"You need to configure...\" → \"Configure...\"" >> "$BODY_FILE"
        ((IMPORTANT_ISSUES++))
    fi

    echo "" >> "$BODY_FILE"
    log_verbose "Writing style check complete"
}

check_required_sections() {
    log_check "Checking required sections..."
    echo "## 2. Required Sections" >> "$BODY_FILE"
    echo "" >> "$BODY_FILE"

    local skill_md="$SKILL_DIR/SKILL.md"

    # Error Handling + Security sections.
    # Only required as CRITICAL on script-bearing skills (their scripts can
    # fail at runtime / read user input / make external calls). For
    # pure-instruction skills, missing these sections is informational —
    # the skill is just a prompt with no I/O surface of its own.
    local critical_sections=("Error Handling" "Security")
    for section in "${critical_sections[@]}"; do
        if grep -qi "##.*$section" "$skill_md"; then
            echo "✅ Found: **$section** section" >> "$BODY_FILE"
            # Only score on script-bearing — for pure-instruction these sections
            # aren't applicable, so writing them shouldn't earn or cost points
            # (otherwise the score ceiling overflows).
            if [[ "$SKILL_ARCHETYPE" == "script-bearing" ]]; then
                ((SCORE+=10))
            fi
        elif [[ "$SKILL_ARCHETYPE" == "script-bearing" ]]; then
            echo "❌ **CRITICAL**: Missing **$section** section" >> "$BODY_FILE"
            ((CRITICAL_ISSUES++))
        else
            echo "ℹ️  No **$section** section (pure-instruction skill — not required)" >> "$BODY_FILE"
        fi
    done

    # Instructional content: skills express instructions under varied names
    # ("Workflow", "Instructions", "Steps", "Decision Flow", "Quick Rules"…),
    # so we don't require a specific heading name. Pass if either:
    #   (a) any heading whose name signals instructions, OR
    #   (b) the body has ≥5 actionable list/step items (fallback signal).
    local instructional_heading_pattern='^#{2,6}[[:space:]]+.*\<(Workflow|Workflows|Instructions|Steps|Process|Procedure|Procedures|How[[:space:]]+(to|it[[:space:]]+works|this[[:space:]]+works)|Decision[[:space:]]*(Flow|Tree|Process)?|Decisions|Rules|Guidelines|Guidance|Behavior|Behaviour|Usage|Approach|Strategy|Recipe|Recipes|Playbook|Operating[[:space:]]+(Rules|Principles))\>'

    local has_instructional_heading=false
    if grep -qiE "$instructional_heading_pattern" "$skill_md"; then
        has_instructional_heading=true
    fi

    # Body = everything after the second --- (close of frontmatter)
    local body_content
    body_content=$(awk 'BEGIN{found=0} /^---$/{found++; if(found==2){skip=1; next}} skip{print}' "$skill_md" 2>/dev/null || true)
    local actionable_lines
    actionable_lines=$(echo "$body_content" | grep -cE '^[[:space:]]*([-*]|[0-9]+\.)[[:space:]]+' 2>/dev/null || echo 0)
    actionable_lines=${actionable_lines:-0}

    if [[ "$has_instructional_heading" == true ]]; then
        echo "✅ Found: instructional heading (Workflow/Instructions/Steps/Rules/…)" >> "$BODY_FILE"
        ((SCORE+=10))
    elif [[ "$actionable_lines" -ge 5 ]]; then
        echo "✅ Found: actionable content ($actionable_lines list/step items)" >> "$BODY_FILE"
        ((SCORE+=10))
    else
        echo "⚠️  **IMPORTANT**: No instructional content detected" >> "$BODY_FILE"
        echo "**Recommendation**: Add a section explaining how Claude should act on this skill (e.g., '## Workflow', '## Instructions', '## Decision Flow', or a list of actionable rules)" >> "$BODY_FILE"
        ((IMPORTANT_ISSUES++))
    fi

    # Examples are checked separately in check_examples() — don't double-count here.

    echo "" >> "$BODY_FILE"
    log_verbose "Required sections check complete"
}

check_hardcoded_paths() {
    log_check "Checking for hardcoded absolute paths..."
    echo "## 3. Portability" >> "$BODY_FILE"
    echo "" >> "$BODY_FILE"

    local skill_md="$SKILL_DIR/SKILL.md"

    # Look for /Users/, /home/, C:\, etc.
    local hardcoded=$(grep -n "/Users/\|/home/\|C:\\\\" "$skill_md" 2>/dev/null || true)

    if [[ -n "$hardcoded" ]]; then
        echo "❌ **CRITICAL**: Hardcoded absolute paths found:" >> "$BODY_FILE"
        echo '```' >> "$BODY_FILE"
        echo "$hardcoded" >> "$BODY_FILE"
        echo '```' >> "$BODY_FILE"
        echo "" >> "$BODY_FILE"
        echo "**Fix**: Use environment variables or relative paths" >> "$BODY_FILE"
        echo "**Example**: \`Style directory: \$STYLE_DIR (default: ./styles/)\`" >> "$BODY_FILE"
        ((CRITICAL_ISSUES++))
    else
        echo "✅ No hardcoded absolute paths detected" >> "$BODY_FILE"
        ((SCORE+=15))
    fi

    echo "" >> "$BODY_FILE"
    log_verbose "Hardcoded paths check complete"
}

check_security_keywords() {
    log_check "Checking security documentation..."
    echo "## 4. Security" >> "$BODY_FILE"
    echo "" >> "$BODY_FILE"

    local skill_md="$SKILL_DIR/SKILL.md"

    # Pure-instruction skills don't process user input, don't make external
    # calls, and don't execute scripts — keyword density says nothing about
    # their safety. Skip the check entirely instead of misleading the reader.
    if [[ "$SKILL_ARCHETYPE" != "script-bearing" ]]; then
        echo "ℹ️  Security keyword density check skipped (pure-instruction skill — no I/O surface)" >> "$BODY_FILE"
        echo "" >> "$BODY_FILE"
        log_verbose "Security keywords check skipped (pure-instruction)"
        return 0
    fi

    local security_keywords=("XSS" "sanitize" "validate" "escape" "security" "CSP")
    local found_keywords=0
    local found_list=""

    for keyword in "${security_keywords[@]}"; do
        if grep -qi "$keyword" "$skill_md"; then
            ((found_keywords++))
            found_list="$found_list $keyword"
        fi
    done

    if [[ $found_keywords -ge 4 ]]; then
        echo "✅ Strong security documentation (found keywords:$found_list)" >> "$BODY_FILE"
        ((SCORE+=20))
    elif [[ $found_keywords -ge 2 ]]; then
        echo "⚠️  **IMPORTANT**: Limited security documentation (found $found_keywords keywords:$found_list)" >> "$BODY_FILE"
        echo "**Recommendation**: Expand security section to cover XSS, input validation, URL/path safety" >> "$BODY_FILE"
        ((IMPORTANT_ISSUES++))
        ((SCORE+=10))
    else
        echo "❌ **CRITICAL**: Insufficient security documentation" >> "$BODY_FILE"
        echo "**Required**: Add Security Considerations section covering:" >> "$BODY_FILE"
        echo "- Input sanitization (HTML escaping, URL validation)" >> "$BODY_FILE"
        echo "- File path safety (directory traversal prevention)" >> "$BODY_FILE"
        echo "- External dependency risks" >> "$BODY_FILE"
        ((CRITICAL_ISSUES++))
    fi

    echo "" >> "$BODY_FILE"
    log_verbose "Security keywords check complete"
}

check_ambiguous_terms() {
    log_check "Checking for ambiguous terminology..."
    echo "## 5. Quality & Clarity" >> "$BODY_FILE"
    echo "" >> "$BODY_FILE"

    local skill_md="$SKILL_DIR/SKILL.md"

    local ambiguous_terms=("simple" "complex" "appropriate" "reasonable" "good" "bad" "fast" "slow" "quick")
    local found_any=false

    # Idiomatic compound terms — when the ambiguous word is part of a known
    # phrase used as a section title or accepted technical term, it's not a
    # vague descriptor. Keyed by term, value is an extended-regex alternation.
    local quick_whitelist='quick[- ]?(start|rules|reference|references|fix|fixes|check|checks|win|wins|guide|tour|notes|recap|summary|tip|tips|look|peek|review|sort|sand|action|actions)'

    for term in "${ambiguous_terms[@]}"; do
        # Word-boundary, case-insensitive match. Use explicit boundaries
        # ([^a-zA-Z0-9_]) for portability across grep implementations.
        local matches
        matches=$(grep -niE "(^|[^a-zA-Z0-9_])${term}([^a-zA-Z0-9_]|$)" "$skill_md" 2>/dev/null || true)

        # Exclude heading lines: section names like "## Quick rules" are
        # naming conventions, not vague descriptors.
        if [[ -n "$matches" ]]; then
            matches=$(echo "$matches" | grep -v ':[[:space:]]*#' || true)
        fi

        # Exclude idiomatic compound terms.
        if [[ -n "$matches" ]] && [[ "$term" == "quick" ]]; then
            matches=$(echo "$matches" | grep -viE "$quick_whitelist" || true)
        fi

        # Cap displayed matches.
        if [[ -n "$matches" ]]; then
            matches=$(echo "$matches" | head -5)
        fi

        if [[ -n "$matches" ]]; then
            if [[ "$found_any" == false ]]; then
                echo "⚠️  **IMPORTANT**: Ambiguous terms detected:" >> "$BODY_FILE"
                echo "" >> "$BODY_FILE"
                found_any=true
                ((IMPORTANT_ISSUES++))
            fi
            echo "**Term: \"$term\"**" >> "$BODY_FILE"
            echo '```' >> "$BODY_FILE"
            echo "$matches" | head -3 >> "$BODY_FILE"
            echo '```' >> "$BODY_FILE"
            echo "" >> "$BODY_FILE"
        fi
    done

    if [[ "$found_any" == true ]]; then
        echo "**Recommendation**: Replace with specific metrics:" >> "$BODY_FILE"
        echo "- \"simple\" → \"lightweight\" or \"straightforward (5-15 slides)\"" >> "$BODY_FILE"
        echo "- \"complex\" → \"requiring >30 seconds to explain\"" >> "$BODY_FILE"
        echo "- \"fast\" → \"< 1 second\"" >> "$BODY_FILE"
        echo "- \"quick\" → \"5-minute guide\"" >> "$BODY_FILE"
        ((SCORE+=3))
    else
        echo "✅ No ambiguous terms detected" >> "$BODY_FILE"
        ((SCORE+=10))
    fi

    echo "" >> "$BODY_FILE"
    log_verbose "Ambiguous terms check complete"
}

check_examples() {
    log_check "Checking for usage examples..."
    echo "## 6. Examples & Documentation" >> "$BODY_FILE"
    echo "" >> "$BODY_FILE"

    local skill_md="$SKILL_DIR/SKILL.md"

    local example_count=$(grep -ci "^###.*example\|^##.*example\|^#.*example" "$skill_md" 2>/dev/null || echo "0")
    example_count=$(echo "$example_count" | tr -d '\n' | tr -d ' ')

    if [[ $example_count -ge 3 ]]; then
        echo "✅ Excellent examples ($example_count found)" >> "$BODY_FILE"
        ((SCORE+=10))
    elif [[ $example_count -ge 2 ]]; then
        echo "✅ Sufficient examples ($example_count found)" >> "$BODY_FILE"
        ((SCORE+=8))
    elif [[ $example_count -eq 1 ]]; then
        echo "⚠️  **IMPORTANT**: Only 1 example found, recommend at least 2" >> "$BODY_FILE"
        ((IMPORTANT_ISSUES++))
        ((SCORE+=3))
    else
        echo "⚠️  **IMPORTANT**: No examples found" >> "$BODY_FILE"
        echo "**Recommendation**: Add at least 2-3 usage examples showing typical use cases" >> "$BODY_FILE"
        ((IMPORTANT_ISSUES++))
    fi

    echo "" >> "$BODY_FILE"
    log_verbose "Examples check complete"
}

check_documentation() {
    log_check "Checking documentation files..."

    # README.md and a separate quick-start guide make sense for skills with
    # supporting scripts (where users may need install/usage docs beyond
    # SKILL.md). For pure-instruction skills, SKILL.md *is* the README —
    # requiring a duplicate file would be busywork.
    if [[ "$SKILL_ARCHETYPE" == "script-bearing" ]]; then
        if [[ -f "$SKILL_DIR/README.md" ]]; then
            echo "✅ README.md exists" >> "$BODY_FILE"
            ((SCORE+=5))
        else
            echo "⚠️  **SUGGESTION**: No README.md found" >> "$BODY_FILE"
            echo "**Recommendation**: Create README.md with quick start, features, and troubleshooting" >> "$BODY_FILE"
            ((SUGGESTIONS++))
        fi

        if [[ -f "$SKILL_DIR/QUICKSTART.md" ]] || grep -qi "quick.*start\|getting.*started" "$SKILL_DIR/SKILL.md" 2>/dev/null; then
            echo "✅ Quick start documentation found" >> "$BODY_FILE"
            ((SCORE+=5))
        else
            echo "⚠️  **SUGGESTION**: No quick start guide" >> "$BODY_FILE"
            ((SUGGESTIONS++))
        fi
    else
        echo "ℹ️  README.md / quick-start checks skipped (pure-instruction skill — SKILL.md serves as README)" >> "$BODY_FILE"
    fi

    # Progressive Disclosure check
    if [[ -f "$SKILL_DIR/SKILL.md" ]]; then
        local skill_md_lines
        skill_md_lines=$(wc -l < "$SKILL_DIR/SKILL.md" | tr -d ' ')
        if [[ -d "$SKILL_DIR/references" ]]; then
            echo "✅ Uses \`references/\` directory (Progressive Disclosure pattern)" >> "$BODY_FILE"
        elif [[ "$skill_md_lines" -gt 200 ]]; then
            echo "⚠️  **SUGGESTION**: SKILL.md is $skill_md_lines lines with no \`references/\` directory" >> "$BODY_FILE"
            echo "**Recommendation**: Move large reference sections to \`references/\` to keep SKILL.md lean and context-efficient" >> "$BODY_FILE"
            ((SUGGESTIONS++))
        fi
    fi

    echo "" >> "$BODY_FILE"
    log_verbose "Documentation check complete"
}

check_scripts() {
    log_check "Checking scripts quality..."
    echo "## 7. Script Quality" >> "$BODY_FILE"
    echo "" >> "$BODY_FILE"

    if [[ ! -d "$SKILL_DIR/scripts" ]]; then
        echo "ℹ️  No scripts directory (not required)" >> "$BODY_FILE"
        echo "" >> "$BODY_FILE"
        return 0
    fi

    local script_count=$(find "$SKILL_DIR/scripts" -type f -name "*.sh" 2>/dev/null | wc -l | tr -d ' ')

    if [[ $script_count -eq 0 ]]; then
        echo "ℹ️  No shell scripts found in scripts/" >> "$BODY_FILE"
        echo "" >> "$BODY_FILE"
        return 0
    fi

    echo "Found $script_count shell script(s)" >> "$BODY_FILE"
    echo "" >> "$BODY_FILE"

    local scripts_score=0
    local max_scripts_score=$((script_count * 3))  # 3 points per script for perfect quality

    # Check each script
    find "$SKILL_DIR/scripts" -type f -name "*.sh" | while read -r script; do
        local script_name=$(basename "$script")
        echo "**Script: $script_name**" >> "$BODY_FILE"

        # Check shebang
        if head -1 "$script" | grep -q "^#!"; then
            echo "- ✅ Has shebang" >> "$BODY_FILE"
            ((scripts_score++))
        else
            echo "- ⚠️  Missing shebang" >> "$BODY_FILE"
            ((IMPORTANT_ISSUES++))
        fi

        # Check error handling
        if grep -q "set -e" "$script"; then
            echo "- ✅ Has error handling (set -e)" >> "$BODY_FILE"
            ((scripts_score++))
        else
            echo "- ⚠️  Missing 'set -e' error handling" >> "$BODY_FILE"
            ((IMPORTANT_ISSUES++))
        fi

        # Check executable permission
        if [[ -x "$script" ]]; then
            echo "- ✅ Executable permission set" >> "$BODY_FILE"
            ((scripts_score++))
        else
            echo "- ⚠️  Not executable (run: chmod +x $script_name)" >> "$BODY_FILE"
            ((IMPORTANT_ISSUES++))
        fi

        echo "" >> "$BODY_FILE"
    done

    # Add scripts score to total
    if [[ $max_scripts_score -gt 0 ]]; then
        local scripts_percentage=$((scripts_score * 100 / max_scripts_score))
        if [[ $scripts_percentage -ge 80 ]]; then
            ((SCORE+=10))
        elif [[ $scripts_percentage -ge 60 ]]; then
            ((SCORE+=7))
        elif [[ $scripts_percentage -ge 40 ]]; then
            ((SCORE+=4))
        fi
    fi

    log_verbose "Scripts check complete"
}

# Generate final report
generate_report() {
    log_check "Generating final report..."

    # Calculate percentage and status
    local percentage=$((SCORE * 100 / MAX_SCORE))
    local status="❌ Critical Issues"

    if [[ $percentage -ge 90 ]]; then
        status="✅ Excellent"
    elif [[ $percentage -ge 75 ]]; then
        status="⚠️  Good"
    elif [[ $percentage -ge 60 ]]; then
        status="⚠️  Needs Improvement"
    fi

    # Production ready?
    local prod_ready="❌ No - Fix critical issues first"
    if [[ $CRITICAL_ISSUES -eq 0 ]]; then
        prod_ready="✅ Yes"
    fi

    # Write complete report
    cat > "$REPORT_FILE" << EOF
# Skill Audit Report: $SKILL_NAME

**Audit Date**: $(date +%Y-%m-%d)
**Skill Directory**: $SKILL_DIR
**Auditor**: Skill Auditor (Claude Code Meta-Skill)

---

## Executive Summary

**Overall Score**: $percentage/100 $status

| Severity | Count |
|----------|-------|
| 🔴 Critical | $CRITICAL_ISSUES |
| 🟡 Important | $IMPORTANT_ISSUES |
| 🟢 Suggestions | $SUGGESTIONS |

**Production Ready**: $prod_ready

---

EOF

    # Append body content
    cat "$BODY_FILE" >> "$REPORT_FILE"

    # Append summary
    cat >> "$REPORT_FILE" << EOF

## Summary

**Score Breakdown:**
- Structure Integrity: Checked
- Required Sections: Checked
- Portability: Checked
- Security: Checked
- Quality & Clarity: Checked
- Documentation: Checked
- Script Quality: Checked

**Next Steps:**
EOF

    if [[ $CRITICAL_ISSUES -gt 0 ]]; then
        cat >> "$REPORT_FILE" << EOF
1. 🔴 Fix all $CRITICAL_ISSUES critical issue(s)
2. Review $IMPORTANT_ISSUES important issue(s)
3. Re-run audit to verify fixes
4. Target score: 85+ for production quality
EOF
    elif [[ $IMPORTANT_ISSUES -gt 0 ]]; then
        cat >> "$REPORT_FILE" << EOF
1. 🟡 Consider fixing $IMPORTANT_ISSUES important issue(s)
2. Current score: $percentage% - Good for production
3. Optional: Address suggestions for excellence
EOF
    else
        cat >> "$REPORT_FILE" << EOF
1. ✅ Skill is production-ready!
2. Score: $percentage% - Excellent quality
3. Optional: Consider suggestions for further polish
EOF
    fi

    cat >> "$REPORT_FILE" << EOF

---

**Generated by**: Skill Auditor v1.0.0
**Report saved to**: $REPORT_FILE
EOF
}

# Main execution
main() {
    echo -e "${BLUE}===================================================${NC}"
    echo -e "${BLUE}Skill Auditor${NC}"
    echo -e "${BLUE}===================================================${NC}"
    echo "Auditing skill: $SKILL_NAME"
    echo "Directory: $SKILL_DIR"

    detect_archetype
    echo "Archetype: $SKILL_ARCHETYPE (max score ceiling: $MAX_SCORE)"
    echo ""

    write_archetype_section

    # Run all checks (they write to BODY_FILE)
    check_yaml_frontmatter
    check_required_sections
    check_hardcoded_paths
    check_security_keywords
    check_ambiguous_terms
    check_examples
    check_documentation
    check_scripts
    check_description_voice
    check_writing_style

    # Generate complete report
    generate_report

    echo ""
    echo -e "${GREEN}✓${NC} Audit complete!"
    echo -e "${BLUE}Report saved to:${NC} $REPORT_FILE"
    echo ""
    echo "Summary:"
    echo "  Score: $((SCORE * 100 / MAX_SCORE))/100"
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
