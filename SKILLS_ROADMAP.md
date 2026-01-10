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

### 🔵 impact-blast-radius-analyzer
**Priority:** High
**Category:** Risk Management
**Trigger:** "analyze blast radius", "check impact of changes"

Analyzes the potential impact of code changes before deployment.

**Planned Features:**
- Identify affected modules and dependencies
- Detect potential breaking changes
- Suggest required test updates
- List stakeholders who should be notified
- Calculate risk score

**Use Cases:**
- Pre-deployment risk assessment
- Large refactoring planning
- API change impact analysis

**Dependencies:** Gemini CLI, Git, static analysis tools

**Estimated Complexity:** High

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
1. release-notes-generator - High value, medium complexity
2. impact-blast-radius-analyzer - Prevents production issues
3. code-story-teller - Helps understand legacy code

### Medium Priority (Next Quarter)
4. context-archaeologist - Good for onboarding
5. technical-debt-scout - Long-term code quality

### Low Priority (Future)
6. Other skills as needed

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

**Last Updated:** 2026-01-10
**Next Review:** End of Q1 2026
