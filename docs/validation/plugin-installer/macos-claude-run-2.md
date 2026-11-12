# macOS Claude acceptance — R2 installation passed

## Verified result

The approved R2 run passed the **single-package installation layer** on a fresh
isolated macOS environment. Source addition and quality-gates installation each
ran once and returned 0; the installer also exited 0. No external action was
retried.

| Evidence | Observed value |
| --- | --- |
| Date/time | 2026-11-09 23:29–23:31 +08:00 |
| OS / architecture | macOS 26.6.2 / arm64 |
| Claude Code / Python | 2.1.319 / 3.12.1 |
| Archive | `dist/agent-skills-installer-fe55c04-candidate-r2.zip`, 41,012 bytes |
| Archive SHA-256 | `77d2189c9fc374920333ad81b825e7f516be49159c1e99067770896dcc237800` |
| Downloaded repository commit | `fe55c04bf9202fe82f1a68b7f5985305c82249f0` |
| Installed identity | `quality-gates@tomwangowa` |
| Installed version / scope / enabled | `0.2.0` / `user` / `true` |
| Installed root, relative to isolation | `claude/plugins/cache/tomwangowa/quality-gates/0.2.0` |
| Expected / installed payload SHA-256 | both `a7c6e396a54fa316a837bd3cc7479254cadb4b09672475649820720eca81add3` |
| Source-add / plugin-install / installer exits | `0` / `0` / `0` |
| Mutating command counts | source-add 1; plugin-install 1 |

The initial plugin inventory was empty. The final native inventory contained
exactly the one selected plugin. The actual installed root was inside the
isolated environment, and independently hashing its files matched the catalog;
the conclusion does not rely on the command's success message alone.

## Isolation and evidence

Fresh HOME, CLAUDE_CONFIG_DIR, XDG_CONFIG_HOME and TMPDIR were created under the
ignored plan workspace. A fresh cwd outside all worktrees avoided ancestor
project settings. No private configuration or account file was copied. The
unmodified extracted entry ran with the absolute real Python interpreter,
`-I` and a clean environment; the observer enforced the two approved mutating
command vectors and single attempts.

The original live `settings.json`, `plugins/installed_plugins.json` and
`plugins/known_marketplaces.json` hashes were unchanged after the run. This
checks those three files, not every possible native host side effect or network
request.

Machine evidence remains in this plan workspace's
`native-claude-r2-_codz_94/`: `run.json`, `commands.jsonl`, `result.json`, the
unpacked R2 archive, downloaded source and installed plugin. The external cwd
is recorded in `run.json`. No cleanup, update or uninstall was performed.

## Observed schema regression evidence

The native marketplace row has exactly `installLocation`, `name`, `source` and
`url`; `source` is `git`. Unlike run 1, the observer captured URL and field-shape
metadata. `tests/fixtures/installer/observed-claude-git.json` retains that actual
output with only installLocation anonymized. The existing Git-source regression
now consumes the observed fixture; all six host tests passed after the switch.
The earlier synthetic fixture remains clearly labeled as the reconstruction
used to fix run 1.

## NOT VERIFIED

- Hooks, MCP and skill execution: no model session was started and no separate
  hook-trust operation was performed.
- Other packages, updates, preservation/migration of an existing native
  installation, dependency installation or journal configuration.
- Codex, Superpowers, mods, Windows, Ubuntu/Debian or another architecture.
- Elimination of a live remote-ref race: the downloaded commit and actual
  installed content were checked, but these are not proof of atomic pinning.

This is one passing installation case, not full cross-platform acceptance or
release approval. No commit, push, production sync or publication occurred.
