# Model Invocation Policy for Routing and Work Logs

- **Date:** 2026-08-18
- **Status:** Design approved in conversation; not committed

## Problem

`work-log-analyzer` and `skill-router` are currently marked as user-only in Claude metadata, Codex policy metadata, and the local skills catalog. This prevents the agent from invoking them when the task clearly needs work-log analysis or skill discovery. `activity-logger` already permits model invocation and is not part of the change.

## Decision

Adopt the smallest consistent policy change:

- Make `work-log-analyzer` model-invokable.
- Make `skill-router` model-invokable.
- Keep `skill-router` non-routable so it cannot recommend itself.
- Keep manual confirmation for downstream skills that remain user-only.
- Leave `activity-logger` unchanged.

Model invocation and routing eligibility remain separate dimensions. A skill may be model-invokable without being a router candidate; `skill-router` is the intentional example.

## Scope

### `work-log-analyzer`

- Remove `disable-model-invocation: true` from its Claude skill metadata.
- Remove `policy.allow_implicit_invocation: false` from its Codex metadata.
- Change its catalog `invocation_intent` from `user` to `model`.
- Preserve its read-only behavior, preferred `mcp__skills-query__*` tools, shell fallback, and query scope.

### `skill-router`

- Remove its Claude and Codex user-only gates.
- Change its catalog `invocation_intent` from `user` to `model`.
- Keep `surfaces.routable: false`.
- Revise the skill contract so it says:
  - the router may be invoked by the agent to select an appropriate skill or workflow;
  - routing a request does not grant permission to execute a downstream user-only skill;
  - model-invokable downstream skills may continue through the existing routing flow;
  - user-only downstream skills must remain at a manual checkpoint until the user explicitly invokes `$skill-name` or `/skill-name`.
- Do not add an internal/manual dual-mode protocol or change the workflow registry.

### `activity-logger`

No changes. Its skill metadata and catalog already declare model invocation, and its recording behavior remains unchanged.

## Component Boundaries

1. **Skill metadata** answers whether the active agent may invoke a skill.
2. **Catalog policy** records lifecycle, invocation intent, and routing eligibility for validation and discovery.
3. **Router behavior** selects a skill or workflow and enforces the downstream invocation boundary.

The validator invariants remain:

- user-only skills retain both Claude and Codex hard gates;
- model skills do not retain either user-only hard gate;
- `skill-router` must not be routable;
- source skill files and the Codex runtime copies stay synchronized.

## Validation

Run, in order:

```text
python3 scripts/validate_skills_catalog.py --check
python3 -m unittest tests/test_validate_skills_catalog.py
```

Then run `skill-auditor` because skill definitions change. Check source/Codex hashes and inspect the final diff to verify that `activity-logger` was untouched and that the downstream manual checkpoint is still present. A static hash match is not treated as proof of fresh runtime behavior; any runtime smoke limitation must be reported explicitly.

If validation fails, fix the relevant metadata, catalog, or documentation inconsistency and rerun the failed check. Do not weaken the general user-only validation rule merely to accommodate these two model-invokable skills.

## Out of Scope

- Core work-log queries and read-only behavior.
- Activity recording behavior.
- Making `skill-router` routable or self-recommending.
- Removing manual confirmation for other user-only skills.
- Adding a dual-mode router protocol.
- Wholesale skill synchronization.
- Commit or push.
