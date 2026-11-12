# macOS Claude acceptance — run 1 stopped before plugin installation

This is the retained first-run failure record. The separately approved
[R2 run later passed the single-package installation layer](macos-claude-run-2.md);
the statements below describe run 1 and its then-current retry boundary.

## Result

**Not passed.** One approved source-add command completed, but the installer
could not normalize the resulting marketplace inventory. The operator cancelled
at the next installation prompt. No plugin installation command was attempted;
the isolated installed-plugin registry was not created. The external action was
not retried.

| Evidence | Observed value |
| --- | --- |
| Date | 2026-11-09, approximately 22:41–22:42 +08:00 |
| OS / architecture | macOS 26.6.2 / arm64 |
| Claude Code | 2.1.319 |
| Python | 3.12.1 |
| Archive SHA-256 | `32f469efcffb684ca2d62aad9a01690e69fcd9efd0fdf768cf43b070cf2baa17` |
| Source-add return code | 0; native JSON `outcome: ok` |
| Downloaded repository commit | `fe55c04bf9202fe82f1a68b7f5985305c82249f0` |
| Expected / downloaded quality-gates version | 0.2.0 / 0.2.0 |
| Expected / downloaded payload SHA-256 | both `a7c6e396a54fa316a837bd3cc7479254cadb4b09672475649820720eca81add3` |
| Plugin-install attempts | 0 |
| Installer exit | 130, operator cancellation after source verification reported `unverified` |
| External mutating CLI commands | 1, source addition only |

The executed mutating command was:

```text
claude plugin marketplace add https://github.com/tomwangowa/agent-skills.git --scope user --json
```

No refresh, update, removal, dependency installation, Codex installation,
Superpowers installation, model session or hook-trust grant was performed.

## Isolation and the execution-directory adjustment

Private HOME/config/account files were not copied. HOME, CLAUDE_CONFIG_DIR,
XDG_CONFIG_HOME and TMPDIR pointed to fresh directories under the ignored
plan workspace. The absolute real Python interpreter ran with `-I` and a clean
environment. A subprocess observer logged return codes and enforced the exact
approved mutating command allowlist plus a single-attempt guard; it did not
edit the archive/product files.

The original proposal put cwd inside the worktree. Inspection found hooks and
plugin settings in ancestor `.claude/settings*.json` files, so cwd was moved to
a new directory outside every worktree to avoid inheriting project settings.
The change was reported before execution. Settings/evidence remained in the
approved ignored workspace; the allowed native commands did not change.

The original live `settings.json`, `plugins/installed_plugins.json` and
`plugins/known_marketplaces.json` hashes matched before and after the run.
That proves preservation of those three files, not an audit of every host file
or all native network traffic.

Machine evidence is retained under this plan workspace's
`native-claude-wg_3de7y/`: `run.json`, `commands.jsonl`, `result.json`,
`offline-replay.json`, the unpacked original candidate and the downloaded
source. The separate external cwd is recorded in `run.json`. Nothing was
automatically removed.

## Root cause and offline correction

The adapter only read `repo` from Claude marketplace rows. Existing inventory
samples used GitHub shorthand (`source: github`), while the installer's own
source-add command uses a full Git URL and produces `source: git`. The
[official CLI reference](https://code.claude.com/docs/en/plugins/cli-reference)
specifies `repo` for GitHub sources and `url` for Git/URL sources.

The native observation captured `source: git`, name and installLocation, but
the observer's field allowlist omitted `url`. Native `known_marketplaces.json`
independently contains the expected Git URL. Consequently the new fixture is
explicitly **synthetic reconstruction**, not falsely labeled a complete native
CLI capture. A future observer must include URL and field-shape metadata.

The regression test first reproduced `Marketplace source is unknown`. The
adapter now selects the field by source type and still refuses missing,
empty or non-string source values. The host tests passed after the correction.
An offline reconstruction using the retained native metadata and downloaded
payload produced exactly one quality-gates installation action without
executing any CLI/network mutation. Final offline suite: **42 cases, 41 passed,
1 Windows process test skipped**.

## Scoped correction review

Self-review in same Codex session: commitment / recency / framing bias not fully controlled.

- Scope: the marketplace-field branch in `hosts.py`, its regression and the
  explicitly synthetic Git-source fixture. Native command construction,
  approval, scope, payload verification and executor behavior did not change.
- Findings: the observed missing-field defect is fixed offline; no additional
  High/Medium finding was identified in this narrow correction. This is not a
  fresh reviewer context or a passing native acceptance result.
- Adversarial checks: missing/empty/non-string Git URLs still fail closed;
  existing GitHub and Codex cases remain in the passing suite. No unknown
  source is converted to an absent installation or an approved command.
- VERIFIED: six host tests and the 42-case offline suite passed; the retained
  payload produced the exact expected action in an offline reconstruction.
- NOT VERIFIED: the corrected adapter and actual plugin installation in a
  new native process. No additional source-add or install call was made.

## Remaining gap and retry boundary

This run proves source download and local payload equality. It does **not**
prove native plugin installation or the corrected adapter against a fresh CLI
run, and it does not exercise hooks/MCP/skills. R2 is an offline-corrected
candidate. Its source changed, and repeating source download reaches an
external service; a new native run needs new explicit approval under the
project's repeat-operation rule. See the [rerun proposal](native-acceptance-rerun-proposal.md).
