# Skills Catalog Governance Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox syntax for tracking.

**Goal:** Establish a validated skills catalog and generated index for the cross-agent skills source repository, without changing runtime invocation behaviour or synchronising to target agent directories.

**Architecture:** skills-catalog.json owns governance metadata. scripts/validate_skills_catalog.py discovers tracked top-level skills through Git, validates repository surfaces, and renders SKILLS_CATALOG.md only when explicitly asked. skill-router keeps trigger and workflow ownership. skill-sync gains a genuinely read-only preview mode.

**Tech Stack:** Python 3 standard library (argparse, json, pathlib, subprocess, unittest), Bash, Git, rsync.

---

## File structure

| Path | Responsibility |
|---|---|
| skills-catalog.json | Approved governance metadata for every tracked top-level local skill. |
| scripts/validate_skills_catalog.py | Catalog validation and deterministic index rendering. |
| tests/test_validate_skills_catalog.py | Standard-library regression tests. |
| SKILLS_CATALOG.md | Generated complete inventory; never hand edit. |
| README.md and README.zh.md | Landing pages with Core Skills links and catalog link. |
| SKILLS_ROADMAP.md | Planning/history document; not an inventory. |
| skill-router/skill-registry.yaml | Router triggers and workflows, reconciled to routable flags. |
| skill-sync/scripts/sync.sh | Existing interactive sync plus read-only --dry-run. |
| skill-sync/scripts/test-sync.sh | Temporary-fixture regression test for --dry-run. |

## Task 1: Approve classifications before writing the catalog

**Files:**
- Read: tracked top-level SKILL.md files, both root READMEs, router registry, .skill-sync-ignore.
- Create later: skills-catalog.json.

- [ ] **Step 1: Enumerate scope from Git, not the filesystem.**

Run:

~~~bash
git ls-files -- '*/SKILL.md' | awk -F/ 'NF == 2 { print $1 }' | sort
~~~

Expected: only tracked first-level skill directories. Exclude untracked team-onboarding, ONBOARDING.md, global, docs, and skills-query-server.

- [ ] **Step 2: Produce the read-only classification table.**

For every id, propose:
id | category | lifecycle | invocation_intent | routable | listed_in_readme | sync

Apply approved definitions. Invocation intent is informational; it does not authorise a frontmatter or runtime change.

- [ ] **Step 3: Get user approval and stop.**

Do not create skills-catalog.json until the full table is approved.

## Task 2: Add failing catalog validator tests

**Files:**
- Create: tests/test_validate_skills_catalog.py
- Create later: scripts/validate_skills_catalog.py

- [ ] **Step 1: Build temporary Git fixtures.**

Use tempfile.TemporaryDirectory and initialise a repository. Add tracked alpha/SKILL.md and beta/SKILL.md, then create untracked/SKILL.md and nested/example/SKILL.md after git add. Tests must prove discovery sees alpha and beta only.

- [ ] **Step 2: Cover schema and identity failures.**

Add unittest cases with these names:
- test_discovery_includes_only_tracked_top_level_skill_directories
- test_validation_rejects_catalog_skill_missing_from_git_inventory
- test_validation_rejects_duplicate_catalog_id
- test_validation_rejects_unknown_category_or_lifecycle

- [ ] **Step 3: Cover surface contracts and rendering.**

Add tests for:
- a routable id missing from router categories;
- a false-routable id still present there;
- a listed-in-readme id outside Core Skills markers;
- sync false without an exact top-level ignore;
- stale SKILLS_CATALOG.md rejected by --check and repaired by --write.

The router fixture includes superpowers:writing-plans and asserts it needs no catalog row.

- [ ] **Step 4: Confirm the red state.**

Run:

~~~bash
python3 -m unittest discover -s tests -p 'test_*.py' -v
~~~

Expected: a missing-module or missing-implementation failure. Do not add a fake implementation.

## Task 3: Implement validator and renderer

**Files:**
- Create: scripts/validate_skills_catalog.py
- Modify: tests/test_validate_skills_catalog.py

- [ ] **Step 1: Implement loading and tracked-skill discovery.**

Define these closed enums:

~~~python
VALID_CATEGORIES = frozenset({
    "quality-gates", "research-critical-thinking", "multi-agent-roles",
    "design-planning", "content-generation", "productivity-tracking",
    "tools-meta",
})
VALID_LIFECYCLES = frozenset({"promoted", "experimental", "personal"})
VALID_INVOCATION_INTENTS = frozenset({"model", "user"})
~~~

Call git ls-files -- '*/SKILL.md', then retain only paths with exactly two path components.

- [ ] **Step 2: Implement catalog and surface validation.**

Validate required fields, boolean surfaces, unique ids, and exact catalog-to-Git identity equality. Parse router ids only before the top-level workflows: line with:

~~~python
ROUTER_ID = re.compile(r"^\s*-\s+id:\s+([^\s#]+)")
~~~

Ignore router ids containing colon. Parse explicit Core Skills markers:

~~~markdown
<!-- core-skills:start -->
<!-- core-skills:end -->
~~~

For sync contracts, only an ignore line exactly equal to id or id/ counts. Broad ignore patterns remain outside catalog policy.

- [ ] **Step 3: Implement deterministic rendering.**

Render category/id-sorted rows without timestamps:

~~~markdown
# Skills Catalog

> Generated from skills-catalog.json. Do not edit by hand; run python3 scripts/validate_skills_catalog.py --write.

| Skill | Category | Lifecycle | Invocation intent | Router | README | Sync |
|---|---|---|---|---|---|---|
| [brainstorming](./brainstorming/SKILL.md) | design-planning | promoted | model | yes | yes | yes |
~~~

--check compares exact expected output; --write is the only mode that writes SKILLS_CATALOG.md.

- [ ] **Step 4: Confirm the green state.**

Run:

~~~bash
python3 -m unittest discover -s tests -p 'test_*.py' -v
~~~

Expected: all validator tests pass.

## Task 4: Add a true read-only skill-sync preview

**Files:**
- Modify: skill-sync/scripts/sync.sh
- Create: skill-sync/scripts/test-sync.sh
- Modify: skill-sync/SKILL.md

- [ ] **Step 1: Add a failing temporary-fixture shell test.**

Copy sync.sh into a temporary fixture root. Configure one existing and one missing target through .skill-sync-targets. Run --dry-run and assert:

~~~bash
test -d "$existing_target"
test ! -e "$missing_target"
grep -F "skipped" "$output_file"
! grep -F "Proceed with sync?" "$output_file"
~~~

Also run --dry-run --no-delete and assert additive mode appears. Trap fixture cleanup.

- [ ] **Step 2: Confirm it fails against current behaviour.**

Run:

~~~bash
bash skill-sync/scripts/test-sync.sh
~~~

Expected: failure because --dry-run is unrecognised and normal flow creates missing targets before preview.

- [ ] **Step 3: Implement --dry-run before target creation.**

Add a dry_run=false flag. Parse --dry-run with --no-delete. Before the existing mkdir loop, handle true with only rsync --dry-run calls against existing targets; print a skipped message for missing targets; never prompt or run a real rsync. Keep default and --no-delete flows unchanged. Update help text.

- [ ] **Step 4: Document and re-run.**

Document safe preview versus interactive mirror in skill-sync/SKILL.md. Then run:

~~~bash
bash skill-sync/scripts/test-sync.sh
~~~

Expected: pass without creating missing fixture targets or waiting for stdin.

## Task 5: Apply approved metadata and reconcile documentation

**Files:**
- Create: skills-catalog.json
- Create via renderer: SKILLS_CATALOG.md
- Modify: skill-router/skill-registry.yaml, .skill-sync-ignore, README.md, README.zh.md, SKILLS_ROADMAP.md

- [ ] **Step 1: Write the approved catalog exactly.**

Add one row per approved id. Do not add/remove disable-model-invocation, agents/openai.yaml, or any runtime configuration.

- [ ] **Step 2: Reconcile router and sync surfaces.**

Every approved routable true local id has exactly one router category entry. Remove local entries approved as routable false. Keep external superpowers entries and workflows. Add exact id/ ignores only for sync false rows; remove matching ignores for sync true rows; preserve infrastructure ignores.

- [ ] **Step 3: Replace hand-maintained README inventories without removing MCP setup.**

In both root READMEs, replace the inventory block from Skills Overview / Skills 總覽 through the heading immediately before MCP Server / MCP Server, then replace the separate Tools & Meta-skills / 工具與元技能 table. Retain the MCP Server description and its Quick setup / 快速設定 commands unchanged. Insert this replacement before the retained MCP section:

~~~markdown
## Skills

The complete generated inventory is in [SKILLS_CATALOG.md](./SKILLS_CATALOG.md).

### Core Skills

<!-- core-skills:start -->
<!-- core-skills:end -->
~~~

Populate the marker region only with approved listed_in_readme links. Localise surrounding prose but not ids or paths.

- [ ] **Step 4: Demote roadmap totals.**

Replace the current Total Implemented and By Category block with a note pointing to SKILLS_CATALOG.md. Retain the legend and historical planning entries.

- [ ] **Step 5: Generate and validate.**

Run:

~~~bash
python3 scripts/validate_skills_catalog.py --write
python3 scripts/validate_skills_catalog.py --check
python3 -m unittest discover -s tests -p 'test_*.py' -v
bash skill-sync/scripts/test-sync.sh
bash skill-sync/scripts/sync.sh --dry-run --no-delete
~~~

Expected: all commands exit 0; the last command neither prompts nor creates target directories.

## Task 6: Audit, review, and ask before committing

**Files:**
- Review: all changes

- [ ] **Step 1: Audit modified skills.**

Run:

~~~bash
bash skill-auditor/scripts/audit_skill.sh skill-router -o /tmp/skill-router-audit.md
bash skill-auditor/scripts/audit_skill.sh skill-sync -o /tmp/skill-sync-audit.md
~~~

Expected: no critical finding.

- [ ] **Step 2: Run final checks.**

Run:

~~~bash
git diff --check
python3 scripts/validate_skills_catalog.py --check
python3 -m unittest discover -s tests -p 'test_*.py' -v
bash skill-sync/scripts/test-sync.sh
git status --short
~~~

Expected: no whitespace errors, all checks pass, and status contains only intentional worktree changes.

- [ ] **Step 3: Dispatch required pre-commit review.**

Use an isolated code-review-codex subagent against main...HEAD and the working-tree diff. It must inspect catalog semantics, generated-output determinism, read-only dry-run guarantees, and scope compliance. Resolve confirmed High or Medium findings and re-run Step 2.

- [ ] **Step 4: Ask for explicit commit approval.**

Do not commit automatically. Report evidence, residual risks, and the exact Conventional Commit message, then request user approval.

## Plan self-review

- Tasks 1–5 cover classification approval, catalog identity, validation, generated index, README and roadmap boundaries, router ownership, sync safety, and all approved non-goals.
- The plan uses JSON and Python standard library only; router trigger prose stays in YAML.
- Only skill-sync --dry-run may target real agent directories, and it is required to be non-mutating.
