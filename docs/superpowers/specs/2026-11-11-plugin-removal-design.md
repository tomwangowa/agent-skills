# Native plugin removal

Status: user approved the separate removal flow and the Codex shared-cache
impact. Installer changes are authorized. No native operation, commit, push or
publication is authorized.

## Scope and flow

The same archive starts with Install/update or Remove packages. Removal has
its own host selection and an unchecked package menu using the existing
Up/Down, Space and Enter controls. Only installed packages offered by this
script are considered, including earlier manual installs; unrelated plugins
are excluded. A package's qualified native identity and actual installed
version, not the bundled version, determine the removal target.

Claude removal requires one confirmed personal installation; project/local and
managed records remain intact. Codex removal targets the shared cache and the
Codex user plugin entry, even if project configuration also refers to that
plugin. Disabled entries remain eligible. Unidentified source, ambiguous
records, unsafe cache paths or unsupported CLI versions are kept with a plain
explanation. Missing or unreadable inventory never becomes an empty successful
removal.

Preview names each package, installed version, marketplace and impact scope:
Claude personal installation or Codex shared cache. The Codex preview warns
that projects referencing the plugin may stop loading it; their configuration
files remain unchanged. One explicit confirmation authorizes exactly that
sealed plan; cancellation and an empty selection execute no mutation. Each
action rechecks its target, runs once, then re-reads inventory and compares
other installed records. The existing per-package phase bars and blank result
separators are retained. Failure, cancellation and timeout never trigger
retry, rollback or cascading removal. A zero exit code alone is not verified
success.

## Native boundaries

For inspected Claude Code `2.1.322 (Claude Code)`, use the qualified native
uninstall command with `--scope user --keep-data --json`. No dependency prune,
marketplace removal, direct cache deletion, configuration rewrite or hook
trust action is supplied. Native uninstall can clear that plugin's own saved
options/secrets; preview discloses this separately from preserved plugin data.
The script preserves work-journal configuration, records, notes and third-party
tools and never enters journal setup while removing packages.

For Codex, use the qualified native `codex plugin remove
<plugin>@<marketplace> --json` command when the CLI's read-only help output
confirms that selector and JSON interface. The inventory must also match the
known marketplace/plugin JSON schema, and the installed target must have one
source-identified record under the resolved `CODEX_HOME`. This avoids tying
removal to one release number while keeping unknown command or inventory
formats ineligible. Codex `0.166.0` and `0.167.0` expose the same removal
interface in their official source.

The native command removes that plugin's complete cache entry and its Codex
user plugin entry; it does not remove the marketplace, plugin data or project
configuration. A project that still references the plugin may not load it until
the plugin is installed again. The preview explicitly names the shared-cache
effect. Before execution, seal the resolved `CODEX_HOME`, plugin record and
cache contents; immediately before each command, recheck that the removal
interface is still available. After execution, require the native identity
receipt, target absence, target-cache absence and unchanged other installed
records and marketplaces. Unknown or changed interfaces remain withheld.

Superpowers is removable only when the installed record is identified as the
upstream package; a same-name plugin is insufficient evidence. Existing
providers can differ from the installer's preferred provider and version.
No catalog refresh or download is needed to remove an identified installation.

## Approach and trade-off

Use a mode picker in the existing entry and a separate removal planner/UI,
reusing immutable actions, once-only execution, native runner, selector and
progress. This keeps one entry for colleagues; the risk of choosing the wrong
mode is bounded by unchecked defaults and the removal-specific preview.
Separate uninstall launchers are a viable alternative but add files users
must distinguish and do not remove the need for a final preview.

No new dependency or protocol is introduced. Existing native CLI behavior is
reused; Claude uses its explicit user scope while Codex exposes a shared-cache
operation. This accepts the risk that a project still referencing a removed
plugin will need it installed again. Native installation and removal
acceptance remain separate from offline presentation/contract tests.

## Validation

Tests use disposable settings and filesystem-backed fake CLIs. Cover Claude
personal removal while project records/data remain, Codex shared-cache removal
with project configuration left intact, manual/newer/disabled installs,
qualified providers, empty/cancelled selection, stale state, ambiguous or
unsafe targets, native errors, misleading success, unverified postconditions,
partial success and interruption. Drive the newly packaged launchers through a
real PTY with fake hosts. Installer regression suites, package/config checks,
syntax/catalog validation, reproducible builds, provenance and exact-extraction
secret scanning remain separate checks. Preserve all earlier archives and the
baseline personal settings/registries. Native acceptance remains NOT VERIFIED
unless separately authorized and performed.
