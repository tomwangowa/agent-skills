# Proposed continuation after R3 observer refusal

Status: **APPROVED AND EXECUTED ONCE; native installation continuation passed**.
Date: 2026-11-10. See [continuation evidence](macos-codex-r3-continuation.md).
The [first native run](macos-codex-r3-run-1.md) is retained. This approval is
consumed and does not authorize another native operation.

## Purpose and exact change

Continue receipt verification with the same unmodified R3 artifact and existing
isolated source checkout. Correct only the observational command allowlist to
permit the installer's exact local Python 3.11+ probe. The installer product,
package payload and archive stay unchanged.

This is a new installer attempt after the original case stopped. It reuses
the isolated HOME/CODEX_HOME/XDG/TMP directories and outside-repository cwd;
it is **not** another fresh-empty-marketplace case. Keep new observer logs in
a separate continuation directory. Initial installed plugin inventory must
still be empty.

## Recheck before launch

- R3 archive SHA-256 must still be
  `ef60a5747f81b90b967e11f5a0cf77536db21539d0bcb90c3d8b995f9b1b71e6`.
- Existing isolated marketplace source must remain the full `tomwangowa`
  Git URL, at recorded commit `fe55c04bf9202fe82f1a68b7f5985305c82249f0`.
- Its selected payload must still hash to
  `bdd888a67f1728221208937bfc554efbd17fc19bdda1590697628eb40b05ed5c`.
- Codex must remain `0.167.0`, inventory empty, and the selected package cache
  absent. If any condition differs, stop before installation and report it.
- Repeat the named original `config.toml` before/after hash comparison without
  publishing its contents. Do not copy credentials or personal settings.

## Allowed operations and consequences

One mutation, at most once, after the installer's installation confirmation:

```text
codex plugin add quality-gates@tomwangowa --json
```

This copies/materializes the already downloaded local package into the isolated
plugin cache and writes isolated Codex user configuration. No new marketplace
download, registration or refresh is allowed. No write to a personal installed
plugin cache or production checkout is approved.

Allowed native inventory reads remain `codex --version`,
`codex plugin marketplace list --json` and
`codex plugin list --marketplace tomwangowa --json`; Claude version discovery
may report unavailable. The corrected observer also permits precisely:

```text
python3 -c "import sys; raise SystemExit(sys.version_info < (3, 11))"
```

No npm/package manager, update/upgrade, uninstall, model session, App Server
call, hook trust or another package is included. If a source/dependency
preparation prompt appears unexpectedly, cancel rather than approve it.
No new model/API invocation is requested; no extra download is intended.

## Acceptance and stop

Require the real installation receipt to name `quality-gates@tomwangowa`, its
path to lie in the previewed isolated CODEX_HOME, manifest version `0.2.0`,
exact installed hash and one enabled final inventory entry. Record native and
installer return codes plus actual writes. Preserve partial state on failure.

No retry or rollback is included. Hooks/MCP/all skills and uninterrupted
fresh end-to-end execution remain separate claims even if continuation passes.
The observer policy had offline checks before execution. The scope above is
preserved as the approved historical plan; results and remaining gaps are in
the continuation evidence linked at the top.
