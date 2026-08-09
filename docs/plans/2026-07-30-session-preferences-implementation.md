# Session Preferences Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use `superpowers:subagent-driven-development` (recommended) or `superpowers:executing-plans` to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Create a shareable, user-only `session-preferences` skill that manually enables modular interaction rules for the current session and supports confirmed rule maintenance.

**Architecture:** Keep `SKILL.md` as a thin control surface and place active policy text in indexed Markdown modules under `references/`. Register the new skill in the catalog and router as discoverable but user-only; do not change global policy or synchronize it to any runtime.

**Tech Stack:** Markdown skill instructions, YAML user-only metadata, JSON skills catalog, YAML router registry, Python stdlib catalog validator, Bash skill auditor.

## Global Constraints

- `session-preferences` is a user-only skill: Claude frontmatter must set `disable-model-invocation: true`, and Codex metadata must set `policy.allow_implicit_invocation: false`.
- It begins only after explicit `$session-preferences` or `/session-preferences`; broad language such as “continue” never enables it.
- Once explicitly enabled, its rules apply from that turn through the current session only. This is a conversational instruction, not a hard runtime state or cross-session guarantee.
- The first modules are `control-return` and generic `deai-voice`. Do not copy `deai-voice-rewrite`'s external-draft workflow, Tom-specific profile, examples, or fact-freeze/flagging output contract.
- `add-rule` and `add-deai` never write a rule before the user sees and confirms the normalized rule and target module. A confirmed addition applies immediately to the remaining current session and is persisted for future activations.
- Do not alter `global/CLAUDE.md`, `global/AGENTS.md`, live host policies, or run `skill-sync`.
- Run `skill-auditor` after creating or modifying this skill. Before proposing any commit, run `code-review-codex`, report its result, then obtain explicit user approval to commit.

---

### Task 1: Create the policy skill, modules, and user manual

**Files:**
- Create: `session-preferences/SKILL.md`
- Create: `session-preferences/agents/openai.yaml`
- Create: `session-preferences/references/INDEX.md`
- Create: `session-preferences/references/control-return.md`
- Create: `session-preferences/references/deai-voice.md`
- Create: `session-preferences/README.md`

**Interfaces:**
- Consumes: explicit user invocations beginning with `$session-preferences` or `/session-preferences`.
- Produces: an in-context, current-session policy activation; a one-line activation acknowledgement; and, for maintenance requests, a proposed normalized rule plus target file awaiting confirmation.
- Persists: only confirmed rules in the reference module and `references/INDEX.md`.

- [ ] **Step 1: Create the strict user-only entry point.**

  Write this frontmatter at the beginning of `session-preferences/SKILL.md`:

  ```yaml
  ---
  name: session-preferences
  description: >-
    User-controlled session interaction preferences. Explicitly enable a
    modular policy bundle for the current session, or propose and confirm a
    new rule. Never enable automatically.
  disable-model-invocation: true
  ---
  ```

  Add an `Activation` section that requires the agent to read `references/INDEX.md` and every listed module, then reply exactly once in concise Traditional Chinese that the rules are enabled for the current session. State that the rules start now, end with the session, and do not apply retroactively or across a new session.

- [ ] **Step 2: Specify reference loading and control-return behavior.**

  In `SKILL.md`, define `references/INDEX.md` as the only active-module list. Require a conflict to be shown to the user rather than silently resolved. In `control-return.md`, require a three-option next-step block only when all three options are concrete, useful, and within the user's scope. Mark one option as recommended with a one-sentence reason. Omit the block when it would be manufactured, repetitive, or unsuitable for a simple answer or clarification.

- [ ] **Step 3: Add a shareable, general de-AI voice module.**

  Write `deai-voice.md` as conversational guidance, not a rewrite procedure. Include only portable rules: use direct, concise language; avoid inflated claims and stock conclusions; avoid repetitive symmetrical constructions; prefer the reader's locale-appropriate terminology; preserve literal identifiers and code; do not over-explain familiar technical terms; and state uncertainty plainly. Explicitly exclude Tom-specific catchphrases, external-draft fact-freeze checklists, reference examples, and personal voice imitation.

- [ ] **Step 4: Define safe rule maintenance.**

  In `SKILL.md`, document these accepted forms:

  ```text
  $session-preferences add-deai <observation or proposed rule>
  $session-preferences add-rule <observation or proposed rule>
  $session-preferences add-rule <category>: <observation or proposed rule>
  ```

  Make `add-deai` target `deai-voice`. For `add-rule` without a category, require the agent to propose a destination module. For a new category, propose the kebab-case module name and the required `INDEX.md` row. Before any edit, display the normalized rule, target module, scope, and whether it takes effect immediately. Only after user confirmation may the agent edit the module and index; it must then state that the rule is active for the rest of the current session.

- [ ] **Step 5: Add the active-module index and README.**

  Give `INDEX.md` a compact table with columns `Module`, `File`, and `Purpose`, with exactly these initial rows:

  ```markdown
  | Module | File | Purpose |
  | --- | --- | --- |
  | control-return | control-return.md | Give three useful next steps only when appropriate. |
  | deai-voice | deai-voice.md | Keep ordinary conversation direct and natural. |
  ```

  Write `README.md` in Traditional Chinese. Include a quick start, the three update forms, confirmation-before-write behavior, immediate current-session effect after confirmation, the new-session reactivation requirement, reference layout, and the explicit statement that runtime synchronization is separate and never automatic.

- [ ] **Step 6: Add Codex gate metadata and perform first content checks.**

  Create `session-preferences/agents/openai.yaml` with:

  ```yaml
  policy:
    allow_implicit_invocation: false
  ```

  Run:

  ```bash
  rg -n 'disable-model-invocation: true|allow_implicit_invocation: false' \
    session-preferences/SKILL.md session-preferences/agents/openai.yaml
  for file in $(find session-preferences -type f -print); do
    git diff --no-index --check /dev/null "$file"
  done
  ```

  Expected: both gate lines appear and every new file passes the whitespace
  check before it is added to Git's index.

### Task 2: Register the skill for discovery without making it auto-routable

**Files:**
- Modify: `skills-catalog.json`
- Modify: `skill-router/skill-registry.yaml`
- Modify: `SKILLS_CATALOG.md` (generated by the validator)

**Interfaces:**
- Consumes: the new top-level `session-preferences/SKILL.md` and its two user-only metadata gates.
- Produces: a `tools-meta` / `experimental` catalog entry that router discovery may recommend only as an explicit `$session-preferences` checkpoint.

- [ ] **Step 1: Add the catalog entry.**

  Insert a lexicographically ordered entry in `skills-catalog.json`:

  ```json
  {
    "id": "session-preferences",
    "category": "tools-meta",
    "lifecycle": "experimental",
    "invocation_intent": "user",
    "surfaces": {
      "routable": true,
      "listed_in_readme": false,
      "sync": true
    }
  }
  ```

  Preserve the repository's compact JSON style and ordering.

- [ ] **Step 2: Add narrow router triggers.**

  Add `session-preferences` under the `meta` category in
  `skill-router/skill-registry.yaml`. Use narrowly scoped discovery triggers:

  ```yaml
  - id: session-preferences
    triggers:
      - "session preferences"
      - "response preferences"
      - "回應規則"
      - "session 規則"
      - "互動偏好"
  ```

  Do not add generic triggers such as `寫作`, `語氣`, `下一步`, or `continue`; these would create false-positive routing. The existing router's user-intent gate must render this match as a manual `$session-preferences` checkpoint.

- [ ] **Step 3: Make the new files visible to the Git-index-based validator.**

  Before validation, use `git add -N` only for the newly created
  `session-preferences/**` files. The validator discovers top-level skills
  through `git ls-files`, so it cannot validate an entirely untracked skill.
  Do not stage unrelated existing changes.

  ```bash
  git add -N session-preferences
  python3 scripts/validate_skills_catalog.py --write
  python3 scripts/validate_skills_catalog.py --check
  ```

  Expected: `--write` updates `SKILLS_CATALOG.md`; the following `--check`
  exits 0 and reports no stale generated index or user-only metadata failure.

- [ ] **Step 4: Run catalog regression tests.**

  Run:

  ```bash
  python3 -m unittest tests/test_validate_skills_catalog.py
  ```

  Expected: the complete validator regression suite passes. If it fails,
  correct the catalog/registry/metadata mismatch rather than weakening the
  validator.

### Task 3: Audit the shareable artifact and preserve the runtime boundary

**Files:**
- Verify: `session-preferences/**`
- Verify: `skills-catalog.json`
- Verify: `skill-router/skill-registry.yaml`
- Verify: `SKILLS_CATALOG.md`

**Interfaces:**
- Consumes: the completed source-tree skill and catalog integration.
- Produces: offline evidence that the source artifact is structurally sound;
  no claim about a fresh Claude or Codex runtime.

- [ ] **Step 1: Run the required skill audit.**

  Run:

  ```bash
  bash skill-auditor/scripts/audit_skill.sh session-preferences
  ```

  Review every finding. Fix critical findings before moving on; for advisory
  findings, either fix them or document why the pure-instruction skill does
  not need the suggested surface.

- [ ] **Step 2: Verify the actual discovery and content contracts.**

  Run:

  ```bash
  python3 scripts/validate_skills_catalog.py --check
  rg -n -C 2 'session-preferences|invocation_intent|routable' \
    skills-catalog.json skill-router/skill-registry.yaml SKILLS_CATALOG.md
  rg -n -C 2 'add-deai|add-rule|confirm|current session|立即' \
    session-preferences/SKILL.md session-preferences/README.md
  git diff --check
  ```

  Expected: the catalog declares `user` and `routable: true`, router contains
  only the narrow triggers, documented update commands require confirmation,
  and all static checks pass.

- [ ] **Step 3: Report the deliberate verification limit.**

  Report the offline results separately from runtime behavior. State that no
  `skill-sync`, live host write, or fresh Claude/Codex smoke was run. Offer a
  fresh-runtime manual-invocation smoke only if the user separately authorizes
  an additive synchronization target and the single test scope.

- [ ] **Step 4: Apply the pre-commit gates only when the user asks to commit.**

  Before proposing a commit, invoke `code-review-codex` on the final diff,
  address any accepted findings, and re-run the Task 3 checks. Then show the
  proposed Conventional Commit message:

  ```text
  feat(skills): add session preferences policy bundle
  ```

  Ask for explicit commit approval. Do not commit, push, or synchronize unless
  the user separately authorizes each action.

## Spec Coverage Review

- Manual-only invocation and session scope: Task 1, Steps 1-2.
- Three real next steps and recommendation rule: Task 1, Step 2.
- Generic, shareable de-AI rules: Task 1, Step 3.
- Confirmed, immediately effective `add-deai` and optional-category
  `add-rule`: Task 1, Step 4.
- Modular references and user manual: Task 1, Step 5.
- User-only runtime gates: Task 1, Step 6 and Task 2, Step 3.
- Discoverable manual router checkpoint and experimental catalog placement:
  Task 2.
- Required auditing, catalog validation, no-sync boundary, and commit gate:
  Task 3.
