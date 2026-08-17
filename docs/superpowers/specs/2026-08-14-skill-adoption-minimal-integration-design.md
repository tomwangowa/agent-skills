# Skill Adoption: Minimal Integration Design

## Status

Approved design. The first implementation slice is complete: the selected
patterns were integrated into `brainstorming/SKILL.md` and committed as
`d24f475` on `main`. This document records the adoption decision and the
remaining boundaries; it does not introduce a standalone productivity skill.

## Goal

Borrow the useful design patterns from the external productivity skills without
duplicating capabilities already present in the local skill set.

The first adoption target is the local `brainstorming` skill. A standalone
`to-questionnaire` skill remains a later candidate, and `wait-what` remains
deferred.

## Context

The external review covered:

- `writing-for-agents`: context pointers, context load versus cognitive load,
  information hierarchy, progressive disclosure, completion criteria, and
  pruning.
- `to-questionnaire`: a user-invoked workflow for turning an information gap
  into an asynchronous questionnaire for a person who holds the missing
  context.
- `wait-what`: a short user-invoked recovery prompt that asks for a re-pitch in
  Simplified Technical English and a shared `CONTEXT.md` vocabulary.
- `grilling`: decision trees, frontier tracking, and fact-versus-decision
  separation.

The local skill set already has related ownership:

- `brainstorming` owns requirement discovery, decision grilling, design gates,
  and pre-implementation approval.
- `skill-router` owns discovery and routing. Its registry and catalog have
  separate source-of-truth roles.
- `handoff` owns reviewed handoff drafts, assertion allowlists, and
  `VERIFIED` / `NOT-VERIFIED` boundaries.
- `role-orchestrator` owns PM/RD artifacts and user review gates for larger
  workflows.

## Chosen Direction

Use a minimal integration rather than importing the external skills as-is.

### 1. Enrich `brainstorming` with four writing patterns

The first implementation updated
`/Users/tom_wang/.claude/skills/brainstorming/SKILL.md` with only these patterns:

1. **Completion criteria** — every phase and decision ends with an observable
   condition that says what is resolved and what remains open.
2. **Context load versus cognitive load** — when adding guidance, identify the
   cost paid on every invocation versus the cost paid by a human who must find
   the skill. Do not add always-loaded text without a trigger benefit.
3. **Progressive disclosure** — keep instructions needed by every branch in
   `SKILL.md`; move branch-specific reference material behind an explicit
   pointer only when the split improves reliability.
4. **Pruning** — remove duplicate, stale, or default-behavior instructions;
   keep one source of truth for each rule.

`leading words` and the full prose of `writing-for-agents` are reference ideas,
not first-phase requirements. The target is a sharper `brainstorming` workflow,
not a second meta-skill about documentation.

### 2. Define `to-questionnaire` as a conditional candidate

If repeated asynchronous information gathering justifies a new skill, it should
be a separate user-invoked skill with a narrow contract:

- Input: the recipient's role and the decisions or facts needed back.
- Output: a reviewable questionnaire draft aimed at the recipient's knowledge
  gap.
- Trigger: the user explicitly asks to prepare questions for another person or
  team.
- Non-trigger: the answer can be found by inspecting the repository, the task
  is an interactive brainstorming session, or the goal is to record an already
  completed conversation.
- Write gate: show the draft before writing a file. Do not copy the external
  skill's automatic write behavior into this local environment.

If implemented later, its router registration must be a separate change and
must preserve `skill-router`'s registry/catalog source-of-truth split.

### 3. Defer `wait-what`

Do not create a local `wait-what` skill in this phase. Its behavior depends on a
shared `CONTEXT.md` and ubiquitous-language contract that the local skill set
does not currently standardize. Without that contract, the skill would mostly
produce a generic rephrasing and could introduce incorrect terminology.

When a shared context contract exists, reassess whether this belongs as a
standalone user-invoked recovery skill or as a small recovery mode in an
existing communication skill.

### 4. Fold `grilling` patterns into existing ownership

Adopt only the following concepts in `brainstorming`:

- decision tree traversal;
- current frontier / unresolved branch tracking;
- fact lookup versus user-owned decision separation.

Do not add a second `grilling` skill or replace the existing one-question-at-a-
time interview contract.

## Alternatives Considered

### A. Minimal integration — recommended

- **How:** Add four writing patterns and the selected grilling concepts to
  `brainstorming`; keep `to-questionnaire` conditional; defer `wait-what`.
- **Benefits:** Smallest context increase, preserves local gates, and removes
  the most important design gap first.
- **Cost:** Some useful external reference remains unavailable as a named
  skill.
- **Pre-mortem:** In twelve months `brainstorming` becomes a longer meta-skill
  with more rules than agents can follow. Guard against this by keeping the
  first change to four patterns, moving branch-specific material behind
  pointers, and measuring whether each new rule changes behavior.

### B. Standalone adoption package

- **How:** Add local `writing-for-agents` and `to-questionnaire` skills, then
  register both with `skill-router`.
- **Benefits:** Clear separation and direct reuse by other skills.
- **Cost:** More always-loaded descriptions, more routing choices, and a new
  overlap boundary with `brainstorming`, `qa-to-notes`, and `role-pm`.
- **Pre-mortem:** Agents route to the new meta-skill instead of applying the
  existing workflow. This is a high cognitive-load failure for a benefit that
  has not yet been demonstrated.

### C. Reference-only adoption

- **How:** Keep the external skills as a reviewed comparison and make no local
  change.
- **Benefits:** No routing or maintenance cost.
- **Cost:** The identified completion-criteria and progressive-disclosure gap
  remains in the local design workflow.
- **Pre-mortem:** The analysis becomes a one-time report and the useful rules
  are not applied when `brainstorming` is maintained.

## Implementation Record and Remaining Boundary

The design was approved, and the first implementation slice was completed as
an independent change:

1. Updated `brainstorming` with the minimal writing and grilling patterns.
2. Ran pressure scenarios covering premature completion, inline guidance load,
   and fact/decision confusion.
3. Ran `quick_validate`, `skill-auditor`, and `git diff --check`; the final
   skill audit was 84/100, Ready, with zero critical or important findings.
4. Rebased the local commits onto the latest `origin/main` and pushed the
   resulting `main` commit `d24f475`.

Runtime forward testing remains a follow-up; the checks above are static and
local validation. Only if an actual recurring asynchronous-information need
is confirmed should `to-questionnaire` be designed and implemented as a
separate change.

Each implementation change retains separate gates for file writes, commit,
external review, push, and merge.

## Success Criteria

The design is successful when:

- the local `brainstorming` skill has explicit, checkable phase completion
  criteria;
- branch-specific guidance can be identified as inline or disclosed by a
  stated rule;
- duplicate and stale instructions have a defined pruning decision;
- `to-questionnaire` has a distinct trigger boundary from `brainstorming`,
  `qa-to-notes`, and `role-pm` before any `to-questionnaire` implementation
  begins;
- no new skill is added solely because an external skill exists.

## Out of Scope for This Slice

- Creating `to-questionnaire` or `wait-what`.
- Changing `skill-router`, `handoff`, or `role-orchestrator`.
- Adding a new `CONTEXT.md` standard.
- Copying external provider, auto-write, auto-commit, or routing behavior.
- Committing this design document without a separate explicit commit approval.
