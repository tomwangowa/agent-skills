---
name: research-synthesis
description: >-
  Use after running 2+ research skills (critical-research, tech-feasibility,
  narrative-auditor, codebase-audit) to synthesize findings into a unified
  decision document. Resolves conflicts between sources, weighs evidence,
  and produces an actionable recommendation.
---

# Research Synthesis

## Overview

Aggregate findings from multiple research skills into a single decision
document that resolves conflicts, weighs evidence, and delivers a clear
recommendation.

**Core principle:** Decisions should be traceable to evidence. Every
recommendation in the decision document must cite which research skill
produced the supporting or opposing evidence.

**Violating the letter but not the spirit doesn't count.** Summarizing
research outputs without resolving contradictions is not synthesis — it's
concatenation. Real synthesis confronts disagreements, assigns weights,
and commits to a recommendation even when evidence is mixed.

**Announce at start:**
> "Synthesizing research findings into a decision document."

## When to Use

**After research is complete:**
- 2+ research skills have been run in the current session
- The user needs to make a decision based on collected evidence
- Findings from different sources need reconciliation

**Manual triggers:**
- "synthesize my research" / "整合研究結果"
- "write a decision doc" / "寫決策文件"
- "what should we do based on the research?"
- "summarize findings and recommend"
- "ADR" / "architecture decision record"

**Prompted by other skills:**
- After `brainstorming` Phase 3 invokes `tech-feasibility` and/or
  `critical-research` — synthesis aggregates before returning to design
- After running `narrative-auditor` + `codebase-audit` on the same
  topic — findings need reconciliation

**Do NOT use when:**
- Only one research skill was run (its own output is sufficient)
- The user wants raw research, not a decision
- The question is simple enough that a single skill already answered it

## Workflow

### Phase 1: Inventory Research Findings

Scan the current conversation for outputs from research skills.
Identify each by its distinctive structure:

| Skill | Recognition Pattern |
|-------|-------------------|
| critical-research | `Verdict:` + `Confidence:` + evidence tables |
| tech-feasibility | `Decision:` (Go/Conditional-Go/Pivot/No-Go) + kill criteria |
| narrative-auditor | Per-claim verdicts (ACCURATE/MISLEADING/FALSE) |
| codebase-audit | Accuracy score (X/Y = Z%) + claim verdicts |

**If findings are from a previous session**, ask the user to paste or
provide the relevant outputs.

**Minimum requirement:** 2 distinct research outputs. If only 1 exists,
inform the user: "Only one research source found. Its conclusion stands
on its own — synthesis adds value when there are multiple sources to
reconcile."

### Phase 2: Normalize Verdicts

Map each skill's verdict system to a common schema:

| Original Verdict | Normalized Strength | Normalized Status |
|-----------------|--------------------|--------------------|
| critical-research: Supported / High confidence | Strong | Confirmed |
| critical-research: Partially Supported / Medium | Moderate | Partially confirmed |
| critical-research: Weakened / Low | Weak | Challenged |
| critical-research: Falsified | Strong | Refuted |
| tech-feasibility: Go / High confidence | Strong | Confirmed |
| tech-feasibility: Conditional-Go | Moderate | Conditionally confirmed |
| tech-feasibility: Pivot | Moderate | Challenged |
| tech-feasibility: No-Go | Strong | Refuted |
| narrative-auditor: ACCURATE | Strong | Confirmed |
| narrative-auditor: DECONTEXTUALIZED | Moderate | Partially confirmed |
| narrative-auditor: MISLEADING / FALSE | Strong | Refuted |
| narrative-auditor: UNVERIFIABLE | Weak | Uncertain |
| codebase-audit: VERIFIED | Strong | Confirmed |
| codebase-audit: PARTIALLY VERIFIED | Moderate | Partially confirmed |
| codebase-audit: FALSE | Strong | Refuted |
| codebase-audit: UNVERIFIED / UNFALSIFIABLE | Weak | Uncertain |

### Phase 3: Identify Conflicts and Agreements

Create a findings matrix:

```markdown
## Findings Matrix

| Topic / Claim | critical-research | tech-feasibility | narrative-auditor | codebase-audit | Consensus |
|--------------|-------------------|------------------|-------------------|----------------|-----------|
| [Claim A] | Confirmed (Strong) | — | — | — | Single source |
| [Claim B] | Confirmed (Mod) | Confirmed (Strong) | — | — | Agreement |
| [Claim C] | Challenged (Weak) | Confirmed (Strong) | — | — | **Conflict** |
```

**For each conflict:**
1. State what each source found
2. Assess why they disagree (different scope? different evidence?)
3. Determine which source is more authoritative for this specific claim
4. Document the resolution rationale

### Phase 4: Weigh Evidence and Decide

Apply evidence hierarchy:

1. **Direct verification** (codebase-audit ran the code) > **Indirect
   analysis** (critical-research cited papers)
2. **Primary sources** (narrative-auditor checked originals) > **Secondary
   sources** (summaries, articles)
3. **Reproducible evidence** (tests, benchmarks) > **Theoretical arguments**
4. **Specific evidence** (about this exact case) > **General evidence**
   (about similar cases)

When evidence is evenly split, state the uncertainty explicitly rather
than forcing a false conclusion.

### Phase 5: Generate Decision Document

Produce an ADR-style document:

```markdown
# Decision: [Title]

**Date**: YYYY-MM-DD
**Status**: Proposed | Accepted | Superseded by [link]
**Decision makers**: [user / team]

## Context

[What prompted this research? What question needed answering?]

## Research Conducted

| Skill | Focus | Verdict | Confidence |
|-------|-------|---------|------------|
| critical-research | [topic] | [normalized] | [High/Medium/Low] |
| tech-feasibility | [topic] | [normalized] | [High/Medium/Low] |
| ... | ... | ... | ... |

## Findings

### Agreements
<!-- Claims confirmed by 2+ sources -->

### Conflicts and Resolutions
<!-- Disagreements with explicit resolution rationale -->

### Uncertainties
<!-- Claims that remain unresolved -->

## Decision

[Clear, actionable statement of what we decided and why.]

## Consequences

### Expected Benefits
- [Benefit traced to evidence]

### Known Risks
- [Risk traced to evidence]

### Open Questions
- [What we still don't know]

## Alternatives Considered

| Alternative | Why Rejected | Source |
|-------------|-------------|--------|
| [Option B] | [Reason] | [Which skill found this] |
```

### Phase 6: Review and Save

1. Present the draft to the user
2. Iterate until approved
3. **Save** to `docs/decisions/YYYY-MM-DD-<topic>.md`
4. **Commit** with message: `docs(decisions): add <topic> decision record`
5. **Transition** based on context:
   - If called from `brainstorming` → return to brainstorming with the
     decision as input for design
   - If standalone → done, or suggest `sp-writing-plans` if
     implementation follows

## Examples

### Example 1: Technology Choice After Multiple Research Skills

**Context:** User ran `tech-feasibility` on Redis vs. Memcached, then
`critical-research` on "Redis is always faster than Memcached for
session storage."

**WRONG:**
> "tech-feasibility says Go for Redis. critical-research says the
> 'always faster' claim is Partially Supported. So Redis is probably
> fine." (No conflict resolution, no decision document)

**RIGHT:**
> "Synthesizing research findings into a decision document."
> 1. Inventories: tech-feasibility (Go, High confidence for Redis) +
>    critical-research (Partially Supported — Redis is faster for
>    reads but Memcached wins on multi-threaded write loads)
> 2. Identifies conflict: tech-feasibility assumed read-heavy workload;
>    critical-research found write-heavy counter-evidence
> 3. Resolves: "Our session store is 90% reads, 10% writes — Redis's
>    read advantage applies to our case"
> 4. Produces ADR with clear "Decision: Use Redis" + risk note about
>    write-heavy growth scenario

### Example 2: Claim Verification Across Sources

**Context:** User ran `narrative-auditor` on a vendor's blog post
claiming "99.9% uptime", then `codebase-audit` on the vendor's SDK
docs.

**RIGHT:**
> 1. narrative-auditor: "99.9% uptime" rated DECONTEXTUALIZED (only
>    applies to US-East region)
> 2. codebase-audit: SDK docs claim "automatic failover" rated FALSE
>    (no failover code found in SDK)
> 3. Synthesis: "Vendor uptime claim is region-limited and their SDK
>    lacks the failover they advertise. Recommendation: require SLA
>    contractually, implement our own failover."

## Rationalization Prevention

| Excuse | Reality |
|--------|---------|
| "The research was clear, no synthesis needed" | If it was clear, synthesis takes 2 minutes. If you're wrong about clarity, synthesis catches the gap. |
| "I can just pick the strongest finding" | Cherry-picking one source while ignoring others is confirmation bias, not synthesis. |
| "The conflicts don't matter for our case" | Document why they don't matter. If you can't articulate it, they might matter more than you think. |
| "An ADR is overkill" | The ADR can be 10 lines for a minor decision. The format ensures completeness, not length. |

## Red Flags — STOP

- You're writing a decision without citing which skill produced the
  evidence → every claim needs attribution
- You resolved a conflict by ignoring one side → go back and explain
  why one source outweighs the other
- Your "synthesis" is just the research outputs pasted in sequence →
  that's concatenation, not synthesis
- You recommended an option without listing alternatives → document
  what was rejected and why

## Constraints

- **Minimum 2 research sources** — don't synthesize a single output
- **Every claim traced to a source** — no unsourced assertions
- **Conflicts must be resolved explicitly** — no silent omissions
- **ADR format** — all decision documents follow the template
- **Save to docs/decisions/** — consistent location
- **Short by default** — minor decisions: 1 page; major: 2 pages max

---

## Error Handling

### Only One Research Source Available
- Inform the user that synthesis requires 2+ sources
- Suggest running an additional research skill, or confirm that the
  single source's conclusion is sufficient

### Research Findings Are Stale (From a Prior Session)
- Ask the user to paste relevant outputs
- Flag that evidence may be outdated if the codebase or external
  context has changed since the research was conducted
- Consider re-running research skills if findings are older than 2 weeks

### All Sources Agree (No Conflicts)
- Synthesis is still valuable: it produces a formal decision record
- Note the agreement explicitly: "All N sources converge on the same
  conclusion, increasing overall confidence"
- Keep the document shorter since conflict resolution is unnecessary

### Irreconcilable Conflict
- When two sources directly contradict with equal authority, do not
  force a resolution
- Present both positions clearly and recommend the user make a judgment
  call, or suggest a PoC / experiment to break the tie
- Document: "This conflict could not be resolved from available
  evidence. Recommended next step: [experiment / expert consultation]"

---

## Security Considerations

### Decision Document Content
- Decision documents may reference proprietary architecture or vendor
  evaluations — remind the user if the repo is public
- Do not include API keys, credentials, or pricing details verbatim
  from research outputs
- Sanitize vendor names or internal project names if the document will
  be shared externally

### Evidence Integrity
- Do not modify or paraphrase research findings in ways that change
  their meaning — quote or summarize faithfully
- If a research skill's output was ambiguous, flag the ambiguity rather
  than resolving it silently

### File Path Safety
- Sanitize filenames: strip characters outside `[a-z0-9-]`
- Validate `docs/decisions/` exists before writing; create if missing

---

## Related Skills

- **critical-research** — upstream: provides falsification-first verdicts
- **tech-feasibility** — upstream: provides Go/No-Go technology assessments
- **narrative-auditor** — upstream: provides per-claim accuracy verdicts
- **codebase-audit** — upstream: provides documentation accuracy scores
- **assumption-extractor** — upstream: provides structured assumption
  inventories with verification status and risk classification
- **micro-poc-validator** — upstream: provides empirical evidence
  (PASS/FAIL/PARTIAL) for specific technical assumptions
- **research-cross-validator** — upstream: provides multi-strategy
  cross-validation results with per-claim consensus ratings
- **brainstorming** — caller: invokes research skills in Phase 3, then
  synthesis before returning to design
- **tech-research-pipeline** — orchestrator: invokes synthesis as the
  final phase (Phase 7) to produce the decision document
- **sp-writing-plans** — downstream: once a decision is made, plan the
  implementation
