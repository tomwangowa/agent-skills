"""Behavior tests for portable probe bundles and evidence-based surface gates."""

from __future__ import annotations

import hashlib
import importlib.util
import json
import os
import shutil
import subprocess
import tempfile
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
SCRIPT = ROOT / "scripts" / "probe_plugin_runtimes.py"
SURFACES = ("claude-cli", "codex-cli")


class ProbeTest(unittest.TestCase):
    def setUp(self) -> None:
        self.temporary = tempfile.TemporaryDirectory(prefix="plugin probe ")
        self.root = Path(self.temporary.name)

    def tearDown(self) -> None:
        self.temporary.cleanup()

    def module(self):
        self.assertTrue(SCRIPT.is_file(), "Runtime probe implementation is missing")
        spec = importlib.util.spec_from_file_location("runtime_probe", SCRIPT)
        self.assertIsNotNone(spec)
        module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(module)
        return module

    def write_contract(self) -> Path:
        evidence = self.root / "observed.json"
        evidence.write_text('{"observation":"controlled test evidence"}\n')
        surfaces = {}
        for surface in SURFACES:
            surfaces[surface] = {
                "status": "verified",
                "client_version": "test-client-1",
                "manifest_format": "claude" if surface == "claude-cli" else "agent-plugins-1.0.0",
                "mcp_launch": {
                    "status": "verified", "command": "node", "args": ["server/dist/index.js"],
                    "tools": ["dashboard", "log_activity", "query_activities", "query_decisions",
                              "query_timeline", "query_todos", "search"],
                    "round_trip": True,
                    "fixture_isolation": {"status": "verified"},
                },
                "hook_events": {event: "verified" for event in ("startup", "resume", "clear", "compact")},
                "routing_result": {"status": "verified", "preference_off": True, "native_reviewer": True},
                "superpowers_version": "test-version",
                "evidence": [{"path": evidence.name, "sha256": hashlib.sha256(evidence.read_bytes()).hexdigest()}],
            }
        path = self.root / "contract.json"
        path.write_text(json.dumps({"schema_version": 1, "surfaces": surfaces}))
        return path

    def alter_contract(self, path: Path, mutate) -> None:
        payload = json.loads(path.read_text())
        mutate(payload)
        path.write_text(json.dumps(payload))

    def test_missing_contract_is_not_verified(self) -> None:
        errors = self.module().validate_runtime_contracts(self.root / "absent.json")
        self.assertTrue(errors)

    def test_rejects_unverified_surface(self) -> None:
        path = self.write_contract()
        self.alter_contract(path, lambda d: d["surfaces"]["codex-cli"].update(status="not_verified"))
        errors = self.module().validate_runtime_contracts(path)
        self.assertTrue(any("codex-cli" in error for error in errors))

    def test_removed_desktop_surface_does_not_block_cli_gate(self) -> None:
        path = self.write_contract()
        self.alter_contract(path, lambda d: d["surfaces"].update({"codex-desktop": {"status": "failed"}}))
        self.assertEqual(self.module().validate_runtime_contracts(path), [])

    def test_round_trip_without_fixture_binding_is_rejected(self) -> None:
        path = self.write_contract()
        self.alter_contract(path, lambda d: d["surfaces"]["codex-cli"]["mcp_launch"].pop("fixture_isolation"))
        self.assertTrue(any("isolation" in e for e in self.module().validate_runtime_contracts(path)))

    def test_verified_label_cannot_replace_mcp_round_trip(self) -> None:
        path = self.write_contract()
        self.alter_contract(path, lambda d: d["surfaces"]["codex-cli"]["mcp_launch"].update(round_trip=False))
        self.assertTrue(self.module().validate_runtime_contracts(path))

    def test_missing_tool_prevents_contract_acceptance(self) -> None:
        path = self.write_contract()
        self.alter_contract(path, lambda d: d["surfaces"]["claude-cli"]["mcp_launch"]["tools"].remove("log_activity"))
        self.assertTrue(self.module().validate_runtime_contracts(path))

    def test_missing_hook_event_prevents_contract_acceptance(self) -> None:
        path = self.write_contract()
        self.alter_contract(path, lambda d: d["surfaces"]["codex-cli"]["hook_events"].pop("compact"))
        self.assertTrue(self.module().validate_runtime_contracts(path))

    def test_modified_evidence_prevents_contract_acceptance(self) -> None:
        path = self.write_contract()
        (self.root / "observed.json").write_text("changed after observation")
        self.assertTrue(self.module().validate_runtime_contracts(path))

    def test_missing_evidence_prevents_contract_acceptance(self) -> None:
        path = self.write_contract()
        (self.root / "observed.json").unlink()
        self.assertTrue(self.module().validate_runtime_contracts(path))

    def test_valid_recorded_contract_is_accepted(self) -> None:
        self.assertEqual(self.module().validate_runtime_contracts(self.write_contract()), [])

    def source_repo(self) -> Path:
        repo = self.root / "source"
        server = repo / "skills-query-server"
        (server / "dist").mkdir(parents=True)
        (server / "dist" / "index.js").write_text("export {};\n")
        (server / "config.json").write_text('{"secret":"private-source-marker"}')
        (server / "README.md").write_text("development-only marker")
        (server / "scripts").mkdir()
        (server / "scripts/probe_server.mjs").write_text("// probe runtime\n")
        shutil.copytree(ROOT / "runtime", repo / "runtime", ignore=shutil.ignore_patterns("__pycache__"))
        for name in ("runtime-package", "dev-package"):
            package = server / "node_modules" / name
            package.mkdir(parents=True)
            (package / "package.json").write_text(json.dumps({"name": name, "version": "1.0.0"}))
        (server / "package.json").write_text(json.dumps({"type": "module"}))
        (server / "package-lock.json").write_text(json.dumps({
            "lockfileVersion": 3,
            "packages": {"": {}, "node_modules/runtime-package": {"version": "1.0.0"},
                         "node_modules/dev-package": {"version": "1.0.0", "dev": True}},
        }))
        for name in ("session-preferences", "control-return"):
            dest = repo / name
            dest.mkdir()
            shutil.copy2(ROOT / name / "SKILL.md", dest / "SKILL.md")
            shutil.copytree(ROOT / name / "scripts", dest / "scripts")
            if (ROOT / name / "references").exists():
                shutil.copytree(ROOT / name / "references", dest / "references")
        for name in ("brainstorming", "completion-gate", "code-review-claude", "code-review-codex"):
            directory = repo / name
            directory.mkdir()
            (directory / "SKILL.md").write_text(f"---\nname: {name}\ndescription: Probe skill.\n---\n\nProbe.\n")
        return repo

    def test_probe_fixture_contains_only_runtime_files(self) -> None:
        repo = self.source_repo()
        dest = self.root / "output with spaces"
        bundle = self.module().build_probe_fixture(repo, dest, "codex-cli")
        self.assertEqual(bundle, dest)
        self.assertTrue((dest / "server/dist/index.js").is_file())
        self.assertTrue((dest / "server/node_modules/runtime-package/package.json").is_file())
        self.assertFalse((dest / "server/node_modules/dev-package").exists())
        self.assertFalse((dest / "server/README.md").exists())
        config = json.loads((dest / "server/config.json").read_text())
        self.assertNotIn("secret", config)
        self.assertTrue((dest / "server" / config["sources"]["activities"]).resolve().is_dir())
        manifest = json.loads((dest / "plugin.json").read_text())
        self.assertEqual(manifest["$schema"], "https://agent-plugins.org/schemas/1.0.0/plugin.schema.json")
        mcp = json.loads((dest / "mcp.json").read_text())
        self.assertEqual(list(mcp["mcpServers"]), ["agent_skills_probe_codex_cli"])
        self.assertEqual(mcp["mcpServers"]["agent_skills_probe_codex_cli"]["type"], "stdio")
        self.assertTrue((dest / "server/probe_server.mjs").is_file())
        identity = json.loads((dest / "server/probe-identity.json").read_text())
        self.assertEqual(identity["surface"], "codex-cli")
        self.assertTrue(identity["probe_id"])
        self.assertNotIn("code-review-claude", [p.name for p in (dest / "skills").iterdir()])

    def test_moved_bundle_hooks_use_its_own_resources(self) -> None:
        repo = self.source_repo()
        original = self.root / "original"
        module = self.module()
        module.build_probe_fixture(repo, original, "claude-cli")
        relocated = self.root / "moved 中文 bundle"
        shutil.move(original, relocated)
        script = relocated / "skills/session-preferences/scripts/session_start_hook.py"
        env = dict(os.environ)
        env.pop("AGENT_SESSION_PREFS", None)
        env["AGENT_SKILLS_CONFIG_DIR"] = str(self.root / "personal-config")
        output = subprocess.run(["python3", str(script)], input="{}", text=True,
                                capture_output=True, cwd=self.root, env=env, timeout=10, check=True)
        context = json.loads(output.stdout)["hookSpecificOutput"]["additionalContext"]
        self.assertIn("session-preferences", context)
        self.assertIn(str(relocated / "skills/session-preferences/references"), context)
        self.assertNotIn(str(original), context)

    def test_codex_legacy_probe_has_no_shadowing_portable_manifest(self) -> None:
        repo = self.source_repo()
        dest = self.root / "legacy probe"
        self.module().build_probe_fixture(repo, dest, "codex-cli", manifest_format="legacy")
        self.assertFalse((dest / "plugin.json").exists())
        manifest = json.loads((dest / ".codex-plugin/plugin.json").read_text())
        self.assertEqual(manifest["hooks"], "./hooks/hooks.json")
        self.assertEqual(manifest["skills"], "./skills/")
        mcp = json.loads((dest / ".mcp.json").read_text())
        self.assertEqual(mcp["mcpServers"]["agent_skills_probe_codex_cli"]["args"],
                         ["launch.mjs"])
        self.assertEqual(mcp["mcpServers"]["agent_skills_probe_codex_cli"]["cwd"], "./server/")

    def test_unknown_manifest_format_is_rejected_before_build(self) -> None:
        repo = self.source_repo()
        dest = self.root / "invalid format"
        with self.assertRaises(ValueError):
            self.module().build_probe_fixture(repo, dest, "codex-cli", manifest_format="unknown")
        self.assertFalse(dest.exists())

    def test_rejects_external_symlink_in_runtime_resources(self) -> None:
        repo = self.source_repo()
        outside = self.root / "private.txt"
        outside.write_text("private-source-marker")
        (repo / "session-preferences/references/external.md").symlink_to(outside)
        with self.assertRaises(ValueError):
            self.module().build_probe_fixture(repo, self.root / "output", "claude-cli")

    def test_existing_destination_is_not_overwritten(self) -> None:
        repo = self.source_repo()
        destination = self.root / "already-present"
        destination.mkdir()
        marker = destination / "keep.txt"
        marker.write_text("keep")
        with self.assertRaises(FileExistsError):
            self.module().build_probe_fixture(repo, destination, "claude-cli")
        self.assertEqual(marker.read_text(), "keep")

    def test_failed_build_does_not_leave_installable_partial_bundle(self) -> None:
        repo = self.source_repo()
        (repo / "skills-query-server/dist/index.js").unlink()
        destination = self.root / "output"
        with self.assertRaises(FileNotFoundError):
            self.module().build_probe_fixture(repo, destination, "claude-cli")
        self.assertFalse(destination.exists())


if __name__ == "__main__":
    unittest.main()
