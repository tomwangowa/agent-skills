# Proposed R3 native Codex installation

Status: **EXECUTED ONCE; stopped by observer before plugin installation**.
Date: 2026-11-10. Source-add exited 0; plugin-add was never attempted.
See [run-1 evidence](macos-codex-r3-run-1.md). This approval is consumed; the
[separate continuation](native-codex-r3-continuation-proposal.md) requires approval.

## Objective and artifact

Run the unmodified extracted R3 installer on macOS arm64 with Codex CLI
`0.167.0`, selecting only `quality-gates@tomwangowa` (`0.2.0`). Prove that the
real add receipt, actual copied package and effective inventory agree in a
fresh configuration. This does not validate existing updates or Superpowers.

Artifact: `dist/agent-skills-installer-fe55c04-candidate-r3.zip`, 43,603 bytes,
SHA-256 `ef60a5747f81b90b967e11f5a0cf77536db21539d0bcb90c3d8b995f9b1b71e6`.
Verify this hash before extracting; retain the archive and evidence afterward.

## Isolation and expected effects

Create fresh HOME, CODEX_HOME, XDG_CONFIG_HOME and TMPDIR directories under a
new ignored task-evidence root. Use a separate fresh working directory outside
all repositories, so no project instructions/settings are inherited. Use a
minimal environment with the actual CLI/Python/Git binaries on PATH, not copies
of personal settings, credentials or login state. Do not run a model session.

Expected writes are the isolated marketplace checkout, Codex user config and
plugin cache, plus local installer/evidence files. No writes to installed
personal plugin caches, production worktrees, global dependencies or the source
repository are allowed. Hash the original Codex `config.toml` before/after
without publishing its contents; this check covers that file only.

One marketplace-add operation downloads the public repository using `main`.
There is no model/API invocation or dependency installation. Git/network access
still occurs. The branch can move: record the downloaded commit and require
the installer catalog's exact payload hash; stop on mismatch.

## Native commands and attempt limits

The extracted interactive installer may issue these mutation vectors, once
each, only after its corresponding explicit confirmation:

```text
codex plugin marketplace add https://github.com/tomwangowa/agent-skills.git --ref main --json
codex plugin add quality-gates@tomwangowa --json
```

Allowed inventory vectors are `codex --version`,
`codex plugin marketplace list --json`, and
`codex plugin list --marketplace tomwangowa --json`, repeated as needed for
preconditions/postconditions. The installer may also probe `claude --version`
during host discovery, but Claude is not selected and no Claude mutation is
allowed. Unqualified Codex plugin listing is not allowed.

Use observational command logging that delegates the real subprocess call;
do not synthesize receipts or replace inventory. Reject any mutation outside
the vectors above or a second attempt. Do not call update/upgrade, uninstall,
reconcile, App Server methods, hook-trust actions or package managers. If a
login or unexpected permission/configuration prerequisite appears, stop and
report it rather than copying credentials or trying another installation.

## Required evidence and stopping conditions

- Record actual OS/architecture, CLI/Python versions, archive hash, command argv,
  return codes and installer exit code. Version other than `0.167.0` stops the
  case before source preparation; no version adaptation is approved here.
- Initial isolated plugin inventory is empty. Preview shows the isolated
  CODEX_HOME. Add returns one qualified receipt with a real installed path.
- Final scoped inventory has one enabled `quality-gates@tomwangowa`. Receipt
  cache version agrees with it; actual manifest version is `0.2.0`; installed
  payload hash equals the catalog. No plugin scope is inferred from a cache.
- Record actual isolated writes and whether the original checked config hash
  stayed unchanged. Preserve partial state on any failure.
- No retries, rollback or further provider/package test is included. A failed
  external operation requires fresh user approval before another attempt.

Installation verification does not authorize or demonstrate hook execution,
MCP availability or every skill. Those remain separate acceptance work.
