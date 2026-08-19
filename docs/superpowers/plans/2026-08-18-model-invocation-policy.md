# Model Invocation Policy Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Allow the agent to invoke `work-log-analyzer` and `skill-router` while preserving router non-self-recommendation and downstream user-only confirmation gates.

**Architecture:** Keep invocation permission, catalog intent, and router eligibility as separate policy layers. Remove user-only gates only from the two target skills, update the catalog to `model`, and revise the router contract so automatic routing does not bypass a downstream user-only skill’s manual checkpoint. Leave `activity-logger` and all core skill behavior unchanged.

**Tech Stack:** Markdown/YAML skill metadata, JSON catalog, Python `unittest`, repository catalog validator, `skill-auditor`, SHA-256 parity checks.

---

## File Map

- Modify: `work-log-analyzer/SKILL.md` — remove the Claude user-only frontmatter gate; keep read-only query behavior unchanged.
- Modify: `work-log-analyzer/agents/openai.yaml` — remove the Codex implicit-invocation denial.
- Modify: `skill-router/SKILL.md` — remove the Claude user-only gate and clarify router-vs-downstream invocation behavior.
- Modify: `skill-router/agents/openai.yaml` — remove the Codex implicit-invocation denial.
- Modify: `skills-catalog.json` — change only the two target entries from `invocation_intent: "user"` to `"model"`; keep their existing `surfaces` values, especially router `routable: false`.
- Modify: `tests/test_validate_skills_catalog.py` — add regression assertions for the target catalog metadata and router contract while retaining the generic validator coverage for user-only gates.
- Do not modify: `activity-logger/SKILL.md`, `skill-router/skill-registry.yaml`, or `scripts/validate_skills_catalog.py` unless validation exposes an already-unseen inconsistency; the approved design does not require changes there.
- Create: no new runtime source files.

## Task 1: Add failing regression coverage for the policy contract

**Files:**
- Modify: `tests/test_validate_skills_catalog.py:915-953`

- [ ] **Step 1: Add a catalog policy test for the two target skills**

Add a test class method that reads `skills-catalog.json`, finds `skill-router` and `work-log-analyzer`, and asserts:

```python
def test_target_skills_are_model_invokable_with_router_non_routable(self) -> None:
    catalog = json.loads(
        (SOURCE_ROOT / "skills-catalog.json").read_text(encoding="utf-8")
    )
    entries = {entry["id"]: entry for entry in catalog["skills"]}

    self.assertEqual(entries["skill-router"]["invocation_intent"], "model")
    self.assertEqual(entries["work-log-analyzer"]["invocation_intent"], "model")
    self.assertFalse(entries["skill-router"]["surfaces"]["routable"])
    self.assertTrue(entries["work-log-analyzer"]["surfaces"]["routable"])
```

- [ ] **Step 2: Add a source metadata test for removed user-only gates**

Add a test that reads both target `SKILL.md` files and both target `agents/openai.yaml` files and asserts the old gate strings are absent:

```python
def test_target_skills_do_not_keep_user_only_runtime_gates(self) -> None:
    for skill_id in ("work-log-analyzer", "skill-router"):
        skill_text = (SOURCE_ROOT / skill_id / "SKILL.md").read_text(
            encoding="utf-8"
        )
        openai_text = (SOURCE_ROOT / skill_id / "agents" / "openai.yaml").read_text(
            encoding="utf-8"
        )

        self.assertNotIn("disable-model-invocation: true", skill_text)
        self.assertNotIn("allow_implicit_invocation: false", openai_text)
```

- [ ] **Step 3: Extend the router contract test with the new boundary**

In `SkillRouterListModeContractTests`, add assertions against Mode 1 that preserve the approved behavior:

```python
def test_smart_routing_separates_router_invocation_from_downstream_execution(self) -> None:
    smart_routing = self.section(
        "## Mode 1 — Smart Routing (default)", "## Mode 2 — Category Browse (`list`)"
    )

    self.assertRegex(smart_routing, r"(?i)router.*(agent|model).*invoke")
    self.assertIn("downstream", smart_routing)
    self.assertIn("user-only", smart_routing)
    self.assertIn("manual checkpoint", smart_routing)
```

- [ ] **Step 4: Run the focused tests and confirm they fail for the current state**

Run:

```bash
python3 -m unittest \
  tests.test_validate_skills_catalog.SkillRouterListModeContractTests \
  tests.test_validate_skills_catalog.ValidateSkillsCatalogTests.test_source_tree_enforces_user_only_runtime_gates
```

Expected: the new catalog, metadata, and router-boundary assertions fail because the current target entries still declare `user` and retain the runtime gates; the existing validator test should continue to pass.

## Task 2: Remove the two target skills’ user-only gates

**Files:**
- Modify: `work-log-analyzer/SKILL.md:1-5`
- Modify: `work-log-analyzer/agents/openai.yaml:1-2`
- Modify: `skill-router/SKILL.md:1-5`
- Modify: `skill-router/agents/openai.yaml:1-2`

- [ ] **Step 1: Remove only the Claude frontmatter gate**

For each target `SKILL.md`, change the frontmatter from:

```yaml
disable-model-invocation: true
```

to no equivalent replacement. Keep `name`, `description`, and all body content unchanged except for the router contract edits in Task 3.

- [ ] **Step 2: Remove only the Codex implicit-invocation denial**

For each target `agents/openai.yaml`, remove the entire two-line block:

```yaml
policy:
  allow_implicit_invocation: false
```

Do not add a permissive replacement; absence of the denial matches existing model-invokable skills such as `activity-logger`.

- [ ] **Step 3: Confirm `activity-logger` remains byte-for-byte untouched**

Run:

```bash
git diff -- activity-logger/SKILL.md activity-logger/agents/openai.yaml
```

Expected: no output. If either file appears in the diff, revert that unrelated change before continuing.

## Task 3: Update the catalog and router behavior contract

**Files:**
- Modify: `skills-catalog.json:40,46`
- Modify: `skill-router/SKILL.md:body sections covering automatic invocation, Mode 1, and manual checkpoints`

- [ ] **Step 1: Change only the two catalog invocation intents**

Update the entries to this shape, preserving every other field and value:

```json
{"id":"skill-router","category":"tools-meta","lifecycle":"promoted","invocation_intent":"model","surfaces":{"routable":false,"listed_in_readme":true,"sync":true}},
{"id":"work-log-analyzer","category":"productivity-tracking","lifecycle":"personal","invocation_intent":"model","surfaces":{"routable":true,"listed_in_readme":false,"sync":true}}
```

Do not change `skill-router/skill-registry.yaml`; `skill-router` remains absent as a routing candidate by catalog policy even though it is model-invokable.

- [ ] **Step 2: Replace the router’s blanket prohibition with the approved boundary**

Update the existing router instructions that currently say the router must never auto-invoke skills. Use this contract instead:

```text
The router itself may be invoked by the agent when the task needs skill discovery or routing. Routing selects a skill or workflow; it does not grant permission to bypass the selected skill's invocation policy.

For a model-invokable downstream skill, continue through the existing routing flow. For a user-only downstream skill, stop at a manual checkpoint and wait for the user to explicitly invoke `$skill-name` or `/skill-name`. A reply such as「好」、「開始」or「繼續」does not count as explicit invocation.
```

Keep the existing Mode 2 and Mode 3 behavior that lists non-routable/deprecated entries and marks user-only steps as manual checkpoints.

- [ ] **Step 3: Update Mode 1 wording without changing routing selection rules**

In the Mode 1 instructions, explicitly state that `skill-router` is an internal routing helper that may be invoked by the agent, while `surfaces.routable: false` prevents it from being recommended as a result. Do not add a new mode, change the registry, or make the router self-recommendable.

- [ ] **Step 4: Run the focused regression tests**

Run:

```bash
python3 -m unittest tests.test_validate_skills_catalog
```

Expected: PASS, including the new target metadata and router contract tests, plus the existing tests that reject user-only skills without hard gates and reject a routable `skill-router`.

## Task 4: Run repository validation and inspect the diff

**Files:**
- Read-only validation of the modified files and generated catalog outputs.

- [ ] **Step 1: Run the catalog validator in check mode**

Run:

```bash
python3 scripts/validate_skills_catalog.py --check
```

Expected: exit code 0 with no catalog consistency errors. Do not use `--write` unless the check reports a generated-file mismatch; if it does, inspect the diff before allowing generated output to change.

- [ ] **Step 2: Verify the expected policy values directly**

Run:

```bash
python3 - <<'PY'
import json
from pathlib import Path

root = Path.cwd()
catalog = json.loads((root / "skills-catalog.json").read_text())
entries = {entry["id"]: entry for entry in catalog["skills"]}
assert entries["skill-router"]["invocation_intent"] == "model"
assert entries["work-log-analyzer"]["invocation_intent"] == "model"
assert entries["skill-router"]["surfaces"]["routable"] is False
assert entries["work-log-analyzer"]["surfaces"]["routable"] is True
for skill_id in ("skill-router", "work-log-analyzer"):
    assert "disable-model-invocation: true" not in (root / skill_id / "SKILL.md").read_text()
    assert "allow_implicit_invocation: false" not in (root / skill_id / "agents" / "openai.yaml").read_text()
print("invocation policy checks passed")
PY
```

Expected output: `invocation policy checks passed`.

- [ ] **Step 3: Check source/Codex parity for the changed skill definitions**

Run the repository’s existing parity/check procedure, or use this fallback when no dedicated command exists:

```bash
sha256sum \
  work-log-analyzer/SKILL.md \
  .codex/skills/work-log-analyzer/SKILL.md \
  skill-router/SKILL.md \
  .codex/skills/skill-router/SKILL.md
```

Expected: each source file’s hash matches its corresponding `.codex/skills` copy. If a copy is stale, perform only the targeted sync for these two skill directories; do not run wholesale sync.

- [ ] **Step 4: Inspect the final diff and status**

Run:

```bash
git diff --check
git diff -- \
  work-log-analyzer/SKILL.md \
  work-log-analyzer/agents/openai.yaml \
  skill-router/SKILL.md \
  skill-router/agents/openai.yaml \
  skills-catalog.json \
  tests/test_validate_skills_catalog.py

git status --short
```

Expected: only the approved skill metadata, catalog, router contract, and regression test changes appear, plus the intentionally untracked design/plan files if they have not been stashed. No activity-logger changes and no unrelated generated-file churn.

## Task 5: Run the required skill audit and report completion evidence

**Files:**
- Read-only audit of `work-log-analyzer` and `skill-router` after modification.

- [ ] **Step 1: Invoke `skill-auditor` for both changed skills**

Use the repository’s `skill-auditor` workflow against:

```text
work-log-analyzer
skill-router
```

Expected: no findings that the frontmatter, Codex metadata, catalog intent, or router manual-checkpoint contract contradict one another. If findings exist, fix the smallest relevant source file and rerun the full validation sequence.

- [ ] **Step 2: Re-run the final checks after any audit fix**

Run:

```bash
python3 scripts/validate_skills_catalog.py --check
python3 -m unittest tests/test_validate_skills_catalog.py
```

Expected: both commands pass.

- [ ] **Step 3: Apply the completion gate before claiming the work is done**

Use the repository `completion-gate` skill and report evidence for:

- validator passed;
- unit tests passed;
- skill audit passed;
- source/Codex parity checked;
- `activity-logger` remained unchanged;
- no commit or push was performed.

## Execution Boundary

Do not commit or push this change as part of this plan. If a commit is requested later, run the required native `code-review-claude` pass before asking for explicit commit approval; push requires a separate explicit approval.
