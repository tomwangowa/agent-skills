# Session Response Language Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox syntax for tracking: - [x].

**Goal:** Add an optional shared response-language default for Claude Code CLI and Codex CLI sessions using session-preferences.

**Architecture:** Read the session-preferences section from agent-skills.json using the existing shared configuration root. Reuse one reader from the SessionStart hook and manual preference loader, then regenerate both native plugin packages from the canonical source.

**Tech Stack:** Python 3 standard library, JSON, unittest, SessionStart hooks, scripts/build_plugins.py.

**Spec:** docs/superpowers/specs/2026-10-20-session-response-language-design.md

## Global Constraints

- The shared file is agent-skills.json in the resolved configuration root.
- response_language accepts language tags or language names and is not restricted to a language-code allowlist.
- After trimming surrounding whitespace, response_language must be encodable as UTF-8, non-empty, contain no line breaks, and be no longer than 80 Unicode code points.
- The user's explicit language request for the current response or requested output takes precedence over response_language.
- response_language overrides general language defaults only; applicable tone, format, terminology, and task-specific output requirements remain active.
- Missing configuration falls back to existing instruction defaults, then the user's current message language if no instruction sets a language.
- Each manual reload replaces the previous configured language default; when the new value is missing or invalid, clear that override and return to the other active instructions.
- Invalid language configuration warns and is skipped without preventing readable preference modules from loading.
- The feature supports Claude Code CLI and Codex CLI through the session-preferences plugin.
- Do not add a configuration editor, file watcher, project-specific setting, runtime-specific setting, or deterministic language enforcement.
- Run skill-auditor after modifying session-preferences/SKILL.md.
- Before claiming implementation complete, apply completion-gate. Before proposing a commit, follow the project's L0/L1/L2 review rules.
- Do not commit without the user's explicit approval. If approved, use a Conventional Commit message.
- Defer plugin version bumps until the release gate: full native acceptance must be refreshed before publishing, per the accepted decision in `docs/superpowers/specs/2026-10-18-ci-and-acceptance-wording-design.md` (A3).

## Review Focus

- A JSON array or scalar root must warn; pin parser behavior with test_response_language_warns_for_invalid_json_and_shape in Task 1 and module preservation with test_invalid_response_language_warns_without_suppressing_modules in Task 2.
- Invalid UTF-8 bytes must warn rather than escape as an exception; pin with test_response_language_warns_on_invalid_utf8 in Task 1.
- An escaped lone surrogate must warn rather than break UTF-8 hook output; pin with test_response_language_rejects_invalid_values in Task 1.
- The 80-code-point boundary must accept 80 and reject 81; pin with test_response_language_enforces_unicode_length_boundary in Task 1.
- A CR or LF remaining inside the trimmed value must be rejected; pin with test_response_language_rejects_invalid_values in Task 1.
- A config file resolving inside a plugin cache must be rejected with a warning; pin with test_response_language_rejects_cache_symlink in Task 1.

---

## File Map

- Modify runtime/agent_skills_runtime/config.py to parse and validate the optional language field using the existing config-root and personal-path rules.
- Modify tests/test_agent_skills_config.py to pin missing, valid, invalid, and security-sensitive configuration inputs.
- Modify session-preferences/scripts/session_start_hook.py to inject the configured default and report config warnings without suppressing modules.
- Modify tests/test_session_start_hooks.py to verify the injected language policy and partial-failure behavior.
- Modify runtime/agent_skills_runtime/preferences.py so the existing load command returns the configured language and separate config warnings.
- Modify tests/test_preferences_overrides.py to verify the manual loader's output.
- Modify session-preferences/SKILL.md so manual activation reads and applies the language value with the approved precedence.
- Modify session-preferences/README.md and docs/plugins/installation.md to document the shared JSON field and reload behavior.
- Regenerate, but do not hand-edit, plugins/claude/session-preferences/ and plugins/codex/session-preferences/ with scripts/build_plugins.py.

### Task 1: Add the Shared Language Settings Reader

**Files:**
- Modify: runtime/agent_skills_runtime/config.py
- Test: tests/test_agent_skills_config.py

**Interfaces:**
- Consumes: resolve_config_root(env, home) and require_external_personal_path(path) from agent_skills_runtime.config.
- Produces: read_response_language(config_root: Path) -> tuple[str | None, list[str]]. Return (None, []) when the file or field is absent; return the trimmed language and no warnings for a valid value; return (None, [warning]) for invalid file or field data.

- [x] **Step 1: Write focused reader tests.** Add tests named test_response_language_missing_config_is_unset, test_response_language_accepts_language_tag_and_name, test_response_language_ignores_unknown_keys, test_response_language_warns_for_invalid_json_and_shape, test_response_language_warns_on_invalid_utf8, test_response_language_rejects_invalid_values, test_response_language_enforces_unicode_length_boundary, and test_response_language_rejects_cache_symlink.

- [x] **Step 2: Run the config test module to verify the new tests fail.**

Run: python3 -m unittest discover -s tests -p 'test_agent_skills_config.py' -v
Expected: existing tests pass; new response-language tests fail because read_response_language is not implemented.

- [x] **Step 3: Implement read_response_language(config_root: Path) -> tuple[str | None, list[str]] in runtime/agent_skills_runtime/config.py.** Read UTF-8 JSON from agent-skills.json, require an object root and an object session_preferences value when present, ignore unknown keys, and validate response_language after trimming. Treat FileNotFoundError as unset with no warning; return a warning for other read, decode, JSON, and validation errors rather than raising.

- [x] **Step 4: Run the config test module.**

Run: python3 -m unittest discover -s tests -p 'test_agent_skills_config.py' -v
Expected: all config tests pass, including all eight response-language tests.

### Task 2: Inject the Language Default at Session Start

**Files:**
- Modify: session-preferences/scripts/session_start_hook.py
- Test: tests/test_session_start_hooks.py

**Interfaces:**
- Consumes: read_response_language(config_root) from Task 1 and the existing load_preferences(default_dir, config_root) function.
- Produces: SessionStart additionalContext with a language-only default directive when configured; warnings in systemMessage; preference modules remain present when only the language config is invalid.

- [x] **Step 1: Add hook tests.** Add test_injects_configured_response_language_without_removing_modules and test_invalid_response_language_warns_without_suppressing_modules. Update test_injects_listed_modules_in_index_order to assert that the shared header no longer gives output styles, CLAUDE.md, or AGENTS.md blanket precedence over configured language.

- [x] **Step 2: Run the SessionStart hook test module to verify the new assertions fail.**

Run: python3 -m unittest discover -s tests -p 'test_session_start_hooks.py' -v
Expected: existing behavior tests pass except the new language and narrowed-precedence assertions.

- [x] **Step 3: Update session-preferences/scripts/session_start_hook.py.** Read the shared language setting alongside modules, add a clearly delimited language-only directive when present, preserve the other style and task rules, and combine config warnings with existing hook warnings. Keep the hook exit status at zero for invalid language configuration.

- [x] **Step 4: Run the SessionStart hook test module.**

Run: python3 -m unittest discover -s tests -p 'test_session_start_hooks.py' -v
Expected: all hook tests pass; invalid language config produces a warning while valid modules remain in additionalContext.

### Task 3: Reload the Setting Through session-preferences

**Files:**
- Modify: runtime/agent_skills_runtime/preferences.py
- Modify: session-preferences/SKILL.md
- Test: tests/test_preferences_overrides.py

**Interfaces:**
- Consumes: read_response_language(config_root) from Task 1 and the existing preference load result.
- Produces: the preferences load JSON object retains content and warnings and adds response_language and config_warnings. response_language is null when unset. The manual activation instructions apply the value from this result starting with the current response.

- [x] **Step 1: Add CLI tests.** Add test_real_cli_load_includes_response_language_and_separate_config_warnings and test_real_cli_load_keeps_modules_when_language_config_is_invalid.

- [x] **Step 2: Run the preference override test module to verify the new tests fail.**

Run: python3 -m unittest discover -s tests -p 'test_preferences_overrides.py' -v
Expected: existing preference tests pass; new CLI response-language assertions fail because the load result lacks the new fields.

- [x] **Step 3: Extend the load branch in runtime/agent_skills_runtime/preferences.py.** Add response_language and config_warnings to its JSON output, and return a nonzero status when either warning list is non-empty while still printing all readable content.

- [x] **Step 4: Update the Activation instructions in session-preferences/SKILL.md.** Read both warning lists, apply readable modules and the configured language, preserve the approved precedence, and report language-configuration warnings separately from inactive modules.

- [x] **Step 5: Run skill-auditor on the modified session-preferences/SKILL.md.** Resolve any findings before continuing.

- [x] **Step 6: Run the preference override test module.**

Run: python3 -m unittest discover -s tests -p 'test_preferences_overrides.py' -v
Expected: all preference tests pass, including both CLI language-loading tests.

### Task 4: Document and Regenerate Both Runtime Packages

**Files:**
- Modify: session-preferences/README.md
- Modify: docs/plugins/installation.md
- Regenerate: plugins/claude/session-preferences/
- Regenerate: plugins/codex/session-preferences/

**Interfaces:**
- Consumes: the shared reader, SessionStart directive, and manual load output from Tasks 1–3.
- Produces: user documentation with the JSON example, shared path precedence, session-start behavior, and manual reload behavior; matching generated Claude Code and Codex plugin packages.

- [x] **Step 1: Document the setting.** Add the agent-skills.json example and explain accepted language tags and names, the 80-code-point single-line validation, missing-setting fallback, invalid-setting warning behavior, manual reload, and language-only precedence in session-preferences/README.md and docs/plugins/installation.md.

- [x] **Step 2: Regenerate all managed plugin outputs from canonical sources.**

Run: python3 scripts/build_plugins.py --write
Expected: generated Claude Code and Codex session-preferences packages include the updated hook, runtime, skill instructions, and documentation.

- [x] **Step 3: Check generated package parity.**

Run: python3 scripts/build_plugins.py --check
Expected: Generated outputs match source.

- [x] **Step 4: Run the repository Python test suite.**

Run: python3 -m unittest discover -s tests
Expected: OK.

### Task 5: Verify Native Language Precedence

**Files:**
- No repository files; acceptance runs against the generated packages from Task 4.

**Interfaces:**
- Consumes: generated Claude Code and Codex session-preferences packages.
- Produces: a pass/fail result for the required native acceptance cases in both runtimes.

- [x] **Step 1: Prepare isolated settings.** Set AGENT_SKILLS_CONFIG_DIR to a temporary directory, write agent-skills.json with response_language set to Japanese, and use a temporary project instruction that sets Traditional Chinese as the general language default, requests concise neutral tone and exactly two bullets, and requires English code comments.

- [x] **Step 2: Verify the configured default in Claude Code CLI and Codex CLI.** Start a new session in each runtime and ask for an ordinary response. Expected: response prose is Japanese despite the conflicting general default.

- [x] **Step 3: Verify preserved style and scoped language rules in both runtimes.** Request a response containing code comments. Expected: the prose is Japanese, it uses exactly two concise neutral bullets, and comments remain English as required by the project instruction.

- [x] **Step 4: Verify the per-turn override in both runtimes.** In each session, explicitly request that the next response be in English. Expected: the response uses English, while applicable tone and format rules remain active.

- [x] **Step 5: Apply completion-gate before claiming implementation complete.** Report evidence for parser, hook, CLI, generated package, and native acceptance behavior.

- [x] **Step 6: Assess pre-commit risk using the project's L0/L1/L2 rules.** L0 uses deterministic checks only; L1 and L2 require one code-review-codex pass; L2 also requires the full completion-gate.

- [x] **Step 7: Use the user's explicit approval before creating the commit.** Approval for commit, push, and PR was given on 2026-10-21; use a Conventional Commit message that describes the feature.
