# R7 full-package installation coexistence results

Date: 2026-11-11. The approved installation/preservation batch is complete on
macOS arm64. All 18 first installations succeeded in two fresh unauthenticated
host profiles. Both reruns attempted zero mutations and retained the installed
payloads and checked settings. **Codex's rerun returned the expected exit 1 for
seven preserved own packages whose update ownership is not verified.** This
does not constitute a fully green Codex rerun status or runtime workflow proof.

The [approved proposal](r7-coexistence-proposal.md) defines the operation limits.
The [sanitized evidence](r7-coexistence-evidence.json) records actual results.

## Candidate and results

The unchanged `dist/agent-skills-installer-fe55c04-candidate-r7.zip` is 56,060
bytes, SHA-256
`d598a8170b57ba27a29a1ecdcbef3c450ec0acf4f25c9a4edca8f864f8b0f4ea`.
Its exact entry ran through a PTY menu driver and a Python subprocess audit
hook. No fake native command results or replaced installer functions were used.

| Host | Packages together | First exit | Rerun exit | Rerun mutation attempts | Files checked |
| --- | --- | --- | --- | --- | --- |
| Claude Code 2.1.322, logged out | 10 | 0 | 0 | 0 | 4,240 |
| Codex 0.167.0, no account | 8 | 0 | 1, known status limitation | 0 | 3,959 |

Both hosts installed quality-gates 0.2.0, technical-decisions 0.1.3,
repo-workflow 0.3.0, content-tools 0.2.0, work-journal 0.2.0,
session-preferences 0.1.4 and skill-toolbox 0.1.3. Claude additionally installed
handoff-mod 0.2.2 and attention-mod 0.6.1. Superpowers is 7.0.0 from
`claude-plugins-official` for Claude and 6.3.0 from `openai-api-curated` for
Codex. Every selected package has one enabled native inventory entry and one
version/cache directory. Claude's reported scope is user; Codex reports no
scope and none is inferred.

Independent local verification compared all **8,199 installed files**, their
bytes and executable modes, with committed Git objects. The 16 own payloads
match R7's frozen hashes; Claude Superpowers matches commit
`bb92a77741419a4ab5f06e711a283343f1ada0c3`, and Codex Superpowers matches the
native official catalog at `d420d13051bffe4543ed39e30fa46b87148e47dd`.
Complete saved payload maps, native versions/roots/enabled state and the
checked registries/settings are unchanged after rerun.

## Codex status limitation

Frozen R7 preserves existing own Codex packages without attempting an update,
but classifies them as `unverified` because update ownership is unknown:

```text
Existing Codex provider preserved; update ownership is not verified.
```

All seven own packages take this path; Superpowers uses its separate preserved
path. The same seven messages appear in preview and final results, yielding
14 warning lines, seven distinct package warnings and exit 1. There were no
other uncertainty messages, no installation/update commands on rerun and no
payload/settings changes. The observer accepted only this exact predeclared
limitation. R7 was not changed to hide it.

## Actual external operations and retained state

The approved batch ran four installer invocations, three marketplace additions,
18 plugin installs and one native Codex catalog startup. The startup sent only
`initialize` and `initialized` and exited 0; its catalog was produced natively.
All first-install mutation commands were issued once, with no retry, refresh,
rollback, removal, dependency installation or package-manager installation.
Downloads used the own and official public sources described in the proposal.

Native installation caches, registries and enabled settings were written inside
the two new isolated profiles. No login or model request was sent by the
observer, and no normal agent session, hook-trust flow, attention panel or MCP
workflow was started. Model token charges were not incurred by an observer
model request; this is not a complete provider billing or network-wire audit.

Journal configuration was declined on all four invocations. No real activity
or note content was read or moved. Mod personal configuration remains pending.
Codex retains its synthetic company provider with `requires_openai_auth = false`;
the test does not contact or verify a real company endpoint. Claude auth status
remained logged out before/after both invocations, and the Codex account auth
file remained absent.

The final check verifies 7,641 baseline files, four original personal settings,
all earlier archives/evidence and earlier native test files. The only declared
post-result baseline-file change is the validation index linking this report.
HEAD, the four existing stashes and the empty staged state are unchanged.
All new native profiles and evidence are retained. No product code, ZIP,
capability record, production mirror or installed personal plugin was changed;
no commit, push or publication occurred.

Private full evidence remains under
`.superpowers/sdd/2026-11-11-r7-coexistence/prepared-qiw2o6pb/`.
The public summary omits auth-output fingerprints, personal config contents,
environment values and absolute installed paths.

## Verification corrections and evidence limits

Before approval, a local preparation checker appended the ZIP root twice and
failed with `FileNotFoundError`; its path handling was corrected and the full
local check passed. No native action ran during that preparation failure.
The directly exercised command whitelist passed 105 allow/deny vectors.

After the native batch, the independent local verifier initially failed a
content-hash assertion because it sorted path strings while R7 sorts path
components. All 18 live payload maps still equalled their first-install
snapshots, and all R7 hashes matched. Only the local verifier's ordering was
corrected; a small reproduction checks the different ordering and rejects a
changed content hash. The complete committed-byte/mode and preservation
verification then passed. No external action was repeated for this correction.

Assumptions checked: the candidate/binaries did not drift (hash checks), all
selected packages installed rather than merely returned success (exact native
inventory plus committed file maps), and rerun was read-only at the installer
mutation boundary (command ledgers plus before/after payload/settings maps).
These checks inspect real state; accepting a fake success message alone cannot
satisfy them. They do not trace every native internal bookkeeping write.

**VERIFIED:** macOS arm64 installation coexistence of all R7-applicable packages,
single native entries/cache versions, exact payload content/modes, both reruns'
zero mutation attempts and retained payload/settings, with the Codex status
limitation explicitly retained.

**NOT VERIFIED:** model/hook/MCP runtime coexistence, Windows/Linux and other
CLI versions/architectures, logged-in full-package coexistence, actual company
endpoint connectivity, journal setup or mod personal configuration, native
older/newer/disabled package cases, OS-launcher end-to-end execution, or a
complete network/keychain/whole-computer audit. Earlier Superpowers-only login
evidence remains separate and is not expanded to full-package runtime behavior.
