---
name: brainstorming
description: >-
  Use before any creative or implementation work — new features, architecture
  changes, refactoring, or workflow design. Explores intent through Socratic
  dialogue, proposes approaches with trade-offs, and produces an approved
  design before any code is written.
---

# Brainstorming Ideas Into Designs

## Overview

Turn vague ideas into validated designs through structured dialogue,
before a single line of code exists.

**Core principle:** Design is not overhead — it is the fastest path to
correct implementation. Every hour of brainstorming saves ten hours of
rework.

**Violating the letter but not the spirit doesn't count.** Presenting a
"design" that's just a restatement of the user's request with
implementation steps tacked on is not brainstorming — it's performing
agreement. Real brainstorming challenges assumptions, surfaces hidden
requirements, and explores alternatives the user hasn't considered.

**Announce at start:**
> "Activating brainstorming — I'll explore the idea with you before
> writing any code."

## When to Use

**Always:**
- New feature or capability
- Architecture or design changes
- Significant refactoring (touching 3+ files or changing interfaces)
- Workflow or process design
- Any task where the user's first message contains ambiguity

**Exceptions (brainstorming can be skipped):**
- Single-line bug fixes with obvious root cause
- Typo corrections, formatting changes
- Tasks where the user provides a complete, unambiguous spec
- The user explicitly says "skip brainstorming" or "just do it"

Thinking "this is too trivial to need a design"? That's exactly when
unexamined assumptions cause the most wasted work. The design can be
three sentences for a small task, but it MUST exist and be approved.

## The Iron Law

```
NO CODE WITHOUT AN APPROVED DESIGN FIRST
```

- Do NOT create files, write functions, scaffold projects, or invoke
  implementation skills before the user approves a design
- Do NOT use EnterPlanMode as a substitute — brainstorming comes BEFORE
  planning
- Do NOT present a design and proceed without explicit user approval
- "Sounds good" or "go ahead" from the user counts as approval
- Silence or topic change does NOT count as approval — ask explicitly

## Workflow

### Phase 1: Understand Context

Before asking any questions, silently gather context:

- Read relevant files (README, CLAUDE.md, existing code in the area)
- Check recent git commits for related work
- Identify existing patterns, conventions, and constraints

Do NOT dump findings on the user. Use them to ask better questions.

### Phase 2: Socratic Dialogue

Ask questions **one at a time**. After each answer, ask the next
question informed by the response.

**Question strategy:**
1. **Purpose** — "What problem does this solve?" / "Who is this for?"
2. **Scope** — "What's in scope? What's explicitly out of scope?"
3. **Constraints** — "Any technical constraints, deadlines, or
   dependencies?"
4. **Success criteria** — "How will we know this works correctly?"
5. **Edge cases** — "What happens when X fails / is empty / is huge?"

**Prefer multiple-choice questions** when you can anticipate the likely
answers. Open-ended questions are fine when you genuinely can't predict.

**Stop asking when:** you can describe the solution back to the user and
they agree you understand it. Don't over-interview — 3-5 questions is
typical.

### Phase 3: Explore Approaches

Propose **2-3 approaches** with trade-offs:

```
## Approach A: [Name] (Recommended)
- **How:** [Brief description]
- **Pros:** [Why this is recommended]
- **Cons:** [Honest downsides]
- **Effort:** [Relative estimate: small / medium / large]

## Approach B: [Name]
- **How:** [Brief description]
- **Pros:** [Advantages over A]
- **Cons:** [Why A is still preferred]
- **Effort:** [Relative estimate]

## Approach C: [Name] (if applicable)
- ...
```

**Lead with your recommendation** and explain why. Don't present options
as equally valid if they aren't.

**REQUIRED:** When approaches involve technical decisions (choice of
library, architecture pattern, protocol, data store, or any component
the team hasn't used before), you MUST invoke `tech-feasibility` to
evaluate the candidates before presenting them. When approaches depend
on factual claims about performance, scalability, or compatibility, you
MUST invoke `critical-research` to verify those claims. Do not present
unverified technical opinions as trade-off analysis.

### Phase 4: Present Design

Present the design in sections **scaled to complexity**. A single-file
task might need only "What we're building" and "How it works". A
multi-component task needs all sections.

After **each section**, ask: "Does this look right so far?"

Sections (use as needed):
1. **What we're building** — one-paragraph summary
2. **Architecture / Components** — how pieces fit together
3. **Data flow** — inputs, transformations, outputs
4. **API / Interface** — what the user or other code interacts with
5. **Error handling** — what can go wrong, how we handle it
6. **Testing strategy** — what tests prove this works
7. **Out of scope** — what we're explicitly NOT doing (YAGNI)

### Phase 5: Document and Transition

After user approval:

1. **Write design doc** to `docs/plans/YYYY-MM-DD-<topic>-design.md`
2. **Commit** the design doc with message:
   `docs(plans): add <topic> design`
3. **Transition:**
   - For multi-step tasks → invoke `sp-writing-plans`
   - For trivial tasks (user approved a 3-sentence design) → proceed
     directly with user's permission

**The default next step is `sp-writing-plans`.** Only skip it when the
design is so small that a plan would be longer than the implementation.

## Rationalization Prevention

| Excuse | Reality |
|--------|---------|
| "The user already knows what they want" | Users know what they want at a high level. The details where bugs live are unexplored. |
| "This is just a small change" | Small changes with wrong assumptions waste more time than large well-designed features. |
| "I'll figure it out as I code" | That's called prototyping, not implementation. You'll throw it away. |
| "The user seems impatient" | Spending 2 minutes on design saves 20 minutes of wrong-direction coding. Users prefer this. |
| "I already know the best approach" | Then presenting it for approval takes 30 seconds. If you're right, no time lost. If wrong, disaster averted. |
| "EnterPlanMode covers this" | Planning is HOW to build. Brainstorming is WHAT to build and WHY. Different stages. |

## Red Flags — STOP

- You're writing code and realize you never brainstormed → **STOP.
  Revert. Brainstorm.**
- You presented "one approach" instead of 2-3 → go back and explore
  alternatives
- You asked 3+ questions in a single message → slow down, one at a time
- You're copy-pasting the user's request as the "design" → that's not
  design, that's transcription
- You skipped context gathering → you're guessing instead of designing

## Examples

### Example 1: Simple Feature

**User:** "Add a dark mode toggle to the settings page"

**WRONG:**
> "I'll add a dark mode toggle. Let me create the component..."
> (Skipped brainstorming entirely)

**RIGHT:**
> "Activating brainstorming — let me explore this before writing code."
> 1. Reads existing settings page, theme system, CSS architecture
> 2. "Is this a system-preference-aware toggle (follows OS setting) or a
>    manual override that persists across sessions?"
> 3. [User answers]
> 4. "Where should the preference be stored?
>    A) localStorage (simplest, no backend)
>    B) User profile API (syncs across devices)
>    C) CSS custom properties only (no persistence)"
> 5. [Presents 2 approaches with trade-offs, gets approval]
> 6. Writes 5-sentence design doc → invokes sp-writing-plans

### Example 2: Ambiguous Request

**User:** "Make the app faster"

**WRONG:**
> "Here are 3 approaches to improve performance:
>  1. Add caching  2. Optimize queries  3. Use CDN"
> (Jumped to solutions without understanding the problem)

**RIGHT:**
> "Activating brainstorming — 'faster' can mean many things."
> 1. "Which part feels slow? Initial load, navigation between pages,
>    or specific actions like search?"
> 2. [User: "Search is unbearable"]
> 3. Profiles search endpoint, reads query code
> 4. "Search takes 3.2s. The bottleneck is a full table scan on the
>    `products` table. Two approaches: ..."
> 5. Invokes tech-feasibility to evaluate indexing vs. search engine

## Constraints

- **One question per message** — never batch questions
- **Never skip for small tasks** — scale the design down, don't skip it
- **Never present a single approach** — minimum 2 options
- **Never proceed without explicit approval**
- **YAGNI ruthlessly** — remove speculative features from every design
- **Design docs are short** — the design doc should be shorter than the
  implementation it describes

## Error Handling

### User Abandons Mid-Session
- If the user changes topic or says "never mind", acknowledge and stop
  brainstorming cleanly — do not persist partial design docs
- If resuming later, re-read context from scratch rather than relying on
  stale prior dialogue

### Context Too Large for Single Session
- If the codebase area is too large to fully explore in Phase 1, focus
  on the entry points and interfaces most relevant to the user's idea
- Document known unknowns in the design doc's "Out of scope" section

### User Provides Contradictory Requirements
- Surface the contradiction explicitly: "You mentioned X, but also Y —
  these seem to conflict. Which takes priority?"
- Do not silently resolve contradictions by picking one side

### Sub-Skill Invocation Failures
- If `tech-feasibility` or `critical-research` cannot reach a
  conclusion, document the uncertainty in the approach trade-offs
- Present the uncertainty to the user rather than hiding it

---

## Security Considerations

### Design Document File Safety
- Validate the `docs/plans/` path exists before writing; create it if
  missing rather than writing to an unexpected location
- Sanitize the `<topic>` in filenames — strip characters outside
  `[a-z0-9-]` to prevent path traversal or shell injection
- Never include secrets, API keys, or credentials in design documents
  even if the user mentions them in dialogue

### User Input in Design Documents
- Design docs may quote user requirements verbatim — escape any content
  that could be interpreted as markdown injection if the doc is rendered
  in a web context
- Do not embed executable code blocks from user input without review

### Scope Limitation
- This skill is read-heavy (gathers context) and write-light (one
  design doc). It does not execute code, install packages, or modify
  existing source files
- The only file mutation is creating `docs/plans/*.md` and committing it

---

## Related Skills

- **sp-writing-plans** — the default downstream skill (design → plan)
- **tech-feasibility** — REQUIRED in Phase 3 for technical decisions
- **critical-research** — REQUIRED in Phase 3 for factual claims
- **research-synthesis** — invoke after Phase 3 when 2+ research skills
  were used, to reconcile findings before presenting design
- **sp-test-driven-development** — downstream of sp-writing-plans (plan → tests → code)
