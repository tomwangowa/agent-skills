# Installer candidate R19: verified post-install state and optional notes

Status: local development candidate, **not ready for colleague installation or
release**. The catalog expects `work-journal` 0.2.1 and
`session-preferences` 0.1.5; those package versions exist only in this working
tree. The Claude and Codex native acceptance bindings are stale. No native host
installation, publication, model request or user-setting write was performed
for R19.

## Superpowers post-install verification

The user's installed `superpowers@claude-plugins-official` was observed at user
scope, enabled, manifest version 7.0.0, with the expected upstream commit and
complete payload hash. The original native install receipt was not retained,
so the exact command result from that attempt cannot be reconstructed.

The installer previously required the Claude official catalog state to be
unchanged across the install. The observed catalog marker moved from
`dceb15d50832e6adf380bedc26dde03d251324b9` before installation to
`e37d307bd9f85dab6fea5dfb5e3dc146753b2d2d` afterward. A pinned public-source
archive comparison found 632 matching local files, 15 upstream-only `.github`
files, and no changed or extra local files. Its runtime-compatible local tree
hash is
`d82a1a4cfbf569201da7a97f9acbf6fc8a495aa83755a8b3518d2c5e570bc2fe`.

R19 keeps the before-install check strict. After a successful install, it accepts
only the two independently checked catalog snapshots, and only when every other
sealed source field, the selected plugin's manifest/version, enabled user
registration and complete installed payload hash match. Unknown snapshots
remain unverified, and the check cannot prevent a source change during the
native command. This narrows the false warning seen in the user's install log;
it is not general approval of future catalog changes.

## Work-journal setup

Fresh setup defaults activity records to `~/.agent-skills/activities`, unless
`CLAUDE_ACTIVITIES_DIR` provides an override. Notes are optional and may remain
empty; the installer explains that adding a notes folder lets the journal
search personal notes alongside work records. This prompt appears after the
selected package installation when no valid journal settings exist. Valid
existing settings are reused without prompting or writing. Before creating new
settings or directories, the installer verifies the installed work-journal
version and checks it again after the user approves the preview. An older
work-journal runtime that cannot read an empty notes list is not given the new
format.

Both the Python runtime and the query MCP accept an empty notes list. A notes
folder can be added later to `sources.notes.paths` in `work-journal.json`, then
the query server must be restarted. The package version changes are
`work-journal` 0.2.0 → 0.2.1 and `session-preferences` 0.1.4 → 0.1.5 because
both ship the shared runtime.

## Verification

- Installer suite: 171 tests, 170 passed and one platform-specific skip.
- Settings and package suites: 29 tests passed.
- Full Python suite: 633 tests, 631 passed, one skipped and one build-test
  error. The error is
  `test_compile_uses_whitelist_and_does_not_emit_unlisted_source`: the working
  tree lacks the source development dependencies. They were not downloaded.
- R19 ZIP: `unzip -t` passed; a repeat build had the same SHA-256. Two relocated
  launcher checks passed with fake host CLIs: existing settings were reused
  unchanged, and fresh setup created the default Activities directory with an
  empty notes list. The fresh setup used two fake installs and one fake update;
  both checks made zero real host calls, external operations or model requests.
- Earlier in this work, the generated journal plugin bundles passed 55 unit
  tests and eight stdio smoke tests, including a write/read round trip with no
  notes configured.
- `check_plugin_release.py --require-acceptance` remains blocked because the
  Claude and Codex native artifact bindings are absent or stale.

The local QA ZIP had SHA-256
`8f3b1add3557ed8917651738f179304139b4e34ba5521959af2db1483811cbb6`.
Neither the ZIP nor its checksum sidecar is included in this repository. It
must not be treated as a published installer.
