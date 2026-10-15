"""Personal rules survive package updates, partial failures and competing writers."""
from __future__ import annotations

import hashlib
import importlib
import json
import os
import shutil
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "runtime"))
INDEX = "| Module | File | Purpose |\n| --- | --- | --- |\n| alpha | alpha.md | Active |\n"
SKILL = "## Rule\n\n```text\nDEFAULT RETURN\n```\n\n## Examples\n```text\nEXAMPLE ONLY\n```\n"


class PreferenceFixture(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory(prefix="personal rules 中文 ")
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name)
        self.defaults = self.root / "defaults"
        self.defaults.mkdir()
        (self.defaults / "INDEX.md").write_text(INDEX)
        (self.defaults / "alpha.md").write_text("DEFAULT ALPHA")
        (self.defaults / "deferred.md").write_text("DEFAULT DEFERRED")
        self.config = self.root / "config"
        self.personal = self.config / "preferences"

    def runtime(self):
        self.assertTrue((ROOT / "runtime/agent_skills_runtime/preferences.py").is_file(),
                        "Personal preference runtime has not been implemented")
        return importlib.import_module("agent_skills_runtime.preferences")

    def write_personal(self, name, content):
        self.personal.mkdir(parents=True, exist_ok=True)
        path = self.personal / name
        path.write_text(content)
        return path


class PreferencesTest(PreferenceFixture):

    def test_same_name_replaces_entire_default_and_new_module_appends(self):
        self.write_personal("INDEX.md", INDEX + "| beta | beta.md | Custom |\n")
        self.write_personal("alpha.md", "PERSONAL ALPHA")
        self.write_personal("beta.md", "PERSONAL BETA")
        content, warnings = self.runtime().load_preferences(self.defaults, self.config)
        self.assertIn("PERSONAL ALPHA", content)
        self.assertNotIn("DEFAULT ALPHA", content)
        self.assertLess(content.index("PERSONAL ALPHA"), content.index("PERSONAL BETA"))
        self.assertEqual(warnings, [])

    def test_deferred_reference_uses_personal_path_without_inlining(self):
        path = self.write_personal("deferred.md", "PERSONAL DEFERRED")
        content, warnings = self.runtime().load_preferences(self.defaults, self.config)
        self.assertIn(f"deferred.md: {path.resolve()}", content)
        self.assertNotIn("PERSONAL DEFERRED", content)
        self.assertNotIn(f"deferred.md: {(self.defaults / 'deferred.md').resolve()}", content)
        self.assertEqual(warnings, [])

    def test_broken_override_is_not_silently_replaced_by_default(self):
        path = self.write_personal("alpha.md", "placeholder")
        path.write_bytes(b"\xff invalid")
        self.write_personal("INDEX.md", "| Module | File | Purpose |\n| beta | beta.md | Valid |\n")
        self.write_personal("beta.md", "VALID BETA")
        content, warnings = self.runtime().load_preferences(self.defaults, self.config)
        self.assertIn("VALID BETA", content)
        self.assertNotIn("DEFAULT ALPHA", content)
        self.assertIn(str(path), "\n".join(warnings))
        self.assertIn("Not loaded", content)

    def test_bad_personal_index_preserves_default_modules_with_warning(self):
        self.write_personal("INDEX.md", "| bad | ../outside.md | Invalid |\n")
        content, warnings = self.runtime().load_preferences(self.defaults, self.config)
        self.assertIn("DEFAULT ALPHA", content)
        self.assertIn("../outside.md", "\n".join(warnings))

    def test_control_return_cannot_be_loaded_as_session_module(self):
        self.write_personal("INDEX.md", INDEX + "| return | control-return.md | Own hook |\n")
        self.write_personal("control-return.md", "PRIVATE RETURN RULE")
        content, warnings = self.runtime().load_preferences(self.defaults, self.config)
        self.assertNotIn("PRIVATE RETURN RULE", content)
        self.assertNotIn("control-return.md:", content)
        self.assertTrue(warnings)

    def test_external_symlink_is_not_injected(self):
        outside = self.root / "outside.md"
        outside.write_text("EXTERNAL CONTENT")
        self.personal.mkdir(parents=True)
        (self.personal / "alpha.md").symlink_to(outside)
        content, warnings = self.runtime().load_preferences(self.defaults, self.config)
        self.assertNotIn("EXTERNAL CONTENT", content)
        self.assertNotIn("DEFAULT ALPHA", content)
        self.assertTrue(warnings)

    def test_loading_is_read_only_and_deterministic(self):
        one = self.runtime().load_preferences(self.defaults, self.config)
        self.assertEqual(one, self.runtime().load_preferences(self.defaults, self.config))
        self.assertFalse(self.config.exists())

    def test_control_return_reads_complete_override_and_default_rule_only(self):
        skill = self.root / "SKILL.md"
        skill.write_text(SKILL)
        content, warnings = self.runtime().load_control_return(skill, self.config)
        self.assertEqual((content, warnings), ("DEFAULT RETURN", []))
        self.write_personal("control-return.md", "# Personal\n\nFULL PERSONAL RETURN")
        content, warnings = self.runtime().load_control_return(skill, self.config)
        self.assertEqual((content, warnings), ("# Personal\n\nFULL PERSONAL RETURN", []))

    def test_invalid_control_override_does_not_fall_back_to_packaged_rule(self):
        skill = self.root / "SKILL.md"
        skill.write_text(SKILL)
        self.write_personal("control-return.md", " ")
        content, warnings = self.runtime().load_control_return(skill, self.config)
        self.assertFalse(content)
        self.assertTrue(warnings)

    def test_first_override_records_base_and_later_edit_preserves_original_base(self):
        runtime = self.runtime()
        old_base = hashlib.sha256(b"DEFAULT ALPHA").hexdigest()
        path = runtime.save_module_override(self.config, "alpha.md", "FIRST", old_base, None)
        current = hashlib.sha256(path.read_bytes()).hexdigest()
        runtime.save_module_override(self.config, "alpha.md", "SECOND", "1" * 64, current)
        metadata = json.loads((self.personal / ".base-hashes.json").read_text())
        self.assertEqual(metadata["modules"]["alpha.md"]["base_hash"], old_base)
        self.assertEqual(path.read_text(), "SECOND")
        self.assertEqual((self.defaults / "alpha.md").read_text(), "DEFAULT ALPHA")

    def test_new_module_updates_index_but_existing_deferred_and_control_do_not(self):
        runtime = self.runtime()
        runtime.save_module_override(self.config, "deferred.md", "CUSTOM DEFERRED", "a" * 64, None)
        runtime.save_module_override(self.config, "control-return.md", "CUSTOM RETURN", None, None)
        self.assertFalse((self.personal / "INDEX.md").exists())
        runtime.save_module_override(self.config, "beta.md", "NEW BETA", None, None)
        content, warnings = runtime.load_preferences(self.defaults, self.config)
        self.assertIn("NEW BETA", content)
        self.assertNotIn("CUSTOM DEFERRED", content)
        self.assertNotIn("CUSTOM RETURN", content)
        self.assertEqual(warnings, [])

    def test_stale_hash_and_unconfirmed_creation_do_not_overwrite(self):
        runtime = self.runtime()
        path = runtime.save_module_override(self.config, "alpha.md", "FIRST", "a" * 64, None)
        before = {p.name: p.read_bytes() for p in self.personal.iterdir() if p.is_file()}
        for expected in [None, "0" * 64]:
            with self.subTest(expected=expected), self.assertRaises(ValueError):
                runtime.save_module_override(self.config, "alpha.md", "LOST UPDATE", None, expected)
        after = {p.name: p.read_bytes() for p in self.personal.iterdir() if p.is_file()}
        self.assertEqual(before, after)
        self.assertEqual(path.read_text(), "FIRST")

    def test_invalid_name_or_empty_rule_does_not_create_personal_directory(self):
        runtime = self.runtime()
        for name, content in [("../escape.md", "RULE"), ("INDEX.md", "RULE"), ("alpha.md", " ")]:
            with self.subTest(name=name), self.assertRaises(ValueError):
                runtime.save_module_override(self.config, name, content, None, None)
        self.assertFalse(self.config.exists())

    def test_two_real_processes_with_same_previous_hash_cannot_lose_update(self):
        runtime = self.runtime()
        path = runtime.save_module_override(self.config, "alpha.md", "INITIAL", "a" * 64, None)
        previous = hashlib.sha256(path.read_bytes()).hexdigest()
        worker = """import sys
from pathlib import Path
from agent_skills_runtime.preferences import save_module_override
try:
 save_module_override(Path(sys.argv[1]), 'alpha.md', sys.argv[2], None, sys.argv[3])
except ValueError:
 sys.exit(2)
"""
        env = dict(os.environ, PYTHONPATH=str(ROOT / "runtime"))
        processes = [subprocess.Popen([sys.executable, "-c", worker, str(self.config), body, previous],
                                      env=env, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
                     for body in ["WRITER A", "WRITER B"]]
        for process in processes:
            process.communicate(timeout=10)
        self.assertEqual(sorted(p.returncode for p in processes), [0, 2])
        self.assertIn(path.read_text(), ["WRITER A", "WRITER B"])

    def test_doctor_reports_changed_defaults_without_replacing_override(self):
        runtime = self.runtime()
        base = hashlib.sha256(b"DEFAULT ALPHA").hexdigest()
        path = runtime.save_module_override(self.config, "alpha.md", "KEEP PERSONAL", base, None)
        (self.defaults / "alpha.md").write_text("UPDATED DEFAULT")
        doctor = importlib.import_module("agent_skills_runtime.doctor")
        results = doctor.check_environment(self.config, {
            "config": ["preferences"], "preferences_defaults": str(self.defaults)})
        self.assertTrue(any(r["status"] == "default_changed" for r in results))
        self.assertEqual(path.read_text(), "KEEP PERSONAL")

    def test_real_cli_loads_effective_rules_and_saves_only_matching_preview(self):
        self.runtime()
        rule = self.root / "proposed.md"
        rule.write_text("CONFIRMED CUSTOM")
        env = dict(os.environ, PYTHONPATH=str(ROOT / "runtime"),
                   AGENT_SKILLS_CONFIG_DIR=str(self.config))
        command = [sys.executable, "-m", "agent_skills_runtime.preferences"]
        saved = subprocess.run(command + ["save", "--module", "beta.md", "--content-file", str(rule)],
                               env=env, capture_output=True, text=True, timeout=10)
        self.assertEqual(saved.returncode, 0, saved.stderr)
        self.assertTrue(saved.stdout.strip(), "Preference CLI did not save a rule")
        self.assertEqual((self.personal / "beta.md").read_text(), "CONFIRMED CUSTOM")
        loaded = subprocess.run(command + ["load", "--default-dir", str(self.defaults)],
                                env=env, capture_output=True, text=True, timeout=10)
        self.assertEqual(loaded.returncode, 0, loaded.stderr)
        self.assertIn("CONFIRMED CUSTOM", json.loads(loaded.stdout)["content"])
        stale = subprocess.run(command + ["save", "--module", "beta.md", "--content-file", str(rule)],
                               env=env, capture_output=True, text=True, timeout=10)
        self.assertNotEqual(stale.returncode, 0)

    def test_doctor_reports_broken_personal_module_instead_of_ok(self):
        self.runtime()
        self.write_personal("alpha.md", " ")
        doctor = importlib.import_module("agent_skills_runtime.doctor")
        results = doctor.check_environment(self.config, {
            "config": ["preferences"], "preferences_defaults": str(self.defaults)})
        self.assertTrue(any(r["component"] == "preferences" and r["status"] == "invalid"
                            for r in results))

    def test_changed_control_default_is_reported_from_its_rule_block(self):
        runtime = self.runtime()
        skill = self.root / "control-return-SKILL.md"
        skill.write_text(SKILL)
        base = hashlib.sha256(b"DEFAULT RETURN").hexdigest()
        runtime.save_module_override(self.config, "control-return.md", "KEEP RETURN", base, None)
        doctor = importlib.import_module("agent_skills_runtime.doctor")
        requirements = {"config": ["preferences"], "preferences_defaults": str(self.defaults),
                        "control_return_skill": str(skill)}
        first = doctor.check_environment(self.config, requirements)
        self.assertFalse(any(r["status"] == "default_changed" for r in first))
        skill.write_text(SKILL.replace("DEFAULT RETURN", "UPDATED RETURN"))
        changed = doctor.check_environment(self.config, requirements)
        self.assertTrue(any(r["component"] == "preferences:control-return.md" and
                            r["status"] == "default_changed" for r in changed))

    def test_malformed_base_metadata_blocks_edit_without_replacing_rule(self):
        runtime = self.runtime()
        path = runtime.save_module_override(self.config, "alpha.md", "KEEP", "a" * 64, None)
        (self.personal / ".base-hashes.json").write_text('{"modules":{"alpha.md":42}}')
        with self.assertRaises(ValueError):
            runtime.save_module_override(self.config, "alpha.md", "LOST", None,
                                         hashlib.sha256(b"KEEP").hexdigest())
        self.assertEqual(path.read_text(), "KEEP")

    def test_removing_override_restores_default_without_stale_update_warning(self):
        runtime = self.runtime()
        base = hashlib.sha256(b"DEFAULT ALPHA").hexdigest()
        path = runtime.save_module_override(self.config, "alpha.md", "PERSONAL", base, None)
        path.unlink()
        (self.defaults / "alpha.md").write_text("NEW DEFAULT")
        content, warnings = runtime.load_preferences(self.defaults, self.config)
        self.assertIn("NEW DEFAULT", content)
        self.assertEqual(warnings, [])
        self.assertEqual(runtime.check_preference_updates(self.defaults, self.config), [])


class HookOverridesTest(PreferenceFixture):
    def run_hook(self, skill, layout="repo", off=False):
        installed = Path(tempfile.mkdtemp(prefix=f"{layout} skills 中文 ", dir=self.root))
        if layout == "plugin":
            (installed / ".codex-plugin").mkdir()
            (installed / ".codex-plugin/plugin.json").write_text("{}")
        skill_parent = installed / "skills" if layout == "plugin" else installed
        target = skill_parent / skill
        shutil.copytree(ROOT / skill, target)
        shutil.copytree(ROOT / "runtime", installed / "runtime", ignore=shutil.ignore_patterns("__pycache__"))
        if skill == "session-preferences":
            shutil.rmtree(target / "references")
            shutil.copytree(self.defaults, target / "references")
        else:
            (target / "SKILL.md").write_text(SKILL)
        env = dict(os.environ, AGENT_SKILLS_CONFIG_DIR=str(self.config),
                   AGENT_SESSION_PREFS="off" if off else "")
        result = subprocess.run([sys.executable, str(target / "scripts/session_start_hook.py")],
                                cwd=self.root, input="{}", text=True, capture_output=True,
                                env=env, timeout=10)
        self.assertEqual(result.returncode, 0, result.stderr)
        return result.stdout

    def test_hooks_resolve_only_bundled_runtime_in_relocated_plugin(self):
        self.write_personal("alpha.md", "PLUGIN PERSONAL ALPHA")
        content = json.loads(self.run_hook("session-preferences", "plugin"))["hookSpecificOutput"]["additionalContext"]
        self.assertIn("PLUGIN PERSONAL ALPHA", content)
        self.assertNotIn("DEFAULT ALPHA", content)

    def test_control_hook_and_off_switch_use_personal_config(self):
        self.write_personal("control-return.md", "PERSONAL RETURN")
        output = json.loads(self.run_hook("control-return"))
        self.assertIn("PERSONAL RETURN", output["hookSpecificOutput"]["additionalContext"])
        self.assertNotIn("DEFAULT RETURN", output["hookSpecificOutput"]["additionalContext"])
        self.assertEqual(self.run_hook("session-preferences", off=True), "")
        self.assertEqual(self.run_hook("control-return", off=True), "")

    def test_missing_package_runtime_does_not_borrow_parent_runtime(self):
        installed = self.root / "incomplete package"
        target = installed / "session-preferences"
        shutil.copytree(ROOT / "session-preferences", target)
        shutil.copytree(ROOT / "runtime", self.root / "runtime")
        env = dict(os.environ, AGENT_SKILLS_CONFIG_DIR=str(self.config), AGENT_SESSION_PREFS="")
        result = subprocess.run([sys.executable, str(target / "scripts/session_start_hook.py")],
                                input="{}", text=True, capture_output=True, env=env, timeout=10)
        self.assertEqual(result.returncode, 0)
        output = json.loads(result.stdout)
        self.assertNotIn("hookSpecificOutput", output)
        self.assertIn("runtime is missing", output["systemMessage"])


if __name__ == "__main__":
    unittest.main()
