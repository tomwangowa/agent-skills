"""Regression tests for the skills catalog validator command-line contract."""

from __future__ import annotations

import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path


SOURCE_ROOT = Path(__file__).resolve().parents[1]
VALIDATOR = SOURCE_ROOT / "scripts" / "validate_skills_catalog.py"
CHECK_MANAGED_FILES = (
    "skills-catalog.json",
    "skill-router/skill-registry.yaml",
    "README.md",
    "README.zh.md",
    ".skill-sync-ignore",
    "SKILLS_CATALOG.md",
)


class SkillsCatalogFixture(unittest.TestCase):
    """A small Git repository that exercises catalog policy without repo state."""

    def setUp(self) -> None:
        self.temporary_directory = tempfile.TemporaryDirectory()
        self.root = Path(self.temporary_directory.name)
        self.git("init", "-q")

        self.write_skill("alpha")
        self.write_skill("beta")
        self.git("add", "alpha/SKILL.md", "beta/SKILL.md")

        # These look like skills on disk, but must not enter Git-based discovery.
        self.write_skill("untracked")
        self.write_skill("nested/example")

        self.write_router({"alpha"})
        self.write_readmes({"alpha"})
        (self.root / ".skill-sync-ignore").write_text(
            "# Infrastructure patterns are not catalog entries.\nnested/*\n",
            encoding="utf-8",
        )
        self.write_catalog(
            {
                "schema_version": 1,
                "skills": [
                    self.catalog_entry(
                        "alpha",
                        category="tools-meta",
                        lifecycle="promoted",
                        invocation_intent="model",
                        routable=True,
                        listed_in_readme=True,
                        sync=True,
                    ),
                    self.catalog_entry(
                        "beta",
                        category="productivity-tracking",
                        lifecycle="experimental",
                        invocation_intent="user",
                        routable=False,
                        listed_in_readme=False,
                        sync=True,
                    ),
                ],
            }
        )

    def tearDown(self) -> None:
        self.temporary_directory.cleanup()

    def git(self, *arguments: str) -> None:
        subprocess.run(
            ["git", *arguments],
            cwd=self.root,
            check=True,
            capture_output=True,
            text=True,
        )

    def write_skill(self, relative_directory: str) -> None:
        skill = self.root / relative_directory / "SKILL.md"
        skill.parent.mkdir(parents=True, exist_ok=True)
        skill.write_text("---\nname: fixture\n---\n", encoding="utf-8")

    def write_router(self, local_ids: set[str]) -> None:
        entries = "\n".join(
            f"      - id: {skill_id}\n        triggers: []" for skill_id in sorted(local_ids)
        )
        (self.root / "skill-router").mkdir(exist_ok=True)
        (self.root / "skill-router" / "skill-registry.yaml").write_text(
            "\n".join(
                [
                    "categories:",
                    "  fixture:",
                    "    label: Fixture",
                    "    skills:",
                    entries,
                    "      - id: superpowers:writing-plans",
                    "        triggers: []",
                    "workflows:",
                    "  - id: fixture-workflow",
                    "    steps: []",
                    "",
                ]
            ),
            encoding="utf-8",
        )

    def write_readmes(self, core_ids: set[str]) -> None:
        core_links = "\n".join(
            f"- [{skill_id}](./{skill_id}/SKILL.md)" for skill_id in sorted(core_ids)
        )
        content = "\n".join(
            [
                "# Fixture skills",
                "",
                "## Core Skills",
                "",
                "<!-- core-skills:start -->",
                core_links,
                "<!-- core-skills:end -->",
                "",
            ]
        )
        for name in ("README.md", "README.zh.md"):
            (self.root / name).write_text(content, encoding="utf-8")

    @staticmethod
    def catalog_entry(
        skill_id: str,
        *,
        category: str,
        lifecycle: str,
        invocation_intent: str,
        routable: bool,
        listed_in_readme: bool,
        sync: bool,
    ) -> dict[str, object]:
        return {
            "id": skill_id,
            "category": category,
            "lifecycle": lifecycle,
            "invocation_intent": invocation_intent,
            "surfaces": {
                "routable": routable,
                "listed_in_readme": listed_in_readme,
                "sync": sync,
            },
        }

    def catalog(self) -> dict[str, object]:
        return json.loads((self.root / "skills-catalog.json").read_text(encoding="utf-8"))

    def write_catalog(self, catalog: dict[str, object]) -> None:
        (self.root / "skills-catalog.json").write_text(
            json.dumps(catalog, indent=2) + "\n", encoding="utf-8"
        )

    def run_validator(self, *arguments: str) -> subprocess.CompletedProcess[str]:
        return subprocess.run(
            [sys.executable, str(VALIDATOR), *arguments],
            cwd=self.root,
            capture_output=True,
            text=True,
        )

    def snapshot_check_state(self) -> dict[str, object]:
        files = {
            relative_path: (
                (self.root / relative_path).read_bytes()
                if (self.root / relative_path).exists()
                else None
            )
            for relative_path in CHECK_MANAGED_FILES
        }
        regular_files = {
            path.relative_to(self.root).as_posix(): path.read_bytes()
            for path in self.root.rglob("*")
            if path.is_file() and ".git" not in path.relative_to(self.root).parts
        }
        directories = sorted(
            path.relative_to(self.root).as_posix()
            for path in self.root.rglob("*")
            if path.is_dir() and ".git" not in path.relative_to(self.root).parts
        )
        paths = sorted(
            path.relative_to(self.root).as_posix()
            for path in self.root.rglob("*")
            if ".git" not in path.relative_to(self.root).parts
        )
        return {
            "files": files,
            "regular_files": regular_files,
            "directories": directories,
            "paths": paths,
        }

    def run_check_read_only(self) -> subprocess.CompletedProcess[str]:
        before = self.snapshot_check_state()
        result = self.run_validator("--check")
        self.assertEqual(self.snapshot_check_state(), before)
        return result

    def assert_validator_succeeds(self, *arguments: str) -> subprocess.CompletedProcess[str]:
        result = (
            self.run_check_read_only()
            if arguments == ("--check",)
            else self.run_validator(*arguments)
        )
        self.assertEqual(
            result.returncode,
            0,
            msg=f"stdout:\n{result.stdout}\nstderr:\n{result.stderr}",
        )
        return result

    def assert_validator_rejects(self, *expected_details: str) -> None:
        result = self.run_check_read_only()
        self.assertNotEqual(result.returncode, 0)
        output = result.stdout + result.stderr
        for expected_detail in expected_details:
            self.assertIn(expected_detail, output)

    def generate_valid_catalog(self) -> None:
        self.assert_validator_succeeds("--write")

    def entry(self, skill_id: str) -> dict[str, object]:
        catalog = self.catalog()
        skills = catalog["skills"]
        assert isinstance(skills, list)
        return next(entry for entry in skills if entry["id"] == skill_id)

    def surfaces(self, skill_id: str) -> dict[str, bool]:
        surfaces = self.entry(skill_id)["surfaces"]
        assert isinstance(surfaces, dict)
        return surfaces  # type: ignore[return-value]


class ValidateSkillsCatalogTests(SkillsCatalogFixture):
    def test_discovery_includes_only_tracked_top_level_skill_directories(self) -> None:
        self.generate_valid_catalog()

        index = (self.root / "SKILLS_CATALOG.md").read_text(encoding="utf-8")
        self.assertIn("[alpha](./alpha/SKILL.md)", index)
        self.assertIn("[beta](./beta/SKILL.md)", index)
        self.assertNotIn("untracked", index)
        self.assertNotIn("nested/example", index)

    def test_validation_rejects_catalog_skill_missing_from_git_inventory(self) -> None:
        self.generate_valid_catalog()
        catalog = self.catalog()
        skills = catalog["skills"]
        assert isinstance(skills, list)
        skills.append(
            self.catalog_entry(
                "ghost",
                category="tools-meta",
                lifecycle="experimental",
                invocation_intent="model",
                routable=False,
                listed_in_readme=False,
                sync=True,
            )
        )
        self.write_catalog(catalog)

        self.assert_validator_rejects("ghost")

    def test_validation_rejects_tracked_skill_missing_from_catalog(self) -> None:
        self.generate_valid_catalog()
        catalog = self.catalog()
        skills = catalog["skills"]
        assert isinstance(skills, list)
        catalog["skills"] = [entry for entry in skills if entry["id"] != "beta"]
        self.write_catalog(catalog)

        self.assert_validator_rejects("beta")

    def test_validation_rejects_catalog_untracked_or_nested_skill(self) -> None:
        self.generate_valid_catalog()

        for skill_id in ("untracked", "nested/example"):
            with self.subTest(skill_id=skill_id):
                catalog = self.catalog()
                skills = catalog["skills"]
                assert isinstance(skills, list)
                skills.append(
                    self.catalog_entry(
                        skill_id,
                        category="tools-meta",
                        lifecycle="experimental",
                        invocation_intent="model",
                        routable=False,
                        listed_in_readme=False,
                        sync=True,
                    )
                )
                self.write_catalog(catalog)

                self.assert_validator_rejects(skill_id)
                self.write_catalog(
                    {
                        "schema_version": 1,
                        "skills": skills[:-1],
                    }
                )

    def test_validation_rejects_duplicate_catalog_id(self) -> None:
        self.generate_valid_catalog()
        catalog = self.catalog()
        skills = catalog["skills"]
        assert isinstance(skills, list)
        skills.append(dict(self.entry("alpha")))
        self.write_catalog(catalog)

        self.assert_validator_rejects("duplicate")

    def test_validation_rejects_unknown_category_or_lifecycle(self) -> None:
        self.generate_valid_catalog()
        baseline = self.catalog()

        for field, invalid_value in (
            ("category", "not-a-category"),
            ("lifecycle", "not-a-lifecycle"),
        ):
            with self.subTest(field=field):
                catalog = json.loads(json.dumps(baseline))
                skills = catalog["skills"]
                assert isinstance(skills, list)
                alpha = next(entry for entry in skills if entry["id"] == "alpha")
                alpha[field] = invalid_value
                self.write_catalog(catalog)

                self.assert_validator_rejects(invalid_value)
                self.write_catalog(baseline)

    def test_validation_allows_deprecated_lifecycle(self) -> None:
        self.generate_valid_catalog()
        catalog = self.catalog()
        skills = catalog["skills"]
        assert isinstance(skills, list)
        beta = next(entry for entry in skills if entry["id"] == "beta")
        beta["lifecycle"] = "deprecated"
        self.write_catalog(catalog)
        self.run_validator("--write")

        result = self.run_check_read_only()

        self.assertEqual(result.returncode, 0, result.stdout + result.stderr)

    def test_validation_rejects_deprecated_skill_on_promoted_surfaces(self) -> None:
        self.generate_valid_catalog()
        catalog = self.catalog()
        skills = catalog["skills"]
        assert isinstance(skills, list)
        alpha = next(entry for entry in skills if entry["id"] == "alpha")
        alpha["lifecycle"] = "deprecated"
        self.write_catalog(catalog)

        self.assert_validator_rejects("deprecated skill alpha")

    def test_validation_rejects_routable_skill_missing_from_router_categories(self) -> None:
        self.generate_valid_catalog()
        self.write_router(set())

        self.assert_validator_rejects("alpha")

    def test_validation_rejects_non_routable_skill_still_present_in_router_categories(self) -> None:
        self.generate_valid_catalog()
        self.write_router({"alpha", "beta"})

        self.assert_validator_rejects("beta")

    def test_validation_rejects_readme_listed_skill_outside_core_markers(self) -> None:
        self.generate_valid_catalog()
        catalog = self.catalog()
        skills = catalog["skills"]
        assert isinstance(skills, list)
        beta = next(entry for entry in skills if entry["id"] == "beta")
        surfaces = beta["surfaces"]
        assert isinstance(surfaces, dict)
        surfaces["listed_in_readme"] = True
        self.write_catalog(catalog)
        for readme_name in ("README.md", "README.zh.md"):
            readme_path = self.root / readme_name
            readme_path.write_text(
                readme_path.read_text(encoding="utf-8")
                + "\n- [beta](./beta/SKILL.md)\n",
                encoding="utf-8",
            )

        self.assert_validator_rejects("beta")

    def test_validation_rejects_invalid_catalog_schema_and_field_types(self) -> None:
        self.generate_valid_catalog()
        baseline = (self.root / "skills-catalog.json").read_text(encoding="utf-8")
        catalog_path = self.root / "skills-catalog.json"

        catalog_path.write_text("{not valid json\n", encoding="utf-8")
        self.assert_validator_rejects("skills-catalog.json", "JSON")
        catalog_path.write_text(baseline, encoding="utf-8")

        cases = (
            ("schema_version", 2, ("schema_version",)),
            ("invocation_intent", "robot", ("alpha", "invocation_intent")),
            ("missing-id", None, ("id",)),
            ("routable", "yes", ("alpha", "routable")),
        )
        for field, value, expected_details in cases:
            with self.subTest(field=field):
                catalog = self.catalog()
                skills = catalog["skills"]
                assert isinstance(skills, list)
                alpha = next(entry for entry in skills if entry["id"] == "alpha")
                if field == "schema_version":
                    catalog["schema_version"] = value
                elif field == "missing-id":
                    del alpha["id"]
                elif field == "routable":
                    surfaces = alpha["surfaces"]
                    assert isinstance(surfaces, dict)
                    surfaces["routable"] = value
                else:
                    alpha[field] = value
                self.write_catalog(catalog)

                self.assert_validator_rejects(
                    "skills-catalog.json", *expected_details
                )
                catalog_path.write_text(baseline, encoding="utf-8")

    def test_validation_rejects_sync_false_without_exact_top_level_ignore(self) -> None:
        self.generate_valid_catalog()
        catalog = self.catalog()
        skills = catalog["skills"]
        assert isinstance(skills, list)
        beta = next(entry for entry in skills if entry["id"] == "beta")
        surfaces = beta["surfaces"]
        assert isinstance(surfaces, dict)
        surfaces["sync"] = False
        self.write_catalog(catalog)
        (self.root / ".skill-sync-ignore").write_text("beta/*\n", encoding="utf-8")

        self.assert_validator_rejects("beta")

    def test_validation_allows_sync_false_with_exact_top_level_ignore(self) -> None:
        self.generate_valid_catalog()

        for ignore_entry in ("beta", "beta/"):
            with self.subTest(ignore_entry=ignore_entry):
                catalog = self.catalog()
                skills = catalog["skills"]
                assert isinstance(skills, list)
                beta = next(entry for entry in skills if entry["id"] == "beta")
                surfaces = beta["surfaces"]
                assert isinstance(surfaces, dict)
                surfaces["sync"] = False
                self.write_catalog(catalog)
                (self.root / ".skill-sync-ignore").write_text(
                    f"{ignore_entry}\n", encoding="utf-8"
                )

                self.assert_validator_succeeds("--write")
                self.assert_validator_succeeds("--check")

                surfaces["sync"] = True
                self.write_catalog(catalog)
                (self.root / ".skill-sync-ignore").write_text(
                    "nested/*\n", encoding="utf-8"
                )

    def test_validation_rejects_sync_true_with_exact_top_level_ignore(self) -> None:
        self.generate_valid_catalog()
        (self.root / ".skill-sync-ignore").write_text("beta\n", encoding="utf-8")

        self.assert_validator_rejects("beta")

    def test_sync_ignore_matches_sync_script_clean_line_rules(self) -> None:
        self.generate_valid_catalog()
        catalog = self.catalog()
        skills = catalog["skills"]
        assert isinstance(skills, list)
        beta = next(entry for entry in skills if entry["id"] == "beta")
        surfaces = beta["surfaces"]
        assert isinstance(surfaces, dict)
        surfaces["sync"] = False
        self.write_catalog(catalog)
        (self.root / ".skill-sync-ignore").write_text(
            " \tbeta/ # excluded from sync\r\n",
            encoding="utf-8",
        )

        self.assert_validator_succeeds("--write")
        self.assert_validator_succeeds("--check")

        surfaces["sync"] = True
        self.write_catalog(catalog)

        self.assert_validator_rejects("beta")

    def test_validation_rejects_when_either_readme_lacks_core_link(self) -> None:
        self.generate_valid_catalog()

        missing_core_section = "# Fixture skills\n"
        missing_core_link = "\n".join(
            [
                "# Fixture skills",
                "",
                "## Core Skills",
                "",
                "<!-- core-skills:start -->",
                "<!-- core-skills:end -->",
                "",
            ]
        )
        for readme_name in ("README.md", "README.zh.md"):
            for label, content in (
                ("marker", missing_core_section),
                ("link", missing_core_link),
            ):
                with self.subTest(readme_name=readme_name, missing=label):
                    (self.root / readme_name).write_text(
                        content,
                        encoding="utf-8",
                    )

                    self.assert_validator_rejects(readme_name)
                    self.write_readmes({"alpha"})

    def test_validation_rejects_duplicate_routable_id(self) -> None:
        self.generate_valid_catalog()
        router_path = self.root / "skill-router" / "skill-registry.yaml"
        router_path.write_text(
            router_path.read_text(encoding="utf-8").replace(
                "workflows:\n",
                "      - id: alpha\n        triggers: []\nworkflows:\n",
            ),
            encoding="utf-8",
        )

        self.assert_validator_rejects("alpha")

    def test_router_allows_external_superpowers_entry_without_catalog_row(self) -> None:
        self.generate_valid_catalog()

        self.assert_validator_succeeds("--check")

    def test_router_rejects_local_id_without_catalog_entry(self) -> None:
        self.generate_valid_catalog()
        self.write_router({"alpha", "rogue"})

        self.assert_validator_rejects("rogue")

    def test_router_ignores_local_id_after_workflows_section(self) -> None:
        self.generate_valid_catalog()
        router_path = self.root / "skill-router" / "skill-registry.yaml"
        router_path.write_text(
            router_path.read_text(encoding="utf-8").replace(
                "workflows:\n  - id: fixture-workflow",
                "workflows:\n  - id: rogue\n    steps: []\n  - id: fixture-workflow",
            ),
            encoding="utf-8",
        )

        self.assert_validator_succeeds("--check")

    def test_renderer_sorts_rows_by_category_then_id(self) -> None:
        self.write_skill("gamma")
        self.git("add", "gamma/SKILL.md")
        catalog = self.catalog()
        skills = catalog["skills"]
        assert isinstance(skills, list)
        alpha = next(entry for entry in skills if entry["id"] == "alpha")
        beta = next(entry for entry in skills if entry["id"] == "beta")
        gamma = self.catalog_entry(
            "gamma",
            category="productivity-tracking",
            lifecycle="experimental",
            invocation_intent="user",
            routable=False,
            listed_in_readme=False,
            sync=True,
        )
        alpha["category"] = "tools-meta"
        beta["category"] = "productivity-tracking"
        catalog["skills"] = [alpha, gamma, beta]
        self.write_catalog(catalog)

        self.assert_validator_succeeds("--write")
        index = (self.root / "SKILLS_CATALOG.md").read_text(encoding="utf-8")
        beta_position = index.index("| [beta](./beta/SKILL.md)")
        gamma_position = index.index("| [gamma](./gamma/SKILL.md)")
        alpha_position = index.index("| [alpha](./alpha/SKILL.md)")
        self.assertLess(beta_position, gamma_position)
        self.assertLess(gamma_position, alpha_position)

    def test_check_rejects_stale_generated_catalog_and_write_repairs_it(self) -> None:
        self.generate_valid_catalog()
        generated_path = self.root / "SKILLS_CATALOG.md"
        expected = generated_path.read_text(encoding="utf-8")
        generated_path.write_text("# stale\n", encoding="utf-8")

        result = self.run_check_read_only()
        self.assertNotEqual(result.returncode, 0)
        self.assertIn("SKILLS_CATALOG.md", result.stdout + result.stderr)
        self.assertEqual(generated_path.read_text(encoding="utf-8"), "# stale\n")

        self.assert_validator_succeeds("--write")
        self.assertEqual(generated_path.read_text(encoding="utf-8"), expected)
        self.assert_validator_succeeds("--check")

    def test_write_preserves_existing_index_when_validation_fails(self) -> None:
        self.generate_valid_catalog()
        generated_path = self.root / "SKILLS_CATALOG.md"
        original = generated_path.read_text(encoding="utf-8")
        self.write_router(set())

        result = self.run_validator("--write")

        self.assertNotEqual(result.returncode, 0)
        self.assertIn("alpha", result.stdout + result.stderr)
        self.assertEqual(generated_path.read_text(encoding="utf-8"), original)


if __name__ == "__main__":
    unittest.main()
