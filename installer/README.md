# CLI plugin installer

[English](README.md) | [繁體中文](README.zh.md)

This archive is a reviewable installer candidate, not evidence of native
platform acceptance. Install Claude Code CLI, Codex CLI, or both first and
retain the authentication/model-provider setup required by your organization.
Codex users with a working company AI endpoint do not need a ChatGPT login
for the verified API-curated installation route. The installer does not configure or
test model endpoints, install either host or change hook trust.

After extracting the entire archive on macOS, open `install-macos.command` or
run `bash install-macos.command`. This ZIP provides only the macOS installer
entry point; Linux and Windows launchers remain available in the source
repository but are not included in this archive. The bundled `install.py` is
used by the macOS launcher and is not a separate supported entry point.

Choose Install/update or Remove packages first; Enter selects Install/update.
Then choose a numbered host and use Up/Down to move through packages, Space to
check or uncheck any package, and Enter to confirm. The scrolling selection
screen lists only package names and their skill names. Press `q` or Ctrl+C to
cancel. Unchecking every package exits without installing anything.
Superpowers is strongly recommended but unchecked. Claude Code offers an
update choice only for one identified personal installation; existing Codex
installations and Superpowers are kept by this installer. Review source preparation,
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

For removal only, Claude Code versions besides `2.1.322` remain withheld pending
removal-adapter validation. Codex removal is offered only when its native
help, inventory and installed cache satisfy the checked interface; an unknown
layout remains withheld. Offline/fake-host checks do not constitute native
removal acceptance on macOS, Linux or Windows.

Each package that runs has its own progress bar. It shows the native Claude Code or Codex command running; it is not a download percentage. If that command exits successfully, the installer reports success. If it exits with an error, the installer reports failure. It does not retry or roll back automatically.

For plugin installs and updates, the installer does not check the Claude Code or Codex version, the Superpowers version, or the installed files after the native command succeeds. A success message means the host command reported success; it does not confirm that the plugin appears after a restart or that every skill works.

Plugins are downloaded by Claude Code or Codex from the configured marketplace. The installer does not compare marketplace files with the copies packaged in this ZIP, so the marketplace may provide a different or newer package. The preview lists only the packages the installer plans to install or update. Existing installations are kept unless you select an update; an existing Superpowers installation is always kept by this installer.

Superpowers is strongly recommended for development work, but is optional and unchecked by default. Claude Code uses its official `claude-plugins-official` catalog. Codex uses the official catalog prepared through its native `/plugins` screen; if more than one official Superpowers catalog is configured, choose one there before running the installer. The installer does not compare Superpowers versions or restrict installation to the CLI versions used in earlier acceptance runs.

A Claude plugin installed for both your account and a project is kept in both places; it does not block unrelated packages. This installer never chooses a copy to replace. Only one enabled, identified user-owned copy is offered for an update; ambiguous copies stay unchanged. If the installed-plugin list truly cannot be read, the installer explains which app is affected and stops that app before asking for updates or installation. A healthy selected app can continue independently.

Optional `work-journal` configuration uses `~/.agent-skills/activities` for new
work records unless an existing `CLAUDE_ACTIVITIES_DIR` override is set. Adding
your notes directory lets `work-log-analyzer` search your notes alongside your
work records; notes are optional and can be added later in `work-journal.json`.
`report-generator` uses those skills for reports. Existing
valid settings are displayed and reused without asking for paths or writing
anything; private extension fields are not displayed. Invalid settings are
preserved and reported. New settings with optional notes are created only when the host reports one
enabled work-journal installation; the installer does not check its version or
files. Without settings, setup explains these uses before
asking for an optional notes directory, previews settings/directory writes,
and requires separate approval. It never replaces an existing settings file
and never moves or reads activity/note contents. Journal setup is optional and
separate from plugin installation. The installer does not change hook trust.
Review `provenance.json` for the source revision and exact input/payload hashes.
The archive contains no credentials or personal settings.
