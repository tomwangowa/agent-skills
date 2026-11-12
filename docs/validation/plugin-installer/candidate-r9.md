# Installer candidate R9: scoped copies and actionable messages

Date: 2026-11-11. **The duplicate-scope regression and message/flow repair are
verified offline and through the relocated macOS launcher with fake hosts.
Native R9 installation has not run.**

## Cause and behavior

The user's screenshot reported `Multiple scopes for one plugin identity` and
then still asked which installed packages to update. Read-only inspection of
the registered plugins found two `skill-creator@claude-plugins-official`
entries, one project-scoped and one user-scoped. Replaying anonymized metadata
through the unchanged R8 adapter reproduced that exact host-wide error. No
fresh native inventory query was performed, and no private project path or
credential was copied into the fixture.

Claude Code supports the same plugin at multiple installation scopes; its
[documented rules](https://code.claude.com/docs/en/plugins/install#choose-an-install-scope)
define user, project and local installations and precedence between them.
R8 incorrectly rejected an unrelated plugin's repeated identity before it
considered the selected packages individually.

R9 retains every Claude installation record instead of collapsing entries or
choosing a scope. An unrelated scoped plugin no longer blocks a new package,
and only repeated Superpowers identities affect its provider-local uncertainty.
The selected target's existing multiple copies still cannot be updated or
duplicated; its per-package planning, recheck and receipt requirements remain.
Codex duplicate rejection and update execution/ownership protection are
unchanged.

The UI names the existing plugin and describes its account/project locations:

```text
"skill-creator": already installed for a project and your account. All existing copies will be kept.
This installer will not update these copies. Other selected packages can continue.
```

Only a single enabled, identified user-owned Claude copy is offered for an
update. The former `update requires selection` text becomes:

```text
1. attention-mod: already installed; the current version will be kept.
Press Enter to keep these versions. To request an update instead, enter its number.
```

An actual inventory/schema failure still protects the affected app. The UI
explains that its installed-plugin list cannot be read, that no selected plugin
for that app will be installed/updated, and asks the user to close the installer
and retain the following details for troubleshooting. When every selected app
is blocked it stops immediately, without update/install prompts or dependency
writes. A healthy selected app can continue independently. Existing plugins
are never removed as a recovery action.

## Artifact

- R9 ZIP (local artifact; not included in the repository)
- SHA-256 (local artifact; not included in the repository)
- Size: **59,461 bytes**.
- SHA-256: `31cc34fa6df68627bfab4ed552256e7efa2f1be192fdd6cc9d40beea5b84c18e`.
- 28 ZIP entries, 27 payload-file hashes and 31 input hashes.
- Repeated offline builds produced identical bytes. Catalog, provider mapping
  and capability records are byte-identical to R8; package versions/payloads
  and the R8 keyboard selector are unchanged.

R8/R7 and all earlier archives/evidence remain intact. The four checked personal
settings/registry files, HEAD, four stashes and empty staged state are preserved.
The earlier temporary skill-link/hook changes are neither expanded nor restored
by this repair. No commit, push, release, account operation or real native/model
invocation was performed.

## Evidence

| Check | Result |
| --- | --- |
| Original R8 adapter replay | exact repeated-scope error reproduced from anonymized registry-shaped data |
| Initial scoped regression tests | four failed against R8 |
| Final installer suite | 113 tests: 112 passed, one PowerShell skip; exit 0 |
| Package/config tests | 14 package and 15 config tests passed |
| Catalog validation / Python syntax / whitespace | passed |
| Reproducibility/provenance | exact archive bytes and recorded hashes matched |
| Gitleaks on fresh exact ZIP extraction | zero findings; exit 0; no ignore rule |
| Relocated macOS launcher with fake hosts | scoped skill-creator copies retained, quality-gates install proposed, cancelled with exit 130 before any write |

The focused tests also verify that selecting an ambiguous installed target
cannot update it while an independent package remains installable; malformed
metadata still blocks writes; and a healthy host remains independent of a
failed host. A filesystem-backed fake installation verifies the newly selected
package's real copied bytes and leaves both existing records unchanged.

The relocated test executes `install-macos.command` → `install.py` → bundled
runtime, drives the actual keyboard menu, and observes the new preservation
message and install preview. It issues only fake version/inventory reads and
cancels before installation: zero real host calls, external installation
operations or model requests. See [sanitized evidence](candidate-r9-evidence.json).
The launcher PTY cannot be inspected by ioctl after it exits on this macOS;
selector-mode restoration remains covered by the real-PTY regression suite.

The first full run exposed an old Codex test transcript that requested an update
number no longer offered by the UI and supplied no input for the validation
retry. That test now explicitly tries the unavailable number, presses Enter
to retain the package, and verifies zero mutations. The final suite is green
with the stated PowerShell skip; the Codex update execution gate was not changed.

The initial relocated fixture bound its own source by array position, but the
fixture placed the official marketplace first. It therefore reached a source
preparation prompt instead of the expected install preview. Binding the fake
source by marketplace name corrected the harness; product/ZIP bytes were not
changed and no real operation was repeated.

Same-session Codex review found no remaining blockers; commitment/recency bias
is not fully controlled. No subagent or external reviewer was used.

**VERIFIED:** the reproduced Claude host-wide false failure is removed;
scoped entries remain intact; unrelated packages remain eligible; ambiguous
target updates stay blocked; messages identify what is retained and what to
do; fatal failures stop before impossible prompts; artifacts reproduce.

**NOT VERIFIED:** a fresh personal native inventory read or R9 native
installation, Windows/Linux keyboard and installation behavior, PowerShell
execution, real company endpoints, or model/hook/MCP workflows. Earlier native
capability evidence is not R9 native acceptance. Context7 was unavailable;
official Claude documentation supplied the scope contract.
