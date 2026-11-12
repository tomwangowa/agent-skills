# Claude official-source probe: preflight stopped

Status: **STOPPED BEFORE DOWNLOAD / NOT NATIVE ACCEPTANCE**.
User #1 approved the Claude capability proposal after R4 offline delivery.
The approved stop-on-version-mismatch condition was reached during local
preflight, before either external mutation command.

## VERIFIED

- The current binary resolves to the same target recorded in the approved
  manifest, and its SHA-256 is unchanged:
  `abc9feeeca8091d51b623291e044cf0528c2f6b74e0c1d6ef671d52c73f7cd3c`.
- One isolated local command ran: `~/.local/bin/claude --version`.
  Exit code `0`; full stdout `2.1.321 (Claude Code)`; stderr empty.
- The manifest incorrectly expected `2.1.319` while already pointing at the
  `2.1.321` binary. This is a proposal preparation error, not evidence that
  the approved binary changed after approval. It also omitted the full
  ` (Claude Code)` portion required by exact CLI-version acceptance.
- Source-add attempts: **0**. Plugin-install attempts: **0**. Model calls: **0**.
- The isolated HOME and Claude config directories contain no files after
  preflight. The command log contains only the local version vector.
- No runtime, providers target, production acceptance record or R4 ZIP was
  changed by this attempt. No current-branch stage/commit/push was performed.

Raw evidence is retained under
`.superpowers/sdd/2026-11-10-superpowers-official-sources/native-claude-capability-8x6cj5n2/evidence/`:
`preflight.json` and `commands.jsonl`. The consolidated local result is
`native-claude-preflight-result.json` in the parent execution workspace.
The original approved [run manifest](superpowers-native-case.json) is preserved.

## Cause and correction

The proposal combined a freshly recorded binary target/hash with a historical
version label. An exact preflight compared the actual full output against that
stale label and correctly stopped. No permissive version normalization or
silent change to the approved condition was used.

A [corrected proposal](superpowers-native-acceptance-r2-proposal.md) and
[new run manifest](superpowers-native-case-r2.json) now pin the observed full
`2.1.321 (Claude Code)` string to the same binary hash and use a fresh exclusive
isolated directory. The selected Superpowers target, pin, two command vectors
and single-attempt budgets are unchanged. This correction is not authorization
to resume: the original proposal explicitly stopped on version mismatch, so
approval of the corrected concrete run is required before mutation.

## NOT VERIFIED

No catalog or payload was downloaded, no native materialization/hash/receipt
contract was established, and no candidate installer or functional/model case
ran. No production acceptance tuple was added. Personal registry/config
before/after fingerprints were not compared because the run stopped before
that native-mutation phase; no claim about a full personal-state audit is made.
