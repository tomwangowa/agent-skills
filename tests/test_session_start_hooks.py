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

    def test_undecodable_module_is_reported_like_a_missing_one(self) -> None:
        self.write_reference("INDEX.md", INDEX_MD)
        self.write_reference("alpha.md", "ALPHA RULE\n")
        (self.skill_dir / "references" / "beta.md").write_bytes(b"\xff\xfe not utf-8")
        output = self.run_json()
        context = output["hookSpecificOutput"]["additionalContext"]
        self.assertIn("ALPHA RULE", context)
        self.assertIn("beta.md", output["systemMessage"])


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

    def test_rule_heading_without_block_does_not_borrow_a_later_block(self) -> None:
        self.write_skill("## Rule\n\nProse only.\n\n## Examples\n\n```text\nEXAMPLE TEXT\n```\n")
        output = self.run_json()
        self.assertNotIn("hookSpecificOutput", output)
        self.assertIn("## Rule", output["systemMessage"])

    def test_missing_skill_md_warns_without_context(self) -> None:
        output = self.run_json()
        self.assertNotIn("hookSpecificOutput", output)
        self.assertIn("SKILL.md", output["systemMessage"])


if __name__ == "__main__":
    unittest.main()
