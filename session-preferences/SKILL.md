---
name: session-preferences
description: "Use when the user explicitly invokes $session-preferences or /session-preferences to enable a modular policy bundle for the current session, or to propose and confirm a new rule. Never enable automatically."
disable-model-invocation: true
---

# Session Preferences

Load and apply the user's active interaction rules from `references/` for the
remainder of this session. This is a manual, session-scoped policy bundle; it
is not a global runtime setting.

## Activation

On `$session-preferences` or `/session-preferences`:

1. Read `references/INDEX.md`, then read every module listed there.
2. Apply those modules from this response onward until the session ends.
3. Reply once: `已啟用 session-preferences；本 session 後續回應會套用目前規則。`

Do not apply rules retroactively or in a new session. The policy is an
instruction carried by the current conversation, not a hard runtime state.

## Maintain Rules

Accept these explicit forms:

```text
$session-preferences add-deai <observation or proposed rule>
$session-preferences add-rule <observation or proposed rule>
$session-preferences add-rule <category>: <observation or proposed rule>
```

`add-deai` always proposes `deai-voice`. For `add-rule` without a category,
choose the best existing module; propose a new kebab-case module and an
`INDEX.md` row only when none fits.

Before writing, show the user:

- normalized rule;
- target module and scope;
- whether a new module and index row are needed;
- that confirmation makes it effective immediately for this session.

Write only after explicit confirmation. Then update the module and, if needed,
`INDEX.md`; state that the rule is now active for the rest of the session.
Run `skill-auditor` after any such change. Never infer and save a rule from
ordinary conversation.

## Conflicts and limits

If active modules conflict, identify the conflict and ask the user to choose;
`INDEX.md` controls loading order, not silent overrides. Do not run
`skill-sync`, change global policy, or modify a live runtime as part of this
skill.

If `INDEX.md` or a listed module cannot be read, report the missing path and
do not claim the policy is enabled.

## Examples

### Example 1: Enable the current-session policy

```text
User: $session-preferences
Assistant: 已啟用 session-preferences；本 session 後續回應會套用目前規則。

User: $session-preferences add-rule 不要用「痛點」當成泛稱
Assistant: 我建議加到 `deai-voice`：避免把「痛點」當泛稱；改直接描述問題。
           確認後我才會寫入，且會立刻套用到本 session。
```

### Example 2: Target an existing module

```text
User: $session-preferences add-rule control-return: 沒有三個真實選項時，不要列下一步
Assistant: 我建議寫入 `control-return`。它只改「交還控制權」的情境，
           確認後立即套用到本 session；要現在寫入嗎？
```
