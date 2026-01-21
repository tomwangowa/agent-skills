#!/bin/bash

##############################################################################
# Spec Review Script
# Reviews specification documents for completeness, clarity, and feasibility
##############################################################################

set -euo pipefail

# Colors for output
RED='\033[0;31m'
YELLOW='\033[1;33m'
GREEN='\033[0;32m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Script directory
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

# Configuration
GEMINI_MODEL="${GEMINI_MODEL:-gemini-2.0-flash-exp}"
TEMP_DIR=$(mktemp -d)
trap 'rm -rf "$TEMP_DIR"' EXIT

##############################################################################
# Helper Functions
##############################################################################

print_header() {
    echo -e "${BLUE}===================================================${NC}"
    echo -e "${BLUE}$1${NC}"
    echo -e "${BLUE}===================================================${NC}"
}

print_error() {
    echo -e "${RED}❌ ERROR: $1${NC}" >&2
}

print_warning() {
    echo -e "${YELLOW}⚠️  WARNING: $1${NC}"
}

print_success() {
    echo -e "${GREEN}✅ $1${NC}"
}

print_info() {
    echo -e "${BLUE}ℹ️  $1${NC}" >&2
}

sanitize_json() {
    # Remove markdown code blocks and extract JSON
    # Handles cases like ```json ... ``` or just raw JSON
    # Only extracts the FIRST code block to avoid concatenation issues
    local input=$(cat)

    # Try to extract JSON from markdown code blocks (first block only)
    if echo "$input" | grep -q '```json'; then
        # Extract only the first ```json ... ``` block
        echo "$input" | awk '/```json/{flag=1;next}/```/{if(flag)exit}flag'
    elif echo "$input" | grep -q '```'; then
        # Extract only the first ``` ... ``` block
        echo "$input" | awk '/```/{if(!flag){flag=1;next}else{exit}}flag'
    else
        # Return as-is if no code blocks found
        echo "$input"
    fi
}

validate_json() {
    # Validate and clean JSON output from AI
    local file="$1"

    if [ ! -f "$file" ]; then
        echo '{"error": "Output file not found"}' > "$file"
        return 1
    fi

    # Check if valid JSON
    if ! jq empty "$file" 2>/dev/null; then
        print_warning "Invalid JSON response from AI, using fallback"
        echo '{"error": "Invalid JSON response from AI"}' > "$file"
        return 1
    fi

    return 0
}

usage() {
    cat << EOF
Usage: $0 <spec_file> [OPTIONS]

Review a specification document before implementation.

Arguments:
    spec_file           Path to the specification Markdown file

Options:
    --with-codebase     Scan existing codebase for integration analysis
    --output FILE       Write report to FILE (default: stdout)
    --format FORMAT     Output format: markdown (default), json, html
    -h, --help          Show this help message

Examples:
    $0 docs/user-auth-spec.md
    $0 docs/payment-spec.md --with-codebase
    $0 docs/api-spec.md --output review-report.md

Environment Variables:
    GEMINI_MODEL        Gemini model to use (default: gemini-2.0-flash-exp)
    GEMINI_API_KEY      Gemini API key (required)

EOF
}

check_dependencies() {
    local missing_deps=()

    if ! command -v gemini &> /dev/null; then
        missing_deps+=("gemini")
    fi

    if ! command -v jq &> /dev/null; then
        missing_deps+=("jq")
    fi

    if [ ${#missing_deps[@]} -gt 0 ]; then
        print_error "Missing required dependencies: ${missing_deps[*]}"
        echo ""
        echo "Install missing tools:"
        for dep in "${missing_deps[@]}"; do
            case $dep in
                gemini)
                    echo "  npm install -g @google/gemini-cli"
                    ;;
                jq)
                    echo "  brew install jq  # macOS"
                    echo "  apt-get install jq  # Ubuntu"
                    ;;
            esac
        done
        exit 1
    fi
}

##############################################################################
# Main Review Functions
##############################################################################

# 1. Completeness Check
check_completeness() {
    local spec_file="$1"
    local output_file="$TEMP_DIR/completeness.json"

    print_info "Running completeness check..."

    # Define expected sections
    local expected_sections=(
        "Background|Context|Overview"
        "Requirements|Specifications"
        "Technical Design|Architecture"
        "API|Interface"
        "Error Handling|Edge Cases"
        "Security"
        "Testing|Test Plan"
        "Deployment|Rollout"
        "Metrics|Success Criteria"
    )

    local missing_sections=()
    local present_sections=()

    # Check for each expected section
    for section_pattern in "${expected_sections[@]}"; do
        if grep -iE "^#{1,3}\s+([0-9]+\.\s+)?($section_pattern)" "$spec_file" > /dev/null; then
            present_sections+=("$section_pattern")
        else
            missing_sections+=("$section_pattern")
        fi
    done

    # Create JSON output
    local present_json="[]"
    local missing_json="[]"

    if [ ${#present_sections[@]} -gt 0 ]; then
        present_json="$(printf '%s\n' "${present_sections[@]}" | jq -R . | jq -s .)"
    fi

    if [ ${#missing_sections[@]} -gt 0 ]; then
        missing_json="$(printf '%s\n' "${missing_sections[@]}" | jq -R . | jq -s .)"
    fi

    jq -n \
        --argjson present "$present_json" \
        --argjson missing "$missing_json" \
        '{present: $present, missing: $missing}' > "$output_file"

    echo "$output_file"
}

# 2. Clarity Check - Find ambiguous language
check_clarity() {
    local spec_file="$1"
    local output_file="$TEMP_DIR/clarity.json"

    print_info "Running clarity check..."

    # Vague terms to detect
    local vague_terms=(
        "fast" "quick" "slow"
        "simple" "easy" "complex"
        "appropriate" "suitable" "reasonable"
        "small" "large" "big"
        "soon" "later" "eventually"
        "should be good" "might work" "probably"
    )

    local ambiguous_lines=()

    # Search for vague terms
    for term in "${vague_terms[@]}"; do
        while IFS=: read -r line_num line_text; do
            # Use jq to safely construct JSON object
            local item_json
            item_json=$(jq -n \
                --arg ln "$line_num" \
                --arg txt "$line_text" \
                --arg term "$term" \
                '{line: ($ln|tonumber), text: $txt, term: $term}')
            ambiguous_lines+=("$item_json")
        done < <(grep -inE "\b$term\b" "$spec_file" | head -20)
    done

    # Use Gemini to detect contradictions
    local contradictions_json="[]"
    if [ -n "${GEMINI_API_KEY:-}" ]; then
        contradictions_json=$(gemini -m "$GEMINI_MODEL" <<EOF | jq -Rs '.'
Analyze this specification document for contradictions and inconsistencies:

$(cat "$spec_file")

Return ONLY a JSON array of contradictions found, in this format:
[
  {
    "location1": "Line X or section name",
    "statement1": "First statement",
    "location2": "Line Y or section name",
    "statement2": "Contradicting statement",
    "explanation": "Why these contradict"
  }
]

If no contradictions found, return: []
EOF
)
    fi

    # Create JSON output
    local ambiguous_json="[]"
    if [ ${#ambiguous_lines[@]} -gt 0 ]; then
        ambiguous_json="$(printf '%s\n' "${ambiguous_lines[@]}" | jq -s .)"
    fi

    jq -n \
        --argjson ambiguous "$ambiguous_json" \
        --argjson contradictions "$contradictions_json" \
        '{ambiguous: $ambiguous, contradictions: $contradictions}' > "$output_file"

    echo "$output_file"
}

# 3. Feasibility Assessment
check_feasibility() {
    local spec_file="$1"
    local output_file="$TEMP_DIR/feasibility.json"

    print_info "Running feasibility assessment..."

    if [ -z "${GEMINI_API_KEY:-}" ]; then
        print_warning "Gemini API key not set, skipping AI-powered feasibility check"
        echo '{"concerns": [], "risks": [], "recommendations": []}' > "$output_file"
        echo "$output_file"
        return
    fi

    # Use Gemini for comprehensive feasibility analysis
    gemini -m "$GEMINI_MODEL" <<EOF | sanitize_json > "$output_file"
You are a senior software architect reviewing a technical specification.

Specification document:
$(cat "$spec_file")

Analyze the feasibility of this specification and return a JSON object with:
{
  "strengths": ["List of technical strengths"],
  "concerns": [
    {
      "title": "Concern title",
      "description": "What is the issue",
      "risk_level": "high|medium|low",
      "recommendation": "How to address it"
    }
  ],
  "dependencies": [
    {
      "name": "Dependency name",
      "type": "external API|library|service",
      "risk": "What could go wrong"
    }
  ],
  "scalability_concerns": ["Issues that may arise at scale"],
  "performance_concerns": ["Potential performance bottlenecks"]
}

Focus on: technical debt, performance, scalability, third-party risks, timeline realism.
Return ONLY valid JSON, no markdown formatting.
EOF

    validate_json "$output_file"
    echo "$output_file"
}

# 4. Workload Estimation
check_workload() {
    local spec_file="$1"
    local output_file="$TEMP_DIR/workload.json"

    print_info "Running workload analysis..."

    # Extract tasks (looking for task lists or numbered items)
    local tasks=()
    while IFS= read -r line; do
        tasks+=("$line")
    done < <(grep -E "^[-*] \[ \]|^[0-9]+\." "$spec_file" | head -30)

    if [ ${#tasks[@]} -eq 0 ]; then
        echo '{"task_count": 0, "analysis": "No tasks found in specification"}' > "$output_file"
        echo "$output_file"
        return
    fi

    if [ -z "${GEMINI_API_KEY:-}" ]; then
        echo "{\"task_count\": ${#tasks[@]}, \"tasks\": []}" > "$output_file"
        echo "$output_file"
        return
    fi

    # Use Gemini to analyze task breakdown
    gemini -m "$GEMINI_MODEL" <<EOF | sanitize_json > "$output_file"
You are a technical project manager reviewing a task breakdown.

Specification document:
$(cat "$spec_file")

Analyze the task breakdown and return JSON:
{
  "task_count": ${#tasks[@]},
  "well_defined_tasks": ["Tasks with clear scope"],
  "tasks_needing_decomposition": [
    {
      "task": "Original task description",
      "issue": "Why it needs breakdown",
      "suggested_subtasks": ["Subtask 1", "Subtask 2", "..."]
    }
  ],
  "missing_tasks": [
    {
      "category": "testing|documentation|deployment|etc",
      "tasks": ["Missing task 1", "Missing task 2"]
    }
  ],
  "complexity_assessment": {
    "underestimated_tasks": ["Tasks likely more complex than described"],
    "dependencies": ["Cross-task dependencies to consider"]
  }
}

Return ONLY valid JSON.
EOF

    validate_json "$output_file"
    echo "$output_file"
}

# 5. Codebase Integration Analysis
check_codebase_integration() {
    local spec_file="$1"
    local output_file="$TEMP_DIR/codebase.json"

    if [ ! -d ".git" ]; then
        echo '{"error": "Not a git repository, skipping codebase analysis"}' > "$output_file"
        echo "$output_file"
        return
    fi

    print_info "Scanning codebase for integration analysis..."

    # Find common patterns in codebase (supporting multiple languages)
    # Define file extensions by category
    local CODE_EXTENSIONS="ts|js|tsx|jsx|py|go|java|rb|php|rs|swift|kt|dart"
    local CPP_EXTENSIONS="c|cpp|cc|cxx|c++|h|hpp|m|mm"
    local WEB_EXTENSIONS="html|css|scss|sass|less|vue|svelte"
    local CONFIG_EXTENSIONS="json|yaml|yml|toml|xml"
    local SHELL_EXTENSIONS="sh|bash|zsh"

    local ALL_EXTENSIONS="$CODE_EXTENSIONS|$CPP_EXTENSIONS|$WEB_EXTENSIONS|$SHELL_EXTENSIONS"

    local source_files=""
    if git rev-parse --is-inside-work-tree >/dev/null 2>&1; then
        # Use git ls-files to respect .gitignore
        source_files=$(git ls-files | grep -E "\.($ALL_EXTENSIONS)$" | head -100)
    else
        # Fallback to find (excluding common directories)
        source_files=$(find . -type d \( -name "node_modules" -o -name ".git" -o -name "dist" -o -name "build" -o -name "vendor" -o -name ".next" -o -name "venv" -o -name "__pycache__" \) -prune \
            -o -type f \( \
                -name "*.ts" -o -name "*.js" -o -name "*.tsx" -o -name "*.jsx" \
                -o -name "*.py" -o -name "*.go" -o -name "*.java" -o -name "*.rb" \
                -o -name "*.php" -o -name "*.rs" -o -name "*.swift" -o -name "*.kt" \
                -o -name "*.c" -o -name "*.cpp" -o -name "*.cc" -o -name "*.h" \
                -o -name "*.m" -o -name "*.mm" -o -name "*.html" -o -name "*.css" \
            \) -print | head -100)
    fi

    local api_patterns=""
    local naming_conventions=""

    if [ -n "$source_files" ]; then
        # Extended patterns for multiple languages
        # JavaScript/TypeScript: export function/class
        # Python: def, class
        # Go: func
        # Java/Swift/Kotlin: public/private class, func
        # C/C++: void/int/class functions
        # Objective-C: @interface, @implementation
        api_patterns=$(echo "$source_files" | head -30 | xargs grep -h \
            -E "export.*(function|class)|^def |^class |^func |public (class|func|void|int)|@interface|@implementation|^fn " \
            2>/dev/null | head -30 || echo "")

        # Naming conventions (variables, constants)
        naming_conventions=$(echo "$source_files" | head -20 | xargs grep -h \
            -E "^(const|let|var) |^[A-Z_]+\s*=|^[a-z_]+\s*=|val |var |let " \
            2>/dev/null | head -30 || echo "")
    fi

    if [ -z "${GEMINI_API_KEY:-}" ]; then
        echo '{"alignment": "unknown", "suggestions": []}' > "$output_file"
        echo "$output_file"
        return
    fi

    # Analyze alignment
    gemini -m "$GEMINI_MODEL" <<EOF | sanitize_json > "$output_file"
You are reviewing how a new specification aligns with existing codebase patterns.

Specification:
$(cat "$spec_file")

Existing code patterns:
$api_patterns

$naming_conventions

Return JSON:
{
  "alignment_score": "good|fair|poor",
  "follows_conventions": ["What matches existing patterns"],
  "deviations": [
    {
      "spec_proposes": "What the spec suggests",
      "codebase_uses": "What the codebase currently uses",
      "recommendation": "Align with existing or document reason for change"
    }
  ],
  "integration_points": ["Suggested files/modules to integrate with"]
}

Return ONLY valid JSON.
EOF

    validate_json "$output_file"
    echo "$output_file"
}

##############################################################################
# Report Generation
##############################################################################

generate_report() {
    local spec_file="$1"
    local completeness_file="$2"
    local clarity_file="$3"
    local feasibility_file="$4"
    local workload_file="$5"
    local codebase_file="$6"

    local spec_name=$(basename "$spec_file" .md)
    local review_date=$(date +%Y-%m-%d)

    cat << EOF
# Spec Review Report: $spec_name

**Review Date**: $review_date
**Document**: $spec_file
**Reviewer**: Spec Review Assistant (Claude Code Skill)

---

## Executive Summary

EOF

    # Calculate metrics
    local critical_count=0
    local important_count=0
    local suggestion_count=0

    # Count issues from each check
    local missing_count=$(jq '.missing | length' "$completeness_file")
    local ambiguous_count=$(jq '.ambiguous | length' "$clarity_file")
    local concerns_count=$(jq '.concerns | length' "$feasibility_file" 2>/dev/null || echo "0")

    critical_count=$((missing_count))
    important_count=$((ambiguous_count + concerns_count))

    echo "**Critical Issues**: $critical_count"
    echo "**Important Issues**: $important_count"
    echo "**Suggestions**: $suggestion_count"
    echo ""

    if [ "$critical_count" -eq 0 ] && [ "$important_count" -eq 0 ]; then
        echo "**Overall Assessment**: ✅ Ready for Implementation"
    elif [ "$critical_count" -gt 0 ]; then
        echo "**Overall Assessment**: ⚠️  Needs Improvement - Address critical issues first"
    else
        echo "**Overall Assessment**: 🟡 Minor Issues - Consider addressing before implementation"
    fi

    echo ""
    echo "---"
    echo ""

    # 1. Completeness Section
    echo "## 1. Completeness Check"
    echo ""

    local present=$(jq -r '.present[]' "$completeness_file" 2>/dev/null)
    if [ -n "$present" ]; then
        echo "### ✅ Present Sections"
        jq -r '.present[] | "- \(.)"' "$completeness_file"
        echo ""
    fi

    local missing=$(jq -r '.missing[]' "$completeness_file" 2>/dev/null)
    if [ -n "$missing" ]; then
        echo "### ❌ Missing Sections (Critical)"
        jq -r '.missing[] | "- \(.)"' "$completeness_file"
        echo ""
        echo "**Recommendation**: Add sections covering these areas before implementation."
        echo ""
    fi

    echo "---"
    echo ""

    # 2. Feasibility Section
    echo "## 2. Feasibility Assessment"
    echo ""

    if [ -f "$feasibility_file" ] && [ "$(jq '.concerns' "$feasibility_file" 2>/dev/null)" != "null" ]; then
        jq -r '.strengths[]? | "### 🟢 Strength\n- \(.)\n"' "$feasibility_file" 2>/dev/null || true

        jq -r '.concerns[]? | "### 🔴 \(.title)\n- **Issue**: \(.description)\n- **Risk Level**: \(.risk_level)\n- **Recommendation**: \(.recommendation)\n"' "$feasibility_file" 2>/dev/null || true
    else
        echo "*Feasibility assessment skipped (requires Gemini API key)*"
        echo ""
    fi

    echo "---"
    echo ""

    # 3. Clarity Section
    echo "## 3. Clarity Check"
    echo ""

    local ambiguous=$(jq '.ambiguous[]?' "$clarity_file" 2>/dev/null)
    if [ -n "$ambiguous" ]; then
        echo "### Ambiguous Descriptions"
        jq -r '.ambiguous[] | "- **Line \(.line)**: \"\(.text)\" - Term: _\(.term)_"' "$clarity_file" | head -10
        echo ""
        echo "**Recommendation**: Replace vague terms with specific, measurable criteria."
        echo ""
    else
        echo "✅ No obviously ambiguous language detected."
        echo ""
    fi

    # Check for contradictions
    local contradictions=$(jq '.contradictions[]?' "$clarity_file" 2>/dev/null)
    if [ -n "$contradictions" ]; then
        echo "### Contradictions Found"
        jq -r '.contradictions[] | "- **\(.location1)** vs **\(.location2)**\n  - First: \(.statement1)\n  - Second: \(.statement2)\n  - Issue: \(.explanation)\n"' "$clarity_file" 2>/dev/null || true
        echo ""
        echo "**Recommendation**: Resolve these contradictions before implementation."
        echo ""
    fi

    echo "---"
    echo ""

    # 4. Workload Section
    echo "## 4. Workload Estimation"
    echo ""

    if [ -f "$workload_file" ]; then
        local task_count=$(jq -r '.task_count' "$workload_file")
        echo "**Total Tasks Found**: $task_count"
        echo ""

        if [ "$task_count" -gt 0 ]; then
            jq -r '.tasks_needing_decomposition[]? | "### ⚠️ Task Needs Breakdown: \(.task)\n- **Issue**: \(.issue)\n- **Suggested Subtasks**:\n\(.suggested_subtasks[] | "  - \(.)")\n"' "$workload_file" 2>/dev/null || echo "*Detailed analysis requires Gemini API*"
        else
            echo "*No formal task list found in specification*"
        fi
        echo ""
    fi

    echo "---"
    echo ""

    # 5. Codebase Integration (if applicable)
    if [ -f "$codebase_file" ] && [ "$(jq '.error' "$codebase_file" 2>/dev/null)" == "null" ]; then
        echo "## 5. Codebase Integration Analysis"
        echo ""

        jq -r '"**Alignment Score**: \(.alignment_score)\n"' "$codebase_file" 2>/dev/null || true
        jq -r '.follows_conventions[]? | "- ✅ \(.)"' "$codebase_file" 2>/dev/null || true
        echo ""
        jq -r '.deviations[]? | "### ⚠️ Deviation Detected\n- **Spec proposes**: \(.spec_proposes)\n- **Codebase uses**: \(.codebase_uses)\n- **Recommendation**: \(.recommendation)\n"' "$codebase_file" 2>/dev/null || true

        echo "---"
        echo ""
    fi

    # Summary
    echo "## Summary of Recommendations"
    echo ""
    echo "### 🔴 Critical (Must Fix Before Implementation)"
    jq -r '.missing[] | "- Add section: \(.)"' "$completeness_file" 2>/dev/null || true
    echo ""
    echo "### 🟡 Important (Address Soon)"
    echo "- Clarify ambiguous language"
    echo "- Address feasibility concerns"
    echo "- Break down complex tasks"
    echo ""
    echo "---"
    echo ""
    echo "**Generated by**: Spec Review Assistant"
    echo "**Powered by**: Gemini AI ($GEMINI_MODEL)"
}

##############################################################################
# Main Execution
##############################################################################

main() {
    # Parse arguments
    local spec_file=""
    local with_codebase=false
    local output_file=""

    while [[ $# -gt 0 ]]; do
        case $1 in
            -h|--help)
                usage
                exit 0
                ;;
            --with-codebase)
                with_codebase=true
                shift
                ;;
            --output)
                output_file="$2"
                shift 2
                ;;
            *)
                spec_file="$1"
                shift
                ;;
        esac
    done

    # Validate inputs
    if [ -z "$spec_file" ]; then
        print_error "Specification file required"
        usage
        exit 1
    fi

    if [ ! -f "$spec_file" ]; then
        print_error "File not found: $spec_file"
        exit 1
    fi

    # Check dependencies
    check_dependencies

    # Run checks
    print_header "Spec Review: $(basename "$spec_file")"

    completeness_result=$(check_completeness "$spec_file")
    clarity_result=$(check_clarity "$spec_file")
    feasibility_result=$(check_feasibility "$spec_file")
    workload_result=$(check_workload "$spec_file")

    if [ "$with_codebase" = true ]; then
        codebase_result=$(check_codebase_integration "$spec_file")
    else
        echo '{}' > "$TEMP_DIR/codebase.json"
        codebase_result="$TEMP_DIR/codebase.json"
    fi

    # Generate report
    print_header "Generating Report"

    if [ -n "$output_file" ]; then
        generate_report "$spec_file" "$completeness_result" "$clarity_result" "$feasibility_result" "$workload_result" "$codebase_result" > "$output_file"
        print_success "Report written to: $output_file"
    else
        generate_report "$spec_file" "$completeness_result" "$clarity_result" "$feasibility_result" "$workload_result" "$codebase_result"
    fi
}

# Run main function
main "$@"
