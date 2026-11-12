# Codex no-account Superpowers native installation result

Date: 2026-11-11. **The separately approved native capability case passed** on
macOS arm64, Codex CLI 0.167.0. Superpowers 6.3.0 installed and enabled through
`openai-api-curated` without an account login or model conversation. This is
native CLI capability evidence, not acceptance of the distributed installer.

## VERIFIED

The [approved proposal](codex-no-account-native-proposal.md) ran once in fresh
HOME/CODEX_HOME/XDG/TMP, with cwd outside Git and no personal credentials/config
copied. The only supplied provider secret was a dummy environment value; the
company model provider used `https://company.invalid/v1` and
`requires_openai_auth = false`. It was deliberately not a real company endpoint.
No account auth file existed before or after. Native inventory selected the
API-curated route, consistent with the matching-version producer's non-backend
auth branch. No login operation was issued.

| Observation | Result |
| --- | --- |
| Version preflight | `codex-cli 0.167.0`, exit 0 |
| App Server startup | One startup, exit 0; initialize response retained |
| Sent protocol | Only `initialize` and `initialized`; no thread/turn/install RPC |
| Native catalog | `.tmp/plugins`, receipt and Git HEAD both `d420d13051bffe4543ed39e30fa46b87148e47dd` |
| Marketplace inventory | `openai-api-curated`, exit 0 |
| Named `--available` query | Exit 0; Superpowers 6.3.0 available, `AVAILABLE` / `ON_INSTALL`, initially not installed |
| Native plugin add | One attempt, exit 0; no retry |
| Receipt identity | `superpowers@openai-api-curated`; cache version `d420d130` |
| Installed manifest | `superpowers` 6.3.0 |
| Complete installed content | 73 files match the official catalog's committed Git blobs; executable permissions also match |
| Final named inventory | Exit 0; installed and enabled |
| Synthetic company configuration | Original model/provider fields retained exactly |
| Original state | 52 protected file hashes, four named personal settings fingerprints, HEAD, four stashes and staged list all unchanged |

Complete content hash:
`2bc88a8ad42d3b2a5f2b7f0b6711b0ae4d18895bfa870dcfeb7c9fc5d31fdba0`.

The wrapper, prepared observer and install helper fingerprints still match the
approved manifest. All command stdout/stderr is retained; native install and
scoped reads had empty stderr. The observer closed the native App Server after
catalog preparation; no process restart or corrected query was needed.

The native sync reached external source services under the approved fallback
scope. Retained state contains a Git checkout with the matching HEAD; individual
network requests and any earlier internal transport attempts were not traced.
The native add wrote only the isolated test cache and plugin enablement settings.
Downloaded files, generated state and logs remain. No cleanup or rollback ran.

## Evidence and verification boundary

Evidence root:
`.superpowers/sdd/2026-11-11-codex-no-account-install/prepared-mlyontal/`.
It includes `run.json`, the approval and once markers, `version.json`, sent
protocol, App Server output, startup result, both pre-install reads, raw native
install receipt, final inventory, installed tree, original-state fingerprints,
and `verification.json`. The independently rerunnable **local-only**
`verify_saved.py` returned exit 0 and wrote `verification-local.json` after
checking saved results, current bytes and preservation. No native command is
run by that verifier. Published summary:
[codex-no-account-native-evidence.json](codex-no-account-native-evidence.json).

Assumptions attacked: an empty inventory alone was insufficient, so the case
required a positive native `--available` entry; a zero add exit alone was
insufficient, so it checked receipt identity, all committed bytes/permissions
and enabled final inventory; the no-account/configuration claim required a
clean environment, no copied credentials, absent auth file, the actual selected
API catalog and preserved provider fields. This is an actual CLI operation,
not a mock that would pass without an installation.

## NOT VERIFIED

The installer ZIP end-to-end flow, arbitrary company endpoint connectivity or
corporate network policy, Windows/Linux, exposed skill/hook/model behavior,
wire-level traffic/billing and a complete whole-computer side-effect audit.
No model request was sent by this observer; that is not a wire-level billing
audit. A synthetic company provider proves configuration preservation, not that
an actual company model service works.

Product runtime, provider hashes, empty acceptance index and R5 were not changed
by this case. No ZIP build, commit, push or release occurred. Integrating this
exact catalog/CLI/platform/payload evidence into installer enablement remains a
separate change; the original colleague-facing cross-platform delivery is not
yet complete.
