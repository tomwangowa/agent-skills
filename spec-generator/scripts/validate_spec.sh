#!/bin/bash

##############################################################################
# Spec Validation Script
# Validates that a specification has all required sections
# (Optional tool - Claude Code performs this check automatically)
##############################################################################

set -euo pipefail

# Colors
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m'

validate_spec() {
    local spec_file="$1"

    if [ ! -f "$spec_file" ]; then
        echo -e "${RED}❌ File not found: $spec_file${NC}"
        exit 1
    fi

    local required_sections=(
        "Background|Context"
        "Requirements"
        "Technical Design|Architecture"
        "Error Handling"
        "Security"
        "Testing"
        "Deployment"
        "Metrics|Success"
    )

    local errors=()
    local warnings=()

    # Check for required sections
    for section in "${required_sections[@]}"; do
        if ! grep -iE "^#{1,3}\s+([0-9]+\.\s+)?($section)" "$spec_file" > /dev/null; then
            errors+=("Missing section: $section")
        fi
    done

    # Check for placeholders
    if grep -E "(TODO|TBD|\[fill in\]|\[describe)" "$spec_file" > /dev/null; then
        warnings+=("Contains placeholder text (TODO/TBD)")
    fi

    # Check for vague terms
    if grep -iE "\b(fast|slow|quick|simple|easy|appropriate)\b" "$spec_file" > /dev/null; then
        warnings+=("Contains vague terms - use specific metrics")
    fi

    # Check minimum length
    local line_count=$(wc -l < "$spec_file")
    if [ "$line_count" -lt 100 ]; then
        warnings+=("Short spec ($line_count lines, recommend 150+)")
    fi

    # Report results
    if [ ${#errors[@]} -gt 0 ]; then
        echo -e "${RED}❌ Validation FAILED${NC}"
        printf '%s\n' "${errors[@]}" | sed 's/^/  - /'
        exit 1
    elif [ ${#warnings[@]} -gt 0 ]; then
        echo -e "${YELLOW}⚠️  Validation passed with warnings:${NC}"
        printf '%s\n' "${warnings[@]}" | sed 's/^/  - /'
        exit 0
    else
        echo -e "${GREEN}✅ Validation PASSED - Spec is complete!${NC}"
        exit 0
    fi
}

if [ $# -eq 0 ]; then
    echo "Usage: $0 <spec_file.md>"
    exit 1
fi

validate_spec "$1"
