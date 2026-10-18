# CI and Acceptance Wording Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Add a macOS CI gate for tests and plugin integrity, make the work-journal server bundle independent of the npm version, and correct the current-state acceptance wording.

**Architecture:** PR-1 adds one workflow with one job, removes npm's hidden lockfile from the generated server bundle, and adds the first test that runs the generated bundle. After PR-1 merges, a ruleset makes that job required on `main`. PR-2 rewrites the acceptance wording at its sources and regenerates the 14 packages under CI.

**Tech Stack:** GitHub Actions (macOS 26 arm64), Python 3.12 `unittest`, Node 24 with Vitest, `scripts/build_plugins.py`.

**Spec:** `docs/superpowers/specs/2026-10-18-ci-and-acceptance-wording-design.md`

## Global Constraints

- Every commit needs the user's explicit approval first. Before proposing one, classify it with `completion-gate` (L0/L1/L2) and run `code-review-claude` once for L1 or L2.
- Commit messages follow Conventional Commits and end with `Co-Authored-By: Claude Opus 5.5 <noreply@anthropic.com>`. PR descriptions end with `🤖 Generated with [Claude Code](https://claude.com/claude-code)`.
- Do not bump any plugin version. Do not edit `artifact_bindings` or evidence hashes in `acceptance.json`.
- Do not add `continue-on-error`, and do not remove a check to turn CI green.
- Workflow: file `.github/workflows/tests-and-plugin-integrity.yml`, workflow name `Tests and plugin integrity`, job id and name `tests-and-plugin-integrity`, `runs-on: macos-26`, Python `3.12`, Node `24`.
- Pin actions by commit SHA:
  - checkout `3d3c42e5aac5ba805825da76410c181273ba90b1` (v7.0.1)
  - setup-python `5fda3b95a4ea91299a34e894583c3862153e4b97` (v7.0.0)
  - setup-node `949feb2413d6458794dcd2491c4babbbce0c15c1` (v7.1.0)
- Leave `docs/validation/skill-plugins/task-8-release-validation.md` and `docs/plugins/superpowers-compatibility.md` unchanged.
- Generated files under `plugins/` change only through `python3 scripts/build_plugins.py --write`.

## Review Focus

1. **The runner's npm writes some other file differently from local npm 11.2.0.** Expected: `--check` passes on the runner. Pinned by the PR-1 CI run (Task 4). On drift, Task 4 adds a step that prints the differing paths.
2. **The generated bundle runs only with its own production `node_modules`, without the hidden lockfile or any dev dependency.** Expected: an MCP round trip succeeds. Pinned by Task 2.
3. **A test assumes local state the runner lacks (a home-directory file, git identity, an installed CLI).** Expected: the full suite passes on a clean runner. Pinned by the PR-1 CI run (Task 4).
4. **Two pushes to `main` in quick succession.** Expected: each `main` commit keeps a completed run; only PR runs are cancelled. Pinned by the per-commit `concurrency.group` for non-PR events in Task 3. A per-ref group is not enough: GitHub keeps at most one pending run per group, so a third quick push would cancel the second.
5. **The ruleset blocks the admin's own emergency merge, or never matches the check.** Expected: the check `tests-and-plugin-integrity` is required, and the admin can bypass. Pinned by the read-back in Task 5.

---

## PR-1 (branch `ci/tests-and-plugin-integrity`)

### Task 1: Drop npm's hidden lockfile from the server bundle

**Files:**
- Modify: `scripts/build_plugins.py:41-44` (`prepare_server`)
- Test: `tests/test_build_plugins.py`
- Regenerated: `plugins/{claude,codex}/work-journal/server/node_modules/.package-lock.json` (deleted), `plugins/{claude,codex}/work-journal/.generated-files.json`

**Interfaces:**
- Produces: the generated work-journal bundles no longer contain `server/node_modules/.package-lock.json`. Task 2 relies on this.

- [ ] **Step 1: Baseline.** From `main`, create `ci/tests-and-plugin-integrity`. Run `python3 -m unittest discover -s tests`, `python3 scripts/build_plugins.py --check`, `python3 scripts/check_plugin_release.py` and `npm --prefix skills-query-server test`. Expected: all pass. If any fails, stop and report; do not attribute it to this plan.

- [ ] **Step 2: Write the failing test** in `BuildTests`:

```python
def test_generated_server_bundles_omit_npm_hidden_lockfile(self):
    for surface in ('claude', 'codex'):
        bundle = ROOT / 'plugins' / surface / 'work-journal/server'
        self.assertTrue((bundle / 'dist/index.js').is_file())
        self.assertFalse((bundle / 'node_modules/.package-lock.json').exists())
        inventory = json.loads((ROOT / 'plugins' / surface / 'work-journal/.generated-files.json').read_text())
        self.assertNotIn('server/node_modules/.package-lock.json', inventory['files'])
```

- [ ] **Step 3: Run it.** Command: `python3 -m unittest tests.test_build_plugins.BuildTests.test_generated_server_bundles_omit_npm_hidden_lockfile -v`. Expected: FAIL on the `assertFalse` (the file exists).

- [ ] **Step 4: Implement.** In `prepare_server`, after the `npm ci` call, add `(destination / 'node_modules/.package-lock.json').unlink(missing_ok=True)`. Put it next to the `.bin` removal, with a comment saying why: npm alone reads this cache, and its contents vary with the npm version.

- [ ] **Step 5: Regenerate.** Run `python3 scripts/build_plugins.py --write`, then `git status --short`. Expected: exactly 2 deleted `.package-lock.json` files and 2 modified `work-journal/.generated-files.json` files, plus the two source edits. If `.source.json` or other packages change, stop and investigate.

- [ ] **Step 6: Verify.** Re-run the Step 3 test (PASS), `--check` (`Generated outputs match source`), `check_plugin_release.py` (passed) and the full `unittest` (OK).

- [ ] **Step 7: Commit (after user approval).** `fix(plugins): omit npm hidden lockfile from server bundle`

### Task 2: Run the generated bundle in a smoke test

**Files:**
- Modify: `skills-query-server/src/stdio.integration.test.ts`

**Interfaces:**
- Consumes: the Task 1 bundles at `plugins/{claude,codex}/work-journal/server/`.

- [ ] **Step 1: Add the test.** Extend `fixture()` with an optional `bundle?: string`. When it is given, `cpSync` that directory recursively into `server bundle` instead of copying `dist` and symlinking `node_modules`, and set `entry` to `join(server, 'launch.mjs')`. Then add, inside the existing `describe`:

```ts
for (const surface of ['claude', 'codex']) {
  it(`the generated ${surface} work-journal bundle runs on its own production dependencies`, async () => {
    const f = fixture(false, join(repo, 'plugins', surface, 'work-journal/server'));
    expect(existsSync(join(f.server, 'node_modules/.package-lock.json'))).toBe(false);
    expect(existsSync(join(f.server, 'node_modules/vitest'))).toBe(false);
    const result = await runSmoke(process.execPath, [f.entry], f.env);
    expect(result.tools).toContain('log_activity');
    expect(result.roundTrip).toBe(true);
  }, 20000);
}
```

`existsSync` comes from `node:fs`. The fixture's `AGENT_SKILLS_CONFIG_DIR` keeps every write inside the temporary directory.

- [ ] **Step 2: Check that the test exercises the bundle.** Temporarily rename `plugins/claude/work-journal/server/node_modules` and run `npm --prefix skills-query-server run test:unit -- src/stdio.integration.test.ts`. Expected: the claude case FAILS because the server cannot load its dependencies. Restore the directory and confirm `git status` shows no change under `plugins/`.

- [ ] **Step 3: Run.** `npm --prefix skills-query-server test`. Expected: all pass, including both new cases.

- [ ] **Step 4: Commit (after user approval).** `test(work-journal): smoke-test the generated server bundle`

### Task 3: Add the workflow

**Files:**
- Create: `.github/workflows/tests-and-plugin-integrity.yml`

- [ ] **Step 1: Write the workflow.** The spec fixes this content:

```yaml
name: Tests and plugin integrity

on:
  pull_request:
    branches: [main]
  push:
    branches: [main]
  workflow_dispatch:

permissions:
  contents: read

concurrency:
  group: ${{ github.workflow }}-${{ github.event_name == 'pull_request' && github.ref || github.sha }}
  cancel-in-progress: ${{ github.event_name == 'pull_request' }}

jobs:
  tests-and-plugin-integrity:
    name: tests-and-plugin-integrity
    runs-on: macos-26
    steps:
      - uses: actions/checkout@3d3c42e5aac5ba805825da76410c181273ba90b1 # v7.0.1
      - uses: actions/setup-python@5fda3b95a4ea91299a34e894583c3862153e4b97 # v7.0.0
        with:
          python-version: '3.12'
      - uses: actions/setup-node@949feb2413d6458794dcd2491c4babbbce0c15c1 # v7.1.0
        with:
          node-version: '24'
          cache: npm
          cache-dependency-path: skills-query-server/package-lock.json
      - name: Install server dependencies
        working-directory: skills-query-server
        run: npm ci
      - name: Generated plugins match source
        run: python3 scripts/build_plugins.py --check
      - name: Release artifact integrity
        run: python3 scripts/check_plugin_release.py
      - name: Python tests
        run: python3 -m unittest discover -s tests
      - name: Server tests
        working-directory: skills-query-server
        run: npm test
```

- [ ] **Step 2: Validate the syntax.** Run `python3 -c "import yaml,sys; d=yaml.safe_load(open('.github/workflows/tests-and-plugin-integrity.yml')); assert list(d['jobs'])==['tests-and-plugin-integrity']; print('ok')"`. Expected: `ok`. actionlint is not installed locally; the runner itself is the final check (Task 4).

- [ ] **Step 3: Commit (after user approval).** `ci: add tests and plugin integrity workflow`

### Task 4: Open PR-1 and get it green

- [ ] **Step 1: Push and open the PR.** Push `ci/tests-and-plugin-integrity` and run `gh pr create --base main`. The description includes the Summary, Verification and Remaining review gates sections. It must say that `work-journal`'s `native_binding` changes, that this binding was already stale, and that `--require-acceptance` still fails as it did on `main`.

- [ ] **Step 2: Watch the run.** `gh pr checks <n> --watch`. Expected: `tests-and-plugin-integrity` passes.

- [ ] **Step 3: If it fails,** invoke `superpowers:systematic-debugging` before changing anything. If `--check` reports drift, add a step before it that rebuilds into a kept staging directory and prints the differing paths (same approach as the local per-file comparison). Fix the root cause, then remove the diagnostic step. Each fix is its own commit and needs approval.

- [ ] **Step 4: Hand over for merge.** Report the green run to the user. The user merges.

## After PR-1 merges

### Task 5: Require the check on `main`

- [ ] **Step 1: Confirm the check ran on `main`.** `gh run list --branch main --workflow tests-and-plugin-integrity.yml --limit 1`. Expected: `completed success`.

- [ ] **Step 2: Draft the ruleset.** Before writing the payload, verify two values against the GitHub REST docs for repository rulesets: the `integration_id` of GitHub Actions, and the `actor_id` of the admin repository role. Payload:

```json
{
  "name": "main requires tests-and-plugin-integrity",
  "target": "branch",
  "enforcement": "active",
  "conditions": {"ref_name": {"include": ["~DEFAULT_BRANCH"], "exclude": []}},
  "bypass_actors": [{"actor_id": "<admin role id>", "actor_type": "RepositoryRole", "bypass_mode": "always"}],
  "rules": [{"type": "required_status_checks", "parameters": {
    "strict_required_status_checks_policy": false,
    "required_status_checks": [{"context": "tests-and-plugin-integrity", "integration_id": "<GitHub Actions app id>"}]}}]
}
```

- [ ] **Step 3: Show the payload to the user. Send it only after approval:** `gh api -X POST repos/tomwangowa/agent-skills/rulesets --input <file>`.

- [ ] **Step 4: Read it back.** `gh api repos/tomwangowa/agent-skills/rulesets/<id>`. Expected: `enforcement: active`, context `tests-and-plugin-integrity`, and an admin bypass actor.

## PR-2 (branch `docs/acceptance-scope`, from the updated `main`)

### Task 6: Correct the generated wording

**Files:**
- Modify: `scripts/plugin_packaging/render.py:153-155`, `docs/plugins/installation.md:3`
- Test: `tests/test_build_plugins.py`
- Regenerated: 14 × `README.md`, `installation.md`, `.generated-files.json`, `.source.json` under `plugins/`

- [ ] **Step 1: Write the failing test** in `BuildTests`:

```python
def test_generated_docs_state_acceptance_scope(self):
    stale = ['Native acceptance passed', '七包已在',
             'Remote marketplace installation and release approval remain pending']
    for surface in ('claude', 'codex'):
        for package in (p for p in (ROOT / 'plugins' / surface).iterdir() if p.is_dir()):
            for name in ('README.md', 'installation.md'):
                text = (package / name).read_text()
                for phrase in stale:
                    self.assertNotIn(phrase, text, f'{package.name}/{name}')
                self.assertIn('work-journal', text)
```

- [ ] **Step 2: Run it.** Command: `python3 -m unittest tests.test_build_plugins.BuildTests.test_generated_docs_state_acceptance_scope -v`. Expected: FAIL on `Native acceptance passed`.

- [ ] **Step 3: Replace the `render.py` README sentence** with this exact text:

> Native acceptance on 2026-10-15 covered all seven packages with Claude Code CLI 2.1.300 and Codex CLI 0.162.1 on isolated macOS fixtures. session-preferences and work-journal changed after that run and need native acceptance again before release. Claude Code CLI 2.1.302 verified GitHub marketplace installation and update checks on 2026-10-17; Codex CLI remote marketplace installation and release approval remain pending.

- [ ] **Step 4: Edit `docs/plugins/installation.md:3`.** Replace `七包已在 macOS 隔離 fixture，以 Claude Code 2.1.300、Codex 0.162.1 實測安裝、hooks、MCP、路由、更新與 fixture 遷移。` with:

> 2026-10-15 的原生驗收在 macOS 隔離 fixture 上，以 Claude Code 2.1.300、Codex 0.162.1 測過七包的安裝、hooks、MCP、路由、更新與 fixture 遷移；`session-preferences` 與 `work-journal` 在那之後有修改，發布前需要重新驗收。

- [ ] **Step 5: Regenerate and verify.** `--write`, then the Step 2 test (PASS), `--check`, `check_plugin_release.py`, and the full `unittest`. `git status` must show changes only to the two sources, the test, and the 14 packages' `README.md`, `installation.md`, `.generated-files.json` and `.source.json`.

- [ ] **Step 6: Commit (after user approval).** `docs(plugins): state which packages need re-acceptance`

### Task 7: Correct the repository and validation records

**Files:**
- Modify: `README.md:21`, `README.zh.md:21`, `docs/validation/skill-plugins/README.md:3-11`, `docs/validation/skill-plugins/acceptance.json` (`limits`)

- [ ] **Step 1: `README.md:21`.** Replace `Native acceptance passed on macOS with isolated fixtures using Claude Code CLI 2.1.300 and Codex CLI 0.162.1.` with:

> Native acceptance on 2026-10-15 covered all seven packages on macOS with isolated fixtures using Claude Code CLI 2.1.300 and Codex CLI 0.162.1; session-preferences and work-journal changed afterward and need native acceptance again before release.

- [ ] **Step 2: `README.zh.md:21`.** Replace `已在 macOS 隔離 fixture，使用 Claude Code CLI 2.1.300 與 Codex CLI 0.162.1 完成原生驗收。` with:

> 2026-10-15 的原生驗收在 macOS 隔離 fixture 上，使用 Claude Code CLI 2.1.300 與 Codex CLI 0.162.1 涵蓋七包；`session-preferences` 與 `work-journal` 在那之後有修改，發布前需要重新驗收。

- [ ] **Step 3: Validation README.** After the sentence ending `using a unique local marketplace and disposable fixtures.`, add:

> session-preferences and work-journal changed after that run (d738ec4 changed runtime migration path matching; a later change removed npm's hidden lockfile from the work-journal server bundle). Their recorded bindings are stale, so `check_plugin_release.py --require-acceptance` fails until native acceptance is re-run for these two packages before release.

- [ ] **Step 4: Append to `acceptance.json` `limits`:**

> The recorded session-preferences and work-journal bindings predate d738ec4 (runtime migration path normalization) and the removal of node_modules/.package-lock.json from the work-journal server bundle; check_plugin_release.py --require-acceptance fails until native acceptance is re-run for these two packages before release.

- [ ] **Step 5: Verify.** Validate the JSON with `python3 -m json.tool docs/validation/skill-plugins/acceptance.json >/dev/null`. Run `grep -rnE '七包已在|Native acceptance passed|完成原生驗收|Remote marketplace installation and release approval remain pending' README.md README.zh.md docs/plugins plugins`; expected: no output. Run `git diff --stat docs/validation/skill-plugins/task-8-release-validation.md docs/plugins/superpowers-compatibility.md`; expected: empty. Run the full `unittest`; expected: OK.

- [ ] **Step 6: Commit (after user approval).** `docs: record which packages need re-acceptance`

### Task 8: Open PR-2 and correct #31

- [ ] **Step 1: Open the PR.** Push and run `gh pr create --base main`, then `gh pr checks <n> --watch`. Expected: `tests-and-plugin-integrity` passes.

- [ ] **Step 2: Correct #31.** Show this comment to the user and post it only after approval (`gh pr comment 31 --body-file <file>`):

> Correction: the last line of this PR's description is wrong for existing installations. The plugin versions did not change, so `claude plugin update` reports `up_to_date` and does not fetch the new documentation. New installations get it; existing installations get it with the next version bump, which is planned together with native re-acceptance before release.

- [ ] **Step 3: Hand over for merge.** Report the green run and the posted comment to the user.
