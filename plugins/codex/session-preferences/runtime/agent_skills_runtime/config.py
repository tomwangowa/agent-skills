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


def read_response_language(config_root: Path) -> tuple[str | None, list[str]]:
    """Read the optional session-wide response language from shared settings."""
    path = config_root / "agent-skills.json"
    try:
        require_external_personal_path(path)
        settings = json.loads(path.read_text(encoding="utf-8"))
    except FileNotFoundError:
        return None, []
    except (OSError, ValueError, RuntimeError) as error:
        return None, [f"Invalid response language configuration at {path}: {error}"]

    if not isinstance(settings, dict):
        return None, [f"Invalid response language configuration at {path}: expected an object"]
    if "session_preferences" not in settings:
        return None, []

    preferences = settings["session_preferences"]
    if not isinstance(preferences, dict):
        return None, [f"Invalid response language configuration at {path}: session_preferences must be an object"]
    if "response_language" not in preferences:
        return None, []

    language = preferences["response_language"]
    if not isinstance(language, str):
        return None, [f"Invalid response language configuration at {path}: response_language must be a string"]
    language = language.strip()
    if not language:
        return None, [f"Invalid response language configuration at {path}: response_language must not be empty"]
    try:
        language.encode("utf-8")
    except UnicodeEncodeError:
        return None, [f"Invalid response language configuration at {path}: response_language must be valid UTF-8 text"]
    if len(language.splitlines()) != 1:
        return None, [f"Invalid response language configuration at {path}: response_language must be a single line"]
    if len(language) > 80:
        return None, [f"Invalid response language configuration at {path}: response_language must be at most 80 Unicode code points"]
    return language, []
