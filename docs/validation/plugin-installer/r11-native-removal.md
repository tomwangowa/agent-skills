# R11 isolated native removal acceptance

Date: 2026-11-12. **PASS for the exact R11 archive, macOS arm64 and Claude Code
2.1.322. Two isolated personal removals completed once each; project files and
the selected synthetic data remained intact. Real user installations were not
targets. Codex removal remains withheld.**

## Authorization and boundaries

The user selected the proposed isolated real-removal acceptance after the
successful personal preview/cancellation. That authorizes this one batch,
using temporary settings and test packages, with preservation of the user's
current installations. It does not authorize real personal-package removal,
account login, new installation/source downloads, model conversations,
credential cleanup, retries, commits, pushes or publication.

The exact archive was
`agent-skills-installer-fe55c04-candidate-r11.zip`, SHA-256
`c686ec875a61a81793782ec6621e424889ad14d1f643a4a3f52113f0e5a36414`.
The relocated macOS launcher ran the shipped `install.py` and bundled runtime,
using the real Claude Code `2.1.322 (Claude Code)` executable. The executable
hash was checked against the previously inspected binary before use.

Fixture setup copied the actual quality-gates/work-journal package bytes and
confirmed their R11 catalog hashes. It created native-shaped synthetic
registry/settings records and a local catalog descriptor, without running
native installation or fetching a marketplace. This proves removal from that
controlled native store; it is not a native install-to-uninstall round trip or
new source-provenance acceptance.

## Isolation

Fresh HOME, CLAUDE_CONFIG_DIR, XDG, temporary and journal directories were used.
No existing settings contents, records, notes, account credentials or API
environment values were copied into them. The OS profile denied outbound
network, reads of real credential/settings directories, keychain access and
writes outside the fixture/terminal. A separate preflight confirmed allowed
fixture writes, denied outside writes, denied socket connection and denied
opening the real settings file without reading its contents.

A guarded CLI path allowed only the required version/inventory queries and
one exact `plugin uninstall <id> --scope user --keep-data --json` command for
each fixture target. Exclusive markers prevented retry. The batch is closed
and consumed; this report's verification reads saved results and fixture
files only and does not issue more native commands.

The preliminary scanner returned exit 1 with eight findings. Six were
64-character source-file SHA-256 values, each corroborated against the named
source file. Two were private-key header examples in reference documentation,
with no encoded private-key payload. These findings were reviewed before any
native call; they are not reported as a zero-finding scan. The initial local
preflight command also had a Python syntax error before execution; it was
corrected before the successful isolation probe. Neither preflight issue
consumed a native uninstall attempt.

## Results

| Check | Result |
| --- | --- |
| Exact shipped entry | `install-macos.command` -> `install.py` -> bundled runtime |
| Native version/inventory queries | 16; successful |
| Native uninstall attempts / retries | two / zero |
| quality-gates 0.2.0 user removal | exit 0, native `outcome: ok`, `scope: user`, `keptData: true` |
| quality-gates project copy | remains enabled at 0.2.0; package hash and project settings unchanged |
| work-journal 0.2.0 user removal | exit 0, native `outcome: ok`, `scope: user`, `keptData: true` |
| Final native inventory | only the quality-gates project record remains |
| User fixture plugin settings | both personal plugin entries removed; unrelated fixture setting retained |
| Synthetic journal, note, record and plugin-data sentinels | nine files byte-identical; no journal setup |
| R11 launcher | exit 0, both results displayed `removed`; no failed/unverified result |
| Real personal settings/registries | five checked files byte-identical |
| Existing archives | eleven ZIPs byte-identical, including exact R11 |
| HEAD / four stashes / staged state | unchanged |
| Source setup / native installation / normal model sessions | zero |

The plugin-data sentinels cover candidate ID folder spellings; all were kept.
The real native `keptData: true` receipts and preserved files support the tested
retention contract, without claiming that every possible data-directory
binding or storage migration was exercised.

The saved evidence is under the ignored
`.superpowers/sdd/2026-11-12-r11-native-removal/prepared-twya0pkz/` directory.
The public [sanitized evidence](r11-native-removal-evidence.json) contains
native result fields and preservation outcomes without raw private paths,
credentials or real settings contents. No R11 archive was rebuilt or replaced.

**VERIFIED:** the exact R11 native personal-removal flow for these two
synthetically registered, real-byte packages; retention of the shared project
copy and tested data; once-only execution; checked real-file/artifact
preservation; and closure of this authorized batch.

**NOT VERIFIED:** a native installation-to-removal round trip, actual stored
credential/secret cleanup (keychain deliberately inaccessible), all
data-directory bindings/migrations, Windows/Linux or other CLI versions,
Codex removal, restarted model/hook/MCP workflows, real production-package
deletion, or atomic protection against concurrent filesystem changes.
