# Claude official-source native capability: partial result

Status: **NATIVE INSTALL SUCCEEDED; SOURCE CONTRACT NOT ACCEPTED**.
The user selected #1 to approve the corrected capability proposal. Source-add
and plugin-install each ran exactly once and exited 0 in the approved isolated
case. No external action was retried. This is not a passed capability gate,
unmodified installer acceptance or functional/model result.

## VERIFIED

| Observation | Actual result |
| --- | --- |
| Platform / architecture | macOS / arm64 |
| Full CLI version | `2.1.321 (Claude Code)` |
| Approved binary SHA-256 | `abc9feeeca8091d51b623291e044cf0528c2f6b74e0c1d6ef671d52c73f7cd3c`, matched |
| Source-add / install | each attempted once; each exit 0 |
| All seven native read commands | exit 0 |
| Marketplace | `claude-plugins-official`, native Git URL matches approved source |
| Before-install Git origin | `https://github.com/anthropics/claude-plugins-official.git` |
| Before-install catalog HEAD | `dceb15d50832e6adf380bedc26dde03d251324b9` |
| Selected raw entry hash | `d85f0111dd6cfcd54268f46dbadbd54d4df344c160cda075134e2d35aae9f888`, unchanged after native operations |
| Pinned payload / native registry `gitCommitSha` | `bb92a77741419a4ab5f06e711a283343f1ada0c3`, exact match |
| Native manifest / effective inventory version | `7.0.0` / `7.0.0` |
| Effective state | enabled `true`, scope `user` |
| Actual installed content | 238 files, no symlinks; all paths/sizes/SHA-256 values recorded |
| Observed complete installed-tree hash | `d9ae919521df6591becf75601b64bd6e9ca358e389bbe95050f966555a7ef704` |
| Required seven skill files | present; this establishes files only |
| Protected personal-state fingerprints | `settings.json`, `plugins/installed_plugins.json`, `plugins/known_marketplaces.json` unchanged |
| Model / delegated-agent calls | 0 / 0 |

The two approved mutation vectors were:

```text
claude plugin marketplace add https://github.com/anthropics/claude-plugins-official.git --scope user --json
claude plugin install superpowers@claude-plugins-official --scope user --json
```

The native install JSON reports `command: install`, `outcome: ok`, plugin ID
`superpowers@claude-plugins-official` and user scope. The installed root came
from native inventory and was verified inside the approved isolated Claude
config. No writes were made by the observer to that plugin cache.

## Source representation changed

Before installation, local Git origin and HEAD were available and the actual
runtime adapter returned `ready`. After installation plus subsequent native
inventory reads, the same official marketplace directory no longer contained
`.git`. It instead contained `.gcs-sha` with exactly the previously verified
catalog HEAD:

```text
dceb15d50832e6adf380bedc26dde03d251324b9
```

The selected raw Superpowers entry and pin remained unchanged. The native
marketplace listing still declared the approved Git URL. The current adapter,
however, explicitly requires `.git/config` and HEAD to corroborate a Claude
configured Git catalog. Reinspection therefore returned unverified with
`Missing or unsafe source: .git/config`, and the observer stopped that gate.

The specific native vector causing this transition was **not isolated**:
filesystem representation was first checked after installation and the three
post-install reads. Do not claim that `plugin install` alone caused it, or that
this behavior is understood for all versions. A `.gcs-sha` filename/value alone
is not sufficient proof for a new trust path. The observed payload hash is
likewise not an independent comparison against a separately approved pinned
upstream tree.

This invalidates the offline assumption that an official Claude Git catalog
retains Git metadata throughout the native flow. The existing refusal is
preserved; no ignore rule, fake Git metadata, source repair, rollback or
permissive acceptance was introduced. A follow-up needs to review how native
archive provenance can be corroborated, define an explicit source contract and
add failure cases before enabling this path. This probe does not authorize
that implementation or another external operation.

## Effects, preserved state and artifacts

The native commands downloaded the official catalog and pinned payload and
wrote marketplace state, registry, enabled setting and cache in the isolated
case. Partial native state remains for review. No model session, hook trust,
actual skill execution, existing personal provider update, Codex operation,
current-branch stage/commit/push or publishing was performed.

Raw evidence remains under
`.superpowers/sdd/2026-11-10-superpowers-official-sources/native-claude-capability-r2-vud_frdl/evidence/`:

- `commands.jsonl`, `state.json`, native stdout/stderr for every vector;
- before/after normalized inventory and selected entry;
- `installed-files.json` for every actual payload file;
- `materialization-observation.json`, including native registry pin evidence.

The execution workspace also contains `native-claude-r2-result.json`.
Anonymized observed fixtures preserve the genuine outputs and partial result:

- `tests/fixtures/installer/observed-claude-superpowers-official.json`;
- `tests/fixtures/installer/observed-claude-superpowers-install.json`;
- `tests/fixtures/installer/observed-claude-official-catalog-transition.json`.

The original preflight and corrected approval manifests remain unchanged.
Production acceptance records remain empty and expected payload hashes remain
unknown; the observed hash has not been promoted into an accepted target.
R4 and its runtime/metadata inputs remain unchanged. No product fix or new
archive is part of this capability attempt.

## NOT VERIFIED

- Claude native archive provenance and the precise transition trigger;
- independent pinned-tree/content-contract comparison and a reviewed native
  acceptance tuple;
- an unmodified candidate installer run after an approved adapter change;
- exposed entries in a restarted model host and all seven real workflow normal/
  failure branches, hooks/MCP, delegation or integration;
- Codex, other CLI versions/platforms/architectures;
- personal state beyond the three explicitly protected files, or arbitrary
  filesystem/network side effects not independently instrumented.

The next recommended step is the [offline source-contract investigation/design](superpowers-archive-source-investigation-proposal.md),
using this observed fixture and without changing native files. A new source or
install attempt must have a fresh concrete proposal and approval.

## Local report checks

Nine recorded native vectors were independently counted: one source-add, one
install and seven allowed reads; all command exits were zero, while the case
verdict remains partial. Every one of the 238 installed-file hashes was retained;
three protected fingerprints still matched at the final check. R4 SHA-256 and
all 28 archived input hashes matched the unchanged product tree. JSON and local
links validated, `git diff --check` passed, nothing was staged, and scoped
Gitleaks found no leaks in the changed report/observed-fixture files. These
checks do not upgrade the unsupported source contract or establish behavior.
