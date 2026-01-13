# Skills Roadmap

This document tracks all skill ideas, their current status, and implementation priority.

## Status Legend

- 🟢 **Implemented** - Completed and available
- 🟡 **In Progress** - Currently being developed
- 🔵 **Planned** - Approved for implementation
- ⚪ **Idea** - Proposed but not yet prioritized
- 🔴 **Blocked** - Waiting for dependencies or decisions

---

## Implemented Skills

### 🟢 code-review-gemini
**Status:** Implemented
**Category:** Code Quality
**Trigger:** "review the staged files", "check code quality"

Performs automated code reviews on staged changes using Gemini CLI.

**Features:**
- Analyzes git diff
- Identifies bugs, security issues, and best practices
- Prioritized findings (high/medium/low)
- Clear actionable feedback

**Dependencies:** Gemini CLI, Git

---

### 🟢 commit-msg-generator
**Status:** Implemented
**Category:** Development Workflow
**Trigger:** "generate commit message", "help me write commit message"

Generates high-quality commit messages following Conventional Commits specification.

**Features:**
- Analyzes staged changes
- Follows Conventional Commits format
- Intelligent type detection (feat/fix/refactor/etc.)
- Explains what and why, not how

**Dependencies:** Gemini CLI, Git

---

## Implemented Skills (Continued)

### 🟢 code-story-teller
**Status:** Implemented
**Category:** Documentation & Understanding
**Trigger:** "tell me the story of this file", "explain code evolution", "show file history"

Analyzes git history to explain how code evolved and why design decisions were made.

**Features:**
- Analyzes git history for a file
- Explains design decisions and their context
- Identifies important milestones and refactorings
- Generates engaging narrative in Traditional Chinese
- Shows contributor impact
- Detects patterns in evolution

**Dependencies:** Gemini CLI, Git

**Complexity:** Medium

---

### 🟢 pr-review-assistant
**Status:** Implemented
**Category:** Code Review & Quality
**Trigger:** "review this PR", "help review pull request", "analyze PR changes"

AI-powered pull request reviewer that provides comprehensive, structured feedback.

**Features:**
- Analyzes PR diff comprehensively using GitHub CLI and Gemini AI
- Identifies bugs, security issues, and code quality problems
- Provides structured feedback (blocking, important, minor)
- Includes specific file names and line numbers
- Generates review summary with risk assessment
- Supports posting review directly to GitHub
- Bilingual output (Traditional Chinese with English code terms)

**Dependencies:** Gemini CLI, GitHub CLI, Git

**Complexity:** Medium-High

---

### 🟢 spec-review-assistant
**Status:** Implemented
**Category:** Documentation & Quality Assurance
**Trigger:** "review this spec", "check specification", "validate requirements doc"

Reviews specification documents before implementation to identify gaps, ambiguities, and potential issues.

**Features:**
- 5-dimensional analysis: Completeness, Feasibility, Clarity, Workload, Codebase Integration
- Checks for all 8 essential sections (Background, Requirements, Design, Error Handling, Security, Testing, Deployment, Metrics)
- Detects vague terms and suggests specific metrics
- AI-powered contradiction detection
- Supports 25+ programming languages
- Generates structured review report with prioritized issues
- Optional codebase integration (--with-codebase flag)

**Dependencies:** Gemini CLI, jq, Git (optional)

**Complexity:** Medium-High

---

### 🟢 spec-generator
**Status:** Implemented
**Category:** Documentation & Planning
**Trigger:** "generate a spec", "create specification", "I need a spec document"

Generates complete specification documents from simple ideas using Claude's AI capabilities.

**Features:**
- Transforms brief ideas into comprehensive 150+ line specifications
- Generates all 8 essential sections automatically
- Uses Claude Code directly (no external dependencies!)
- Context-aware (adapts to project tech stack)
- Produces review-ready specs that pass spec-review-assistant validation
- Automatic filename suggestion and directory detection
- Integrated validation (checks for placeholders, vague terms)
- Conversational refinement (iterate on sections as needed)

**Dependencies:** None - uses Claude Code's native capabilities

**Complexity:** Medium

**Integration:** Works seamlessly with spec-review-assistant for validation

---

### 🟢 ui-design-analyzer
**Status:** Implemented
**Category:** UI/UX & Design Quality
**Trigger:** "analyze this UI", "review this screenshot", "is this design good", "check interface quality"

Analyzes UI/UX design from screenshots using Claude's native multimodal capabilities.

**Features:**
- 6-dimensional analysis: Usability, Visual Design, Accessibility, Consistency, Responsive, Improvements
- WCAG 2.1/2.2 accessibility compliance checking (visual aspects)
- Color harmony and contrast ratio analysis
- Touch target size validation (mobile)
- Design system compliance checking
- Actionable improvement suggestions with specific values
- Before/after comparison support
- Color palette extraction and suggestions
- No external dependencies - uses Claude Code's native vision

**Dependencies:** None - uses Claude Code's native multimodal capabilities

**Complexity:** Medium

**Use Cases:**
- Pre-development design review
- Implementation validation (design vs actual)
- Accessibility audit (visual compliance)
- Color scheme improvement
- Design iteration feedback

---

## Planned Skills

### 🔵 release-notes-generator
**Priority:** High
**Category:** Release Management
**Trigger:** "generate release notes", "create changelog"

Automatically generates release notes from commits between versions.

**Planned Features:**
- Categorize changes (features, fixes, breaking changes)
- Multiple output styles (formal, casual, technical)
- Multi-language support (English, Traditional Chinese)
- Audience-specific versions (developers, PMs, end-users)
- Auto-link to issue tracker
- Generate breaking change migration guides

**Use Cases:**
- Release announcements
- CHANGELOG.md updates
- Internal release summaries

**Dependencies:** Gemini CLI, Git

**Estimated Complexity:** Medium

---

### 🔵 context-archaeologist
**Priority:** Medium
**Category:** Code Understanding
**Trigger:** "explain why this code exists", "show code context"

Traces code origins and provides historical context.

**Planned Features:**
- Find original commit and author
- Extract related issues and PR discussions
- Summarize business context and technical constraints
- Generate "Why is this here?" documentation
- Timeline of major changes

**Use Cases:**
- Understanding legacy code
- Onboarding new team members
- Refactoring decisions

**Dependencies:** Gemini CLI, Git, GitHub API (optional)

**Estimated Complexity:** Medium

---

### 🔵 technical-debt-scout
**Priority:** Medium
**Category:** Code Quality
**Trigger:** "find technical debt", "analyze code quality"

Identifies and quantifies technical debt in the codebase.

**Planned Features:**
- Detect code smells and anti-patterns
- Analyze complexity hotspots
- Calculate refactoring ROI
- Generate prioritized improvement recommendations
- Track debt trends over time

**Use Cases:**
- Sprint planning
- Technical debt reduction initiatives
- Code quality metrics

**Dependencies:** Gemini CLI, Git, static analysis tools

**Estimated Complexity:** High

---

## Pull Request Skills

This section focuses on skills that enhance the Pull Request workflow - from creation to review to merge.

### 🔵 pr-description-generator
**Priority:** High
**Category:** Documentation & Workflow
**Trigger:** "generate PR description", "create pull request", "write PR summary"

Automatically generates comprehensive PR descriptions from commit history.

**Planned Features:**
- Analyze all commits between base and current branch
- Categorize changes (features, fixes, refactors, docs)
- Generate structured PR description
- Create test plan checklist
- List affected files and components
- Calculate impact metrics (lines changed, risk level)
- Include breaking changes section
- Auto-link related issues
- Multi-language support (English & Traditional Chinese)

**Template Format:**
```markdown
## Summary
Brief overview of the PR

## Changes
### Features
- Feature 1
- Feature 2

### Bug Fixes
- Fix 1

### Refactoring
- Refactor 1

## Test Plan
- [ ] Unit tests pass
- [ ] Integration tests pass
- [ ] Manual testing completed

## Impact
- Files changed: 12
- Lines added: 342
- Lines removed: 128
- Risk level: Medium
- Affected modules: auth, database

## Breaking Changes
(if any)

## Related Issues
Closes #123
Related to #456

🤖 Generated with Gemini CLI
```

**Use Cases:**
- Every PR creation
- Standardize PR documentation
- Save time writing descriptions
- Improve PR quality

**Dependencies:** Gemini CLI, Git

**Estimated Complexity:** Medium

---

### 🔵 pr-merge-readiness-checker
**Priority:** Medium
**Category:** Quality Gate & Risk Management
**Trigger:** "check if PR is ready", "can I merge this", "PR readiness"

Validates if a PR is ready to be merged based on multiple criteria.

**Planned Features:**
- Check CI/CD pipeline status
- Verify required approvals
- Detect merge conflicts
- Check test coverage changes
- Validate branch protection rules
- Verify linked issues are resolved
- Check for unresolved review comments
- Calculate merge risk score
- Suggest optimal merge time

**Output Format:**
```
PR Readiness Report
==================
✅ CI/CD: All checks passed
✅ Approvals: 2/2 required
✅ Conflicts: None
⚠️  Test Coverage: Decreased by 1.2%
✅ Branch Protection: Compliant
❌ Unresolved Comments: 3 threads

Risk Score: Medium (65/100)
Recommendation: Request changes - resolve comments first

Blockers:
- 3 unresolved review threads
- Test coverage decreased

Suggested Actions:
1. Address review comments
2. Add tests to maintain coverage
```

**Dependencies:** GitHub CLI, Git, CI/CD integration

**Estimated Complexity:** High

---

### 🔵 pr-impact-analyzer
**Priority:** High
**Category:** Risk Analysis
**Trigger:** "analyze PR impact", "what does this PR affect", "PR blast radius"

Analyzes the downstream impact of PR changes.

**Potential Features:**
- Identify affected modules and services
- Find dependent components
- List teams that should be notified
- Suggest documentation updates
- Predict deployment risks
- Generate rollback plan
- Estimate performance impact

**Output Format:**
```
Impact Analysis
==============
Direct Impact:
- auth-service
- user-database

Indirect Impact:
- notification-service (depends on auth)
- analytics-pipeline (depends on user-database)

Teams to Notify:
- @backend-team (owners of auth-service)
- @data-team (owners of analytics-pipeline)

Documentation to Update:
- API_DOCS.md (auth endpoints changed)
- DEPLOYMENT.md (new environment variables)

Deployment Risk: Medium
- Database schema changes require migration
- API breaking changes need versioning
```

**Dependencies:** Gemini CLI, Git, dependency analysis tools

**Estimated Complexity:** High

---

## Ideas (Not Yet Prioritized)

### ⚪ performance-prophet
**Category:** Performance
**Trigger:** "predict performance impact", "analyze performance"

Predicts performance impact of code changes before deployment.

**Potential Features:**
- Identify algorithmic complexity issues (O(n²), etc.)
- Detect memory leaks
- Suggest optimization strategies
- Generate benchmark recommendations

**Estimated Complexity:** High

---

### ⚪ api-consistency-guardian
**Category:** API Design
**Trigger:** "check API consistency", "validate API design"

Ensures API design consistency across the codebase.

**Potential Features:**
- Check naming conventions
- Verify error handling patterns
- Validate request/response formats
- Suggest improvements for consistency

**Estimated Complexity:** Medium

---

### ⚪ meeting-notes-to-action-items
**Category:** Project Management
**Trigger:** "convert meeting notes to tasks", "extract action items"

Converts meeting notes into actionable tasks.

**Potential Features:**
- Extract action items from text
- Generate GitHub issues or TODO comments
- Identify owners and deadlines
- Auto-categorize (bug, feature, investigation)

**Estimated Complexity:** Low

---

### ⚪ onboarding-wizard
**Category:** Documentation
**Trigger:** "generate onboarding guide", "create getting started"

Generates onboarding documentation for new team members.

**Potential Features:**
- Analyze codebase structure
- Generate key module descriptions
- Create learning path
- List common tasks with instructions

**Estimated Complexity:** Medium

---

### ⚪ test-failure-analyzer
**Category:** Testing & Debugging
**Trigger:** "analyze test failure", "why did tests fail"

Analyzes test failures and suggests fixes.

**Potential Features:**
- Read test output
- Identify failure root cause
- Suggest fixes
- Locate relevant code

**Estimated Complexity:** Medium

---

### ⚪ dependency-update-checker
**Category:** Maintenance
**Trigger:** "check outdated dependencies", "update dependencies"

Checks for outdated dependencies and security vulnerabilities.

**Potential Features:**
- Scan package manifests
- Check for security vulnerabilities
- Suggest safe updates
- Generate update plan

**Estimated Complexity:** Low-Medium

---

## Implementation Guidelines

When implementing a new skill:

1. **Create directory structure**
   ```
   skill-name/
   ├── SKILL.md
   ├── README.md
   └── scripts/
       └── main_script.sh
   ```

2. **Use existing skills during development**
   - Use `code-review-gemini` to review changes
   - Use `commit-msg-generator` for commit messages

3. **Update this roadmap**
   - Move skill from "Planned" to "In Progress"
   - Update status when completed
   - Add any learnings or notes

4. **Update main README.md**
   - Add skill to the skills table
   - Add usage examples if needed

5. **Test thoroughly**
   - Test with various inputs
   - Document edge cases
   - Add troubleshooting section

---

## Priority Matrix

### High Priority (Implement Soon)
1. **pr-description-generator** - Saves time, improves PR quality
2. **release-notes-generator** - High value, medium complexity
3. **pr-impact-analyzer** - Prevents production issues, risk analysis

### Medium Priority (Next Quarter)
4. **pr-merge-readiness-checker** - Quality gate automation
5. **context-archaeologist** - Good for onboarding
6. **technical-debt-scout** - Long-term code quality

### Low Priority (Future)
7. Other skills as needed

---

## Contributing New Skill Ideas

To propose a new skill:

1. Add it to the "Ideas" section
2. Include:
   - Name and category
   - Trigger phrases
   - Key features
   - Use cases
   - Estimated complexity
3. Discuss in team meeting or create an issue

---

**Last Updated:** 2026-01-13
**Next Review:** End of Q1 2026
