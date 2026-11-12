# Codex no-account Superpowers installation proposal

Date: 2026-11-11. **APPROVED AND EXECUTED ONCE; PASSED.**
See the [native result](codex-no-account-native-results.md). This completed
approval does not authorize another startup, query or installation.
Purpose: test actual native Superpowers installation without a coding-agent
account login. This is a native capability case, not acceptance of R5 or the
distributed installer. No production acceptance record will be added by it.

## Exact scope

Prepared case:
`.superpowers/sdd/2026-11-11-codex-no-account-install/prepared-mlyontal/`.
Fresh HOME/CODEX_HOME/XDG/TMP, cwd outside Git, no personal credentials copied.
The isolated config contains a synthetic company provider with
`requires_openai_auth = false`, `https://company.invalid/v1`, and an environment
variable containing a dummy key. This intentionally tests configuration shape
without using a real company endpoint or secret. No `auth.json` exists.

The exact installed CLI must remain `codex-cli 0.167.0`; wrapper/helper/config
fingerprints and environment are recorded in `run.json`. One App Server startup
uses the previous tested protocol (`initialize`, then `initialized`) and
disables remote-plugin/discovery prefetch and analytics. It performs one native
catalog sync, allowing the native Git, GitHub HTTP and missing-snapshot official
export fallback chain documented in the previous catalog proposal. This can
reach GitHub/OpenAI download services; a wire-request count is not asserted.
No model request or model-token charge is planned; no company endpoint request,
login, MCP call or hook authorization is included.

After startup, each operation below runs at most once, with the same feature
overrides and clean environment:

1. `codex plugin marketplace list --json`.
2. `codex plugin list --marketplace openai-api-curated --available --json`.
3. Only if native availability and all fixed preconditions agree:
   `codex plugin add superpowers@openai-api-curated --json`.
4. On successful installation and local receipt/content checks:
   `codex plugin list --marketplace openai-api-curated --json`.

The snapshot must match commit `d420d13051bffe4543ed39e30fa46b87148e47dd`, the
previously observed raw entry hash, Superpowers 6.3.0 and complete payload tree
hash. If source content moved, selection is different, policy refuses the
plugin or authentication is demanded, stop; do not adapt, log in or retry.
There is at most one plugin-add attempt, timeout 180 seconds. Native
installation writes the isolated plugin cache and enabled plugin configuration.
Partial writes remain. No original user configuration is modified.

## Outcome checks and limits

Keep raw native output, once markers, protocol and settings. Compare the actual
installed receipt/root/version, enabled inventory and complete installed file
map to the native catalog's committed Git blobs. Check that the synthetic
company provider fields remain unchanged and `auth.json` remains absent;
recheck named original settings, product/R5/prior-evidence fingerprints, HEAD,
stashes and staged list. Preserve downloaded state and logs without cleanup.

`install_once.py` refuses unless this new case is explicitly marked approved;
it does not contain a retry. Native startup/list failures and timeouts are
results, not permission to run them again. No model conversation, actual company
endpoint test, Claude installation, Windows/Linux run, package upgrade,
acceptance/hash change, ZIP build, commit or publication is authorized.

A success proves the native CLI can install this exact official payload without
account login while retaining a synthetic company model configuration. It does
not prove an arbitrary company's endpoint/network policy, workflow behavior,
or installer candidate end-to-end acceptance. Those limits remain explicit.
