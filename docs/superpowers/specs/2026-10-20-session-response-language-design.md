# Session Response Language Design

- Date: 2026-10-20
- Status: Accepted
- Scope: Claude Code CLI and Codex CLI sessions using the session-preferences plugin

## Summary

Add an optional session-wide response language default to the shared
agent-skills configuration. Claude Code and Codex read the same value from
agent-skills.json. A setting changes language selection only: tone, format,
and other applicable rules from output styles, CLAUDE.md, AGENTS.md, and
session-preferences remain active.

The feature uses the existing SessionStart hook for automatic loading and
extends the manual session-preferences activation path to reload the value
during an active session.

## Context and Existing Structure

The repository has one shared configuration root resolved in this order:

1. AGENT_SKILLS_CONFIG_DIR
2. XDG_CONFIG_HOME/agent-skills
3. ~/.config/agent-skills

The session-preferences source hook loads personal preference modules and
injects them into the session. The same source is packaged for Claude Code and
Codex by the plugin build process. The manual session-preferences command
currently reloads preference modules for the active session.

The SessionStart hook currently says that output styles, CLAUDE.md, and
AGENTS.md take precedence over injected modules. That general precedence
statement must be narrowed so configured language takes precedence over
general language defaults only, while all other applicable instructions
remain active.

## Configuration Schema

The shared file is agent-skills.json in the resolved configuration root:

    {
      "session_preferences": {
        "response_language": "繁體中文"
      }
    }

response_language is an optional string. It accepts language tags or language
names, for example ja, zh, 繁體中文, or 法語. It is not restricted to a
language-code allowlist.

After trimming surrounding whitespace, the remaining value must be encodable
as UTF-8, non-empty, contain no line breaks, and be no longer than 80 Unicode
code points. No language-code allowlist or canonicalization is applied. This
prevents invalid Unicode and accidental multi-line content from being treated
as a language label while retaining support for language names.

## Language Priority and Behavior

Apply language selection for the assistant's general response prose in this
order:

1. The user's explicit language request for the current response or requested
   output.
2. The configured response_language as the session-wide default.
3. General language defaults in output styles, CLAUDE.md, AGENTS.md, and
   active session-preferences modules.
4. If none of these specify a language, follow the language of the user's
   current message.

The configured value changes only the general response-language default.
Applicable tone, format, terminology, and task-specific output requirements
remain active. Language requirements scoped to a particular artifact also
remain in force unless the user explicitly changes that scope. For example,
the response prose can be Japanese while code comments remain English when a
project rule requires them.

When response_language is absent, existing instruction defaults continue to
apply. If those instructions do not set a language, the assistant follows the
user's current message language.

## Architecture and Data Flow

1. Add a shared reader for agent-skills.json to the source runtime.
2. The SessionStart hook reads the effective preferences and shared language
   setting, then adds both to the session context.
3. The manual session-preferences load path reads the same shared setting
   alongside the preference modules and replaces any previously loaded
   response-language default from that response onward. A missing or invalid
   setting clears the previous configured default and falls back to the other
   active instructions.
4. The existing plugin build process packages the shared source for both
   Claude Code and Codex.

SessionStart handles the existing startup, resume, clear, and compact events.
There is no file watcher. A changed setting applies in a new session or after
manual reload. Removing or invalidating the setting and manually reloading
clears the previously configured language default.

## Error Handling

- A missing agent-skills.json file or missing response_language field means
  that no language default is configured.
- Invalid JSON produces a warning and skips the language setting.
- An invalid session_preferences structure or response_language value
  produces a warning and skips the language setting.
- Invalid language configuration does not prevent readable preference
  modules from loading.
- Unknown fields are ignored.
- SessionStart reports configuration warnings through its system message.
  Manual loading reports configuration warnings separately from preference
  module warnings.

## Verification Strategy

Automated checks should cover:

- Missing file and missing field behavior.
- Valid language tags and localized language names.
- Empty, non-string, multi-line, invalid Unicode, and over-80-Unicode-code-point values.
- Invalid JSON, invalid object structure, and unknown fields.
- The SessionStart hook injecting a valid language setting together with
  loaded preference modules.
- Invalid language configuration warning without suppressing preference
  modules.
- Manual reload reading the same value and warning behavior as SessionStart.
- Manual reload after removing or invalidating a previously configured value
  clears the previous language default and resumes the existing instruction
  priority.
- Generated Claude Code and Codex packages containing the shared behavior.

Native acceptance in both Claude Code and Codex should cover:

- A configured language overriding a conflicting general language default.
- Tone and format rules remaining active under the configured language.
- Task-specific rules such as English code comments remaining active.
- An explicit language request in the current turn overriding the configured
  default.

Parser, hook, and packaging behavior can be checked deterministically. Model
adherence to injected precedence text requires native acceptance and cannot be
guaranteed by the hook itself.

## Out of Scope

- A configuration editor or a command that writes agent-skills.json.
- Watching the file for live changes during a session.
- Project-specific language settings or separate Claude Code and Codex
  values.
- Programmatic enforcement that guarantees every model response uses the
  selected language.
- Changing the user's tone, format, or other response rules.

## Main Risk

An agent may inconsistently follow the configured language when other
instructions state a conflicting language default. The hook must state the
language-only precedence clearly, and native acceptance must test that case
in both runtimes. This remains prompt-level guidance rather than deterministic
enforcement.
