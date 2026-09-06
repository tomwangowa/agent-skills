# Diagnosis rubric — the 30 core features

The 30 narrative features that most reliably separate human from AI fiction (StoryScope Tables 13–15; scoring criteria adapted from its released taxonomy). Alone they detect AI at 84.8% macro-F1 — this checklist *is* the detector, run in reverse.

## Protocol

1. Score **one group at a time**, in five separate passes. Never assess the whole rubric in one read: models self-evaluating text collapse onto one or two salient dimensions and go blind to the rest (measured on the slop taxonomy — span precision 0.13 when given the full guide at once).
2. For each feature, quote the short passage that justifies the score. No quote, no score.
3. Apply the scoring rules below mechanically — no judgment calls about what counts as drift.
4. Scales are 1–5 unless a row notes otherwise. "Target" is the human mean.

## Scoring rules

| Case | Rule |
|---|---|
| Numeric rows (scale/ordinal) | **Drifted** when the story's score sits on the AI side of the midpoint between the Target and AI values. Example: thematic explicitness Target 3.3 / AI 3.9 → midpoint 3.6 → a story scoring 4 is drifted, 3.5 is not. |
| Percentage rows (categorical/binary) | **Drifted** when the story exhibits the AI-column option **and** AI% ÷ Target% ≥ 1.4. (The ratios are precomputed: every percentage row in groups A–C and E qualifies except *Subplots*, which is cumulative evidence only and never counts alone.) Absence of a human-leaning option is never drift by itself — most individual human stories also lack any given one. |
| Group D | Human-positive markers, scored as **one unit**: +1 drifted only if *none* of its three markers appears anywhere in the story; 0 otherwise. |
| Not applicable | A feature with no occasion in the text (no jeopardy → pre-threat investment; no reveal → recontextualization) scores **n/a** and leaves the assessable count. Reference explicitness is n/a only when the story makes no allusive gesture at all — an unnamed borrowed quotation or a recognizable unattributed retelling *is* an occasion (score it implicit). Short texts produce several n/a — that is expected, not a defect of the story. |
| Over-correction | A numeric score at the far extreme *away* from the AI direction (e.g. discontinuity 5/5, thematic explicitness 1/5) → flag as **over-correction advisory**. Report it (it is the humanizer-fingerprint failure mode) but don't count it in the drift share. |

**Triage:** assessable = 26 units maximum — 25 scored rows (groups A, B, C, E minus the two advisory rows *Subplots* and *Location variety*) plus 1 unit for group D — minus any n/a. Compute drift share = drifted ÷ assessable:

| Drift share | Action |
|---|---|
| ≥ 20% | Structural revision (Workflow B, all three passes) |
| 10–20% | Targeted fixes on the drifted features |
| < 10% | Style pass only |

## Group A — Thematic over-determination (AI drifts high)

| Feature | How to judge | Target | AI |
|---|---|---|---|
| Thematic explicitness | 1 = themes stay implicit; 5 = thesis-like statements tell the reader how to interpret events | ~3.3 | 3.9 |
| Moral/philosophical weighting | How far ethical debate and thematic exposition outweigh story pleasure; check narrator commentary and climactic speeches | ~3.3 | 3.7 |
| Thematic unity | 5 = every scene, subplot, image reinforces one thematic core | ~4.4 | 4.7 |
| Narrator thematic commentary | Does the narrating voice generalize about what events mean ("That is how people are")? | yes in ~52% | 77% |
| Dialogue as philosophical debate | Do key dialogues argue ideas rather than advance want/conflict? | dominant in ~34% | 59% |
| Reference explicitness | Vague unnamed allusion as the dominant intertext mode (the human-leaning state is a balanced mix of named + implicit, 37% vs 16%) | implicit-only ~50% | 72% |

## Group B — Sensory & embodied performativity (AI drifts high)

| Feature | How to judge | Target | AI |
|---|---|---|---|
| Dominant emotion mode | Classify strong-affect scenes: explicit label / embodied sensation / behavior / ambiguous; drifted when embodied dominates | embodied dominant in ~38% | 81% |
| Setting as psychological mirror | Do weather/landscape/architecture consistently externalize inner states? | ~3.6 | 4.1 |
| Environmental emphasis | Landscape and ecology beyond backdrop | ~2.8 | 3.2 |
| Olfactory imagery | Smell among regularly engaged senses — judge salience relative to length (one prominent instance counts in flash-length text; recurring use in longer work) | ~57% | 82% |
| Sensory density | Proportion of text doing multi-sense description; 5 = lush, pace-slowing | ~3.7 | 3.9 |
| Depth of interior access | 1 = external only; 5 = stream of consciousness | ~3.7 | 3.9 |

## Group C — Structural streamlining (AI drifts high/tidy)

| Feature | How to judge | Target | AI |
|---|---|---|---|
| Causal-chain continuity | 5 = every event tightly linked in one line from incitement to end | ~3.9 | 4.2 |
| Subplots *(advisory — cumulative evidence only)* | Absence of any subplot; too common in human stories (57%) to count alone | no-subplot ~57% | 79% |
| Resolution agency | Turning point triggered by protagonist choice vs chance/others | choice ~46% | 69% |
| Resolution mode | External act / internal acceptance / partial / open / catastrophic; drifted on internal acceptance | internal ~27% | 47% |
| Protagonist introduction | Device at first substantial appearance — one of: external description / in-action / in-dialogue / inner thought / others' reports. Drifted only on external description; the other four are never drift (in-dialogue is the strongest human marker) | description ~30% | 52% |
| Opening spatial grounding | How completely the first scene fixes local + global place (1–4) | ~2.1 | 2.3 |
| Spatial granularity | Density of place names, rooms, routes (1–4) | ~2.3 | 2.5 |
| Pre-threat investment | Interiority/backstory built before jeopardy | ~2.8 | 3.0 |

## Group D — Human-positive markers (one unit: +1 only if all three absent)

| Marker | How to judge | Human | AI |
|---|---|---|---|
| Named intertextuality | Any real text/author/work explicitly named | present in ~47% | 24% |
| Fourth-wall gesture | Any wink, aside, or reader acknowledgement anywhere | present in ~67% | 39% |
| Direct reader address | Any "you"/"dear reader" moment | present in ~28% | 7% |

## Group E — Temporal complexity & diversity (AI drifts low/tidy)

| Feature | How to judge | Target | AI |
|---|---|---|---|
| Chronological discontinuity | Frequency/sharpness of time jumps | ~2.4 | 2.1 |
| Anachrony intensity | Scene-level flashbacks/flash-forwards as structure | ~2.6 | 2.3 |
| Nonlinear framing for disclosure | Time devices used to stage revelations | ~2.0 | 1.7 |
| Recontextualization after surprise | How much earlier text a reveal recolors | ~3.3 | 3.0 |
| Location variety *(advisory — not counted)* | Flag when a 3,000+ word story never leaves one locale without the premise demanding confinement | 2+ full-scene locales common | single-location bias |
| Dialogue proportion | Fraction of text in quoted speech (1 = none, 3 = balanced, 5 = dominates) | ~3.0 | 2.7 |
| Moral polarity toward protagonist | Narrative's final stance; drifted when clearly affirmative or clearly condemning | ambivalent ~59% | clear 62% |

## Report format

Cite by quoting a short phrase, not by paragraph number:

```text
SEPIA DIAGNOSIS — <title>
Group A: 3 drifted, 1 n/a (narrator commentary — "It was then she learned…"; …)
Group B: 2 drifted (…)
Group C: 1 drifted, 1 n/a (…)
Group D: 0 (named intertextuality present — "…")
Group E: 2 drifted (…)
Advisories: over-correction none; subplots absent; single-location
Drift share: 8 / 24 assessable = 33% → structural revision
Plan: <ordered fixes, deepest layer first, each tied to a quoted passage>
```
