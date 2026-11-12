# R7 existing Superpowers preservation: offline evidence

Date: 2026-11-11. The user requested rerun/preservation verification before
native R7 acceptance. The exact shipped R7 runtime passed **29 synthetic
scenarios, each run twice: 58 installer runs, zero mutation commands**.
All synthetic installed files and settings fingerprints stayed identical.

Archive SHA-256:
`d598a8170b57ba27a29a1ecdcbef3c450ec0acf4f25c9a4edca8f864f8b0f4ea`.
The ZIP and its runtime were extracted without modifications. Its real menu,
inventory parser, planning and executor were exercised using synthetic native
CLI responses; no real host CLI, download or model request was executed.

## VERIFIED

- Both Claude and Codex: older, same and newer Superpowers versions; enabled
  and disabled state; official and alternate provider identities. Those 24
  combinations each ran twice. No install, update, source-add, enable, remove
  or downgrade command was accepted by the observer.
- Additional cases cover incomplete native metadata, duplicate inventory,
  and Claude project/local scope. Codex inventory has no observed scope; the
  result records `null` and does not invent one.
- Recognized existing providers returned `preserved`, exit 0, including newer
  or disabled providers. A malformed Codex enabled-state row returned
  `unverified`, exit 1, with no mutation. An uncertain inventory never became
  permission to reinstall.
- The same profile/fixture was passed to R7 twice, and complete fixture file
  maps were compared before/after both runs. The observer raises immediately
  on any command outside version and inventory reads.

The initial checker incorrectly required success/`preserved` for malformed
Codex enabled metadata. Actual R7 correctly returned uncertainty and no writes;
inspection of `_codex_plugins` confirmed the non-boolean rejection. Only the
checker expectation was corrected, with that case now requiring exit 1 and
`unverified`. No product or ZIP change was made. A redundant Codex scope-only
fixture was removed because the native schema exposes no scope.

Evidence: `.superpowers/sdd/2026-11-11-r7-preservation/` contains the standalone
replay, input paths, correction note and all scenario results. Published summary:
[r7-existing-install-preservation.json](r7-existing-install-preservation.json).

## Plugin inventory question

`secure-ai-development-gate` is shipped inside `quality-gates` **0.2.0** in the
agent-skills repository/marketplace, for both Claude Code and Codex. The package
mapping, each host's native plugin manifest and actual SKILL.md were checked.
Both quality-gates entries in the frozen R7 catalog list that skill. The active
Codex installation also has the 0.2.0 skill file. Package presence does not by
itself prove every security workflow or scanner has been exercised.

## NOT VERIFIED

Native older/newer/alternate-provider materialization; Windows/Linux; models/
hooks; arbitrary provider/configuration or filesystem states. The later
[separately approved R7 native batch](r7-native-acceptance-results.md) passed
all three actual same-version reruns with zero mutation attempts and unchanged
payload/registry/settings. It does not make every offline matrix combination
a native result.
