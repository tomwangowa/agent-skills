# Session Preferences Design

## Purpose

Add a shareable, user-invoked `session-preferences` skill. It lets a user
activate a small, extensible set of interaction rules for the remainder of
the current session without making them global runtime policy.

The first release provides two rule modules:

- `control-return`: when returning control, offer three real next steps only
  when they are useful; mark one as recommended and state why.
- `deai-voice`: concise, general conversational rules that avoid formulaic
  AI-sounding prose. This is deliberately separate from the existing
  `deai-voice-rewrite` workflow and does not make Tom-specific voice the
  default.

## Scope and activation

- The skill is user-only. The user explicitly invokes
  `$session-preferences` or `/session-preferences`; a model must not enable it
  on its own.
- On activation, reply briefly that the policy is enabled for the current
  session. It applies from that point until the session ends, not
  retroactively and not to a new session.
- This is a session-level instruction, not a runtime-enforced guarantee. A
  fresh-runtime smoke is the only way to observe actual cross-turn behavior.
- It does not alter global policy or automatically synchronize skills to
  other runtimes.

## Files

```text
session-preferences/
├── SKILL.md
├── README.md
├── agents/
│   └── openai.yaml
└── references/
    ├── INDEX.md
    ├── control-return.md
    └── deai-voice.md
```

`SKILL.md` is the thin entry point: activation behavior, reference loading,
and the rule-maintenance workflow. `references/INDEX.md` lists active modules
and their reading order. It does not silently resolve conflicts: if rules
conflict, the agent identifies the conflict and asks the user which rule
wins.

The skill is additionally represented in:

- `skills-catalog.json` as `invocation_intent: user`, `routable: true`.
- `skill-router/skill-registry.yaml` so the router can recommend it as a
  manual `$session-preferences` checkpoint.
- generated `SKILLS_CATALOG.md`.

The user-only metadata gates are required in both runtimes:

- `SKILL.md`: `disable-model-invocation: true`.
- `agents/openai.yaml`: `policy.allow_implicit_invocation: false`.

## User interface

```text
$session-preferences
$session-preferences add-deai <observation or proposed rule>
$session-preferences add-rule <observation or proposed rule>
$session-preferences add-rule <category>: <observation or proposed rule>
```

`add-deai` is the shortcut for the `deai-voice` module. With `add-rule`, the
category is optional: the agent proposes the destination module. If the rule
does not fit an existing module, it proposes a new module and its index entry.

For every update request, the agent first presents the normalized rule and
target file. It changes a reference only after the user confirms. The update
also keeps `INDEX.md` current. No rule is inferred and saved merely because a
phrase appeared in normal conversation.

`README.md` is Traditional Chinese and documents activation, both update
forms, the current-session boundary, rule-module organization, and the fact
that runtime synchronization is separate and never automatic.

## Content boundaries

`deai-voice.md` is an independently useful, general conversational reference.
It may distill compatible ideas from the local style guidance, but must not
copy the entire external-content rewrite workflow, its fact-freeze checklist,
or Tom-specific examples and tone profile. That prevents duplicate,
purpose-mismatched rules from drifting apart.

## Verification

Before proposing a commit:

1. Run `skill-auditor` after creating or changing the skill or a reference.
2. Run `scripts/validate_skills_catalog.py --check` to verify catalog,
   generated catalog document, and user-only metadata gates.
3. Run `git diff --check`.
4. Verify the README examples match the documented invocation and update
   workflow.

These are offline checks. A fresh Claude or Codex runtime smoke would require
separate authorization because the skill would first have to be synchronized
to that runtime; this design does not authorize or perform that sync.

## Out of scope

- Global or automatic application of these rules.
- Automatic synchronization to Codex, Claude, or any other runtime.
- A hard runtime mechanism that forces every later response to comply.
- Copying the entire `deai-voice-rewrite` skill into this one.
- A generic manifest framework beyond the plain `references/INDEX.md` file.
