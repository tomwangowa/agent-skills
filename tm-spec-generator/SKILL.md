---
name: spec-generator
description: Generate complete specification documents from simple ideas. Use this Skill when the user wants to create a spec, needs a project specification, wants to document requirements, or asks to generate a specification document.
id: tm-spec-generator
namespace: tm
domain: spec
action: generator
version: "1.0.0"
updated: "2026-01-17"
---

# Spec Generator

## Purpose

This Skill transforms brief ideas or descriptions into comprehensive, production-ready specification documents by:
1. Using Claude's capabilities to generate complete, structured specifications
2. Ensuring all 8 essential sections are populated with meaningful content
3. Automatically saving to the project's appropriate directory
4. Producing specifications ready for spec-review-assistant validation

The Skill eliminates the need for manual specification writing by generating comprehensive documents from simple user ideas.

---

## Instructions

When the user expresses intent to generate a specification (for example: "generate a spec for X", "create specification for Y", "I need a spec document", "write a requirements doc for Z"), follow these steps strictly.

### Step 1: Capture and understand the idea

- The user's idea is already in the conversation context
- If the idea is very brief (< 2 sentences), ask clarifying questions:
  - What problem does this solve?
  - Who are the target users?
  - Are there any technical constraints?
  - Are there must-have vs nice-to-have features?
- If the idea is detailed, proceed directly to generation

### Step 2: Determine output location and filename

- Check if project has `docs/specs/` directory using Glob tool
- If not found, check for `specs/` directory
- Default to `docs/specs/` if neither exists (you will create it)
- Suggest a filename in kebab-case based on the feature name:
  - "User Authentication" → `user-authentication-spec.md`
  - "Google Drive Sync" → `google-drive-sync-spec.md`
  - "Dark Mode Toggle" → `dark-mode-toggle-spec.md`
- Ask user to confirm the filename or provide their preferred name

### Step 3: Gather project context (if applicable)

If generating a spec for an existing project:
- Use Glob to identify tech stack (package.json, go.mod, Gemfile, etc.)
- Use Grep to find existing patterns (components, APIs, naming conventions)
- Note the framework/language in use
- This context will help generate project-specific recommendations

### Step 4: Generate the complete specification

Using your capabilities as Claude, generate a comprehensive specification document with ALL 8 essential sections fully populated:

#### 1. Background/Context
- **Current State**: Describe what exists today, what users can/cannot do
- **Problem Statement**: What pain point does this solve?
- **Business Value**: Why is this worth building? ROI?
- **User Impact**: How will this improve UX?
- **Assumptions**: What are we assuming about users, tech, constraints?

#### 2. Requirements

**Functional Requirements** (FR-1, FR-2, etc.):
- Each requirement must be specific and testable
- Include clear acceptance criteria
- Cover: core functionality, user interactions, data operations, integrations, edge cases

**Non-Functional Requirements** (NFR-1, NFR-2, etc.):
- **NFR-1: Performance** - Use specific metrics: "p95 latency < 200ms" NOT "fast"
- **NFR-2: Scalability** - Specific numbers: "Handle 10,000 concurrent users"
- **NFR-3: Availability** - Percentage: "99.9% uptime"
- **NFR-4: Security** - Compliance standards, encryption requirements
- **NFR-5: Usability** - Measurable: "< 3 clicks to complete task"
- **NFR-6: Compatibility** - Specific: "Chrome, Firefox, Safari (latest 2 versions)"

#### 3. Technical Design
- **Architecture Overview**: High-level system components and data flow
- **API Endpoints** (if applicable): REST/GraphQL endpoints with examples
- **Data Models**: Database schemas, entity relationships
- **UI Components** (if applicable): Component structure, props, state
- **Technology Stack**: Specific libraries/frameworks with rationale
- **Integration Points**: How this connects with existing systems

#### 4. Error Handling
- **Input Validation**: Specific validation rules for each input
- **Edge Cases**: List concrete edge cases and how to handle them
- **Failure Scenarios**: What can go wrong? How to detect and recover?
- **Error Messages**: User-facing messages (clear, actionable)
- **Retry Logic**: When and how to retry failed operations

#### 5. Security Considerations
- **Authentication & Authorization**: How users auth, permission model
- **Data Protection**: Encryption (at rest/in transit), PII handling, GDPR
- **Input Sanitization**: XSS, SQL injection, CSRF prevention
- **API Security**: Rate limiting, token management, secure headers
- **Compliance**: Regulatory requirements (GDPR, HIPAA, SOC 2, etc.)

#### 6. Testing Strategy
- **Unit Tests**: What to test, coverage goals, test framework
- **Integration Tests**: What integrations, mock strategy
- **E2E Tests**: Critical user flows, test tools (Playwright, Cypress)
- **Performance Tests**: Load testing scenarios, stress testing
- **Test Environment**: Setup requirements, data management

#### 7. Deployment Plan
- **Strategy**: Blue-green, canary, rolling, or feature flags (with reasoning)
- **Rollout Phases**: Timeline, user segments (internal → beta → 100%)
- **Database Migrations**: Migration steps, rollback procedures
- **Monitoring & Alerts**: What to monitor, alert thresholds
- **Rollback Plan**: Trigger conditions, steps, time target

#### 8. Success Metrics
- **KPIs**: Specific metrics with targets (response time, error rate, adoption)
- **Success Criteria**: Quantifiable thresholds that define success
- **Monitoring Dashboard**: What metrics to display
- **Review Schedule**: When/how to review metrics

#### Additional Sections (also include these)
- **Tasks**: Checkbox task breakdown for implementation
- **Open Questions & Risks**: Unknowns, risks, and mitigation strategies
- **Dependencies**: External services, teams, libraries
- **Future Enhancements**: Out-of-scope features for v2

### Step 5: Quality checks before saving

Ensure your generated specification:
- ✅ Has ALL 8 numbered sections (## 1. through ## 8.)
- ✅ Each section has substantial content (not just examples or placeholders)
- ✅ Uses specific metrics (e.g., "p95 < 200ms" not "fast")
- ✅ Contains NO placeholder text (no "TODO", "TBD", "[fill in]", "[describe]")
- ✅ Is at least 150 lines of comprehensive content
- ✅ Uses the format: `## 1. Background/Context`, `## 2. Requirements`, etc.

### Step 6: Save the specification

- Use the Write tool to save the generated spec to the determined location
- If the output directory doesn't exist, you may need to create it or inform the user
- Confirm the file was saved successfully

### Step 7: Present results and next steps

Your response should include:

1. **Confirmation**: "Specification generated and saved successfully"
2. **File location**: Full path to the saved spec
3. **Brief summary**: What was generated (e.g., "Google Drive sync spec with OAuth authentication, conflict resolution, and offline support")
4. **Sections included**: Confirm all 8 main sections are present
5. **Statistics**: Approximate line count or content volume
6. **Next steps**: Offer to:
   - Run spec-review-assistant to validate completeness
   - Make refinements based on feedback
   - Commit the spec to git

id: tm-spec-generator
namespace: tm
domain: spec
action: generator
version: "1.0.0"
updated: "2026-01-17"
---

## Quality Standards

Your generated specifications must meet these standards:

### Content Quality
- **Be Specific**: Use concrete metrics, not vague terms
  - ❌ "The system should respond quickly"
  - ✅ "API response time p95 < 200ms"
- **Be Comprehensive**: All 8 sections with detailed content (minimum 150 lines total)
- **Be Actionable**: Provide concrete implementation guidance
- **Be Realistic**: Consider real-world constraints and trade-offs

### Formatting
- Use markdown headers: `# Feature Specification: [Title]`
- Number main sections: `## 1. Background/Context`, `## 2. Requirements`, etc.
- Use subsections with `###` for organization
- Use lists, code blocks, and tables where appropriate
- Include document metadata at the end (version, date, author, status)

### Completeness
- Every functional requirement must have acceptance criteria
- Every non-functional requirement must have measurable targets
- Every design decision must explain "why"
- Every risk must have mitigation strategy
- Tasks must be broken down and actionable

---

## Example Interaction

**User:**
> Generate a spec for implementing Google Drive sync in my Prompt Optimizer app. The app has Conversation mode and Classic mode. Currently prompts are saved in local storage or exported as JSON. I want to sync them to Google Drive.

**Your Actions:**
1. ✅ Understand the idea (already clear enough)
2. ✅ Check for `docs/specs/` or `specs/` directory
3. ✅ Suggest filename: `google-drive-sync-spec.md`
4. ✅ (Optional) Scan project for tech stack if it exists
5. ✅ Generate complete 8-section specification covering:
   - Background: Current local storage limitations
   - Requirements: OAuth auth, auto-sync, offline mode, conflict resolution
   - Technical Design: Google Drive API integration, sync architecture
   - Error Handling: Network failures, quota limits, conflicts
   - Security: OAuth scopes, token storage, data encryption
   - Testing: Unit/integration/E2E tests
   - Deployment: Feature flag rollout
   - Success Metrics: Adoption rate, sync success rate, performance
   - Tasks: Broken down implementation tasks
   - Risks: API changes, quota limits, user privacy concerns
6. ✅ Save using Write tool to `docs/specs/google-drive-sync-spec.md`
7. ✅ Confirm saved and offer to run spec-review-assistant

**Your Response:**
```
Specification generated and saved successfully! ✅

**File**: docs/specs/google-drive-sync-spec.md
**Summary**: Google Drive sync spec with OAuth authentication, bidirectional sync,
conflict resolution, offline support, and phased rollout plan.

**Sections included**:
✅ 1. Background/Context
✅ 2. Requirements (8 functional, 6 non-functional)
✅ 3. Technical Design (Google Drive API integration)
✅ 4. Error Handling (network, conflicts, quota limits)
✅ 5. Security Considerations (OAuth 2.0, data encryption)
✅ 6. Testing Strategy (unit, integration, E2E)
✅ 7. Deployment Plan (3-phase rollout)
✅ 8. Success Metrics (adoption, sync success rate)

**Additional sections**: Tasks, Open Questions & Risks, Dependencies, Future Enhancements

**Content**: ~350 lines

Would you like me to review this spec with spec-review-assistant to validate completeness?
```

id: tm-spec-generator
namespace: tm
domain: spec
action: generator
version: "1.0.0"
updated: "2026-01-17"
---

## Constraints

- Must generate all 8 essential sections
- Must use specific, measurable criteria (not vague terms)
- Must contain no placeholder text (TODO/TBD)
- Should be 150+ lines of substantive content
- Should pass spec-review-assistant with minimal critical issues

---

## Edge Cases

### Very Brief Input
**User:** "login page"

**Your Action:**
- Ask clarifying questions:
  - "What authentication methods? (email/password, OAuth, SSO?)"
  - "What features needed? (remember me, password reset, 2FA?)"
  - "Any specific security requirements?"
- Then generate comprehensive spec with reasonable assumptions
- Note assumptions in "Open Questions" section

### Very Detailed Input
**User:** [3 paragraphs of detailed requirements]

**Your Action:**
- Extract and organize all details into appropriate sections
- Use user's specific requirements as FR-1, FR-2, etc.
- Expand with standard best practices (security, testing, deployment)

### No Project Directory
**User:** Generating spec outside a project

**Your Action:**
- Ask where to save the spec, or default to `~/specs/`
- Generate generic best-practices spec (not project-specific)
- Note: "Generic implementation - adapt to your tech stack"

id: tm-spec-generator
namespace: tm
domain: spec
action: generator
version: "1.0.0"
updated: "2026-01-17"
---

## Integration with spec-review-assistant

After generating the spec, always offer to validate it:

```
Would you like me to review this spec with spec-review-assistant?
```

If user agrees:
1. Run the spec-review-assistant skill on the generated file
2. Display the review results
3. If critical issues found, offer to refine the spec
4. Iterate until spec passes validation

---

## Best Practices

### For Generation
- Always include specific numbers and metrics
- Base technical choices on project context (if available)
- Consider real-world constraints (budget, timeline, resources)
- Include both happy path and error scenarios
- Think about security from the start

### For User Guidance
- Encourage users to provide at least 2-3 sentences
- Ask for clarification on ambiguous points before generating
- Suggest reviewing with team before implementation
- Recommend iterating on the spec based on feedback

id: tm-spec-generator
namespace: tm
domain: spec
action: generator
version: "1.0.0"
updated: "2026-01-17"
---

## Related Skills

- **spec-review-assistant**: Validates generated specs for completeness
- **commit-msg-generator**: Commits the spec with proper message
- **pr-review-assistant**: Reviews implementation code against spec

**Recommended Workflow:**
1. **spec-generator** → Create specification
2. **spec-review-assistant** → Validate it
3. Refine based on feedback
4. **commit-msg-generator** → Commit the spec
5. Begin implementation
6. **pr-review-assistant** → Review code against spec

---

## Example Output Structure

When you generate a spec, it should look like this:

```markdown
# Feature Specification: [Feature Name]

## 1. Background/Context

**Current State**: [Detailed current situation]

**Problem Statement**: [Clear problem definition]

**Business Value**: [Why build this]

**User Impact**: [How users benefit]

**Assumptions**: [What we're assuming]

## 2. Requirements

### Functional Requirements
- **FR-1**: [Specific requirement]
  - Acceptance Criteria: [How to verify it's done]
- **FR-2**: [Another requirement]
  - Acceptance Criteria: [Verification method]

### Non-Functional Requirements
- **NFR-1: Performance** - API p95 latency < 200ms, page load < 2s
- **NFR-2: Scalability** - Support 10,000 concurrent users
- **NFR-3: Availability** - 99.9% uptime (8.7h downtime/year)
- **NFR-4: Security** - SOC 2 compliant, HTTPS only, JWT tokens
- **NFR-5: Usability** - < 3 clicks for core tasks, mobile-responsive

## 3. Technical Design

[Architecture, APIs, data models, components, technology stack]

## 4. Error Handling

[Validation, edge cases, failures, retry logic, error messages]

## 5. Security Considerations

[Auth, data protection, sanitization, compliance]

## 6. Testing Strategy

[Unit, integration, E2E, performance tests]

## 7. Deployment Plan

[Strategy, phases, migrations, monitoring, rollback]

## 8. Success Metrics

[KPIs, success criteria, monitoring dashboard]

## Tasks
- [ ] [Implementation tasks]
- [ ] [Testing tasks]
- [ ] [Deployment tasks]

## Open Questions & Risks
[Questions needing answers, risks and mitigation]

## Dependencies
[External services, teams, libraries]

## Future Enhancements
[V2 features, nice-to-haves]
```

id: tm-spec-generator
namespace: tm
domain: spec
action: generator
version: "1.0.0"
updated: "2026-01-17"
---

## Important Notes

- You (Claude Code) are generating the specification content directly
- Do NOT call external scripts or Gemini CLI
- Use your own knowledge and understanding to create comprehensive specs
- The spec should be immediately useful for engineering teams
- Quality over speed - take time to create thorough documentation
- If you're unsure about technical details, note them in "Open Questions"

---

## Validation Before Saving

Before using Write tool to save the spec, verify:
1. All 8 numbered sections (## 1. through ## 8.) are present
2. Each section has substantial content (not just headers)
3. No TODO, TBD, or [placeholder] text
4. Specific metrics used instead of vague terms
5. Total content is comprehensive (aim for 150+ lines)

If any check fails, regenerate that section before saving.

id: tm-spec-generator
namespace: tm
domain: spec
action: generator
version: "1.0.0"
updated: "2026-01-17"
---

## After Saving

Always offer these next steps:
1. **Review with spec-review-assistant**: "Would you like me to validate this spec for completeness?"
2. **Refinement**: "Would you like me to expand any particular section?"
3. **Team review**: "I recommend sharing this with your team for feedback"
4. **Git commit**: "Should I commit this spec to version control?"
