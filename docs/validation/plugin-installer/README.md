# Plugin installer validation

## Current published archive: macOS trial (2026-11-13)

[Download the trial ZIP](https://github.com/tomwangowa/agent-skills/releases/download/installer-macos-trial-2026-11-13/agent-skills-installer-macos-trial-2026-11-13.zip); see the [GitHub release notes](https://github.com/tomwangowa/agent-skills/releases/tag/installer-macos-trial-2026-11-13).
This pre-release was built from merged main commit
`23282d8d8d04f1627deea7fb8cc677e8b6b1bca7`, contains only the macOS launcher,
and includes `session-preferences` 0.1.6. Its SHA-256 is
`9f1904929e1058fc9c14a2fdbee16c1dedb0f27503fe10cde343d94ef1a3ea99`.
It was published for manual testing; the exact ZIP has not been installed
through a real host. The R7 native results below apply only to the R7 bytes,
not to this release asset.

## Preserved R19 local-candidate evidence

[R19](candidate-r19.md) is a local QA candidate, not the current published ZIP.
It verifies a later Superpowers post-install check and optional work-journal
notes setup with fake hosts. Its package versions and native acceptance bindings
were stale at the time; its ZIP SHA-256 was
`8f3b1add3557ed8917651738f179304139b4e34ba5521959af2db1483811cbb6`.
Keep its results tied to that candidate only. R19 predates the Codex removal
capability update and does not represent the current installer source.

## Preserved R17 evidence

[R17](candidate-r17.md) records the initial work-journal default and the same
two-snapshot Superpowers check. R19 adds a second runtime check after settings
approval and verifies the relocated first-use notes flow.

## Preserved R14 evidence

[R14](candidate-r14.md) labels Superpowers as strongly recommended in the
package selection menu while keeping it unchecked by default. It carries
forward R13's archive source behavior; native R14 installation is unverified.

## Preserved R13 evidence

[R13](candidate-r13.md) supports one independently compared Claude official
catalog archive snapshot. Its relocated planner proposes Superpowers for the
observed local tree; native R13 installation and restarted behavior remain
unverified. Unknown archive revisions remain withheld.

## Preserved R12 evidence

[R12](candidate-r12.md) fixes both R11 review findings. Removal binds approval
to the resolved configuration directory and its device/inode, rejecting an
ancestor-link redirect or directory replacement. Complete unrelated local or
unknown-origin plugin records remain untrusted and preserved without blocking
identified targets; malformed metadata still stops writes. The full installer
suite passed 158 tests with one PowerShell skip. Four relocated removal cases
and installation replay passed with fake CLIs, including zero uninstall calls
after a profile switch. Eleven old archives and five personal files are
unchanged. See [evidence](candidate-r12-evidence.json) and
[bounded self-review](candidate-r12-review.md). No real R12 host/model operation
ran; R11 native evidence below remains R11-specific.

## Preserved R11 evidence

[R11](candidate-r11.md) adds an explicit personal-removal mode for identified
Claude Code 2.1.322 installations. Its package list starts unchecked; preview,
state recheck, native user-scope uninstall with retained data and fresh
inventory/project payload verification are separate steps. Journal data,
project copies and tools stay; Codex removal remains withheld for unresolved
personal/project ownership. Final suite: 150 tests, 149 passed and one
PowerShell skip. The relocated launcher passed empty/cancel/confirmed removal
and installation replay with fake hosts. Five personal files and ten prior
ZIPs remain unchanged. See [offline evidence](candidate-r11-evidence.json).

The later [isolated native removal acceptance](r11-native-removal.md) passed
using real Claude Code 2.1.322 on macOS arm64: two personal test removals, zero
retries, a retained project copy and retained synthetic data. Five real
personal files and eleven ZIPs were unchanged. The native store was seeded
with real package bytes and synthetic records; no native install-to-uninstall
round trip or model request ran. See [native evidence](r11-native-removal-evidence.json).

## Preserved R10 evidence

[R10](candidate-r10.md) adds separate per-package phase bars and blank-line
result blocks, captures native JSON while forwarding interactive prompts,
explains work-journal consumers and automatically reuses valid configuration.
It corrects false payload mismatches caused by inspected Claude 2.1.322
`.in_use/<pid>` metadata; unknown marker entries and payload changes still fail.
Final suite: 128 tests, 127 passed and one PowerShell skip. The relocated macOS
launcher passed real keyboard/progress/prompt interaction with fake hosts;
no native R10 installation or model request ran. Five checked personal files
and nine prior ZIPs are unchanged. See [sanitized evidence](candidate-r10-evidence.json).

## Preserved R9 evidence

[R9](candidate-r9.md) fixes the reproduced host-wide failure caused by a Claude
plugin with both user and project installations. All existing rows are retained;
unrelated packages can continue and ambiguous targets still cannot be updated.
Messages name the plugin and explain preservation/account/project locations.
Real unreadable inventories stop the affected app before impossible update or
install prompts. Final suite: 113 tests, 112 passed and one PowerShell skip.
Relocated fake-host launcher verification passed. That validation did not run
native R9 installation; the user's subsequent native observations and their
R10 repairs are described above. Previous native evidence remains specific to
its original run.

## Preserved R8 evidence

[R8](candidate-r8.md) replaces the static package markers with an actual
Up/Down + Space checkbox menu, with Enter confirmation and a scrolling list of
package/skill names only. The installer suite has 108 tests: 107 passed and one
PowerShell skip. A relocated macOS launcher with fake host commands verified
unchecking all nine defaults and selecting Superpowers, then cancelling before
source writes. Native R8 installation, Windows/Linux keyboard behavior and the
user's separate native-inventory failure remain unverified. The existing
catalog and capability records are unchanged; R7's native results below remain
R7-specific. Earlier candidates and native profiles are retained.

## Preserved R7 evidence

The [exact R7 native batch](r7-native-acceptance-results.md) passed six invocations
on macOS arm64: first install and rerun for Claude 2.1.322 logged out, Claude
2.1.322 logged in, and Codex 0.167.0 without an account. All reruns attempted zero
mutations and preserved native payload/registry/settings. R7 bytes are unchanged.
Windows/Linux, Codex account-backed catalogs, native edge-case preservation and
runtime workflow coexistence remain unverified.

The [full-package installation coexistence batch](r7-coexistence-results.md)
verified ten Claude and eight Codex packages together in fresh profiles. All
18 first installs succeeded; both reruns attempted zero mutations and retained
8,199 installed files/modes and checked settings. Claude rerun exited 0; Codex
rerun returned the expected exit 1 for seven preserved own packages whose
update ownership is not verified. This status gap remains unresolved. The
[proposal](r7-coexistence-proposal.md) records the consumed one-batch approval;
additional native operations require new approval. Runtime workflows were not
executed.

The [R7 candidate](candidate-r7.md) integrates the verified payload hashes and
two exact native capability records: macOS arm64 Claude 2.1.322 (logged in and
logged out) and Codex 0.167.0 through `openai-api-curated` (no account login).
The 56,060-byte ZIP includes two minimized evidence summaries. Final installer
suite: 101 tests, 100 passed and one PowerShell skip; exact archive provenance,
reproducibility, relocated offline planning and extracted-content secret scan
passed. R6's four scan findings were verified file-hash false positives; R7
omits unnecessary raw-log fingerprints/workspace pointers, with no ignore rule.
Earlier ZIPs and full native evidence are retained. Subsequent exact-R7 native
results are linked above; Windows/Linux remain unverified. See the report for
exact hashes and scope.

The [R7 existing-install replay](r7-existing-install-preservation.md) passed
29 synthetic scenarios / 58 installer runs, with zero mutation commands and
unchanged fixture files. This is offline evidence. The [native first-install
and rerun batch](r7-native-acceptance-results.md) passed all three native reruns.

## Native evidence and historical candidates

The [Claude account-state matrix](claude-login-matrix-results.md) passed both
native cases on 2026-11-11: Claude Code 2.1.322 on macOS arm64 installed and
enabled Superpowers 7.0.0 while logged in and while logged out. Native auth was
checked before and after each installation, and all 238 installed files/modes
in each case match independent pinned Git objects. Two source-adds, two installs
and one isolated native login ran under the approved scope, without model
requests. No installer acceptance/hash or R5 update was included. The older
Claude 2.1.321 case had no auth-state observation and is not the basis for this
matrix result.

The [no-account Codex native case](codex-no-account-native-results.md) passed on
2026-11-11: Codex 0.167.0 on macOS arm64 installed and enabled Superpowers 6.3.0
from `openai-api-curated`, without login or a model conversation. One native
startup and one plugin add ran; all native exits were zero. All 73 installed
files and executable modes match the official catalog's Git tree. Synthetic
company model settings and original personal settings were retained. This is
native capability evidence; installer acceptance, Windows/Linux and actual
company endpoint connectivity remain unverified. No acceptance/hash or R5 update
was included.

The [Codex catalog-variant change](codex-catalog-variants-offline.md) now follows
the single official catalog exposed by native Codex, including
`openai-api-curated`, and preserves company model-provider configuration.
Offline installation/receipt transcripts cover a no-account scenario: installer
suite 96 tests, 95 passed and 1 PowerShell test skipped. The subsequent
[no-account native installation](codex-no-account-native-results.md) passed.
No Superpowers acceptance record or new ZIP was created; R5 is unchanged.

The [Codex official catalog probe](superpowers-codex-catalog-result.md) completed
one approved native startup on 2026-11-11, without a model conversation or
installation. Fresh unauthenticated Codex 0.167.0 exposes `openai-api-curated`,
which R5 does not support (the working-tree adapter above now recognizes it).
Both physical official manifests
contain Superpowers 6.3.0. The approved list queries omitted `--available`, so
their empty arrays do not establish availability; no query was repeated.
This is catalog-only evidence and adds no provider acceptance record.

The [R5 remaining-package batch](macos-r5-remaining-results.md) passed all 14
installations on 2026-11-11: eight Claude packages and six Codex packages. Every
native mutation and both installer/final-inventory exits were zero. Versions,
enabled state and complete installed files matched R5. With the earlier two
quality-gates cases below, every one of R5's 16 own host/package pairs has
installation evidence across separate cases. Superpowers, other platforms,
all-packages-in-one-config coexistence and runtime behavior remain unverified.

The [R5 macOS native cases](macos-r5-native-results.md) passed on 2026-11-11:
Claude Code 2.1.322 and Codex 0.167.0 each installed and enabled
`quality-gates@tomwangowa` 0.2.0 in fresh, separate test settings. Both installer
exits were zero; independent checks matched all 27 Claude and 25 Codex package
files to R5. Two source additions and two installs ran, without retries or
model calls. Those earlier cases verified only quality-gates; the remaining
own-package installations are now covered by the later batch above.

The [own-source regression repair](own-source-regression-fix.md) is now verified
in the working tree only: missing own-package sources can be planned on both
hosts, and declining source preparation remains separate from installation
consent. The offline installer suite ran 87 tests: 86 passed and one PowerShell
test was skipped. The subsequent [R5 candidate](candidate-r5.md) packages that
repair, with exact-archive offline checks and reproducible bytes; its packaging
step performed no native operation. The preserved R4 archive still contains the original
defect. The archive-source design remains proposed and unimplemented.

The [offline archive investigation](superpowers-archive-source-investigation.md)
has delivered a proposed source contract and failure matrix, not a product fix.
It also reproduced an **unfixed R4 regression**: own-package planning with a
missing marketplace reads a Superpowers-only `readiness=None` and raises
`AttributeError` on both hosts. The old passing suite did not cover this case;
R4 must not be treated as a colleague-ready accepted installer. Review the
[proposed correction](../../superpowers/specs/2026-11-10-claude-archive-source-design.md)
before implementation. No new native operation was performed in that study.


The corrected Claude official-source capability case performed one source-add
and one installation, both exit 0, on Claude `2.1.321 (Claude Code)`, macOS arm64.
Superpowers `7.0.0` is enabled at user scope; the native registry pin matches the
approved upstream SHA, and all 238 installed files were fingerprinted. However,
the official catalog lost `.git` metadata and gained `.gcs-sha` after native
operations, so the current Git-only provenance check correctly withheld
acceptance. See the [partial native result](superpowers-native-claude-run-2.md).
No acceptance record was added; this is not candidate or functional acceptance.
The [first local preflight](superpowers-native-preflight-1.md) stopped before
any download on the old version label. Neither run authorizes another external
operation.

The official-source follow-up is implemented offline with schema 2 targets,
provider-local uncertainty, exact native acceptance gates and host-specific
receipts. The new R4 offline evidence is recorded in
[official-source verification](superpowers-official-sources-offline.md).
Superpowers automatic writes remain disabled: expected payload hashes are
unknown and the production native acceptance index is empty. Previous R2/R3
native results below do not transfer to the changed candidate or Superpowers.
See the [native capability proposal](superpowers-native-acceptance-proposal.md)
and [seven-workflow proposal](superpowers-function-acceptance-proposal.md).
The offline R4 implementation itself performed no native/model operation. The
later scoped capability attempt above did perform approved native downloads
and writes; no model, current-branch commit or publishing occurred.

The [R3 Codex native continuation passed one installation case](macos-codex-r3-continuation.md):
quality-gates `0.2.0`, exact payload hash, enabled state and exit codes were
verified. It reused the source from the [observer-stopped first attempt](macos-codex-r3-run-1.md);
an uninterrupted fresh run remains unverified. No source mutation was repeated.
Further native operations require new approval.
The Claude native result below remains an R2-only observation.

**R2 passed one native installation case:** macOS 26.6.2 arm64 / Claude Code
2.1.319 installed quality-gates 0.2.0 at user scope in a fresh isolated
environment. Source-add, install and installer exits were 0; the actual installed
payload hash matched exactly. The original three checked settings/installation
registry files were unchanged. See [R2 evidence](macos-claude-run-2.md).

The first run stopped on an unsupported Git URL field mapping; that failure
and offline correction remain in [run-1 evidence](macos-claude-run-1.md).
The offline baseline is 42 cases, 41 passed and 1 Windows process test skipped;
the six host tests also passed after adopting the genuine R2 observed fixture.
Beyond the R2 Claude and R3 Codex cases above, other packages/platforms and
hooks/MCP/skills remain unverified. Completed native runs do not authorize
another external operation.

## Scope and baseline

Implementation is authorized in `feat/cross-platform-plugin-installer`. Native
downloads/installations, commits and publishing require separate approval.
The baseline HEAD is `fe55c04bf9202fe82f1a68b7f5985305c82249f0`.

On 2026-11-09, macOS arm64:

- `python3 -m unittest discover -s tests -p 'test_plugin_packages.py'`: 14 passed.
- `python3 scripts/validate_skills_catalog.py --check`: exit 0.
- Existing state: two untracked design/plan files and four untouched stashes.
- `build_plugins.py --check` and the full `test_build_plugins.py` are **not
  offline checks**: `prepare_server` executes `npm ci`.
- Context7 is unavailable in this session; official documentation and local
  native command help are used instead.

## Native inventory evidence

Local help was inspected without installing or refreshing a marketplace:
Claude Code 2.1.319 and Codex CLI 0.167.0. Read-only inventory commands were
`claude plugin list --json`, `claude plugin marketplace list --json`, and
`codex plugin list --marketplace tomwangowa --json`. No model session ran.

Claude's documented inventory is an array with `id`, `version`, `scope`,
`enabled`, `installPath`; marketplace inventory has `name`, `source`,
`installLocation`, plus `repo` for GitHub shorthand or `url` for Git/URL
sources. Source identity must come from the matching marketplace,
not be inferred from the plugin name or cache directory.

Codex returned an object with `installed` and `available` arrays. Installed
entries contain `pluginId`, `name`, `marketplaceName`, `version`, `installed`,
`enabled`, `source`, `marketplaceSource`, `installPolicy`, `authPolicy`.
`source.path` is a marketplace source directory, **not evidence of the installed
plugin root**. No scope field was returned. Inventory alone cannot verify the
installed root or update ownership. R3's new-install receipt path supplies
separate target/content evidence; it does not enable existing updates. The
observed fixtures are anonymized; synthetic fixtures are explicitly distinguished.

Unqualified Codex listing may access the remote global catalog. The installer
must not issue it as an allegedly offline probe. Only named configured sources
may be queried, and external source refresh requires its own confirmation.

## Provider evidence and limits

The user confirmed **official CLI catalogs first, with host-specific versions
and separate required-function verification** on 2026-11-10. See the
[confirmed policy and official-source constraints](superpowers-official-source-strategy.md).
Codex `0.167.0` reserves its official catalog name; it cannot be prepared by
simply substituting its Git URL into the ordinary marketplace-add path.
Provider/runtime changes are implemented offline; new Superpowers native, candidate and functional acceptance are still pending.
The [supplementary design](../../superpowers/specs/2026-11-10-superpowers-official-sources-design.md)
and [implementation plan](../../superpowers/plans/2026-11-10-superpowers-official-sources.md)
were jointly approved by user #1 for offline implementation; external operations remain outside that approval.

The [2026-11-09 Codex/Superpowers capability audit](codex-superpowers-capability-audit.md)
updates the following preliminary limits: Codex add returns `installedPath`,
but inventory-based update ownership remains unresolved; Superpowers has
different recommended host marketplaces and those official payloads currently
lag the candidate's expected `7.0.2`. That audit itself ran no native plugin
operation; the later R3 native case is linked above.

The exposed Superpowers provider has native manifests identifying
`superpowers` version `7.0.2`. Its source repository is `obra/superpowers`;
its bundled development marketplace is named `superpowers-dev`. This is
identity evidence, not proof of end-to-end compatibility. The Codex marketplace
uses a relative URL source; automatic installation of that unvalidated source
must remain unavailable until isolated native acceptance establishes it.

Official references inspected:

- [OpenAI plugin packaging](https://developers.openai.com/plugins/build/plugins)
- [Claude plugin command reference](https://code.claude.com/docs/en/plugins/cli-reference)
- [Codex native implementation](https://github.com/openai/codex/blob/main/codex-rs/cli/src/plugin_cmd.rs)
- [Superpowers marketplace](https://github.com/obra/superpowers/blob/main/.claude-plugin/marketplace.json)

## Native plugin installation/functionality: NOT VERIFIED

Except for the R2 macOS/Claude case and R3 macOS/Codex continuation above, other
macOS packages/updates, Windows/PowerShell processes, Ubuntu/Debian installation,
CPU architecture combinations, dependency installation, remote source pinning,
hooks, MCP and skill behavior remain unverified for this installer. A syntax
check or synthetic process transcript proves only its own layer.

Before a native run, propose the exact commands, fresh temporary HOME/config
roots, CLI versions, source refs, network access and expected writes. Do not
copy private credentials, auto-authorize hooks or run model sessions. Every
repeat of an external action requires renewed approval. Preserve evidence of
partial writes and uncertainty; do not automatically roll back installations.

## Offline implementation evidence

The generated candidate includes three platform launchers, standard-library
models/catalog/planning/execution, optional journal setup, an interactive UI,
and an offline ZIP builder. Both root READMEs now have seven workflow scenarios
and a package-to-scenario table. No plugin payload was changed.

Final checks on macOS arm64 / Python 3.12.1:

| Check | Result |
| --- | --- |
| `PYTHONPATH=runtime python3 -m unittest discover -s tests -p 'test_installer_*.py'` | 41 cases: 40 passed, 1 skipped; exit 0 |
| `python3 -m unittest discover -s tests -p 'test_agent_skills_config.py'` | 15 passed |
| `python3 -m unittest discover -s tests -p 'test_plugin_packages.py'` | 14 passed |
| `python3 scripts/validate_skills_catalog.py --check` | exit 0 |
| `git diff --check` | exit 0 |
| Python AST / JSON parsing | passed for the changed scope |
| POSIX launcher syntax/process tests | passed on macOS; this is not native Linux acceptance |
| ZIP hashes, allowlist, reproducibility and relocated subprocesses | passed |

The skipped test is the PowerShell/download-alias process check because this
environment has no `pwsh`; it is not counted as a passing platform test.

| Design requirement | Evidence and boundary |
| --- | --- |
| Host-specific skills, manual policies and defaults | catalog tests; seven packages plus Claude's two mods; Superpowers unchecked |
| Unknown/disabled/non-user installs retained | host/planning refusal tests; missing Codex scope/root is not guessed |
| One decision for preview/execution | actual action/prior-result fingerprint; stale approval/source-change tests |
| Dependency consent and independent failures | mapped existing managers only; exact argv, timeout/failure/cancel tests; real manager installs unverified |
| Optional setup preserves personal data | temp-file race, malformed config, path precedence/cache alias and preview tests; no note contents read |
| Relocatable launchers/archive | real POSIX/fake-CLI subprocesses, spaces/CJK paths, isolated imports and archive hashes |
| Source versions/content | local payload hash compared before/after; live remote ref race explicitly remains |
| README scenarios | both languages cover all packages and verified entry names; attention model cost and mod writes disclosed |
| Real install/functionality | not run; requires separate approved native acceptance |

The dependency map's IDs were checked against
[Homebrew Python](https://formulae.brew.sh/formula/python@3.13),
[Node](https://formulae.brew.sh/formula/node@24),
[Git](https://formulae.brew.sh/formula/git),
[Ubuntu Python](https://packages.ubuntu.com/noble/python3),
[Bash](https://packages.ubuntu.com/noble/bash),
[rsync](https://packages.ubuntu.com/noble/rsync),
[Git](https://packages.ubuntu.com/noble/git),
[jq's install guidance](https://jqlang.org/download/) and
[Microsoft's Azure tooling guidance](https://github.com/Azure/azure-functions-skills/blob/main/templates/skills/azure-functions-setup/SKILL.md).
These are package-ID references, not native install evidence or a guarantee
that a particular OS repository contains a suitable runtime. No manager is
installed or elevated automatically.

See the [same-session review](review.md) for fixed findings, assumptions,
rulings and remaining gaps, and the [native run proposal](native-acceptance-proposal.md)
for the exact external-operation approval scope. The overall feature remains
incomplete until its required native capabilities and acceptance are resolved.

## Original offline artifact and source scan (before run 1)

- Candidate: `dist/agent-skills-installer-fe55c04-candidate.zip` (40,963 bytes).
- SHA-256: `32f469efcffb684ca2d62aad9a01690e69fcd9efd0fdf768cf43b070cf2baa17`.
- ZIP: 22 files, 18 host/package entries. Payload hashes and all recorded input
  hashes matched the current worktree after rebuilding the intermediate archive.
- Gitleaks `dir` scanned the 36-file review scope and unpacked candidate
  (approximately 361 KB): no leaks found, exit 0. The ignored review directory
  contains only task inputs/artifacts, not private configuration or Git history.
- No stage, commit, push, plugin payload edit or native installation was made;
  the four original stashes remain. This archive is local and unpublished.

## Corrected candidate R2

- Latest candidate: `dist/agent-skills-installer-fe55c04-candidate-r2.zip`
  (41,012 bytes).
- SHA-256: `77d2189c9fc374920333ad81b825e7f516be49159c1e99067770896dcc237800`.
- Only the Git/URL marketplace field mapping changed in product code; the
  source payloads and their versions remain unchanged.
- Native source-add was attempted once; no plugin-install command or external
  retry was executed. The original artifact/evidence remain available.
