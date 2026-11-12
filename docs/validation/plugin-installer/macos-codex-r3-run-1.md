# R3 macOS Codex native run 1

Date: 2026-11-10 (Asia/Taipei). Status: **STOPPED BEFORE PLUGIN INSTALLATION**.
The approved source-add operation succeeded once; the observation harness
then refused a local Python version probe. Plugin receipt verification remains
**NOT VERIFIED**. No external retry or automatic rollback occurred.

## Actual environment and scope

- macOS `26.6.2`, arm64; Codex CLI `0.167.0`; Python `3.12.1`.
- Unmodified extracted R3 archive: 43,603 bytes, SHA-256
  `ef60a5747f81b90b967e11f5a0cf77536db21539d0bcb90c3d8b995f9b1b71e6`.
  All 22 hashed packaged files matched before execution.
- Fresh HOME, CODEX_HOME, XDG_CONFIG_HOME and TMPDIR under the ignored task
  evidence directory; clean environment; working directory in `/private/tmp`
  outside all repositories. No private settings or credentials were copied.
- Only Codex and `quality-gates@tomwangowa` were selected. Dependency install,
  model sessions, hook authorization, App Server operations and other packages
  were not selected or executed.

The actual CLI was used; observations delegated to real `subprocess.run`.
The wrapper restricted commands and attempts but did not synthesize inventory
or installation results. The unpacked installer/runtime was not edited.

## Observed result

| Operation/evidence | Result |
| --- | --- |
| Initial configured marketplace list | empty |
| `codex plugin marketplace add https://github.com/tomwangowa/agent-skills.git --ref main --json` | one attempt, exit 0 |
| Registered identity/source | `tomwangowa`, Git URL `https://github.com/tomwangowa/agent-skills.git` |
| Downloaded commit | `fe55c04bf9202fe82f1a68b7f5985305c82249f0` |
| Downloaded quality-gates payload hash | `bdd888a67f1728221208937bfc554efbd17fc19bdda1590697628eb40b05ed5c`; matches R3 catalog |
| Last scoped installed inventory | empty |
| `codex plugin add quality-gates@tomwangowa --json` | **0 attempts** |
| Selected plugin's isolated cache directory | absent |
| Instrumented process exit | 1 |
| Installer normal return code | none: observer exception escaped before normal completion |
| Original personal Codex `config.toml` SHA-256 | unchanged before/after |

The source checkout and marketplace registration remain in the isolated
CODEX_HOME. The observed marketplace root is `codex/.tmp/marketplaces/tomwangowa`
relative to the run directory. The original config comparison covers that
single named file; it is not a whole-machine filesystem audit.

## Cause and correction boundary

The installer performs this existing local dependency probe:

```text
python3 -c "import sys; raise SystemExit(sys.version_info < (3, 11))"
```

The observation wrapper's allowlist included native plugin commands but omitted
this read-only Python probe. It raised `RuntimeError` before the probe ran,
after successful source preparation and before the installation preview. This
is a harness defect introduced for this run, not evidence that R3 installation
or Codex receipt handling failed. Those branches were never reached.

The failed wrapper and all original evidence are retained unchanged. A separate
continuation wrapper now allows that exact Python probe and **forbids any
marketplace add/refresh/update**, reusing the verified downloaded source. Its
only allowed mutation is one quality-gates add. It has not been used for a
native run.

Offline checks reproduced the original refusal, then executed the local Python
probe successfully under the corrected policy. Six unapproved command vectors
were rejected before execution, including source-add, npm, unqualified listing
and another package. A process double checked the one-attempt install budget;
no Codex CLI was called by those checks. An initial checker omitted its
`completed` test namespace and raised `NameError`; the corrected checker exited
0. This checker error had no native operation or product-code effect.

## Evidence and remaining acceptance

Original ignored evidence:
`.superpowers/sdd/2026-11-09-cross-platform-plugin-installer/native-codex-r3-gphqu3ei/`.
It contains `run.json`, `observe.py`, `commands.jsonl`, `terminal.log`,
`result.json`, `inspection.json`, the extracted artifact and isolated state.

Prepared, unexecuted continuation:
`.superpowers/sdd/2026-11-09-cross-platform-plugin-installer/native-codex-r3-continuation-g7dd8t41/`.
Its `offline-policy-checks.json` records the local policy checks. The failed
native run's logs are not overwritten by preparation or by a future continuation.

VERIFIED: one isolated native source registration/download; source identity,
commit and expected package content; no plugin-add attempt; the named original
config file unchanged; corrected observer policy checks without native calls.

NOT VERIFIED: a real plugin-add receipt, actual installed payload/state,
uninterrupted fresh end-to-end R3 execution, native CODEX_HOME cache-root
canonicalization, hooks/MCP/skills, other platforms/providers/versions.

An explicitly approved [continuation later passed](macos-codex-r3-continuation.md)
with one plugin-add and no repeated source-add. The result above remains the
historical first-attempt outcome; the shared isolated cache now contains that
continuation's installed package. The original stop/no-retry condition was
honored before renewed approval; neither run authorizes another native action.
