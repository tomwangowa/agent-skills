---
name: control-return
description: "Use when the user explicitly invokes $control-return or /control-return to re-apply the three-next-steps rule mid-session. A SessionStart hook auto-applies the rule at session start; the model must not invoke this skill on its own."
disable-model-invocation: true
---

# Control Return

Session-scoped rule, loaded automatically by a SessionStart hook; the manual
command re-applies it. It is an instruction carried by the current
conversation, not a runtime setting.

## Activation

On `$control-return` or `/control-return`:

1. Apply the rule below from this response onward until the session ends.
   Do not apply it retroactively.
2. Reply once: `已啟用 control-return；本 session 後續回應會附三個下一步。`

There is no off command inside a session; if the user asks to stop, stop.
To start a session without the rule, set `AGENT_SESSION_PREFS=off` first.

## Automatic loading

`scripts/session_start_hook.py` runs as a SessionStart hook in Claude Code
and Codex with matcher `startup|clear|compact`. It injects the `## Rule`
block below verbatim, and the activation reply is not sent. If the block
cannot be found, the hook warns and the rule is not active.

## Rule

```text
當你歸還控制權時，要順帶給我三個可行的下一步，並推薦其中一個且說明理由。
三個 Next Steps 的描述要清楚，不要簡略，以免我又要問你釐清問題。
不要為了湊數硬編選項。
例外：向我提問確認需求，或工作還在進行中的回報，不附。
```

## Error Handling

The SessionStart hook always exits 0 so a rule problem never blocks a session.

- `SKILL.md` unreadable or not valid UTF-8: nothing is injected, and a
  `systemMessage` names the path.
- No ```` ```text ```` block inside the `## Rule` section: nothing is injected,
  and a `systemMessage` says so. A text block in a later section is never used.
- Any other failure: a `systemMessage` reports it and nothing is injected.

When a warning appears, the rule is inactive until `SKILL.md` is fixed or the
manual command is used.

## Security Considerations

- The `## Rule` block is injected verbatim as model instructions. Keep the
  installed skill directory writable only by the user.
- The hook reads only this `SKILL.md`, makes no network calls, does not
  execute file content, and ignores its stdin payload.
- The hook validates that the rule block is non-empty, and builds output with
  `json.dumps`, which escapes quotes, newlines, and control characters, so
  rule content cannot break the hook JSON.

## Examples

### Example 1: Normal reply

```text
User: /control-return
Assistant: 已啟用 control-return；本 session 後續回應會附三個下一步。

User: 幫我看一下這個 diff
Assistant: （review 結果）

           下一步（三個選項，建議第 1 個）：
           1. 修掉第 2 點的競態問題，再重跑測試。**建議**，因為它會讓結果不穩。
           2. ……
           3. ……
```

### Example 2: Clarification question (no block)

```text
User: 幫我把這個功能做成 skill
Assistant: 這個 skill 啟用後要持續整個 session，還是只影響下一則回覆？
           A) 持續  B) 一次性  （建議 A，因為……）
           ← 這則是向使用者提問確認需求，依例外規則不附三個下一步。
```
