# Personal Plugin Removal Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [x]`) syntax for tracking.

**Goal:** Add the approved, separate package-removal flow while preserving project configuration and user journal data.

**Architecture:** A mode chooser dispatches to installation or a focused removal UI. A pure removal planner constructs qualified actions; execution rechecks and verifies native inventory using the existing once-only engine and progress presenter.

**Tech Stack:** Python 3.11+ standard library and the existing native CLI adapters.

**Spec:** `docs/superpowers/specs/2026-11-11-plugin-removal-design.md` (user-approved flow).

## Global Constraints

- Eligible Claude CLI: `2.1.322 (Claude Code)`; only `--scope user --keep-data --json` uninstall, never prune or marketplace removal.
- Codex CLI may remove a qualified plugin's shared cache when its help output and inventory expose the verified native removal interface; the preview warns that projects referencing it may stop loading it, while project config, plugin data and other marketplace entries stay untouched.
- Empty defaults, explicit preview confirmation, no retry/rollback, no journal setup/data reads, no dependency installation.
- Preserve R10 and earlier archives; no real host calls, models, commit or publication without separate authorization.
- Execute inline in this session; no subagents or external reviewers.

## Review Focus

- Duplicate user entries must not collapse into a removable target.
- Project entries sharing a Claude cache must survive personal removal.
- Newer versions and disabled manual installs must remain removable when identified.
- A successful command whose target remains must be reported unverified.
- Codex removal must use the exact qualified identity, remove only its cache entry, and preserve every other installed-plugin record and marketplace.
- Cancellation after one command must retain completed results and stop further commands.

## Scope amendment — 2026-11-12

The user approved removal from the Codex shared cache after the preview warns
that project configurations may continue to reference the removed plugin. Use
only the native `codex plugin remove <plugin>@<marketplace> --json` command
when a read-only CLI help probe advertises the qualified selector and JSON
output, and inventory/cache checks match the expected structure. Do not edit
project settings or remove marketplaces, plugin data or other cache entries.
The official Codex `0.166.0` and `0.167.0` sources expose this interface; an
unknown or incompatible interface remains withheld.

### Task 1: Removal decisions and verified execution

**Files:** create `runtime/agent_skills_installer/removal.py`, `tests/test_installer_removal.py`; update `execution.py`, `progress.py`.
**Interfaces:** `removal_options(catalog, inventories, claude_root, *, codex_remove_supported)` returns options with eligibility reasons; `make_removal_plan(options, selected)` seals removal actions; `recheck_removal` and `verify_removal` compare registered targets and protected records.

- [x] Write failing tests for Claude personal/project preservation, disabled/newer/manual installs, source ambiguity, paths, stale state and native result verification.
- [x] Run `PYTHONPATH=runtime:tests python3 -m unittest test_installer_removal`; observe the missing behavior.
- [x] Implement the narrow planner and state checks; add removed outcomes to execution/progress without changing install/update semantics.
- [x] Run the focused tests, including the five review-focus cases and interruption/partial results.

### Task 2: Separate interactive removal entry

**Files:** create `runtime/agent_skills_installer/removal_ui.py`; update `__main__.py`, builder allowlist and focused tests.
**Interfaces:** `choose_operation(input_fn, output)` returns install/remove/cancel; `run_removal(catalog, input_fn, output, runner, *, package_selector=None, progress=None)` returns an exit code.

- [x] Write failing menu/transcript tests for unchecked defaults, host selection, preview, empty selection, decline, successful removal, no journal prompts and no install/dependency/source commands.
- [x] Implement the mode dispatch and removal-only workflow; keep the old `ui.run` install interface intact.
- [x] Verify focused tests and the actual bundled entry with a real PTY and fake native CLIs.

### Task 3: Regression and reviewable R11

**Files:** installer/root READMEs, validation index and new R11 report/evidence; new R11 ZIP and trial directory.

- [x] Run full `test_installer_*.py`, package/config tests, catalog/syntax/whitespace checks.
- [x] Perform current-session native code review and completion gate; fix concrete findings and rerun affected checks.
- [x] Build an exclusive R11 archive twice; verify identical bytes and all input/payload hashes, scan a fresh exact extraction, and verify the relocated launcher.
- [x] Recheck old archive hashes, five personal file hashes, HEAD, stashes and staged state; report verified behavior and remaining native/platform gaps without committing.

### Task 4: Codex shared-cache removal extension

**Files:** modify `runtime/agent_skills_installer/removal.py`, `removal_ui.py`, `execution.py`, `tests/test_installer_removal.py`, and installer removal documentation.

- [x] Gate the native path on the qualified remove command and JSON capability, plus a verified plugin identity and `CODEX_HOME` cache tree; do not pin removal to one CLI version.
- [x] Preview the shared-cache impact, call only `codex plugin remove <plugin>@<marketplace> --json`, and confirm the target cache is gone while other plugins and marketplaces remain.
- [x] Update the existing Codex removal assertions and document that project config stays but may still reference the removed plugin.
- [ ] Run the focused and full installer test suites; native Codex removal acceptance remains for the user trial.
