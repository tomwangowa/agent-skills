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

Use this seven-stage flow in order:

1. **Intake**
2. **Audience Analysis & Framework Selection**
3. **Research Checkpoint**
4. **Narrative Strategy & Outline**
5. **Slide Plan + QA**
6. **User Approval**
7. **Generator Handoff**

The flow remains stage-gated. The planner must complete the current stage
before moving to the next, and User Approval remains an explicit gate before
Generator Handoff.

### Stage 1: Intake

**Auto-detect input mode:**

- **From-scratch:** User provides only a topic, keyword, brief, or rough
  direction → continue to Stage 2, Audience Analysis & Framework Selection.
  This mode does not treat supporting material as an existing slide structure.
- **Optimize:** User provides an existing document or structured content,
  including an outline, PPT, PDF, Markdown file, or report → read and analyze
  it, then continue to Stage 2 with pre-filled context. It must still pass
  through the Research Checkpoint in Stage 3; Optimize never skips that
  checkpoint. Ask only for decisions that are missing from the supplied
  material.

Every plan must record this intake metadata immediately after input-mode
detection:

```markdown
**Input Mode**: From-scratch | Optimize
**Source Type**: Topic / Brief / Outline / PPT / PDF / Markdown / Report
**Source of Truth**: [the primary source explicitly selected by the user]
**Cover Image**: [user-provided URL/path | generator style default | none]
**Ending Image**: [user-provided URL/path | generator style default | none]
**Logo**: [user-provided URL/path | none]
**Company Name**: [value | generator default | none/not applicable]
**Author Name**: [value | generator default | none/not applicable]
**Custom Footer Text**: [value | generator default | none/not applicable]
**Footer Enabled**: [enabled | disabled | generator default]
```

- `From-scratch` covers a topic, brief, or rough direction.
- `Optimize` covers existing documents or structured content, including an
  outline, PPT, PDF, Markdown file, or report.
- In the canonical `Source Type` enum, `Outline` means an existing outline
  supplied for optimization; it is distinct from a From-scratch rough
  direction or brief.
- If multiple sources exist, ask which one is the source of truth before
  planning when the answer is not already explicit.
- Do not infer the source-of-truth winner from file dates, memory,
  completeness, or model preference.

**Source-of-truth conflict handling:** When the declared source of truth
conflicts with supporting material, use the declared source, record the
conflict and its location, and do not silently merge the versions. A single
conflict does not stop the whole plan. An unresolved choice of primary source
does stop Intake until the user clarifies it.

**Optimize source semantics:**

- For existing slides, `Visible Elements` records what the source actually
  contains.
- For reports or long Markdown, `Visible Elements` records planned elements
  derived from the source; it must not claim that the source already had that
  layout.
- Source `Speaker Note` content remains a spoken supplement and does not enter
  `Visible Elements` unless the user explicitly asks for that.

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
5. **Visual assets and footer** — Resolve each value for the canonical metadata, asking each missing decision in a separate message:
   - Cover Image and Ending Image: user-provided URL/path, generator style default, or explicit `none`
   - Logo: user-provided URL/path or explicit `none`
   - Company Name, Author Name, and Custom Footer Text: explicit value, documented generator default, or `none/not applicable`
   - Footer Enabled: `enabled`, `disabled`, or documented generator default
   - If `Footer Enabled` is `enabled`, all three footer text fields must resolve to an explicit value or documented default. If disabled, they resolve to `none/not applicable`. Do not claim Step 1 can be skipped while any required value remains unresolved.

**For Optimize mode:** Read the existing material first, then ask only
questions whose answers are not already evident from the content, including
visual-asset and footer decisions.

### Stage 2: Audience Analysis & Framework Selection

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

### Stage 3: Research Checkpoint

Before producing a narrative, complete one bounded Research Checkpoint. This is
required for both From-scratch and Optimize inputs; neither mode may silently
skip it or turn it into open-ended topic research. The checkpoint tests only the
evidence needed to support the presentation's Core Message and major Supporting
Messages.

#### Material-Change Predicate

A **material change** is any of the following:

- new evidence, status change, or source issue that could change the Core
  Message, a major Supporting Message, a recommendation or comparison, the
  audience's decision, or the source-of-truth decision
- addition, removal, or material rewrite of the candidate or locked Core Message
  or a major Supporting Message
- addition, removal, material rewrite, or material strengthening of a visible-
  slide content claim or required data element

During the checkpoint, an initial material gap identified in Step 2 is also in
scope under this predicate. The last category excludes decorative details and
minor examples that do not affect the narrative or slide content. This named
predicate is the single rule for research offers and checkpoint re-entry.

#### Checkpoint Procedure

1. **Inventory material claims.** From the audience analysis, selected
   framework, and supplied material, list the candidate Core Message and each
   major Supporting Message. Assign exactly one evidence status using this
   precedence when more than one condition applies:
   **Conflicted > Gap > Unverified > Supported**.
   - **Conflicted** — credible sources disagree or the source of truth is
     unclear; this takes precedence over all other statuses
   - **Gap** — material evidence or a necessary example is missing and no
     conflict is established
   - **Unverified** — neither independent verification nor sufficient support
     from the explicit user-designated source exists
   - **Supported** — sufficient support exists and no higher precedence condition
     applies; label it as **independently verified** or
     **declared-source-supported (not independently verified)**
2. **Identify narrative-changing gaps.** Prioritize only gaps that could change
   the Core Message, weaken a major Supporting Message, reverse a comparison or
   recommendation, or materially change the audience's decision. Record the
   claim, why it matters, and the source or evidence location checked. Do not
   research decorative details, minor examples, or claims that do not affect the
   narrative.
3. **Reconcile sources without merging silently.** Use the source explicitly
   designated in Intake as the source of truth. Record conflicting supporting
   sources, inaccessible sources, stale data, and claims that cannot be
   independently verified. Do not silently choose a newer, fuller, or more
   convenient version. An unresolved conflict remains visible in the checkpoint
   output.
4. **Offer targeted `critical-research` when needed.** If any initial material
   gap identified in Step 2, new evidence, status change, or source issue meets
   the **Material-Change Predicate**, show the user the bounded research
   question(s) and offer `critical-research`. This is the same named predicate
   used to decide whether the change requires checkpoint re-entry below. If
   accepted, run research only for those questions and only for this checkpoint;
   require falsification-first findings, source transparency, and an explicit
   statement of remaining uncertainty. Do not broaden the topic or start
   another research loop without returning to the user for a new scope decision.
   If the user declines, or research is unavailable or inconclusive, preserve
   the gap only if the user explicitly accepts the third Stop Condition;
   otherwise leave acceptance pending and do not continue.

#### Stop Condition

Stop the checkpoint and lock its context when **one** of these conditions is
true:

- the Core Message and every major Supporting Message have sufficient evidence
  for the intended audience; or
- an explicit, user-designated source supports the Core Message and major
  Supporting Messages, even if independent verification is not available; or
- after targeted research is declined, unavailable, or inconclusive, the user
  explicitly accepts preserving a material gap, with its narrative impact and
  evidence status recorded.

This does not require resolving minor gaps. Do not claim that an explicit source
has been independently verified unless it has. A material gap may be carried
forward only under the third condition, with its impact and evidence status
recorded; otherwise, do not use it to justify another unbounded search.

#### Required Checkpoint Output

```markdown
## Research Checkpoint

**Candidate Core Message**: [one sentence]

| Message | Evidence status | Source / location | Narrative impact |
|---------|-----------------|------------------|------------------|
| Core | Supported / Unverified / Conflicted / Gap | ... | ... |
| Supporting 1 | ... | ... | ... |

**Material gaps and conflicts**: [claims, competing sources, and why they matter]
**Research offered**: [bounded `critical-research` questions, or "none needed"]
**Research result**: [findings and remaining uncertainty, if run]
**Unresolved gaps to preserve**: [gap, impact, and how it will be labeled in the Slide Plan]
**Material gap acceptance**: [accepted by user | pending | not applicable]
**Material gap / impact / status**: [gap | narrative impact | evidence status]
**Stop condition met**: [sufficient evidence | explicit source | accepted material gap | neither]

**Context Lock**: [input mode, source type, source of truth, audience, purpose,
duration, constraints, selected framework, and the evidence snapshot above]
```

Once the stop condition is met, the Context Lock is the contract for Stage 4
and later production. The locked Core Message and major Supporting Message set
are immutable: Stage 4 may organize them into an outline and shorten wording
for a slide title only when the meaning is unchanged, but it must not add,
remove, or materially rewrite them. If narrative work requires such a change,
stop and return explicitly to Stage 3 before continuing. Do not silently
restart research, switch or replace the source of truth, or relabel an evidence
status (**Supported**, **Unverified**, **Gap**, or **Conflicted**). A harmless
presentation-title edit is allowed and does not reopen the checkpoint. If any
new evidence, status change, source issue, or any Stage 4 or Stage 5 addition,
removal, material rewrite, or material strengthening of a visible-slide claim or
required data element meets the **Material-Change Predicate**, stop and return
explicitly to Stage 3, report what changed, and obtain a new locked context. A
status change that does not meet the Material-Change Predicate may instead be
recorded as an explicit, documented checkpoint update; it must not be made
silently. Other non-material updates may be recorded without reopening the
checkpoint.

### Stage 4: Narrative Strategy & Outline

Produce:

1. **Core Message** — Reproduce the locked Core Message from Stage 3. It may
   be shortened for a slide title only when its meaning is unchanged.
2. **Supporting Messages** — Reproduce the locked major Supporting Message set
   from Stage 3. Organize or label these messages for the outline, but do not
   add, remove, or materially rewrite them.
3. **Story Arc** — Map each section to its role in the narrative:
   - Opening: hook the audience (question, statistic, story)
   - Build-up: establish context and evidence
   - Climax: deliver the core insight or recommendation
   - Resolution: summarize and call to action
4. **Section Outline** — Each section's title, purpose, and estimated
   slide count

**When material is insufficient:**
The Stage 3 Research Checkpoint must already have identified and bounded any
material evidence gap. Do not start unbounded research here. Carry the locked
gap into the narrative and label its effect explicitly:

> "The locked Research Checkpoint found that [section/claim] lacks [data or
> example]. We can continue with the available material and mark this gap in
> the Slide Plan, or return explicitly to Stage 3 to scope a targeted
> `critical-research` question."

Use the locked Stage 3 checkpoint's **Material gap acceptance** field to
control this branch. If the field is **not applicable**, no unresolved material
gap was carried forward, so proceed without requesting gap acceptance. If the
field is **accepted by user**, proceed with available material only when the
checkpoint records the material gap, narrative impact, and evidence status. If
the field is **pending**, stop and request a decision before continuing. Do not
imply that an unavailable or inconclusive result resolved the gap.

**Present the outline as the Stage 4 output.** Continue to Stage 5 only after
narrative strategy and outline work is complete; the explicit user approval gate
is Stage 6, after the Slide Plan + QA.

### Stage 5: Slide Plan + QA

Expand the Stage 4 outline into a per-slide plan:

```markdown
## Slide Plan: [Presentation Title]

**Input Mode**: From-scratch | Optimize
**Source Type**: Topic / Brief / Outline / PPT / PDF / Markdown / Report
**Source of Truth**: [the primary source explicitly selected by the user]
**Cover Image**: [user-provided URL/path | generator style default | none]
**Ending Image**: [user-provided URL/path | generator style default | none]
**Logo**: [user-provided URL/path | none]
**Company Name**: [value | generator default | none/not applicable]
**Author Name**: [value | generator default | none/not applicable]
**Custom Footer Text**: [value | generator default | none/not applicable]
**Footer Enabled**: [enabled | disabled | generator default]
**Framework**: [Selected Framework]
**Duration**: [X] min | **Total slides**: [N]
**Core Message**: [One sentence]
**Locked Accepted Research Gap**: [none | accepted gap statement]
**Locked Gap Narrative Impact**: [none | impact on the narrative]
**Locked Gap Evidence Status**: [none | Gap / Unverified / Conflicted / Supported]
**Material Gap Acceptance**: [accepted by user | pending | not applicable]

---

### Slide 1: Title Slide
- **Title**: [Presentation title]
- **Subtitle**: [Context or tagline]
- **Visible Elements**:
  - **Title**: [visible title]
  - **Body**: [visible subtitle or other text]
- **Visual**: Cover image
- **Visual Constraints**:
  - [At most three hierarchy, emphasis, or layout limits]
- **QA**:
  - **Narrative alignment** (From-scratch) OR **Content coverage** (Optimize): Yes / No
  - **Required elements present** (From-scratch) OR **Unauthorized additions** (Optimize): Yes / No
  - **Visual constraint limit**: Yes / No

### Slide 2: [Opening Hook]
- **Title**: [Engaging question or statement]
- **Key Points**:
  - [Point 1]
  - [Point 2]
  - [Point 3]
- **Speaker Note**: [What to say, 2-3 sentences]
- **Visible Elements**:
  - **Title**: [visible title]
  - **Body**: [visible text or key content]
  - **Flow**: [relationship, if present]
  - **Comparison**: [comparison, if present]
  - **Table**: [table content, if present]
  - **Diagram**: [diagram relationship, if present]
  - **Callout**: [visible callout, if present]
- **Visual Suggestion**: [chart / image / diagram / none]
- **Visual Constraints**:
  - [Constraint 1]
  - [Constraint 2]
- **QA**:
  - **Narrative alignment** (From-scratch) OR **Content coverage** (Optimize): Yes / No
  - **Required elements present** (From-scratch) OR **Unauthorized additions** (Optimize): Yes / No
  - **Visual constraint limit**: Yes / No

### Slide 3-N: [Content Slides]
...

### Slide N: [Closing / CTA]
- **Title**: [Call to action or summary]
- **Key Points**:
  - [Takeaway 1]
  - [Takeaway 2]
  - [Next steps]
- **Speaker Note**: [Closing remarks]
- **Visible Elements**:
  - **Title**: [visible title]
  - **Body**: [visible text or key content]
  - **Callout**: [visible callout, if present]
- **Visual**: Ending image
- **Visual Constraints**:
  - [Constraint 1]
- **QA**:
  - **Narrative alignment** (From-scratch) OR **Content coverage** (Optimize): Yes / No
  - **Required elements present** (From-scratch) OR **Unauthorized additions** (Optimize): Yes / No
  - **Visual constraint limit**: Yes / No
```

**Slide Plan field semantics:**

- Every slide must record `Visible Elements`, `Visual Constraints`, and `QA`; retain
  the existing `Title`, `Subtitle`, `Key Points`, `Speaker Note`, and `Visual
  Suggestion` fields wherever they apply.
- `Visible Elements` contains only content and relationships that will be visible
  on the slide. Include only the applicable types: `Title`, `Body`, `Flow`,
  `Comparison`, `Table`, `Diagram`, and `Callout`; omit absent types rather than
  writing `N/A`.
- Do not put `Intent`, `Key Takeaway`, `Editorial Notes`, or `AI Explanation`
  in `Visible Elements`. `Key Points` and `Speaker Note` remain separate
  narrative/spoken supplements, not visible slide content; repeat content in
  `Body` when it is actually intended to appear on the slide.
- `Visual Suggestion` may recommend a chart, image, or diagram, but it never
  replaces the visible content that the slide must specify.
- `Visual Constraints` describe hierarchy, emphasis, or layout limits only. They
  must contain no new content and may contain no more than three items per slide.

**Mode-specific QA:**

- **From-scratch** — check every slide for:
  - **Narrative alignment**: visible elements and slide content support the
    slide's role in the narrative.
  - **Required elements present**: required content from the brief and slide role
    is present in the visible elements.
  - **Visual constraint limit**: no more than three visual constraints are listed.
- **Optimize** — check every slide for:
  - **Content coverage**: for existing slides, no source-visible content is
    omitted; for reports or long Markdown, important source content is retained
    in planned visible elements without claiming that the source already had
    that layout.
  - **Unauthorized additions**: for existing slides, no source-absent visible
    content is added; for reports or long Markdown, no unsupported claim is added.
  - **Visual constraint limit**: no more than three visual constraints are listed.
- Each QA item is recorded as `Yes` or `No`. Every `No` must be disclosed in the
  completed Slide Plan before Stage 6 approval. A `No` is non-blocking: the user
  may request correction or explicitly accept the exception. For every failed QA
  check, record its name, `No` status, reason, and an acceptance status of either
  `accepted by user` or `pending/unaccepted`; carry that complete record forward
  unchanged with the approved plan for handoff.

**Slide count guidelines:**

| Duration | Slide Count | Pace |
|----------|-------------|------|
| 5 min | 5-7 slides | ~1 min/slide |
| 15 min | 12-18 slides | ~1 min/slide |
| 30 min | 20-30 slides | ~1-1.5 min/slide |
| 60 min | 35-50 slides | ~1-1.5 min/slide |

**Complete Slide Plan + QA, then enter Stage 6: User Approval.** Do not hand
off to the generator until the user explicitly approves this Slide Plan.

### Stage 6: User Approval

Present the completed Slide Plan and its QA results, including every `No`, its
reason, and an acceptance status of `accepted by user` or `pending/unaccepted`.
Each `No` is visible before approval but is non-blocking: the user may request a
correction or explicitly accept it, with the acceptance status recorded. The user
must explicitly approve the plan
before proceeding to Stage 7. Silence or a topic change does not count as
approval; revise the requested stage instead.

### Stage 7: Generator Handoff

After the Stage 6 User Approval of the Slide Plan, pass the **complete approved
Slide Plan**, not a summary or reconstructed outline, to the generator. The
handoff must preserve the complete plan plus this metadata and audit context:

- `Input Mode`, `Source Type`, and `Source of Truth`
- every Step 1 visual-asset and footer requirement: `Cover Image`, `Ending
  Image`, `Logo`, `Company Name`, `Author Name`, `Custom Footer Text`, and
  `Footer Enabled`; each value must include its explicit selection, resolved
  generator default, or explicit `none` / not applicable resolution
- every slide's `Visible Elements` and `Visual Constraints`
- `Locked Accepted Research Gap`, `Locked Gap Narrative Impact`, `Locked Gap
  Evidence Status`, and `Material Gap Acceptance`
- every source-of-truth conflict, including the conflicting source and its
  concrete section, page, slide, or content anchor location
- every failed QA check with its check name, `No` status, reason, and acceptance
  status of either `accepted by user` or `pending/unaccepted`
- `Speaker Note` content as notes only; never convert it into automatic visible
  slide content

> "Slide Plan is ready. Would you like to generate the presentation now?"

- **Yes** → invoke `interactive-presentation-generator` with the complete
  approved Slide Plan as input. Step 1 (Gather Requirements) may be skipped only
  when the handoff preserves every requirement that Step 1 asks for: the content
  source, purpose, target audience, duration, cover image, ending image, logo,
  company name, author name, custom footer text, and footer enable/disable
  setting. Missing values must be resolved explicitly before claiming Step 1 is
  skipped: cover or ending images may explicitly use the generator's style
  defaults, the logo may be explicitly `none`, and footer settings may be
  explicitly disabled or assigned their documented defaults. When the footer is
  enabled, company name, author name, and custom footer text must each have an
  explicit value or a documented default. When the footer is disabled, those
  fields resolve to `none` or not applicable. Any unresolved enabled-footer
  field keeps Step 1 active; the generator must run Step 1 or explicitly collect
  and resolve it. The planner must not claim that Step 1 was skipped while
  leaving a requirement unresolved. Step 4 (Generate Content Structure) may be skipped because the
  complete approved Slide Plan supplies it. Only Steps 1 and 4 may be skipped;
  generator Steps 2 (Choose Style), 3 (Choose Output Format), 5 (Generate
  Files), 6 (Add Enhancements), and 7 (Provide Instructions) run unchanged.
  This handoff does not rewrite the generator's workflow.
- **No** → save the Slide Plan to
  `docs/presentations/YYYY-MM-DD-<topic>-slide-plan.md` and inform the
  user they can run `interactive-presentation-generator` later with this
  file as input.
- **Revise** → go back to the stage the user wants to adjust.

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
- A plan omits `Input Mode`, `Source Type`, or `Source of Truth` → restore the
  canonical metadata before continuing
- `Visible Elements` contains intent, key-takeaway interpretation, editorial
  notes, or AI explanation → remove it from visible content and keep narrative
  material in the appropriate separate field
- A slide has more than three `Visual Constraints` → reduce them to three or
  fewer; constraints must not add content
- An Optimize plan hides a failed QA check or treats a report as if it already
  had a slide layout → disclose the failure and label report elements as planned
- Research restarts after the checkpoint without an explicit return to Stage 3
  → stop and restore the locked context
- You chained to generator without user approval of the Slide Plan →
  revert and ask

## Examples

### Example 1: From-Scratch (Technical Talk)

**User:** "Help me plan a 30-minute talk on WebAssembly for backend devs"

**RIGHT:**
> "Activating presentation planner — I'll design the narrative first."
> 1. Records `Input Mode: From-scratch`, `Source Type: Topic`, and
>    `Source of Truth: the user's WebAssembly topic`.
> 2. Gathers: Purpose = Educate, Audience = Technical, Duration = 30 min.
> 3. Audience Profile: "Backend developers who know JavaScript/Python but
>    haven't used Wasm. They care about performance and deployment
>    simplicity. Concrete benchmarks will make them take Wasm seriously."
> 4. Auto-selects: **What → So What → Now What** (educational).
> 5. Research Checkpoint inventories the Core Message and major Supporting
>    Messages, confirms enough benchmark evidence, records `Stop condition
>    met: sufficient evidence`, and locks the context before outlining.
> 6. A representative slide records the canonical fields:
>    `Visible Elements` = `Title: Why Wasm matters` and `Body: benchmark
>    comparison`; `Visual Constraints` = `one dominant comparison`,
>    `high-contrast numbers` (two items); and `QA` = `Narrative alignment:
>    Yes`, `Required elements present: Yes`, `Visual constraint limit: Yes`.
>    Its separate `Speaker Note` explains the benchmark verbally and is not
>    copied into visible content.
> 7. Produces the complete Slide Plan, discloses any failed QA checks, asks
>    for explicit approval, then offers the generator handoff.

**WRONG:**
> "I'll create a presentation about WebAssembly."
> (Skipped the Research Checkpoint and Slide Plan approval, then jumped to
> the generator.)

### Example 2: Optimize Mode (Report with Source Conflict)

**User:** "Turn the current quarterly review report into a leadership deck;
the older outline is reference only."

**RIGHT:**
> "Activating presentation planner — I'll analyze the report and preserve its
> source boundaries."
> 1. Records `Input Mode: Optimize`, `Source Type: Report`, and
>    `Source of Truth: current quarterly review report`; reads the report
>    before asking only for missing purpose, audience, duration, or constraints.
> 2. Records the conflict: the older outline says the launch was in Q2 at
>    `Outline.md`, section "Timeline", bullet 4, while the report says Q3 at
>    `quarterly-review.md`, page 3, anchor "Launch milestone". It uses the
>    report and does not silently merge the dates.
> 3. For the report, labels `Visible Elements` as **planned elements derived
>    from the report**, not as a layout that already existed in the source:
>    `Title: Launch status` and `Body: Q3 milestone and metric`.
> 4. Uses Optimize QA on that slide: `Content coverage: Yes`,
>    `Unauthorized additions: No` (reason: the draft included a customer
>    count not supported by the report; `pending/unaccepted`), and
>    `Visual constraint limit: Yes`. The `No` is disclosed before approval,
>    remains non-blocking, and is either corrected or explicitly accepted by
>    the user.
> 5. Carries the complete plan, the Source of Truth conflict, planned-element
>    distinction, and the failed QA record into handoff only after explicit
>    Slide Plan approval.

### Example 3: Evidence Gap and Bounded Stop

**User:** "Plan a talk from this short brief; one supporting claim has no
reliable evidence, and I do not want indefinite research."

**RIGHT:**
> 1. Records `Input Mode: From-scratch`, `Source Type: Brief`, and the brief
>    as `Source of Truth`, then inventories the unsupported supporting claim.
> 2. Offers one bounded `critical-research` question tied to that claim. If
>    the user declines, the research skill is unavailable, or its result is
>    inconclusive, records that outcome and does not start another research
>    loop.
> 3. Requests an explicit decision. If the user accepts preserving the gap,
>    locks `Material Gap Acceptance: accepted by user` and records
>    `Locked Accepted Research Gap`, `Locked Gap Narrative Impact`, and
>    `Locked Gap Evidence Status: Gap` in the Slide Plan. The gap is labeled
>    in the affected slide and its `QA` remains visible.
> 4. Continues with available material only after that acceptance; otherwise
>    stops with `Material Gap Acceptance: pending` and asks the user to decide.
>    It never implies that declined, unavailable, or inconclusive research
>    resolved the gap or justifies an unbounded search.

## Writing Tone（暖色調語氣指南）

Slide Plan 的敘述段落應帶有溫度，像在跟同事分享觀察。

1. **對話式口吻** — 適度用「你」拉近距離，不說教
2. **問句引導節奏** — 用問句推進思路，特別適合 speaker notes 的段落開頭
3. **具體案例錨定** — 每個論點有具體人名、產品、數據支撐，不說空話
4. **坦誠面對不確定** — 用「值得注意的是...」「目前看來...」保留探索空間，不武斷定調
5. **段落短、呼吸快** — 一個段落一個觀點，短句收尾
6. **引用是為了對話** — 引述後接「這點呼應了...」「但換個角度看...」，不堆砌
7. **開放式收束** — 結尾留下問題或延伸方向

> 適用範圍：Core Message 描述、Speaker Notes、narrative arc 敘述。Slide 標題與 bullet points 維持精簡客觀。

## Constraints

- **One question per message** during intake — never batch questions
- **Always produce a Core Message** — no plan is complete without one
- **Always auto-select a framework** — present the recommendation, don't
  ask users to pick from a menu
- **Never skip Audience Analysis** — scale it down for obvious cases,
  don't skip it
- **Every slide must include canonical `Visible Elements`, `Visual Constraints`,
  and mode-specific `QA`** — omit absent visible element types, and limit visual
  constraints to three
- **Keep visible and narrative content separate** — `Intent`, `Key Takeaway`,
  `Editorial Notes`, `AI Explanation`, `Key Points`, and `Speaker Note` do not
  become visible elements merely because they are written in the plan;
  `Visual Suggestion` never substitutes for visible content
- **Every QA `No` must be disclosed before approval, remains non-blocking, and
  must carry its failure and acceptance status (`accepted by user` or
  `pending/unaccepted`) forward**
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
- When making that switch, reclassify the canonical metadata immediately:
  set `Input Mode` to `From-scratch`, change `Source Type` from `Outline` to
  `Brief` or `Topic` based on the remaining usable input, and retain the
  original outline as supporting material rather than the source of truth.
  Never emit a `From-scratch` plan whose canonical `Source Type` remains
  `Outline`.
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
  Stage 3
- **report-generator** — optional upstream: reports can be input for
  Optimize mode
- **brainstorming** — sibling: both are planning skills; brainstorming
  is for code, presentation-planner is for slides
