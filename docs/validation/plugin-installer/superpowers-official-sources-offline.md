# Superpowers official-source offline evidence — R4

Status on 2026-11-10: **offline implementation verified within the scope below**.
The user approved the supplemental design and plan together with #1. Tasks 1–4
were implemented inline in this linked worktree; Task 5 produced proposals only.
The overall Superpowers installation/function delivery is **not complete**.
Native capability, unmodified candidate installation, restarted-host entries
and real behavior remain separate unverified gates.

## Behavior and evidence

- Schema 2 separates official catalog provenance from payload provenance.
  Claude `claude-plugins-official` targets observed manifest `7.0.0` and the
  pinned `obra/superpowers` Git payload; Codex `openai-curated` targets observed
  manifest `6.3.0` within its native-managed catalog. The raw selected entry
  hashes come from the reviewed public snapshot, not a fabricated native URL.
- Missing native Codex official state produces `/plugins` guidance, not
  marketplace-add/refresh or managed-state repair. Unknown provider-local
  state withholds Superpowers without poisoning unrelated known own packages;
  actual global inventory failure remains host-wide uncertainty.
- Every existing Superpowers provider is preserved, including newer `7.0.2`,
  disabled, duplicate or uncertain entries. No update, enable, downgrade or
  duplicate installation is offered. External defaults are validated unchecked.
- Exact native acceptance requires full CLI version/platform/architecture,
  selected catalog/entry, manifest version, expected complete tree hash and
  reviewed evidence reference. An unrelated historical catalog revision may
  differ, but the current verified revision and snapshot are sealed at consent.
- Source/install actions recheck provider and plugin state before mutation.
  Codex verifies the real receipt/root/enabled state, cache revision's eight
  SHA characters and separate manifest version; Claude checks pinned origin,
  user scope, manifest and complete content. Partial writes stay unverified,
  with a single attempt and no automatic retry/rollback.
- Real UI tests use temporary trees and process doubles. A pending Superpowers
  selection does not install its dependencies; an independent own package can
  install and still return a partial-result exit for pending Superpowers.
  Entry exposure and seven-workflow behavior are explicitly NOT VERIFIED.

Production `installer/provider-acceptance.json` is still `records: []`, and
both Superpowers expected payload hashes are unknown. This deliberately blocks
its source/install/dependency proposals in R4. No synthetic acceptance record
has been promoted into product metadata. The implementation does not convert
file presence or test success into native compatibility evidence.

## VERIFIED

Final checks on the current macOS arm64 / Python 3.12.1 tree:

| Check | Actual result |
| --- | --- |
| `PYTHONPATH=runtime python3 -m unittest discover -s tests -p 'test_installer_*.py'` | 83 cases: 82 passed, 1 PowerShell skip; exit 0 |
| `python3 -m unittest discover -s tests -p 'test_agent_skills_config.py'` | 15 passed; exit 0 |
| `python3 -m unittest discover -s tests -p 'test_plugin_packages.py'` | 14 passed; exit 0 |
| `python3 scripts/validate_skills_catalog.py --check` | exit 0 |
| Python AST / installer JSON and POSIX launcher syntax | 29 Python files parsed; JSON and syntax checks passed |
| Deterministic/exclusive ZIP and relocated subprocesses | installer bundle cases passed, including schema 2/provider runtime/empty acceptance after relocation |
| Archive CRC, file hashes and current input hashes | all 24 recorded file hashes and 28 recorded input hashes matched |
| `git diff --check` and staged-diff check | exit 0; nothing staged |
| Scoped Gitleaks `dir --redact` | source scope plus extracted R4; exit 0, no leaks found; final scope recorded in local evidence |
| Same-session native review | L2, `quality-gates:code-review-codex`; resolved findings and bias/gaps in [review](superpowers-official-sources-review.md) |

The skipped test requires `pwsh`, which is unavailable. It does not count as a
passing Windows/platform case. The original 52-case baseline also passed with
one PowerShell skip before this change. Expected red tests reproduced missing
provider/schema/gate behavior before implementation; later self-review fixes
have explicit red/green regressions. Native output fixtures were not replaced
with synthetic success data.

## Artifact and preservation

- R4 ZIP (local artifact; not included in the repository): **51,780 bytes**, 25 archive files,
  18 host/package catalog entries.
- SHA-256: `46994537305c0f97268aa9cfbed825378b9b485130ff25732b57a3b8e304a549`.
- Catalog schema 2; provenance schema 1 and dependency schema 1 remain distinct.
- Baseline HEAD: `fe55c04bf9202fe82f1a68b7f5985305c82249f0`.
  This is a dirty-worktree build; HEAD alone does not describe its inputs.
- R3 ZIP remains byte-identical, SHA-256
  `ef60a5747f81b90b967e11f5a0cf77536db21539d0bcb90c3d8b995f9b1b71e6`.
  R3 native evidence stays scoped to R3, not this changed runtime.
- Four original stashes remain. No current-branch stage/commit/push, plugin
  payload edit, installed-cache/private-config write, host download/install,
  model session or delegation occurred in this offline implementation.
- Local effects are source/tests/docs, ignored verification artifacts, the
  exclusive R4 ZIP and empty isolated Claude probe directories. Fixture Git
  repositories/commits and fake native processes are test-only local effects.

Local detailed logs and metadata are under
`.superpowers/sdd/2026-11-10-superpowers-official-sources/`, including
`installer-suite-release.log`, `r4-artifact.json`, `scan-scope.json`,
`gitleaks-r4.json` and the task ledger. Historical R2/R3 files were preserved.

## NOT VERIFIED and next gates

- **New official-source native capability:** no direct native probe ran; no
  real materialization/tree hash has been accepted. See the concrete
  [Claude-first native proposal](superpowers-native-acceptance-proposal.md)
  and [binary/environment/one-attempt manifest](superpowers-native-case.json).
- **Unmodified candidate installation:** after capability evidence, target
  hashes/records need review and a new exclusive candidate needs a separate
  approved run. Capability success cannot establish candidate success.
- **Codex native official setup:** no verified fresh initialization path is
  authorized. Do not copy or seed managed `.tmp/plugins`, `.tmp/plugins.sha`
  or caches as a substitute. This prerequisite remains unresolved.
- **Exposed entries and behavior:** no restarted model host, seven workflow
  normal/failure cases, delegation, hook trust, MCP or integration was run.
  The [functional proposal](superpowers-function-acceptance-proposal.md)
  records the matrix; exact model/budget/fixture manifests still need approval.
- **Other platforms/CLI/architectures:** Windows PowerShell and native
  Windows/Linux/other architectures remain unverified. Host-specific versions
  do not inherit maintainer-provider or another platform's acceptance.
- **Repository-wide server/release gates:** full server tests and
  `build_plugins.py --check` execute `npm ci`; they were not run under offline
  approval. No release/publishing claim is made.
- **Independent/concurrent verification:** review stayed in this session by
  approved choice. Concurrent native-state/ref changes inside a command cannot
  be made atomic by these checks; mismatches yield retained partial state.
