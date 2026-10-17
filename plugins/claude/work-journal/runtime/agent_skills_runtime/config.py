"""Shared path precedence; keep this contract aligned with runtime-config.ts."""
from __future__ import annotations

import json
import os
from pathlib import Path
from typing import Mapping


def require_external_personal_path(path: Path) -> Path:
    """Reject disposable plugin storage, including paths reached through symlink aliases."""
    resolved = path.resolve()
    for parent in [resolved, *resolved.parents]:
        if any((parent / name).is_file() for name in (
                '.claude-plugin/plugin.json', '.codex-plugin/plugin.json', 'plugin.json')):
            raise ValueError('Personal settings and data must be outside plugin caches')
    return path


def resolve_data_path(value: str, base: Path, home: Path) -> Path:
    if not isinstance(value, str) or not value.strip() or "\0" in value:
        raise ValueError("Expected a non-empty data path")
    if value == "~":
        path = home
    elif value.startswith("~/"):
        path = home / value[2:]
    elif value.startswith("~"):
        raise ValueError("Named-user home paths are not supported")
    else:
        path = Path(value)
        if not path.is_absolute():
            path = base / path
    # Node path.resolve is lexical; following /var symlinks here would disagree.
    return Path(os.path.abspath(os.path.normpath(path)))


def resolve_config_root(env: Mapping[str, str], home: Path) -> Path:
    explicit = env.get("AGENT_SKILLS_CONFIG_DIR")
    xdg = env.get("XDG_CONFIG_HOME")
    value = explicit or xdg
    if value:
        if not Path(value).is_absolute() and not value.startswith("~/") and value != "~":
            raise ValueError("Config root must be an absolute or ~/ path")
        root = resolve_data_path(value, home, home)
        return require_external_personal_path(root if explicit else root / "agent-skills")
    return require_external_personal_path(resolve_data_path("~/.config/agent-skills", home, home))


def resolve_activities_dir(env: Mapping[str, str], settings: dict, config_root: Path, home: Path) -> Path:
    sources = settings.get("sources", {})
    if not isinstance(sources, dict):
        raise ValueError("Expected sources settings")
    value = env.get("CLAUDE_ACTIVITIES_DIR") or sources.get("activities")
    return require_external_personal_path(resolve_data_path(value, config_root, home))


def validate_work_journal(settings: object) -> dict:
    if not isinstance(settings, dict) or not isinstance(settings.get("sources"), dict):
        raise ValueError("work-journal.json must contain a sources object")
    sources = settings["sources"]
    activities = sources.get("activities")
    if not isinstance(activities, str) or not activities.strip() or "\0" in activities:
        raise ValueError("sources.activities must be a non-empty path")
    notes = sources.get("notes")
    if not isinstance(notes, dict) or not isinstance(notes.get("paths"), list) or not notes["paths"]:
        raise ValueError("sources.notes.paths must be a non-empty array")
    if any(not isinstance(p, str) or not p.strip() or "\0" in p for p in notes["paths"]):
        raise ValueError("sources.notes.paths must contain non-empty paths")
    for name in ("recursive", "exclude_hidden"):
        if name in notes and not isinstance(notes[name], bool):
            raise ValueError(f"sources.notes.{name} must be boolean")
    return settings


def read_work_journal(config_root: Path) -> dict:
    require_external_personal_path(config_root / 'work-journal.json')
    return validate_work_journal(json.loads((config_root / "work-journal.json").read_text(encoding="utf-8")))
