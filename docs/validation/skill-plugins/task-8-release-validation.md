# Task 8 — migration, updates and release readiness

The seven packages passed the recorded native acceptance on 2026-10-15 with
Claude Code CLI 2.1.300 and Codex CLI 0.162.1 on macOS. Tests used a unique
local marketplace, isolated fixture settings and synthetic journal records.
The Git-hosted marketplace path and publication remain unverified or pending
approval; see `acceptance.json` for each check and its bounds.

## Review corrections

A fresh Codex reviewer reported zero Critical and five Important findings. The
independent context reduced author anchoring, but it was still the same model
family. Each finding was reproduced and corrected:

| Finding | Correction | Evidence |
| --- | --- | --- |
| Flat mirrors named `skills` ascended to a runtime outside the installed tree | Native manifests now identify nested plugin layouts; flat mirrors use their own sibling runtime | Relocated preference/control hooks, logger initialization/write and analyzer read; failure reproduced before correction |
| Recovery rejected a deleted target | Preflight permits a missing regular target, rejects symlinks/path changes/new edits, then restores original bytes and mode | Delete-after-apply regression failed before correction and passes after it |
| Setup/doctor CLI bypassed the common root resolver | Explicit CLI roots use the shared absolute/tilde validation | Subprocess rejects relative roots; patched-home preview verifies quoted tilde expansion |
| User configuration could be written inside disposable plugin caches | Python/Node guard real-path cache ancestors across setup, preference, activity and note writes | Native manifest and symlink-alias fixtures reject the paths without creating data |
| Root onboarding described legacy private config and `tsx` entry points | Both READMEs now describe external settings preview/setup and the compiled server | Catalog, build and link checks |

A further backup race was reproduced: bytes read for backup could differ from
the reviewed snapshot. Apply now checks the backup hash before writes and
revalidates the full snapshot after backup; the regression leaves the target
unchanged on failure. Two Minor documentation observations were also resolved.

## Verification

VERIFIED:

- Full Python suite: 154 tests. Node 24.21.0 isolated toolchain: 52 Vitest tests
  and 8 native stdio tests. Shared-config, reference-logging and sync dry-run
  shell suites passed.
- `validate_skills_catalog.py --check`, deterministic plugin rebuild, release
  artifact validation, Claude manifest validation for seven packages and
  marketplace, and `git diff --check` passed.
- Production and development dependency audits report zero vulnerabilities.
  Gray-matter's executable frontmatter engine was removed; data-only YAML/JSON
  parsing is covered by regression tests. The build host's global Node 23.7.0
  emits Vitest's unsupported-engine warning; the test suite used isolated Node
  24.21.0, and the global runtime was left unchanged.
- Native MCP host calls listed seven tools and wrote/read unique fixture
  markers. Startup, resume, clear, compact, preference-off, owned routing,
  manual invocation, conditional Superpowers, update and fixture migration
  passed on both CLIs. All fourteen final native 0.1.0 package bindings match
  the generated release artifacts.
- Both fixture migration runs applied one reviewed replacement and restored
  the exact original bytes while retaining unrelated fixture settings. The
  0.1.1 update cohort preserved the personal override and journal configuration
  while detecting the changed packaged default.
- The unique test marketplace and all fourteen selected installations were
  removed through native CLI commands; the final native inventories contain
  none of the test packages. All seven personal fixture file fingerprints are
  unchanged.
- Modified skills were re-audited. Sensitive-input review and a fallback secret
  scan were performed on a disposable copy of changed public source, excluding
  private records and `node_modules`. Eight matches reduce to four existing
  examples duplicated across platforms: three generic private-key headers
  without key bodies and one environment-variable API-key lookup. No embedded
  credential was found; the scanner's exit 2 remains recorded as NEEDS_REVIEW.

## Native setup and limitations

Claude used isolated plugin settings. Its work-journal server was launched from
the installed bundle entry via an explicit strict fixture MCP config, so the
test verifies the packaged command and host round-trip but does not establish
automatic plugin MCP discovery under strict isolation. Codex used its native
plugin MCP entry. Existing Codex plugins, MCP servers and user hooks were
disabled only by per-invocation overrides. Superpowers 7.0.0 was already
registered; only the selected planning boundary was exercised, so broader
`tested_versions` remain empty.

Claude's local marketplace update succeeded. Codex's local filesystem
marketplace rejected `marketplace upgrade` because that operation expects a Git
source; native `plugin add` refreshed the local fixture package and its resource
hash. A normal remote Git marketplace install/update flow was not exercised.
The source release version remains 0.1.0; 0.1.1 existed only in the disposable
native update cohort.

Cleanup left unresolved native-state differences. Hash-only snapshots matched
the initial configuration before cleanup. The first cleanup changed the
unselected semantic fingerprint of `~/.codex/config.toml`; the final test cycle
also changed the semantic fingerprints of Claude's `installed_plugins.json`
and `known_marketplaces.json` compared with the prior clean snapshot. Current
native listings and registry files contain no selected test package or
marketplace. The original values were not saved, so the changed fields cannot
be attributed safely. No manual restore, prune or trust-state rewrite was
performed; see `native-acceptance-cleanup.json`.

Native acceptance is limited to these macOS clients and isolated scenarios. It
does not cover remote marketplace distribution, other operating systems,
minimum supported tool versions, arbitrary-editor races, crash recovery at
every write boundary, whole-transaction atomicity, a real-user settings
migration or full third-party legal review. Commit, push, publication and
production sync remain separate approval steps.
