# Codex new-install receipts: candidate R3

Date: 2026-11-10 (Asia/Taipei). Baseline HEAD:
`fe55c04bf9202fe82f1a68b7f5985305c82249f0`.

## Result and scope

The Codex new-install flow now consumes the native command's JSON receipt
instead of trying to infer installed root/scope from inventory. Its original
offline checks and subsequent [one native continuation case](macos-codex-r3-continuation.md)
are recorded separately; overall native platform/function acceptance is incomplete.
Only the audited Codex CLI `0.167.0` and the repository's `tomwangowa` packages
are supported by this receipt path. Existing Codex installs/updates and external
Superpowers installation remain withheld.

The approved follow-up was the new-install repair described in the
[capability audit](codex-superpowers-capability-audit.md). No new feature design,
source replacement, native install, commit, push or installed-cache edit was
authorized or performed in this follow-up.

## Implementation

- `native_runner` captures Codex add's JSON stdout, retaining inherited stdin
  and stderr so native diagnostics are visible. Other mutation commands retain
  their existing terminal behavior.
- Execution passes the actual command result to verification. A successful
  Codex result retains an immutable receipt in its outcome and displays the
  verified installed root. Raw native JSON is not printed or persisted.
- Inventory records the resolved CODEX_HOME target separately from plugin
  scope; the default is `~/.codex`. Empty, relative and ambiguous explicit
  CODEX_HOME values fail closed. No plugin/skill scope is manufactured.
- The approved plan includes the target config root and CLI version. Recheck
  rejects target changes and protects existing unregistered cache directories,
  symlinked cache parents and non-directory parent components before add runs.
- Verification requires the expected identity/source, a successful receipt,
  an absolute root in the previewed target's audited native store layout,
  a matching manifest name/version, exact payload hash and one enabled native
  inventory entry. The receipt's cache version must agree with inventory;
  it is checked separately from the package manifest version.
- The builder includes `receipts.py`. The bundle README describes the exact
  version boundary, stdout capture and remaining runtime limitations.

The result proves a native CLI write target plus effective enabled state at
the time of inspection. It does not establish the configuration layer that
owns that enabled state. Existing updates therefore remain blocked even if a
future inventory producer supplies apparent scope/root values.

## Verification evidence

| Check | Observed result |
| --- | --- |
| Initial new receipt tests against the previous implementation | 7 tests; 5 expected failures, 2 passed; exit 1 |
| Retained-result display / orphan-cache tests before their fixes | 3 tests; 2 expected failures, 1 passed; exit 1 |
| Cache-parent symlink test before its fix | 1 expected failure; exit 1 |
| `PYTHONPATH=runtime python3 -m unittest discover -s tests -p 'test_installer_codex_receipts.py' -v` | 10 passed; exit 0 |
| `PYTHONPATH=runtime python3 -m unittest discover -s tests -p 'test_installer_*.py'` | 52 cases: 51 passed, 1 skipped; exit 0 |
| `python3 -m unittest discover -s tests -p 'test_agent_skills_config.py'` | 15 passed; exit 0 |
| `python3 -m unittest discover -s tests -p 'test_plugin_packages.py'` | 14 passed; exit 0 |
| `python3 scripts/validate_skills_catalog.py --check` | exit 0 |
| Python AST parsing | passed for installer modules, builder and installer tests |
| R3 archive/input hashes | 26 input hashes and 22 packaged-file hashes matched; 23 entries |
| Local Markdown links / whitespace / JSON | 68 links in the 45-file review scope checked; passed |
| Gitleaks `dir` on review scope and unpacked R3 | no leaks found; exit 0 |
| Staged paths / original stashes | 0 staged; 4 stashes retained |

The 20 invalid-receipt/postcondition cases cover absent/malformed/wrong-shaped
JSON, missing/incorrect identity/path/version/auth policy, source conflicts,
disabled state, missing/symlinked roots, changed manifests/content and nonzero
native exit. Each checks failure reporting with one attempt and no automatic
uninstall. Other tests cover unknown CLI versions, config target changes,
ambiguous HOME configuration, existing installs, orphan caches and cache-parent
symlinks. Real temporary payload files and the actual interactive installer are
used; the external Codex process is replaced with a fixture. A separate real
subprocess fixture verifies JSON stdout capture and visible stderr.

The suite also covers existing Claude behavior and relocated bundle imports/
execution. The skipped case is the existing PowerShell process check: `pwsh`
is unavailable. It is not a passing Windows result.

The final receipt-only rerun after correcting the fixture's absent-stdout case
also passed all 10 tests. The review snapshot and scanner/check outputs are in
the ignored task directory
`.superpowers/sdd/2026-11-09-cross-platform-plugin-installer/r3-review-yur6bbf2/`.

The full repository discovery command and `build_plugins.py --check` were not
run: an unrelated server-build test/gate executes `npm ci`, which exceeds this
offline-only authorization. No npm command or package download ran. The
applicable installer, shared-config and package checks above passed; the full
repository suite is **NOT VERIFIED**.

## Same-session review

Self-review in same Codex session: commitment / recency / framing bias not fully controlled.

Reviewed with `quality-gates:code-review-codex`: installer models, host adapter,
planning, execution, receipt verification, UI, builder, changed execution/plan
tests, receipt tests and the bundle README. No unresolved findings remained
within this scope. This is a same-session native review, not an independent
agent or external reviewer.

Adversarial checks covered: receipt paths pointing into a marketplace;
cache-version/manifest-version confusion; stale target approval; an absent
inventory entry hiding an existing cache; symlinked target parents; partial
native writes; and a new CLI version with an unaudited schema. The orphan-cache
and symlink-parent cases initially reached add and were corrected before the
final suite. No personal files were involved in these reproductions.

RISK: L2 for the receipt/target boundary and preservation of existing files.
Completion evidence includes the targeted failure cases, installer regression
suite, shared-config/package checks and same-session review. This does not
authorize a commit or supply native platform acceptance.

## Local artifact

- File: `dist/agent-skills-installer-fe55c04-candidate-r3.zip`.
- Size: 43,603 bytes.
- SHA-256: `ef60a5747f81b90b967e11f5a0cf77536db21539d0bcb90c3d8b995f9b1b71e6`.
- R2 remains available with its original SHA-256. Its successful Claude native
  case applies to R2; it does not automatically establish R3 native behavior.
- R3 contains uncommitted runtime changes. Its HEAD alone is not a clean-source
  assertion; `provenance.json` records exact build inputs.

## VERIFIED / NOT VERIFIED

VERIFIED: the offline receipt flow, failure/preservation behavior, affected
regression checks and packaged inputs listed above. The red/green observations
show that the success and preservation tests detect missing behavior; success
is not inferred solely from a fixture's return code.

NOT VERIFIED: uninterrupted fresh end-to-end execution; default CODEX_HOME and
alternate symlink/canonicalization configurations; managed/project
configuration interactions; concurrent filesystem replacement between checks
and native writes; Windows/Linux native process behavior; hooks/MCP/skills;
other Codex versions; the full repository/server checks. The store-layout and
version assumptions are tied to the previously inspected `rust-v0.167.0`
producer, not generalized to future versions.

Subsequent [native run 1](macos-codex-r3-run-1.md) registered/downloaded the
source once, then stopped when its observer omitted a local Python probe.
An explicitly approved [continuation](macos-codex-r3-continuation.md) then
installed quality-gates once with native/installer exits 0 and exact payload
verification. Both sets of evidence remain available; no further native
operation is authorized by either completed run.
