"""Cross-runtime config priority and explicit, non-destructive setup behavior."""
import importlib
import json
import os
import sys
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "runtime"))


class RuntimeConfigTest(unittest.TestCase):
    def config(self):
        return importlib.import_module("agent_skills_runtime.config")

    def test_shared_cases(self):
        cases = json.loads((ROOT / "tests/fixtures/plugin-config-cases.json").read_text())
        for case in cases:
            with self.subTest(case=case["name"]):
                config = self.config()
                home = Path(case["home"])
                root = config.resolve_config_root(case["env"], home)
                settings = {"sources": {"activities": case.get("settings_activity", "data/activities")}}
                self.assertEqual(str(root), case["root"])
                self.assertEqual(str(config.resolve_activities_dir(case["env"], settings, root, home)),
                                 case["activities"])

    def test_relative_root_is_rejected_instead_of_using_launch_directory(self):
        with self.assertRaises(ValueError):
            self.config().resolve_config_root({"AGENT_SKILLS_CONFIG_DIR": "relative"}, Path("/fixture/home"))

    def test_missing_invalid_and_empty_notes_settings_fail(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            with self.assertRaises(FileNotFoundError):
                self.config().read_work_journal(root)
            path = root / "work-journal.json"
            for body in ["{", "[]", '{"sources":{"activities":"data","notes":{"paths":[]}}}',
                         '{"sources":{"activities":"data","notes":{"paths":[""]}}}']:
                path.write_text(body)
                with self.subTest(body=body), self.assertRaises(ValueError):
                    self.config().read_work_journal(root)

    def test_setup_creates_selected_folders_and_preserves_existing_config(self):
        setup = importlib.import_module("agent_skills_runtime.setup")
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            config_root, activities, notes = root / "config", root / "journal", root / "notes"
            path = setup.setup_work_journal(config_root, activities, [notes])
            before = path.read_bytes()
            self.assertTrue(activities.is_dir() and notes.is_dir())
            changed = root / "other-journal"
            self.assertEqual(setup.setup_work_journal(config_root, changed, [notes]), path)
            self.assertEqual(path.read_bytes(), before)
            self.assertFalse(changed.exists())
            self.assertEqual(self.config().read_work_journal(config_root)["sources"]["activities"], str(activities))

    def test_setup_rejects_empty_notes_without_creating_files(self):
        setup = importlib.import_module("agent_skills_runtime.setup")
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            with self.assertRaises(ValueError):
                setup.setup_work_journal(root / "config", root / "journal", [])
            self.assertEqual(list(root.iterdir()), [])

    def test_setup_relative_data_paths_use_the_config_root(self):
        setup = importlib.import_module("agent_skills_runtime.setup")
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            previous = Path.cwd()
            try:
                os.chdir(root)
                config_root = root / "settings"
                setup.setup_work_journal(config_root, Path("journal"), [Path("notes")])
                self.assertTrue((config_root / "journal").is_dir())
                self.assertFalse((root / "journal").exists())
            finally:
                os.chdir(previous)

    def test_doctor_only_checks_selected_requirements_and_does_not_create_config(self):
        doctor = importlib.import_module("agent_skills_runtime.doctor")
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory) / "missing-config"
            result = doctor.check_environment(root, {"commands": ["python3"], "config": []})
            self.assertEqual([r["component"] for r in result], ["python3"])
            self.assertEqual(result[0]["status"], "ok")
            self.assertFalse(root.exists())
            result = doctor.check_environment(root, {"commands": [], "config": ["work-journal"]})
            self.assertEqual(result[0]["status"], "missing")
            self.assertFalse(root.exists())


if __name__ == "__main__":
    unittest.main()
