# Package Unpackaged Skills Implementation Plan

> **Superseded in part:** after the final review the owner widened scope (arxiv-digest added, 48 members, all seven packages bumped, shipped re-acceptance wording made generic). The spec's Decisions and Changes sections are authoritative; this plan records the original task breakdown.

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Ship seven more skills in four existing plugin packages and bump those packages by one minor version.

**Architecture:** Package membership lives in `plugin-packages.json`; `scripts/build_plugins.py --write` renders `plugins/claude/` and `plugins/codex/` plus `.claude-plugin/marketplace.json`. Two skills first get portable script paths so they work from a versioned plugin cache.

**Tech Stack:** Python 3 (`unittest`), JSON config, npm (skills-query-server audit only), Claude Code CLI (`claude plugin validate`).

**Spec:** `docs/superpowers/specs/2026-11-08-package-unpackaged-skills-design.md`

## Global Constraints

- Work only in this worktree on `feat/plugins-add-unpackaged-skills`; never touch `production`.
- Versions: quality-gates `0.2.0`, work-journal `0.2.0`, content-tools `0.2.0`, repo-workflow `0.3.0`; the other three packages keep their versions.
- Total packaged source skills: `47`.
- Never hand-edit `plugins/claude/`, `plugins/codex/` or `.claude-plugin/marketplace.json`; regenerate with `python3 scripts/build_plugins.py --write`.
- `plugin-packages.json` and its generated output go in the same commit.
- No personal absolute paths in tracked files; write `~`.
- Every commit needs Tom's explicit approval first. Before proposing a commit, load `completion-gate` and follow its L0/L1/L2 rule (L1/L2 run `code-review-claude` once).
- `npm ci` / `npm audit` contact the npm registry: ask Tom before running them.

## Review Focus

1. A packaged skill still names `~/.claude/skills/<skill>/scripts/...`: works on Tom's machine, fails for every plugin user. Pinned by `test_packaged_skills_use_portable_script_paths` (Task 1).
2. `report-generator` sibling paths when the Codex plugin layout differs from Claude's: the sibling scripts must resolve in both generated trees. Pinned by Task 4 Step 1.
3. A runtime resource is missing from the whitelist (for example `parse_emls.py`): the skill installs but its script is absent. Pinned by Task 4 Step 2 and `build_plugins.py --check`.
4. content-tools declares `report-generator` from `work-journal`, but the skill is missing there: `validate_packages` must reject it. Pinned by `test_cross_package_dependency_must_be_offered` (Task 2).
5. A non-zero npm audit is silently recorded as evidence: `verify_acceptance` would later fail at release time. Pinned by Task 3 Step 2 (stop on `total != 0`).

---

### Task 0: Baseline

- [ ] **Step 1: Run the CI checks on the clean branch**

```bash
python3 scripts/build_plugins.py --check && python3 scripts/check_plugin_release.py && python3 -m unittest discover -s tests
```

Expected: all pass. If anything fails, stop and report it to Tom as pre-existing; do not count it against this change. (`npm test` for the server is unaffected by this change and needs `npm ci`; skip it unless Tom approves the registry call.)

### Task 1: Portable script paths

**Files:**
- Modify: `newsletter-digest/SKILL.md:64`, `newsletter-digest/SKILL.md:176`
- Modify: `report-generator/SKILL.md:69-70`
- Test: `tests/test_plugin_packages.py`

**Interfaces:**
- Produces: SKILL.md text using `<skill_base_directory>` (the base directory shown when the skill loads), same convention as `work-log-analyzer/SKILL.md:57`.

- [ ] **Step 1: Write the failing test** in `PackageTests`:

```python
def test_packaged_skills_use_portable_script_paths(self):
    pattern = re.compile(r'~/\.claude/skills/[a-z0-9-]+/(scripts|templates|references)/')
    offenders = [s for p in self.packages for s in p['skills']
                 if pattern.search((ROOT / s / 'SKILL.md').read_text(encoding='utf-8'))]
    self.assertEqual(offenders, [])
```

(add `import re`). This is the long-term regression guard; it passes now because the two skills are not packaged yet, and must still pass after Task 2. The test that fails first checks the two files directly:

```python
def test_new_members_use_portable_script_paths(self):
    for skill in ['newsletter-digest', 'report-generator']:
        text = (ROOT / skill / 'SKILL.md').read_text(encoding='utf-8')
        self.assertNotIn('~/.claude/skills/', text, skill)
```

- [ ] **Step 2: Run to verify it fails**

Run: `python3 -m unittest tests.test_plugin_packages -k portable -v`
Expected: `test_new_members_use_portable_script_paths` FAILS for `newsletter-digest`.

- [ ] **Step 3: Edit the two SKILL.md files**

- newsletter-digest line 64: `python3 <skill_base_directory>/scripts/parse_emls.py "<folder_path>" -o /tmp/newsletter-digest.json`; line 176: expected path `<skill_base_directory>/scripts/parse_emls.py`. Add one sentence near line 64 defining `<skill_base_directory>` as the base directory shown when this skill loads.
- report-generator lines 69-70: `bash <skill_base_directory>/../activity-logger/scripts/init_activities.sh list` and `bash <skill_base_directory>/../work-log-analyzer/scripts/aggregate_activities.sh \`, with the same one-sentence definition, plus: "These sibling skills ship in the same work-journal package."

- [ ] **Step 4: Run to verify it passes**

Run: `python3 -m unittest tests.test_plugin_packages -k portable -v`
Expected: both tests PASS.

- [ ] **Step 5: Propose commit to Tom** (`fix(skills): use portable script paths in newsletter-digest and report-generator`), after the completion-gate check.

### Task 2: Package membership, versions and generated output

**Files:**
- Modify: `plugin-packages.json`
- Modify: `scripts/plugin_packaging/catalog.py:102-103`
- Modify: `tests/test_plugin_packages.py:13-42`
- Modify: `README.md:21`, `README.zh.md:21`, `docs/plugins/README.md:15`
- Regenerate: `plugins/claude/`, `plugins/codex/`, `.claude-plugin/marketplace.json`

**Interfaces:**
- Consumes: Task 1's portable SKILL.md files.
- Produces: package definitions that Task 4 verifies in the generated trees.

- [ ] **Step 1: Update test expectations first**

In `APPROVED`: append `review-convergence-gate` to quality-gates; `understand-file understand-function understand-repo` to repo-workflow; `newsletter-digest qa-to-notes` to content-tools; `report-generator` to work-journal. In `APPROVED_VERSIONS`: the four versions from Global Constraints. Line 42: `(47, 47)`. Add:

```python
def test_cross_package_dependency_must_be_offered(self):
    packages = copy.deepcopy(self.packages)
    journal = next(p for p in packages if p['name'] == 'work-journal')
    journal['skills'].remove('report-generator')
    self.assertTrue(any('absent from work-journal' in e
                        for e in validate_packages(packages, self.catalog)))
```

- [ ] **Step 2: Run to verify failure**

Run: `python3 -m unittest tests.test_plugin_packages -v`
Expected: `test_exact_approved_membership` FAILS; `test_cross_package_dependency_must_be_offered` ERRORS (`report-generator` is not in work-journal yet).

- [ ] **Step 3: Edit `plugin-packages.json` and `catalog.py`**

- Skills, versions as in Step 1 (append new skills at the end of each list, matching `APPROVED` order).
- `runtime_resources` additions: work-journal `report-generator/agents/openai.yaml`; content-tools `newsletter-digest/agents/openai.yaml`, `newsletter-digest/scripts/parse_emls.py`, `qa-to-notes/agents/openai.yaml`; repo-workflow `understand-file/agents/openai.yaml`, `understand-function/agents/openai.yaml`, `understand-repo/agents/openai.yaml`.
- content-tools `requirements.commands`: `["python3"]`.
- content-tools dependency on `report-generator`: `provider` `"work-journal"`, keep `kind` `"optional"`, `condition` `"Only when the work-journal package is installed"`.
- `catalog.py:102-103`: `47` and message `'Exactly 47 distinct source skills are required'`.
- README wording: `40` → `47` in the three lines listed (keep the rest of each sentence).

- [ ] **Step 4: Regenerate**

Run: `python3 scripts/build_plugins.py --write && python3 scripts/build_plugins.py --check`
Expected: write succeeds; check reports no drift. `.claude-plugin/marketplace.json` shows the four new versions.

- [ ] **Step 5: Run tests**

Run: `python3 -m unittest discover -s tests && python3 scripts/check_plugin_release.py`
Expected: all pass.

- [ ] **Step 6: Commit together with Task 3** (generated output and audit evidence ship in one commit; see Task 3 Step 4).

### Task 3: work-journal audit evidence

**Files:**
- Modify: `docs/validation/skill-plugins/production-audit.json`
- Modify: `docs/validation/skill-plugins/acceptance.json` (the `production-audit.json` sha256 entry)

- [ ] **Step 1: Ask Tom to approve the registry calls**, then run:

```bash
cd skills-query-server && npm ci && npm audit --omit=dev --json > ../docs/validation/skill-plugins/production-audit.json
```

`--omit=dev` matches what `build_plugins.py:66` ships (`npm ci --omit=dev`).

- [ ] **Step 2: Check the result**

Run: `python3 -c "import json;print(json.load(open('docs/validation/skill-plugins/production-audit.json'))['metadata']['vulnerabilities']['total'])"`
Expected: `0`. If not `0`, stop and report the findings to Tom; do not record them as evidence.

- [ ] **Step 3: Update the hash**

Run: `shasum -a 256 docs/validation/skill-plugins/production-audit.json` and put the value in the `production-audit.json` entry of `acceptance.json`. If the audit file is byte-identical to the committed one, leave both unchanged and note it.

- [ ] **Step 4: Propose commit to Tom** (`feat(plugins): package seven more skills in four packages`) covering Tasks 2-3, after the completion-gate check.

### Task 4: Verify the generated trees

No file changes; this is the evidence for the PR.

- [ ] **Step 1: Sibling paths resolve in both layouts**

For `root` in `plugins/claude/work-journal/skills` and `plugins/codex/work-journal/skills`:

```bash
base="$root/report-generator"
test -f "$base/../activity-logger/scripts/init_activities.sh" && test -f "$base/../work-log-analyzer/scripts/aggregate_activities.sh"
```

Then run `CLAUDE_ACTIVITIES_DIR="$scratch/activities" AGENT_SKILLS_CONFIG_DIR="$scratch/config" bash "$base/../activity-logger/scripts/init_activities.sh" list` with `$scratch` an empty session scratch folder. Expected: exits 0 and reports no activities; real activity data is untouched.

- [ ] **Step 2: Bundled parser runs**

Run: `python3 plugins/claude/content-tools/skills/newsletter-digest/scripts/parse_emls.py --help` and the same under `plugins/codex/`.
Expected: usage text, exit 0.

- [ ] **Step 3: Strict validation**

Run: `claude plugin validate --strict plugins/claude/<name>` for quality-gates, work-journal, content-tools, repo-workflow.
Expected: each passes.

- [ ] **Step 4: Open the PR** after Tom approves pushing: `git push -u origin feat/plugins-add-unpackaged-skills`, PR body lists the four versions, the excluded skills with reasons, and Task 4 evidence. After merge: remind Tom to sync `production` (local and remote) and to tag `quality-gates-v0.2.0`, `work-journal-v0.2.0`, `content-tools-v0.2.0`, `repo-workflow-v0.3.0`.
