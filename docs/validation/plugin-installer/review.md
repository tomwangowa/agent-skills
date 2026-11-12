# Installer candidate review

This records the offline review before native run 1. The subsequent native
finding and scoped correction are documented in [run-1 evidence](macos-claude-run-1.md):
`hosts.py` omitted the Git/URL `url` field. A new regression reproduced the
failure, the source-type mapping was corrected, and the offline suite now has
42 cases (41 passed, 1 skipped). A separately approved R2 run subsequently passed
the macOS/Claude single-package installation case; see [R2 evidence](macos-claude-run-2.md)
and its [historical approval scope](native-acceptance-rerun-proposal.md). The
remaining review sections retain the original offline baseline and its limits.

## Findings

No remaining High/Medium code finding was identified in the reviewed offline
scope after the fixes below. **Full delivery and native acceptance remain
incomplete**, especially Codex scope/root evidence, Superpowers installation
and Windows process behavior. This is not release approval.

Self-review in same Codex session: commitment / recency / framing bias not fully controlled.

| Priority | Location | Finding and disposition |
| --- | --- | --- |
| High | `runtime/agent_skills_installer/journal.py:53` | Existing valid settings could contain unrelated extension values that the preview echoed. Fixed by selecting only journal path/options fields; `test_preview_does_not_echo_unrelated_settings_values` observed RED→GREEN. No real private settings were used in that reproduction. |
| Medium | `runtime/agent_skills_installer/execution.py:50`, `ui.py:212` | Execution interruption was recorded but lost at the UI boundary. A structured cancellation flag now stops later phases and returns 130; `test_execution_interrupt_returns_cancelled_exit` RED→GREEN. |
| Medium | `installer/install-macos.command:33`, Linux counterpart | Python manager interruption was flattened into generic exit 1. Preserve 130 and prior-write uncertainty; bootstrap refusal/failure/interruption process test RED→GREEN. |
| Medium | `runtime/agent_skills_installer/ui.py:277` | An approved journal write conflicting with another creator returned overall exit 0. Keep the other file and return 1 for incomplete configuration; filesystem-backed `test_journal_conflict_reports_incomplete_operation` RED→GREEN. |
| Medium | `runtime/agent_skills_installer/journal.py:37` | Missing ancestor directories were created but absent from the preview. Include every missing ancestor; `test_preview_lists_missing_ancestor_directories` RED→GREEN. |
| Medium | `runtime/agent_skills_installer/journal.py:42` | An unavailable drive/share anchor could repeat forever during ancestor discovery. Reject it; bounded unavailable-anchor test RED→GREEN. Native Windows behavior is still not proven. |
| Medium | `runtime/agent_skills_installer/hosts.py:70` | Marketplace identity could be confused with Superpowers plugin identity. Registered Claude entries now check the native manifest identity/version/repository and a real skill entry; provider alias test RED→GREEN. |
| Medium | `runtime/agent_skills_installer/catalog.py:122` | The handoff mod's manual skill was missing from its catalog. Read its actual policy and expose `/handoff-mod:handoff`; surface test RED→GREEN. |
| Medium | `runtime/agent_skills_installer/catalog.py:94` | Folded YAML descriptions (`>-`) could become a one-character purpose. Parse only the description block; real report-generator description test RED→GREEN. |
| Medium | `runtime/agent_skills_installer/catalog.py:158` | Valid JSON with the wrong outer shape produced uncaught exceptions. Normalize malformed catalog shapes into data errors; invalid bundle data test RED→GREEN. |

## Adversarial check

- Change the source payload after confirmation: the transcript test changes a
  real manifest; no install command runs.
- Change settings after preview, or race immediately before publication: real
  temporary files retain the competing bytes and no discarded data directories
  are created. Invalid settings are not replaced.
- Return zero without post-install evidence: executor tests produce
  `unverified`, not `installed`. A failing prerequisite blocks its dependent;
  independent commands can continue without retries or rollback.
- Cancel after a confirmed source action: the transcript retains that prior
  result, reports cancellation and sends no plugin installation command.
- Move the archive, clear repository PYTHONPATH and use another cwd: actual
  subprocesses load the bundled runtime and execute fake-CLI refusal/failure
  paths. Native host downloads were not involved.
- Mirror-test check: command arguments, preserved bytes, created files,
  cancellation codes and archive contents are asserted. Replacing the executor
  or journal apply with a no-op fails the corresponding behavior tests.

## Assumptions

1. The observed host schemas can describe absence. Malformed JSON, nonzero
   exit and conflicting/incomplete metadata are attacked with refusal tests;
   unknown Codex scope/root remains unknown rather than inferred from a cache.
2. Files and sources can change between preview and execution. Target state,
   CLI version, source payload hash and tools are rechecked; config creation is
   create-only. This does not eliminate a remote ref moving during a native
   installation or every hostile filesystem TOCTOU race.
3. Python exists as a real runtime. POSIX refusal/handoff/argument tests run on
   macOS. Windows registry discovery, download-alias behavior and PowerShell
   execution-policy handling have not been executed; the relevant process test
   is explicitly skipped.
4. Native commands can partially write before failure/cancellation. Fake CLI
   and runner tests verify result propagation and no automatic retry/removal;
   real managers and native subprocess descendants remain unverified.

## Review scope

The explicit scope includes both READMEs, every maintained file under
`installer/`, `runtime/agent_skills_installer/`,
`scripts/build_plugin_installer.py`, all nine `tests/test_installer_*.py` files,
the installer fixtures, approved design/plan documents and these validation
records. New files were included explicitly; a tracked-only Git diff would
have omitted most of the implementation. Existing plugin payloads, private
settings, hooks, production and installed caches were not edited.

## Verification

Risk: **L2**, because the program proposes external installations and creates
personal configuration. Native review used `quality-gates:code-review-codex`
in this session, with `quality-gates:completion-gate` evidence requirements.

VERIFIED:

- Final installer suite: 41 cases, 40 passed, 1 skipped, exit 0.
- Existing config tests: 15 passed; package tests: 14 passed.
- Catalog consistency and tracked diff whitespace checks: exit 0.
- Python AST/JSON parsing, POSIX launcher syntax, ZIP payload hashes,
  reproducibility, exclusive output and relocation checked.
- Changed-scope Gitleaks directory scan is recorded in the validation summary.

NOT VERIFIED:

- All real dependency/plugin downloads, updates and installations for this
  installer; no native installation acceptance run is authorized yet.
- Windows/PowerShell process behavior, actual download aliases, native
  Windows journal hard-link behavior and Ubuntu/Debian/other architecture runs.
- Codex installed root/scope and hence safe verified updates; source paths are
  not treated as installed paths. Superpowers automatic source installation.
- Hooks/MCP/skills execution and model-backed functionality.
- Full repository tests, plugin rebuild and server npm tests: some invoke
  `npm ci`/external operations and are outside the approved offline scope.
- A fresh reviewer context, arbitrary hostile path-swap races, native child
  process trees, company policy on managed computers, and live source pinning.

## Rulings I made

1. Use same-session native review as required by the approved plan rather than
   the upstream workflow's delegated final reviewer. Cost: no fresh reviewer
   context; author bias remains.
2. Preserve and mark unknown Codex installations unverified instead of guessing
   scope/root. Cost: updates require additional native capability evidence and
   new installations cannot be reported verified by the observed schema.
3. Publish complete create-only journal settings before making planned data
   directories, then reuse the existing setup validation. Cost: a small local
   publication wrapper must be maintained; Windows filesystem behavior remains
   unverified.
4. Deliver an offline candidate while withholding Superpowers automatic
   installation, real native acceptance and npm-ci-using checks. Cost: the full
   requested installation capability is not complete; those scopes still need
   evidence and explicit approval before use/release.

## Deferred minors

None recorded. No additional polish was bundled into the fix pass.

## Summary

The offline candidate is reviewable. No commit, push, production sync,
publication, model session or native installation test was performed. See the
[first native acceptance proposal](native-acceptance-proposal.md) before
approving a real run.
