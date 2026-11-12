# R3 macOS Codex native continuation

Date: 2026-11-10 (Asia/Taipei). Status: **ONE NATIVE INSTALLATION CASE PASSED**.
Codex `0.167.0` installed `quality-gates@tomwangowa` `0.2.0` in the existing
isolated environment. Native add, installer and final scoped inventory all
exited 0. Independent file/hash checks corroborated the installer's result.

This is the explicitly approved continuation of the
[observer-stopped first run](macos-codex-r3-run-1.md). It is not an uninterrupted
fresh-empty-marketplace run or full cross-platform/plugin-function acceptance.

## Artifact and isolation

- macOS `26.6.2`, arm64; Codex CLI `0.167.0`; Python `3.12.1`.
- Unmodified R3 ZIP, 43,603 bytes; SHA-256
  `ef60a5747f81b90b967e11f5a0cf77536db21539d0bcb90c3d8b995f9b1b71e6`.
  Its 22 packaged-file hashes matched before execution and after inspection.
- Reused the previous isolated HOME/CODEX_HOME/XDG/TMP and working directory
  outside all repositories. Personal settings and credentials were not copied.
- Source remained commit `fe55c04bf9202fe82f1a68b7f5985305c82249f0`, already
  downloaded in the first run. Its selected package hash was checked before
  continuation. Initial scoped installed inventory was empty and the selected
  plugin cache was absent.
- The corrected observational wrapper delegated real subprocess calls, allowed
  the exact local Python version probe and rejected source-add/refresh operations.
  The extracted installer/runtime was not patched or replaced.

## Actual operations and result

Only one mutation was attempted, once:

```text
codex plugin add quality-gates@tomwangowa --json
```

The installer preview showed the isolated CODEX_HOME and selected only
quality-gates. No source/dependency preparation was requested. There was no
source registration, refresh or download command in this continuation, no
observer refusal and no retry/rollback. Inventory reads were qualified to
`tomwangowa`; no unqualified catalog listing was used.

| Evidence | Actual result |
| --- | --- |
| Native add exit | 0 |
| Installer exit | 0 |
| Final scoped inventory exit | 0 |
| Receipt identity | `quality-gates@tomwangowa` |
| Receipt/cache version | `0.2.0` |
| Actual plugin manifest name/version | `quality-gates`, `0.2.0` |
| Receipt auth policy | `ON_INSTALL` |
| Installed path relative to isolated CODEX_HOME | `plugins/cache/tomwangowa/quality-gates/0.2.0` |
| Installed files compared with source | 25 files, identical relative paths and per-file SHA-256 values |
| Installed payload SHA-256 | `bdd888a67f1728221208937bfc554efbd17fc19bdda1590697628eb40b05ed5c` |
| Catalog/source/installed hash agreement | exact match |
| Final installed inventory | one entry, `installed: true`, `enabled: true` |
| Source identity in inventory | full `https://github.com/tomwangowa/agent-skills.git` URL |
| Isolated user config | `plugins."quality-gates@tomwangowa".enabled = true` |
| Original personal Codex `config.toml` | SHA-256 unchanged before/after |

The actual native add receipt had all six producer fields: `pluginId`, `name`,
`marketplaceName`, `version`, `installedPath`, `authPolicy`. Its installed path
was checked against the previewed isolated target; it was not inferred from
the marketplace's source path. No plugin scope was invented from the cache.

Observed persistent writes include the new isolated package cache and isolated
user configuration enabling it. The prior source checkout/registration remains.
This is a bounded operation/config-file check, not a whole-machine filesystem
or network audit. No model session, hook-trust action, dependency install,
App Server operation, update, uninstall or additional package was invoked.

## Evidence and fixture

Ignored continuation evidence:
`.superpowers/sdd/2026-11-09-cross-platform-plugin-installer/native-codex-r3-continuation-g7dd8t41/`.
It contains `run.json`, `preflight.json`, `observe.py`, `commands.jsonl`,
`terminal.log`, `result.json` and independently checked `verified.json`.
The original failed run and its logs remain intact; the shared isolated state
now also contains this continuation's actual installed package.

The complete native receipt, with only its installed path anonymized, is saved
as `tests/fixtures/installer/observed-codex-add.json`. The existing receipt tests
now use this observed format rather than reconstructing the six fields. This
test/fixture change does not alter R3 runtime or build inputs.

After adopting the observed receipt fixture,
`PYTHONPATH=runtime python3 -m unittest discover -s tests -p 'test_installer_codex_receipts.py' -v`
passed all 10 tests (exit 0). The prior full installer suite remains the
recorded 52-case R3 offline baseline; it was not repeated for a fixture-only
change.

## VERIFIED / NOT VERIFIED

VERIFIED: one actual Codex add with the native receipt schema; explicit isolated
CODEX_HOME store path; actual package manifest and all 25 payload files;
effective enabled inventory and isolated user config; native/installer exit
codes; the named original config unchanged; no source mutation in continuation.

NOT VERIFIED: an uninterrupted fresh end-to-end R3 case; default CODEX_HOME or
alternate symlink/canonicalization configurations; project/managed overrides
and ownership for updates; other packages/Codex versions; Windows/Linux native
behavior; hooks, MCP and all skill execution; the full repository/server checks.

Assumptions checked independently: a zero exit alone could hide a wrong package
(actual manifest/files/hash were checked); source path could be mistaken for
installed path (receipt root lies in the cache and bytes match); a valid package
could remain disabled (native inventory and isolated config both enable it).
No compatibility claim is extended beyond this case.

The original first run contributed one source-add attempt. This continuation
contributed one plugin-add attempt; neither mutation was retried. Further native
operations require a new selected scope and approval.
