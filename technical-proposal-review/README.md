# technical-proposal-review

Purpose: review a technical wiki / RFC / enhancement proposal when the reviewer lacks project context.

## Boundary with existing skills

| Need | Skill |
|---|---|
| I don't know this project; help me understand a proposal before reviewing it | `technical-proposal-review` |
| I understand the feature; find implementation gaps in PM spec/wireframe | `spec-gap-finder` |
| Verify documentation against source code | `codebase-audit` |
| Determine whether technology X can satisfy requirement Y | `tech-feasibility` |
| Produce a new technical design | `role-rd` |

## Recommended router disambiguation

If both `technical-proposal-review` and `spec-gap-finder` match, ask:

> **你現在最需要的是哪一種？**
> 1. 我對專案不熟，需要先看懂 technical proposal 再 review → `technical-proposal-review`
> 2. 我已經理解功能，要找 spec / wireframe 開發前的缺口 → `spec-gap-finder`

## Installation

1. Copy this folder to your skills directory as `technical-proposal-review/`.
2. Register the skill in `skill-router/skill-registry.yaml` under `categories.dev-process.skills`
   (entry already present in this repository's registry).
3. Add the skill to `skills-catalog.json` (category `design-planning`), then run
   `python3 scripts/validate_skills_catalog.py --write` and commit the regenerated `SKILLS_CATALOG.md`.
