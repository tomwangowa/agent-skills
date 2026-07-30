# Session Preferences De-AI Expansion Design

## Purpose

Expand `session-preferences`' shareable `deai-voice` policy from a short
conversation preference into a layered Traditional Chinese writing policy.
It must improve ordinary session replies without turning the skill into
Tom-specific voice emulation, an automatic global policy, or an external-draft
rewriter.

The design takes inspiration only from the *methods* visible in
`allenloves/de-ai-tone`: identify recurring rhetorical habits, give each rule
an observable decision test, and run a focused self-check for longer text.
It does not copy or adapt that project's wording, tables, examples, or CC
BY-SA-licensed material. `agent-skills` remains MIT.

## Scope and precedence

After a user explicitly activates `$session-preferences`, apply the policy to
new Traditional Chinese prose for the rest of that session. Do not apply it to
code, literal quotations, identifiers, paths, API fields, fixed templates, or
explicitly requested tables and lists.

Apply this priority order:

1. The user's explicit wording, voice, and formatting instructions.
2. Fidelity to source material, quotations, identifiers, contractual text,
   and other immutable content.
3. The active `deai-voice` policy.
4. Default conversational preferences.

Use Taiwan Traditional Chinese and full-width punctuation by default. Respect
the requested locale, quoted source, or a technical convention when that is
more appropriate.

## Layered references

Keep `deai-voice` as the one always-loaded de-AI module. It contains the
priority order, a compact decision table, and rules that apply to every new
Traditional Chinese response: start directly, end after the last substantive
point, avoid empty discourse labels, artificial contrasts, mechanical
three-part parallelism, repetitive mini-summaries, needless decorative emoji,
and vague business jargon.

Add three original, deferred references:

```text
references/
├── deai-voice.md          # always loaded core and loading decisions
├── deai-longform.md       # continuous prose and self-check
├── deai-translation.md    # translation-specific fidelity and syntax guidance
└── taiwan-zh.md           # Taiwan usage and punctuation guidance
```

`INDEX.md` continues to list only `control-return` and `deai-voice` as active
modules. `deai-voice.md` directs the agent to read a deferred reference only
when needed:

| Situation | Deferred reference |
| --- | --- |
| A requested draft or a response with more than two prose paragraphs | `deai-longform.md` |
| Translation | `deai-translation.md` |
| Taiwan wording, suspected Mainland usage, or punctuation needs judgment | `taiwan-zh.md` |

More than one reference may apply to the same reply. If a required deferred
reference cannot be read, report the missing file and do not claim that layer
was applied.

## Rule maintenance

Keep the existing confirmation gate. For
`$session-preferences add-deai <rule>`, first normalize the proposed rule and
propose one destination: `deai-voice`, `deai-longform`, `deai-translation`, or
`taiwan-zh`. Write only after explicit confirmation, then read the changed
reference so the approved rule takes effect for the rest of the current
session.

`SKILL.md` must describe this routing so `add-deai` does not incorrectly claim
that every de-AI rule belongs in the always-loaded core file. Update the README
to document the four destinations and the deferred-loading behavior.

## Boundaries

- Do not change the user-only metadata gates, catalog, router, activation
  command, host policies, or sync behavior.
- Do not import Tom's personal voice profile, the `deai-voice-rewrite` fact
  freeze workflow, or an outward-facing draft rewrite contract.
- Do not add a mandatory visible checklist, a text linter, or numeric word
  quotas. The extended checks are silent reasoning aids unless the user asks
  to see them.
- In translation, source fidelity overrides de-AI cleanup when the source
  deliberately uses a rhetorical form.

## Verification

1. Verify every reference named by `SKILL.md` and `deai-voice.md` exists and
   is readable.
2. Run `skill-auditor` after modifying the skill.
3. Run `python3 scripts/validate_skills_catalog.py --check` and
   `git diff --check`.
4. Walk five static scenarios: a short reply, a three-paragraph draft, a
   translation, Taiwan terminology or punctuation, and an `add-deai` proposal.
   Check the intended references, precedence, and no-checklist output.
5. Treat a fresh runtime smoke as separate, single-use work. Run it only with
   explicit authorization; do not infer success from offline checks.
