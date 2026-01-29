---
name: spec-review-assistant
description: Review specification documents before implementation to identify gaps, ambiguities, and potential issues. Use when the user provides a spec document or asks to review requirements, design, or tasks.
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
   - Read the entire document using Read tool

2. **Perform multi-dimensional analysis** across all review dimensions:

   #### Dimension 1: Completeness Check
   Verify presence of essential sections:
   - ✅ **Background/Context**: Why this project exists
   - ✅ **Requirements**: Functional and non-functional requirements
   - ✅ **Technical Design**: Architecture, data models, APIs
   - ✅ **Error Handling**: Edge cases and error scenarios
   - ✅ **Security Considerations**: Auth, data protection, vulnerabilities
   - ✅ **Testing Strategy**: Unit, integration, E2E tests
   - ✅ **Deployment Plan**: How to roll out
   - ✅ **Success Metrics**: How to measure success

   Mark each as:
   - ✅ Present and complete
   - ⚠️ Present but incomplete
   - ❌ Missing (critical issue)

   #### Dimension 2: Feasibility Assessment
   Evaluate technical approach:
   - Technology choices alignment with stack
   - Performance implications (identify potential bottlenecks)
   - Scalability concerns (can it handle growth?)
   - Third-party dependencies risks (SLA, vendor lock-in)
   - Timeline realism (is the timeline feasible?)
   - Resource requirements (team size, skills needed)

   #### Dimension 3: Clarity Check
   Identify unclear descriptions:
   - **Vague terms**: "fast", "simple", "appropriate", "should be good", "user-friendly"
   - **Undefined acronyms or jargon**: Check for unexplained technical terms
   - **Contradictory statements**: Find conflicting requirements
   - **Inconsistent terminology**: Same concept with different names
   - **Missing acceptance criteria**: How to verify it's done?

   For each vague term, suggest specific, measurable criteria.

   #### Dimension 4: Workload Estimation
   Analyze task breakdown:
   - **Tasks too large**: Cannot be estimated accurately (> 3 days)
   - **Missing subtasks**: Testing, documentation, error handling not mentioned
   - **Underestimated complexity**: Looks simple but has hidden complexity
   - **Dependencies not accounted for**: Sequential dependencies ignored
   - **Suggested decomposition**: How to break down large tasks

   #### Dimension 5: Codebase Integration (Optional)
   If user requests alignment check with existing code:
   - Scan codebase structure using Glob
   - Check naming conventions consistency
   - Verify API design patterns match
   - Identify architectural misalignment
   - Suggest integration points

3. **Generate structured review report** (see Output Format below)

4. **Present findings** with severity levels:
   - 🔴 Critical (Must fix before implementation)
   - 🟡 Important (Address soon)
   - 🟢 Nice to have (Optional improvements)

5. **Offer next steps**:
   - Address specific issues
   - Generate improved version of spec
   - Add missing sections
   - Clarify ambiguous parts

---

## Output Format

Generate a structured Markdown report following this template:

```markdown
# Spec Review Report: [Document Name]

**Review Date**: YYYY-MM-DD
**Document**: [file path]
**Reviewer**: [Your Model Name]

---

## Executive Summary

**Overall Assessment**: ⚠️ [Ready / Needs Minor Improvements / Needs Major Improvements]
**Critical Issues**: N
**Important Issues**: N
**Suggestions**: N

**Recommendation**: [One-line recommendation]

---

## 1. Completeness Check

### ✅ Present Sections
- [List complete sections]

### ❌ Missing Sections (Critical)
1. **[Section Name]**
   - Impact: [Why this matters]
   - Recommendation: [What to add]

### ⚠️ Incomplete Sections
1. **[Section Name]** (Line X-Y)
   - Issue: [What's missing]
   - Recommendation: [How to complete]

---

## 2. Feasibility Assessment

### 🟢 Strengths
- [List positive aspects]

### 🔴 Concerns
1. **[Concern Title]** (Line X)
   - Issue: [What's the problem]
   - Risk: [What could go wrong]
   - Recommendation: [How to mitigate]

---

## 3. Clarity Check

### Ambiguous Descriptions
1. **Line X**: "[Vague quote]"
   - Issue: [Why it's unclear]
   - Recommendation: [Specific alternative]

### Contradictions
1. **Lines X vs Y**
   - Line X: "[Statement 1]"
   - Line Y: "[Statement 2]"
   - Recommendation: [How to resolve]

### Undefined Terms
- **[Term]** (Line X): [Clarification needed]

---

## 4. Workload Estimation

### ✅ Well-Defined Tasks
- [List clear tasks]

### ⚠️ Tasks Needing Decomposition
1. **"[Task name]"** (Task #X)
   - Too broad - suggest breakdown:
     - [Subtask 1]
     - [Subtask 2]
     - [Include testing, docs, error handling]

### Missing Tasks
- [List tasks not mentioned but necessary]

---

## 5. Codebase Integration Analysis

*(Only if --with-codebase requested)*

### ✅ Alignment with Existing Code
- [List matching patterns]

### ⚠️ Deviations Detected
1. **[Deviation Type]** (Line X)
   - Spec uses: [Proposed approach]
   - Codebase uses: [Current pattern]
   - Recommendation: [How to align]

---

## Summary of Recommendations

### 🔴 Critical (Must Fix Before Implementation)
1. [Critical issue 1]
2. [Critical issue 2]

### 🟡 Important (Address Soon)
1. [Important issue 1]
2. [Important issue 2]

### 🟢 Nice to Have
1. [Suggestion 1]
2. [Suggestion 2]

---

## Next Steps

1. **Immediate**: Address all critical issues
2. **Before kickoff**: Resolve important issues
3. **Optional**: Implement nice-to-have improvements
4. **Re-review**: Run this check again after updates

---

**Generated by**: Spec Review Assistant
**Powered by**: [Your Model Name] <noreply@example.com>
```

---

## Review Dimensions Deep Dive

### Completeness Checklist

Essential sections for a complete spec:

| Section | Purpose | Red Flags if Missing |
|---------|---------|---------------------|
| **Background** | Context and motivation | Team doesn't understand "why" |
| **Requirements** | What to build | Scope creep, missed features |
| **Technical Design** | How to build it | Architecture misalignment |
| **Error Handling** | Edge cases | Production crashes |
| **Security** | Threats and mitigations | Vulnerabilities |
| **Testing** | How to verify | Poor quality, bugs slip through |
| **Deployment** | How to ship | Launch delays, downtime |
| **Metrics** | How to measure success | No way to evaluate impact |

### Vague Terms to Watch For

| Vague Term | Better Alternative |
|------------|-------------------|
| "Fast" | "p95 latency < 200ms" |
| "Simple" | "< 3 user clicks to complete" |
| "User-friendly" | "WCAG 2.1 AA compliant" |
| "Scalable" | "Handle 10K concurrent users" |
| "Secure" | "OAuth 2.0 + JWT tokens" |
| "Available" | "99.9% uptime SLA" |
| "Handle errors appropriately" | "Log + retry 3x + user notification" |

### Task Size Guidelines

| Task Size | Characteristics | Action |
|-----------|----------------|--------|
| **Right-sized** | 1-3 days, clear acceptance criteria | ✅ Keep as-is |
| **Too large** | > 3 days, vague scope | ⚠️ Decompose |
| **Too small** | < 2 hours, trivial | 🟢 Consider grouping |

---

## Constraints

- Only works with Markdown (.md) files
- Best results with specs following a standard template
- Codebase integration requires access to project files
- Limited to text analysis (no visual design review)

---

## Trigger Phrases

Users can invoke this Skill by saying:
- "Review this spec"
- "Check my requirements document"
- "Audit this design doc"
- "Validate the specification"
- "Find gaps in this spec"
- "Is this spec ready for implementation?"

---

## Examples

### Example 1: Basic Spec Review

**User:**
> Review the spec in `docs/user-auth-spec.md`

**Your workflow:**
1. Read `docs/user-auth-spec.md` using Read tool
2. Analyze across all 5 dimensions
3. Identify missing sections (e.g., security considerations)
4. Find vague terms (e.g., "secure password storage")
5. Check task breakdown
6. Generate structured report
7. Present findings with severity levels

### Example 2: Spec Review with Codebase Integration

**User:**
> Check if `docs/payment-integration.md` fits our existing architecture

**Your workflow:**
1. Read `docs/payment-integration.md`
2. Scan existing codebase:
   ```bash
   # Find existing payment-related code
   find . -name "*payment*" -o -name "*billing*"
   ```
3. Check naming conventions:
   ```bash
   # See existing API patterns
   grep -r "export.*function" src/api/
   ```
4. Compare spec's proposed approach with existing patterns
5. Report both spec issues AND architectural alignment
6. Suggest integration points

### Example 3: Targeted Review

**User:**
> Does this spec have all the required sections?

**Your workflow:**
1. Read the spec
2. Run completeness check specifically
3. List present sections
4. List missing sections with impact
5. Suggest templates for missing parts

---

## Best Practices

### For Spec Authors

**Before requesting review:**
- ✅ Use clear, specific language
- ✅ Include acceptance criteria for each requirement
- ✅ Document assumptions explicitly
- ✅ Add diagrams for complex flows
- ✅ Define all acronyms and jargon

**After receiving review:**
- Address critical issues immediately
- Clarify ambiguous sections
- Add missing sections
- Re-run review to verify improvements

### For Reviewers (You)

**During review:**
- Be specific in feedback (include line numbers)
- Suggest concrete alternatives, not just problems
- Prioritize issues by severity
- Focus on preventing implementation issues

**When presenting:**
- Start with executive summary
- Highlight critical issues first
- Provide actionable recommendations
- Offer to help address issues

---

## Integration with Workflow

### Recommended Usage Pattern

```
1. Author writes spec →
2. Run Spec Review Skill →
3. Address issues →
4. Team review meeting →
5. Final approval →
6. Begin implementation
```

### When to Re-Review

- After addressing critical issues
- Before design review meetings
- When requirements change significantly
- Before implementation kickoff

---

## Common Patterns

### Missing Error Handling

**Symptom**: Spec describes happy path only

**Check for:**
- What happens if API call fails?
- What if user inputs invalid data?
- What if database is unavailable?
- What if third-party service times out?

**Recommendation**: Add "Error Scenarios" section

### Underestimated Tasks

**Symptom**: Tasks like "Build dashboard" or "Integrate payments"

**Hidden complexity:**
- Testing (unit, integration, E2E)
- Error handling for each feature
- Documentation
- Performance optimization
- Security hardening

**Recommendation**: Decompose into 1-3 day subtasks

### Contradictory Requirements

**Symptom**: Different sections conflict

**Examples:**
- "Real-time updates" vs "Poll every 30s"
- "High security" vs "Easy signup (no email verification)"
- "Fast" vs "Complex validation rules"

**Recommendation**: Clarify priority and resolve conflict

---

## Related Skills

- **spec-generator**: Generates initial spec from ideas
- **pr-review-assistant**: Reviews code changes
- **code-review-gemini**: Reviews code quality

**Workflow**: Use Spec Review Assistant BEFORE implementation, and PR Review Assistant DURING/AFTER implementation.

---

## When NOT to Use This Skill

- Reviewing code (use code-review skills instead)
- Generating specs (use spec-generator instead)
- Reviewing non-technical documents
- Reviewing visual designs (need different skill)
