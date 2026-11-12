# Codex official catalog initialization probe

Date: 2026-11-11. Status: **APPROVED AND EXECUTED ONCE**.
See the [result and query limitation](superpowers-codex-catalog-result.md):
startup exit 0, official catalog prepared, API-curated name exposed; no install
or model request. This executed proposal does not authorize another run.
Purpose: test the native startup path identified in the
[matching-version source](superpowers-reference-findings.md), without installing
Superpowers, changing product code or starting a model conversation.

## One native startup, in fresh isolated state

Prepared root:
`.superpowers/sdd/2026-11-11-superpowers-codex-catalog/prepared-wiw4qxz0/`.

The exact executable wrapper path/hash, clean environment, cwd outside Git,
fresh HOME/CODEX_HOME/XDG/TMP directories and once-only observer are saved in
`run.json`. No personal auth/configuration is copied. Local preflight must
still return exactly `codex-cli 0.167.0`; otherwise stop before startup.

Start this process once, substituting the resolved installed `codex` executable:

```text
codex -c features.plugins=true -c features.remote_plugin=false -c features.plugin_discovery_prefetch=false -c analytics.enabled=false app-server --listen stdio:// --strict-config
```

Only send these protocol messages, in order, after the matching initialize
response. No thread, turn, login, plugin install or MCP request is permitted:

```json
{"id":1,"method":"initialize","params":{"clientInfo":{"name":"agent-skills-superpowers-catalog-probe","version":"1.0.0"},"capabilities":{"experimentalApi":false,"explicitGatewayOauth":true}}}
{"method":"initialized","params":{}}
```

Observe the native `.tmp/plugins` catalog and `.tmp/plugins.sha` for at most
180 seconds. Do not create/repair those files from the observer. Close stdin
after observation; if necessary terminate only this test process. Keep all
downloaded files, logs, generated databases/settings and partial state.

## Network and native fallback scope

This starts one native catalog synchronization. Its producer can try trusted
Git, GitHub HTTP and, for a missing snapshot, the official export backup in
sequence. This proposal includes those internal fallback transports for that
single startup; it is not a claim of one HTTP request or one wire transfer.
Expected source is `openai/plugins` on GitHub; the source also names
`https://chatgpt.com/backend-api/plugins/export/curated` as a backup, which may
return a download URL. Preserve which route actually worked or failed.

Remote-plugin/discovery prefetch and analytics are disabled for this process.
No model request is sent and no model token charge is planned. No account login
or credential copying is included. If native authentication or unexpected
authorization is required, stop and report it rather than fulfilling it.

## Bounded final observations

If a catalog materializes, run each of these once in the same isolated state:

```text
codex plugin marketplace list --json
codex plugin list --marketplace openai-curated --json
codex plugin list --marketplace openai-api-curated --json
```

These named lists avoid the source code's remote-global catalog fetch branch;
do not run an unqualified plugin list. A nonzero/empty result is evidence, not
permission to rerun. Record native responses plus the actual selected catalog
names, Superpowers entries/versions, commit receipt and metadata form. Do not
substitute expected source values for missing observations.

The helper consumes a start marker and refuses unapproved launch. No process
restart, repeated query, marketplace add/refresh, plugin add, acceptance/hash
update, model/hook action, commit or cleanup is included. A backup snapshot
without an exact commit is not upgraded to verified provenance.

## Expected outcome and limits

The result should establish whether this exact installed CLI can prepare its
official catalog without a model conversation, and which official route is
actually visible with fresh unauthenticated state. It may instead falsify that
candidate path. Either result is useful and must be preserved.

This does not approve adding `openai-api-curated` to the installer, setting
Superpowers hashes, modifying the Claude archive policy or installing any
plugin. Those decisions follow actual observations; the current product and
all old archives/native cases remain unchanged.

Compare named original settings fingerprints and protected product/artifact
hashes before/after. These are bounded checks, not a complete native/network
side-effect audit. Native behavior and all functionality remain **NOT VERIFIED**
until a separately approved case actually runs.
