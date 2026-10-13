# SessionStart Hooks Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Auto-apply `session-preferences` and `control-return` in every Claude Code and Codex session through SessionStart hooks.

**Architecture:** Each skill ships its own `scripts/session_start_hook.py`. The script locates its skill directory from `__file__`, reads the rule files, and prints `hookSpecificOutput.additionalContext` JSON, which both runtimes accept. Claude Code runs the copy under `~/.claude/skills`, and Codex runs the skill-sync mirror under `~/.codex/skills`. The matcher is `startup|clear|compact`, and `AGENT_SESSION_PREFS=off` disables both scripts.

**Tech Stack:** Python 3 stdlib only. The scripts must run on `/usr/bin/python3` 3.9.6 as well as the pyenv 3.12 shim. Tests use `unittest` with subprocess, matching `tests/test_validate_skills_catalog.py`.

**Spec:** `docs/superpowers/specs/2026-10-12-session-start-hooks-design.md`

**Commit rule (applies to every commit step):** Do not commit without Tom's explicit approval for that specific commit. Before asking, classify the change with `completion-gate` L0/L1/L2. For L1/L2, run `code-review-claude` once. Chain the checks into the commit with `&&`.

---

## File map

| File | Action | Responsibility |
|---|---|---|
| `session-preferences/scripts/session_start_hook.py` | Create | Read INDEX and its listed modules, then emit the context JSON |
| `control-return/scripts/session_start_hook.py` | Create | Extract the `## Rule` text block, then emit the context JSON |
| `tests/test_session_start_hooks.py` | Create | Fixture-based subprocess tests for both scripts |
| `session-preferences/SKILL.md` | Modify | Remove "never automatic"; add `## Automatic loading` |
| `control-return/SKILL.md` | Modify | Same, plus an off-switch note |
| `session-preferences/agents/openai.yaml`, `control-return/agents/openai.yaml` | Modify | Update `short_description` |
| `session-preferences/README.md` | Modify | Describe automatic loading |
| `CLAUDE.md` | Modify | Rewrite the first line; add `## Deployment` |
| `AGENTS.md` | Create (symlink) | Relative symlink to `CLAUDE.md` |
| `~/.claude/settings.json` | Modify (outside repo) | Add a SessionStart group with two hooks |
| `~/.codex/hooks.json` | Modify (outside repo) | Add SessionStart with two hooks |

---

### Task 0: Branch

- [ ] **Step 1: Create a feature branch.** The untracked spec and plan files carry over to the new branch.

```bash
git -C /Users/tom_wang/Development/harness/agent-skills switch -c feat/session-start-hooks
```

Expected: `Switched to a new branch 'feat/session-start-hooks'`

---

### Task 1: session-preferences hook script

**Files:**
- Create: `session-preferences/scripts/session_start_hook.py`
- Test: `tests/test_session_start_hooks.py`

- [ ] **Step 1: Write the failing tests**

Create `tests/test_session_start_hooks.py`:

```python
"""Regression tests for the SessionStart hook scripts of session-preferences and control-return."""

from __future__ import annotations

import json
import os
import shutil
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path


SOURCE_ROOT = Path(__file__).resolve().parents[1]
SP_SCRIPT = SOURCE_ROOT / "session-preferences" / "scripts" / "session_start_hook.py"
CR_SCRIPT = SOURCE_ROOT / "control-return" / "scripts" / "session_start_hook.py"
HOOK_INPUT = json.dumps({"hook_event_name": "SessionStart", "source": "startup"})
SP_HEADER = "[session-preferences — auto-applied by SessionStart hook]"
CR_HEADER = "[control-return — auto-applied by SessionStart hook]"

INDEX_MD = """# Active modules

| Module | File | Purpose |
| --- | --- | --- |
| alpha | alpha.md | First module. |
| beta | beta.md | Second module. |
"""


class HookFixture(unittest.TestCase):
    """Copy a hook script into a throwaway skill directory so tests never read real rules."""

    script: Path

    def setUp(self) -> None:
        self.temporary_directory = tempfile.TemporaryDirectory()
        self.skill_dir = Path(self.temporary_directory.name) / "skill"
        (self.skill_dir / "scripts").mkdir(parents=True)
        self.installed = self.skill_dir / "scripts" / "session_start_hook.py"
        shutil.copy(self.script, self.installed)

    def tearDown(self) -> None:
        self.temporary_directory.cleanup()

    def run_hook(self, **env_overrides: str) -> tuple[int, str]:
        env = {k: v for k, v in os.environ.items() if k != "AGENT_SESSION_PREFS"}
        env.update(env_overrides)
        result = subprocess.run(
            [sys.executable, str(self.installed)],
            input=HOOK_INPUT,
            capture_output=True,
            text=True,
            env=env,
            timeout=10,
        )
        return result.returncode, result.stdout

    def run_json(self, **env_overrides: str) -> dict:
        code, stdout = self.run_hook(**env_overrides)
        self.assertEqual(code, 0)
        return json.loads(stdout)


class SessionPreferencesHookTest(HookFixture):
    script = SP_SCRIPT

    def write_reference(self, name: str, text: str) -> Path:
        references = self.skill_dir / "references"
        references.mkdir(exist_ok=True)
        path = references / name
        path.write_text(text, encoding="utf-8")
        return path

    def write_full_fixture(self) -> None:
        self.write_reference("INDEX.md", INDEX_MD)
        self.write_reference("alpha.md", "ALPHA RULE\n")
        self.write_reference("beta.md", "BETA RULE\n")
        self.write_reference("gamma.md", "GAMMA DEFERRED\n")

    def test_injects_listed_modules_in_index_order(self) -> None:
        self.write_full_fixture()
        output = self.run_json()
        context = output["hookSpecificOutput"]["additionalContext"]
        self.assertEqual(output["hookSpecificOutput"]["hookEventName"], "SessionStart")
        self.assertTrue(context.startswith(SP_HEADER))
        self.assertIn("those take precedence", context)
        self.assertLess(context.index("ALPHA RULE"), context.index("BETA RULE"))
        self.assertNotIn("systemMessage", output)

    def test_lists_deferred_references_by_absolute_path_without_inlining(self) -> None:
        self.write_full_fixture()
        context = self.run_json()["hookSpecificOutput"]["additionalContext"]
        gamma = (self.skill_dir / "references" / "gamma.md").resolve()
        self.assertIn(f"gamma.md: {gamma}", context)
        self.assertNotIn("GAMMA DEFERRED", context)
        self.assertNotIn("INDEX.md:", context)

    def test_off_switch_prints_nothing(self) -> None:
        self.write_full_fixture()
        code, stdout = self.run_hook(AGENT_SESSION_PREFS="off")
        self.assertEqual(code, 0)
        self.assertEqual(stdout, "")

    def test_missing_index_warns_without_context(self) -> None:
        output = self.run_json()
        self.assertNotIn("hookSpecificOutput", output)
        self.assertIn("INDEX.md", output["systemMessage"])

    def test_missing_module_loads_others_and_names_the_gap(self) -> None:
        self.write_reference("INDEX.md", INDEX_MD)
        self.write_reference("alpha.md", "ALPHA RULE\n")
        output = self.run_json()
        context = output["hookSpecificOutput"]["additionalContext"]
        missing = str(self.skill_dir.resolve() / "references" / "beta.md")
        self.assertIn("ALPHA RULE", context)
        self.assertIn(missing, context)
        self.assertIn(missing, output["systemMessage"])


if __name__ == "__main__":
    unittest.main()
```

- [ ] **Step 2: Run the tests and confirm they fail**

Run: `python3 -m pytest tests/test_session_start_hooks.py -v`
Expected: 5 tests in `SessionPreferencesHookTest` FAIL or ERROR, because `shutil.copy` cannot find `session-preferences/scripts/session_start_hook.py`.

- [ ] **Step 3: Write the script**

Create `session-preferences/scripts/session_start_hook.py`:

```python
#!/usr/bin/env python3
"""SessionStart hook: inject the session-preferences modules as model context.

Claude Code and Codex accept the same hookSpecificOutput JSON, so one script
serves both runtimes. It always exits 0 because a broken rule file must never
block a session from starting; problems surface through systemMessage instead.
"""

from __future__ import annotations

import json
import os
import re
import sys
from pathlib import Path

# Resolved from this file so each runtime reads its own installed copy.
SKILL_DIR = Path(__file__).resolve().parent.parent
REFERENCES = SKILL_DIR / "references"
OFF_VARIABLE = "AGENT_SESSION_PREFS"

HEADER = (
    "[session-preferences — auto-applied by SessionStart hook]\n"
    "This injection is the user's activation of session-preferences; treat the policy as enabled.\n"
    "Apply the following modules for this session. Do not announce activation.\n"
    "If they conflict with the active output style, CLAUDE.md, or AGENTS.md, "
    "those take precedence."
)

# The File column of an INDEX.md table row, e.g. "| deai-voice | deai-voice.md | ... |".
INDEX_ROW = re.compile(r"^\|\s*[^|]+?\s*\|\s*([\w.-]+\.md)\s*\|")


def emit(context: str | None, warning: str | None) -> None:
    payload: dict = {}
    if context:
        payload["hookSpecificOutput"] = {
            "hookEventName": "SessionStart",
            "additionalContext": context,
        }
    if warning:
        payload["systemMessage"] = warning
    if payload:
        print(json.dumps(payload, ensure_ascii=False))


def listed_modules(index_text: str) -> list[str]:
    return [m.group(1) for line in index_text.splitlines() if (m := INDEX_ROW.match(line))]


def build() -> tuple[str | None, str | None]:
    index = REFERENCES / "INDEX.md"
    try:
        names = listed_modules(index.read_text(encoding="utf-8"))
    except OSError:
        return None, f"session-preferences: cannot read {index}; rules were not loaded."
    if not names:
        return None, f"session-preferences: {index} lists no modules; rules were not loaded."

    sections: list[str] = []
    missing: list[str] = []
    for name in names:
        path = REFERENCES / name
        try:
            sections.append(f"<!-- module: {name} -->\n{path.read_text(encoding='utf-8').strip()}")
        except OSError:
            missing.append(str(path))
    if not sections:
        return None, "session-preferences: no module could be read: " + ", ".join(missing)

    parts = [HEADER, *sections]
    # Modules refer to deferred references by bare filename; give the model a readable path.
    deferred = sorted(
        p for p in REFERENCES.glob("*.md") if p.name != "INDEX.md" and p.name not in names
    )
    if deferred:
        parts.append(
            "Deferred references (read only when an active module calls for it):\n"
            + "\n".join(f"- {p.name}: {p}" for p in deferred)
        )
    warning = None
    if missing:
        parts.append(
            "Not loaded (unreadable; do not claim these rules are applied):\n"
            + "\n".join(f"- {m}" for m in missing)
        )
        warning = "session-preferences: some modules were not loaded: " + ", ".join(missing)
    return "\n\n".join(parts), warning


def main() -> int:
    if os.environ.get(OFF_VARIABLE, "").lower() == "off":
        return 0
    try:
        if sys.stdin is not None and not sys.stdin.isatty():
            sys.stdin.read()  # Drain hook input; its content does not change the output.
        context, warning = build()
    except Exception as error:  # noqa: BLE001 - any failure must degrade to a warning
        context, warning = None, f"session-preferences hook failed: {error}"
    emit(context, warning)
    return 0


if __name__ == "__main__":
    sys.exit(main())
```

- [ ] **Step 4: Run the tests and confirm they pass**

Run: `python3 -m pytest tests/test_session_start_hooks.py -v -k SessionPreferences`
Expected: 5 passed

Run: `/usr/bin/python3 -m unittest tests.test_session_start_hooks.SessionPreferencesHookTest -v`
Expected: `Ran 5 tests ... OK`. This confirms the script runs on the system Python 3.9.6 that Codex may use.

- [ ] **Step 5: Smoke-test against the real repo rules**

```bash
echo '{}' | python3 session-preferences/scripts/session_start_hook.py | python3 -c "import json,sys; d=json.load(sys.stdin); c=d['hookSpecificOutput']['additionalContext']; print(len(c.encode()), 'bytes'); print([l for l in c.splitlines() if l.startswith('<!-- module')]); print('warning:', d.get('systemMessage'))"
```

Expected: about 4000 bytes; modules `deai-voice.md`, `explanation-depth.md`, `socratic-dialogue.md`; `warning: None`.

No commit in this task. Task 2 shares the test file, so the commit happens at the end of Task 2.

---

### Task 2: control-return hook script

**Files:**
- Create: `control-return/scripts/session_start_hook.py`
- Test: `tests/test_session_start_hooks.py` (append a class)

- [ ] **Step 1: Write the failing tests**

Insert this class into `tests/test_session_start_hooks.py`, directly above `if __name__ == "__main__":`:

````python
CR_SKILL_MD = """---
name: control-return
---

# Control Return

## Rule

```text
RULE LINE ONE
RULE LINE TWO
```

## Examples

```text
EXAMPLE TEXT
```
"""


class ControlReturnHookTest(HookFixture):
    script = CR_SCRIPT

    def write_skill(self, text: str) -> None:
        (self.skill_dir / "SKILL.md").write_text(text, encoding="utf-8")

    def test_injects_only_the_rule_block(self) -> None:
        self.write_skill(CR_SKILL_MD)
        output = self.run_json()
        context = output["hookSpecificOutput"]["additionalContext"]
        self.assertTrue(context.startswith(CR_HEADER))
        self.assertIn("RULE LINE ONE\nRULE LINE TWO", context)
        self.assertNotIn("EXAMPLE TEXT", context)
        self.assertNotIn("systemMessage", output)

    def test_off_switch_prints_nothing(self) -> None:
        self.write_skill(CR_SKILL_MD)
        code, stdout = self.run_hook(AGENT_SESSION_PREFS="off")
        self.assertEqual(code, 0)
        self.assertEqual(stdout, "")

    def test_missing_rule_block_warns_without_context(self) -> None:
        self.write_skill("# Control Return\n\nNo rule section here.\n")
        output = self.run_json()
        self.assertNotIn("hookSpecificOutput", output)
        self.assertIn("## Rule", output["systemMessage"])

    def test_missing_skill_md_warns_without_context(self) -> None:
        output = self.run_json()
        self.assertNotIn("hookSpecificOutput", output)
        self.assertIn("SKILL.md", output["systemMessage"])
````

- [ ] **Step 2: Run the tests and confirm they fail**

Run: `python3 -m pytest tests/test_session_start_hooks.py -v -k ControlReturn`
Expected: 4 ERROR, because `control-return/scripts/session_start_hook.py` does not exist yet.

- [ ] **Step 3: Write the script**

Create `control-return/scripts/session_start_hook.py`:

```python
#!/usr/bin/env python3
"""SessionStart hook: inject the control-return rule as model context.

The rule text is extracted from SKILL.md so the skill file stays the single
source of truth. Always exits 0; problems surface through systemMessage.
"""

from __future__ import annotations

import json
import os
import re
import sys
from pathlib import Path

# Resolved from this file so each runtime reads its own installed copy.
SKILL_MD = Path(__file__).resolve().parent.parent / "SKILL.md"
OFF_VARIABLE = "AGENT_SESSION_PREFS"

HEADER = (
    "[control-return — auto-applied by SessionStart hook]\n"
    "Apply the following rule for this session. Do not announce activation.\n"
    "If it conflicts with the active output style, CLAUDE.md, or AGENTS.md, "
    "those take precedence."
)

# The first ```text block after the "## Rule" heading.
RULE_BLOCK = re.compile(r"^## Rule[ \t]*\n.*?^```text[ \t]*\n(.*?)^```", re.DOTALL | re.MULTILINE)


def emit(context: str | None, warning: str | None) -> None:
    payload: dict = {}
    if context:
        payload["hookSpecificOutput"] = {
            "hookEventName": "SessionStart",
            "additionalContext": context,
        }
    if warning:
        payload["systemMessage"] = warning
    if payload:
        print(json.dumps(payload, ensure_ascii=False))


def build() -> tuple[str | None, str | None]:
    try:
        text = SKILL_MD.read_text(encoding="utf-8")
    except OSError:
        return None, f"control-return: cannot read {SKILL_MD}; rule was not loaded."
    match = RULE_BLOCK.search(text)
    if not match or not match.group(1).strip():
        return None, f"control-return: no ```text block under '## Rule' in {SKILL_MD}; rule was not loaded."
    return f"{HEADER}\n\n{match.group(1).strip()}", None


def main() -> int:
    if os.environ.get(OFF_VARIABLE, "").lower() == "off":
        return 0
    try:
        if sys.stdin is not None and not sys.stdin.isatty():
            sys.stdin.read()  # Drain hook input; its content does not change the output.
        context, warning = build()
    except Exception as error:  # noqa: BLE001 - any failure must degrade to a warning
        context, warning = None, f"control-return hook failed: {error}"
    emit(context, warning)
    return 0


if __name__ == "__main__":
    sys.exit(main())
```

- [ ] **Step 4: Run the full test file and confirm it passes**

Run: `python3 -m pytest tests/test_session_start_hooks.py -v`
Expected: 9 passed

Run: `/usr/bin/python3 -m unittest tests.test_session_start_hooks -v`
Expected: `Ran 9 tests ... OK`

- [ ] **Step 5: Smoke-test against the real SKILL.md**

```bash
echo '{}' | python3 control-return/scripts/session_start_hook.py | python3 -c "import json,sys; d=json.load(sys.stdin); print(d['hookSpecificOutput']['additionalContext'])"
```

Expected: the header, then the four rule lines starting with `當你歸還控制權時`. No `Example` text.

> **Review follow-up (applied during execution, 2026-10-12):** the pre-commit `code-review-claude` pass led to three changes, so the committed scripts differ slightly from the code blocks above. (1) The file-read handlers catch `(OSError, ValueError)`, so a non-UTF-8 file is reported like a missing one instead of failing the whole hook. (2) `RULE_BLOCK` stops at the next `## ` heading, so it can never take a later section's text block as the rule. (3) A failed stdin drain no longer skips building the context. Two regression tests cover (1) and (2); both failed before the fix. The suite now has 11 tests. A later Task 3 review found that an INDEX row whose File cell failed the pattern (for example a backticked filename) was silently skipped. `listed_modules` now parses table cells, accepts backticks, and reports invalid cells like missing modules (commit `f36865b`, 13 tests).

- [ ] **Step 6: Commit (Tom's approval required)**

Classify with `completion-gate`. New executable scripts and tests are expected to be L1, so run `code-review-claude` once. Show Tom the result and ask for approval. Only after approval:

```bash
python3 -m pytest tests/test_session_start_hooks.py -q && \
git add session-preferences/scripts/session_start_hook.py control-return/scripts/session_start_hook.py tests/test_session_start_hooks.py && \
git commit -m "feat(session-preferences,control-return): add SessionStart hook scripts

Co-Authored-By: Claude Opus 5.5 <noreply@anthropic.com>"
```

---

### Task 3: Skill text, agents metadata, README

**Files:**
- Modify: `session-preferences/SKILL.md`, `control-return/SKILL.md`
- Modify: `session-preferences/agents/openai.yaml`, `control-return/agents/openai.yaml`
- Modify: `session-preferences/README.md`

- [ ] **Step 1: session-preferences frontmatter description.** Replace the `description:` line with:

```yaml
description: "Use when the user explicitly invokes $session-preferences or /session-preferences to re-apply the session policy bundle mid-session, or to propose and confirm a new rule. A SessionStart hook auto-applies the bundle at session start; the model must not invoke this skill on its own."
```

- [ ] **Step 2a: session-preferences intro.** Replace:

```markdown
Load and apply the user's active interaction rules from `references/` for the
remainder of this session. This is a manual, session-scoped policy bundle; it
is not a global runtime setting.
```

with:

```markdown
Apply the user's active interaction rules from `references/` for the rest of
the session. A SessionStart hook loads them automatically; the manual command
re-applies them. This is session-scoped, not a global runtime setting.
```

- [ ] **Step 2: session-preferences Activation section.** Replace the paragraph that begins `Do not apply rules retroactively or in a new session.` with:

```markdown
New sessions already get these modules from the SessionStart hook (see
Automatic loading). Use the manual command when the hook did not run, for
example when `AGENT_SESSION_PREFS=off` was set, and the user wants the policy
for the rest of this session. Do not apply rules retroactively.
```

- [ ] **Step 3: session-preferences new section.** Insert this directly before `## Maintain Rules`:

```markdown
## Automatic loading

`scripts/session_start_hook.py` runs as a SessionStart hook in Claude Code
(`~/.claude/settings.json`) and Codex (`~/.codex/hooks.json`) with matcher
`startup|clear|compact`. It injects `INDEX.md` modules verbatim, plus the
absolute paths of deferred references. In hook mode the activation reply is
not sent. Setting `AGENT_SESSION_PREFS=off` before starting a session skips
injection. If a file is unreadable, the hook names the path in a warning and
the missing rules must not be claimed as applied.
```

- [ ] **Step 4: control-return frontmatter description.** Replace the `description:` line with:

```yaml
description: "Use when the user explicitly invokes $control-return or /control-return to re-apply the three-next-steps rule mid-session. A SessionStart hook auto-applies the rule at session start; the model must not invoke this skill on its own."
```

- [ ] **Step 5: control-return Activation and new section.** Replace `There is no off command. If the user asks to stop, stop.` with:

```markdown
There is no off command inside a session; if the user asks to stop, stop.
To start a session without the rule, set `AGENT_SESSION_PREFS=off` first.

## Automatic loading

`scripts/session_start_hook.py` runs as a SessionStart hook in Claude Code
and Codex with matcher `startup|clear|compact`. It injects the `## Rule`
block below verbatim, and the activation reply is not sent. If the block
cannot be found, the hook warns and the rule is not active.
```

Replace the intro line `Manual, session-scoped rule. It is an instruction carried by the current` / `conversation, not a runtime setting.` with:

```markdown
Session-scoped rule, loaded automatically by a SessionStart hook; the manual
command re-applies it. It is an instruction carried by the current
conversation, not a runtime setting.
```

Also in `## Activation`, replace step 1's second sentence `Do not apply it retroactively or in a new session.` with `Do not apply it retroactively.`

- [ ] **Step 6: agents metadata.** In `session-preferences/agents/openai.yaml`, set:

```yaml
  short_description: "Session response rules, auto-applied at session start"
```

In `control-return/agents/openai.yaml`, set:

```yaml
  short_description: "End each reply with three next steps, auto-applied at session start"
```

Leave `allow_implicit_invocation: false` unchanged in both files.

- [ ] **Step 7: README.** In `session-preferences/README.md`:
  - Replace the first paragraph's `是一組手動啟用的 session 回應規則。它不會自己啟用，也不會改 global policy 或同步到其他 runtime。` with `是一組 session 回應規則。Claude Code 和 Codex 開新 session、/clear、壓縮 context 時，SessionStart hook 會自動注入；它不會改 global policy，也不會自己同步到其他 runtime。`
  - Replace the `## 啟用` section body with:

````markdown
平常不用做任何事，hook 會在 session 開始時載入規則。想在某個 session 不套用，開 session 前設 `AGENT_SESSION_PREFS=off`。

hook 沒跑的 session 裡，要手動套用時：

```text
$session-preferences
```
````

  - Replace `「每則回覆附三個下一步」已獨立成另一個手動 skill：`$control-return`。它不會隨 `$session-preferences` 一起啟用。` with `「每則回覆附三個下一步」是另一個 skill：`$control-return`，有自己的 SessionStart hook，同一個 `AGENT_SESSION_PREFS=off` 也會關掉它。`

  - In the module list under `## 規則檔案`, add `explanation-depth.md` between the `deai-voice.md` and `socratic-dialogue.md` bullets, matching `references/INDEX.md`:

```markdown
- `explanation-depth.md`：重要判斷、設計變更和交接內容要交代理由、影響範圍、取捨與驗證方式。
```

- [ ] **Step 8: Check for leftover "never automatic" wording**

```bash
grep -n -i -E "never enable automatically|anual, session-scoped|不會自己啟用|in a new session|手動 skill" session-preferences/SKILL.md session-preferences/README.md control-return/SKILL.md
```

Expected: no output, exit code 1.

- [ ] **Step 9: Run skill-auditor on both skills.** Invoke `skill-auditor` for `session-preferences` and `control-return`. Fix any finding or record a disposition. Then re-run the tests, because they read `control-return/SKILL.md`:

```bash
python3 -m pytest tests/test_session_start_hooks.py -q && echo '{}' | python3 control-return/scripts/session_start_hook.py | grep -c "當你歸還控制權時"
```

Expected: `13 passed`, then `1`.

- [ ] **Step 10: Catalog check**

Run: `python3 scripts/validate_skills_catalog.py --check`
Expected: exit 0. If it reports a stale description, run `--write`, review the diff, and include the regenerated files in this commit.

- [ ] **Step 11: Commit (Tom's approval required).** Classify with `completion-gate`; skill text is expected to be L1, so run `code-review-claude` once and ask Tom. After approval:

```bash
python3 scripts/validate_skills_catalog.py --check && \
git add session-preferences/SKILL.md session-preferences/README.md session-preferences/agents/openai.yaml control-return/SKILL.md control-return/agents/openai.yaml && \
git commit -m "docs(session-preferences,control-return): document SessionStart auto-loading

Co-Authored-By: Claude Opus 5.5 <noreply@anthropic.com>"
```

If Step 10 regenerated catalog files, add them to the same `git add`.

---

### Task 4: Repo guidance — CLAUDE.md Deployment and AGENTS.md symlink

**Files:**
- Modify: `CLAUDE.md`
- Create: `AGENTS.md` (symlink)

- [ ] **Step 1: Rewrite the first line.** In `CLAUDE.md`, replace:

```markdown
This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.
```

with:

```markdown
This file provides guidance to coding agents working in this repository. Claude Code reads `CLAUDE.md`; Codex reads `AGENTS.md`, which is a symlink to this file.
```

- [ ] **Step 2: Add the Deployment section.** Insert this directly before `## Creating New Skills`:

```markdown
## Deployment

- `~/.claude/skills` is a symlink to the `agent-skills-production` worktree (branch `production`). Changes on `main` take effect only after they are merged into `production`.
- `~/.codex/skills` and `~/.omp/agent/skills` are rsync mirrors written by `skill-sync`. After `production` changes, run `skill-sync --dry-run`, review every write and deletion, and sync only after confirmation.
- New or modified Codex hooks (`~/.codex/hooks.json`) run only after they are approved in Codex.
- SessionStart hooks for `session-preferences` and `control-return` read the runtime's own installed copy, so a Codex rule change is live only after `skill-sync`.
```

- [ ] **Step 3: Create the symlink**

```bash
cd /Users/tom_wang/Development/harness/agent-skills && ln -s CLAUDE.md AGENTS.md && ls -l AGENTS.md && head -3 AGENTS.md
```

Expected: `AGENTS.md -> CLAUDE.md`, followed by the new first lines.

- [ ] **Step 4: Confirm git stores it as a symlink**

```bash
git add -N AGENTS.md && git ls-files -s AGENTS.md
```

Expected: mode `120000`.

- [ ] **Step 5: Commit (Tom's approval required).** Classify with `completion-gate` (docs only, expected L0) and ask Tom. After approval:

```bash
test -L AGENTS.md && \
git add CLAUDE.md AGENTS.md && \
git commit -m "docs(repo): document deployment chain and add AGENTS.md symlink

Co-Authored-By: Claude Opus 5.5 <noreply@anthropic.com>"
```

- [ ] **Step 6: Commit spec and plan (Tom's approval required)**

```bash
git add docs/superpowers/specs/2026-10-12-session-start-hooks-design.md docs/superpowers/plans/2026-10-12-session-start-hooks.md && \
git commit -m "docs(specs): add session-start hooks design and plan

Co-Authored-By: Claude Opus 5.5 <noreply@anthropic.com>"
```

---

### Task 5: Land on main and production (Tom's decision)

- [ ] **Step 1: Ask Tom how to land the branch on `main`.** Recent history includes both GitHub PRs (#25) and direct commits. Do not push or open a PR without explicit approval.

- [ ] **Step 2: After `main` has the commits, ask approval to fast-forward production**

```bash
git -C /Users/tom_wang/Development/harness/agent-skills-production merge --ff-only main
```

Expected: `Fast-forward`. If it is not a fast-forward, stop and report to Tom; do not merge or rebase on your own.

- [ ] **Step 3: Verify the installed copy**

```bash
ls -l ~/.claude/skills/session-preferences/scripts/session_start_hook.py ~/.claude/skills/control-return/scripts/session_start_hook.py && \
echo '{}' | python3 ~/.claude/skills/session-preferences/scripts/session_start_hook.py | python3 -c "import json,sys; print(json.load(sys.stdin).get('systemMessage'))"
```

Expected: both files are listed, then `None`.

---

### Task 6: Claude Code hook

- [ ] **Step 1: Back up settings**

```bash
cp ~/.claude/settings.json ~/.claude/settings.json.bak-session-start-hooks
```

- [ ] **Step 2: Add the hook group.** Invoke `update-config`, then append this group to the existing `hooks.SessionStart` array. Leave the existing `cc-status` group untouched:

```json
{
  "matcher": "startup|clear|compact",
  "hooks": [
    { "type": "command", "command": "python3 /Users/tom_wang/.claude/skills/session-preferences/scripts/session_start_hook.py", "timeout": 5 },
    { "type": "command", "command": "python3 /Users/tom_wang/.claude/skills/control-return/scripts/session_start_hook.py", "timeout": 5 }
  ]
}
```

- [ ] **Step 3: Validate the JSON and show the diff**

```bash
python3 -c "import json; d=json.load(open('/Users/tom_wang/.claude/settings.json')); print(json.dumps(d['hooks']['SessionStart'], indent=1))" && \
diff ~/.claude/settings.json.bak-session-start-hooks ~/.claude/settings.json
```

Expected: two groups, `cc-status` first; the diff shows only the added group.

- [ ] **Step 4: Verify in a real session**

```bash
claude -p "List, verbatim, every line in your context that starts with '[session-preferences' or '[control-return'. If none, reply NONE."
```

Expected: both header lines.

```bash
AGENT_SESSION_PREFS=off claude -p "List, verbatim, every line in your context that starts with '[session-preferences' or '[control-return'. If none, reply NONE."
```

Expected: `NONE`.

```bash
claude -p "Is session-preferences enabled in this session, and is control-return active? Answer yes or no for each and quote the text that tells you."
```

Expected: yes for both, quoting the injected headers, including the activation sentence. If the model answers no for session-preferences, `deai-voice.md`'s "after the user enables" condition is being read literally; report this to Tom before continuing.

---

### Task 7: Codex sync and hook

- [ ] **Step 1: Preview the sync**

```bash
bash ~/.claude/skills/skill-sync/scripts/sync.sh --dry-run
```

Show Tom the full preview: every write and every deletion per target. `~/.codex/skills` currently holds target-only entries such as `.memory`, `.worktrees`, `code-comprehension-skills`, and `.pytest_cache`, and mirror mode deletes them. Ask Tom to choose between mirror mode and `--no-delete`.

- [ ] **Step 2: Run the sync Tom chose.** Use `sync.sh` or `sync.sh --no-delete`. The script prompts `y/N`; Tom answers.

- [ ] **Step 3: Verify the Codex copy**

```bash
diff -rq --exclude=.DS_Store --exclude=__pycache__ ~/.claude/skills/session-preferences ~/.codex/skills/session-preferences; \
diff -rq --exclude=.DS_Store --exclude=__pycache__ ~/.claude/skills/control-return ~/.codex/skills/control-return; \
echo '{}' | python3 ~/.codex/skills/session-preferences/scripts/session_start_hook.py | python3 -c "import json,sys; print(json.load(sys.stdin).get('systemMessage'))"
```

Expected: no diff output, then `None`.

- [ ] **Step 4: Back up and edit hooks.json**

```bash
cp ~/.codex/hooks.json ~/.codex/hooks.json.bak-session-start-hooks && \
python3 - <<'EOF'
import json
from pathlib import Path

path = Path.home() / ".codex" / "hooks.json"
data = json.loads(path.read_text())
base = "/Users/tom_wang/.codex/skills"
data["hooks"]["SessionStart"] = [{
    "matcher": "startup|clear|compact",
    "hooks": [
        {"type": "command", "command": f"python3 {base}/session-preferences/scripts/session_start_hook.py", "timeout": 5},
        {"type": "command", "command": f"python3 {base}/control-return/scripts/session_start_hook.py", "timeout": 5},
    ],
}]
path.write_text(json.dumps(data, indent=2, ensure_ascii=False) + "\n")
EOF
diff ~/.codex/hooks.json.bak-session-start-hooks ~/.codex/hooks.json
```

Expected: the diff adds only `SessionStart`; `PreToolUse` is unchanged.

- [ ] **Step 5: Tom approves the hooks in Codex.** Ask Tom to open the Codex TUI and approve the two new SessionStart hooks. The agent cannot do this.

- [ ] **Step 6: Confirm trust state**

```bash
grep -n -A1 'hooks.state' ~/.codex/config.toml
```

Expected: the original `pre_tool_use:0:0` entry keeps the same `trusted_hash` (`sha256:46a8258957ce…`), and two new entries for the SessionStart hooks appear with their own hashes. The exact key names are NOT VERIFIED; record what Codex writes.

- [ ] **Step 7: Verify in a real session**

```bash
codex exec "List, verbatim, every line in your context that starts with '[session-preferences' or '[control-return'. If none, reply NONE."
AGENT_SESSION_PREFS=off codex exec "List, verbatim, every line in your context that starts with '[session-preferences' or '[control-return'. If none, reply NONE."
```

```bash
codex exec "Is session-preferences enabled in this session, and is control-return active? Answer yes or no for each and quote the text that tells you."
```

Expected: both header lines for the first run, then `NONE`, then yes for both with quotes. If the first run shows only part of the session-preferences block, `additional_context_limit` is truncating it; report this to Tom.

---

### Task 8: Resume and compact checks, then record results

- [ ] **Step 1: Claude resume**

```bash
claude -p "Reply OK." --output-format json | python3 -c "import json,sys; print(json.load(sys.stdin)['session_id'])"
```

Then, with that id:

```bash
claude -p --resume <session_id> "List, verbatim, every line in your context that starts with '[session-preferences' or '[control-return'. If none, reply NONE."
```

Expected (assumption under test): both header lines are still present.

- [ ] **Step 2: Codex resume**

```bash
codex exec "Reply OK." && \
codex exec resume --last "List, verbatim, every line in your context that starts with '[session-preferences' or '[control-return'. If none, reply NONE."
```

Expected (assumption under test): both header lines.

- [ ] **Step 3: Compact (Tom runs this).** Ask Tom to run `/compact` in an interactive Claude Code session and in an interactive Codex session, then send the same "List, verbatim…" prompt in each.

- [ ] **Step 4: Record results in the spec.** Add a `## 9. Verification results` section to `docs/superpowers/specs/2026-10-12-session-start-hooks-design.md` with the observed output of Tasks 6–8, and update section 3's NOT VERIFIED line. If either resume check returned `NONE`, stop and raise the matcher decision with Tom again; do not change the matcher on your own.

- [ ] **Step 5: Commit the results (Tom's approval required)**

```bash
git add docs/superpowers/specs/2026-10-12-session-start-hooks-design.md && \
git commit -m "docs(specs): record session-start hooks verification results

Co-Authored-By: Claude Opus 5.5 <noreply@anthropic.com>"
```
