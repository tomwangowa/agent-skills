# User-only Skill Invocation Implementation Plan

> **For agentic workers:** Execute this plan task-by-task with `superpowers:executing-plans`. Do not use subagents unless Tom explicitly requests delegation. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Make `invocation_intent: user` a hard runtime policy while keeping every user-only skill except `skill-router` discoverable through `skill-router` recommendations.

**Architecture:** The catalog remains the policy source of truth. A user-only catalog row requires Claude Code frontmatter and Codex metadata that disable implicit invocation. `skill-router` reads the catalog after matching the registry, converts user-only matches into copyable `$skill-name` recommendations, and treats user-only workflow steps as manual checkpoints.

**Tech Stack:** Python standard library validator and `unittest`; JSON catalog; YAML-shaped skill metadata; Markdown skill instructions.

## Global Constraints

- `invocation_intent: user` means only an explicit `$skill-name` or `/skill-name` starts the skill.
- `routable` means router discovery and recommendation only; it never grants implicit execution.
- Every user-only skill except `skill-router` is discoverable through the router registry.
- Claude Code user-only metadata is exactly `disable-model-invocation: true`.
- Codex user-only metadata is exactly `policy.allow_implicit_invocation: false` in `agents/openai.yaml`.
- Do not sync to a live runtime, call a model, or call an external endpoint during implementation.
- Run `code-review-codex` before asking Tom for any commit approval; do not commit without that approval.

---

## File map

| File | Responsibility |
|---|---|
| `skills-catalog.json` | Declare the four newly discoverable user-only skills as `routable: true`; retain `skill-router` as the only non-routable user skill. |
| `scripts/validate_skills_catalog.py` | Enforce user-only runtime metadata and the catalog/registry discovery rule. |
| `tests/test_validate_skills_catalog.py` | Exercise all new validator failure modes and router instruction contracts. |
| `<user-skill>/SKILL.md` | Add Claude's hard gate to all fourteen user-only skills. |
| `<user-skill>/agents/openai.yaml` | Add Codex's hard gate to all fourteen user-only skills. |
| `skill-router/skill-registry.yaml` | Add the four newly discoverable user-only skills; retain existing user-only entries and workflow definitions. |
| `skill-router/SKILL.md` | Define recommend-only behavior for user-only matches, manual workflow checkpoints, and invocation labels in list mode. |
| `SKILLS_CATALOG.md` | Regenerated index after catalog changes. |

## User-only skill set

`ai-weekly-insight`, `arxiv-digest`, `claude-workflow-designer`,
`deai-voice-rewrite`, `git-status-tui`, `handoff`, `newsletter-digest`,
`qa-to-notes`, `report-generator`, `role-orchestrator`, `skill-router`,
`skill-sync`, `tech-research-pipeline`, and `work-log-analyzer`.

The four catalog rows that change from `routable: false` to `true` are
`claude-workflow-designer`, `deai-voice-rewrite`, `git-status-tui`, and
`handoff`. `skill-router` is excluded from that change.

## Task 1: Make the validator reject incomplete user-only policy

**Files:**

- Modify: `scripts/validate_skills_catalog.py`
- Modify: `tests/test_validate_skills_catalog.py`

**Interfaces:**

- Add `validate_invocation_policy(entries: Iterable[Mapping[str, Any]], root: Path) -> None`.
- Call it from `validate()` after `validate_router()` and before index rendering.
- The function reads `<skill-id>/SKILL.md` and `<skill-id>/agents/openai.yaml` only for catalog rows where `invocation_intent == "user"`.

- [ ] **Step 1: Extend the fixture helpers and write failing validator tests**

Make the default user-only `beta` fixture valid by adding
`disable-model-invocation: true` through `write_skill()` and adding a
`write_openai_metadata()` helper that writes:

```yaml
policy:
  allow_implicit_invocation: false
```

Write tests that start from this valid user-only `beta` fixture and each fail
when one condition is removed or contradicted:

```python
def test_validation_rejects_user_skill_without_claude_hard_gate(self) -> None: ...
def test_validation_rejects_user_skill_without_codex_hard_gate(self) -> None: ...
def test_validation_rejects_model_skill_with_user_only_claude_gate(self) -> None: ...
def test_validation_rejects_model_skill_with_user_only_codex_gate(self) -> None: ...
```

- [ ] **Step 2: Run the four tests and verify RED**

Run:

```bash
python3 -m unittest \
  tests.test_validate_skills_catalog.ValidateSkillsCatalogTests.test_validation_rejects_user_skill_without_claude_hard_gate \
  tests.test_validate_skills_catalog.ValidateSkillsCatalogTests.test_validation_rejects_user_skill_without_codex_hard_gate \
  tests.test_validate_skills_catalog.ValidateSkillsCatalogTests.test_validation_rejects_model_skill_with_user_only_claude_gate \
  tests.test_validate_skills_catalog.ValidateSkillsCatalogTests.test_validation_rejects_model_skill_with_user_only_codex_gate -v
```

Expected: the tests fail because `validate()` does not yet inspect either
runtime metadata file.

- [ ] **Step 3: Add the minimal validator**

Implement `validate_invocation_policy()` with exact scalar checks:

```python
CLAUDE_USER_ONLY = re.compile(r"^disable-model-invocation:\\s*true\\s*$", re.MULTILINE)
CODEX_USER_ONLY = re.compile(
    r"^policy:\\s*\\n\\s+allow_implicit_invocation:\\s*false\\s*$",
    re.MULTILINE,
)
```

For each catalog entry:

- `user`: require both matching metadata forms.
- `model`: reject either user-only form if present.

Report the exact file path and skill ID in every failure.

- [ ] **Step 4: Run the four tests and verify GREEN**

Run the command from Step 2. Expected: all four tests pass.

- [ ] **Step 5: Run the full suite before the next task**

Run:

```bash
python3 -m unittest discover -s tests -p 'test_*.py' -v
```

Expected: all existing tests and the four new tests pass.

## Task 2: Add hard gates to every user-only skill

**Files:**

- Modify: the fourteen `<skill-id>/SKILL.md` files listed in “User-only skill set”
- Create: the fourteen corresponding `<skill-id>/agents/openai.yaml` files

**Consumes:** `validate_invocation_policy()` from Task 1.

**Produces:** Claude Code and Codex metadata that satisfy the catalog policy.

- [ ] **Step 1: Write a failing inventory test**

Add a test that loads the real catalog and calls the validator against
`SOURCE_ROOT`; it must fail until every catalog user skill has both gates:

```python
def test_source_tree_enforces_user_only_runtime_gates(self) -> None:
    result = subprocess.run(
        [sys.executable, str(VALIDATOR), "--check"],
        cwd=SOURCE_ROOT,
        capture_output=True,
        text=True,
    )
    self.assertEqual(result.returncode, 0, result.stderr)
```

Run only this test first. Expected: FAIL mentioning the first user-only skill
without required metadata.

- [ ] **Step 2: Add the Claude frontmatter field**

In each user-only `SKILL.md`, add the scalar inside the existing YAML
frontmatter without changing its name or description:

```yaml
disable-model-invocation: true
```

- [ ] **Step 3: Add the Codex metadata files**

Create `agents/openai.yaml` in each of the fourteen user-only directories:

```yaml
policy:
  allow_implicit_invocation: false
```

Do not add this file to any model-invoked skill.

- [ ] **Step 4: Verify GREEN**

Run the source-tree test from Step 1, then:

```bash
python3 scripts/validate_skills_catalog.py --check
```

Expected: both commands pass.

## Task 3: Make all user-only skills discoverable without self-routing

**Files:**

- Modify: `skills-catalog.json`
- Modify: `skill-router/skill-registry.yaml`
- Modify: `scripts/validate_skills_catalog.py`
- Modify: `tests/test_validate_skills_catalog.py`

**Consumes:** the hard-gate policy from Tasks 1–2.

**Produces:** thirteen discoverable user-only entries and an explicit
`skill-router` resolver exception.

- [ ] **Step 1: Write failing catalog/registry tests**

Add tests for:

```python
def test_validation_rejects_user_skill_other_than_skill_router_when_not_routable(self) -> None: ...
def test_validation_rejects_skill_router_when_routable(self) -> None: ...
```

Use the fixture `beta` for the first case and a fixture skill named
`skill-router` for the second. Expected failures must name the violating skill.

- [ ] **Step 2: Run the two tests and verify RED**

Run the two test methods with `python3 -m unittest ... -v`.

Expected: FAIL because the validator currently treats `routable` independently
from `invocation_intent`.

- [ ] **Step 3: Enforce discovery policy in the validator**

Extend `validate_invocation_policy()`:

```python
if entry["invocation_intent"] == "user" and skill_id != "skill-router":
    if not entry["surfaces"]["routable"]:
        fail(f"{CATALOG_PATH}: user skill {skill_id} must be routable")
elif skill_id == "skill-router" and entry["surfaces"]["routable"]:
    fail(f"{CATALOG_PATH}: skill-router must not route to itself")
```

- [ ] **Step 4: Change the four catalog rows and add registry entries**

Set `routable: true` for `claude-workflow-designer`, `deai-voice-rewrite`,
`git-status-tui`, and `handoff`; leave `skill-router` false. Add the four
newly discoverable skills to the existing matching registry categories using
triggers copied from each skill’s frontmatter description and explicit command
name. Do not add `skill-router` to the registry.

- [ ] **Step 5: Verify GREEN and regenerate the index**

Run:

```bash
python3 -m unittest discover -s tests -p 'test_*.py' -v
python3 scripts/validate_skills_catalog.py --write
python3 scripts/validate_skills_catalog.py --check
```

Expected: all tests pass and `SKILLS_CATALOG.md` has only the intended router
status changes.

## Task 4: Make routing and workflows recommend-only for user skills

**Files:**

- Modify: `skill-router/SKILL.md`
- Modify: `tests/test_validate_skills_catalog.py`

**Consumes:** catalog invocation intent and registry entries from Task 3.

**Produces:** a documented router contract that does not implicitly launch
user-only skills.

- [ ] **Step 1: Write a failing router contract test**

Extend `SkillRouterListModeContractTests` or add
`SkillRouterInvocationContractTests`. Extract the Mode 1 and workflow sections
and assert they contain all of:

```python
self.assertIn("skills-catalog.json", smart_routing)
self.assertIn("$skill-name", smart_routing)
self.assertIn("must not invoke", smart_routing)
self.assertIn("manual checkpoint", workflows)
self.assertIn("Invocation", list_mode)
```

- [ ] **Step 2: Run the contract test and verify RED**

Run only the new contract test. Expected: FAIL because Mode 1 currently reads
only the registry and directs the agent to invoke after confirmation.

- [ ] **Step 3: Update the router instructions**

Make these exact behavioral changes:

- Mode 1 reads `skills-catalog.json` after a match. A catalog `user` match
  returns a short recommendation and `$skill-name`, then stops.
- Mode 1 retains the existing invocation flow only for a catalog `model` match.
- List-mode category tables add an `Invocation` column for every entry.
- Workflow handling labels a user-only step as `manual checkpoint` and prints
  its `$skill-name`; it never invokes that step after a general confirmation.
- Retain `full-research` and `role-pipeline` as discovery entry points; their
  sole user-only steps become manual checkpoints.

- [ ] **Step 4: Run the contract test and verify GREEN**

Run the command from Step 2. Expected: PASS.

- [ ] **Step 5: Run skill audit**

Run:

```bash
bash skill-auditor/scripts/audit_skill.sh skill-router
```

Delete the generated `skill-router-audit-report.md` after reading it; it is a
local audit artifact, not part of the change.

## Task 5: Final verification and review

**Files:** all files modified by Tasks 1–4.

- [ ] **Step 1: Run complete local verification**

```bash
python3 -m unittest discover -s tests -p 'test_*.py' -v
python3 scripts/validate_skills_catalog.py --check
git diff --check
git status --short
```

Expected: all tests pass, catalog check passes, no whitespace errors, and only
the planned source, metadata, test, registry, and generated-index files are
modified.

- [ ] **Step 2: Run native Codex review**

Use `code-review-codex` on the complete branch diff. Read every changed skill
metadata file and the validator/test diff. Record any findings and fix only
findings within this plan’s scope.

- [ ] **Step 3: Ask Tom for commit approval**

Propose the conventional commit message:

```text
feat(skills): enforce user-only invocation policy
```

Do not stage, commit, push, merge, or sync skills without Tom’s explicit
approval for that action.

- [ ] **Step 4: Post-merge manual smoke, only after authorization**

After a separately authorized sync to the installed Claude Code and Codex
skill directories, start fresh sessions. Confirm that user-only skills are not
implicitly available while an explicit `/skill-name` or `$skill-name` still
works. Do not call a model or external endpoint during this smoke.
