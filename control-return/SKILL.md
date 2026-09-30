---
name: control-return
description: "Use when the user explicitly invokes $control-return or /control-return to make every reply in the current session end with three next steps. Never enable automatically."
disable-model-invocation: true
---

# Control Return

Manual, session-scoped rule. It is an instruction carried by the current
conversation, not a runtime setting.

## Activation

On `$control-return` or `/control-return`:

1. Apply the rule below from this response onward until the session ends.
   Do not apply it retroactively or in a new session.
2. Reply once: `已啟用 control-return；本 session 後續回應會附三個下一步。`

There is no off command. If the user asks to stop, stop.

## Rule

```text
當你歸還控制權時，要順帶給我三個可行的下一步，並推薦其中一個且說明理由。
三個 Next Steps 的描述要清楚，不要簡略，以免我又要問你釐清問題。
不要為了湊數硬編選項。
例外：向我提問確認需求，或工作還在進行中的回報，不附。
```

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
