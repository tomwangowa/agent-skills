# Codex and Superpowers capability audit

Sources inspected: 2026-11-09; report checked: 2026-11-10 (Asia/Taipei).
Baseline: Codex CLI `0.167.0`, installer candidate R2.
This is a read-only capability investigation and a proposed repair scope.
No installer behavior changed and no new native plugin operation ran.

## Decision

Codex is not blocked by a total absence of installed-path information:
`codex plugin add ... --json` returns `installedPath`. The installer currently
discards that command output and relies on an inventory format without this
field. A bounded repair for **new installations** is feasible; existing-plugin
updates need additional configuration and active-version evidence.

Superpowers cannot be repaired by replacing one repository URL. Its recommended
marketplaces differ by host, and their current payload versions differ from
the candidate's expected `7.0.2`. Retain the existing provider and automation block until
the selected host/source/version has isolated native acceptance.

## What was actually inspected

- Installed Codex CLI `0.167.0` exported its experimental JSON schema with
  `codex app-server generate-json-schema --experimental --out <scratch>`.
  This exited 0 in fresh HOME/CODEX_HOME/XDG/TMP directories. It did not start
  an App Server session or execute a plugin request.
- Producer code was read from OpenAI's `rust-v0.167.0` tag, matching the local
  CLI version. Current official documentation was checked against this code.
- Public upstream README files and marketplace/plugin manifests were retrieved
  through read-only GitHub calls. These network reads did not register a
  marketplace, install a plugin, start a model session or authorize hooks.
- Evidence is kept in the ignored task directory
  `.superpowers/sdd/2026-11-09-cross-platform-plugin-installer/capability-audit-rlrqfp80/`:
  `protocol/` contains the generated schema; `source-evidence.json` contains
  source URLs, line ranges and relevant manifest snapshots/blob SHAs.

## Codex: installation receipt and configuration ownership

The tagged CLI producer serializes `pluginId`, `name`, `marketplaceName`,
`version`, `installedPath` and `authPolicy` after a successful add. These are
fields from the actual installation outcome, rather than a guessed cache path.
See [CLI add/result implementation](https://github.com/openai/codex/blob/rust-v0.167.0/codex-rs/cli/src/plugin_cmd.rs#L139).

The local installation implementation copies/materializes the package through
the store, then calls `set_user_plugin_enabled` for the selected CODEX_HOME.
That proves the operation's write target in this implementation. It does not
prove the effective enabled state after other configuration layers are applied.
See [installation implementation](https://github.com/openai/codex/blob/rust-v0.167.0/codex-rs/core-plugins/src/manager.rs#L2325).

Consequences for the repair:

1. Preserve and strictly parse the successful add result; require the expected
   plugin/marketplace identity, cache version and an absolute existing directory.
2. Hash the installed package and check its manifest version separately from
   the host's cache version, then re-read its
   effective inventory state. A zero exit code or an asserted receipt alone
   must not count as verified installation.
3. Model installation write target and effective configuration ownership
   separately. Do not fill Codex's missing `scope` with Claude's literal
   `user`, and do not use a skill's `scope` as plugin ownership evidence.
4. If the receipt is absent, malformed, contradictory or points elsewhere,
   report an unverified partial result and preserve the installation. Do not
   retry or uninstall automatically.

This requires changes to the host adapter, action-result model, execution
verification and tests. Existing Claude inventory semantics can stay intact.

## Codex: what reads can and cannot prove

The exact-version schema exposes `plugin/read`, `skills/list` and `config/read`.
Plugin details have skill paths, but no universal installed-root/scope field;
configuration results expose `layers` and `origins`. The install protocol
response itself has only `appsNeedingAuth` and `authPolicy`, so it cannot replace
the CLI's installation receipt. OpenAI documents generating protocol definitions
for the installed CLI in its [App Server reference](https://learn.chatgpt.com/docs/app-server).

The native detail producer selects paths differently by source: an installed
Git/npm plugin uses its active cache root; a local source uses its source
directory, including for installed packages. Therefore a detail skill path is
not a general installed-root authority. Other source materialization paths can
perform filesystem/network work; an operation's name alone is not proof that
the whole App Server request/startup is side-effect free. No App Server request
was executed in this audit. See [detail path selection](https://github.com/openai/codex/blob/rust-v0.167.0/codex-rs/core-plugins/src/manager.rs#L2691)
and [source materialization](https://github.com/openai/codex/blob/rust-v0.167.0/codex-rs/core-plugins/src/loader.rs#L1769).

For existing installs, the native store constructs roots from CODEX_HOME,
marketplace identity and active version. Active-version selection prefers a
`local` directory when present, otherwise orders valid directory versions;
choosing the newest mtime or matching the marketplace's advertised version is
incorrect. This permits a version-specific fallback proposal, provided CLI
inventory, configuration ownership, manifest and content checks corroborate it.
Cache existence alone remains insufficient. See [store roots](https://github.com/openai/codex/blob/rust-v0.167.0/codex-rs/core-plugins/src/store.rs#L112)
and [active-version selection](https://github.com/openai/codex/blob/rust-v0.167.0/codex-rs/core-plugin-common/src/installed.rs#L47).

Keep existing-plugin updates blocked until this ownership/read path is validated
in isolation, including project/managed overrides, disabled state, multiple
versions and missing cache files. A future App Server adapter is optional;
its schema availability does not establish safe operational behavior.

## Superpowers: host-specific source and version evidence

The upstream installation instructions recommend Anthropic's official
marketplace or the maintainer's marketplace for Claude, and OpenAI's official
marketplace for Codex. See [Superpowers installation instructions](https://github.com/obra/superpowers/blob/main/README.md#installation).

These are the manifest snapshots retrieved in this audit; mutable branches may
change after this date:

| Route | Marketplace identity | Actual selection evidence | Version evidence | Matches candidate 7.0.2? |
| --- | --- | --- | --- | --- |
| Claude official | `claude-plugins-official` | Git source `obra/superpowers` pinned to `bb92a77741419a4ab5f06e711a283343f1ada0c3` | Plugin manifest at that commit: `7.0.0` | No |
| Claude maintainer | `superpowers-marketplace` | Git URL `https://github.com/obra/superpowers.git`, without a pinned ref/SHA in the entry | Marketplace entry and current upstream manifest: `7.0.2` | Candidate only; mutable source and native acceptance unresolved |
| Codex official | `openai-curated` | Local package `./plugins/superpowers` within `openai/plugins` | Bundled `.codex-plugin/plugin.json`: `6.3.0` | No |
| Current installer development source | `superpowers-dev` | Direct `obra/superpowers` repository and its bundled development manifests | Previously inspected provider: `7.0.2` | Identity evidence only; not accepted as a production route |

Sources: [Claude official entry](https://github.com/anthropics/claude-plugins-official/blob/main/.claude-plugin/marketplace.json),
[manifest at its pinned commit](https://github.com/obra/superpowers/blob/bb92a77741419a4ab5f06e711a283343f1ada0c3/.claude-plugin/plugin.json),
[maintainer entry](https://github.com/obra/superpowers-marketplace/blob/main/.claude-plugin/marketplace.json),
[upstream manifest](https://github.com/obra/superpowers/blob/main/.claude-plugin/plugin.json),
[Codex official entry](https://github.com/openai/plugins/blob/main/.agents/plugins/marketplace.json),
[Codex bundled manifest](https://github.com/openai/plugins/blob/main/plugins/superpowers/.codex-plugin/plugin.json).

Codex `0.167.0` recognizes `.claude-plugin/marketplace.json` as a fallback after
its native marketplace paths. The maintainer repository's missing
`.agents/plugins/marketplace.json` therefore does **not** prove incompatibility.
It also does not prove its Git source, hooks or skills work in Codex. See
[manifest discovery](https://github.com/openai/codex/blob/rust-v0.167.0/codex-rs/core-plugins/src/marketplace.rs#L20).

The provider model needs separate fields for marketplace repository/identity,
plugin repository or relative content path, selected ref/commit, declared
manifest version and expected payload hash. A matching name or homepage cannot
prove equivalent package content; the official Codex package has its own
manifest, and its cache version may also be derived from a curated catalog SHA.
Existing installations from another marketplace must remain untouched.

Recommended candidate policy: retain the candidate expectation of `7.0.2`, show the official
routes' version mismatch, and evaluate the maintainer route separately per host.
Do not silently downgrade to an official route or relabel `superpowers-dev`.
Whether to accept an older official version is a user decision, not an adapter
normalization rule.

## Proposed next increments and acceptance

1. **Codex new-install receipt only:** retain command results, introduce
   host-specific ownership evidence, and add offline malformed/mismatched
   receipt and conflicting-state cases. Keep existing updates and external
   Superpowers installation blocked. This is the smallest useful repair.
2. **Existing Codex inventory/update:** validate configuration origins and active
   cache selection, then test project/managed overrides and partial state before
   allowing updates. Requires a separately approved isolated native run.
3. **Superpowers source model:** represent the per-host mappings above, require
   source/version/content verification, and prepare one explicitly selected
   native route. No route is automatically accepted by this report.

Before native acceptance, present exact commands, source/ref, temporary config
roots, expected downloads/writes and verification conditions. Approval of this
audit did not authorize those operations. Do not copy personal credentials,
start a model session, enable hooks automatically or perform retries.

## VERIFIED / NOT VERIFIED

VERIFIED: exact installed-version schema export; tagged native field producers,
root/version-selection logic and manifest fallback; public source/manifest
snapshots; current installer's missing receipt/ownership handling. The report's
five local links, both edited documents' whitespace and source-evidence JSON
passed deterministic checks. All 25 R2 build inputs and 21 hashed archive entries
still match; the archive SHA-256 is unchanged. No paths are staged and the four
original stashes remain. See ignored `audit-checks.json` beside source evidence.
An initial schema inspection looked for a standalone `PluginSummary.json` and
failed; the corrected inspection read its nested definition and exited 0.

NOT VERIFIED: actual Codex add result on this machine; operational App Server
read/startup effects; effective plugin configuration ownership; either CLI's
Superpowers installation or skill/hook compatibility; other OS/architecture
combinations. Static source and schema do not prove these runtime behaviors.

Assumptions challenged: official sources may lag the candidate version (observed
on both hosts); skill paths may refer to source directories (confirmed by
producer code); cache version may differ from manifest version (curated route);
cache presence may disagree with effective enablement (still requires native
validation). No completion claim is made for the overall installer feature.
