# User-only skill invocation design

## Status

Approved design. Implementation has not started.

## Problem

`skills-catalog.json` records `invocation_intent`, but the current value
`user` is metadata only. It neither prevents Claude Code or Codex from
implicitly invoking a skill nor consistently describes router behavior.

Tom's policy is explicit:

> `invocation_intent: user` means only the user may explicitly invoke the
> skill.

At the same time, user-only skills must remain discoverable through
`$skill-router`, because hiding them makes useful capabilities easy to forget.

## Definitions

### `invocation_intent`

- `model`: the runtime may invoke the skill implicitly.
- `user`: the runtime must not invoke the skill implicitly. The user starts it
  with `$skill-name` or `/skill-name`.

### `routable`

`routable` means that `skill-router` may discover and recommend a skill for a
matching user need. It does not grant permission to execute the skill.

Every user-only skill except `skill-router` itself is routable. `skill-router`
is the resolver, so it remains outside its own registry to avoid self-
recommendation while still being available through direct invocation and list
mode.

## Runtime behavior

### Claude Code

Every user-only `SKILL.md` includes:

```yaml
disable-model-invocation: true
```

This leaves explicit `/skill-name` invocation available while preventing
implicit model invocation.

### Codex

Every user-only skill has `agents/openai.yaml` containing:

```yaml
policy:
  allow_implicit_invocation: false
```

This keeps `$skill-name` available to the user while excluding the skill from
default implicit invocation.

## Router and workflow behavior

`skill-router` reads the catalog as well as the registry when it evaluates a
match.

- For a model-invoked skill, retain the existing recommendation and invocation
  flow.
- For a user-only skill, show a concise recommendation and the exact command,
  for example `可用，但需手動啟動：$handoff`. Do not invoke it after the user
  responds with a general confirmation such as "好".
- List mode shows invocation intent for all listed skills, not only entries
  outside the registry.
- A workflow may show a user-only skill as a manual checkpoint. It must stop
  there and show the exact command instead of invoking the step. The current
  one-step `full-research` and `role-pipeline` workflows therefore remain
  discoverable entry points but direct the user to `$tech-research-pipeline`
  and `$role-orchestrator` respectively.

## Catalog and validation

The current fourteen user-only skills remain user-only. Thirteen are routable;
only `skill-router` remains non-routable.

The validator will reject all of the following:

- a user-only skill without Claude's `disable-model-invocation: true`;
- a user-only skill without Codex's
  `policy.allow_implicit_invocation: false`;
- a user-only skill other than `skill-router` that is missing from the router
  registry;
- `skill-router` appearing in its own registry;
- a model-invoked skill that has user-only runtime metadata.

The generated catalog index continues to show lifecycle, invocation intent,
router presence, README presence, and sync policy.

## Tests and verification

Tests will be written before implementation and cover the validation failures
above plus router instructions for manual checkpoints. Verification includes:

1. the full Python unit suite;
2. `python3 scripts/validate_skills_catalog.py --check`;
3. `git diff --check`;
4. `skill-auditor` for the modified `skill-router` skill;
5. native Codex review before any commit request.

After merge and an explicitly authorized sync to each runtime's installed
skill directory, a fresh Claude Code session and a fresh Codex session must
verify that implicit invocation is unavailable while explicit `/skill-name`
and `$skill-name` remain available. No model or external endpoint call is
needed for that smoke check.

## Out of scope

- Reclassifying any existing `model` skill as `user`.
- Automatically applying live runtime policy.
- Changing the behavior of third-party namespaced skills.
- Replacing the catalog/registry design with a new manifest framework.

## Pre-mortem

| Failure mode | Prevention |
|---|---|
| Catalog says user-only but a host still exposes implicit invocation | Validate both runtime metadata files and smoke fresh sessions after an authorized apply. |
| Router discovers a user-only skill then invokes it after a vague confirmation | Add an explicit catalog branch in router instructions and regression coverage. |
| A user-only skill disappears from discovery | Require all except `skill-router` to occur exactly once in the registry. |
| A workflow bypasses the manual gate | Treat user-only workflow steps as checkpoints and test the documented behavior. |
