# CLI plugin runtime validation

Supported surfaces: Claude Code CLI and Codex CLI. On 2026-10-15 the seven
packages passed bounded native acceptance on macOS with Claude Code CLI 2.1.300
and Codex CLI 0.162.1 using a unique local marketplace and disposable fixtures.
session-preferences and work-journal changed after that run (d738ec4 changed
runtime migration path matching; a later change removed npm's hidden lockfile
from the work-journal server bundle). Their recorded bindings are stale, so
`check_plugin_release.py --require-acceptance` fails. The checker requires one
evidence record per surface that binds all seven packages, so passing it again
needs a new seven-package native acceptance run; the release version bump
changes every package manifest and would require that run anyway.
A 2026-10-17 follow-up verified GitHub marketplace installation and no-op
updates with Claude Code CLI 2.1.302; a positive version transition used a
temporary local Git remote. Codex CLI remote Git marketplace installation and
update remain untested. See `remote-marketplace-validation.md` and
`acceptance.json` for evidence and remaining limits. The user explicitly
removed Codex desktop support on 2026-10-13.

The desktop failure remains in runtime-contracts.json historical_excluded_surfaces:
its tool call reached the live activity source and its injected policy named the
CLI probe. The user reports removing the sole test activity; no query of live
activity records was performed. A rollout source of vscode is not proof of the
VS Code interface; the user confirmed the independent desktop app.

## CLI packaging contract

Claude uses .claude-plugin/plugin.json. Codex uses the approved compatibility
format .codex-plugin/plugin.json with .mcp.json, without a portable root manifest.
Codex 0.162.1 skips hooks for the portable Agent Plugins format; see the retained
runtime observations and https://github.com/openai/codex/issues/47925.

Old 0.0.2 CLI evidence covers the seven tools, actual fixture write/read, all four
SessionStart events, preference-off behavior and native reviewer routing with
Superpowers 7.0.0. The normal-user-config collision check now uses guarded 0.0.3
probes with independent server IDs agent_skills_probe_claude_cli and
agent_skills_probe_codex_cli. The extra probe_identity tool exists only in the
probe; the seven production handlers are used unchanged.

Before calling any data tool, call probe_identity and verify its surface, unique
probe_id and canonical fixture paths. Guarded probes refuse data access until
this identity call, reject config outside their own data folders and recheck
real paths before each call. Do not call the existing skills-query server during
the probe. Matching names alone cannot prove fixture binding.

## Rebuild and direct-client check

Build the existing server first. Use a fresh destination: the builder refuses
to overwrite an existing bundle. These commands run from the feature worktree.

```sh
npm --prefix skills-query-server run build
python3 scripts/probe_plugin_runtimes.py build --surface codex-cli \
  --manifest-format legacy --destination /tmp/agent-skills-codex-probe
node skills-query-server/scripts/smoke_client.mjs -- node \
  /tmp/agent-skills-codex-probe/server/launch.mjs
```

The smoke client automatically checks probe_identity when present. Direct-client
success does not replace native host checks. If using npm --prefix, remember that
npm runs the smoke command from skills-query-server; use an absolute launcher path.

The old CLI, desktop and completed guarded CLI test installations were removed
through codex plugin remove; the live skills-query config was preserved. The
later seven-package native acceptance is recorded separately in `acceptance.json`.
Its selected test packages and marketplace were also removed through each CLI;
the cleanup report records unresolved Codex and Claude registry fingerprint
changes. Probe hook trust is reviewed with normal /hooks, never bypassed.

Task 3 adds personal preference overrides and bundled runtime resources. New
probe builds use 0.0.4 because their hook behavior changed. The retained 0.0.2
and 0.0.3 native observations describe the earlier fixtures, not native acceptance
of 0.0.4. Current source/relocation tests do not replace the later two-CLI release
acceptance gate. guarded-probe-progress.json is the initial timeout snapshot;
guarded-cli-observations.json records the subsequent successful query.

## Evidence and gates

runtime-observations.json and codex-hook-observations.json retain earlier CLI
observations and raw-log hashes. New guarded host results must explicitly verify
fixture isolation before the gate is accepted. Raw logs stay in the ignored task
workspace, not in release bundles. Desktop is excluded by the user's scope change,
not labelled passing.

```sh
python3 -m unittest discover -s tests -p 'test_plugin_runtime_probe.py' -v
npm --prefix skills-query-server test
npm --prefix skills-query-server run smoke -- --contract \
  ../docs/validation/skill-plugins/runtime-contracts.json
```

The current production and development dependency audits have zero reported
vulnerabilities. This does not certify other platforms, minimum tool versions,
Codex CLI remote Git marketplace installation/update, a positive version
transition from GitHub, or a full third-party legal review. Commit, push and
publication each still require explicit user approval.
