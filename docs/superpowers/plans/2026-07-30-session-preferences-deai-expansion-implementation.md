# Session Preferences De-AI Expansion Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use `superpowers:subagent-driven-development` (recommended) or `superpowers:executing-plans` to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Expand the user-invoked `session-preferences` de-AI policy into a
layered, shareable Traditional Chinese writing policy without changing its
manual activation or user-only runtime gates.

**Architecture:** Keep `deai-voice.md` as the small always-loaded policy.
Make it route explicitly to three original deferred references for long-form
prose, translation, and Taiwan Traditional Chinese. Keep deferred files out
of `INDEX.md`, so their content is loaded only for the matching output.

**Tech Stack:** Markdown skill instructions; existing `skill-auditor` Bash
script; existing Python catalog validator; Git static checks.

---

## Guardrails

- Do not copy, translate, paraphrase closely, or import examples/tables from
  `allenloves/de-ai-tone`; retain only independently expressed policy ideas.
- Do not import Tom-specific voice, the external-draft rewrite workflow, fact
  freeze checking, or flag-don't-fix behavior from `deai-voice-rewrite`.
- Preserve `disable-model-invocation: true`,
  `policy.allow_implicit_invocation: false`, the `$session-preferences`
  command, and the existing confirmation-before-write rule.
- Do not change the catalog, router, global policies, sync configuration, or
  live host files.
- Preserve unrelated untracked files under `docs/superpowers/{plans,specs}`.
- Do not commit, push, synchronize, or run a fresh runtime smoke without the
  user's separate, explicit approval.

### Task 1: Define the always-loaded de-AI contract

**Files:**
- Modify: `session-preferences/SKILL.md`
- Modify: `session-preferences/references/deai-voice.md`
- Modify: `session-preferences/references/INDEX.md`

- [ ] **Step 1: Preserve activation and add deferred-reference behavior.**

  In `SKILL.md`, retain the existing activation requirement to read
  `references/INDEX.md` and every module listed there. Immediately after it,
  add a rule that an active module may direct conditional reading of a
  reference that is intentionally absent from `INDEX.md`. Require the agent to
  read the named file before producing the matching kind of content, and to
  name a missing deferred file instead of claiming its rules were applied.

  Expected invariant: `INDEX.md` remains the complete list of *always-loaded*
  modules, not the list of every supporting reference.

- [ ] **Step 2: Route `add-deai` to the correct reference.**

  Replace the sentence that makes `add-deai` always target `deai-voice` with
  this behavior: normalize the rule, propose exactly one destination among
  `deai-voice`, `deai-longform`, `deai-translation`, and `taiwan-zh`, explain
  its scope, and wait for explicit confirmation. Keep the existing behavior
  for generic `add-rule` requests and new non-de-AI modules.

  Add this destination guide to `SKILL.md`:

  ```markdown
  - `deai-voice`: every new Traditional Chinese reply and reference-loading
    decisions.
  - `deai-longform`: requested drafts or prose longer than two paragraphs.
  - `deai-translation`: source-to-target translation behavior.
  - `taiwan-zh`: Taiwan terminology or Chinese punctuation judgment.
  ```

  After a confirmed addition, require a reread of the edited reference so the
  rule is active for the remaining current session.

- [ ] **Step 3: Replace the core reference with compact, universal rules.**

  Rewrite `deai-voice.md` around these sections:

  ```markdown
  # General conversational voice

  ## Priority
  1. Explicit user wording, voice, and format.
  2. Source fidelity, quotations, identifiers, fixed text, and required form.
  3. This policy.
  4. Default conversational preferences.

  ## Apply to every new Traditional Chinese reply
  - Lead with the answer; do not use enthusiastic acknowledgement as a
    substitute for content.
  - Let the final substantive sentence end the reply; do not append a generic
    promise, recap, or decorative emoji.
  - Remove labels that merely announce importance, certainty, or a summary.
  - Use a contrast or a parallel list only when each part carries information
    the other parts do not already provide.
  - Prefer concrete verbs and nouns to broad process or business labels.

  ## Read a deferred reference when needed
  | Situation | Read before replying |
  | --- | --- |
  | Draft or more than two prose paragraphs | `deai-longform.md` |
  | Translation | `deai-translation.md` |
  | Taiwan usage or punctuation needs judgment | `taiwan-zh.md` |
  ```

  Finish with explicit exclusions for code, literal quotations, identifiers,
  paths, fixed templates, and explicitly requested tables/lists. State that a
  requested locale, quoted source, or technical convention outranks the
  Taiwan-default wording preference.

- [ ] **Step 4: Keep the index compact.**

  Leave `INDEX.md` with only `control-return` and `deai-voice`. Update the
  `deai-voice` purpose text to say that it provides core conversational rules
  and routes longer or specialized output to deferred references. Do not add
  the three deferred files as active rows.

- [ ] **Step 5: Check the core contract before adding details.**

  Run:

  ```bash
  rg -n -C 2 'INDEX|deferred|add-deai|deai-longform|deai-translation|taiwan-zh' \
    session-preferences/SKILL.md \
    session-preferences/references/deai-voice.md \
    session-preferences/references/INDEX.md
  git diff --check -- session-preferences/SKILL.md \
    session-preferences/references/deai-voice.md \
    session-preferences/references/INDEX.md
  ```

  Expected: the entry point documents all four de-AI destinations, `INDEX.md`
  lists only two active modules, and Git reports no whitespace errors.

### Task 2: Add original deferred guidance

**Files:**
- Create: `session-preferences/references/deai-longform.md`
- Create: `session-preferences/references/deai-translation.md`
- Create: `session-preferences/references/taiwan-zh.md`

- [ ] **Step 1: Add long-form prose guidance.**

  Create `deai-longform.md` with a short preflight and silent final pass. The
  preflight must require: state the claim before decoration; keep an
  `X versus Y` construction only when X is a plausible reader assumption; and
  use a list only for genuinely parallel material. The final pass must check:
  repeated section endings, empty transition labels, overused dashes, chained
  parallelism, unnecessary quantity words, and long sentences whose logic
  cannot be followed in one reading.

  Do not impose word-count quotas. Require the agent to perform the pass
  silently unless the user asks to see it.

- [ ] **Step 2: Add translation-specific guidance.**

  Create `deai-translation.md` with this order of decisions:

  ```markdown
  1. Preserve terminology, technical meaning, evidence strength, and deliberate
     rhetoric in the source.
  2. Only then make the target Chinese natural: split overloaded modifier
     chains, avoid passive wording when Chinese does not need it, remove
     needless pronoun repetition, and use natural clause order.
  3. Do not erase a source's deliberate parallelism, contrast, or formal
     register merely because a de-AI rule would normally discourage it.
  ```

  Add a final reminder that uncertainty, ambiguity, or untranslatable wordplay
  must be flagged rather than invented away.

- [ ] **Step 3: Add Taiwan Traditional Chinese guidance.**

  Create `taiwan-zh.md` with four compact sections:

  1. Default to Taiwan terms when there is a clearly established everyday or
     technical equivalent.
  2. Judge meaning before replacement: do not replace terms that are correct
     in their field, part of a quotation, or selected by the user.
  3. Avoid empty internet/business jargon by naming the actual action or
     outcome instead.
  4. Use full-width Chinese punctuation in Chinese prose; leave code, URLs,
     identifiers, and English-only spans unchanged.

  Include at most a small original set of high-confidence examples, each
  framed as a contextual preference rather than a global blacklist. Do not
  replicate the external project's table or its category structure.

- [ ] **Step 4: Verify file presence and deferred boundaries.**

  Run:

  ```bash
  for file in \
    session-preferences/references/deai-longform.md \
    session-preferences/references/deai-translation.md \
    session-preferences/references/taiwan-zh.md; do
    test -s "$file"
    sed -n '1,220p' "$file"
  done
  rg -n 'deai-longform|deai-translation|taiwan-zh' \
    session-preferences/references/INDEX.md && exit 1 || true
  ```

  Expected: all three files exist and contain guidance; the active index does
  not name a deferred reference.

### Task 3: Update the user manual and perform scenario checks

**Files:**
- Modify: `session-preferences/README.md`
- Verify: `session-preferences/SKILL.md`
- Verify: `session-preferences/references/*.md`

- [ ] **Step 1: Explain the layered policy in the README.**

  Keep the existing Traditional Chinese activation and current-session
  explanation. Replace the single de-AI module description with a table:

  ```markdown
  | 規則檔 | 何時讀取 | 用途 |
  | --- | --- | --- |
  | `deai-voice.md` | 啟用時 | 通用語氣、優先序與載入判斷 |
  | `deai-longform.md` | 草稿或超過兩段的敘述 | 長文去 AI 味與靜默自檢 |
  | `deai-translation.md` | 翻譯 | 忠實優先的自然繁中處理 |
  | `taiwan-zh.md` | 台灣用語或標點需要判斷 | 地區用語與標點 |
  ```

  Explain that `add-deai` now proposes the most suitable one of these files,
  still requires confirmation, and becomes active immediately after the
  confirmed write.

- [ ] **Step 2: Walk the five static scenarios.**

  Record the following expected behavior in the PR notes or final report; do
  not add a runtime test framework merely for prose instructions:

  | Input | Required reads | Expected guard |
  | --- | --- | --- |
  | A one-paragraph status answer | core only | direct answer with no forced checklist |
  | A three-paragraph explanatory draft | core + long-form | inspect contrasts, endings, and sentence load silently |
  | English-to-Traditional-Chinese translation | core + translation | preserve deliberate source rhetoric and uncertain meaning |
  | A Taiwan wording or punctuation request | core + Taiwan guidance | respect source, user locale, and code spans before normalizing |
  | `add-deai` rule request | target proposed first | no write before confirmation; reread after confirmation |

- [ ] **Step 3: Check documentation consistency.**

  Run:

  ```bash
  rg -n -C 2 'add-deai|deai-longform|deai-translation|taiwan-zh|INDEX' \
    session-preferences/SKILL.md session-preferences/README.md \
    session-preferences/references/deai-voice.md
  git diff --check -- session-preferences
  ```

  Expected: all four references have one consistent name and the README does
  not say every de-AI rule is always loaded.

### Task 4: Run required offline checks and prepare a reviewable diff

**Files:**
- Verify: `session-preferences/**`
- Verify: `skills-catalog.json`
- Verify: `skill-router/skill-registry.yaml`

- [ ] **Step 1: Validate the skill.**

  Run:

  ```bash
  bash skill-auditor/scripts/audit_skill.sh session-preferences
  python3 scripts/validate_skills_catalog.py --check
  git diff --check
  ```

  Expected: the skill audit has no critical findings, the existing catalog
  remains valid without catalog edits, and the full working-tree diff has no
  whitespace errors.

- [ ] **Step 2: Inspect the exact change scope.**

  Run:

  ```bash
  git status --short
  git diff -- session-preferences \
    docs/superpowers/specs/2026-07-30-session-preferences-deai-expansion-design.md \
    docs/superpowers/plans/2026-07-30-session-preferences-deai-expansion-implementation.md
  ```

  Expected: only the session-preferences references and documentation created
  for this expansion appear; unrelated runtime-policy documents remain
  untouched.

- [ ] **Step 3: Apply the review and commit boundary.**

  When the user asks to commit, invoke `code-review-codex` against the final
  diff, address accepted findings, and rerun this task's checks. Then ask for
  explicit commit approval before proposing a Conventional Commit message.
  Do not run `skill-sync` or a fresh runtime smoke as part of this plan. A
  fresh smoke needs a separate authorization and must be reported as distinct
  from the offline evidence.

## Spec Coverage Review

- Original, license-safe distillation: Guardrails and Tasks 1–2.
- Core versus deferred loading: Task 1.
- Long-form, translation, and Taiwan usage breadth: Task 2.
- Confirmation-gated rule maintenance and immediate session effect: Task 1,
  Step 2 and Task 3, Step 1.
- Shareable scope and explicit exclusions: Guardrails and Task 1, Step 3.
- Static scenario verification, skill audit, catalog validation, and runtime
  boundary: Tasks 3–4.
