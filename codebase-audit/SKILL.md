---
name: codebase-audit
description: Claims-first codebase audit that extracts documentation claims and verifies them against code. Use when asked to "audit", "verify docs match code", "check if README claims are true", or "validate documentation accuracy". Falsification-first approach.
allowed-tools: Bash, Read, Grep, Glob, Task
---

# Codebase Audit

## Overview

Documentation makes claims. Code makes behavior. This skill finds divergence.

**Core principle:** Extract every testable claim from documentation, then attempt to falsify each one against the actual codebase. Claims that survive falsification are VERIFIED. Claims that don't are exposed.

This is not a code review. Code reviews ask "is this code good?" This skill asks "is what the documentation says actually true?"

## When to Use

- Verifying that README claims match actual implementation
- Auditing CLAUDE.md, CONTRIBUTING.md, or architectural docs against code
- Checking if JSDoc/docstrings describe what functions actually do
- Validating that test descriptions match what tests actually test
- Post-migration verification: do the docs still reflect reality?
- Onboarding validation: can a new developer trust the docs?

## When NOT to Use

- General code quality review (use `code-review-gemini` or `code-review-claude`)
- Research tasks with no codebase to audit (use `critical-research`)
- Security vulnerability scanning (use dedicated security tools)
- Performance auditing (use profilers and benchmarks)

## Workflow

### Step 1: Define Audit Scope

Ask the user (or determine from context):
1. **Target documents**: Which docs to audit? (README, CLAUDE.md, JSDoc, test descriptions, API docs)
2. **Target codebase**: Which directories/files to verify against?
3. **Depth**: Full audit or focused audit on specific sections?

If not specified, default to: README.md + CLAUDE.md in the project root, verified against the full codebase.

### Step 2: Extract Claims

Read each target document and extract every **testable claim** — any statement that asserts something about the codebase that can be verified as true or false.

Categories of claims:
- **Structural**: "The project has X directory structure", "Each module contains Y"
- **Behavioral**: "Function X returns Y when given Z", "The API supports pagination"
- **Dependency**: "Requires Node.js 18+", "Uses PostgreSQL for storage"
- **Configuration**: "Set ENV_VAR to enable feature X", "Default port is 3000"
- **Process**: "Run `npm test` to execute tests", "Deploy with `make deploy`"
- **Coverage**: "All endpoints have integration tests", "100% type coverage"

Record each claim with its source location (file:line).

**Ignore non-testable statements**: opinions, aspirations, future plans ("we plan to..."), and subjective assessments ("easy to use").

### Step 3: Classify by Risk

Assign each claim a risk level based on the consequence of it being false:

| Risk | Criteria | Example |
|------|----------|---------|
| **Critical** | False claim causes data loss, security breach, or production failure | "Authentication is required for all API endpoints" |
| **High** | False claim causes broken setup, wasted developer hours, or wrong architecture decisions | "Run `npm install` to set up the project" |
| **Medium** | False claim causes confusion or minor inefficiency | "The config file supports hot-reloading" |
| **Low** | False claim is cosmetic or trivial | "The project follows Conventional Commits" |

### Step 4: Select Verification Method

Apply verification methods based on risk level:

| Method | All Claims | Critical + High | Critical Only |
|--------|-----------|-----------------|---------------|
| **A: Static Analysis** | Yes | Yes | Yes |
| **B: Test Evidence + Mirror Test** | Yes | Yes | Yes |
| **C: Runtime Probe** | — | Yes | Yes |
| **D: Dependency Trace** | — | Yes | Yes |
| **E: Mutation Test** | — | — | Yes |

#### Method A: Static Analysis
Search the codebase for evidence that supports or contradicts the claim:
- Use `Grep` to find relevant code patterns
- Use `Glob` to verify file structure claims
- Use `Read` to inspect specific implementations

#### Method B: Test Evidence + Mirror Test
Check if tests exist that verify the claim, then apply the Mirror Test:
- Does a test for this claim exist?
- Would the test **still pass** if the claimed behavior were removed? (Mirror Test)
- Does the test assert on the **specific behavior** claimed, or merely on a related side effect?

#### Method C: Runtime Probe
For Critical and High risk claims, attempt to verify through execution:
- Run commands the docs claim should work
- Check that claimed endpoints exist
- Verify that configuration options have the documented effect

#### Method D: Dependency Trace
Trace the dependency chain for claims about integrations:
- Is the claimed dependency in package.json / requirements.txt / go.mod?
- Is it actually imported and used, or just listed?
- Does the version match what's documented?

#### Method E: Mutation Test (Critical only)
For the highest-risk claims, consider what would happen if the claim were false:
- If "all inputs are sanitized" is false, where would unsanitized input enter?
- If "authentication is required" is false, which routes are unprotected?

### Step 5: Execute (Falsification-First)

For each claim, **search for counter-evidence first**:

1. Assume the claim is FALSE
2. Search for evidence that contradicts it
3. If counter-evidence found: the claim is weakened or falsified
4. If no counter-evidence found: search for supporting evidence
5. If supporting evidence found: the claim is verified
6. If neither found: the claim is unfalsifiable with available tools

This order matters. Starting with supporting evidence creates confirmation bias.

### Step 6: Assign Verdicts

Each claim receives one of these verdicts (aligned with `critical-research` verdict system):

| Verdict | Meaning | Action Required |
|---------|---------|-----------------|
| **VERIFIED** | Claim confirmed by code evidence | None |
| **PARTIALLY VERIFIED** | Claim is true in some cases but not all | Update docs to reflect scope |
| **UNVERIFIED** | Cannot confirm or deny with available tools | Flag for manual review |
| **FALSE** | Claim contradicted by code evidence | Fix code or fix docs |
| **UNFALSIFIABLE** | Claim is too vague to test | Rewrite claim to be testable |

### Step 7: Generate Remediation Prompts

For every FALSE or PARTIALLY VERIFIED claim, generate a specific remediation:

```
CLAIM: [quoted claim] (source: file:line)
VERDICT: FALSE
EVIDENCE: [what was found]
REMEDIATION: [specific action — either fix the code or fix the docs]
```

### Step 8: Synthesize Report

Compile findings into the output format below.

## Output Format

```markdown
# Codebase Audit Report

## Audit Scope
- **Documents audited**: [list with file paths]
- **Codebase scope**: [directories/files checked]
- **Date**: [audit date]

## Documentation Accuracy Score
- **Total claims extracted**: X
- **VERIFIED**: Y (Z%)
- **PARTIALLY VERIFIED**: A (B%)
- **UNVERIFIED**: C (D%)
- **FALSE**: E (F%)
- **UNFALSIFIABLE**: G (H%)
- **Overall accuracy**: Y / (X - G) = Z% (excluding unfalsifiable)

## Critical + High Risk Findings

### FALSE Claims
| # | Claim | Source | Evidence | Remediation |
|---|-------|--------|----------|-------------|
| 1 | "..." | file:line | [what was found] | [fix code / fix docs] |

### PARTIALLY VERIFIED Claims
| # | Claim | Source | Scope Limitation | Remediation |
|---|-------|--------|------------------|-------------|
| 1 | "..." | file:line | [true for X, false for Y] | [update docs] |

## Medium + Low Risk Findings

### FALSE Claims
| # | Claim | Source | Evidence | Remediation |
|---|-------|--------|----------|-------------|

### PARTIALLY VERIFIED Claims
| # | Claim | Source | Scope Limitation | Remediation |
|---|-------|--------|------------------|-------------|

## UNVERIFIED Claims (Manual Review Needed)
| # | Claim | Source | Why Unverifiable |
|---|-------|--------|-----------------|

## UNFALSIFIABLE Claims (Docs Need Rewriting)
| # | Claim | Source | Suggested Rewrite |
|---|-------|--------|-------------------|

## Verified Claims (Passing)
[List of claims that survived falsification, grouped by document]

## Methodology Notes
- [Any limitations of this audit]
- [What could not be checked and why]
- [Assumptions made during verification]
```

## Examples

### Example 1: README Audit

```
User: "Audit the README against the actual codebase"

Step 1 → Scope: README.md, verified against full repo
Step 2 → Extract 23 claims (structure, setup, API, testing)
Step 3 → Classify: 3 Critical, 7 High, 8 Medium, 5 Low
Step 4 → Apply methods A+B for all, C+D for Critical+High, E for Critical
Step 5 → Falsification-first execution
Step 6 → Verdicts: 15 VERIFIED, 3 PARTIALLY VERIFIED, 2 FALSE, 1 UNVERIFIED, 2 UNFALSIFIABLE
Step 7 → Remediation for 5 non-passing claims
Step 8 → Report with 87% accuracy score
```

### Example 2: API Documentation Audit

```
User: "Check if our API docs match the actual endpoints"

Step 1 → Scope: docs/api.md, verified against src/routes/
Step 2 → Extract 45 claims (endpoints, params, responses, auth)
Step 3 → Classify: 8 Critical (auth claims), 15 High (endpoint behavior), 22 Medium
Step 4 → Methods A+B+C+D for Critical+High, A+B for Medium
Step 5 → Find 3 endpoints documented but not implemented, 2 undocumented endpoints
Step 6 → 5 FALSE claims, rest VERIFIED
Step 7 → Remediation: add missing endpoints or remove from docs
Step 8 → Report with 89% accuracy score
```

## Error Handling

1. **No documentation found**: Inform user and suggest which files could serve as documentation. Offer to audit code comments/JSDoc instead.
2. **No testable claims extracted**: The documentation may be purely aspirational. Report this explicitly and suggest converting statements to testable claims.
3. **Codebase too large to fully verify**: Prioritize Critical and High risk claims. State what was not checked in Methodology Notes.
4. **Ambiguous claims**: Classify as UNFALSIFIABLE and suggest a rewrite that would make the claim testable.
5. **Runtime verification fails**: Note the failure, mark claim as UNVERIFIED, include the error in the report.

## Security Considerations

- **Read-only by default**: This skill reads code and docs but does not modify them. Runtime probes (Method C) execute only documented commands (e.g., `npm test`) and should be confirmed with the user before running.
- **No credential exposure**: Never include secrets, tokens, or env var values in the audit report. Report their existence/absence, not their content.
- **Source validation**: When auditing claims about external URLs or APIs, verify the domain is legitimate before fetching.
- **Scope containment**: Only audit files within the specified project directory. Do not follow symlinks outside the project root without user confirmation.

## Constraints

- Only verify claims against code that exists in the repository. Do not speculate about runtime behavior unless executing a Runtime Probe (Method C).
- Do not modify any files. This is a read-only audit.
- Do not fabricate evidence. If you cannot verify a claim, mark it UNVERIFIED — not VERIFIED.
- Falsification search must precede corroboration search for every claim. No exceptions.
- Report all findings, including verified claims. A clean bill of health is also valuable information.

## Related Skills

- **critical-research** — Uses the same falsification-first methodology for web research. Verdict system aligned.
- **code-review-gemini** — Complements audits with code quality review (includes adversarial pass).
- **code-review-claude** — Quick code quality checks (includes adversarial quick check).
- **sp-verification-before-completion** — Applies similar rigor to completion claims (includes adversarial self-verification).
