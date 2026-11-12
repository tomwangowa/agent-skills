# Claude Code Superpowers installation: logged in and logged out

Date: 2026-11-11. **Both separately approved native installation cases passed**
on macOS arm64, Claude Code `2.1.322 (Claude Code)`. Superpowers 7.0.0 installed
and enabled at user scope with and without a Claude account login. This closes
the native account-state capability requirement for this exact environment;
it does not constitute acceptance of the installer ZIP.

## VERIFIED

| Case | Auth before | Auth after | Source add / install | Installed result |
| --- | --- | --- | --- | --- |
| No account | `loggedIn: false`, `authMethod: none` | Same | One command each, both exit 0 | 7.0.0, enabled, user scope |
| Signed in to isolated profile | `loggedIn: true`, `authMethod: claude.ai` | Same | One command each, both exit 0 | 7.0.0, enabled, user scope |

Both cases used the same binary SHA-256
`a9d237949db816a0b7afd88a9a8e1df36b3a597a30f5a41d1c0539eb180a3450`, official
catalog `https://github.com/anthropics/claude-plugins-official.git`, selected
entry hash `d85f0111dd6cfcd54268f46dbadbd54d4df344c160cda075134e2d35aae9f888`
and pinned payload commit `bb92a77741419a4ab5f06e711a283343f1ada0c3` from
`https://github.com/obra/superpowers.git`.

Each native installed registry reports that exact pin. In each case all 238
installed files, complete path list, SHA-256 values and executable permissions
match the already fetched independent pinned Git objects. Neither case ignored
or normalized committed files. Complete installed-content hash for both:
`d9ae919521df6591becf75601b64bd6e9ca358e389bbe95050f966555a7ef704`.

Version, both marketplace lists and both plugin lists exited 0 in each case.
Both signed-in auth-status commands exited 0. Both no-account auth-status
commands exited 1 with `loggedIn: false` / `authMethod: none`; those exits are
expected unauthenticated status, not installation errors. No source/install
command was re-executed. No model, MCP, hook-trust or workflow execution request
was issued.

## Isolation and authentication

The [preflight and approved scope](claude-login-matrix-proposal.md) found that
the existing user's login did not carry into an isolated CLAUDE_CONFIG_DIR.
Consequently the signed-in test did not copy a token or pretend that an empty
profile was authenticated. One approved native `auth login --claudeai` opened
the browser for the isolated profile and returned `Login successful`, exit 0.
The subsequent native auth-before/auth-after observations verify the actual
signed-in state. No credentials were filled by the observer.

The no-account case has fresh HOME/CLAUDE_CONFIG_DIR/XDG/TMP. The signed-in case
has its own CLAUDE_CONFIG_DIR/XDG/TMP/cwd and uses the real HOME for native OS
integration. Both prepared clean environments omit inherited authentication,
API and proxy overrides. The test compared native auth-state hashes before and
after, but the committed summary omits those hashes and retains only
status/method/provider. Observer JSON reports exclude account email,
organization, OAuth URL/code/token and credential values; native authentication
storage is separate and remains available to the isolated test profile. The native login
stores the isolated profile's authentication state through native storage,
potentially including the OS keychain; that approved state remains, with no
automatic logout or cleanup.

Total native mutation budget consumed: two source-add commands, two plugin
installs, one native login. Source and payload downloads reached the approved
external services. This counts command attempts, not individual wire requests
or the native implementation's internal transport attempts. The only plugin
and enablement writes were to the two test profiles. No personal provider was
updated, duplicated or downgraded.

## Source storage observation

Both catalogs report Git HEAD `43fd1f9db0941b2b83cb62268e35970d4a67c202`.
The selected entry/payload pin stayed unchanged despite this differing from
the historical catalog revision. Local snapshots were taken after every
version/auth/source/list/install vector. From source-add onward, every snapshot
in both cases showed the matching Git origin/HEAD, `.git` present and `.gcs-sha`
absent. **No Git-to-archive transition was observed in these two cases.**
This does not establish when or why the older 2.1.321 case transitioned, or
prove a cold-start archive contract. No source-policy relaxation was applied.

## Independent local verification and retained state

Evidence root:
`.superpowers/sdd/2026-11-11-claude-login-matrix/prepared-0ua9ulq8/`.
Each subcase retains its once markers, actual native command results,
sanitized auth observations, per-vector catalog snapshots, native installed
files and `verification.json`. `verify_saved_case.py` is local-only: it checks
the saved results, current installed bytes/modes, the independent pinned Git
objects and original-state fingerprints without launching Claude or a network
operation. It returned exit 0 for both cases and saved `verification-local.json`.
Published summary: [claude-login-matrix-evidence.json](claude-login-matrix-evidence.json).

After both cases, all 52 protected product/archive/prior-evidence file hashes,
four named original personal settings fingerprints, HEAD, four stashes and the
staged list match the preflight baseline. Candidate R5, runtime code, provider
hashes and the empty production acceptance index are unchanged. Downloaded
native state and isolated authentication are retained. No commit, push, ZIP
build or release occurred.

Adversarial checks: login state was observed immediately before and after
actual installation rather than inferred from environment variables; a zero
install exit was insufficient without enabled/scope/version, native registry
pin and full committed content; both cases used independent config/cache roots,
and personal preservation was checked after the second case. These are actual
native operations, not mocked install results.

## NOT VERIFIED

The installer ZIP end-to-end flow, Windows/Linux, other Claude versions,
actual company endpoint connectivity/network restrictions, exposed workflow/
hook/model behavior, full OS-keychain state, wire-level traffic/billing or a
complete whole-computer side-effect audit. Named-file preservation does not
prove all possible host state is unchanged. The original cross-platform
colleague-facing installer remains unfinished until its integration and
platform acceptance work is completed.
