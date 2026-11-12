# Installer candidate R17: post-install source checks and work-journal defaults

Status: local development candidate, **not ready for native installation or
release**. The required Claude/Codex native artifact bindings are stale, and
the updated plugin versions exist only in this working tree. R17's catalog
expects `work-journal` 0.2.1 and `session-preferences` 0.1.5; the remote
marketplace must contain the matching artifacts before R17 can install them.
No push, merge, publication, native host operation or model request has run.

## Superpowers

The actual `superpowers@claude-plugins-official` registry entry was observed
at user scope, version 7.0.0, with enabled settings, the expected upstream
commit and the complete expected payload hash. The exact original installation
receipt was not retained; restarted host and skill behavior are unverified.

After the user's attempt, the official catalog marker was `e37d307bd9f85dab6fea5dfb5e3dc146753b2d2d`.
A single public fixed-commit GitHub archive download was independently compared
against the local catalog: 632 local files matched; 15 upstream-only files
were under `.github`; no local extra/changed files were observed. The verified
local tree hash using the runtime's Path-component sorting is
`d82a1a4cfbf569201da7a97f9acbf6fc8a495aa83755a8b3518d2c5e570bc2fe`.

The first calculation used string ordering instead of the runtime's path
ordering and gave a mismatched hash. This was corrected before R17 was built;
the synthetic regression fixture includes paths for which those orders differ.
Both independently compared snapshots are now accepted. Before native install,
the entire originally approved source state must still match. After a
successful install, a change between these two verified snapshots is accepted
only if all other sealed source fields, the target's manifest/version, enabled
user registration and complete installed payload hash match. A third, unknown
catalog version remains unverified; this is not a general solution for arbitrary
catalog updates. No atomic protection against a change during native execution
is claimed.

## Work journal

New optional setup proposes `~/.agent-skills/activities`, respecting an existing
`CLAUDE_ACTIVITIES_DIR` override. At package selection the default is noted.
The first setup explains that adding a notes folder enables searching notes
alongside work records; Enter skips it. The settings and created directories
are previewed and require separate approval. Existing valid or invalid settings
are preserved. Python and MCP now accept an explicitly empty notes list; missing
or malformed settings still fail. A later notes folder can be added to
`sources.notes.paths` in `work-journal.json`, followed by a query-server restart.

Both generated local work-journal packages completed a disposable MCP write/read
round trip with no notes. Isolated server tests passed 55 unit tests and eight
stdio smoke tests; Python settings tests passed 15 and package tests passed 14.
Two skill-auditor runs reported zero critical/important findings. The build
used an offline npm cache; npm reported Node 23 is outside Vitest's declared
engine range, though the tests executed successfully. A previous full installer
run failed because an old test supplied the former prompt sequence; that test
was updated and the suite rerun. See the final test report below.

Artifact integrity checks passed. `check_plugin_release.py --require-acceptance`
failed because native Claude and Codex bindings are absent or stale; no new
native acceptance or security attestation has been claimed. The package ZIP is
R17 (local artifact; not included in the repository),
SHA-256 (local artifact; not included in the repository):
`9e259452e712e99c406d90a88cdbc8c56090b1db580eaccedf81d2f77160c66a`.
The repeat build and archive provenance matched; extracted content Gitleaks scan
had zero findings. A relocated launcher replay with fake hosts passed existing
installation behavior and reuse of existing journal settings. These offline
checks do not prove native R17 installation, current-user cleanup, Windows/Linux,
or model/hook/MCP behavior in an actual coding-agent session.
