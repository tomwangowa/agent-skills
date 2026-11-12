# Installer candidate R11: separate personal removal

Date: 2026-11-12. **The approved removal flow is implemented and verified
offline and through the relocated macOS launcher with fake hosts. The later
[isolated native removal batch](r11-native-removal.md) passed for exact R11 on
macOS arm64 / Claude Code 2.1.322. Native R11 installation has not run; Codex
removal remains withheld.**

## Behavior

The existing entry first asks Install/update or Remove packages; Enter keeps
Install/update. Removal has a separate host/package flow with every package
unchecked. Only installed packages offered by this script are considered,
including identified earlier manual installs, disabled plugins and versions
newer or older than the archive. The native qualified provider and registered
version determine the target. An unchecked package is never removed.

For the inspected Claude Code `2.1.322 (Claude Code)` command format, the
approved preview produces only a qualified native uninstall with
`--scope user --keep-data --json`. Project/local/managed records are protected,
and project payloads sharing the selected cache are hashed before and after.
Unknown source, duplicate personal records, an unsafe or linked cache,
unsupported CLI version or unreadable inventory keeps the affected items and
explains why. Superpowers must be identified as upstream, but its actual
installed provider may differ from the archive's preferred install provider.

One confirmation consumes exactly the sealed preview. Before each command,
the target registration and protected bytes are checked again. Afterward,
the native JSON must identify the requested uninstall, personal scope and
retained data; fresh inventory must show the personal target absent and the
multiset of every other record unchanged. Remaining project bytes must match.
Zero exit status alone is insufficient. Each result uses its own phase bar
and blank separator, with failure/interruption/uncertainty preserved rather
than retried, rolled back or labelled installed.

Removal mode does not prepare sources, refresh/remove marketplaces, install
dependencies, prune dependencies, configure journal paths or read records and
notes. Journal settings, work records, notes, plugin data directories and
shared tools are retained. The preview discloses that native Claude uninstall
can clear the removed plugin's own saved options/secrets; `--keep-data` does
not mean all native plugin settings are kept.

Codex 0.167.0's retained tagged producer source calls the cache-store uninstall
before `clear_user_plugin`: `cli/src/plugin_cmd.rs:681`,
`core-plugins/src/manager.rs:2428`, `core-plugins/src/store.rs:343`. Current
inventory cannot establish separate personal/project ownership. The approved
design therefore keeps Codex installations with a visible explanation; it
does not call a disable operation and pretend it removed the package. Opening
this path requires separate ownership/preservation evidence.

## Artifact

- R11 ZIP (local artifact; not included in the repository)
- SHA-256 (local artifact; not included in the repository)
- Size: **71,532 bytes**; SHA-256:
  `c686ec875a61a81793782ec6621e424889ad14d1f643a4a3f52113f0e5a36414`.
- 32 ZIP entries, 31 payload-file hashes and 35 input hashes.
- Repeat builds produced identical bytes; every provenance input and payload
  hash matched. Catalog, provider mapping and native capability records remain
  byte-identical to R10. Earlier archives/trial directories remain intact.
- [Approved design](../../superpowers/specs/2026-11-11-plugin-removal-design.md),
  [implementation plan](../../superpowers/plans/2026-11-11-plugin-removal.md),
  [sanitized evidence](candidate-r11-evidence.json).

## Verification

| Check | Result |
| --- | --- |
| Initial planner tests | 12 tests failed on missing removal planner, then passed after implementation |
| Initial UI tests | nine tests failed on missing removal UI, then passed; final focused suite has 22 tests |
| Complete installer suite | 150 tests: 149 passed, one PowerShell skip; exit 0 |
| Package/config tests | 14 package and 15 config tests passed |
| Catalog / Python syntax / tracked whitespace | passed |
| Relocated macOS removal entry, real keyboard menu and fake CLIs | empty exit 0 / zero uninstalls; cancel exit 130 / zero uninstalls; confirmed exit 0 / two fake uninstalls |
| Fake removal preservation | newer manual user targets removed; project record/shared package bytes, journal settings, notes, work records and plugin data remained unchanged |
| Relocated installation entry | two fake installs and one fake up-to-date update; progress, JSON capture, live native prompt and existing journal reuse passed |
| Exact fresh archive extraction Gitleaks | zero findings, exit 0; default rules, no ignore file or allow comments |
| Personal/artifact preservation | five personal files, ten old ZIPs, HEAD, all four stashes and staged state unchanged |

The first complete run failed four old keyboard tests because they waited for
Hosts without answering the new Operation prompt. The harness now explicitly
accepts the install default; all four terminal restoration/cancellation/choice
checks passed, followed by the green complete suite. The new Codex UI test
also confirms that its ownership limit is explained without offering or
executing uninstall. No product behavior was weakened to accommodate tests.

The offline process-boundary doubles use disposable on-disk payload/registry/settings
files and native-shaped data. The shipped archive itself is exercised through
`install-macos.command` -> `install.py` -> bundled runtime in a real PTY, with
no real Claude/Codex invocation in those offline replays. Only fake targets are deleted; permission
prompts remain visible before the harness supplies its answer. No external
installation, model conversation, credential copy, hook trust, commit, push,
publication, production sync or restoration of the old trial state occurred.

Same-session Codex review found no remaining blocking code findings.
Commitment/recency bias is not fully controlled; no subagent or external
reviewer was used. This change is treated as L2 because it adds explicit
uninstall behavior, despite the offline-only verification boundary.

**VERIFIED:** the approved separate removal flow, unchecked selection and
qualified user targets, preservation/failure contracts against real fixture
files, Codex refusal, installer regressions, reproduced archive/provenance,
secret scan and checked personal/artifact preservation.

**NOT VERIFIED by this initial offline batch:** native R11 uninstall/install/update, native Windows/Linux
execution and PowerShell, native saved-option/secret cleanup and data
retention, restarted host/model/hook/MCP behavior, or an atomic transaction
against concurrent file changes. Current CLI protocol inspection and earlier
installation acceptance do not establish native removal acceptance. Bundled
skill names may differ from the installed older/newer package; actual native
identity/version, not that skill list, governs removal.

The subsequent native removal proof and its narrower setup/retention limits
are recorded separately in [R11 native removal acceptance](r11-native-removal.md).
