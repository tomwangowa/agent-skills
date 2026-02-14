---
name: presentation-planner
description: >-
  Use before creating presentations — transforms a topic or rough outline into
  a complete Slide Plan with narrative strategy, audience analysis, and
  per-slide detail. Auto-chains to interactive-presentation-generator for
  production.
---

# Presentation Planner

## Overview

Turn a topic or rough outline into a validated Slide Plan through structured
planning, before any slides are generated.

**Core principle:** A presentation without a narrative strategy is just a
collection of bullet points. Every minute spent on planning saves ten minutes
of slide reshuffling.

**Violating the letter but not the spirit doesn't count.** Dumping the user's
outline into a slide-per-section format is not planning — it's transcription.
Real planning identifies the core message, selects a narrative framework,
and structures content for the target audience.

**Announce at start:**
> "Activating presentation planner — I'll help you design the narrative
> before generating any slides."

## When to Use

**Always before `interactive-presentation-generator`:**
- User wants to create a presentation from a topic or idea
- User has a rough outline that needs structure and polish
- User wants to convert a report or document into a presentation
- User asks "help me plan a talk about X"

**Exceptions (planner can be skipped):**
- User provides a complete, per-slide plan with titles and key points
- User explicitly says "skip planning" or "just generate slides"
- User only needs to re-style an existing presentation (no content change)

## The Iron Law

```
NO SLIDES WITHOUT A NARRATIVE STRATEGY FIRST
```

- Do NOT chain to `interactive-presentation-generator` before the user
  approves a Slide Plan
- Do NOT skip Audience Analysis — even "obvious" audiences have
  assumptions worth examining
- Do NOT present a Slide Plan and proceed without explicit user approval
- "Looks good" or "go ahead" from the user counts as approval
- Silence or topic change does NOT count as approval — ask explicitly

## Workflow

### Phase 1: Intake

**Auto-detect input mode:**

- **From-scratch:** User provides only a topic, keyword, or brief
  description → enter full planning flow from Phase 2
- **Optimize:** User provides an existing outline, document path, or
  pastes structured content → read and analyze, then skip to Phase 3
  with pre-filled context

**Gather information (one question at a time):**

1. **Purpose** — What should this presentation achieve?
   - Persuade (adopt a proposal, approve a budget)
   - Educate (teach a concept, share knowledge)
   - Report (status update, project summary)
   - Inspire (keynote, motivational, vision)
2. **Audience** — Who is listening?
   - Technical (engineers, developers)
   - Executive (C-suite, directors, managers)
   - General (mixed, non-specialist)
   - Domain expert (researchers, analysts, designers)
3. **Duration** — How long?
   - Lightning talk (5 min)
   - Short session (15 min)
   - Standard session (30 min)
   - Full session (60 min)
4. **Constraints** — Anything mandatory or forbidden?
   - Must-include content, company guidelines, tone requirements
   - If none, move on

**For Optimize mode:** Read the existing material first, then ask only
questions whose answers are not already evident from the content.

### Phase 2: Audience Analysis & Framework Selection

**Audience Profile:**
Generate a 3-sentence audience profile covering:
- Who they are and what they already know
- What they care about (their goals, pain points)
- What will make them act on your message

**Auto-select narrative framework** based on purpose + audience:

| Purpose | Audience | Framework |
|---------|----------|-----------|
| Persuade decision-makers | Executive | **SCQA** (Situation → Complication → Question → Answer) |
| Educate or share knowledge | Any | **What → So What → Now What** |
| Report progress or results | Executive / Mixed | **Chronological** (timeline with milestones) |
| Sell a product or project | Any | **Problem → Solution → Impact** |
| Tell a story or journey | General | **Hero's Journey** (challenge → transformation → result) |
| Compare options for a decision | Technical / Executive | **Compare & Contrast** (criteria matrix) |

**Present the selection:**
> "Based on your audience ([profile]) and purpose ([purpose]), I recommend
> the **[Framework Name]** framework because [reason]. Here's how it
> structures your talk: [brief outline of framework sections]."
>
> "Does this framework fit, or would you prefer a different approach?"

### Phase 3: Narrative Strategy & Outline

Produce:

1. **Core Message** — One sentence the audience should remember if they
   forget everything else
2. **Supporting Messages** — 3-5 key arguments or evidence that support
   the core message
3. **Story Arc** — Map each section to its role in the narrative:
   - Opening: hook the audience (question, statistic, story)
   - Build-up: establish context and evidence
   - Climax: deliver the core insight or recommendation
   - Resolution: summarize and call to action
4. **Section Outline** — Each section's title, purpose, and estimated
   slide count

**When material is insufficient:**
> "Your [section] lacks concrete data or examples. Would you like to run
> `critical-research` to find supporting evidence before continuing?"

If user declines, proceed with available material and note the gap.

**Present outline for approval.** User must confirm before Phase 4.

### Phase 4: Slide Plan

Expand the approved outline into a per-slide plan:

```markdown
## Slide Plan: [Presentation Title]

**Framework**: [Selected Framework]
**Duration**: [X] min | **Total slides**: [N]
**Core Message**: [One sentence]

---

### Slide 1: Title Slide
- **Title**: [Presentation title]
- **Subtitle**: [Context or tagline]
- **Visual**: Cover image

### Slide 2: [Opening Hook]
- **Title**: [Engaging question or statement]
- **Key Points**:
  - [Point 1]
  - [Point 2]
  - [Point 3]
- **Speaker Note**: [What to say, 2-3 sentences]
- **Visual Suggestion**: [chart / image / diagram / none]

### Slide 3-N: [Content Slides]
...

### Slide N: [Closing / CTA]
- **Title**: [Call to action or summary]
- **Key Points**:
  - [Takeaway 1]
  - [Takeaway 2]
  - [Next steps]
- **Speaker Note**: [Closing remarks]
- **Visual**: Ending image
```

**Slide count guidelines:**

| Duration | Slide Count | Pace |
|----------|-------------|------|
| 5 min | 5-7 slides | ~1 min/slide |
| 15 min | 12-18 slides | ~1 min/slide |
| 30 min | 20-30 slides | ~1-1.5 min/slide |
| 60 min | 35-50 slides | ~1-1.5 min/slide |

**Present Slide Plan for approval.** User must confirm before Phase 5.

### Phase 5: Handoff

After Slide Plan approval:

> "Slide Plan is ready. Would you like to generate the presentation now?"

- **Yes** → invoke `interactive-presentation-generator` with the Slide
  Plan as input. The generator can skip its own Step 1 (Gather
  Requirements) and Step 4 (Generate Content Structure) since the
  planner already produced them. Proceed directly to Step 2 (Choose
  Style) → Step 3 (Choose Format) → Step 5 (Generate Files).
- **No** → save the Slide Plan to
  `docs/presentations/YYYY-MM-DD-<topic>-slide-plan.md` and inform the
  user they can run `interactive-presentation-generator` later with this
  file as input.
- **Revise** → go back to the phase the user wants to adjust.

## Narrative Frameworks Reference

### SCQA (Situation → Complication → Question → Answer)
Best for persuading decision-makers. Establishes shared context, introduces
the problem, frames the question, then delivers the recommendation.

### What → So What → Now What
Best for education and knowledge sharing. Presents facts, explains their
significance, then suggests actions.

### Problem → Solution → Impact
Best for selling ideas or products. Shows the pain, presents the fix,
quantifies the benefit.

### Hero's Journey
Best for storytelling and inspiration. Takes the audience through a
challenge, the struggle, and the transformation.

### Compare & Contrast
Best for decision presentations. Sets criteria, evaluates options
side-by-side, delivers a recommendation.

### Chronological
Best for status updates and retrospectives. Walks through the timeline
with milestones, turning points, and current state.

## Rationalization Prevention

| Excuse | Reality |
|--------|---------|
| "The user already has an outline" | An outline is a list of topics, not a narrative. Lists don't persuade, stories do. |
| "This is just a status update" | Status updates are the most common bad presentations. A Chronological framework with a Core Message transforms them. |
| "The audience already knows the topic" | Experts are the hardest audience — they'll spot gaps in your argument instantly. Planning matters more, not less. |
| "I'll just make a slide per bullet" | That's a document, not a presentation. Presentations need a narrative arc. |
| "Planning takes too long" | A 5-minute talk needs a 5-minute plan. Saving 5 minutes of planning costs 30 minutes of reshuffling slides. |

## Red Flags — STOP

- You're generating slides and realize you never planned → **STOP.
  Plan first.**
- You skipped Audience Analysis because the audience "seemed obvious" →
  go back and write the profile
- You produced a Slide Plan that's just the outline with "Slide N:"
  prefixed → that's formatting, not planning
- You have no Core Message → the presentation has no point
- Every slide has 6+ bullet points → you're writing a document, not
  planning a presentation
- You chained to generator without user approval of the Slide Plan →
  revert and ask

## Examples

### Example 1: From-Scratch (Technical Talk)

**User:** "Help me plan a 30-minute talk on WebAssembly for backend devs"

**RIGHT:**
> "Activating presentation planner — I'll design the narrative first."
> 1. Gathers: Purpose = Educate, Audience = Technical, Duration = 30 min
> 2. Audience Profile: "Backend developers who know JavaScript/Python but
>    haven't used Wasm. They care about performance and deployment
>    simplicity. Concrete benchmarks will make them take Wasm seriously."
> 3. Auto-selects: **What → So What → Now What** (educational)
> 4. Core Message: "WebAssembly lets you run near-native-speed code in
>    places you never could before — and it's ready for production today."
> 5. Produces 22-slide plan with speaker notes
> 6. "Slide Plan ready. Generate now?" → chains to generator

**WRONG:**
> "I'll create a presentation about WebAssembly."
> (Skipped planning entirely, jumped to generator)

### Example 2: Optimize Mode (Existing Outline)

**User:** "I have this outline for my quarterly review, can you improve it?
[pastes 10 bullet points]"

**RIGHT:**
> "Activating presentation planner — I'll analyze your outline."
> 1. Detects Optimize mode, reads the 10 bullets
> 2. Asks: "Is this for your leadership team or your direct team?"
> 3. Identifies: no Core Message, flat structure, data-heavy sections
>    lack context
> 4. Auto-selects: **Chronological** with added "So What" for each
>    milestone
> 5. Restructures into narrative arc, suggests where to add impact
>    statements
> 6. Produces Slide Plan for approval

### Example 3: Report to Presentation

**User:** "Turn my monthly report into a presentation for the board"

**RIGHT:**
> 1. Reads the report file (Optimize mode)
> 2. Audience = Executive → auto-selects **SCQA**
> 3. Extracts data from report, restructures around a Core Message
> 4. Suggests: "The report has 15 metrics. For a board presentation,
>    I recommend focusing on the top 3 that support your Core Message.
>    The rest can go in an appendix slide."
> 5. Produces focused Slide Plan (not a 1:1 report-to-slides mapping)

## Constraints

- **One question per message** during intake — never batch questions
- **Always produce a Core Message** — no plan is complete without one
- **Always auto-select a framework** — present the recommendation, don't
  ask users to pick from a menu
- **Never skip Audience Analysis** — scale it down for obvious cases,
  don't skip it
- **Slide Plan must be approved** before handoff to generator
- **Respect slide count guidelines** — flag if the plan exceeds the
  guideline by more than 20%

---

## Error Handling

### User Provides Contradictory Requirements
- Surface the contradiction: "You mentioned this is for executives (who
  prefer high-level) but also want to include code demos (which are
  technical). Which takes priority?"
- Do not silently resolve — let the user decide

### User Abandons Mid-Session
- If the user changes topic or says "never mind", stop cleanly
- Do not save partial Slide Plans
- If resuming later, re-read context from scratch

### Existing Outline is Unstructured
- If the provided material is too unstructured to analyze (e.g., stream
  of consciousness notes), inform the user:
  "This material is quite unstructured. I'll switch to From-scratch mode
  and use your notes as reference material."
- Extract what you can, ask for the rest

### Content Exceeds Duration
- If the Slide Plan exceeds the target slide count by more than 20%:
  "The current plan has [N] slides for a [X]-minute talk. That's
  [Y] slides over the guideline. I recommend cutting [section] or
  splitting into two talks."
- Let the user decide what to cut

### Research Skill Unavailable or Inconclusive
- If user agrees to run `critical-research` but it returns inconclusive
  results, note the gap in the Slide Plan:
  "Speaker Note: [Data needed — research was inconclusive. Consider
  gathering this before presenting.]"

---

## Security Considerations

### Slide Plan File Safety
- Validate the `docs/presentations/` path exists before writing; create
  if missing
- Sanitize `<topic>` in filenames — strip characters outside `[a-z0-9-]`
  to prevent path traversal
- Never include confidential data in Slide Plans unless the user
  explicitly provides it

### User Input in Slide Plans
- Slide Plans may quote user content verbatim — escape markdown injection
  if rendered in web context
- Do not embed executable code blocks from user input without review
- Speaker Notes may contain sensitive talking points — remind user if
  the plan will be shared

### Scope Limitation
- This skill reads existing files (outlines, reports) and writes one
  Slide Plan file
- It does not generate presentation files (that's the generator's job)
- It does not execute code, install packages, or modify source files
- The only file mutation is creating `docs/presentations/*.md`

---

## Related Skills

- **interactive-presentation-generator** — downstream: produces slides
  from the Slide Plan
- **critical-research** — optional upstream: fills evidence gaps in
  Phase 3
- **report-generator** — optional upstream: reports can be input for
  Optimize mode
- **brainstorming** — sibling: both are planning skills; brainstorming
  is for code, presentation-planner is for slides
