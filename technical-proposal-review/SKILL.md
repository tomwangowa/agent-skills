---
name: technical-proposal-review
description: Use when the user asks to review a technical wiki, design proposal, RFC, or enhancement proposal while lacking project context ("review this enhancement proposal", "I don't know this project", "help me understand this technical wiki", "review this RFC", "technical proposal review"), or wants informed feedback on a design they did not author. Builds an evidence-grounded mental model first, separates unknowns from design flaws, then produces prioritized constructive technical feedback.
---

# Technical Proposal Review

Review a technical proposal from the position of an engineer who may not know the project yet.

**Core principle:** Understand before judging.

Do not convert missing context into criticism. Do not convert plausible inference into fact.

## When to Use

Use for:
- enhancement proposals
- technical wiki pages
- RFCs / design docs
- architecture change proposals
- internal engineering proposals written by another team or engineer
- reviews where the user explicitly lacks project background

## When NOT to Use

- PM spec / wireframe gap analysis before implementation → use `spec-gap-finder`
- verify documentation claims against an available codebase → use `codebase-audit`
- evaluate whether a specific technology can meet requirements → use `tech-feasibility`
- general source-code quality review → use the runtime-native code reviewer
- create a new technical design from requirements → use `role-rd`

## Inputs

Accept any combination of:
- proposal / wiki / RFC text or file
- linked architecture docs
- codebase or repository context
- diagrams or screenshots
- Jira / issue context
- author comments or review discussion

Work with the available material. Do not block merely because optional context is missing.

If referenced material is available locally or through an approved connected source, inspect it when it materially affects the review.

---

# Workflow

## Phase 1 — Establish Evidence Boundaries

Before interpreting the design, classify information into three buckets:

- **FACT** — explicitly stated in the supplied material or directly verified from an authoritative source
- **INFERENCE** — an interpretation grounded in stated evidence, but not explicitly established
- **UNKNOWN** — information required for stronger judgment but not currently available

Never present INFERENCE as FACT.

When evidence can be cited by file, section, line, code symbol, or document heading, attach that evidence to important conclusions.

## Phase 2 — Build the Mental Model

Assume the user is new to the project.

Reconstruct only what the evidence supports:

1. What the current system does
2. What problem or limitation motivates the proposal
3. Who or what is affected
4. Current components and responsibilities
5. Important data flow / control flow
6. APIs, persistence, state, dependencies, and trust boundaries when relevant

Produce a compact current-system flow when possible:

```text
Component A
  -> Component B
  -> Component C
```

If the document does not contain enough information to reconstruct part of the system, mark it UNKNOWN rather than filling the gap.

## Phase 3 — Reconstruct the Proposed Change

Explain:

- what changes
- what remains unchanged
- components added / modified / removed
- changed data flow or control flow
- the core design decision
- the stated rationale

Summarize as:

```text
BEFORE
[current behavior]

AFTER
[proposed behavior]
```

Do not infer author intent beyond what the evidence supports.

## Phase 4 — Understanding Gate

Before technical criticism, determine whether the available context is sufficient for a meaningful review.

Create:

### Ten Things to Know
The 5-10 facts that carry most of the proposal's meaning.

### Glossary
Only project-specific terms, acronyms, component names, protocols, or domain concepts needed to follow the proposal.

### Unknowns
Missing context that materially limits technical judgment.

### Hidden Assumptions
For each material assumption:

```text
Assumption:
Evidence:
If false:
Need verification:
```

Then assign:

- **READY** — enough context exists for technical review
- **PARTIAL** — some review is possible, but important judgments must remain conditional
- **NOT READY** — the material is too incomplete to make meaningful design judgments

If PARTIAL, continue but explicitly constrain the review to supported areas.
If NOT READY, stop design criticism and produce only the minimum questions needed to unblock understanding.

## Phase 5 — Questions for the Author

Generate only questions whose answers would materially improve understanding or a design decision.

Prioritize:

- **P0** — answer may determine whether the design is correct or viable
- **P1** — affects implementation, reliability, compatibility, maintenance, or rollout
- **P2** — improves clarity or documentation quality

Do not ask questions already answered by the supplied material.
Do not ask generic checklist questions without tying them to a concrete part of the proposal.

## Phase 6 — Technical Review

Run only if the Understanding Gate is READY or PARTIAL.

Evaluate applicable dimensions only:

### Correctness
- Does the proposed mechanism solve the stated problem?
- Are important scenarios or state transitions missing?
- Could it create inconsistent state or incorrect behavior?

### Architecture
- Are responsibilities assigned to the component or layer that owns the related state and behavior?
- Does coupling increase unnecessarily?
- Are abstractions justified by the problem?
- Is complexity proportional to the requirement?

### Reliability
- failure handling
- timeout / retry
- idempotency
- partial failure
- recovery
- race conditions / concurrency
- state consistency

### Performance
Only when evidence supports meaningful analysis:
- latency
- CPU / memory
- network / I/O
- scale / throughput

### Compatibility and Rollout
- backward compatibility
- API / schema compatibility
- migration
- versioning
- rollout
- rollback

### Security and Privacy
Only when relevant:
- trust boundaries
- authentication / authorization
- validation
- sensitive data handling
- privilege changes

### Maintainability and Operations
- testability
- observability
- debugging
- ownership
- operational complexity
- future change cost

For every issue, distinguish one of:

- **DESIGN FLAW** — available evidence shows the proposed behavior itself is problematic
- **MISSING CONTEXT** — reviewer lacks required project information
- **MISSING DOCUMENTATION** — the design may exist, but the proposal does not explain it
- **OPEN QUESTION** — a decision or behavior is not yet resolved

This classification is mandatory.

## Phase 7 — Challenge With Concrete Scenarios

For significant risks, use concrete failure scenarios:

```text
Scenario:
Trigger:
Observed behavior:
Impact:
Proposal handles it?: Yes / No / Unclear
Evidence:
```

Prefer 3-7 high-value scenarios over exhaustive generic edge-case lists.

## Phase 8 — Alternatives and Complexity Check

Do not invent alternatives merely to appear thorough.

Propose an alternative only when it reveals a meaningful trade-off or simpler viable design.

For each useful alternative:
- approach
- advantages
- disadvantages
- added/removed complexity
- conditions under which it is preferable

Explicitly answer:

> Is the proposed solution materially heavier than the problem requires (more moving parts, layers, or failure modes than the requirement demands)?

Support the answer with concrete design elements, not taste or style preference.

## Phase 9 — Constructive Review Feedback

Translate findings into comments the user can actually give to the author.

Prefer wording such as:
- 「我想確認……」
- 「這裡目前看起來依賴一個假設……」
- 「如果 X 發生，現在的設計會怎麼處理？」
- 「文件目前沒有交代 X；這會影響我對 Y 的判斷。」
- 「是否考慮過 X？我主要擔心的是 Y scenario。」

Avoid unsupported declarations such as:
- 「這個設計不好」
- 「這樣不合理」
- 「一定要改成……」

Prioritize feedback as:

- **Blocking** — correctness / viability / severe operational risk
- **Important** — should be resolved before implementation or rollout
- **Suggestion** — useful improvement but not required for correctness
- **Documentation** — improve the proposal's ability to communicate an existing design

## Examples

### Example 1 — RFC review without project background

**Input:** "Help me review this RFC for our billing service. I don't know this project."
The RFC document is provided (file or pasted text).

**Behavior:**
1. Phases 1-4 build the mental model and gate on understanding. Anything the RFC does not establish — e.g. how the current billing DB is migrated — is listed under Unknowns, not guessed.
2. Phase 5 produces P0 questions such as "How are in-flight subscriptions migrated during the cutover?" only if the RFC omits it.
3. Phases 6-9 produce the review; the report follows the Output Format with each issue tagged DESIGN FLAW / MISSING CONTEXT / MISSING DOCUMENTATION / OPEN QUESTION.

### Example 2 — Proposal review with codebase available

**Input:** "Review this enhancement proposal" + repository access.

**Behavior:** Claims that touch existing code (current component responsibilities, data flow) are verified against the repository and marked FACT with file/symbol evidence; unverifiable claims stay INFERENCE or UNKNOWN. The review only criticizes behavior the evidence actually contradicts.

### Example 3 — Material too thin to review

**Input:** A one-page sketch with no current-state description and no linked docs.

**Behavior:** The Understanding Gate returns NOT READY. No design criticism is emitted; the report contains the mental model of what is knowable, the Unknowns list, and the minimum P0 questions needed to unblock review.

---

# Output Format

Keep the report proportional to the proposal. Do not mechanically fill empty sections.

```markdown
# Technical Proposal Review: [Title]

## 1. Executive Summary
[5-10 sentences]

## 2. Mental Model
### Current System
...
### Proposed Change
...
### Before vs After
...

## 3. Evidence Boundary
### Facts
...
### Inferences
...
### Unknowns
...

## 4. Understanding Gate
**Status:** READY | PARTIAL | NOT READY
**Reason:** ...

### Ten Things to Know
1. ...

### Glossary
| Term | Meaning | Evidence / Confidence |
|------|---------|-----------------------|

## 5. Hidden Assumptions
| Assumption | Evidence | If False | Verification Needed |
|------------|----------|----------|---------------------|

## 6. Questions for the Author
### P0
- ...
### P1
- ...
### P2
- ...

## 7. Technical Review
### Blocking
- **[DESIGN FLAW / MISSING CONTEXT / MISSING DOCUMENTATION / OPEN QUESTION]** ...
### Important
- ...
### Suggestions
- ...

## 8. Failure Scenarios
...

## 9. Alternatives / Complexity Check
...

## 10. Review Comments I Can Use
[concise, constructive comments ready for discussion]

## 11. Confidence
**Overall:** High | Medium | Low
**Limited by:** ...
```

---

# Calibration Rules

1. **Understanding before critique.** Do not start with a flaw list.
2. **Evidence over plausibility.** Common industry practice is not evidence that this project works that way.
3. **Silence is not failure.** If the proposal omits retry, auth, migration, etc., classify it first as missing documentation/context unless evidence shows the design truly lacks it.
4. **No checklist dumping.** Only raise concerns that connect to the actual proposal.
5. **No architecture theater.** Do not reward or demand extra components, patterns, layers, or diagrams unless they solve a demonstrated problem.
6. **Risk-weighted depth.** Spend more review effort on correctness, irreversible changes, state, compatibility, security, and failure recovery than on naming or style.
7. **Separate comprehension difficulty from design quality.** A reviewer being unfamiliar with the project is not a defect in the design.
8. **Revise the mental model when contradicted.** Later evidence may invalidate earlier inference; update it explicitly.
9. **Do not force certainty.** Use "cannot determine from current evidence" whenever the material does not establish the answer.
10. **Prefer a small number of consequential comments.** Five well-supported comments are better than twenty generic observations.

# Escalation to Other Skills

Recommend another skill only when the proposal review exposes a distinct follow-up need:

- need to verify proposal claims against actual implementation → `codebase-audit`
- a technology choice is a key unresolved feasibility risk → `tech-feasibility`
- a critical assumption needs a minimal experiment → `micro-poc-validator`
- the input is primarily a PM spec / wireframe with implementation gaps → `spec-gap-finder`

Do not automatically run follow-up skills unless the surrounding harness permits it.
