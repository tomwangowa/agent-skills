# Claude Code account-state installation matrix

Date: 2026-11-11. **APPROVED; BOTH NATIVE INSTALLATION CASES EXECUTED ONCE AND PASSED.**
See the [actual two-case results](claude-login-matrix-results.md). The original
scope below is retained; this spent approval does not authorize another run.
Requirement: Superpowers must install in Claude Code with an account login and
without an account login. These are independent native cases, not conclusions
borrowed from Codex or inferred from the same install command.

## Observed authentication facts

The user explicitly permitted use of the current Claude account state while
keeping plugin writes isolated and not copying/logging credentials or sending
model requests. The installed binary is `2.1.322 (Claude Code)`, SHA-256
`a9d237949db816a0b7afd88a9a8e1df36b3a597a30f5a41d1c0539eb180a3450`.
Local version/auth/plugin help reads returned zero.

One `claude auth status --json` observation was made in each context:

| Context | Native status | Exit | Installation conclusion |
| --- | --- | --- | --- |
| Current user environment | `loggedIn: true`, `authMethod: claude.ai`, `apiProvider: firstParty` | 0 | Current account exists; no plugin installed here |
| Fresh HOME and CLAUDE_CONFIG_DIR | `loggedIn: false`, `authMethod: none`, `apiProvider: firstParty` | 1 | Genuine no-account case is ready for an approved install |
| Isolated CLAUDE_CONFIG_DIR with current HOME/environment | `loggedIn: false`, `authMethod: none`, `apiProvider: firstParty` | 1 | Current login did not carry into the isolated profile |

Exit 1 in the last two rows is the observed unauthenticated status, not a
failed installation. Only status/method/provider and output fingerprints were
retained; account email/organization and credential values were not recorded.
No login, source-add, plugin install or model request ran in this preflight.

The older Claude 2.1.321 installation did not record authentication state and
does not fill either cell in this matrix. It remains useful for payload/source
observations, not for proving login independence.

## Prepared cases and required user action

Root: `.superpowers/sdd/2026-11-11-claude-login-matrix/prepared-0ua9ulq8/`.
Each case has its own config/cache/temp/cwd. The no-account case also has a
fresh HOME. The signed-in case uses the real HOME for native OS integration,
but an isolated CLAUDE_CONFIG_DIR; inherited auth/API/proxy overrides will not
be used by its prepared clean environment.

Because native auth does not automatically carry over, a true signed-in case
requires the user to log into that isolated native profile. The prepared
`login-isolated.command` runs only `claude auth login --claudeai` under the
documented isolated environment. It has not run. Native OAuth login opens the
browser, contacts Anthropic authentication services, and stores the new test
profile's authentication state through native storage, potentially including
the OS keychain. No token is read from or copied out of the current account.
The user performs authentication; the observer never fills credentials.

The permission to inspect/use the existing login did not authorize moving its
credentials or installing into the personal plugin directory. If the user does
not authenticate the isolated profile, mark the signed-in install **pending**;
do not substitute fake tokens or a simulated logged-in result.

## New native-operation scope for approval

Approve **two cases**, each with at most one source add and one install:

```text
claude plugin marketplace add https://github.com/anthropics/claude-plugins-official.git --scope user --json
claude plugin install superpowers@claude-plugins-official --scope user --json
```

Maximum combined mutation budget: two source-adds and two plugin installs;
no retry. Official catalog and pinned payload downloads reach external
GitHub/Anthropic source services. No model request or model-token charge is
planned. CLI paths, binary hash, clean environments and fixed payload checks
are stored in `run.json`; `install_case_once.py` is prepared, syntax checked
and refuses installation before approval. Each case consumes its own start
marker. Native errors/prompts/timeouts stop that case without retry or cleanup.

Per-case read budget: one version read, one auth-status before and after,
one marketplace list before and after, one plugin list before and after.
Authentication output is reduced to the non-secret status fields above.
The signed-in case must report true/`claude.ai` immediately before source-add;
the no-account case must report false/`none`. Otherwise stop before mutations.

After every vector, local-only observations retain catalog Git/marker presence,
origin/HEAD if available, raw selected entry and marker bytes/hash. This also
isolates any Git-to-archive transition by vector instead of inferring its timing.
These native lists may themselves alter catalog storage and are included in
the approved side-effect scope. No observer repairs native metadata.

Before install, require the unchanged raw entry hash, official catalog URL,
payload URL `https://github.com/obra/superpowers.git` and pin
`bb92a77741419a4ab5f06e711a283343f1ada0c3`. On a moved selected entry, stop.
After install, require native version 7.0.0, enabled true, user scope, the native
registry's exact payload pin, all 238 committed files/permissions and full
content hash `d9ae919521df6591becf75601b64bd6e9ca358e389bbe95050f966555a7ef704`.
Compare to the already fetched independent pinned Git objects; no reference
fetch is included. Preserve partial native state and every result.

Named original settings/product/archive/prior-evidence fingerprints, HEAD,
stashes and staged state are rechecked. This is not a whole-computer or keychain
side-effect audit. No logout, credential export, personal plugin update,
dependency install, hook trust, model session, runtime fix, accepted hash/record
change, new ZIP, commit, release or Windows/Linux run is included.

## Completion and limits

The login requirement is confirmed only after **both actual cases** meet their
auth pre/postconditions and complete native installation/content verification.
A native capability result does not by itself enable the installer's pending
Claude archive policy or constitute an unmodified ZIP acceptance run. Those
remain separate integration work, even when both native installs succeed.
