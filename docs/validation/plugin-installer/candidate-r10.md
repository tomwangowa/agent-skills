# Installer candidate R10: package progress and journal explanation

Date: 2026-11-11. **Offline regression tests and the relocated macOS launcher
with fake hosts passed. Native R10 installation/update has not run.**

## User-visible changes

Each selected package now has a separate bar for checking the current state,
executing the native command, and checking the installed files/version. The
bar represents completed phases, not a guessed download percentage. Finished
results and errors belong to that package's block; the next package starts
after a blank line. Packages kept without a command get a separate kept row.
Unselected packages do not produce result noise.

Native JSON stdout is captured for verification rather than dumped onto the
screen. Native stderr is forwarded immediately, including prompts with no
trailing newline; stdin remains inherited. The bar pauses while a prompt is
open. The installer never supplies an answer. Native failures show the provided
JSON message when available, with no automatic retry. Timeout/cancellation
retains the existing uncertain-write handling. Codex's checked installation
path remains in its package result. Preview still discloses source, version,
write target and relevant side effects, but no longer dumps command arrays.

The optional `work-journal` setup now explains its consumers before asking for
paths: `activity-logger` saves work records under Activities;
`work-log-analyzer` searches those records and the selected Notes folders;
`report-generator` uses those skills to prepare reports. Existing valid
configuration is shown and reused without path prompts, writes or directory
creation. Unrelated extension fields are not displayed. Invalid configuration
is kept unchanged and reported. Missing configuration keeps the separate,
create-only preview/approval flow, including concurrent-creator protection.
No activity or note contents are read or moved.

## Verified cause of the two mod warnings

The user's native R9 transcript reported successful `up_to_date` updates for
handoff-mod 0.2.2 and attention-mod 0.6.1, followed by installer verification
warnings. Read-only file comparison found no changed or missing package files:
handoff-mod had two extra `.in_use/<pid>` markers and attention-mod had one.

Read-only inspection of the installed Claude Code 2.1.322 binary identified
the native root `.in_use` directory, PID filenames, a 4096-byte marker limit,
and the JSON schema `pid` plus optional string `procStart`/`procStartFt` fields.
Native cache bookkeeping is separate from plugin payload. No new native
inventory, update, model conversation or permission grant was executed.

R10 applies the exception only in installed-Claude verification for the exact
CLI string `2.1.322 (Claude Code)`. Entries must be immediate regular,
non-executable, non-symlink PID files with matching integer PID, permitted
fields and bounded marker length. Unexpected entries, extra payload files,
symlinks and changed source files still fail. Other CLI versions receive no
exception. Source/catalog hashes and capability records remain unchanged.
No running-session markers are removed. Both currently installed mod payloads
passed the read-only corrected hash check; this is not a new native update.
A successful native `up_to_date` result is described as already up to date only
after the normal installed-state verification passes.

## Artifact and evidence

- R10 ZIP (local artifact; not included in the repository)
- SHA-256 (local artifact; not included in the repository)
- Size: **64,766 bytes**; SHA-256:
  `c2ce2d07a959331b6648f8c8048177da79cae1f8d5b75f0c8c0049befa0d605c`.
- 30 ZIP entries, 29 payload-file hashes, 33 input hashes; repeated offline
  builds produced identical bytes and every provenance hash was checked.
- Catalog, providers and native capability records are byte-identical to R9.
- [Sanitized evidence](candidate-r10-evidence.json).

| Check | Result |
| --- | --- |
| Initial nine focused tests against R9 | four failures reproduced the marker, progress, JSON and existing-journal problems |
| Final installer suite | 128 tests: 127 passed, one PowerShell skip; exit 0 |
| Package/config tests | 14 package and 15 config tests passed |
| Catalog / Python syntax / tracked whitespace | passed |
| Real child process with no-newline stderr prompt | prompt observed before the parent sends its answer; raw JSON retained internally |
| Child timeout and per-package failure messages | passed; no retry |
| Exact ZIP extraction Gitleaks scan | zero findings, exit 0; default rules, no ignore file or allow comments |
| Relocated macOS launcher, real keyboard menu and fake CLIs | two fake installs, one fake up-to-date update, exit 0; separate bars and blank lines, prompt interaction, no raw JSON |
| Existing journal and mod data in relocated fixture | byte-identical; no new journal path prompts/directories |
| Prior archives and personal settings/registries | nine prior ZIPs and five personal files unchanged from the post-user-install baseline |

The first complete regression run exposed a removed Codex receipt-path line;
the line was restored in the package block, then the full suite passed. The
first relocated fixture omitted bash/jq/node from its isolated PATH, correctly
causing work-journal to be skipped and exit 1. Supplying the existing local
tool paths corrected that fixture; product/ZIP bytes were unchanged. The
successful replay made zero real host calls, external operations or model
requests. Nothing was retried against the user's native installation.

Same-session Codex self-review covered the runtime changes, new presentation
and process modules, tests, entry wiring and builder allowlist. No remaining
blocking finding was identified; commitment/recency bias is not fully
controlled. No subagent or external reviewer was used. HEAD, four stashes and
empty staged state are preserved. No commit, push, release, production mirror
sync or restoration of the earlier trial links/hooks was performed.

**VERIFIED:** package phase bars and separated errors, captured JSON with
interactive prompts, existing journal reuse/explanation, exact-schema cache
marker handling with payload changes still rejected, reproducible artifact,
and preservation of the checked personal files and prior artifacts.

**NOT VERIFIED:** native R10 installation/update; Windows/Linux native
execution and PowerShell; arbitrary CLI versions or terminal escape protocols;
model, hook trust, MCP and real skill workflows. Whole-tree verification is
not an atomic filesystem snapshot. Prior native capability evidence remains
specific to its original run. This release adds no company endpoint test or
account setup.
