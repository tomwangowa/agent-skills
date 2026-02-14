# Design: presentation-planner

**Date**: 2026-02-15
**Status**: Approved

## Summary

Phase-gated presentation planning skill that transforms a topic or rough
outline into a complete Slide Plan, then auto-chains to
`interactive-presentation-generator`.

## Design Decisions

| Decision | Choice |
|----------|--------|
| Input mode | From-scratch + optimize existing, auto-switch |
| Output depth | Complete Slide Plan + auto-chain to generator |
| Research | Optional integration (suggest `critical-research`, don't force) |
| Narrative framework | Auto-select by context, user adjusts during review |
| Architecture | Phase-gated pipeline (Approach A) |

## Workflow

5 phases: Intake -> Audience Analysis & Framework Selection ->
Narrative Strategy & Outline -> Slide Plan -> Handoff

## Integration

- Upstream (optional): `critical-research`, `report-generator`
- Downstream: `interactive-presentation-generator`

## Out of Scope

- Visual design (generator's job)
- Rehearsal/practice features
- Multi-person collaboration
- Built-in research (delegates to `critical-research`)
