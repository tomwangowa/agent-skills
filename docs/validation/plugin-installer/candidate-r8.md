# Installer candidate R8: selectable, compact package menu

Date: 2026-11-11. **The package-selection repair is verified offline and in a
real macOS terminal with fake host commands. Native R8 installation has not run.**

R7 printed about 108 lines before package input. Its `[x]` and `[ ]` markers
were static text; entering a number worked, but arrow/Space interaction did
not exist. The user explicitly chose Up/Down, Space and Enter interaction and
requested only package and contained skill names on this screen.

## Artifact

- R8 ZIP (local artifact; not included in the repository)
- SHA-256 (local artifact; not included in the repository)
- Size: **58,544 bytes**; SHA-256:
  `bd3dfe2cf169114985a42f0c4ac9d0b691b1aa99e53789751c2ad1e7d2e8c488`
- 28 ZIP entries; 27 recorded payload-file hashes and 31 input hashes.
- Two independent offline builds produced identical bytes. The exact catalog
  and native capability records are byte-identical to R7. Package versions,
  skill surfaces and source/provider acceptance requirements are unchanged.
- R7 and earlier ZIPs, native profiles and evidence are retained. No existing
  archive or personal installation was replaced.

## User-visible changes

The normal interactive entry opens a scrolling checkbox menu. Up/Down moves
the focus, Space checks or unchecks any package, and Enter confirms. `q` and
Ctrl+C cancel. Superpowers is initially unchecked; other applicable packages
retain their checked defaults. Multiple hosts qualify package names by host.

Each package shows only its name and contained skill names. Versions, source
URLs, pinned commits, skill descriptions and repeated notices are removed from
selection. The list scrolls within the terminal height rather than dumping
the whole catalog. Source/dependency/install approvals remain separate. The
attention-mod model-token/excerpt notice appears at installation confirmation.

Going back retains the previous selection. Unchecking everything exits without
requesting an installation; any source writes already approved earlier in that
run are reported and retained rather than falsely described as no changes.
Redirected stdin cannot confirm the normal entry's package choices.

The screenshot also showed `Native inventory failed`. This is a separate
observed problem, not a disabled checkbox. R8 reports the adapter's available
inventory-error detail after selection, and still withholds writes for that
host. **Its cause in the user's personal environment is not established.** No
native inventory query was repeated or adapter safety check relaxed to guess
around it. Fake malformed inventory verifies that the error is visible and
cannot authorize an installation.

## Verification

| Check | Result |
| --- | --- |
| Original R7 reproduction | Numeric `10` accepted; no keyboard toggle; 108 preselection lines |
| Initial regression tests | Three failed: noisy output, immediate keyboard cancellation, arrow/Space selection |
| Final `test_installer_*.py` suite | 108 tests: 107 passed, 1 PowerShell skip; exit 0 |
| `test_plugin_packages.py` | 14 passed |
| `test_agent_skills_config.py` | 15 passed |
| `validate_skills_catalog.py --check` | exit 0 |
| Source parsing / diff whitespace | Python AST and `git diff --check` passed |
| Reproducible ZIP / provenance | exact bytes and file hashes matched |
| Gitleaks on a fresh exact R8 extraction | 0 findings; exit 0; no ignore rule |
| Relocated macOS launcher, 80 columns × 18 rows | all nine defaults unchecked, Superpowers checked, only official-source proposal, cancelled with exit 130 |

The relocated test executed `install-macos.command` → `install.py` → bundled
runtime using a PATH containing fake Claude and local Python/Git/dirname only.
It approved no source or installation. All fake host calls were version or
inventory reads: **zero real host invocations, external installation operations
or model requests**. This proves launcher/menu interaction, not native host
installation. Public evidence is in [the R8 summary](candidate-r8-evidence.json).

Keyboard tests exercise real PTY input, including selecting Superpowers,
unchecking every default, q/Ctrl+C cancellation and terminal-mode restoration.
Initial test-harness assumptions failed: PTY output must be drained while
waiting, and Darwin itself sets `PENDIN` on raw-to-canonical restoration. A
standalone openpty/setraw/tcsetattr experiment reproduces that sole kernel-bit
change. Tests compare every other terminal attribute at the real selector
boundary and process exit; no product workaround was added for that bit.
The launcher PTY was revoked after process exit, preventing a separate ioctl
observation there; the regression suite covers restoration directly.

Same-session Codex review found no remaining blockers. Commitment/recency bias
was not fully controlled. No subagent, external reviewer, native host retry,
account operation, model conversation, commit, push or publication occurred.
The four checked personal settings/registry files remain unchanged from the
start of this repair; existing temporary link/hook changes were not restored
or expanded by this task.

**VERIFIED:** compact names-only package selection, actual Up/Down/Space/Enter
interaction, selecting Superpowers and deselecting defaults, no-selection and
cancellation behavior, prior-write reporting, inventory-error refusal,
artifact reproducibility and relocated fake-host launcher interaction.

**NOT VERIFIED:** native installation with R8, the user's inventory-failure
cause, native Windows/Linux keyboard behavior, PowerShell execution, actual
company endpoints, or model/hook/MCP workflows. R7's native acceptance does
not establish R8 native acceptance. Very narrow terminals may require resizing.
The Windows implementation follows [Python's console key API](https://docs.python.org/3/library/msvcrt.html)
and [Microsoft's VT console API](https://learn.microsoft.com/en-us/windows/console/console-virtual-terminal-sequences);
documentation is not native Windows evidence. Context7 was unavailable.
