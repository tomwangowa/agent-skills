---
name: research-cross-validator
description: >-
  Cross-validate technical claims using multiple independent verification
  strategies (official docs, counter-examples, source code inspection).
  Use when a tech-feasibility report, design document, or any technical
  analysis contains claims that were verified by only one method or one
  AI session. Triggered by "cross-validate", "verify these claims",
  "double-check this", or "independent verification".
allowed-tools: Read, Glob, Grep, WebSearch, WebFetch, Task, Bash, mcp__context7__resolve-library-id, mcp__context7__query-docs
---

# Research Cross-Validator

## Overview

Independently verify technical claims using multiple orthogonal
strategies to eliminate single-source bias and AI hallucination risk.
Each claim is tested through 2-3 independent verification paths, and
results are compared for consistency.

**Core principle:** A claim verified by only one method is an opinion.
A claim verified by three independent methods is evidence.

**Announce at start:**
> "Cross-validating claims — I'll verify each one through multiple
> independent strategies and flag any inconsistencies."

## When to Use

- After `tech-feasibility` or `critical-research` produces a report —
  cross-validate key verdicts
- When an AI-generated analysis makes technical claims you want to trust
- When a vendor's documentation makes capability claims
- When two sources disagree and you need a tiebreaker
- After `assumption-extractor` flags CRITICAL assumptions as
  PARTIALLY VERIFIED

**When NOT to use:**
- The claim can be tested by running code (use `micro-poc-validator`
  instead — empirical beats theoretical)
- The claim is subjective or opinion-based (no objective verification
  possible)
- You only have one claim to check (use `critical-research` for
  single-claim falsification)

## Required Input

```
CLAIMS:    List of specific technical claims to verify
            (extract from a document, or provide directly)
SOURCE:    Where these claims came from
            (e.g., "tech-feasibility report from 2026-01-14")
PRIORITY:  Which claims matter most? (optional — will prioritize
            CRITICAL-impact claims if not specified)
```

If the user provides a file path, extract the top 5-10 verifiable
technical claims automatically.

## Verification Strategies

Each claim is tested through **at least 2** of these independent
strategies:

### Strategy A: Official Documentation

Query the authoritative source for the technology in question.

**Tools**: `mcp__context7__query-docs`, `WebFetch` on official docs site

**Evidence strength**: HIGH (if docs are current and specific)

**Process**:
1. Identify the official documentation source
2. Search for the specific capability claimed
3. Record: confirmed / denied / not mentioned
4. Note the doc version and date

### Strategy B: Counter-Evidence Search

Actively search for evidence that the claim is FALSE.

**Tools**: `WebSearch` with falsification queries

**Evidence strength**: HIGH (if counter-evidence is from credible source)

**Process**:
1. Construct falsification queries:
   - `"[tech] cannot [claimed capability]"`
   - `"[tech] limitation [relevant area]"`
   - `"[tech] [capability] not working"`
   - `"[tech] [capability] broken"` / `"[tech] [capability] issue"`
2. Search GitHub Issues for the project
3. Record: counter-evidence found / no counter-evidence / ambiguous

### Strategy C: Source Code Inspection

For open-source tools, check the actual implementation.

**Tools**: `Bash` (pip show, npm info), `Read`, `Grep`, `WebFetch`
on GitHub

**Evidence strength**: HIGHEST (code is truth)

**Process**:
1. Locate the relevant source file/function
2. Check if the claimed capability is implemented
3. Check function signatures, parameters, return types
4. Record: implemented / not implemented / partially implemented

### Strategy D: Community Corroboration

Check if real users have confirmed or denied the capability.

**Tools**: `WebSearch` on Stack Overflow, GitHub Discussions, Reddit

**Evidence strength**: MEDIUM (anecdotal but valuable in aggregate)

**Process**:
1. Search for users reporting success/failure with the claimed capability
2. Check recency (last 6 months preferred)
3. Record: corroborated / contradicted / no data

### Strategy E: Version-Specific Check

Verify the claim holds for the specific version in use.

**Tools**: `Bash` (check installed version), `WebSearch` for changelogs

**Evidence strength**: HIGH (version-specific evidence is precise)

**Process**:
1. Identify the version in use (or planned)
2. Check changelog for relevant additions/removals/breaking changes
3. Record: confirmed for version X / not available until version Y /
   removed in version Z

## Workflow

### Step 1: Extract and Prioritize Claims

From the source document, extract concrete technical claims. Prioritize:
1. Claims marked as CRITICAL or HIGH impact (from `assumption-extractor`)
2. Claims that are foundational — other claims depend on them
3. Claims that came from a single source only

**Limit**: Max 10 claims per session. If more exist, ask the user to
prioritize.

### Step 2: Select Strategies Per Claim

For each claim, select the 2-3 most appropriate strategies:

| Claim type | Primary strategy | Secondary strategy | Tertiary |
|-----------|-----------------|-------------------|----------|
| Library capability | C (source code) | A (official docs) | B (counter-evidence) |
| API availability | A (official docs) | B (counter-evidence) | D (community) |
| Performance claim | B (counter-evidence) | D (community) | E (version check) |
| Compatibility | C (source code) | D (community) | A (docs) |
| Vendor claim | B (counter-evidence) | D (community) | A (docs) |

### Step 3: Execute Verification (Per Claim)

Run each selected strategy independently. Do NOT let the result of one
strategy influence how you search in another — this is the key to
avoiding confirmation bias.

**Parallel execution**: If verifying multiple claims, use `Task` agents
to run verifications in parallel where possible.

### Step 4: Compare Results

For each claim, compare strategy results:

| Outcome | Meaning | Confidence |
|---------|---------|------------|
| **All agree: TRUE** | Strong confirmation | HIGH |
| **All agree: FALSE** | Strong refutation | HIGH |
| **Majority agree, minority disagrees** | Likely true/false with caveats | MEDIUM |
| **Evenly split** | Genuinely uncertain | LOW |
| **Only one strategy found evidence** | Weak — needs more data | LOW |

### Step 5: Generate Cross-Validation Report

```markdown
# Cross-Validation Report

**Date**: YYYY-MM-DD
**Source**: [document or origin of claims]
**Claims evaluated**: [N]

## Summary

| Claim | Strategy A | Strategy B | Strategy C | Consensus | Confidence |
|-------|-----------|-----------|-----------|-----------|------------|
| [C1]  | TRUE      | TRUE      | TRUE      | CONFIRMED | HIGH       |
| [C2]  | TRUE      | FALSE     | —         | DISPUTED  | LOW        |
| [C3]  | FALSE     | FALSE     | FALSE     | REFUTED   | HIGH       |

## Detailed Findings

### Claim 1: [statement]

**Consensus**: CONFIRMED / DISPUTED / REFUTED / UNCERTAIN
**Confidence**: HIGH / MEDIUM / LOW

| Strategy | Result | Evidence | Source |
|----------|--------|----------|--------|
| A: Official docs | TRUE | [what was found] | [URL] |
| B: Counter-evidence | TRUE (no counter-evidence found) | [search queries used] | — |
| C: Source code | TRUE | [function/file that confirms] | [path/URL] |

**Resolution**: [If disputed, explain the discrepancy and which
evidence is more authoritative]

### Claim 2: [statement]
(repeat)

## Implications

### Confirmed Claims (safe to rely on)
- [C1]: [brief restatement]

### Refuted Claims (must update plan)
- [C3]: [brief restatement] — **Impact**: [what this breaks]

### Disputed Claims (need further investigation)
- [C2]: [brief restatement] — **Recommended**: [micro-PoC / expert
  consultation / defer]

## Upstream Impact

<!-- How these findings affect the source document -->

| Source Document Section | Affected Claims | Required Update |
|------------------------|----------------|-----------------|
| [Section 2.1] | C2, C3 | Rewrite to account for refuted claims |
```

## Examples

### Example 1: Library Capability Claims

```
Claims from tech-feasibility report:

C1: "nodriver supports connecting to remote browsers via WSS"
  Strategy A (docs): FALSE — no WSS documentation found
  Strategy C (source): FALSE — start() accepts host+port only
  Strategy D (community): FALSE — GitHub issue #47 confirms not supported
  Consensus: REFUTED (HIGH confidence)

C2: "Playwright connect_over_cdp() accepts wss:// URLs"
  Strategy A (docs): TRUE — official docs show wss:// examples
  Strategy C (source): TRUE — connect_over_cdp signature accepts string URL
  Strategy E (version): TRUE — available since Playwright 1.20
  Consensus: CONFIRMED (HIGH confidence)
```

### Example 2: API Availability Claims

```
C1: "ScraperAPI provides a structured Amazon Reviews endpoint"
  Strategy A (docs): PARTIAL — endpoint listed but marked "beta"
  Strategy B (counter): FALSE — multiple reports of 404 since Nov 2024
  Strategy D (community): FALSE — users report endpoint returns empty data
  Consensus: REFUTED (HIGH confidence)
  Resolution: Docs are outdated; real-world testing confirms endpoint is
  non-functional
```

## Constraints

- **Independence of strategies** — do NOT let one strategy's result
  influence another's search. Run them as if each is the first check.
- **Minimum 2 strategies per claim** — single-strategy verification is
  not cross-validation.
- **Max 10 claims per session** — cross-validation is thorough by design;
  limit scope to maintain quality.
- **Recency matters** — prefer evidence from the last 6 months. Flag
  older evidence as potentially stale.
- **Source attribution** — every finding must link to a specific URL,
  file path, or search query.
- **No consensus forcing** — if strategies disagree, report DISPUTED
  with LOW confidence. Do not pick a winner without justification.

## Error Handling

| Scenario | Action |
|----------|--------|
| Official docs don't mention the capability at all | Record as "NOT DOCUMENTED" — distinct from FALSE. Absence of evidence ≠ evidence of absence. Recommend micro-PoC. |
| Source code is unavailable (closed-source tool) | Skip Strategy C, increase weight on A + B + D |
| All search queries return no results | Broaden terms; if still nothing, record as "NO DATA" and flag as high uncertainty |
| Conflicting versions of the same doc exist | Use the version matching the user's installed/planned version |
| Strategy execution reveals the claim is poorly defined | Ask the user to clarify before continuing verification |

## Security Considerations

- **Read-only by default** — this skill primarily reads docs and searches.
  The only Bash usage is for checking installed package versions (`pip
  show`, `npm list`), not for executing arbitrary code.
- **No credential exposure** — never include API keys in search queries.
- **Source validation** — verify URLs point to legitimate domains before
  citing. Flag suspicious sources.
- **Search query sanitization** — sanitize user-provided claim text
  before constructing search queries.

## Related Skills

- **tech-feasibility** — upstream: produces reports containing claims to
  cross-validate
- **critical-research** — complementary: focused falsification of a
  single hypothesis; cross-validator handles multiple claims in parallel
- **assumption-extractor** — upstream: extracts assumptions that become
  claims for cross-validation
- **micro-poc-validator** — complementary: cross-validator uses desk
  research; micro-poc uses empirical testing. Use micro-poc for claims
  that can be tested with code.
- **research-synthesis** — downstream: combines cross-validation results
  with other research into decisions
- **tech-research-pipeline** — orchestrator: invokes this skill after
  critical-research and before research-synthesis
