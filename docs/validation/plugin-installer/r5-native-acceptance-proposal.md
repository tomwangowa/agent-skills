# R5 native installation proposal

Date: 2026-11-11. Status: **APPROVED AND EXECUTED ONCE PER HOST**.
The user approved this scope with `ok`. Both cases passed the bounded
installation checks; see [results](macos-r5-native-results.md). The text below
retains the approved scope and does not authorize another run.

## Scope to approve

Run the unchanged R5 installer once for Claude Code and once for Codex on this
macOS 26.6.2 arm64 machine. Select only `quality-gates@tomwangowa` version
`0.2.0`, with no update or dependency installation. This first check establishes
the basic installation path for both hosts; it does not accept all packages,
Superpowers or all three platforms.

- Claude Code local version: `2.1.322 (Claude Code)`.
- Codex local version: `codex-cli 0.167.0`.
- Python local version: `3.12.1`.
- R5: `dist/agent-skills-installer-fe55c04-candidate-r5.zip`.
- SHA-256: `3047be151e9e89644a35d6542356badf90bf4e34dd3f7497d14a13c05a932ace`.

Only local `--version` probes ran during preparation, in a temporary clean
environment. Both returned zero. Codex printed a warning because that version
probe's fresh CODEX_HOME did not yet exist; the prepared installation cases
have their config directories created. No marketplace inventory command ran.

## Prepared cases and execution

Prepared root:
`.superpowers/sdd/2026-11-11-r5-native-acceptance/prepared-n8v9i6g1/`.

Each host has a separate `run.json`, HOME, CLAUDE_CONFIG_DIR, CODEX_HOME,
XDG_CONFIG_HOME, TMPDIR and extracted R5. Its working directory is outside all
Git repositories. The child receives only the explicit environment recorded
in `run.json`, including existing executable PATH; no personal settings,
credentials or environment secrets are copied. Git uses no global/system
configuration and cannot prompt for credentials.

The small launch helper checks approval status, R5 SHA-256 and all 24 embedded
file hashes, then executes the unchanged `install.py` using isolated Python.
A one-use start marker prevents accidental relaunch. The helper does not
replace CLI responses, installer code or subprocess behavior.

After approval, run the prepared Claude case first, then Codex if Claude
passes. Recheck the version displayed by the installer before host selection.
Select the intended host, package 1 only, no updates; approve source preparation
and then installation only when the actual previews match this proposal.
Stop on a version mismatch, changed payload, failure, sign-in request or an
unexpected dependency/permission prompt. No other host mutation follows a
failed case without a new decision.

## Exact native mutation budget

At most one attempt for each command below, four mutation attempts total:

```text
claude plugin marketplace add https://github.com/tomwangowa/agent-skills.git --scope user --json
claude plugin install quality-gates@tomwangowa --scope user --json
codex plugin marketplace add https://github.com/tomwangowa/agent-skills.git --ref main --json
codex plugin add quality-gates@tomwangowa --json
```

The installer also performs its normal version probes and repeated inventory
reads around source preparation and installation. Approved inventory vectors
are Claude marketplace/plugin list and Codex marketplace list plus
`codex plugin list --marketplace tomwangowa --json`. One final inventory of
the selected host may corroborate its result. Unqualified Codex plugin listing
is excluded. Existing local Python tool probes and local file/hash inspection
are included; package-manager commands are excluded.

## Effects, cost and retention

The cases download the public `tomwangowa/agent-skills` marketplace from GitHub
and write its registration, downloaded files, plugin cache and enabled state
inside their isolated directories. Native commands may make their own metadata
or network requests. No model session is planned, so no model token cost is
expected. No new account, API credential, hook authorization or paid service
is requested.

The downloaded branch may have changed since R5 was built. The installer must
withhold installation if package content differs from its saved catalog; it
must not update R5 expectations to make the run pass.

Retain the prepared directories, native output and any partial writes as
evidence. No retry, refresh, update, uninstall, rollback or automatic cleanup
is included. Any repeat of an external operation requires new approval.

## Evidence and pass conditions

For each host, retain terminal output, native/installer exit codes, initial and
final inventories, actual installed path and manifest, and independent complete
file/hash comparison against R5's selected payload hash:

- Claude: `a7c6e396a54fa316a837bd3cc7479254cadb4b09672475649820720eca81add3`.
- Codex: `bdd888a67f1728221208937bfc554efbd17fc19bdda1590697628eb40b05ed5c`.

Require exactly the selected plugin, version `0.2.0`, enabled state and an
installed root inside the intended isolated config. Claude must report user
scope; Codex must provide the actual receipt/cache target without inventing a
scope. Native source-add, install and installer exits must all be zero.
Zero exit alone is insufficient.

Compare fingerprints of the original Claude settings/installation registries
and Codex config before/after, without copying or printing their contents.
This is a check of named files, not a whole-machine filesystem/network audit.
Keep R5 and all old archives, stash entries and earlier native cases unchanged.

## NOT VERIFIED by approval or preparation

No native case has started. Passing the proposed cases would establish only
one package's R5 installation on these two macOS CLIs. Windows, Ubuntu/Debian,
other packages, Superpowers, dependency installation, real hooks/MCP/skills,
restarted-host entries and model behavior remain separate acceptance work.
No commit, push, production sync or publishing is included.
