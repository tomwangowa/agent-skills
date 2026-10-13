---
name: session-preferences
description: "Use when the user explicitly invokes $session-preferences or /session-preferences to re-apply the session policy bundle mid-session, or to propose and confirm a new rule. A SessionStart hook auto-applies the bundle at session start; the model must not invoke this skill on its own."
disable-model-invocation: true
---

# Session Preferences

## Visualization

Use ASCII to visualize content when explaining concepts.

Apply the user's active interaction rules from `references/` for the rest of
the session. A SessionStart hook loads them automatically; the manual command
re-applies them. This is session-scoped, not a global runtime setting.

## Activation

On `$session-preferences` or `/session-preferences`:

1. Read `references/INDEX.md`, then read every module listed there.
2. Apply those modules from this response onward until the session ends.
3. Reply once: `已啟用 session-preferences；本 session 後續回應會套用目前規則。`

New sessions already get these modules from the SessionStart hook (see
Automatic loading). Use the manual command when the hook did not run, for
example when `AGENT_SESSION_PREFS=off` was set, and the user wants the policy
for the rest of this session. Do not apply rules retroactively.

An active module may direct conditional reading of a reference intentionally
absent from `INDEX.md`. Read that reference before producing the matching
content. If it cannot be read, name the missing path and do not claim that its
rules were applied. `INDEX.md` remains the complete list of always-loaded
modules.

## Automatic loading

`scripts/session_start_hook.py` runs as a SessionStart hook in Claude Code
(`~/.claude/settings.json`) and Codex (`~/.codex/hooks.json`) with matcher
`startup|clear|compact`. It injects `INDEX.md` modules verbatim, plus the
absolute paths of deferred references. In hook mode the activation reply is
not sent. Setting `AGENT_SESSION_PREFS=off` before starting a session skips
injection. If a file is unreadable, the hook names the path in a warning and
the missing rules must not be claimed as applied.

## Maintain Rules

Accept these explicit forms:

```text
$session-preferences add-deai <observation or proposed rule>
$session-preferences add-rule <observation or proposed rule>
$session-preferences add-rule <category>: <observation or proposed rule>
```

For `add-deai`, choose and propose the best destination:

- `deai-voice`: every new Traditional Chinese reply and reference-loading
  decisions.
- `deai-longform`: requested drafts or prose longer than two paragraphs.
- `deai-translation`: source-to-target translation behavior.
- `taiwan-zh`: Taiwan terminology or Chinese punctuation judgment.

For `add-rule` without a category, choose the best existing module; propose a
new kebab-case module and an `INDEX.md` row only when none fits.

Before writing, show the user:

- normalized rule;
- target module and scope;
- whether a new module and index row are needed;
- that confirmation makes it effective immediately for this session.

Write only after explicit confirmation. Then update the module and, if needed,
`INDEX.md`; reread the modified reference; and state that the rule is now
active for the rest of the session. Run `skill-auditor` after any such change.
Never infer and save a rule from ordinary conversation.

## Conflicts and limits

If active modules conflict, identify the conflict and ask the user to choose;
`INDEX.md` controls loading order, not silent overrides. Do not run
`skill-sync`, change global policy, or modify a live runtime as part of this
skill.

If `INDEX.md` or a listed module cannot be read, report the missing path and
do not claim the policy is enabled.

## Error Handling

The SessionStart hook always exits 0 so a rule problem never blocks a session.

- `INDEX.md` unreadable or listing no modules: nothing is injected, and a
  `systemMessage` names the path.
- A listed module unreadable, not valid UTF-8, or with an invalid filename
  in `INDEX.md`: the other modules are injected, the context lists the
  missing path as not loaded, and a `systemMessage` repeats it.
- Any other failure: a `systemMessage` reports it and nothing is injected.

When a warning appears, treat the named rules as inactive until the file is
fixed or the manual command succeeds.

## Security Considerations

- Module text is injected verbatim as model instructions. Anyone who can write
  to `references/` controls those instructions, so keep the installed skill
  directory writable only by the user.
- The hook validates each `INDEX.md` File cell (backticks allowed) against
  `[\w.-]+\.md`. A cell with a path separator or other invalid character is
  not loaded and is reported like a missing module, so an entry cannot point
  outside `references/` and cannot disappear silently.
- Output is built with `json.dumps`, which escapes quotes, newlines, and
  control characters in rule text, so rule content cannot break the hook JSON.
- The hook reads only files inside this skill directory, makes no network
  calls, does not execute file content, and ignores its stdin payload.
- Rules must not contain secrets; they are sent to the model every session.

## Examples

### Example 1: Enable the current-session policy

```text
User: $session-preferences
Assistant: 已啟用 session-preferences；本 session 後續回應會套用目前規則。

User: $session-preferences add-rule 不要用「痛點」當成泛稱
Assistant: 我建議加到 `deai-voice`：避免把「痛點」當泛稱；改直接描述問題。
           確認後我才會寫入，且會立刻套用到本 session。
```

### Example 2: Place a de-AI rule by its scope

```text
User: $session-preferences add-deai 翻譯時不要為了自然就改掉原文刻意的排比
Assistant: 我建議寫入 `deai-translation`。它只約束翻譯時的忠實性判斷；
           確認後我才會寫入，且會立刻套用到本 session。
```

### Example 3: Target an existing module

```text
User: $session-preferences add-rule socratic-dialogue: 每個問題都附一個具體例子
Assistant: 我建議寫入 `socratic-dialogue`。它只改 brainstorming 這類一問一答的情境，
           確認後立即套用到本 session；要現在寫入嗎？
```
