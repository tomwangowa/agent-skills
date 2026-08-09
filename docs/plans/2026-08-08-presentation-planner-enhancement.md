# Presentation Planner Enhancement Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Extend `presentation-planner` with source-aware metadata, a bounded Research Checkpoint, richer per-slide planning fields, mode-specific QA, and explicit handoff context without changing its narrative-planning role.

**Architecture:** Keep the existing single-file, stage-gated pure-instruction skill. Update the workflow in place: classify input and source-of-truth during Intake, run a bounded research checkpoint before narrative design, then emit one common Slide Plan shape whose QA semantics vary by input mode. Keep generator production unchanged; document the additional handoff payload in `presentation-planner` only.

**Tech Stack:** Markdown skill instructions, existing Claude Code skill conventions, `skill-auditor` shell audit, manual scenario validation.

---

## File map

- **Modify:** `presentation-planner/SKILL.md`
  - Preserve frontmatter, trigger rules, narrative frameworks, existing save/handoff behavior, security guidance, and warm-tone guidance.
  - Update workflow stages and intake rules.
  - Add source metadata and conflict handling.
  - Add Research Checkpoint and stop condition.
  - Extend the Slide Plan template with `Visible Elements`, `Visual Constraints`, and mode-specific QA.
  - Clarify Optimize behavior for slides versus reports/long Markdown.
  - Carry QA gaps and source conflicts into generator handoff.
  - Add at least one From-scratch and one Optimize example that exercise the new fields.
- **Create:** `docs/plans/2026-08-08-presentation-planner-enhancement.md` (this plan only; no runtime code or automated test fixture is required by the approved design).
- **Read-only validation targets:** `interactive-presentation-generator/SKILL.md`, `skill-auditor/scripts/audit_skill.sh`, and `completion-gate/SKILL.md`.

## Validation strategy

This is a pure-instruction skill, so there is no executable unit-test suite to add. Verification must prove the instruction contract instead:

1. Search and inspect the final skill for every approved design requirement.
2. Run the skill auditor against `presentation-planner`.
3. Manually simulate one From-scratch prompt and one Optimize prompt, including an evidence gap and a source conflict, and compare the expected stage behavior and output fields against the skill text.
4. Check the handoff wording against `interactive-presentation-generator` so the planner skips only the already-covered generator steps and does not claim to change generator production.
5. Run the completion gate before reporting the implementation as complete.

---

### Task 1: Capture a baseline and map the existing workflow

**Files:**
- Read: `presentation-planner/SKILL.md`
- Read: `interactive-presentation-generator/SKILL.md`
- Read: `skill-auditor/scripts/audit_skill.sh`

- [x] **Step 1: Run the existing skill audit before editing**

Run:

```bash
bash "$PWD/skill-auditor/scripts/audit_skill.sh" "$PWD/presentation-planner"
```

Expected: the auditor completes and prints the current archetype, score, and findings. Save the output mentally for comparison; do not edit the skill in this step.

- [x] **Step 2: Record the edit boundaries**

Confirm that the implementation will touch only `presentation-planner/SKILL.md`. Do not modify `interactive-presentation-generator/SKILL.md`; the approved scope explicitly keeps generator production unchanged.

- [x] **Step 3: Check the baseline working tree**

Run:

```bash
git status --short
```

Expected: only the already-created design/plan documentation appears as uncommitted work; do not overwrite unrelated changes.

---

### Task 2: Update Intake and input-mode semantics

**Files:**
- Modify: `presentation-planner/SKILL.md` in `## Workflow`, `### Stage 1: Intake`, and adjacent constraints/error-handling text

- [x] **Step 1: Replace the original workflow list with the approved seven-stage flow**

Make the workflow read as:

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

Keep the existing stage-gated behavior and explicit approval requirement.

- [x] **Step 2: Add Intake metadata requirements**

Immediately after input-mode detection, require every plan to record:

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

Define the values as follows:

- `From-scratch` covers a topic, brief, or rough direction.
- `Optimize` covers an existing outline, PPT, PDF, Markdown file, or report.
- `Outline` means an existing outline supplied for optimization; it is distinct
  from a From-scratch rough direction or brief.
- If multiple sources exist, ask which one is the source of truth before planning when the answer is not already explicit.
- Do not infer the winner from file dates, memory, completeness, or model preference.

- [x] **Step 3: Add conflict handling**

State that when the source of truth conflicts with supporting material, the planner must use the declared source, record the conflict and its location, and avoid silently merging the versions. A single conflict does not stop the whole plan; an unresolved primary-source choice does stop Intake until clarified.

- [x] **Step 4: Define Optimize source semantics**

Add explicit rules:

- Existing outlines (`Source Type: Outline`) are Optimize inputs whose supplied
  structure is analyzed and improved; they are not reclassified as
  From-scratch unless the outline is too unstructured, in which case the
  canonical metadata must be reclassified as `From-scratch` with `Brief` or
  `Topic`.
- Existing slides: `Visible Elements` records what the source actually contains.
- Reports/long Markdown: `Visible Elements` records planned elements derived from the source and must not claim that the source already had that layout.
- Source speaker notes remain spoken supplements and do not enter `Visible Elements` unless the user explicitly asks for that.

- [x] **Step 5: Preserve the existing intake questions and Optimize shortcut**

Keep purpose, audience, duration, constraints, visual assets, and footer settings as one-at-a-time questions. For Optimize mode, read the supplied material first and ask only for missing decisions, adding source-of-truth clarification when needed. Resolve Cover Image, Ending Image, Logo, Company Name, Author Name, Custom Footer Text, and Footer Enabled to an explicit value, documented generator default, or explicit none/not applicable before claiming the generator's Step 1 can be skipped.

- [x] **Step 6: Add a regression check for the intake rules**

Run:

```bash
grep -n -E "Input Mode|Source Type|Source of Truth|From-scratch|Optimize|source of truth|Speaker Note" presentation-planner/SKILL.md
```

Expected: all intake metadata, including visual-asset/footer fields and source-boundary terms, appear in the Stage 1 Intake section and canonical schema rather than only in an example template.

---

### Task 3: Add the bounded Research Checkpoint

**Files:**
- Modify: `presentation-planner/SKILL.md` between the existing Stage 2 framework-selection stage and Stage 4 narrative-strategy stage
- Modify: `presentation-planner/SKILL.md` in `### Stage 4: Narrative Strategy & Outline` so the old evidence-gap behavior points to the checkpoint

- [x] **Step 1: Insert a dedicated Research Checkpoint stage**

Add a stage after Audience Analysis & Framework Selection and before Narrative Strategy with this behavior:

1. Identify evidence gaps affecting the Core Message or Supporting Messages.
2. Identify source conflicts and claims that remain unverified.
3. Offer `critical-research` when a gap affects the narrative or slide content.
4. Stop once the Core Message and each major Supporting Message have enough evidence or an explicit source.
5. Lock the research context before entering production.

- [x] **Step 2: Define the stop condition in measurable language**

State that “enough” means the evidence can support the presentation’s Core Message and each major Supporting Message; exhaustive background research is not required. Preserve unresolved gaps in the Slide Plan instead of inventing facts.

- [x] **Step 3: Define the production boundary**

After the checkpoint:

- Do not silently restart research.
- Do not rename locked concepts or change source-of-truth content.
- Perform consistency checks only while producing the narrative and Slide Plan.
- If new evidence would change the core narrative or source decision, pause handoff and explicitly return to the Research Checkpoint.

- [x] **Step 4: Reconcile the existing “material is insufficient” branch**

Change the existing Stage 4 wording so it no longer launches an unbounded research discussion during outline generation. It should point to the Research Checkpoint, preserve the gap in the plan if research is declined or inconclusive, and continue only with an explicit gap note.

- [x] **Step 5: Verify stage order and stop-condition wording**

Run:

```bash
grep -n -E "Research Checkpoint|enough evidence|Stop condition|production|restart research|critical-research" presentation-planner/SKILL.md
```

Expected: the checkpoint appears before Narrative Strategy, and no later stage instructs the planner to begin open-ended research.

---

### Task 4: Extend the Slide Plan schema and mode-specific QA

**Files:**
- Modify: `presentation-planner/SKILL.md` in `### Stage 5: Slide Plan + QA`, the slide template, slide-count guidance, and constraints/red-flags sections

- [x] **Step 1: Add the common per-slide fields**

Extend the existing slide template with:

```markdown
- **Visible Elements**:
  - **Title**: [visible title]
  - **Body**: [visible text or key content]
  - **Flow**: [relationship, if present]
  - **Comparison**: [comparison, if present]
  - **Table**: [table content, if present]
  - **Diagram**: [diagram relationship, if present]
  - **Callout**: [visible callout, if present]
- **Visual Constraints**:
  - [constraint 1]
  - [constraint 2]
- **QA**:
  - **[mode-specific check 1]**: Yes / No
  - **[mode-specific check 2]**: Yes / No
  - **Visual constraint limit**: Yes / No
```

Keep `Title`, `Subtitle`, `Key Points`, `Speaker Note`, and `Visual Suggestion` as existing narrative fields.

- [x] **Step 2: Add field semantics and omission rules**

Document that:

- `Visible Elements` contains only visible slide content and relationships.
- Do not put `Intent`, `Key Takeaway`, `Editorial Notes`, or `AI Explanation` in `Visible Elements`.
- Omit absent element types rather than writing `N/A`.
- `Key Points` and `Speaker Note` are narrative/spoken supplements, not visible slide content.
- `Visual Suggestion` may recommend a chart, image, or diagram but cannot replace visible content.
- `Visual Constraints` describe hierarchy, emphasis, or layout limits, contain at most three items, and must not add content.

- [x] **Step 3: Define From-scratch QA**

Require these three checks for From-scratch slides:

- `Narrative alignment`: visible elements and slide content support the slide’s narrative role.
- `Required elements present`: required content for the brief and slide role is present.
- `Visual constraint limit`: no more than three constraints.

- [x] **Step 4: Define Optimize QA by source type**

Require these three checks for Optimize slides:

- `Content coverage`: existing-slide content is not omitted; reports/long Markdown retain important source content.
- `Unauthorized additions`: existing slides gain no source-absent content; reports gain no unsupported claims.
- `Visual constraint limit`: no more than three constraints.

- [x] **Step 5: Define non-blocking disclosure behavior**

State that every `No` result must be visible before approval, does not automatically block approval, and may be corrected or explicitly accepted by the user. Require accepted exceptions and failed checks to be carried into handoff.

- [x] **Step 6: Update red flags and constraints**

Add red flags for:

- Slide plans without `Input Mode`, `Source Type`, or `Source of Truth`.
- Visible Elements that contain intent or speaker interpretation.
- More than three Visual Constraints.
- Optimize plans that hide failed QA checks.
- Research restarting after the checkpoint without an explicit return.

Keep the existing slide-count guidelines and the existing explicit Slide Plan approval gate.

- [x] **Step 7: Verify schema completeness**

Run:

```bash
grep -n -E "Visible Elements|Visual Constraints|Narrative alignment|Required elements present|Content coverage|Unauthorized additions|Visual constraint limit|No result|accepted" presentation-planner/SKILL.md
```

Expected: each approved field and QA behavior appears in the actual workflow/template, not only in an example.

---

### Task 5: Update handoff and examples without changing the generator

**Files:**
- Modify: `presentation-planner/SKILL.md` in `### Stage 7: Generator Handoff`, `### Example 1`, `### Example 2`, `### Example 3`, and related constraints
- Read-only comparison: `interactive-presentation-generator/SKILL.md`

- [x] **Step 1: Expand handoff payload**

After Slide Plan approval, require the planner to pass the complete plan plus:

- `Input Mode`, `Source Type`, and `Source of Truth`.
- `Cover Image`, `Ending Image`, `Logo`, `Company Name`, `Author Name`, `Custom Footer Text`, and `Footer Enabled`, each resolved to an explicit selection, documented generator default, or explicit `none` / not applicable value.
- `Visible Elements` and `Visual Constraints`.
- Source-of-truth conflicts.
- Failed QA checks and whether the user accepted them.
- `Speaker Note` as notes only, never as automatic visible content.

Keep the existing optimization that lets the generator skip its own requirements and content-structure steps, but explicitly state that this does not rewrite the generator’s production workflow.

- [x] **Step 2: Add a From-scratch example**

Extend the technical-talk example so it shows:

- `Input Mode: From-scratch` and `Source Type: Topic`.
- A Research Checkpoint that finds enough benchmark evidence and stops.
- One slide with planned `Visible Elements`, at most three `Visual Constraints`, and the three From-scratch QA labels.
- A separate `Speaker Note` that is not copied into visible content.

- [x] **Step 3: Add an Optimize example with a source conflict**

Extend the existing outline/report examples with:

- `Input Mode: Optimize` and a concrete `Source Type`.
- An explicit `Source of Truth`.
- A conflict with an older outline or translation that is recorded rather than silently merged.
- One slide showing Optimize QA, including a disclosed `No` result that remains user-reviewable.
- A report/long-Markdown note that elements are planned rather than extracted from an existing slide.

- [x] **Step 4: Add an evidence-gap example or branch**

Ensure at least one example says that an inconclusive or declined `critical-research` result is preserved as a gap in the Slide Plan and does not trigger indefinite research.

- [x] **Step 5: Compare handoff wording with the generator contract**

Read the generator’s workflow and verify that the planner only claims to skip Step 1 and Step 4 after supplying their inputs. Do not add new generator fields or modify its file.

- [x] **Step 6: Check the examples are not contradictory**

Run:

```bash
grep -n -E "Example|Input Mode|Source Type|Source of Truth|Research Checkpoint|Speaker Note|Visible Elements|QA" presentation-planner/SKILL.md
```

Expected: both modes and the evidence-gap behavior are demonstrated, and examples use the same field names as the canonical template.

---

### Task 6: Run skill audit and fix findings

**Files:**
- Modify: `presentation-planner/SKILL.md` only if the audit identifies a concrete issue

- [x] **Step 1: Run the automated audit**

Run:

```bash
bash "$PWD/skill-auditor/scripts/audit_skill.sh" "$PWD/presentation-planner"
```

Expected: the audit completes without a shell error and prints a report for the pure-instruction skill.

Evidence (2026-08-08): exit 0; archetype `pure-instruction`; score `81/100`; Critical `0`, Important `2`, Suggestions `1`; report says production-ready. Reported Important findings were ambiguous terms (`appropriate`, `good`, `bad`) and the description opening; the Suggestion was the 773-line reference split. None is a concrete approved-design, portability, trigger, or handoff defect.

- [x] **Step 2: Review each finding against the approved scope**

For each finding, classify it as:

- Must fix: contradicts the approved design, creates an ambiguous workflow, leaks personal paths/secrets, or breaks an existing trigger/handoff.
- Optional: a style suggestion that does not affect the design or portability.

Do not add unrelated features just to increase the score.

Evidence (2026-08-08): all three findings classified Optional. No SKILL.md edit was made for audit-score improvement.

- [x] **Step 3: Fix concrete findings inline**

For every must-fix finding, edit the exact section that caused it, preserving the single-skill scope. Re-run the audit after each logical group of fixes.

Evidence (2026-08-08): no must-fix findings; no inline correction required.

- [x] **Step 4: Confirm no personal path leaked from the reference note**

Run:

```bash
grep -n -E "/Users/|/home/|[A-Za-z]:\\\\" presentation-planner/SKILL.md || true
```

Expected: no user-specific absolute paths are present in the skill.

Evidence (2026-08-08): grep produced no matches.

---

### Task 7: Perform practical scenario validation

**Files:**
- Read: `presentation-planner/SKILL.md`
- Read: `docs/specs/2026-08-08-presentation-planner-enhancement-design.md`

No new fixture file is needed; record results in the implementation report or final response.

- [x] **Step 1: Validate the From-scratch scenario**

Use this prompt mentally or in a fresh skill invocation:

```text
Help me plan a 15-minute educational talk on WebAssembly for backend developers. I have only this topic and no source document.
```

Expected behavior:

1. Classify as `From-scratch` / `Topic`.
2. Ask purpose, audience, duration, and constraints one at a time as needed.
3. Produce audience analysis and auto-select a framework.
4. Run the Research Checkpoint before narrative strategy; stop when evidence supports the Core Message and major Supporting Messages.
5. Produce `Visible Elements`, `Visual Constraints` (maximum three), separate `Speaker Note`, and From-scratch QA labels.
6. Require explicit Slide Plan approval before handoff.

Evidence (2026-08-08, manual/document inspection only): the skill explicitly maps topic-only input to `From-scratch`/`Topic`, preserves one-question intake, requires audience/framework analysis, places the checkpoint before narrative strategy, specifies the three visible fields and QA labels, and gates handoff on approval. No model invocation was run.

- [x] **Step 2: Validate the Optimize scenario**

Use this prompt mentally or in a fresh skill invocation:

```text
Improve this quarterly review report into a 15-minute leadership presentation. The current report is the source of truth; an older outline is reference only. The report contains milestones and metrics but no slide layout.
```

Expected behavior:

1. Classify as `Optimize` / `Report`.
2. Record the report as `Source of Truth` and treat the older outline as supporting material.
3. Mark `Visible Elements` as planned elements derived from the report, not extracted existing layout.
4. Use Optimize QA semantics: coverage, unauthorized additions, and constraint limit.
5. Record any conflict with the older outline and expose any `No` checks before approval.
6. Do not automatically stop approval solely because a QA item is `No`.

Evidence (2026-08-08, manual/document inspection only): Example 2 and the Optimize source semantics cover declared source of truth, older-outline conflict recording, planned report elements, Optimize QA, and non-blocking disclosed `No` results. No model invocation was run.

- [x] **Step 3: Validate an evidence-gap branch**

Use this prompt mentally:

```text
Plan a talk from a short brief, but one supporting claim has no reliable evidence. I do not want to spend the whole session researching it.
```

Expected behavior: offer `critical-research`, stop once the remaining gap no longer changes the core narrative or explicitly preserve the unresolved gap if research is declined/inconclusive; never continue research indefinitely.

Evidence (2026-08-08, manual/document inspection only): Stage 3 bounds targeted research, defines explicit acceptance for declined/unavailable/inconclusive results, preserves the gap and evidence status, and requires explicit return to Stage 3 for material changes. Example 3 exercises the branch. No model or research-provider execution was run.

- [x] **Step 4: Validate the handoff contract**

Confirm the handoff text carries metadata, visible elements, visual constraints, source conflicts, failed QA, accepted exceptions, and speaker-note separation while still allowing the generator to skip only its already-supplied requirements/content-structure work.

Evidence (2026-08-08, document inspection): Stage 7 requires the complete approved plan, intake metadata, generator Step 1 visual/footer resolutions, visible elements, visual constraints, locked gap context, conflicts, failed QA records, and speaker-note separation; it permits skipping only Steps 1 and 4 and leaves Steps 2, 3, 5, 6, and 7 unchanged. Generator diff is empty.

- [x] **Step 5: Record uncovered limitations**

Document that these manual scenarios do not execute an actual model conversation, do not test `critical-research` availability, and do not prove behavior on every possible source format. Keep these limitations in the final `NOT VERIFIED` section.

Evidence (2026-08-08): limitations recorded in the final validation report and below in Task 8.

---

### Task 8: Final requirements review and completion verification

**Files:**
- Read: `docs/specs/2026-08-08-presentation-planner-enhancement-design.md`
- Read: `presentation-planner/SKILL.md`
- Read: `docs/plans/2026-08-08-presentation-planner-enhancement.md`

- [x] **Step 1: Run a spec-to-skill checklist**

Check each approved requirement explicitly:

- Existing narrative purpose preserved.
- Seven-stage workflow present.
- Input metadata present.
- Source-of-truth conflict behavior present.
- From-scratch/Optimize semantics present, including `Outline` as an Optimize
  `Source Type` and its distinction from a From-scratch rough direction.
- Speaker Note boundary present.
- Research Checkpoint and stop condition present.
- Production boundary present.
- Common Slide Plan fields present.
- Mode-specific QA present.
- Non-blocking QA disclosure present.
- Handoff payload present.
- Two practical examples and an evidence-gap path present.
- AI Native notes are not introduced as a new skill.
- Generator file remains unmodified.

Evidence (2026-08-08): static grep/checklist and direct document inspection verified every item, including `Outline` semantics. Generator diff is empty. The handoff review also confirmed Step 1 visual/footer resolutions are preserved, as required by the generator contract.

- [x] **Step 2: Check the diff scope**

Run:

```bash
git diff --stat && git status --short
```

Expected: implementation changes are limited to `presentation-planner/SKILL.md` plus the approved design/spec and plan files; no generator or unrelated skill files changed.

Evidence (2026-08-08, historical snapshot before the later docs path migration): tracked diff names were the approved spec and `presentation-planner/SKILL.md`; the plan was the only untracked file. `interactive-presentation-generator/SKILL.md` had no diff. `git diff --stat` reported 2 tracked files: 426 insertions and 61 deletions. This snapshot does not describe the current Git index.

- [x] **Step 3: Re-run the final audit**

Run:

```bash
bash "$PWD/skill-auditor/scripts/audit_skill.sh" "$PWD/presentation-planner"
```

Expected: the final audit completes successfully. Report its actual score/findings; do not claim a clean audit unless the output proves it.

Evidence (2026-08-08): exit 0; score `81/100`; Critical `0`, Important `2`, Suggestions `1`; audit completed and reported production-ready. It is not a clean zero-finding audit.

- [x] **Step 4: Apply completion-gate discipline before reporting**

Before any completion statement, list at least three assumptions and attack them:

- The planner is consumed as prompt instructions rather than by a strict parser; counter-scenario: a downstream tool expects exact fields, mitigated by retaining the canonical Markdown field names.
- Users identify a source of truth when asked; counter-scenario: they provide multiple files without priority, mitigated by the explicit Intake clarification gate.
- Research can stop once evidence supports the narrative; counter-scenario: later evidence changes the core claim, mitigated by the explicit return-to-checkpoint rule.

Evidence (2026-08-08): these assumptions and counter-scenarios were reviewed against the Intake, Context Lock, and Stage 7 handoff text. `git diff --check` returned exit 0.

Then report:

```markdown
VERIFIED:
- [actual audit command and result]
- [actual spec-to-skill checklist result]
- [actual diff-scope result]
- [scenario checks actually performed]

NOT VERIFIED:
- [model conversation behavior not executed, if applicable]
- [critical-research availability/inconclusive provider behavior, if not run]
- [platforms or source formats not exercised]
```

- [ ] **Step 5: Stop before committing implementation changes**

The user must explicitly approve any implementation commit. Do not commit or push as part of this plan without that approval and the required native code-review pass if the repository workflow treats the Markdown change as a reviewable skill change.
