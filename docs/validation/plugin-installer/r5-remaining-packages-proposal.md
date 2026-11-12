# R5 remaining-package native installation proposal

Date: 2026-11-11. Status: **APPROVED AND EXECUTED; 14 INSTALLATIONS VERIFIED**.
The user approved the entire batch with `ok`. See [results](macos-r5-remaining-results.md).
The scope below is retained as the approved record, not authorization to rerun.

## Scope

Use the unchanged R5 archive on macOS 26.6.2 arm64, Claude Code
`2.1.322 (Claude Code)` and Codex `0.167.0`, with Python 3.12.1. Install the
remaining own packages: eight on Claude and six on Codex, 14 installations.
The earlier quality-gates cases remain unchanged; quality-gates and Superpowers
are not selected here. Windows/Linux and runtime functionality remain separate.

| Package | R5 version | Hosts |
| --- | --- | --- |
| technical-decisions | 0.1.3 | Claude and Codex |
| repo-workflow | 0.3.0 | Claude and Codex |
| content-tools | 0.2.0 | Claude and Codex |
| work-journal | 0.2.0 | Claude and Codex |
| session-preferences | 0.1.4 | Claude and Codex |
| skill-toolbox | 0.1.3 | Claude and Codex |
| handoff-mod | 0.2.2 | Claude only |
| attention-mod | 0.6.1 | Claude only |

The saved archive SHA-256 remains
`3047be151e9e89644a35d6542356badf90bf4e34dd3f7497d14a13c05a932ace`.
Every selected manifest version and complete expected payload hash is sealed
in the prepared case's `run.json`, copied from this archive.

## Tools and settings

Local preflight confirmed executable git, Python 3.12.1, Bash 3.2.57, jq 1.7.1,
Node v23.7.0 and openrsync (protocol 29). This confirms required command
availability, not that every skill works with those versions. No dependency
installation or system upgrade is included.

Use fresh separate HOME, CLAUDE_CONFIG_DIR, CODEX_HOME, XDG_CONFIG_HOME and
TMPDIR directories for each host, plus cwd outside all Git repositories. No
personal configuration, credentials, journal records or environment secrets
are copied. Git does not read global/system settings or prompt for credentials.
The earlier native test environments are not reused or changed.

Prepared root: `.superpowers/sdd/2026-11-11-r5-remaining-packages/prepared-fwh91yoc/`.

The launch helper refuses unapproved or already started cases, verifies the
archive and all 24 embedded file hashes, and launches the unmodified installer
in the clean environment. A recording wrapper delegates every subprocess
unchanged and saves its actual argv, exit and captured stdout/stderr, including
native inventories and Codex receipts. It does not synthesize native outcomes
or change installer decisions. Installer output is also saved; tool transcripts
supplement native messages printed directly to the terminal.

Offline checks used local Python child processes only: exit codes 0 and 7 and
stdout were preserved. Both unapproved host launches were refused before any
native command or start marker. No native compatibility claim follows from
these checks.

## Native command budget

At most two marketplace additions and 14 package installations. Each vector
below is allowed once; there is no retry, refresh, update, enable-existing,
uninstall or rollback:

```text
claude plugin marketplace add https://github.com/tomwangowa/agent-skills.git --scope user --json
claude plugin install technical-decisions@tomwangowa --scope user --json
claude plugin install repo-workflow@tomwangowa --scope user --json
claude plugin install content-tools@tomwangowa --scope user --json
claude plugin install work-journal@tomwangowa --scope user --json
claude plugin install session-preferences@tomwangowa --scope user --json
claude plugin install skill-toolbox@tomwangowa --scope user --json
claude plugin install handoff-mod@tomwangowa --scope user --json
claude plugin install attention-mod@tomwangowa --scope user --json
codex plugin marketplace add https://github.com/tomwangowa/agent-skills.git --ref main --json
codex plugin add technical-decisions@tomwangowa --json
codex plugin add repo-workflow@tomwangowa --json
codex plugin add content-tools@tomwangowa --json
codex plugin add work-journal@tomwangowa --json
codex plugin add session-preferences@tomwangowa --json
codex plugin add skill-toolbox@tomwangowa --json
```

Normal installer version and local tool probes and surrounding native inventory
reads are included. Codex plugin inventory queries must be qualified to
`tomwangowa`; no global remote catalog query is included. A final native
inventory per host may corroborate all selected packages together.

## Menu choices and failure handling

- Claude: choose host 1; packages `2,3,4,5,6,7,8,9`; preserve all updates.
- Codex: choose host 2; packages `2,3,4,5,6,7`; preserve all updates.
- Approve source preparation only for the displayed own repository, then check
  the downloaded selected manifests and complete payload hashes against R5.
- Approve installation only if the actual action list matches this host's
  approved packages, source and versions. Decline dependency installation and
  optional journal-location setup. Do not configure feedback recipients.
- Source/version/content mismatch, sign-in or unexpected authorization prompts
  stop the affected flow. Do not change expectations to make it pass.
- An ordinary per-package failure is retained and reported; the unchanged
  installer may continue the other already-approved independent packages. This
  batch approves that continuation on both hosts, but never a retry of a failed
  item. An interruption or unapproved command/prompt stops the current flow.

## External effects and cost

The two fresh cases download the public GitHub marketplace and write source
registration, downloaded files, installed caches and enabled state inside their
own test directories. Native commands may perform metadata/network traffic.
This installs/registers hooks and MCP definitions as package contents; it does
not grant hook trust or launch a conversation, panel or MCP server for a
functionality test. No model request or model token charge is planned.

`attention-mod` can call the haiku model during later session use, and
`handoff-mod` can automatically write notes/store data during later sessions.
This batch does not start those sessions or exercise those behaviors. Journal
setup and existing activity/note contents are also outside the scope.

All outputs, installed state and partial writes remain for inspection. No
cleanup, commit, push, production sync or publishing is included. Repeating an
external operation requires new approval.

## Evidence and success conditions

Record per-package native exits and actual inventory/receipt information.
Require installed identity, manifest version, enabled state and actual installed
root to match the preview. Claude must report user scope; Codex must corroborate
its native receipt/cache path without inventing scope. Independently compare
every installed file/path and aggregate hash against the selected R5 payload
and the downloaded source; native exit zero alone is insufficient.

Retain full captured machine outputs and report successes, skips, failures and
unverified items individually. Compare original named settings/registries,
archive/product fingerprints, HEAD/stashes and earlier native evidence before
and after. These are bounded file checks, not a whole-machine side-effect audit.

## NOT VERIFIED by preparation or installation alone

No native batch case has started. Even if all installs succeed, that does not
verify Windows/Linux, Superpowers, missing-tool installation, existing-user
migration/update, journal setup, hook/MCP startup, model/skill behavior or
restarted-host entry exposure. No production acceptance record is added by
this proposal.
