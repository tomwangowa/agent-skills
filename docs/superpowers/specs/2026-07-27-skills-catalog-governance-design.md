# Skills Catalog Governance Design

**Status:** Approved design, pending implementation

## Goal

Make `/Users/tom_wang/.claude/skills` a maintainable, cross-agent source of truth without moving its existing flat skill directories or changing runtime invocation behaviour.

The repository will gain one machine-readable catalog, deterministic validation, and a generated index. The catalog owns governance metadata; each `SKILL.md` remains the source of its operational instructions.

## Non-goals

- Do not move skills into bucket directories.
- Do not change `disable-model-invocation`, `agents/openai.yaml`, or any runtime routing behaviour in this change.
- Do not run a real `skill-sync` write or modify target agent directories.
- Do not include untracked `ONBOARDING.md` or `team-onboarding/` in the inventory.
- Do not convert this repository into a Claude or Codex plugin package.

## Catalog

Add a root-level `skills-catalog.json` with `schema_version: 1` and one entry for every tracked, top-level directory containing `SKILL.md`.

```json
{
  "schema_version": 1,
  "skills": [
    {
      "id": "brainstorming",
      "category": "design-planning",
      "lifecycle": "promoted",
      "invocation_intent": "model",
      "surfaces": {
        "routable": true,
        "listed_in_readme": true,
        "sync": true
      }
    }
  ]
}
```

### Field contract

| Field | Allowed values | Meaning |
|---|---|---|
| `id` | a tracked top-level skill directory name | Stable skill identity and path anchor. |
| `category` | `quality-gates`, `research-critical-thinking`, `multi-agent-roles`, `design-planning`, `content-generation`, `productivity-tracking`, `tools-meta` | Human-facing organisation reused by the generated index. |
| `lifecycle` | `promoted`, `experimental`, `personal` | Maturity and promotion policy, independent of discovery or sync. |
| `invocation_intent` | `model`, `user` | Desired future invocation policy. Informational in this change. |
| `surfaces.routable` | boolean | Whether the local skill must have exactly one entry in `skill-router/skill-registry.yaml`. |
| `surfaces.listed_in_readme` | boolean | Whether the skill appears in the concise Core Skills section of both root READMEs. |
| `surfaces.sync` | boolean | Whether the source-to-target mirror is allowed to copy this skill. |

`global/`, `docs/`, `skills-query-server/`, hidden directories, and untracked paths are supporting infrastructure, not catalog skills. External router identifiers such as `superpowers:*` remain outside the catalog.

## Validation and rendering

Add `scripts/validate_skills_catalog.py`, implemented with Python's standard library plus Git. The script has two explicit modes:

```bash
python3 scripts/validate_skills_catalog.py --check
python3 scripts/validate_skills_catalog.py --write
```

`--check` is read-only and fails on any of the following:

1. Invalid JSON, unsupported schema version, invalid enum, duplicate id, or missing required field.
2. A tracked top-level `SKILL.md` directory missing from the catalog, or a catalog id with no such tracked directory.
3. A `routable: true` local id missing from the registry, an id listed more than once, or a `routable: false` local id still present there. `superpowers:*` references are exempt.
4. A `listed_in_readme: true` skill without an explicit link from both root READMEs' Core Skills section.
5. A `sync: false` skill not protected by an exact top-level entry in `.skill-sync-ignore`, or a `sync: true` skill excluded by one.
6. A stale generated `SKILLS_CATALOG.md`.

`--write` renders only `SKILLS_CATALOG.md`. It never rewrites the catalog, router, README, or any `SKILL.md`. The generated index is sorted by category then id and contains metadata plus links to each `SKILL.md`; it intentionally does not copy descriptions from skill frontmatter.

## Documentation and router boundaries

`SKILLS_CATALOG.md` is the complete machine-derived inventory. `README.md` and `README.zh.md` remain landing pages: retain their principles, installation, and high-level workflow explanation; remove fragile total-skill claims and hand-maintained full inventories; add a concise Core Skills section and a link to the generated index.

`SKILLS_ROADMAP.md` remains a planning/history document, not an inventory. Its current implementation totals will be removed or labelled historical so they cannot contradict the catalog.

`skill-router/skill-registry.yaml` continues to own natural-language triggers, routing explanations, external tool references, and workflow definitions. The catalog owns only the yes/no policy that a local skill must be represented there. This avoids flattening router semantics into JSON while still detecting stale or omitted local entries.

## Safe sync preview

Add a `--dry-run` option to `skill-sync/scripts/sync.sh`. Unlike the script's existing preview phase, this option is a true read-only operation:

- It reads the same target and ignore configuration as normal sync.
- It never calls `mkdir -p`, prompts for confirmation, or invokes a real `rsync` copy.
- For an existing target, it runs only `rsync --dry-run` and reports the filtered preview.
- For a missing target, it reports that the target was skipped and does not create it.
- It can be combined with `--no-delete` to preview additive mode; default preview uses mirror-mode deletion semantics.

The existing no-argument and `--no-delete` paths keep their current behaviour. Update `skill-sync/SKILL.md`, its README references, and root README descriptions so users can distinguish the safe preview from the interactive mirror flow.

## Classification approval gate

Before writing `skills-catalog.json`, inventory all tracked top-level skills and present a proposed table of category, lifecycle, invocation intent, and surfaces. The user approves or changes that table as a whole. The untracked `team-onboarding/` directory is excluded from this review.

Initial lifecycle definitions:

- `promoted`: maintained and intentionally discoverable; it has a defined README and/or router surface.
- `experimental`: usable local work that is not yet promoted as a stable default.
- `personal`: Tom-specific workflow or context; it may still be routed or synced when its surface flags say so.

## Delivery plan

1. Produce the read-only classification proposal and wait for approval.
2. Add the approved catalog and validation/rendering script.
3. Generate `SKILLS_CATALOG.md`, update both root READMEs, reconcile the registry, and clarify the roadmap's historical status.
4. Run `--write`, then `--check`, JSON parsing, catalog/router/README/sync-contract checks, and `skill-sync --dry-run` only.
5. Run `skill-auditor` for the modified `skill-router` skill, then `code-review-codex` before proposing a commit. Ask for explicit commit approval.

## Acceptance criteria

- Every tracked top-level skill directory is represented once in `skills-catalog.json`; no untracked or infrastructure directory is represented.
- `python3 scripts/validate_skills_catalog.py --check` exits successfully in the feature worktree.
- Re-running `--write` produces no subsequent diff in `SKILLS_CATALOG.md`.
- Both root READMEs link to the generated catalog and contain no authoritative total-skill claim.
- Router and `.skill-sync-ignore` relationships match the approved catalog flags.
- `bash skill-sync/scripts/sync.sh --dry-run` does not create a missing configured target and does not prompt for confirmation.
- No runtime invocation metadata, target sync state, or untracked source-worktree content changes.

## Risks and mitigations

| Risk | Mitigation |
|---|---|
| A contributor edits catalog data but forgets to regenerate the index. | `--check` treats stale generated output as a failure. |
| A broad ignore pattern makes `sync` contract checks ambiguous. | Only exact top-level skill entries participate in the catalog sync contract; general infrastructure ignores remain outside it. |
| Router trigger text becomes duplicated in catalog. | Keep triggers exclusively in `skill-registry.yaml`; catalog stores only the routing policy. |
| Governance refactor accidentally changes agent behaviour. | Treat `invocation_intent` as informational and do not touch runtime invocation metadata. |
