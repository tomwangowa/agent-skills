# Superpowers official-source policy and implementation constraints

Date: 2026-11-10. Status: **SOURCE POLICY CONFIRMED; IMPLEMENTATION DESIGN PENDING**.
The user confirmed official catalogs first, accepting host-specific versions
and separately verifying required functionality. No installer behavior or
provider configuration was changed in this investigation. No marketplace was
registered/refreshed, no plugin installed and no model session invoked.

## Confirmed policy and retained requirements

The [approved design's new source-policy section](../../superpowers/specs/2026-11-09-cross-platform-plugin-installer-design.md)
records the user's decision. `7.0.2` was an observed provider identity, not a
previously approved minimum version. Keep Superpowers strongly recommended but
unchecked; preserve existing installs/settings and explicit source/installation
consent. Do not replace or downgrade an existing maintainer provider merely
because the official catalog advertises an older version.

This policy selects a preferred distribution route. Official listing is not
proof of active vendor endorsement, compatibility, runtime registration or
passing behavior tests.

## Source snapshots and required files

These are public Git catalog snapshots, not an authenticated Codex remote
global-catalog lookup. Mutable catalogs must be rechecked before a proposed
native operation; a version observed here is not a permanently pinned release.
Codex `main` file observations are recorded by individual blob SHA; a complete
release commit and installed-payload hash still need to be selected and checked
before native acceptance.

| Host | Preferred catalog | Catalog repository | Plugin source | Observed manifest version |
| --- | --- | --- | --- | --- |
| Claude Code | `claude-plugins-official` | `anthropics/claude-plugins-official` | `obra/superpowers` at `bb92a77741419a4ab5f06e711a283343f1ada0c3` | `7.0.0` |
| Codex | `openai-curated` | `openai/plugins` | relative `./plugins/superpowers` | `6.3.0` |

The upstream installation guide directs Claude users to Anthropic's official
catalog (and offers a maintainer alternative), and Codex users to OpenAI's
official catalog. See [upstream instructions](https://github.com/obra/superpowers/blob/main/README.md#installation),
[Claude catalog entry](https://github.com/anthropics/claude-plugins-official/blob/main/.claude-plugin/marketplace.json),
[its pinned plugin manifest](https://github.com/obra/superpowers/blob/bb92a77741419a4ab5f06e711a283343f1ada0c3/.claude-plugin/plugin.json),
[Codex Git catalog](https://github.com/openai/plugins/blob/main/.agents/plugins/marketplace.json)
and [Codex bundled manifest](https://github.com/openai/plugins/blob/main/plugins/superpowers/.codex-plugin/plugin.json).

All seven required source files were retrieved for each host/version:
`writing-plans`, `test-driven-development`, `systematic-debugging`,
`executing-plans`, `subagent-driven-development`, `requesting-code-review`,
`finishing-a-development-branch`. Their frontmatter names match. Six of the
seven paired files have different content/blob hashes; finishing-a-development-
branch matches exactly. File presence therefore cannot stand in for equivalent
workflow behavior. The exact file URLs/blob SHAs and fetched content are kept
in ignored `superpowers-official-source-confirmed-20261110.json` under the task
evidence directory.

## Counter-evidence: a URL substitution is insufficient

The existing installer assigns one external marketplace/source/version to both
hosts, maps external source-add to `superpowers-dev`, hashes only repository-local
payload layouts and limits Codex receipt verification to `tomwangowa`. Its
Codex inventory filter also skips other catalog URLs. Consequently, merely
changing `providers.json` could miss an installed provider, misidentify its
source or run an unverifiable install. The source model and its consumers need
a reviewed, bounded change together.

Claude distinguishes marketplace sources from plugin sources. Its official
Superpowers entry references a different Git repository at a fixed commit,
so the plugin payload is not a relative directory inside the official catalog.
See [Claude's source reference](https://code.claude.com/docs/en/plugins/marketplace-reference#plugin-sources).

There is an additional **Codex 0.167.0** constraint. The tagged implementation
reserves `openai-curated`; ordinary Git marketplace-add supplies no managed-name
exception and is rejected when the downloaded manifest uses that reserved
name. The official Git URL does not bypass this check. This is verified static
producer/policy evidence, not an attempted native command. See
[source/name validation](https://github.com/openai/codex/blob/rust-v0.167.0/codex-rs/core-plugins/src/marketplace_policy.rs#L318).

The native curated catalog has its own synchronization state and SHA receipt;
installation under its identity can derive a cache version from the catalog
SHA rather than the plugin manifest version. A third-party installer must not
populate or rewrite this native state to impersonate the official catalog.
See [native curated synchronization](https://github.com/openai/codex/blob/rust-v0.167.0/codex-rs/core-plugins/src/startup_sync.rs#L30),
[curated installation version](https://github.com/openai/codex/blob/rust-v0.167.0/codex-rs/core-plugins/src/manager.rs#L2325)
and [cache-version conversion](https://github.com/openai/codex/blob/rust-v0.167.0/codex-rs/core-plugins/src/loader.rs#L523).

Official OpenAI documentation supports qualified plugin add/list, including add's
actual installed-path receipt, and the native `/plugins` browser. These docs do
not establish that a fresh, unauthenticated temporary CLI can initialize this
particular official catalog through an automation-safe command. Keep that
capability NOT VERIFIED. See [developer commands](https://learn.chatgpt.com/docs/developer-commands#codex-plugin)
and [plugin browser](https://learn.chatgpt.com/docs/plugins#plugin-browser-in-codex-cli).

## Candidate implementation paths, not yet approved

| Candidate | Mechanism | Trade-off / likely failure | Relative effort |
| --- | --- | --- | --- |
| A. Host-specific native catalog adapters (recommended) | Separate catalog origin from plugin payload source/ref/path; use native install only when origin, selected version and payload can be verified. For Codex, consume its native prepared official catalog; if absent/unverifiable, show native setup instructions and leave only Superpowers pending. | Preserves automatic installation where supported. Catalog changes or missing managed state can block one host; never silently reuse old acceptance or fall back to the maintainer catalog. | Moderate, bounded to provider metadata, adapters, planning/verification, UI and tests |
| B. Official installation guidance for both hosts first | Keep Superpowers installation manual, display exact official entry and prerequisites, then verify native installed inventory/entry state separately. | Smaller change but does not deliver the intended automatic Superpowers branch. Manual actions may diverge from installer status, so completion stays pending until corroborated. | Small |

Both candidates preserve the selected official-source policy. Neither creates
a private fork/renamed official catalog, embeds Superpowers into our packages,
or silently replaces an existing provider. The broad technology choice remains
the working native CLI/Python prototype; the new uncertainty is the official
catalog preparation and payload-verification boundary, not a new platform or
library choice.

Candidate A's minimum proposed data needs are: host; catalog identity and
provenance kind (configured Git versus native-managed); catalog ref/commit;
plugin source kind/repository/ref or relative path; plugin manifest version;
expected payload/required-file evidence; and per-host/version/platform
acceptance state. A native cache version remains separate. Field names/schema
and automation details are not yet approved by the source-policy decision.

Use available evidence to distinguish an absent plugin from an unknown
provider. Unverified scope/root/provenance, duplicate providers, disabled state,
conflicting sources and existing caches remain preserved. A model must not
invent `scope=user` for Codex or use an arbitrary cache path as proof of a
registered official source. No unqualified remote catalog query is an offline
probe. Do not refresh an existing official catalog automatically: that changes
metadata for other packages as well and requires its own preview/consent.

## Proposed acceptance, all Superpowers runtime cases NOT RUN

Keep three evidence levels distinct, keyed by CLI version, plugin version,
source commit and platform:

1. **Installation:** exact qualified source/identity, actual installed manifest
   and payload, native inventory enabled state and exit codes; retain actual
   installed-path evidence. This is not skill registration or functionality.
2. **Entry availability:** read the current host's exposed native skill metadata
   and owning provider. Verify the seven selected entries belong to the actual
   installed version. Do not substitute source directories, registry mentions
   or a package-cache folder for this evidence.
3. **Required behavior:** run selected branches on a new disposable fixture,
   with explicit boundaries and retained outputs. Test the expected normal
   result and a requirement-specific failure case. Do not infer all behavior
   from one loaded instruction or a passing build.

| Entry | Proposed behavior evidence and boundary |
| --- | --- |
| `writing-plans` | Produces a concrete plan from a small approved fixture spec; waits at the implementation approval boundary |
| `test-driven-development` | Demonstrates a real failing fixture test before the minimal change and a passing result afterward |
| `systematic-debugging` | Reproduces a controlled fixture failure and establishes its cause before proposing the fix |
| `executing-plans` | Follows selected approved steps, reports evidence and stops on a forced failed prerequisite |
| `subagent-driven-development` | Registration/loading alone is an entry check; actual delegation is a separate test requiring explicit agent/model/data scope approval |
| `requesting-code-review` | Obeys runtime-native reviewer routing and approved scope; does not invoke retired Gemini or send a diff to an unapproved external reviewer |
| `finishing-a-development-branch` | Presents integration choices and preserves explicit commit/push/merge boundaries; no real integration is needed for a fixture check |

Behavior cases invoke a real model/session and may consume tokens. Before any
such run, propose exact CLI/model, prompts, fixture files, outputs, writes,
agent use, stop conditions and cost boundary. This source-policy confirmation
does not authorize those calls. Test hooks separately through the native trust
flow; no automatic hook authorization or permanent personal configuration
change is included. Missing/unverified branches remain explicitly unavailable.

## Current verification and next gate

VERIFIED: the user's source-policy decision; public catalog/plugin source
snapshots; all 14 required source files and frontmatter identities; the tagged
Codex reserved-name/managed-state behavior in code; current adapter/model limits.

NOT VERIFIED: either official Superpowers native installation using this
installer; official Codex catalog initialization in a fresh isolated CLI;
current native exposed entries; behavior/hook compatibility; other platforms;
catalog race/payload bookkeeping during native materialization. No additional
model, install, update or source-registration action was executed here.

The record uses technical-decisions:critical-research to challenge uniform
source handling before relying on the catalog entries. The three central
assumptions were attacked: same name implies same content (false for six
required files), same Git-add mechanism works for both hosts (rejected by Codex
policy), and official listing implies runtime compatibility (unproven).

The user selected completion of candidate A's supplementary design and plan.
The [design](../../superpowers/specs/2026-11-10-superpowers-official-sources-design.md)
and [conditional implementation plan](../../superpowers/plans/2026-11-10-superpowers-official-sources.md)
are prepared together for review, not implementation approval. Runtime changes
and new native/model runs retain separate review/authorization boundaries. R3
remains unchanged, with its prior quality-gates native evidence intact.
