# First native acceptance scope — run 1 stopped

Approved and executed once on 2026-11-09. Source addition returned 0, but
inventory normalization blocked continuation; plugin installation was not
attempted. Cwd was moved outside the worktree to avoid inherited settings.
See [run-1 evidence](macos-claude-run-1.md). This historical scope does not
authorize the [new rerun proposal](native-acceptance-rerun-proposal.md).

## Approval scope

One macOS arm64 run of the generated archive, using installed Claude Code
2.1.319 and the current real Python 3.11+ interpreter. Select **Claude only**,
**quality-gates only**, no updates, no third-party tool installation, no
Superpowers/mod installation and no journal setup. Expected plugin version:
`0.2.0`. A failure ends this run; no retry is included.

Create a fresh ignored directory under this plan's
`.superpowers/sdd/2026-11-09-cross-platform-plugin-installer/` workspace, with
separate `home/`, `claude/`, `xdg/`, `tmp/`, `cwd/` and `unpacked/` directories.
Extract the archive there. The child process receives a clean environment via
`env -i`, only the existing executable PATH and these selected HOME,
CLAUDE_CONFIG_DIR, XDG_CONFIG_HOME and TMPDIR values. No private configuration,
Git credentials, environment secrets or account files are copied. Do not start
a model session or grant hook trust.

## Exact operation sequence

Launch the extracted `install.py` using the absolute real Python interpreter
with `-I`, in a terminal attached to the fresh `cwd/`. Respond to the menus:

1. Choose Claude Code only.
2. Choose quality-gates only; leave updates empty.
3. Approve the separately displayed source preparation.
4. Approve the quality-gates installation preview only if the source payload
   still matches this bundle's expected version/hash. Otherwise stop.

The approved mutating native command vectors are limited to:

```text
claude plugin marketplace add https://github.com/tomwangowa/agent-skills.git --scope user --json
claude plugin install quality-gates@tomwangowa --scope user --json
```

Read-only CLI version, marketplace list and plugin list calls, plus local
manifest/hash checks, surround those operations. No refresh, update, removal,
package-manager or model-session command is authorized by this proposal.

## Effects and evidence

This downloads the public marketplace from GitHub and writes marketplace/plugin
state under the isolated home/config directories. The native CLI may perform
its own metadata/network traffic. No model request is planned and no model
token cost is expected. The marketplace command follows its native default
branch, not a guaranteed immutable ref: the bundle must reject unexpected
content, and a source can still move during the command. Retain that limitation
in the result rather than claiming precise pinning.

Record the OS/architecture and actual CLI version, archive SHA-256,
before/after inventory, native return codes and installed manifest/tree hash.
An installed listing proves the installation layer only; hooks, MCP and skills
are not exercised. Do not remove the temporary directory automatically: it is
the review evidence and may contain partial native writes.

This proposal requires explicit approval before execution. A repeat of either
external native operation needs new approval. Codex and Superpowers capability
investigation, Windows/Ubuntu/Debian runs and full `npm ci`-using project checks
are separate scopes, not included in this first run.
