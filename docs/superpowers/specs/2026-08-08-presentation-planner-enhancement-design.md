# Presentation Planner Enhancement Design

## 1. Goal

Improve the existing `presentation-planner` skill by extracting reusable principles from the AI Native presentation production notes, while preserving its original purpose: audience analysis, narrative strategy, Slide Plan creation, explicit approval, and handoff to `interactive-presentation-generator`.

The referenced notes will not become a skill in this task. A separate skill may be designed later.

## 2. Workflow

The planner keeps its existing flow and adds source-aware production safeguards:

```text
Intake
  ↓
Audience Analysis & Framework Selection
  ↓
Research Checkpoint
  ↓
Narrative Strategy & Outline
  ↓
Slide Plan + QA
  ↓
User Approval
  ↓
Generator Handoff
```

### 2.1 Intake metadata

Record these values at the beginning of every Slide Plan:

- `Input Mode`: `From-scratch` or `Optimize`
- `Source Type`: `Topic`, `Brief`, `PPT`, `PDF`, `Markdown`, or `Report`
- `Source of Truth`: the primary source explicitly selected by the user

When multiple sources conflict, use the declared source of truth, record the conflict, and do not silently merge or infer a winner. A single conflict does not block the whole plan. If no primary source is clear, ask before continuing.

### 2.2 Input modes

**From-scratch** applies to a topic, brief, or rough direction. `Visible Elements` describes the planned content structure, and `Visual Constraints` provides guidance for the eventual slide generation.

**Optimize** applies to an existing outline, PPT, PDF, Markdown file, or report. For existing slides, `Visible Elements` records elements actually present in the source. For reports or long-form Markdown, it records planned elements derived from the source and must not pretend that the original source already had that layout.

`Speaker Note` remains a spoken supplement. Source speaker notes must not be copied into `Visible Elements` unless the user explicitly requests that behavior.

## 3. Research Checkpoint

The Research Checkpoint occurs after audience/framework analysis and before narrative strategy.

1. Identify evidence gaps affecting the Core Message or Supporting Messages.
2. Identify source conflicts and claims that remain unverified.
3. Offer `critical-research` when a gap affects the narrative or slide content.
4. Stop once the Core Message and each major Supporting Message have enough evidence or an explicit source.
5. Lock the research context before entering production.

The stop condition is sufficient evidence for this presentation, not exhaustive background research. Preserve unresolved gaps in the Slide Plan rather than filling them with guesses.

After the checkpoint, do not silently restart research, rename locked concepts, or change the source-of-truth content. Perform consistency checks only. If new evidence would change the core narrative or source decision, pause handoff and return to the Research Checkpoint explicitly.

## 4. Slide Plan schema

The existing narrative fields remain. Add the following metadata and per-slide fields:

```markdown
**Input Mode**: From-scratch | Optimize
**Source Type**: Topic / Brief / PPT / PDF / Markdown / Report
**Source of Truth**: [primary source]

### Slide N: [Slide Title]
- **Title**: [slide title]
- **Subtitle**: [optional]
- **Visible Elements**:
  - **Title**: [visible title]
  - **Body**: [visible text or key content]
  - **Flow**: [relationship, if present]
  - **Comparison**: [comparison, if present]
  - **Table**: [table content, if present]
  - **Diagram**: [diagram relationship, if present]
  - **Callout**: [visible callout, if present]
- **Key Points**:
  - [narrative point]
- **Speaker Note**: [spoken supplement]
- **Visual Suggestion**: [chart / image / diagram / none]
- **Visual Constraints**:
  - [constraint 1]
  - [constraint 2]
- **QA**:
  - **[mode-specific check 1]**: Yes / No
  - **[mode-specific check 2]**: Yes / No
  - **Visual constraint limit**: Yes / No
```

Rules:

- `Visible Elements` contains only visible slide content and relationships. Do not put Intent, Key Takeaway, Editorial Notes, or AI Explanation there.
- Omit elements that do not exist; do not fill them with `N/A`.
- `Key Points` and `Speaker Note` serve the narrative but are not visible slide content.
- `Visual Constraints` describe hierarchy, emphasis, or layout limits and contain at most three items. They must not add content.
- `Visual Suggestion` may recommend a chart, image, or diagram but does not replace `Visible Elements`.

### 4.1 QA by mode

For **From-scratch**:

- `Narrative alignment`: visible elements and slide content support the narrative role.
- `Required elements present`: required content for the brief and slide role is present.
- `Visual constraint limit`: no more than three constraints.

For **Optimize**:

- `Content coverage`: existing-slide content is not omitted; for reports/long Markdown, important source content is not omitted.
- `Unauthorized additions`: no unsupported content is added; for existing slides, no source-absent content is added; for reports, no unsupported claim is added.
- `Visual constraint limit`: no more than three constraints.

A `No` result must be shown before approval. It does not automatically block approval. The user may request a revision or explicitly accept the exception. Handoff must include failed checks and whether the user accepted them.

## 5. Handoff

After Slide Plan approval, pass the complete plan to `interactive-presentation-generator`, including:

- All intake metadata
- `Visible Elements`
- `Visual Constraints`
- Source-of-truth conflicts
- Failed QA checks and any accepted exceptions
- `Speaker Note` as notes only, never as automatic visible content

The generator may skip its existing requirement-gathering and content-structure steps, but must preserve the source metadata, visual constraints, and disclosed QA gaps.

## 6. Validation

Validate the change through:

1. Specification review for mode boundaries, Research Checkpoint, stop condition, schema completeness, and generator compatibility.
2. `skill-auditor` review and correction of findings.
3. A From-scratch example covering narrative planning, planned visible elements, and mode-specific QA.
4. An Optimize example covering source-of-truth, source fidelity, conflicts, and per-slide QA.
5. At least one example with an evidence gap to confirm research stops when the evidence is sufficient rather than continuing indefinitely.

## 7. Out of scope

- Turning the referenced AI Native notes into a separate skill.
- Rewriting the generator's production workflow.
- Creating a new Presentation Source file format.
- Turning the planner into a PPT/PDF translation-only tool.
- Automatically writing research results to an external knowledge base.
- Adding an automated test framework; validation uses skill audit and practical examples.
