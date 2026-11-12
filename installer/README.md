# CLI plugin installer

This archive is a reviewable installer candidate, not evidence of native
platform acceptance. Install Claude Code CLI, Codex CLI, or both first and
retain the authentication/model-provider setup required by your organization.
Codex users with a working company AI endpoint do not need a ChatGPT login
for the verified API-curated installation route. The installer does not configure or
test model endpoints, install either host or change hook trust.

After extracting the entire archive:

- macOS: open `install-macos.command`, or run `bash install-macos.command`.
- Ubuntu/Debian: run `bash install-linux.sh`.
- Windows: run `./install-windows.ps1` in PowerShell under your organization's
  execution policy. No policy bypass is supplied. If the script is blocked,
  ask your administrator or review the policy before continuing.
- With a real Python 3.11+ interpreter: run `python3 install.py` (`python.exe
  install.py` on Windows). Do not probe Windows `py`/Store aliases to install
  a runtime without consent.

Choose Install/update or Remove packages first; Enter selects Install/update.
Then choose a numbered host and use Up/Down to move through packages, Space to
check or uncheck any package, and Enter to confirm. The scrolling selection
screen lists only package names and their skill names. Press `q` or Ctrl+C to
cancel. Unchecking every package exits without installing anything.
Superpowers is strongly recommended but unchecked. Existing installations are
kept by default; choose updates separately. Review source preparation,
dependency installation and plugin installation at their separate prompts.
Enter at a yes/no prompt means no. `q` or EOF cancels; `b` at installation
approval returns to package selection. Earlier approved writes remain.

In Remove packages, every package starts unchecked. Only installed packages
offered by this script appear, including identified earlier manual installs;
an unchecked item is never removed. The preview lists the actual installed
version and qualified marketplace identity before asking for confirmation.
No journal setup, source refresh, dependency installation, dependency prune
or marketplace cleanup runs in removal mode.

Claude personal removal is implemented for the inspected Claude Code
`2.1.322 (Claude Code)` command format. It explicitly passes
`--scope user --keep-data --json`, so project/local/managed installations and
plugin data directories stay. Claude Code may clear that plugin's own saved
options/secrets when its last installation is removed; the preview discloses
this. Work-journal settings, work records, notes and shared tools stay. Disabled
plugins and newer/older installed versions can be selected when their source,
identity and native cache path are identified. Same-name plugins from another
source, duplicate personal records, unknown versions or linked/unsafe cache
paths are kept with an explanation. Superpowers uses its actual identified
installed provider, which can differ from this archive's preferred provider.

Codex removal is offered when a read-only help check confirms the native
`codex plugin remove <plugin>@<marketplace> --json` interface and the installed
plugin inventory/cache match the expected structure. It is not restricted to
one Codex version: official `0.166.0` and `0.167.0` source both expose that
interface. A CLI with a different or unknown interface is kept unchanged. The
native command removes the selected plugin's complete cache entry and Codex
user entry, even when project configuration also references it. The preview
says this may stop those projects from loading the plugin; their configuration
and the plugin's data directory remain. Marketplace and other plugin entries
are not removed.

Before each uninstall, the installer rechecks the selected registration and
the target cache. The preview also identifies the actual configuration
directory: switching a profile link or replacing that directory stops removal
and requires a new preview. Stable ancestor links remain usable; direct linked
cache paths remain withheld. It accepts success only after the native result
and fresh inventory confirm the target is gone, other plugin entries remain,
and (for Claude) protected project files match. This is a conservative check,
not an atomic filesystem transaction. Partial results are reported per
package; failure/cancellation never triggers retry, reinstallation or rollback.

An unrelated plugin from a local/file/unknown source remains registered and
untrusted, while independently identified packages can continue. A same-name
unknown provider is kept, never treated as a trusted install or removal target.
Missing required inventory fields and unknown own-marketplace metadata still
stop writes; an unreadable list never means no plugins are installed.

Claude Code versions besides `2.1.322` remain withheld pending
removal-adapter validation. Codex versions are eligible only when their native
help, inventory and installed cache satisfy the checked interface; an unknown
layout remains withheld. Offline/fake-host checks do not constitute native
removal acceptance on macOS, Linux or Windows.

Each selected package has its own progress bar: checking the current state,
running the native command, then checking the installed files/version. These
are completed phases, not download percentages. A finished package and its
messages form one block, with a blank line before the next package. JSON
command results are captured for verification instead of printed verbatim;
native permission/input prompts on stderr remain visible immediately, with
stdin inherited. Failures include the native error message when provided and
are never retried automatically. A verified native `up_to_date` result is
shown as already up to date.

A Claude plugin installed for both your account and a project is kept in both
places; it does not block unrelated packages. This installer never chooses a
copy to replace. Only one enabled, identified user-owned copy is offered for
an update; ambiguous copies stay unchanged. If the installed-plugin list truly
cannot be read, the installer explains which app is affected and stops that
app before asking for updates or installation. A healthy selected app can
continue independently. Keep the displayed error details for troubleshooting;
removing existing plugins is not a recovery step.

The bundle catalogs exact local plugin payload hashes and versions. A changed
marketplace is withheld for review rather than installed using stale content
descriptions. Sources may still move during a native install; post-install
checks cannot eliminate that race. No native acceptance is implied.

Codex new-install verification is limited to the audited CLI 0.167.0. It checks
the native JSON installation receipt, the previewed CODEX_HOME settings/cache
target (default `~/.codex`), effective enabled state, manifest version and exact
installed payload hash. Receipt stdout is captured; native stderr and stdin
remain interactive (stderr is forwarded immediately). Cache version and manifest version are checked separately.
This does not establish project/managed configuration ownership or runtime skill
behavior. Existing entries remain preserved and marked unverified; updates are
blocked. Unregistered caches and symlinked cache parents are also preserved.
Other Codex versions are withheld pending adapter validation. Native Windows
preference writes/migration still require POSIX locks; shell workflows need
separately supplied tools.

Superpowers uses each host's official catalog, without requiring equal versions:
Claude `claude-plugins-official`, observed manifest `7.0.0`, points to
`https://github.com/obra/superpowers.git` pinned at
`bb92a77741419a4ab5f06e711a283343f1ada0c3`; Codex `openai-curated`, observed
manifest `6.3.0`, points to `./plugins/superpowers` within its native-managed
catalog. This candidate also recognizes native `openai-api-curated`
using `.agents/plugins/api_marketplace.json`; native inventory chooses the
route, not the configured model endpoint URL or a guessed login state. Exactly
one official catalog must be exposed. Each catalog needs its own exact native
acceptance; evidence for one name never authorizes the other. R5 predates this
adapter change and the capability records below. Catalog origin and payload origin are checked separately. An existing
provider always remains, even if newer, disabled or from another catalog.

Codex official setup uses native `/plugins`; no ordinary Git marketplace-add
or refresh can initialize that reserved catalog. The installer only reads a
native-prepared catalog and commit receipt. A missing raw source URL stays
absent in native inventory; catalog identity/path/commit/entry/payload evidence
must corroborate managed origin. Missing or uncertain state affects only
Superpowers; an actual global inventory failure stops the affected host.

For a colleague already using a company AI endpoint: keep the existing
`model_provider`, provider `base_url`, authentication environment variables and
organization policy. No endpoint URL, key or login is requested by this
installer. If Codex exposes `openai-api-curated`, the adapter checks that
catalog. If no official catalog is prepared, use the native `/plugins` flow;
the installer does not launch a model conversation or initialize it silently.
Access to a company model endpoint does not imply access to GitHub/plugin
download hosts. When those sources are blocked or native policy disables
plugins, report the actual restriction and ask the administrator; this
installer supplies no mirror, proxy, certificate bypass or policy override.
Company endpoint connectivity and actual installation remain separate checks.

`provider-acceptance.json` includes exactly two native capability records with
verified payload hashes. Automatic Superpowers proposals are enabled only for:

| Host / CLI | Platform / architecture | Catalog | Native manifest / account state tested |
| --- | --- | --- | --- |
| Claude Code `2.1.322 (Claude Code)` | macOS arm64 | `claude-plugins-official` | 7.0.0; logged in and logged out |
| Codex `codex-cli 0.167.0` | macOS arm64 | `openai-api-curated` | 6.3.0; no account login, synthetic company provider preserved |

The two sanitized source summaries are included under `acceptance-evidence/`
and referenced directly by each record. They prove native CLI capability, not
a native run of this exact ZIP. Windows/Linux, other architectures/CLI versions,
and Codex `openai-curated` have no transferable record: Superpowers and its
dependency proposals remain withheld there. Other independently eligible
packages can continue. A Claude catalog already in unsupported archive form
also remains withheld; the verified cases used native Git catalogs. No archive
trust exception was added.

Enablement requires the exact CLI version, platform, architecture, catalog,
entry, manifest version and complete payload hash. A historical catalog commit
change alone does not invalidate an unchanged proven payload, but any observed
source change after consent stops that operation. Codex's native cache version
must equal the current catalog SHA's first eight characters, separately from
the manifest version. No state/cache repair, retry or rollback is performed.

Installation, exposed entries in a restarted host, and real behavior of the
seven workflows are separate evidence layers. Neither metadata presence nor a
synthetic test proves model behavior. The native and functional proposals in
the repository require separate approval before external operations.

Claude Code 2.1.322 creates `.in_use/<pid>` files in a plugin cache while a
session uses it. Post-install verification recognizes only the inspected
non-executable regular-file marker schema for that exact CLI version; unknown
marker entries, symlinks, payload changes and other extra files still fail.
Catalog/source hashes are unchanged, and existing session markers are not
removed. Other CLI versions do not receive this exception.

Optional `work-journal` configuration uses `~/.agent-skills/activities` for new
work records unless an existing `CLAUDE_ACTIVITIES_DIR` override is set. Adding
your notes directory lets `work-log-analyzer` search your notes alongside your
work records; notes are optional and can be added later in `work-journal.json`.
`report-generator` uses those skills for reports. Existing
valid settings are displayed and reused without asking for paths or writing
anything; private extension fields are not displayed. Invalid settings are
preserved and reported. New settings with optional notes are created only
after the selected host's compatible work-journal runtime is verified; older
installed versions must be updated first. Without settings, setup explains these uses before
asking for an optional notes directory, previews settings/directory writes,
and requires separate approval. It never replaces an existing settings file
and never moves or reads activity/note contents.
Installation status, configuration and hook authorization are
reported separately. Review `provenance.json` for the source revision and exact
input/payload hashes. The archive contains no credentials or personal settings.
