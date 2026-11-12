# R5 macOS native installation results

Date: 2026-11-11. Result: **TWO SINGLE-PACKAGE INSTALLATION CASES VERIFIED**.
The user approved the [exact scope](r5-native-acceptance-proposal.md), then the
unchanged R5 installer installed and enabled `quality-gates@tomwangowa` 0.2.0
once on Claude Code and once on Codex. This is not full feature/release acceptance.

## VERIFIED

| Evidence | Claude Code | Codex |
| --- | --- | --- |
| OS / architecture / Python | macOS 26.6.2 / arm64 / 3.12.1 | macOS 26.6.2 / arm64 / 3.12.1 |
| Actual displayed CLI version | 2.1.322 (Claude Code) | codex-cli 0.167.0 |
| Source preparation attempts | 1 | 1 |
| Plugin installation attempts | 1 | 1 |
| Installer exit | 0 | 0 |
| Final native inventory exit | 0 | 0 |
| Installed identity / manifest version | quality-gates@tomwangowa / 0.2.0 | quality-gates@tomwangowa / 0.2.0 |
| Effective installed/enabled state | enabled, user scope | installed and enabled; no scope inferred |
| Installed root, relative to isolated host config | plugins/cache/tomwangowa/quality-gates/0.2.0 | plugins/cache/tomwangowa/quality-gates/0.2.0 |
| Files independently compared | 27 | 25 |
| Complete installed content matches R5 and downloaded source | yes | yes |

R5 remained 51,800 bytes with SHA-256
`3047be151e9e89644a35d6542356badf90bf4e34dd3f7497d14a13c05a932ace`.
All 24 embedded file fingerprints matched before and after each case. The
launcher only set clean environment/cwd and executed the original entry; it did
not replace the installer, native command runner or CLI responses.

The downloaded selected payload was independently fingerprinted before approving
each installation. Afterward, every installed relative path and file digest
matched that source snapshot and R5's expected aggregate hash:

- Claude: `a7c6e396a54fa316a837bd3cc7479254cadb4b09672475649820720eca81add3`.
- Codex: `bdd888a67f1728221208937bfc554efbd17fc19bdda1590697628eb40b05ed5c`.

Exactly one selected plugin appeared in each final inventory. The installed
roots were inside the intended separate test settings directories. Codex's
receipt verifier printed the installed root; an independent check confirmed
that root's actual manifest/files and the isolated config's enabled entry.
Claude explicitly reported user scope. No scope was invented for Codex.

## Actual external operations

Each command ran once, under its corresponding isolated settings:

```text
claude plugin marketplace add https://github.com/tomwangowa/agent-skills.git --scope user --json
claude plugin install quality-gates@tomwangowa --scope user --json
codex plugin marketplace add https://github.com/tomwangowa/agent-skills.git --ref main --json
codex plugin add quality-gates@tomwangowa --json
```

The cases downloaded the public marketplace and wrote source registration,
source files, installed caches and enabled state in their own test directories.
The installer performed its approved surrounding native inventories; one final
inventory per host corroborated the results. No retries, refresh/update,
dependency installation, model session, hook authorization, uninstall or
rollback was performed. No commit, push or publication occurred.

## Retention and evidence

Machine-readable results: [macos-r5-native-evidence.json](macos-r5-native-evidence.json).
Detailed isolated state remains at
`.superpowers/sdd/2026-11-11-r5-native-acceptance/prepared-n8v9i6g1/`.
Each host has its approved `run.json`, one-use start marker, tool transcript,
downloaded-source file fingerprints, final native inventory and independent
`verified.json`; the root holds baseline and summary records. Cwd directories
outside the repository were retained. No automatic cleanup occurred.

The original three named Claude settings/registry files and original Codex
`config.toml` had unchanged existence/link/hash fingerprints. Product inputs,
all five saved ZIPs, HEAD, staged state and four stashes were unchanged. The
25 previously fingerprinted native evidence files were also unchanged.
These checks cover named files; they are not a whole-machine side-effect audit.

## Evidence limits and deviations

- Initial inventories and individual native subprocess return codes were
  consumed by the unchanged installer but not separately retained as raw
  machine events. R5's executor only reports `installed` after native
  returncode zero and successful postcondition verification; both flows and
  final inventories exited zero. Command attempt counts follow the single
  source/install previews and approvals plus the unchanged no-retry executor.
- Codex's raw add receipt was consumed by R5 but not separately logged. Its
  verified installed-root output was retained and independently corroborated;
  this record does not claim to retain the receipt's full original JSON.
- One Codex package-description menu chunk was truncated by the tool's output
  budget. The source/install approval previews and final outcomes were retained.
- A documentation patch initially failed its text-match check and made no
  changes; the corrected patch was local only. No external operation was repeated.

## NOT VERIFIED

Windows/PowerShell, Ubuntu/Debian and other architectures; other packages and
Superpowers; installation of missing dependencies; hooks, MCP, actual skill
execution, restarted-host entries and model workflows; existing-install
updates/migration; elimination of remote-ref races or all native/network side
effects. No production Superpowers acceptance record or payload hash was added.

These two cases establish the R5 basic installation path on the specified
macOS CLIs. Additional native or model operations require a new concrete scope
and approval; this result is not permission to repeat these commands.
