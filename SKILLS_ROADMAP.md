# Skills Roadmap

This document tracks all skill ideas, their current status, and implementation priority.

## Status Legend

- 🟢 **Implemented** - Completed and available
- 🟡 **In Progress** - Currently being developed
- 🔵 **Planned** - Approved for implementation
- ⚪ **Idea** - Proposed but not yet prioritized
- 🔴 **Blocked** - Waiting for dependencies or decisions

---

## Overview

**Total Implemented:** 17 skills across 6 categories

### By Category

| Category | Count | Skills |
|----------|-------|--------|
| 🔍 Code Quality & Review | 4 | code-review-gemini, code-review-claude, pr-review-assistant, skill-auditor |
| 🔀 Git & Version Control | 1 | code-story-teller |
| 🎨 Design & UI/UX | 1 | ui-design-analyzer |
| 🤝 Multi-Agent Roles | 3 | role-orchestrator, role-pm, role-rd |
| 🚀 Productivity & Content Creation | 3 | interactive-presentation-generator, work-log-analyzer, activity-logger |
| 🔬 Research & Analysis | 5 | critical-research, assumption-extractor, micro-poc-validator, research-cross-validator, tech-research-pipeline |

### Quality Scores (by skill-auditor)

- **103/100** - skill-auditor (meta-validated ✅)
- **88/100** - code-review-gemini (production-ready ✅)
- **85/100** - assumption-extractor (production-ready ✅)
- **78/100** - micro-poc-validator (production-ready ✅)
- **78/100** - research-cross-validator (production-ready ✅)
- **76/100** - tech-research-pipeline (production-ready ✅)
- **75/100** - interactive-presentation-generator (production-ready ✅)

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

### 🟢 work-log-analyzer
**Status:** Implemented (Enhanced with Activity Aggregation)
**Category:** Documentation & Productivity
**Trigger:** "analyze my work log", "check TODOs in journal", "track project evolution", "aggregate my activities", "show me this week's work"

Analyzes work logs, journals, and development notes to track project evolution, manage TODOs, extract insights, and aggregate structured activity records from activity-logger.

**Features:**
- **6 query types:**
  - **Action Items Extraction** (NEW): AI-powered extraction from discussions, decisions, and TODOs with status tracking
  - **Activity Aggregation**: Aggregate and filter structured activity records from activity-logger
  - Timeline: Evolution tracking across log entries
  - TODO: Task management with overdue detection
  - Decision: Rationale and context tracking
  - Search: Keyword-based finding
- **Activity Aggregation capabilities:**
  - Date range filtering (today, yesterday, this-week, last-week, this-month, all)
  - Project, type, and tag filtering
  - Multiple output formats (by-date, by-project, by-type, json)
  - Cross-platform date handling (macOS/Linux)
  - Efficient batch processing with jq
- Intelligent date parsing and overdue task detection
- Supports multiple log formats (Markdown, plain text, structured, unstructured, JSON)
- TODO format tolerance (various checkbox styles, completion markers)
- Chronological timeline generation for project evolution
- Decision history extraction with context and rationale
- Bilingual output (Traditional Chinese with English technical terms)
- Includes example work log for immediate testing
- Shell script for activity aggregation (`aggregate_activities.sh`)

**Dependencies:**
- Core features: None - uses Claude Code's native capabilities
- Activity Aggregation: `jq` (JSON processor), `date` (standard on most systems)

**Complexity:** Medium

**Use Cases:**
- **Activity reporting** (NEW): Daily/weekly/monthly work reports from activity logs
- **Cross-session tracking** (NEW): Aggregate work across multiple Claude Code sessions
- **Project activity analysis** (NEW): Filter and analyze activities by project, type, or tag
- Daily standup preparation (yesterday's work, today's plan)
- Sprint retrospective (decisions and progress review)
- Technical debt tracking (HACK, FIXME, TODO items)
- Decision documentation (ADR generation from logs)
- Personal productivity tracking
- Project continuity and knowledge preservation

**Integration Points:**
- Seamlessly integrates with activity-logger for structured activity records
- Can process both traditional work logs and JSON activity records
- Unified query interface for mixed log sources

---

### 🟢 activity-logger
**Status:** Implemented
**Category:** Productivity & Session Management
**Trigger:** "log this activity", "record what I just did", "save session activity"

Records work activities from the current Claude Code session to enable cross-session activity aggregation and work log generation.

**Features:**
- Session-based activity tracking across multiple concurrent Claude Code instances
- Automatic project context capture (git branch, remote, changed files, recent commits)
- Activity type classification (task_completed, bug_fixed, refactoring, research, documentation, review)
- Tag-based organization for easy categorization
- JSON-based storage for structured querying
- Session management (info, list, stats, archive)
- Git integration for automatic file change detection
- Credential sanitization in git URLs
- Efficient batch processing with jq for scalability
- Works in all git states (including fresh repos without HEAD)
- Cross-platform compatibility (macOS/Linux)

**Dependencies:**
- `jq` - JSON processor (required)
- `git` - Version control (required)
- `openssl` - Secure random generation (optional, falls back to /dev/urandom or $RANDOM)

**Complexity:** Medium

**Use Cases:**
- Cross-session activity aggregation across multiple projects
- Automatic work log generation from session activities
- Project time tracking and productivity analysis
- Context preservation for interrupted work sessions
- Team activity reporting and standup preparation
- Integration with work-log-analyzer for comprehensive logging

**Integration Points:**
- Designed to work with work-log-analyzer skill for activity aggregation
- Activity records stored in `~/.claude/activities/` as JSON
- Processed activities archived to `~/.claude/activities/processed/`

---

### 🟢 interactive-presentation-generator
**Status:** Implemented
**Category:** Productivity & Content Creation
**Trigger:** "create a presentation", "generate slides", "make a deck from outline"

Generate professional interactive presentations from outlines or briefs with customizable styles and assets.

**Features:**
- **3 output formats:** reveal.js HTML (primary), Marp markdown, Slidev
- **20 professional styles:** Editorial, Minimalist, Technical, Traditional, Creative, and more
- **Style categories:** Technical (blueprint, cyber-neon), Minimalist (swiss-clean, blue-mono, japanese-minimal), Traditional (ukiyo-e, kabuki-gold, byobu), Editorial (fashion-layout, kinfolk, red-editorial), and 8 more
- **Customizable assets:** Cover images, ending images, logos
- **Dynamic footers:** Template variables (PAGE_NUMBER, COMPANY_NAME, AUTHOR, DATE)
- **Security hardened:** XSS prevention, input validation, CSP support
- **Complete documentation:** SKILL.md, README, QUICKSTART, 3 example presentations
- **Self-contained:** All 20 styles bundled (no external style dependencies)

**Dependencies:** None - fully self-contained with bundled styles

**Complexity:** Medium-High

**Use Cases:**
- Technical conference talks (use blueprint or cyber-neon style)
- Business presentations (use swiss-clean or premium-mockup)
- Educational lectures (use japanese-minimal or kinfolk-editorial)
- Product launches (use fashion-layout or digital-pop)
- Team training sessions
- Quick status updates (5-minute lightning talks)

**Quality Score:** 75/100 (audited by skill-auditor, production-ready ✅)

**Integration Points:**
- Standalone skill, no dependencies on other skills
- Can use custom style YAML via $STYLE_YAML_DIR environment variable
- Generated HTML works offline (CDN-based, but all assets downloadable)

---

### 🟢 skill-auditor
**Status:** Implemented
**Category:** Code Quality & Meta-Tools
**Trigger:** "audit this skill", "check skill quality", "is this skill production-ready", "validate skill standards"

Meta-skill that audits other skills for quality, security, and production readiness.

**Features:**
- **100-point scoring system** with weighted categories
- **7 audit categories:** Structure (15%), Security (30%), Error Handling (20%), Portability (15%), Quality (10%), Documentation (10%), Scripts
- **50+ automated checks:** YAML validation, hardcoded paths, security keywords, ambiguous terms, examples, documentation
- **Line-number precision:** Shows exact locations of issues
- **Actionable recommendations:** Specific fixes, not just problem identification
- **Report generation:** Structured markdown with severity levels (Critical/Important/Suggestion)
- **Templates included:** Security section, Error handling section for quick fixes
- **Production-ready gate:** Clear pass/fail criteria (Critical = 0)
- **Meta-validated:** Passes its own audit (103/100 score)

**Dependencies:**
- bash 4.0+, grep, sed, find, mktemp (standard Unix tools)
- Optional: Gemini CLI for AI-powered semantic analysis

**Complexity:** Medium

**Use Cases:**
- Pre-commit quality gate for skill changes
- Team skill sharing validation (ensure portability)
- Continuous quality improvement tracking
- Batch audit of skill libraries
- CI/CD integration for automated quality checks
- Before/after comparison for skill improvements

**Quality Score:** 103/100 (self-audit passed ✅, meta-validation success)

**Integration Points:**
- Can trigger code-review-gemini for script quality checks
- Git hook ready for pre-commit validation

**Three-Round Review:**
- Spec Review: Fixed 7 critical, 21 important issues
- Code Review (Gemini): Fixed critical report generation flaw (sed portability)
- Self-Audit: Achieved 103/100 (meta-validation proves correctness)

---

### 🟢 assumption-extractor
**Status:** Implemented
**Category:** Research & Analysis
**Trigger:** "extract assumptions", "what assumptions does this plan make", "audit assumptions"

Systematically extracts explicit and implicit assumptions from technical documents, design plans, or feasibility assessments.

**Features:**
- 10-category assumption taxonomy (technical capability, compatibility, performance, availability, cost, security, behavioral, environmental, temporal, dependency)
- Visibility classification (explicit vs implicit)
- Verification status tracking (verified, unverified, contradicted, partially verified)
- Risk impact scoring (CRITICAL, HIGH, MEDIUM, LOW)
- Dependency graph between assumptions
- Cascading failure analysis
- Recommended verification order with time estimates

**Dependencies:** None - uses Claude Code's native capabilities

**Complexity:** Medium

**Quality Score:** 85/100 (audited by skill-auditor, production-ready ✅)

---

### 🟢 micro-poc-validator
**Status:** Implemented
**Category:** Research & Analysis
**Trigger:** "validate this assumption", "can X actually do Y?", "prove it with code", "micro-poc"

Empirically validates technical assumptions through minimal code experiments (5-30 min spikes).

**Features:**
- Time-boxed experiments (default 15 min, max 30 min)
- Structured experiment template (setup, test, assert)
- Pre-flight safety check (cost, isolation, dependencies, credentials)
- Binary outcome classification (PASS, FAIL, PARTIAL, TIMEOUT, BLOCKED)
- Batch mode for multiple assumptions (sorted by kill impact, stops on BLOCKING FAIL)
- Raw output preservation for traceability
- Upstream document update suggestions

**Dependencies:** Language-specific runtimes for the technology being tested

**Complexity:** Medium

**Quality Score:** 78/100 (audited by skill-auditor, production-ready ✅)

---

### 🟢 research-cross-validator
**Status:** Implemented
**Category:** Research & Analysis
**Trigger:** "cross-validate", "verify these claims", "double-check this", "independent verification"

Cross-validates technical claims using multiple independent verification strategies.

**Features:**
- 5 verification strategies: Official docs, Counter-evidence search, Source code inspection, Community corroboration, Version-specific check
- Minimum 2 strategies per claim (independence enforced)
- Per-claim consensus rating (CONFIRMED, DISPUTED, REFUTED, UNCERTAIN)
- Confidence scoring (HIGH, MEDIUM, LOW)
- Conflict resolution with evidence hierarchy
- Max 10 claims per session for quality
- Parallel execution support via Task agents

**Dependencies:** None - uses Claude Code's native capabilities

**Complexity:** Medium

**Quality Score:** 78/100 (audited by skill-auditor, production-ready ✅)

---

### 🟢 tech-research-pipeline
**Status:** Implemented
**Category:** Research & Analysis
**Trigger:** "full research pipeline", "rigorous tech evaluation", "research pipeline", "evaluate [tech] thoroughly"

Orchestrates full 8-phase technical research workflow with gate checks.

**Features:**
- 8-phase pipeline: brainstorming → tech-feasibility → assumption-extractor → micro-poc-validator → critical-research → narrative-auditor → research-cross-validator → research-synthesis
- Gate A (empirical validity): stops on BLOCKING assumption failure
- Gate B (convergence): flags conflicts between research phases
- Pipeline state management with progress tracking
- Abbreviated mode (skip phases 5-6 for medium-stakes decisions)
- Early termination at any gate
- User approval required at each gate

**Dependencies:** All 7 upstream research skills

**Complexity:** High (orchestrator)

**Quality Score:** 76/100 (audited by skill-auditor, production-ready ✅)

---

### 🟢 role-orchestrator
**Status:** Implemented
**Category:** Multi-Agent Roles
**Trigger:** "role orchestrator", "multi-role pipeline", "PM then RD", "start role pipeline"

Orchestrates a multi-role development pipeline (PM → RD) using subagent dispatch with user-approval gates.

**Features:**
- Sequential PM → RD pipeline with Gate A (requirements) and Gate B (design)
- Project profile loading from `.claude/project-profile.yaml`
- Interactive profile creation when no profile exists
- Size-calibrated output depth (small/medium/large)
- Convergence check between PM and RD artifacts
- Prompt injection mitigation for subagent dispatch
- Pipeline state management with progress tracking

**Dependencies:** role-pm, role-rd (dispatched as subagents)

**Quality Score:** 85/100 (AI-adjusted, production-ready ✅)

---

### 🟢 role-pm
**Status:** Implemented
**Category:** Multi-Agent Roles
**Trigger:** "PM analysis", "requirements gathering", "role-pm"

PM role that produces size-calibrated requirements artifacts.

**Features:**
- Size-calibrated output: bullets + AC (small), user stories + MoSCoW (medium), full PRD + RACI (large)
- Structured artifact format with metadata and handoff protocol
- Product risk identification (not technical risks)
- Acceptance criteria required for every requirement

**Dependencies:** None

**Quality Score:** 85/100 (AI-adjusted, production-ready ✅)

---

### 🟢 role-rd
**Status:** Implemented
**Category:** Multi-Agent Roles
**Trigger:** "RD analysis", "technical design", "role-rd"

RD role that produces size-calibrated design artifacts from PM requirements.

**Features:**
- Size-calibrated output: code plan (small), design doc (medium), architecture doc (large)
- Feasibility checks: intuition (small), tech-feasibility (medium), tech-research-pipeline (large)
- Implementation roadmap with independently testable tasks
- T-shirt / story point / hour-based estimation by size

**Dependencies:** tech-feasibility (medium), tech-research-pipeline (large)

**Quality Score:** 85/100 (AI-adjusted, production-ready ✅)

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

## Document Template Extensions

### ⚪ Document Template Generator: Multi-Template Support
**Category:** Documentation & Planning
**Priority:** Medium
**Trigger:** "generate ADR", "create post-mortem", "write API docs"

Claude-native template generation supporting multiple document templates for technical documentation.

**Proposed Templates** (in priority order):

#### 1. ADR (Architecture Decision Record) - High Priority
**Use Cases:**
- Document technical decisions (database choice, framework selection, API design)
- Capture context, rationale, and trade-offs
- Link with work-log-analyzer for decision tracking

**Template Sections:**
- Title and Status (Proposed/Accepted/Deprecated/Superseded)
- Context (what situation led to this decision)
- Decision (what was decided)
- Rationale (why this decision)
- Alternatives Considered (what else was evaluated)
- Consequences (pros and cons)
- Related Decisions

**Example Usage:**
```
Generate an ADR for choosing PostgreSQL over MongoDB
```

**ROI**: Very High - Prevents future confusion, speeds up onboarding

---

#### 2. Post-mortem / Incident Report - High Priority
**Use Cases:**
- Document production incidents
- Root cause analysis
- Action items for prevention
- Team learning

**Template Sections:**
- Summary (duration, impact, severity)
- Timeline (detailed event sequence)
- Root Cause Analysis
- Contributing Factors
- Resolution Steps
- Action Items (preventive measures)
- Lessons Learned

**Example Usage:**
```
Generate a post-mortem for the API outage on 2026-01-13
```

**ROI**: High - Critical for reliability improvement, required by many orgs

---

#### 3. API Documentation - High Priority
**Use Cases:**
- Document REST/GraphQL APIs
- OpenAPI/Swagger compatible
- Keep docs in sync with code

**Template Sections:**
- Endpoint overview
- Request/Response schemas
- Authentication requirements
- Error codes and handling
- Rate limiting
- Examples (curl, JavaScript, Python)

**Example Usage:**
```
Generate API docs for my auth endpoints based on the code
```

**ROI**: High - Daily use, improves team efficiency

---

#### 4. Troubleshooting Guide / Runbook - Medium Priority
**Use Cases:**
- On-call engineer reference
- Common issues and solutions
- Step-by-step recovery procedures

**Template Sections:**
- Problem description
- Symptoms and detection
- Root cause
- Solution steps
- Prevention measures
- Related incidents

**Example Usage:**
```
Generate a troubleshooting guide for database connection timeouts
```

**ROI**: Medium - Reduces MTTR, helps on-call engineers

---

#### 5. Migration Plan - Medium Priority
**Use Cases:**
- Database schema changes
- Version upgrades
- Data format migrations

**Template Sections:**
- Migration overview and goals
- Pre-migration checklist
- Step-by-step migration procedure
- Rollback plan
- Testing strategy
- Risk assessment and mitigation

**Example Usage:**
```
Generate a migration plan for upgrading from PostgreSQL 12 to 15
```

**ROI**: Medium - Critical when needed, but less frequent

---

#### 6. Demo Script / Presentation Guide - Low Priority
**Use Cases:**
- Technical presentations
- Feature demos
- Training materials

**Template Sections:**
- Objective and audience
- Story flow and scenarios
- Code examples
- Timing and pacing
- Q&A preparation
- Visual aids suggestions

**Example Usage:**
```
Generate a demo script for presenting [feature/tool]
```

**ROI**: Low-Medium - Useful but less frequent than others

---

#### 7. Performance Analysis Report - Low Priority
**Use Cases:**
- Performance optimization projects
- Benchmark comparisons
- Bottleneck identification

**Example Usage:**
```
Generate a performance report based on my load test results
```

**ROI**: Low-Medium - Specialized use case

---

### Implementation Approach

**Option A: Claude-native template generation (Recommended)**
- Use Claude Code's native capabilities for template generation
- Automatically select template based on user's request
- Use Claude's understanding to choose the right format

**Option B: Separate Skills**
- Create dedicated skills (adr-generator, post-mortem-generator, etc.)
- More focused but higher maintenance cost

**Recommendation**: Start with Option A, add 3 most valuable templates:
1. ADR
2. Post-mortem
3. API Documentation

**Estimated Effort**:
- Infrastructure: 4-6 hours (template system)
- Per template: 1-2 hours (define structure and examples)
- Total for 3 templates: 10-12 hours

**Dependencies**: None - uses Claude Code's native capabilities

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
   - Follow Conventional Commits format for commit messages

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

**Last Updated:** 2026-03-04
**Next Review:** End of Q1 2026
