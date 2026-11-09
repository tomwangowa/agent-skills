# Package Unpackaged Skills — Design

- Date: 2026-11-08
- Branch: `feat/plugins-add-unpackaged-skills` (base `a5a0c59`)
- Status: approved; revised 2026-11-08 after final review (owner decisions below)

## Goal

Add the remaining tracked skills that fit the plugins' audience into the
existing seven plugin packages, in one PR. The primary audience is the
owner's TrendLife colleagues; the repository and marketplace stay public, so
anyone can install and read what ships.

## Decisions

### Packaged (8 skills, 4 packages)

| Package | Version | Added skills |
|---|---|---|
| quality-gates | 0.1.1 → 0.2.0 | review-convergence-gate |
| work-journal | 0.1.2 → 0.2.0 | report-generator |
| content-tools | 0.1.1 → 0.2.0 | newsletter-digest, qa-to-notes, arxiv-digest |
| repo-workflow | 0.2.1 → 0.3.0 | understand-file, understand-function, understand-repo |

Minor bumps follow `RELEASE_NOTES.md`: a new skill is a backward-compatible
capability expansion. The other three packages get a patch bump because their
generated content changes too: skill-toolbox 0.1.2 → 0.1.3 (skill-router's
`package-index.json` lists the new members), technical-decisions
0.1.2 → 0.1.3 and session-preferences 0.1.3 → 0.1.4 (shipped acceptance
wording, see Changes §3).

Release tags: `quality-gates-v0.2.0`, `work-journal-v0.2.0`,
`content-tools-v0.2.0`, `repo-workflow-v0.3.0`, `skill-toolbox-v0.1.3`,
`technical-decisions-v0.1.3`, `session-preferences-v0.1.4`.

TrendLife-specific content is accepted because the audience is TrendLife
colleagues: `qa-to-notes` (Teams publish mode) and `arxiv-digest` (relevance
keywords) carry no internal data, and `narrative-auditor` already shipped the
same context.

### Not packaged

| Skill | Reason |
|---|---|
| ai-weekly-insight | Ships `trendlife-context.yaml` (internal project status and cost figures from Confluence); waits for the owner's decision on whether that file may be public |
| deai-voice-rewrite | One person's writing voice; reads a Claude-only output style |
| git-status-tui | Owner's choice |
| lesson | Not plugin-safe yet (see below) |
| code-review-gemini | Retired; `catalog.py` rejects deprecated skills |

`lesson` stores `config.json` in its own skill directory
(`lesson/scripts/lesson.py:17-18`) and `/lesson setup` writes the script's
absolute path into agent instruction files (`lesson.py:478`). Under a plugin
install both point into a versioned cache directory, so the config is lost
and the session-start command breaks on every upgrade. Making it plugin-safe
(config outside the cache, path-independent session entry) is a separate
design task.

## Changes

### 1. Skill content: portable script paths

Plugin installs do not live under `~/.claude/skills/`. Replace hardcoded
paths with the convention already used by `work-log-analyzer`
(`<skill_base_directory>` = the base directory shown when the skill loads):

- `newsletter-digest/SKILL.md:64` and `:176` →
  `<skill_base_directory>/scripts/parse_emls.py`
- `report-generator/SKILL.md:69-70` →
  `<skill_base_directory>/../activity-logger/scripts/init_activities.sh` and
  `<skill_base_directory>/../work-log-analyzer/scripts/aggregate_activities.sh`

The sibling path works in all three layouts checked: the Claude plugin
(`plugins/claude/work-journal/skills/`), the Codex plugin
(`plugins/codex/work-journal/skills/`), and a flat `~/.claude/skills/`
checkout. `report-generator` must therefore ship in the same package as
`activity-logger` and `work-log-analyzer` (work-journal), which already ships
both scripts.

### 2. `plugin-packages.json`

- Add the skills above to their packages and set the seven versions above.
- Add `runtime_resources` (only whitelisted files ship):
  - work-journal: `report-generator/agents/openai.yaml`
  - content-tools: `newsletter-digest/agents/openai.yaml`,
    `newsletter-digest/scripts/parse_emls.py`, `qa-to-notes/agents/openai.yaml`,
    `arxiv-digest/agents/openai.yaml`, `arxiv-digest/references/deep-reading-handoff.md`
  - repo-workflow: `understand-file/agents/openai.yaml`,
    `understand-function/agents/openai.yaml`, `understand-repo/agents/openai.yaml`
  - quality-gates: none (`review-convergence-gate` has only `SKILL.md`)
- content-tools `requirements.commands`: add `python3` (`parse_emls.py`
  uses only the standard library).
- content-tools dependency on `report-generator`: change provider from
  `external` to `work-journal` (still `optional`). `catalog.py` then checks
  that work-journal actually offers the skill.
- content-tools: add an `optional` dependency on `technical-decisions:deep-reading`
  (arxiv-digest hands deep reads to it).
- work-journal dependency on `lesson` stays `external`.

### 3. Member count and re-acceptance wording

`scripts/plugin_packaging/catalog.py:102-103` and
`tests/test_plugin_packages.py:42` require exactly 40 source skills. Change to
48, and update the "40" wording in `README.md:21`, `README.zh.md:21` and
`docs/plugins/README.md:15`.

The shipped text (`docs/plugins/installation.md`, copied into all seven
packages, and the plugin README sentence in `scripts/plugin_packaging/render.py`)
listed which packages need native re-acceptance. Listing packages there means
any package change rewrites all seven. Replace it with a generic sentence that
points to `acceptance.json`. Unshipped docs (`README.md`, `README.zh.md`,
`docs/plugins/README.md`, `docs/validation/skill-plugins/README.md`) state that
all seven bindings are stale.

### 4. Generated output and evidence

- Run `npm audit` for the work-journal server before its bump and refresh
  `docs/validation/skill-plugins/production-audit.json` (project rule).
- Run `python3 scripts/build_plugins.py --write`; commit generated output
  together with `plugin-packages.json`. Never hand-edit `plugins/claude|codex/`.

## Verification

- `python3 scripts/build_plugins.py --write`, then
  `python3 scripts/build_plugins.py --check` reports no drift.
- `claude plugin validate --strict` passes for all seven packages and the marketplace.
- `validate_skills_catalog.py --check`, `check_plugin_release.py` and the full
  `unittest` suite pass.
- From the generated Claude and Codex work-journal directories, resolve and
  run `report-generator`'s sibling script paths once (`init_activities.sh
  list` against a temporary data directory), not just inspect the tree.
- Run `parse_emls.py --help` from the generated content-tools directory, and
  confirm `arxiv-digest/references/deep-reading-handoff.md` ships on both surfaces.
- Baseline: run the same test suite on the clean branch first; report any
  pre-existing failure separately.

## Out of scope

- Making `lesson` plugin-safe.
- `ai-weekly-insight/trendlife-context.yaml` being present in the public
  repository history (reported to the owner as a separate decision).
- Native install acceptance on both CLIs (the README already records that
  changed packages need re-acceptance before release).
- Declaring the remaining cross-package skill references as optional
  dependencies (understand-* → sepia, report-generator →
  interactive-presentation-generator and code-story-teller, qa-to-notes →
  narrative-auditor); each degrades gracefully when the other skill is absent.
- Syncing `production`; reminded after merge.
