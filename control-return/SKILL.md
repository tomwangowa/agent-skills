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

1. Locate this installation's bundled `runtime/`. Resolve the personal root
   with `resolve_config_root(os.environ, Path.home())` from
   `agent_skills_runtime.config`, then call
   `load_control_return(this_skill_md, config_root)` from
   `agent_skills_runtime.preferences`. Read its effective content and warnings.
2. Apply readable effective content from this response onward until the
   session ends. Do not bypass personal content with the default below or
   apply it retroactively. If loading fails, name the warning and remain inactive.
3. After a successful load, reply once:
   `已啟用 control-return；本 session 後續回應會附三個下一步。`

There is no off command inside a session; if the user asks to stop, stop.
To start a session without the rule, set `AGENT_SESSION_PREFS=off` first.

## Automatic loading

`scripts/session_start_hook.py` runs as a SessionStart hook in Claude Code
and Codex. Register it for `startup|resume|clear|compact`. It injects the
complete personal override when present, otherwise the `## Rule` block below.
The activation reply is not sent. If the selected rule cannot be read, the
hook warns and the rule is not active.

## Rule

```text
當你歸還控制權時，要順帶給我三個可行的下一步，並推薦其中一個且說明理由。
三個 Next Steps 的描述要清楚，不要簡略，以免我又要問你釐清問題。
不要為了湊數硬編選項。
例外：向我提問確認需求，或工作還在進行中的回報，不附。
```

## Error Handling

The SessionStart hook always exits 0 so a rule problem never blocks a session.

- Without a personal override, `SKILL.md` unreadable or not valid UTF-8:
  nothing is injected, and a
  `systemMessage` names the path.
- Without a personal override, no ```` ```text ```` block inside `## Rule`: nothing is injected,
  and a `systemMessage` says so. A text block in a later section is never used.
- Any other failure: a `systemMessage` reports it and nothing is injected.

The shared personal root resolves from `AGENT_SKILLS_CONFIG_DIR`, then
`XDG_CONFIG_HOME/agent-skills`, then the current user's
`~/.config/agent-skills`. If `preferences/control-return.md` exists, its whole
content replaces the packaged Rule block. A broken or empty personal copy
leaves the rule inactive with a warning, rather than reverting silently.

On explicit manual activation, use `load_control_return(skill_md, config_root)`
from this source repository's or plugin's bundled `runtime/`, then apply the
returned content only when readable. Do not bypass a personal copy by reading
the packaged Rule block alone. This file never belongs in the
session-preferences personal INDEX.

Changing a personal rule requires a complete preview and explicit user
confirmation. Use the shared `preferences save` command with the preview's
personal-file SHA-256 as `--expected-hash`; absence is required for first
creation. A stale hash requires a new preview and new approval. On first
creation from the default, `--base-hash` records the SHA-256 of the stripped
Rule block encoded as UTF-8. Keep installed `SKILL.md` unchanged.

When a warning appears, identify the failed path and do not claim the rule is
active. Missing bundled runtime, invalid configuration, unreadable files and
stale writes are reported explicitly.

## Security Considerations

- The `## Rule` block is injected verbatim as model instructions. Keep the
  installed skill directory writable only by the user.
- The hook reads this `SKILL.md` or the resolved personal override, makes no network calls, does not
  execute file content, and ignores its stdin payload.
- The hook validates that the rule block is non-empty, and builds output with
  `json.dumps`, which escapes quotes, newlines, and control characters, so
  rule content cannot break the hook JSON.
- Personal rule symlinks are rejected; keep the personal directory writable
  only by the user and do not store secrets in injected rules. Confirmed edits
  use atomic replacement and POSIX writer locks on macOS, Linux and WSL;
  native Windows writing is not supported.

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
