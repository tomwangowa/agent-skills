# R7 native installation and rerun acceptance

Date: 2026-11-11. **The exact R7 ZIP passed all three approved native cases and
all three reruns on macOS arm64.** All six installer invocations exited 0.
This is actual candidate installation, not only CLI capability or synthetic
inventory replay. R7 bytes remain unchanged: 56,060 bytes, SHA-256
`d598a8170b57ba27a29a1ecdcbef3c450ec0acf4f25c9a4edca8f864f8b0f4ea`.

## VERIFIED

| Case | CLI | First native installation | Rerun | Installed content |
| --- | --- | --- | --- | --- |
| Claude, no account | 2.1.322 | Exit 0; Superpowers 7.0.0 enabled, user scope | Exit 0; zero mutation attempts | 238 files |
| Claude, signed in | 2.1.322 | Exit 0; Superpowers 7.0.0 enabled, user scope | Exit 0; zero mutation attempts | 238 files |
| Codex, no account | 0.167.0 | Exit 0; API-curated Superpowers 6.3.0 enabled | Exit 0; zero mutation attempts | 73 files |

Each rerun kept the installed path/cache version, complete file bytes and
executable modes, enabled state and native registry/settings fingerprints
identical to the first run's saved state. Each profile has exactly one
Superpowers cache directory; each Claude registry has one user-scope entry
at pin `bb92a77741419a4ab5f06e711a283343f1ada0c3`. No update, enable, remove,
source-add or install was attempted on rerun, and no budget guard blocked one.

Installed content/modes were independently compared to committed Git blobs:
the already fetched independent Claude upstream pin above, and Codex's actual
native catalog commit `d420d13051bffe4543ed39e30fa46b87148e47dd`. Complete
content hashes match R7's expected targets: Claude
`d9ae919521df6591becf75601b64bd6e9ca358e389bbe95050f966555a7ef704` and Codex
`2bc88a8ad42d3b2a5f2b7f0b6711b0ae4d18895bfa870dcfeb7c9fc5d31fdba0`.

Native auth status was checked before and after both invocations per Claude
profile. No-account stayed false/`none`; signed-in stayed true/`claude.ai`.
Expected unauthenticated status exits were 1, authenticated status exits 0;
these are separate from the six successful installer exits. One new isolated
native browser login completed successfully. No credentials were copied from
an existing profile or filled by the observer; only non-secret auth status
fields were retained in observer reports. Native authentication storage remains.

Codex retained the synthetic company provider fields and created no account
auth file. Its one native catalog startup exited 0 after only `initialize` and
`initialized`, without a thread/turn. The endpoint was deliberately `.invalid`
with a dummy environment key; no real company connectivity was tested.

## Operations and instrumentation

The [approved scope](r7-native-acceptance-proposal.md) consumed two Claude source
adds, three plugin installs, one Codex native catalog startup, one isolated
Claude login and six R7 invocations. No command was retried. No model request
was sent by the observer. Downloads reached the approved official services;
these are command counts, not wire requests or native internal transport counts.

The unchanged `install.py` ran under a PTY menu driver and Python subprocess
audit hook. Arguments were logged without environment values; the hook enforced
the approved budget. Real installed host executables handled every call, with
no fake CLI or replaced runtime function. There were zero blocked commands.
Native write success was checked by the stock installer and corroborated by
separate final native inventories/content. The ledger records launches, not an
independent per-child exit trace. All native working directories were outside Git.

The signed-in profile used real HOME for native OS integration with a separate
CLAUDE_CONFIG_DIR; the other profiles used fresh HOME/config/cache directories.
All downloaded/native files, logs and test authentication are retained; no
cleanup or logout ran. The Python entry was exercised, not OS shell launchers
end to end. No model, workflow or hook-trust request was added.

## Independent verification and preservation

Evidence root:
`.superpowers/sdd/2026-11-11-r7-native-acceptance/prepared-9am00ufx/`.
It retains frozen specifications, once markers, subprocess ledgers, PTY
transcripts/input events, sanitized auth observations, native inventories,
first-run state snapshots, per-phase results and native catalog setup output.
The local-only `verify_batch_local.py` returned exit 0 after checking all six
results, live installed bytes/modes/settings, unique cache/registry entries,
committed Git content, packaged file hashes and original-state fingerprints.
It launches no native host or network operation. Published summary:
[r7-native-acceptance-evidence.json](r7-native-acceptance-evidence.json).

All 76 protected prior files, four named original personal settings, old ZIPs
including R7, HEAD, four stashes and staged list are unchanged. The validation
index was intentionally updated before approval. An initial one-off checker
omitted that documented exception and stopped on the index; the changed-path
set contained only that expected document. The corrected check passed with no
native repeat or product/archive edit. No commit, push or publication occurred.

Adversarial checks required actual first-install ledgers and committed content;
zero attempted rerun mutations plus identical native state; observed auth
before/after; and original-state preservation. A no-op installer or a blocked
reinstall would fail these checks. Exit 0 alone was not accepted as proof.

## Other requested checks and NOT VERIFIED

The [offline matrix](r7-existing-install-preservation.md) adds 29 scenarios / 58
runs for older/newer versions, disabled/alternate providers and malformed
inventory. Those combinations remain offline evidence; the native reruns here
use the versions just installed.

`secure-ai-development-gate` is present in agent-skills **quality-gates 0.2.0**
for both hosts and both R7 catalog entries. Package mapping, native manifests
and actual skill files were checked. This batch selected only Superpowers;
quality-gates was not reinstalled or functionally exercised here.

Not verified: Windows/Linux and other versions/architectures; Codex account-backed
main/remote catalogs; actual company endpoint/network policy; native older/newer/
disabled/alternate-provider cases; full package coexistence; OS launchers end to
end; workflow/hook/model behavior; complete OS/network/keychain or billing audit.
Named-file preservation does not cover every possible host-state change.

R7 is natively accepted for these three macOS/Python-entry cases. The original
complete cross-platform delivery still has the gaps above. No ZIP rebuild or
capability-record rewrite was performed to obtain this result.
