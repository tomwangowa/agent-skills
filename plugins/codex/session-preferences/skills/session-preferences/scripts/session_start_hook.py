#!/usr/bin/env python3
"""SessionStart hook: inject the session-preferences modules as model context.

Claude Code and Codex accept the same hookSpecificOutput JSON, so one script
serves both runtimes. It always exits 0 because a broken rule file must never
block a session from starting; problems surface through systemMessage instead.
"""

from __future__ import annotations

import json
import os
import sys
from pathlib import Path

# Resolved from this file so each runtime reads its own installed copy.
SKILL_DIR = Path(__file__).resolve().parent.parent
REFERENCES = SKILL_DIR / "references"
OFF_VARIABLE = "AGENT_SESSION_PREFS"

HEADER_BASE = (
    "[session-preferences — auto-applied by SessionStart hook]\n"
    "This injection is the user's activation of session-preferences; treat the policy as enabled.\n"
    "Apply the following modules for this session. Do not announce activation."
)
HEADER = (HEADER_BASE + "\n"
          "If they conflict with the active output style, CLAUDE.md, or AGENTS.md, those take precedence.")
CONFIGURED_LANGUAGE_HEADER = (HEADER_BASE + "\n"
                              "The configured response language below overrides general language defaults only; "
                              "keep other applicable instructions active.")


def language_directive(language: str) -> str:
    """Describe the configured default without weakening scoped output rules."""
    value = json.dumps(language, ensure_ascii=False)
    return (
        "[session-preferences — response-language default]\n"
        f"Use the configured response_language value {value} as the default language for general response prose this session.\n"
        "The user's explicit language request for the current response or requested output takes precedence.\n"
        "This setting overrides general language defaults in output styles, CLAUDE.md, AGENTS.md, and "
        "session-preferences modules only. Keep applicable tone, format, terminology, and task-specific "
        "requirements active, including language requirements scoped to an artifact."
    )


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
    # Source skills live under the repo; packaged skills live under plugin/skills.
    skill_dir = SKILL_DIR
    package_root = skill_dir.parent
    # Flat mirrors are also named skills; only native manifests identify plugin nesting.
    if package_root.name == "skills" and any(
            (package_root.parent / marker).is_file() for marker in
            (".claude-plugin/plugin.json", ".codex-plugin/plugin.json")):
        package_root = package_root.parent
    runtime = package_root / "runtime"
    if not (runtime / "agent_skills_runtime/preferences.py").is_file():
        raise RuntimeError("Bundled preference runtime is missing; rules were not loaded")
    sys.path.insert(0, str(runtime))
    from agent_skills_runtime.config import read_response_language, resolve_config_root
    from agent_skills_runtime.preferences import load_preferences
    config_root = resolve_config_root(os.environ, Path.home())
    preference_context, warnings = load_preferences(REFERENCES, config_root)
    language, config_warnings = read_response_language(config_root)
    warnings.extend(config_warnings)

    if language:
        sections = [CONFIGURED_LANGUAGE_HEADER, language_directive(language)]
        if preference_context:
            sections.append(preference_context)
        context = "\n\n".join(sections)
    else:
        context = f"{HEADER}\n\n{preference_context}" if preference_context else None

    return (context, "session-preferences: " + "; ".join(warnings) if warnings else None)


def main() -> int:
    if os.environ.get(OFF_VARIABLE, "").lower() == "off":
        return 0
    try:
        if sys.stdin is not None and not sys.stdin.isatty():
            sys.stdin.read()  # Drain hook input; its content does not change the output.
    except Exception:  # noqa: BLE001 - the input is unused, so a bad stream is harmless
        pass
    try:
        context, warning = build()
    except Exception as error:  # noqa: BLE001 - any failure must degrade to a warning
        context, warning = None, f"session-preferences hook failed: {error}"
    emit(context, warning)
    return 0


if __name__ == "__main__":
    sys.exit(main())
