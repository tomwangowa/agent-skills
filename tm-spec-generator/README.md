# Spec Generator

A Claude Code Skill that automatically generates comprehensive, production-ready specification documents from simple ideas using Claude's AI capabilities.

## Overview

**Spec Generator** transforms brief user ideas into complete specification documents with all 8 essential sections:

1. ✅ Background/Context
2. ✅ Requirements (Functional & Non-Functional)
3. ✅ Technical Design
4. ✅ Error Handling
5. ✅ Security Considerations
6. ✅ Testing Strategy
7. ✅ Deployment Plan
8. ✅ Success Metrics

**Key Advantage**: Uses Claude Code's AI capabilities directly - no external dependencies, more reliable output, better project context awareness.

## Quick Start

### No Installation Required!

This skill works out of the box with Claude Code. No need to install Gemini CLI or configure API keys!

### Usage

Simply tell Claude what you want to build:

```
Generate a spec for user authentication with OAuth support
```

```
I need a specification for implementing dark mode in my React app
```

```
Create a spec for adding Google Drive sync to my Prompt Optimizer app.
The app has Conversation and Classic modes. Currently prompts are saved
in local storage. I want to sync them to Google Drive.
```

That's it! Claude will:
1. 🤔 Understand your idea
2. 📝 Generate a complete 8-section specification
3. 💾 Save it to `docs/specs/` or `specs/` directory
4. ✅ Offer to validate with spec-review-assistant

## How It Works

### Workflow

```
User describes idea (brief or detailed)
    ↓
Claude analyzes and asks clarifying questions (if needed)
    ↓
Claude generates complete specification with all 8 sections
    ↓
Claude saves to docs/specs/[filename].md
    ↓
Claude offers to run spec-review-assistant for validation
```

### What Claude Generates

Every specification includes:

#### 1. Background/Context
- Current situation and limitations
- Problem statement
- Business value and ROI
- User impact
- Assumptions

#### 2. Requirements

**Functional Requirements** with acceptance criteria:
- FR-1, FR-2, FR-3... (specific, testable requirements)

**Non-Functional Requirements** with metrics:
- Performance: "p95 latency < 200ms" (not "fast")
- Scalability: "Handle 10,000 concurrent users" (not "scalable")
- Availability: "99.9% uptime"
- Security: Specific compliance standards
- Usability: Measurable targets

#### 3. Technical Design
- Architecture overview with data flow
- API endpoints (with examples)
- Data models and schemas
- UI components
- Technology stack with rationale
- Integration points

#### 4. Error Handling
- Input validation rules
- Edge case handling
- Failure scenarios and recovery
- Error messages
- Retry logic

#### 5. Security Considerations
- Authentication & authorization approach
- Data protection and encryption
- Input sanitization (XSS, SQL injection, CSRF)
- API security
- Compliance requirements

#### 6. Testing Strategy
- Unit tests scope and framework
- Integration tests approach
- E2E tests for critical flows
- Performance testing scenarios
- Test data management

#### 7. Deployment Plan
- Deployment strategy (blue-green, canary, etc.)
- Phased rollout timeline
- Database migrations
- Monitoring and alerting setup
- Rollback procedures

#### 8. Success Metrics
- Specific KPIs with targets
- Success criteria
- Monitoring dashboard design
- Review schedule

#### Bonus Sections
- **Tasks**: Implementation checklist
- **Open Questions & Risks**: Unknowns and mitigation
- **Dependencies**: External services, teams, libraries
- **Future Enhancements**: V2 features

## Features

### 🎯 No External Dependencies

- **No Gemini CLI required** - Uses Claude's native capabilities
- **No API keys needed** - Works directly in Claude Code
- **No installation** - Ready to use immediately

### 🧠 Intelligent Context Awareness

Claude automatically:
- Detects your project's tech stack
- Follows existing architectural patterns
- Uses appropriate terminology for your domain
- Makes reasonable assumptions based on best practices

### ✨ High-Quality Output

Generated specs:
- Use specific metrics (e.g., "p95 < 200ms" not "fast")
- Include concrete acceptance criteria
- Contain no placeholder text (no TODO/TBD)
- Are immediately actionable for teams
- Pass spec-review-assistant validation

### 🔄 Iterative Refinement

If needed:
- Ask Claude to expand specific sections
- Request more technical detail
- Add project-specific constraints
- Regenerate with different focus

## Examples

### Example 1: Simple Feature

**You say:**
```
Generate a spec for a logout button
```

**Claude generates:**
- Complete 150+ line spec
- Covers session cleanup, API endpoint, security
- Includes edge cases (concurrent sessions, token invalidation)
- Notes assumptions about auth mechanism

### Example 2: Complex Feature

**You say:**
```
I need a spec for real-time collaborative editing with live cursors,
instant sync, conflict resolution, and offline mode
```

**Claude generates:**
- Comprehensive 300+ line spec
- WebSocket or OT architecture
- Specific latency targets (< 100ms for cursors)
- CRDT/OT algorithm recommendations
- Offline queue design
- Conflict resolution strategies

### Example 3: With Project Context

**In a React project:**
```
Generate a spec for dark mode toggle
```

**Claude generates:**
- Spec tailored to React (hooks, context API)
- References your existing styling approach (Tailwind/CSS-in-JS)
- Follows your component naming patterns
- Integrates with your state management

## Best Practices

### For Better Input

✅ **Good Input:**
```
User authentication with OAuth support. Users should sign in with Google
and GitHub. Include email verification, password reset, and 2FA support.
Target response time < 200ms.
```

❌ **Too Brief:**
```
login page
```

**Tip:** If your input is brief, Claude will ask clarifying questions.

### For Better Specs

Mention in your idea:
- Target users or use cases
- Technical constraints or preferences
- Must-have vs nice-to-have features
- Integration requirements
- Performance or security needs

### For Team Adoption

1. Review generated specs with your team
2. Refine based on organizational standards
3. Use as living documents (update during implementation)
4. Build a library of past specs for reference

## Output Location

Claude automatically determines where to save:

1. Checks for `docs/specs/` directory
2. Falls back to `specs/` directory
3. Asks you if neither exists
4. Creates directory if you confirm

## File Naming

Claude suggests kebab-case filenames:
- "User Authentication" → `user-authentication-spec.md`
- "Google Drive Sync" → `google-drive-sync-spec.md`
- "Dark Mode Toggle" → `dark-mode-toggle-spec.md`

You can accept the suggestion or provide your own filename.

## Integration with spec-review-assistant

After generating, Claude offers to validate:

```
Would you like me to review this spec with spec-review-assistant?
```

If you agree:
1. Claude runs spec-review-assistant
2. Shows you the review report
3. Highlights any issues found
4. Offers to refine the spec if needed

### Complete Workflow Example

```
You: Generate a spec for Google Drive sync

Claude: I'll generate a comprehensive specification for Google Drive sync.
        I'll save it to docs/specs/google-drive-sync-spec.md

[Claude generates and saves complete spec]

Claude: ✅ Specification generated and saved!
        File: docs/specs/google-drive-sync-spec.md
        Content: ~350 lines with all 8 essential sections

        Would you like me to review this spec with spec-review-assistant?

You: yes

[Claude runs spec-review-assistant]

Claude: Review complete! 0 critical issues, 2 minor suggestions:
        - Consider adding more details on conflict resolution
        - Specify exact OAuth scopes needed

        Should I refine these sections?
```

## Advantages Over Script-Based Approach

| Aspect | Script-Based (Old) | Claude-Based (New) |
|--------|-------------------|--------------------|
| **Setup** | Requires Gemini CLI + API key | None - works immediately |
| **Context** | Limited to file scans | Full conversation + codebase |
| **Quality** | Depends on prompt engineering | Claude's native understanding |
| **Refinement** | Need to regenerate | Can iterate conversationally |
| **Reliability** | External API dependency | Built into Claude Code |

## Typical Output Size

- Simple features: 150-200 lines
- Medium features: 200-350 lines
- Complex features: 350-500+ lines

## Performance

- **Generation time**: 10-30 seconds (depending on complexity)
- **Quality**: Ready for team review
- **Success rate**: High (no external API failures)

## Limitations

- Requires being in a Claude Code conversation
- Best with at least 2-3 sentences of input
- Output quality depends on input clarity
- Technical recommendations based on common best practices (customize as needed)

## Tips & Tricks

### Get More Detailed Specs

```
Generate a detailed spec for [feature] with emphasis on security and scalability
```

### Project-Specific Specs

Make sure Claude has scanned your codebase:
```
First scan my project structure, then generate a spec for [feature]
that follows our existing patterns
```

### Iterate on Sections

```
Expand the Technical Design section with more details on the data model
```

```
Add more specific test scenarios to the Testing Strategy section
```

## Related Skills

### Recommended Workflow

1. **spec-generator** ← You are here
   - Generate initial specification

2. **spec-review-assistant**
   - Validate completeness and quality
   - Identify gaps or ambiguities

3. Refine spec based on review

4. **commit-msg-generator**
   - Commit the spec with proper message

5. Begin implementation

6. **pr-review-assistant**
   - Review implementation against spec

## Support

Since this skill uses Claude Code directly:
- No external dependencies to troubleshoot
- No API keys to configure
- No installation required

If you need help:
- Ask Claude to explain any section
- Request modifications or expansions
- Ask for examples or clarifications

---

**Happy Spec Writing! 📝✨**

_Powered by Claude Code - No external tools required!_
