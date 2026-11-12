# macOS native rerun scope — R2 executed once

Approved and executed once on 2026-11-09. The source-add, selected plugin-install
and installer all returned 0; actual scope/version/payload checks passed. See
[R2 evidence](macos-claude-run-2.md). This historical approval does not authorize
another external retry or any excluded functionality test.

## Concrete scope requiring new approval

Run the corrected `dist/agent-skills-installer-fe55c04-candidate-r2.zip` once:

- SHA-256: `77d2189c9fc374920333ad81b825e7f516be49159c1e99067770896dcc237800`.
- Size: 41,012 bytes.
- Installed Claude Code 2.1.319, macOS arm64, existing real Python 3.11+.
- Select Claude Code only and quality-gates only, expected version 0.2.0 and
  payload hash `a7c6e396a54fa316a837bd3cc7479254cadb4b09672475649820720eca81add3`.

Create fresh HOME/config/tmp/evidence directories under the ignored plan
workspace. Use a fresh cwd outside every worktree to avoid ancestor project
settings. Keep the original candidate, run-1 evidence and downloaded source
unchanged; do not reuse them as a passing fresh-install fixture.

Launch the unmodified extracted entry with an absolute real Python interpreter
and `-I`, clean environment and the scoped HOME/CLAUDE_CONFIG_DIR/
XDG_CONFIG_HOME/TMPDIR. Observe command return codes, source type/URL/field
shape and plugin inventory without recording arbitrary config/MCP values.
Enforce a single-attempt allowlist for these two mutating command vectors:

```text
claude plugin marketplace add https://github.com/tomwangowa/agent-skills.git --scope user --json
claude plugin install quality-gates@tomwangowa --scope user --json
```

Approve source preparation, then approve plugin installation only if the live
source payload still matches R2. If source verification fails or another
unexpected operation is proposed, stop and retain the evidence. No automatic
retry is included.

## Effects, costs and exclusions

This repeats the GitHub repository download into a new isolated environment,
then may install the one plugin there. The native CLI may make its own
metadata/network calls. No model session, model request, private credentials,
dependency/host installation or hook-trust grant is part of the scope; no model
token cost is expected. No source refresh, update, uninstall, Codex/Superpowers/
mod installation, journal configuration, commit, push or publication is included.

Record before/after inventories, native exit codes, installed root/scope,
version and actual payload hash. Installation evidence remains separate from
hooks/MCP/skills functionality. Leave the directories intact for review.

This is a new approval checkpoint because run 1 has ended, the installer has
changed, and a new run repeats an external download. Approval of run 1 does not
silently approve this rerun or another retry after it.
