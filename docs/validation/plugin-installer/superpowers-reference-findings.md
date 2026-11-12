# Superpowers reference-source findings

Date: 2026-11-11. Scope: the user approved exactly two reference fetches and
local inspection. Both fetches succeeded once; no native plugin, App Server,
model or downloaded-code execution occurred. Product code and gates are unchanged.

## VERIFIED: independent Claude payload content

The fetched Superpowers commit is exactly
`bb92a77741419a4ab5f06e711a283343f1ada0c3` (manifest 7.0.0). All 238 committed
Git blobs match the preserved native installation and its saved observation:
same complete path list, byte sizes, SHA-256 values and executable permissions.
The commit contains 183 non-executable and 55 executable files. No committed
path was ignored, normalized or replaced; Git administrative metadata is not
a committed tree entry.

The independently corroborated installed-content hash, using the existing
installer ordering/serialization contract, is:
`d9ae919521df6591becf75601b64bd6e9ca358e389bbe95050f966555a7ef704`.

This closes the independent payload-content gap for the saved Claude 7.0.0
case. It does not establish when `.git` became an archive, prove initial marker
absence, or grant acceptance to the current Claude 2.1.322 binary. No target
hash or production acceptance record was changed.

## VERIFIED: Codex's native initialization producer

The fetched `rust-v0.167.0` source resolved to commit
`086ccc833bc9cf01024ad2dd6af7dbd421b6bf9a`, matching the CLI version used in the
recent installer cases. Relevant source paths and line ranges were retained
with exact file fingerprints in `reference-findings.json` in the evidence root.

| Producer | Observed code contract |
| --- | --- |
| `app-server/src/lib.rs` 495-505, 1009-1037 | Default runtime options start plugin startup tasks when the message processor is created |
| `app-server/src/message_processor.rs` 556-578 | Calls the plugin manager's startup tasks; no thread/turn request is necessary for that call |
| `core-plugins/src/manager.rs` 774-790, 2892-2906 | Starts native curated sync when plugins are enabled, policy permits Git and an authenticated remote global catalog is not active |
| `core-plugins/src/startup_sync.rs` 23-36, 77-170, 197-242 | Fetches OpenAI's official catalog into `.tmp/plugins`, writes `.tmp/plugins.sha`, and can fall back from trusted Git to GitHub HTTP and a missing-snapshot export backup |
| `cli/src/plugin_cmd.rs` 246-280, 841-858 | Named plugin listing consumes existing local curated roots; it does not invoke this startup sync, and a non-global marketplace name avoids the remote-global fetch branch |
| `core-plugins/src/manager.rs` 686-693, 3682-3718 | Catalog selection depends on auth mode; without Codex-backend auth it selects `.agents/plugins/api_marketplace.json` rather than the ordinary curated manifest |

Therefore a bounded **native App Server startup probe** is a candidate for
official preparation without starting a model conversation or writing native
catalog state from the installer. This remains a static inference until tested.
The current product only accepts `openai-curated`; adopting
`openai-api-curated`, if its real entry is eligible, is a separate explicit
scope decision. This investigation does not silently add that provider.

The same source also enables discovery prefetch by default and supports native
transport fallbacks. A concrete probe must name those effects and disable
unnecessary remote/discovery work. Calling an operation a list/startup does
not make it read-only.

## Retained evidence and local corrections

Evidence root:
`.superpowers/sdd/2026-11-11-superpowers-evidence/prepared-_zbibmjg/`.
It contains the approval manifest, once-only fetch markers/results, independent
committed-file list and comparison, extracted source index and exact excerpts.
Machine-readable summary: [superpowers-reference-findings.json](superpowers-reference-findings.json).

One local aggregate check initially sorted full path strings instead of using
the existing Path-component ordering. Every per-file map already matched; the
aggregate assertion failed until the comparison used the documented existing
ordering. This changed only the checker, not payload bytes or product code.
One local Git search also needed `-e` for a pattern beginning with `--`.
Neither correction repeated a fetch or executed any downloaded code.

## NOT VERIFIED

Actual native Codex startup synchronization, current catalog entries and
Superpowers availability on its API-curated route; Claude archive transition
timing/contract and current-version acceptance; cold-start archive trust;
new installer code, native candidate installation, exposed entries or model/
skill behavior. Legal, commercial-cost and general API compatibility claims
are not made by this source-only inspection. Context7 is not exposed here.

The next concrete candidate is the
[isolated Codex catalog probe](superpowers-codex-catalog-proposal.md), requiring
separate approval because it performs a new native download/synchronization.
