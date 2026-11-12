# R5 remaining-package installation results

Date: 2026-11-11. Result: **14 OF 14 INSTALLATIONS VERIFIED**.
The user approved the [whole batch](r5-remaining-packages-proposal.md). The
unchanged R5 installer installed and enabled eight Claude packages and six
Codex packages in fresh, separate test settings. No selected item failed,
was skipped or remained unverified.

## VERIFIED

Environment: macOS 26.6.2 arm64, Python 3.12.1; Claude Code
`2.1.322 (Claude Code)` and `codex-cli 0.167.0`.

Every selected native install exited zero, and both installers and their final
native inventories exited zero. Independent checks confirmed the declared
manifest versions, enabled state, intended isolated installed roots, complete
relative file lists and every file's SHA-256 against the downloaded source and
R5's expected aggregate hashes.

| Package | Version | Claude files matched | Codex files matched |
| --- | --- | --- | --- |
| technical-decisions | 0.1.3 | 50 | 50 |
| repo-workflow | 0.3.0 | 26 | 26 |
| content-tools | 0.2.0 | 62 | 62 |
| work-journal | 0.2.0 | 3665 | 3665 |
| session-preferences | 0.1.4 | 31 | 31 |
| skill-toolbox | 0.1.3 | 30 | 27 |
| handoff-mod | 0.2.2 | 50 | Claude only |
| attention-mod | 0.6.1 | 61 | Claude only |

Totals: 3,975 installed files compared for Claude, 3,861 for Codex; 7,836 file
comparisons in this batch. Claude reported user scope for every selected
package. Codex's actual JSON receipts supplied the installed cache roots, and
the final inventory plus isolated config corroborated enabled state; no scope
was invented for Codex.

With the [earlier quality-gates cases](macos-r5-native-results.md), R5 now has
successful installation evidence for all 16 own host/package pairs: nine on
Claude and seven on Codex, across separate cases. Quality-gates was not selected
in this batch, so this is not a test of all packages together in one config.

## Actual downloads and writes

Each host added the public own marketplace once; all 14 selected installs ran
once. The exact 16 vectors, native exits, per-package hashes and results are
in [macos-r5-remaining-evidence.json](macos-r5-remaining-evidence.json).
No failed or successful command was retried. Both cases started with an empty
native marketplace inventory and fresh test config directories.

Source registration, downloaded repositories, installed caches and enabled
state were written inside those directories and retained. The installer made
its approved surrounding inventory/tool probes, plus one final native inventory
per host. All observed subprocess vectors matched the approved native reads,
local Python probe or exact mutation list; no package-manager, model-session,
update, refresh, uninstall, rollback or hook-trust command ran.

R5 remained 51,800 bytes with SHA-256
`3047be151e9e89644a35d6542356badf90bf4e34dd3f7497d14a13c05a932ace`.
All 24 packaged-file fingerprints matched before and after each flow. No
installer, plugin payload or acceptance-index code/data was changed to obtain
these results. No commit, push or publication occurred.

## Deliberately skipped configuration

Optional journal-location setup was declined on both hosts; no activity/note
contents were read or moved and no journal settings file was created there.
Claude also reported three handoff-mod userConfig options and one attention-mod
option unset. No configure command or feedback-recipient setting was supplied.
The modules installed successfully, but their personal setup and later session
behavior were not exercised. No conversation, attention panel, MCP function or
skill was started as a functionality test; no model token cost was incurred by
an explicitly launched model session.

## Evidence and preservation

Detailed retained state:
`.superpowers/sdd/2026-11-11-r5-remaining-packages/prepared-fwh91yoc/`.
Each host has its approved menu/package plan, unmodified extracted R5, start
marker, native `commands.jsonl`, installer output, tool transcript, downloaded
source fingerprints, final inventory, exit result and independent verification.
Claude's native terminal JSON receipts and all six Codex captured add receipts
were retained. The recorder delegates real subprocess calls and preserves their
return values; it does not fabricate CLI responses or installer decisions.

The four original named settings/registry files had unchanged existence/link/
hash fingerprints. All 25,123 fingerprinted pre-run files were unchanged before
documentation updates, including product inputs, all five ZIPs, earlier test
cases and saved evidence. HEAD, staged state and four stashes were unchanged.
The new case directories, external working directories, partial-capable logs
and installed files were kept; no automatic cleanup was performed.

These are bounded checks of the recorded files and subprocesses, not a
whole-machine filesystem or native internal network/process audit.

## NOT VERIFIED

- Windows/PowerShell, Ubuntu/Debian and other architectures; Superpowers.
- Actual skills, hooks, MCP startup, model workflows and restarted-host entries.
- Journal/mod personal configuration, updates/migration, missing-tool installs
  and real user data workflows.
- All nine Claude/seven Codex own packages together in one config: the earlier
  quality-gates cases and this batch deliberately used separate directories.
- Elimination of remote-ref races or all native side effects.
- Full repository/server gates that can execute `npm ci`; no product code
  changed in this installation-only batch, so they were not rerun.

This completes the approved remaining-package installation batch. It does not
complete three-platform delivery or authorize another external operation.
