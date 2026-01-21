# Spec Review Assistant

A Claude Code Skill for reviewing specification documents before implementation to identify gaps, ambiguities, and potential issues.

## Overview

**Spec Review Assistant** helps engineering teams catch specification problems early by performing automated analysis across five key dimensions:

1. ✅ **Completeness Check** - Identifies missing sections
2. 🎯 **Feasibility Assessment** - Evaluates technical approach
3. 🔍 **Clarity Check** - Detects ambiguous language
4. 📊 **Workload Estimation** - Analyzes task breakdown
5. 🔗 **Codebase Integration** - Verifies alignment with existing code

## Quick Start

### Prerequisites

```bash
# Install required tools
npm install -g @google/gemini-cli
brew install jq  # macOS
# OR
apt-get install jq  # Ubuntu

# Set Gemini API key
export GEMINI_API_KEY="your-api-key-here"
```

### Usage

#### Via Claude Code

Simply ask Claude to review your spec:

```
Review the spec in docs/user-auth-spec.md
```

```
Check if docs/payment-integration.md fits our existing architecture
```

#### Direct Script Usage

```bash
# Basic review
./scripts/review_spec.sh docs/my-spec.md

# With codebase integration
./scripts/review_spec.sh docs/my-spec.md --with-codebase

# Save report to file
./scripts/review_spec.sh docs/my-spec.md --output review-report.md
```

## What It Checks

### 1. Completeness Check ✅

Verifies presence of essential sections:
- Background/Context
- Requirements (functional & non-functional)
- Technical Design/Architecture
- API specifications
- Error handling strategy
- Security considerations
- Testing strategy
- Deployment plan
- Success metrics

### 2. Feasibility Assessment 🎯

AI-powered analysis of:
- Technology stack alignment
- Performance implications
- Scalability concerns
- Third-party dependency risks
- Timeline realism

### 3. Clarity Check 🔍

Detects:
- Vague terms: "fast", "simple", "appropriate"
- Undefined acronyms
- Contradictory statements
- Inconsistent terminology

### 4. Workload Estimation 📊

Analyzes task breakdown:
- Identifies overly broad tasks
- Suggests decomposition
- Flags missing subtasks (testing, docs, deployment)
- Assesses complexity

### 5. Codebase Integration 🔗

When using `--with-codebase`:
- Scans existing code patterns
- Compares naming conventions
- Identifies architectural deviations
- Suggests integration points

## Example Output

```markdown
# Spec Review Report: User Authentication

**Overall Assessment**: ⚠️ Needs Improvement
**Critical Issues**: 3
**Important Issues**: 7

## 1. Completeness Check

### ❌ Missing Sections (Critical)
- Error Handling Strategy
- Security Considerations

## 2. Feasibility Assessment

### 🔴 Database Schema Complexity
- Issue: Proposed schema requires 5 joins for main query
- Risk: Performance degradation at scale
- Recommendation: Consider denormalization or caching layer

## 3. Clarity Check

### Ambiguous Descriptions
- **Line 56**: "The system should respond quickly"
  Issue: "Quickly" is subjective
  Recommendation: Specify target: "p95 latency < 200ms"
```

## Configuration

### Environment Variables

```bash
# Required for AI-powered analysis
export GEMINI_API_KEY="your-api-key"

# Optional: Choose model
export GEMINI_MODEL="gemini-2.0-flash-exp"
```

## Troubleshooting

### "Gemini command not found"

```bash
npm install -g @google/gemini-cli
```

### "Missing GEMINI_API_KEY"

```bash
export GEMINI_API_KEY="your-key"
```

### "jq command not found"

```bash
# macOS
brew install jq

# Ubuntu/Debian
sudo apt-get install jq
```

## Related Skills

- **pr-review-assistant**: Reviews code changes in PRs
- **commit-msg-generator**: Generates conventional commit messages
- **code-review-gemini**: Reviews code quality with Gemini

**Use Spec Review Assistant BEFORE implementation**, and other skills DURING/AFTER implementation.

---

**Happy Spec Reviewing! 🎉**
