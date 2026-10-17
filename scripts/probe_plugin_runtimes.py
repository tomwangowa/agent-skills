#!/usr/bin/env python3
"""Build disposable, self-contained plugin probes and validate recorded evidence."""

from __future__ import annotations

import argparse
import hashlib
import json
import os
import shutil
import sys
import tempfile
import uuid
from pathlib import Path


SURFACES = ("claude-cli", "codex-cli")
EVENTS = ("startup", "resume", "clear", "compact")
TOOLS = {"dashboard", "log_activity", "query_activities", "query_decisions",
         "query_timeline", "query_todos", "search"}
PLUGIN_SCHEMA = "https://agent-plugins.org/schemas/1.0.0/plugin.schema.json"
MCP_SCHEMA = "https://agent-plugins.org/schemas/1.0.0/mcp.schema.json"


def _read_json(path: Path) -> dict:
    value = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(value, dict):
        raise ValueError(f"Expected a JSON object: {path}")
    return value


def validate_runtime_contracts(path: Path) -> list[str]:
    """Reject incomplete observations, missing tool behavior, and changed evidence."""
    try:
        payload = _read_json(path)
    except (OSError, ValueError) as error:
        return [f"Runtime contract is incomplete: {error}"]
    if payload.get("schema_version") != 1 or not isinstance(payload.get("surfaces"), dict):
        return ["Runtime contract is incomplete: expected schema_version 1 and surfaces"]
    errors = []
    for surface in SURFACES:
        record = payload["surfaces"].get(surface)
        if not isinstance(record, dict):
            errors.append(f"{surface}: missing observation")
            continue
        if record.get("status") != "verified":
            errors.append(f"{surface}: not verified ({record.get('status', 'missing')})")
        for key in ("client_version", "manifest_format", "superpowers_version"):
            if not isinstance(record.get(key), str) or not record[key].strip():
                errors.append(f"{surface}: missing {key}")
        mcp = record.get("mcp_launch", {})
        if not isinstance(mcp, dict):
            mcp = {}
        if mcp.get("status") != "verified" or mcp.get("round_trip") is not True:
            errors.append(f"{surface}: MCP round trip not verified")
        isolation = mcp.get("fixture_isolation", {})
        if not isinstance(isolation, dict) or isolation.get("status") != "verified":
            errors.append(f"{surface}: fixture isolation not verified")
        observed = mcp.get("tools", [])
        if not isinstance(observed, list) or not all(isinstance(item, str) for item in observed):
            observed = []
        if not TOOLS.issubset(observed):
            errors.append(f"{surface}: missing MCP tools: {', '.join(sorted(TOOLS - set(observed)))}")
        if not isinstance(mcp.get("command"), str) or not mcp["command"].strip():
            errors.append(f"{surface}: missing MCP launch command")
        if not isinstance(mcp.get("args"), list) or not all(isinstance(a, str) for a in mcp["args"]):
            errors.append(f"{surface}: missing MCP launch arguments")
        events = record.get("hook_events", {})
        if not isinstance(events, dict):
            events = {}
        for event in EVENTS:
            if events.get(event) != "verified":
                errors.append(f"{surface}: SessionStart {event} not verified")
        routing = record.get("routing_result", {})
        if not isinstance(routing, dict):
            routing = {}
        if (routing.get("status") != "verified" or routing.get("preference_off") is not True
                or routing.get("native_reviewer") is not True):
            errors.append(f"{surface}: routing and preference-off behavior not verified")
        evidence = record.get("evidence")
        if not isinstance(evidence, list) or not evidence:
            errors.append(f"{surface}: missing recorded evidence")
            continue
        for item in evidence:
            if not isinstance(item, dict) or not isinstance(item.get("path"), str) or not item["path"]:
                errors.append(f"{surface}: invalid evidence reference")
                continue
            artifact = path.parent / item["path"]
            try:
                actual = hashlib.sha256(artifact.read_bytes()).hexdigest()
            except OSError as error:
                errors.append(f"{surface}: unreadable evidence: {error}")
                continue
            if actual != item.get("sha256"):
                errors.append(f"{surface}: evidence checksum mismatch: {item['path']}")
    return errors


def _copy_tree(source: Path, target: Path) -> None:
    # Refuse external links before copytree can turn private files into package files.
    if source.is_symlink() or any(path.is_symlink() for path in source.rglob("*")):
        raise ValueError(f"Symlink is not allowed in probe resources: {source}")
    if not source.is_dir():
        raise FileNotFoundError(source)
    shutil.copytree(source, target, ignore=shutil.ignore_patterns(
        "__pycache__", "*.pyc", "*.test.*", "*.d.ts", "*.map"))


def _write_json(path: Path, payload: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")


def build_probe_fixture(repo_root: Path, destination: Path, surface: str,
                        manifest_format: str = "portable") -> Path:
    """Create a relocatable bundle without source-private configuration or dev dependencies."""
    if surface not in SURFACES:
        raise ValueError(f"Unknown surface: {surface}")
    if manifest_format not in ("portable", "legacy"):
        raise ValueError(f"Unknown manifest format: {manifest_format}")
    repo_root, destination = repo_root.resolve(), destination.absolute()
    if destination.exists() or destination.is_symlink():
        raise FileExistsError(destination)
    source_server = repo_root / "skills-query-server"
    if not (source_server / "dist/index.js").is_file():
        raise FileNotFoundError("Compile skills-query-server before building a probe")
    destination.parent.mkdir(parents=True, exist_ok=True)
    staging = Path(tempfile.mkdtemp(prefix=".plugin-probe-", dir=destination.parent))
    try:
        plugin = f"skill-plugins-probe-{surface}"
        _copy_tree(repo_root / "runtime", staging / "runtime")
        server_name = "agent_skills_probe_" + surface.replace("-", "_")
        reviewer = "code-review-claude" if surface == "claude-cli" else "code-review-codex"
        for name in ("session-preferences", "control-return", "brainstorming", "completion-gate", reviewer):
            source = repo_root / name
            target = staging / "skills" / name
            target.mkdir(parents=True)
            if (source / "SKILL.md").is_symlink():
                raise ValueError(f"Symlink is not allowed: {source / 'SKILL.md'}")
            shutil.copy2(source / "SKILL.md", target / "SKILL.md")
            for resource in ("scripts", "references", "assets", "agents"):
                if (source / resource).exists():
                    _copy_tree(source / resource, target / resource)
        server = staging / "server"
        server.mkdir()
        shutil.copy2(source_server / "scripts/probe_server.mjs", server / "probe_server.mjs")
        _write_json(server / "probe-identity.json", {
            "plugin": plugin, "surface": surface, "probe_id": uuid.uuid4().hex,
        })
        _copy_tree(source_server / "dist", server / "dist")
        _write_json(server / "package.json", {"type": "module"})
        lock = _read_json(source_server / "package-lock.json")
        for relative, metadata in lock.get("packages", {}).items():
            if not relative or metadata.get("dev"):
                continue
            parts = Path(relative).parts
            if parts[0] != "node_modules" or ".." in parts or Path(relative).is_absolute():
                raise ValueError(f"Invalid dependency path: {relative}")
            installed = source_server / relative
            if not installed.exists() and metadata.get("optional"):
                continue
            target = server / relative
            target.parent.mkdir(parents=True, exist_ok=True)
            _copy_tree(installed, target)
        for relative in ("data/activities", "data/notes"):
            (staging / relative).mkdir(parents=True)
        _write_json(server / "config.json", {"sources": {
            "activities": "../data/activities",
            "notes": {"paths": ["../data/notes"], "recursive": True, "exclude_hidden": True},
        }})
        (server / "launch.mjs").write_text(
            "import { fileURLToPath } from 'node:url';\n"
            "// Keep relative fixture data independent of the host's working directory.\n"
            "process.chdir(fileURLToPath(new URL('.', import.meta.url)));\n"
            "await import('./probe_server.mjs');\n", encoding="utf-8")
        hooks = staging / "hooks"
        hooks.mkdir()
        policy = (f"Runtime probe routing: use {plugin}:brainstorming for exploration; "
                  f"use {plugin}:completion-gate for completion verification; "
                  f"use {plugin}:{reviewer} for native review. Respect higher-priority instructions.")
        (hooks / "policy.md").write_text(policy + "\n", encoding="utf-8")
        (hooks / "routing.py").write_text(
            "import json\nfrom pathlib import Path\n"
            "context = Path(__file__).with_name('policy.md').read_text(encoding='utf-8')\n"
            "print(json.dumps({'hookSpecificOutput': {'hookEventName': 'SessionStart', "
            "'additionalContext': context}}))\n", encoding="utf-8")
        commands = ["skills/session-preferences/scripts/session_start_hook.py",
                    "skills/control-return/scripts/session_start_hook.py", "hooks/routing.py"]
        _write_json(hooks / "hooks.json", {"hooks": {"SessionStart": [{
            "matcher": "startup|resume|clear|compact",
            "hooks": [{"type": "command", "command": f'python3 "${{CLAUDE_PLUGIN_ROOT}}/{script}"'}
                      for script in commands],
        }]}})
        identity = {"name": plugin, "version": "0.0.4",
                    "description": "Disposable local plugin runtime probe"}
        if surface == "claude-cli":
            _write_json(staging / ".claude-plugin/plugin.json", identity)
            _write_json(staging / ".mcp.json", {"mcpServers": {server_name: {
                "command": "node", "args": ["${CLAUDE_PLUGIN_ROOT}/server/launch.mjs"],
            }}})
        elif manifest_format == "legacy":
            # Codex 0.162.1 skips hooks for Agent Plugins manifests, even with an overlay.
            _write_json(staging / ".codex-plugin/plugin.json", {
                **identity, "skills": "./skills/", "hooks": "./hooks/hooks.json",
            })
            _write_json(staging / ".mcp.json", {"mcpServers": {server_name: {
                "command": "node", "args": ["launch.mjs"], "cwd": "./server/",
            }}})
        else:
            _write_json(staging / "plugin.json", {"$schema": PLUGIN_SCHEMA, **identity,
                "extensions": {"com.openai": {"hooks": "./hooks/hooks.json"}}})
            _write_json(staging / "mcp.json", {"$schema": MCP_SCHEMA, "mcpServers": {server_name: {
                "type": "stdio", "command": "node", "args": ["launch.mjs"], "cwd": "./server/",
            }}})
        if destination.exists():
            raise FileExistsError(destination)
        staging.rename(destination)
        return destination
    finally:
        if staging.exists():
            shutil.rmtree(staging)


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    commands = parser.add_subparsers(dest="command", required=True)
    build = commands.add_parser("build")
    build.add_argument("--surface", choices=SURFACES, required=True)
    build.add_argument("--manifest-format", choices=("portable", "legacy"), default="portable")
    build.add_argument("--destination", type=Path, required=True)
    build.add_argument("--repo-root", type=Path, default=Path(__file__).resolve().parents[1])
    check = commands.add_parser("check-contract")
    check.add_argument("path", type=Path)
    args = parser.parse_args(argv)
    try:
        if args.command == "build":
            print(build_probe_fixture(args.repo_root, args.destination, args.surface, args.manifest_format))
            return 0
        errors = validate_runtime_contracts(args.path)
        if errors:
            print("\n".join(errors), file=sys.stderr)
            return 1
        print("Both CLI runtime contracts are verified against recorded evidence.")
        return 0
    except (OSError, ValueError, TypeError) as error:
        print(f"Probe failed: {error}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    sys.exit(main())
