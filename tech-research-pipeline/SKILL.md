---
name: tech-research-pipeline
description: >-
  Orchestrates a full technical research workflow by chaining specialized
  skills in sequence: brainstorming → tech-feasibility → assumption-extractor
  → micro-poc-validator → critical-research → narrative-auditor →
  research-cross-validator → research-synthesis. Use when evaluating a
  technology choice, planning a migration, or making any significant
  technical decision that warrants rigorous multi-angle analysis.
  Triggered by "full research pipeline", "rigorous tech evaluation",
  "research pipeline", or "evaluate [tech] thoroughly".
---

# Tech Research Pipeline

## Overview

A workflow orchestrator that chains 8 specialized research skills into a
rigorous evaluation pipeline. Each phase builds on the previous one's
output, with explicit gate checks between phases to allow early
termination when evidence is conclusive.

**Core principle:** No single research method is sufficient. Correctness
comes from layering independent verification strategies — desk research,
empirical testing, falsification, self-audit, and cross-validation —
each compensating for the others' blind spots.

**Announce at start:**
> "Starting tech research pipeline — this is a multi-phase evaluation
> that chains 8 specialized skills. I'll check in with you at each gate."

## When to Use

- Evaluating a technology for a critical production system
- Planning a migration that affects core architecture
- Making a build-vs-buy decision with significant cost implications
- Any technical decision where being wrong is expensive (> 1 week of
  rework)
- When previous ad-hoc research produced plans with hidden errors
  (like the ScraperAPI migration experience)

**When NOT to use:**
- Single-question technology lookup (use `tech-feasibility` alone)
- Single claim verification (use `critical-research` alone)
- The decision is low-stakes or easily reversible
- You already have empirical evidence from a working prototype

**Estimated time:** 30-90 minutes for a complete pipeline run, depending
on the number of assumptions and claims to verify.

## Required Input

```
QUESTION:    The technical decision to evaluate
              (e.g., "Should we migrate from nodriver to Playwright for
              remote browser automation?")
STAKES:      Why does this decision matter?
              (e.g., "Wrong choice = 2 months wasted on unviable architecture")
CONSTRAINTS: Budget, timeline, team size, existing infrastructure
DEPTH:       full / abbreviated
              - full: all 8 phases (recommended for critical decisions)
              - abbreviated: skip phases 5-7, go directly from micro-PoC
                to synthesis (for medium-stakes decisions)
```

## Pipeline Architecture

```
Phase 0 ─── brainstorming ──────────────── Scope & Intent
   │                                         │
   ▼                                         ▼
Phase 1 ─── tech-feasibility ────────────── Feasibility Report
   │                                         │
   ▼                                         ▼
Phase 2 ─── assumption-extractor ────────── Assumption Registry
   │                                         │
   ▼                                         ▼
Phase 3 ─── micro-poc-validator ─────────── Empirical Evidence
   │                                         │
  GATE A ── Are BLOCKING assumptions valid? ─┤
   │         NO → STOP or PIVOT              │
   ▼         YES → continue                  ▼
Phase 4 ─── critical-research ───────────── Counter-Evidence
   │                                         │
   ▼                                         ▼
Phase 5 ─── narrative-auditor ───────────── Self-Audit
   │                                         │
   ▼                                         ▼
Phase 6 ─── research-cross-validator ────── Cross-Validation
   │                                         │
  GATE B ── Do findings converge? ───────── │
   │         NO → flag conflicts             │
   ▼         YES → proceed                   ▼
Phase 7 ─── research-synthesis ──────────── Decision Document
```

## Workflow

### Phase 0: Scope Definition (brainstorming)

**Invoke:** `brainstorming`

**Purpose:** Clarify what we're actually deciding, what's in/out of
scope, and what success looks like.

**Input to brainstorming:**
- The user's QUESTION and CONSTRAINTS
- Instruct brainstorming to focus on scope definition only — defer
  technical evaluation to later phases

**Output captured:**
- Approved scope statement
- Success criteria
- 2-3 candidate approaches to evaluate

**Gate check:** User approves scope before proceeding.

---

### Phase 1: Feasibility Assessment (tech-feasibility)

**Invoke:** `tech-feasibility`

**Purpose:** Structured evaluation of whether the candidate approaches
are technically viable.

**Input:**
- GOAL: from Phase 0 scope statement
- TECH: candidate approach(es) from Phase 0
- CONSTRAINTS: from user input

**Output captured:**
- Feasibility report with sub-hypotheses (H1, H2, ...)
- Fit analysis with Y/N/? ratings
- Kill criteria
- Initial verdict (Go / Conditional-Go / Pivot / No-Go)

**Early exit:** If verdict is **No-Go** with HIGH confidence, present
to user. Pipeline can stop here if the evidence is clear.

---

### Phase 2: Assumption Extraction (assumption-extractor)

**Invoke:** `assumption-extractor`

**Purpose:** Surface all hidden assumptions in the Phase 1 report.

**Input:**
- The feasibility report from Phase 1
- CONTEXT: the decision from Phase 0

**Output captured:**
- Assumption Registry with all assumptions classified
- CRITICAL + UNVERIFIED assumptions identified
- Recommended verification order

**Handoff to Phase 3:** The CRITICAL + UNVERIFIED assumptions (with
recommended method = "Micro-PoC") become the input for Phase 3.

---

### Phase 3: Empirical Validation (micro-poc-validator)

**Invoke:** `micro-poc-validator` (batch mode)

**Purpose:** Test CRITICAL assumptions with actual code before investing
more research time.

**Input:**
- CRITICAL + UNVERIFIED assumptions from Phase 2
- Sorted by KILL_IMPACT (BLOCKING first)

**Output captured:**
- Micro-PoC batch report
- Per-assumption: PASS / FAIL / PARTIAL / BLOCKED

**Execution rules:**
- Run in KILL_IMPACT order (BLOCKING first)
- Stop on first BLOCKING FAIL
- Present results to user before continuing

---

### GATE A: Empirical Validity Check

**Decision point:** Are the BLOCKING assumptions valid?

| Outcome | Action |
|---------|--------|
| All BLOCKING assumptions PASS | Continue to Phase 4 |
| Any BLOCKING assumption FAILS | **STOP** — present failure to user, discuss pivot options |
| BLOCKING assumption is PARTIAL | User decides: continue with caveats, or pivot |
| BLOCKING assumption is BLOCKED (can't test) | Flag risk, continue with explicit uncertainty |

**User approval required to proceed past Gate A.**

---

### Phase 4: Falsification Search (critical-research)

**Invoke:** `critical-research`

**Purpose:** Actively search for evidence that the approach will FAIL,
even after empirical validation passes.

**Input:**
- Hypothesis: "[Approach from Phase 0] is viable for [Goal]"
- Focus falsification on:
  - Risks identified in Phase 1 but not tested in Phase 3
  - Temporal risks (will this still work in 6 months?)
  - Scale risks (works in micro-PoC but will it work in production?)
  - Cost risks (hidden costs not apparent in small tests)

**Output captured:**
- Counter-evidence table
- Supporting evidence table
- Verdict with confidence

---

### Phase 5: Self-Audit (narrative-auditor)

**Invoke:** `narrative-auditor`

**Purpose:** Treat the Phase 1 feasibility report as an "external
narrative" and audit it for accuracy, omissions, and bias.

**Input:**
- The feasibility report from Phase 1
- Instruct narrative-auditor to check:
  - Are the cited sources accurate?
  - Are there significant omissions?
  - Does the report's conclusion follow from its evidence?
  - Are there signs of confirmation bias?

**Output captured:**
- Per-claim verdicts (ACCURATE / DECONTEXTUALIZED / MISLEADING / etc.)
- Omission analysis
- Overall assessment score

**Value:** This is the "auditor checking the auditor" step — the
feasibility report was AI-generated, so having a separate skill audit
it catches self-reinforcing errors.

---

### Phase 6: Cross-Validation (research-cross-validator)

**Invoke:** `research-cross-validator`

**Purpose:** Verify remaining key claims through multiple independent
strategies.

**Input:**
- Claims from Phase 1 that were NOT tested empirically in Phase 3
- Claims that Phase 4 (critical-research) or Phase 5 (narrative-auditor)
  flagged as uncertain or disputed

**Output captured:**
- Cross-validation report with per-claim consensus
- Confirmed / Disputed / Refuted classifications

---

### GATE B: Convergence Check

**Decision point:** Do all phases' findings tell a consistent story?

| Outcome | Action |
|---------|--------|
| Findings converge (same direction) | Proceed to synthesis with high confidence |
| Minor conflicts (1-2 disputed claims, non-critical) | Proceed to synthesis, flag disputes |
| Major conflicts (critical claims disputed) | Present to user — may need additional micro-PoC or expert input |

---

### Phase 7: Decision Synthesis (research-synthesis)

**Invoke:** `research-synthesis`

**Purpose:** Combine all findings into a single decision document.

**Input:**
- All outputs from Phases 1-6
- Gate A and Gate B results

**Output captured:**
- ADR-style decision document with:
  - Evidence traced to specific phases/skills
  - Conflicts explicitly resolved
  - Clear Go / No-Go / Conditional-Go recommendation
  - Risk register
  - PoC scope (if Conditional-Go)

**Final step:** Present decision document to user for approval.

---

## Abbreviated Mode

When DEPTH = `abbreviated`, skip Phases 5-6:

```
Phase 0 → Phase 1 → Phase 2 → Phase 3 → GATE A → Phase 4 → Phase 7
```

This is suitable for medium-stakes decisions where:
- The feasibility report has fewer than 5 claims and does not need self-auditing
- Claims are few enough to not need cross-validation
- Time is limited but you still want empirical validation

---

## Pipeline State Management

The pipeline maintains state across phases. After each phase, record:

```markdown
## Pipeline State: [Topic]

### Completed Phases
- [x] Phase 0: Scope approved — [1-line summary]
- [x] Phase 1: Feasibility — Conditional-Go (Medium confidence)
- [x] Phase 2: Assumptions — 12 found (3 CRITICAL, 4 HIGH)
- [x] Phase 3: Micro-PoC — 3/3 BLOCKING passed
- [ ] Phase 4: Critical research — in progress
- [ ] Phase 5: Self-audit — pending
- [ ] Phase 6: Cross-validation — pending
- [ ] Phase 7: Synthesis — pending

### Gates
- Gate A: PASSED (all BLOCKING assumptions verified)
- Gate B: pending

### Key Findings So Far
- [Most important finding from each completed phase]

### Open Questions
- [Questions that later phases should address]
```

Present this state summary to the user between phases so they can
track progress and make informed decisions about continuing.

## Examples

### Example: ScraperAPI Migration (Retrospective)

If the ScraperAPI migration had used this pipeline:

```
Phase 0 (brainstorming):
  Scope: Migrate review extraction from local Chrome to managed APIs
  Approaches: A) ScraperAPI structured, B) Raw HTML + parser, C) Remote browser

Phase 1 (tech-feasibility):
  H1: nodriver ↔ remote browser WSS → ? (uncertain)
  H2: ScraperAPI Reviews API available → ? (uncertain)
  Verdict: Conditional-Go

Phase 2 (assumption-extractor):
  A-1: nodriver supports WSS → CRITICAL, UNVERIFIED → Micro-PoC
  A-2: ScraperAPI Reviews API works → CRITICAL, UNVERIFIED → API probe
  A-3: CDP cookie injection viable → CRITICAL, UNVERIFIED → Micro-PoC
  (Total: 15 assumptions, 6 CRITICAL)

Phase 3 (micro-poc-validator):
  A-1: FAIL — nodriver has no WSS support (5 min test)
  ⚠️ BLOCKING FAIL — pipeline would stop here on Day 1

GATE A: FAIL
  → Pivot discussion: Replace nodriver with Playwright
  → Re-run Phase 1-3 with Playwright
  → A-1 (revised): PASS — Playwright connect_over_cdp() works
  → Continue pipeline

Phase 4 (critical-research):
  Counter-evidence: Amazon login wall breaks review endpoints
  → A-2 now has counter-evidence

Phase 5 (narrative-auditor):
  Audit of Phase 1 report: "ScraperAPI Reviews API available" rated
  MISLEADING — endpoint listed in docs but non-functional since Nov 2024

Phase 6 (research-cross-validator):
  A-2 cross-validated: REFUTED by 3/3 strategies
  A-3 cross-validated: UNCERTAIN — needs full PoC

GATE B: Minor conflict (A-3 uncertain)

Phase 7 (research-synthesis):
  Decision: Conditional-Go with Playwright (not nodriver)
  Tier 1: ScraperAPI Product API (confirmed working)
  Tier 2: Raw HTML + BeautifulSoup (needs Gate 1 PoC)
  Tier 3: Playwright + Remote Browser (needs Gate 2 PoC)

RESULT: Would have caught the nodriver error on DAY 1 instead of
        discovering it weeks later in the feasibility assessment.
```

## Constraints

- **Sequential phases** — do not skip phases (except in abbreviated
  mode). Each phase's input depends on the previous phase's output.
- **User approval at gates** — never proceed past Gate A or Gate B
  without user confirmation.
- **State visibility** — always show pipeline state between phases so
  the user knows where they are.
- **Time awareness** — if the pipeline is taking too long, suggest
  switching to abbreviated mode. The user's time is more valuable than
  methodological completeness.
- **No sunk-cost continuation** — if Gate A fails, STOP. Don't
  rationalize continuing because "we've already done Phases 0-2".
- **Skill invocation** — use the Skill tool to invoke each skill.
  Do not inline the skill's logic — let each skill run its own workflow.

## Error Handling

| Scenario | Action |
|----------|--------|
| A skill is unavailable or fails | Record the gap, continue with remaining skills, note reduced confidence in synthesis |
| User wants to skip a phase | Allow it but record: "Phase N skipped by user decision — findings may be incomplete" |
| Pipeline interrupted mid-session | Save pipeline state; can resume in a new session by providing the state summary |
| Phase produces no actionable output | Record "no findings" and continue — absence of evidence is itself a data point |
| Phases 4-6 discover a NEW critical assumption not caught in Phase 2 | Add it to the assumption registry, run micro-PoC if it's BLOCKING, then continue |
| Gate A fails but user wants to continue anyway | Allow it but add explicit risk: "Proceeding past failed Gate A — BLOCKING assumption A-N is falsified. Plan viability is questionable." |

## Security Considerations

- **Orchestrator only** — this skill does not execute code or make
  external calls directly. All execution happens through the invoked
  skills, which have their own security constraints.
- **State file safety** — pipeline state summaries may contain
  proprietary technical details. Save to `docs/research/` within the
  project, not to public locations.
- **Credential awareness** — when passing context between phases,
  never forward API keys or credentials. Each skill handles its own
  credential access.

## Related Skills (Invoked in Order)

1. **brainstorming** — Phase 0: scope and intent
2. **tech-feasibility** — Phase 1: structured feasibility assessment
3. **assumption-extractor** — Phase 2: assumption inventory
4. **micro-poc-validator** — Phase 3: empirical validation
5. **critical-research** — Phase 4: falsification search
6. **narrative-auditor** — Phase 5: self-audit of own report
7. **research-cross-validator** — Phase 6: multi-strategy verification
8. **research-synthesis** — Phase 7: decision document
