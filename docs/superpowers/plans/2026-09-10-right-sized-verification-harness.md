# Right-sized commit verification harness Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Make commit-boundary verification choose the minimum evidence required by change risk while preserving stronger checks for auth, session, permission, data, deployment, and regression work.

**Architecture:** Keep `completion-gate/SKILL.md` as the single source of truth for L0/L1/L2 profiles and escalation rules. Update the Codex and Claude runtime policy mirrors only with trigger and reviewer mapping; do not add a new dispatcher skill, hook, CLI, or catalog entry.

**Tech Stack:** Markdown policy files, Git, Python unittest, the existing skills catalog validator, and the existing `skill-auditor` checks.

**Spec:** `docs/superpowers/specs/2026-09-10-right-sized-verification-harness-design.md`

## Global Constraints

- L0 uses deterministic checks only and does not invoke a native reviewer.
- L1 uses affected-scope checks plus one runtime-native reviewer; it does not expand the full completion gate.
- L2 uses targeted checks, relevant regression/smoke checks, one runtime-native reviewer, and the full completion gate.
- Unknown risk or missing L1 evidence escalates one tier, never silently passes.
- Codex maps to `code-review-codex`; Claude Code and OMP map to `code-review-claude`.
- Preserve the two runtime-only policy lines currently present in `~/.claude/CLAUDE.md`.
- Do not commit until the user gives explicit approval after native review.

---

### Task 1: Carry the approved spec and add policy regression cases

**Files:**
- Create: `docs/superpowers/specs/2026-09-10-right-sized-verification-harness-design.md`
- Create: `tests/test_right_sized_verification_policy.py`

**Interfaces:**
- Consumes: the approved design at `docs/superpowers/specs/2026-09-10-right-sized-verification-harness-design.md`.
- Produces: deterministic regression cases that fail before the new tiered policy exists and pass after the policy and mirrors are updated.

- [ ] **Step 1: Copy the approved design into this worktree**

  Preserve the approved sections: goal, confirmed decisions, risk tiers, runtime ownership, commit-boundary flow, reporting contract, failure handling, policy validation cases, out-of-scope boundaries, and planned change surface.

- [ ] **Step 2: Write the failing policy tests**

  Add tests that read the repository policy files and assert the required observable contract:

  ```python
  REQUIRED_FILES = (
      ROOT / "completion-gate/SKILL.md",
      ROOT / "global/AGENTS.md",
      ROOT / "global/CLAUDE.md",
  )

  def test_completion_gate_defines_all_risk_tiers():
      text = (ROOT / "completion-gate/SKILL.md").read_text(encoding="utf-8")
      for marker in ("L0", "L1", "L2", "NOT VERIFIED", "ESCALATED"):
          assert marker in text

  def test_runtime_policies_route_review_by_tier():
      codex = (ROOT / "global/AGENTS.md").read_text(encoding="utf-8")
      claude = (ROOT / "global/CLAUDE.md").read_text(encoding="utf-8")
      assert "L0" in codex and "code-review-codex" in codex
      assert "L0" in claude and "code-review-claude" in claude
  ```

  Keep assertions about policy meaning rather than exact paragraph wording.

- [ ] **Step 3: Run the new tests to verify RED**

  Run: `python3 -m unittest tests.test_right_sized_verification_policy -v`

  Expected: FAIL because the current policy still requires an unconditional native reviewer and has no L0/L1/L2 matrix.

### Task 2: Implement the tiered policy in `completion-gate`

**Files:**
- Modify: `completion-gate/SKILL.md`
- Test: `tests/test_right_sized_verification_policy.py`

**Interfaces:**
- Consumes: the failing policy assertions from Task 1.
- Produces: one policy source defining risk classification, minimum evidence, escalation, and reporting.

- [ ] **Step 1: Add the risk classification section**

  Add the L2 hard escalators first, then the L0/L1 split:

  ```text
  if auth/session/permission, data-loss risk, production config/deploy/rollback,
  or known production incident/regression: L2
  elif only docs/format/comments/non-executable assets: L0
  else: L1
  ```

  State that uncertainty escalates one tier, capped at L2, and that diff size, file extension, or directory alone cannot decide risk.

- [ ] **Step 2: Define the minimum evidence for each tier**

  Keep L0 deterministic-only, L1 targeted checks plus one native reviewer, and L2 targeted plus regression/smoke checks, one native reviewer, and the full adversarial completion gate.

- [ ] **Step 3: Define escalation and reporting**

  Require escalation from L1 to L2 when relevant tests are unavailable or native review leaves unresolved uncertainty. Require `VERIFIED`, `NOT VERIFIED`, `RISK`, `REASON`, `CHECKS`, and `ESCALATED` in commit-boundary reports.

- [ ] **Step 4: Run the focused policy tests**

  Run: `python3 -m unittest tests.test_right_sized_verification_policy -v`

  Expected: PASS.

### Task 3: Update runtime policy mirrors without duplicating the matrix

**Files:**
- Modify: `global/AGENTS.md`
- Modify: `global/CLAUDE.md`
- Modify: `/Users/tom_wang/.codex/AGENTS.md`
- Modify: `/Users/tom_wang/.claude/CLAUDE.md`
- Test: `tests/test_right_sized_verification_policy.py`

**Interfaces:**
- Consumes: the tier matrix from `completion-gate/SKILL.md`.
- Produces: runtime-specific commit trigger and reviewer mapping.

- [ ] **Step 1: Replace unconditional pre-commit reviewer wording in the repository mirrors**

  Codex policy must say L0 skips native review, L1/L2 use `code-review-codex`, and Claude review is not auto-invoked from Codex. Claude policy must say L0 skips native review, L1/L2 use `code-review-claude`, and OMP uses the same mapping.

- [ ] **Step 2: Apply the same policy change to the actual runtime files**

  Update `~/.codex/AGENTS.md` and `~/.claude/CLAUDE.md` without overwriting runtime-only content. Keep the two Claude-only rules that are absent from `global/CLAUDE.md`.

- [ ] **Step 3: Keep completion-gate trigger timing unchanged**

  Preserve the existing rule that completion claims and commit transitions invoke `completion-gate`; only the depth of evidence changes by tier.

- [ ] **Step 4: Verify mirror policy and focused tests**

  Run: `python3 -m unittest tests.test_right_sized_verification_policy -v`

  Run: `diff -u global/AGENTS.md /Users/tom_wang/.codex/AGENTS.md` and confirm no unexpected differences.

  Run: `diff -u global/CLAUDE.md /Users/tom_wang/.claude/CLAUDE.md` and confirm only the known runtime-only rules differ.

### Task 4: Run repository and skill-quality verification

**Files:**
- Test: `tests/test_right_sized_verification_policy.py`
- Test: existing repository test suite and catalog validator

**Interfaces:**
- Consumes: all policy changes from Tasks 1–3.
- Produces: evidence that the catalog, policy tests, and modified skill remain valid.

- [ ] **Step 1: Run all repository tests**

  Run: `python3 -m unittest discover -s tests -p 'test_*.py' -v`

  Expected: PASS with zero failures.

- [ ] **Step 2: Validate catalog and generated surfaces**

  Run: `python3 scripts/validate_skills_catalog.py --check`

  Expected: exit 0 with no catalog drift.

- [ ] **Step 3: Audit the modified skill**

  Run the existing `skill-auditor` workflow against `completion-gate/SKILL.md`. Review the report for portability, ambiguity, duplicated policy, and missing escalation behavior.

- [ ] **Step 4: Run policy scenario dry runs**

  Verify expected outcomes for: typo → L0; Markdown link → L0; ordinary bug fix/API behavior → L1; login/session/permission → L2; missing L1 test → L2; unresolved review → L2; unknown risk → next higher tier.

### Task 5: Review, commit, and prepare PR

**Files:**
- Review: complete branch diff
- Test: staged secret scan and completion-gate evidence

**Interfaces:**
- Consumes: verified branch changes and policy test output.
- Produces: user-approved commit and a PR containing the design, policy, mirror, and regression changes.

- [ ] **Step 1: Inspect the complete diff and run staged secret scanning**

  Run: `git diff --check`.

  Run: `bash secure-ai-development-gate/scripts/scan-staged-secrets.sh` after staging only the intended repository files. Treat fallback-scan warnings as `NEEDS_REVIEW` unless confirmed to be documentation examples.

- [ ] **Step 2: Run Codex native review before asking for commit approval**

  Use `code-review-codex` on the complete branch diff. Fix any blocking findings and rerun the relevant tests.

- [ ] **Step 3: Run completion-gate before any completion claim**

  Report fresh evidence, assumptions, and `NOT VERIFIED` items. Do not claim the branch is complete until the evidence is present.

- [ ] **Step 4: Ask the user for explicit commit approval**

  Do not commit before approval, even though the user requested a PR.

- [ ] **Step 5: Commit with a Conventional Commit message**

  Suggested message: `feat(verification): add right-sized commit gates`

- [ ] **Step 6: Create the PR after the commit exists**

  Use the configured GitHub CLI or PR mechanism. Include the risk-tier summary, verification commands, known mirror difference, and any `NOT VERIFIED` items.
