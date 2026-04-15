---
name: spec-gap-finder
description: >
  Analyze PM spec and UI wireframe from an RD perspective to find gaps, ambiguities, and undefined
  edge cases before implementation starts. Produces a structured pre-dev question list ready for
  a single alignment meeting with PM/Designer. Use when: (1) RD receives a new feature spec or
  wireframe and wants to identify unknowns before coding, (2) user says "review this spec",
  "find gaps in this wireframe", "what questions should I ask PM", "pre-dev review", or
  "spec gap finder", (3) user pastes or attaches a PM spec, PRD, wireframe, or design mockup
  and wants to know what's missing.
---

# Spec Gap Finder

Analyze PM spec + UI wireframe from an RD perspective. Produce a structured question list that catches what the spec/wireframe left undefined, so RD can align with PM/Designer in one meeting instead of five rounds of back-and-forth.

## Workflow

### 1. Collect Input

Accept one or more of:
- PM spec text (pasted, file, or Confluence URL via MCP)
- UI wireframe (screenshot image or Figma description)
- Existing Jira ticket description

If the user provides only one, ask: "Do you also have a [spec / wireframe]? Having both gives better coverage, but I can work with what you have."

### 2. Summarize Understanding

Before running the checklist, output a 3-5 bullet summary of what the feature does, to confirm you understood the spec correctly. Ask the user to confirm or correct.

### 3. Run Checklist

Read [references/checklist.md](references/checklist.md) and evaluate each of the 10 categories against the spec + wireframe:

1. Error States
2. Loading States
3. Empty States
4. Responsive / Mobile Behavior
5. Accessibility (a11y)
6. API Contract / Data Assumptions
7. Edge Cases
8. Copy / i18n
9. Animation / Transition Specs
10. Data Validation

For each category:
- If the spec/wireframe **clearly addresses** it: skip (do not list)
- If the spec/wireframe is **silent or ambiguous**: generate concrete, specific questions
- If the category **does not apply** to this feature: mark N/A with one-line reason

Do NOT generate generic questions. Every question must reference a specific element from the spec/wireframe.

Example — too vague: "What happens on error?"
Example — specific: "When the payment API returns 402, does the user see an inline error on the checkout form or a full-page error?"

### 4. Output Format

```markdown
# Pre-Dev Question List: [Feature Name]

> Spec reviewed: [source]
> Wireframe reviewed: [source]
> Generated: [date]

## Must Clarify Before Dev (Blocks Implementation)

### [Category Name]
- [ ] [Specific question referencing spec/wireframe element]
- [ ] [Specific question referencing spec/wireframe element]

## Nice to Clarify (Won't Block, But Reduces Rework)

### [Category Name]
- [ ] [Specific question]

## N/A Categories
- [Category]: [one-line reason]

---
_[X] questions across [Y] categories. Suggested action: schedule one 30-min alignment meeting._
```

### 5. Suggest Next Step

After outputting the question list:
- If < 5 questions: "This spec is pretty thorough. You could async these on Slack/Teams."
- If 5-15 questions: "Recommend a 30-min alignment meeting with PM + Designer."
- If > 15 questions: "This spec has significant gaps. Consider a working session before starting dev."

## Key Principles

- **RD perspective only** — ask what an implementer needs to know, not what a PM should have thought of
- **Specific over generic** — every question must reference a concrete UI element, flow, or data point from the spec
- **Prioritized** — separate "blocks dev" from "nice to have" so PM knows what to answer first
- **Actionable format** — checkboxes so PM/Designer can tick off answers during the meeting

## Examples

### Example 1: Mobile app feature with wireframe

```
User: "I got a spec for a new 'Add to Cart' feature and a Figma wireframe. Can you find the gaps?"
[pastes spec text + attaches wireframe screenshot]

spec-gap-finder output:
1. Summarizes feature understanding (5 bullets)
2. Runs 10-category checklist
3. Produces question list:
   - Must Clarify: 8 questions (error states for payment failure, empty cart behavior,
     loading state during price calculation, mobile swipe-to-delete interaction)
   - Nice to Clarify: 4 questions (animation on quantity change, i18n for currency format)
   - N/A: 1 category (Accessibility — already covered in spec's a11y section)
4. Suggests: "Recommend a 30-min alignment meeting with PM + Designer."
```

### Example 2: Confluence spec only, no wireframe

```
User: "Review this spec for gaps" [pastes Confluence page content]

spec-gap-finder output:
1. Asks: "Do you also have a wireframe or Figma link? Having both gives better coverage."
2. User: "Not yet, Designer is still working on it."
3. Proceeds with spec-only review, flags visual/interaction questions as
   "Pending wireframe — revisit when design is ready"
```

## Error Handling

- **Spec too vague to analyze**: If the input is less than 3 sentences or lacks any feature description, respond: "This spec doesn't have enough detail for a meaningful gap analysis. Can you provide more context about what the feature does?"
- **Unreadable wireframe**: If a screenshot is too small or blurry, ask the user to provide a higher-resolution image or describe the layout in text.
- **Ambiguous scope**: If the spec describes multiple independent features, ask the user to clarify which feature to review first, or offer to review them one at a time.

## Security Considerations

- **Input handling**: Spec content may contain sensitive business logic or unreleased feature details. Do not store or reference spec content beyond the current conversation.
- **File path safety**: When reading spec files from disk, validate the path exists before attempting to read. Do not follow symlinks outside the working directory.
- **No external transmission**: Do not send spec content to external APIs or services beyond what is needed for the current analysis.
