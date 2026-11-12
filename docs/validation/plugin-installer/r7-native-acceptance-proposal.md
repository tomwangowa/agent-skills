# R7 native installation and rerun acceptance proposal

Date: 2026-11-11. **APPROVED AND EXECUTED; ALL SIX INSTALLER INVOCATIONS PASSED.**
See the [native installation and rerun results](r7-native-acceptance-results.md).
This spent approval does not authorize another native operation.
Scope: the unchanged R7 ZIP, installed through its real Python entry and native
Claude/Codex processes, followed by rerun preservation in the same test profiles.
No native capability probe is substituted for the actual installer flow.

## Frozen candidate and prepared environments

ZIP: `dist/agent-skills-installer-fe55c04-candidate-r7.zip`, 56,060 bytes,
SHA-256 `d598a8170b57ba27a29a1ecdcbef3c450ec0acf4f25c9a4edca8f864f8b0f4ea`.
Prepared root:
`.superpowers/sdd/2026-11-11-r7-native-acceptance/prepared-9am00ufx/`.
Three independent config/cache profiles have exact R7 copies; each native cwd
was checked to be outside Git. No account credentials or personal settings
were copied. Real installed executable/wrapper hashes match the earlier cases:
Claude 2.1.322 and Codex 0.167.0; drift stops before network/install.

| Case | Setup | First R7 run | Second R7 run |
| --- | --- | --- | --- |
| Claude, no account | Fresh HOME and native config | Only Superpowers 7.0.0 selected | Must preserve installed payload, state and version |
| Claude, signed in | Fresh native config; one new isolated native browser login | Only Superpowers 7.0.0 selected | Must preserve installed payload, state and version |
| Codex, no account | Fresh HOME/CODEX_HOME with synthetic company provider; one native catalog startup | Only API-curated Superpowers 6.3.0 selected | Must preserve installed payload, state and version |

The signed-in case uses the real HOME for native OS integration and a fresh
CLAUDE_CONFIG_DIR; its native OAuth login can contact Anthropic authentication
services/open the browser and write native authentication state, potentially
to the keychain. The user completes authentication; no credential export,
copying or automated credential entry is included. Old authenticated profiles
are retained, not uninstalled/reset to create a fresh case.

Codex config contains `https://company.invalid/v1`, a dummy key environment
variable, `requires_openai_auth = false`, plugins enabled, remote-plugin and
discovery-prefetch disabled, and analytics disabled. The endpoint is not real;
no company service or model request is included. Settings must survive both runs.

## Budget and exact actions

Run the actual R7 `install.py` twice per case: **six installer invocations**.
The Python entry is tested with the existing real Python interpreter; native
OS launcher end-to-end behavior is outside this batch. No candidate file or
runtime function is modified, and no fake native runner is used.

Maximum new external/native mutation budget for the entire batch:

- **Two** Claude official marketplace additions, at most one per fresh profile:
  `claude plugin marketplace add https://github.com/anthropics/claude-plugins-official.git --scope user --json`.
- **Two** Claude installs, at most one per fresh profile:
  `claude plugin install superpowers@claude-plugins-official --scope user --json`.
- **One** Codex official native catalog startup, with exactly `initialize` and
  `initialized`, no thread/turn. Native Git/GitHub HTTP/missing-snapshot official
  export fallback transports are included for that single startup, matching the
  earlier tested producer. Download services can include GitHub/OpenAI and the
  official curated export backup; no wire-request count is asserted.
- **One** Codex install:
  `codex plugin add superpowers@openai-api-curated --json`.
- **One** isolated Claude account login, handled through the native browser flow.
- **Zero** source/install/update/enable/remove/dependency commands on any rerun.

Source/payload downloads and native registry/cache/settings writes occur only
in the prepared test profiles. No model call or model-token charge is planned.
No dependency or package-manager installation is included. Actual command
attempts, not internal network retries/transports, are counted by these limits.

R7's stock CLI version and selected-host inventory calls are included on each
run. Codex plugin inventories must be named `openai-api-curated`; no unqualified
Codex list is permitted. Additional observers are bounded to auth status before/
after each Claude run (four per Claude profile), one final plugin inventory
after each run, local Git/file/hash observations, and the native Codex startup's
version/protocol observation. Native lists may change their own catalog state;
those changes must be recorded rather than treated as an installer write.

The menu selects only the relevant host and Superpowers (Claude package 10,
Codex package 8 with the frozen catalog). Updates stay blank. Source consent is
given only for the approved Claude official source, installation consent only
for the exact first-install target. No `--yes` bypass or hidden consent shortcut
is added. If prerequisites or an unexpected command/prompt appears, stop that
case without retry, repair, privilege change or auto-approval.

## Observation and pass conditions

`run.json` pins ZIP, files, binaries, clean environments, menu choices, protocol
and budgets. Prepared `audited_entry.py` executes the unchanged R7 entry with a
Python subprocess audit hook: it records arguments without environment values
and rejects a command outside the approved whitelist/budget before launch.
It does not mock a host CLI or replace installer functions. Native stdout,
stdin/TTY behavior and exit status remain real. The observer and transcripts
are test instrumentation; their presence is disclosed in the result.

Each phase consumes a start marker; no process restart or repeated phase is
included. Native startup wait is at most 180 seconds, isolated login at most 600
seconds, and each installer invocation at most 900 seconds; stock native
command timeouts still apply. Preserve partial
state on timeout/failure; terminate only the test process group if necessary.

First install must exit successfully with the real native version, expected
source/pin, enabled state and complete payload hash: Claude 238 files at pin
`bb92a77741419a4ab5f06e711a283343f1ada0c3`; Codex 73 files from its verified
native official catalog. Source drift or uncertain provenance stops installation.

Before/after rerun, compare installed paths, complete file bytes/permissions,
manifest/cache versions, effective enabled state and native registry/config
fingerprints. The subprocess ledger must contain no mutation command in the
rerun phase, and R7 must report preservation. Do not infer preservation from
exit 0 alone. Changed native metadata/source storage must be reported explicitly.

Compare protected personal settings, all old archives, native evidence, HEAD,
stashes and staged list. Keep every transcript, profile and result. No cleanup,
logout, credential migration, account/package upgrade, model/workflow/hook-trust
test, Windows/Linux run, R7 rebuild, commit, push or publication is included.

This batch can establish native R7 installation and same-version rerun behavior
for the three listed cases. Older/newer/disabled/alternate-provider cases retain
their separately labelled offline coverage until actual native cases are run.
