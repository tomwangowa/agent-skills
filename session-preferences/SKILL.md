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

1. Locate this installation's package root: the source repository contains
   `runtime/`; a plugin contains `skills/session-preferences/` and its own
   `runtime/`. Put that `runtime/` on `PYTHONPATH` and run
   `python3 -m agent_skills_runtime.preferences load --default-dir <this-skill>/references`.
   Read the returned effective content and warnings; do not load only the
   packaged INDEX and bypass personal copies.
2. Apply those modules from this response onward until the session ends.
3. If there are no warnings, reply once:
   `已啟用 session-preferences；本 session 後續回應會套用目前規則。`
   Otherwise apply readable modules and name the inactive ones; do not claim
   complete activation.

New sessions already get these modules from the SessionStart hook (see
Automatic loading). Use the manual command when the hook did not run, for
example when `AGENT_SESSION_PREFS=off` was set, and the user wants the policy
for the rest of this session. Do not apply rules retroactively.

An active module may direct conditional reading of a reference intentionally
absent from `INDEX.md`. Read that reference before producing the matching
content. If it cannot be read, name the missing path and do not claim that its
rules were applied. `INDEX.md` remains the complete list of always-loaded
modules in the packaged INDEX plus explicitly indexed personal additions.

## Shared Configuration

Resolve the personal root using `AGENT_SKILLS_CONFIG_DIR`, otherwise
`XDG_CONFIG_HOME/agent-skills`, otherwise `~/.config/agent-skills` for the
current user. Explicit environment roots must be absolute or `~/` paths.
Personal rules live under `preferences/` outside plugin caches.

The packaged INDEX defines default active modules. A same-name personal file
replaces the whole default; a new module in the personal INDEX is appended.
Deferred references use the personal copy when present, without becoming
always-loaded modules. `preferences/control-return.md` belongs only to the
control-return hook and must not be added to this INDEX.

An invalid personal copy is reported as inactive; never silently substitute
the packaged default. Apply readable modules and identify each failed one.

## Automatic loading

`scripts/session_start_hook.py` runs as a SessionStart hook in Claude Code
and Codex. Register it for `startup|resume|clear|compact`. It injects the
effective INDEX modules with whole-file personal substitutions, plus absolute
paths of deferred references. In hook mode the activation reply is
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

Before showing the preview, record the SHA-256 of the existing personal file
bytes, or absence if there is no personal file. On a first override, copy the
packaged content and record its SHA-256 as the base hash. Show the complete
proposed content and personal destination; do not edit installed references.

Write only after explicit confirmation, using the shared runtime's `save`
command with `--module <filename.md>`, `--content-file`, and the preview's `--expected-hash`
when a personal file exists. For a first override of an existing default,
also pass `--base-hash`; omit it for a newly proposed module. The command
preserves the original base hash, atomically replaces files under a writer
lock, and adds a personal INDEX row only for a new module. Editing a deferred
reference does not make it always loaded.

For example, after confirming an edit of an existing personal translation file:

```sh
PYTHONPATH="<package-root>/runtime" python3 -m agent_skills_runtime.preferences save --module deai-translation.md --content-file "<complete-proposal-file>" --expected-hash "<preview-sha256>"
```

Replace the placeholders with the resolved package path, preview file and
recorded hash. The result names the saved `path` and new `sha256`.

If the file changed since preview, stop, reread it, show a new preview and
obtain fresh confirmation. Never retry with a newly computed hash under the
old approval. Reread the saved file and apply it to this session as already
specified by the confirmed request. Run `skill-auditor` after skill instruction
changes; personal rule edits must also be inspected for conflicts and secrets.
Never infer and save a rule from ordinary conversation.

## Conflicts and limits

If active modules conflict, identify the conflict and ask the user to choose;
`INDEX.md` controls loading order, not silent overrides. Do not run
`skill-sync`, change global policy, or modify a live runtime as part of this
skill.

If an INDEX or listed module cannot be read, report the path and do not claim
the whole policy is enabled. Readable modules remain active.

## Error Handling

The SessionStart hook always exits 0 so a rule problem never blocks a session.

- Packaged `INDEX.md` unreadable or listing no modules: any readable personal
  additions may still load; otherwise nothing is injected, and a
  `systemMessage` names the path.
- A listed module unreadable, not valid UTF-8, or with an invalid filename
  in `INDEX.md`: the other modules are injected, the context lists the
  missing path as not loaded, and a `systemMessage` repeats it.
- Missing bundled runtime, invalid config root, invalid personal INDEX or
  personal override: warnings identify the inactive components. Neither
  missing modules nor missing runtime is treated as a complete activation.
- A stale preview, malformed base-hash metadata, unsafe filename or unreadable
  proposed content blocks writing; reread and obtain a new confirmed preview.
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
- The hook reads packaged defaults and the resolved personal preferences
  directory, makes no network calls, does not execute file content, and ignores
  its stdin payload. Symlink rule files are rejected. Keep both locations
  writable only by the user.
- Python's POSIX writer lock supports macOS, Linux and WSL. Native Windows
  writing is not supported by this runtime. A stale content hash prevents
  competing writers from silently replacing each other's changes.
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
