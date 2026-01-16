---
name: spec-review-assistant
description: Review specification documents before implementation to identify gaps, ambiguities, and potential issues. Use when the user provides a spec document or asks to review requirements, design, or tasks.
id: tm-spec-review-assistant
namespace: tm
domain: spec
action: review
qualifier: assistant
version: "1.0.0"
updated: "2026-01-17"
---

# Spec Review Assistant

## Purpose

This Skill performs pre-implementation reviews of specification documents to:
1. **Completeness Check**: Identify missing sections or information
2. **Feasibility Assessment**: Evaluate technical approach and identify risks
3. **Clarity Check**: Detect ambiguous descriptions and contradictions
4. **Workload Estimation**: Assess task breakdown and identify missing subtasks
5. **Codebase Integration** (Optional): Verify alignment with existing architecture

The Skill helps prevent costly rework by catching specification gaps early.

---

## Instructions

When the user requests a spec review (for example: "review this spec", "check my requirements doc", "audit this design document"), follow these steps:

### Execution Steps

1. **Locate the specification document**
   - Ask for the file path if not provided
   - Confirm the document format (should be Markdown)
   - Read the entire document

2. **Run the review script**
   ```bash
   bash scripts/review_spec.sh <spec_file_path> [--with-codebase]
   ```
   - Use `--with-codebase` flag if reviewing for an existing project
   - The script will analyze the document across all dimensions

3. **Present the structured review report**
   - Display the complete report with severity levels
   - Highlight critical issues first
   - Provide actionable recommendations

4. **Offer next steps**
   - Ask if the user wants to:
     - Address specific issues
     - Generate an improved version of the spec
     - Add missing sections
     - Clarify ambiguous parts

### Review Dimensions

#### 1. Completeness Check
Verifies presence of essential sections:
- **Background/Context**: Why this project exists
- **Requirements**: Functional and non-functional requirements
- **Technical Design**: Architecture, data models, APIs
- **Error Handling**: Edge cases and error scenarios
- **Security Considerations**: Auth, data protection, vulnerabilities
- **Testing Strategy**: Unit, integration, E2E tests
- **Deployment Plan**: How to roll out
- **Success Metrics**: How to measure success

#### 2. Feasibility Assessment
Evaluates technical approach:
- Technology choices alignment with stack
- Performance implications
- Scalability concerns
- Third-party dependencies risks
- Timeline realism
- Resource requirements

#### 3. Clarity Check
Identifies unclear descriptions:
- Vague terms: "fast", "simple", "appropriate", "should be good"
- Undefined acronyms or jargon
- Contradictory statements
- Inconsistent terminology
- Missing acceptance criteria

#### 4. Workload Estimation
Analyzes task breakdown:
- Tasks too large to estimate
- Missing subtasks (testing, documentation, error handling)
- Underestimated complexity
- Dependencies not accounted for
- Suggested task decomposition

#### 5. Codebase Integration (Optional)
When `--with-codebase` is used:
- Scan existing code structure
- Compare naming conventions
- Check API design patterns
- Identify architectural misalignment
- Suggest integration points

id: tm-spec-review-assistant
namespace: tm
domain: spec
action: review
qualifier: assistant
version: "1.0.0"
updated: "2026-01-17"
---

## Output Format

The script generates a structured Markdown report:

```markdown
# Spec Review Report: [Document Name]

**Review Date**: YYYY-MM-DD
**Document Version**: [if specified]
**Reviewer**: Spec Review Assistant

---

## Executive Summary

**Overall Assessment**: ⚠️ Needs Improvement
**Critical Issues**: 3
**Important Issues**: 7
**Suggestions**: 12

**Recommendation**: Address critical and important issues before implementation.

id: tm-spec-review-assistant
namespace: tm
domain: spec
action: review
qualifier: assistant
version: "1.0.0"
updated: "2026-01-17"
---

## 1. Completeness Check

### ✅ Present Sections
- Background
- Requirements
- Technical Design

### ❌ Missing Sections (Critical)
1. **Error Handling Strategy**
   - Impact: High risk of undefined behavior
   - Recommendation: Add section covering error scenarios, retry logic, fallback behavior

2. **Security Considerations**
   - Impact: Potential vulnerabilities
   - Recommendation: Document authentication, authorization, input validation, data encryption

### ⚠️ Incomplete Sections
1. **Requirements** (Line 23-45)
   - Issue: Missing non-functional requirements
   - Recommendation: Add performance, scalability, availability requirements

---

## 2. Feasibility Assessment

### 🟢 Strengths
- Technology stack is well-established
- Architecture follows existing patterns

### 🔴 Concerns
1. **Database Schema Complexity** (Line 89)
   - Issue: Proposed schema requires 5 joins for main query
   - Risk: Performance degradation at scale
   - Recommendation: Consider denormalization or caching layer

2. **Third-Party API Dependency** (Line 112)
   - Issue: Critical flow depends on external service with 99% SLA
   - Risk: 1% downtime = user-facing failures
   - Recommendation: Implement circuit breaker and fallback mechanism

id: tm-spec-review-assistant
namespace: tm
domain: spec
action: review
qualifier: assistant
version: "1.0.0"
updated: "2026-01-17"
---

## 3. Clarity Check

### Ambiguous Descriptions
1. **Line 56**: "The system should respond quickly"
   - Issue: "Quickly" is subjective
   - Recommendation: Specify target: "p95 latency < 200ms"

2. **Line 78**: "Handle errors appropriately"
   - Issue: "Appropriately" is undefined
   - Recommendation: Specify: log, retry, user notification strategy

### Contradictions
1. **Lines 34 vs 67**
   - Line 34: "Real-time updates required"
   - Line 67: "Polling every 30 seconds"
   - Recommendation: Clarify: use WebSocket for real-time or adjust requirement

### Undefined Terms
- **MTP** (Line 45): Not defined - clarify if "Minimum Testable Product"
- **Quantum sync** (Line 92): Unclear technical term

---

## 4. Workload Estimation

### Task Breakdown Analysis

#### ✅ Well-Defined Tasks
- "Implement user authentication API" - clear scope

#### ⚠️ Tasks Needing Decomposition
1. **"Build dashboard"** (Task #3)
   - Too broad - suggest breakdown:
     - Design dashboard layout
     - Implement data fetching layer
     - Create chart components
     - Add filtering and sorting
     - Write unit tests
     - Add E2E tests

2. **"Integrate payment gateway"** (Task #5)
   - Missing subtasks:
     - Research gateway options
     - Handle webhook setup
     - Implement refund flow
     - Add fraud detection
     - Test in sandbox

#### Missing Tasks
- Database migration scripts
- API documentation
- Monitoring and alerting setup
- Performance testing
- Security audit

id: tm-spec-review-assistant
namespace: tm
domain: spec
action: review
qualifier: assistant
version: "1.0.0"
updated: "2026-01-17"
---

## 5. Codebase Integration Analysis

### Alignment with Existing Code
✅ **Follows existing patterns**:
- REST API conventions match current endpoints
- Error response format consistent

⚠️ **Deviations detected**:
1. **Naming Convention** (Line 89)
   - Spec uses: `getUserData()`
   - Codebase uses: `fetchUserProfile()`
   - Recommendation: Align with `fetch*` pattern

2. **Database Access**
   - Spec proposes: Direct SQL queries
   - Current pattern: ORM (Prisma)
   - Recommendation: Use existing ORM or document rationale for change

---

## Summary of Recommendations

### 🔴 Critical (Must Fix Before Implementation)
1. Add error handling strategy section
2. Document security considerations
3. Define ambiguous performance requirements
4. Clarify contradictions (real-time vs polling)

### 🟡 Important (Address Soon)
1. Decompose overly broad tasks
2. Add missing testing and documentation tasks
3. Specify concrete acceptance criteria
4. Align naming conventions with codebase

### 🟢 Nice to Have
1. Add sequence diagrams for complex flows
2. Include rollback procedures
3. Document monitoring strategy

id: tm-spec-review-assistant
namespace: tm
domain: spec
action: review
qualifier: assistant
version: "1.0.0"
updated: "2026-01-17"
---

## Next Steps

1. **Immediate**: Address all critical issues
2. **Before kickoff**: Resolve important issues
3. **Optional**: Implement nice-to-have improvements
4. **Re-review**: Run this check again after updates

---

**Generated by**: Spec Review Assistant (Claude Code Skill)
**Powered by**: Gemini AI for semantic analysis
```

id: tm-spec-review-assistant
namespace: tm
domain: spec
action: review
qualifier: assistant
version: "1.0.0"
updated: "2026-01-17"
---

## Constraints

- Only works with Markdown (.md) files
- Requires Gemini CLI for AI-powered semantic analysis
- Codebase integration requires being run from project root
- Best results with specs following a standard template

---

## Trigger Phrases

Users can invoke this Skill by saying:
- "Review this spec"
- "Check my requirements document"
- "Audit this design doc"
- "Validate the specification"
- "Find gaps in this spec"
- "Is this spec ready for implementation?"

id: tm-spec-review-assistant
namespace: tm
domain: spec
action: review
qualifier: assistant
version: "1.0.0"
updated: "2026-01-17"
---

## Examples

### Example 1: Basic Spec Review

**User:**
> Review the spec in `docs/user-auth-spec.md`

**Expected behavior:**
1. Read the spec document
2. Run `review_spec.sh docs/user-auth-spec.md`
3. Display structured review report
4. Offer to help address identified issues

---

### Example 2: Spec Review with Codebase Integration

**User:**
> Check if `docs/payment-integration.md` fits our existing architecture

**Expected behavior:**
1. Read the spec document
2. Run `review_spec.sh docs/payment-integration.md --with-codebase`
3. Scan existing codebase for patterns
4. Report both spec issues and architectural alignment
5. Suggest integration points

id: tm-spec-review-assistant
namespace: tm
domain: spec
action: review
qualifier: assistant
version: "1.0.0"
updated: "2026-01-17"
---

### Example 3: Targeted Review

**User:**
> Does this spec have all the required sections?

**Expected behavior:**
1. Run completeness check specifically
2. List missing sections
3. Suggest templates for missing parts

---

## Best Practices

### For Spec Authors
- Use clear, specific language
- Include acceptance criteria
- Document assumptions explicitly
- Add diagrams for complex flows

### For Reviewers
- Run this check before design review meetings
- Address critical issues first
- Use the report as discussion guide
- Re-run after making changes

id: tm-spec-review-assistant
namespace: tm
domain: spec
action: review
qualifier: assistant
version: "1.0.0"
updated: "2026-01-17"
---

## Integration with Workflow

### Recommended Usage Pattern

```
1. Author writes spec → 2. Run Spec Review Skill → 3. Address issues →
4. Team review meeting → 5. Final approval → 6. Begin implementation
```

### Git Hook Integration (Optional)

Add to `.git/hooks/pre-commit`:
```bash
# Auto-review specs before committing
if [[ "$file" == docs/specs/*.md ]]; then
  claude-skill spec-review-assistant "$file"
fi
```

---

## Future Enhancements

- Support for other formats (Google Docs, Notion)
- Template library for common spec types
- Automated spec improvement suggestions
- Integration with project management tools
- Historical analysis (compare spec vs actual implementation)

id: tm-spec-review-assistant
namespace: tm
domain: spec
action: review
qualifier: assistant
version: "1.0.0"
updated: "2026-01-17"
---

## Related Skills

- **pr-review-assistant**: Reviews code changes
- **commit-msg-generator**: Generates commit messages
- **code-review-gemini**: Reviews code quality

Use Spec Review Assistant BEFORE implementation, and PR Review Assistant DURING/AFTER implementation.
