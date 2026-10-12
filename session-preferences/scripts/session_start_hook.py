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
    except (OSError, ValueError):
        return None, f"session-preferences: cannot read {index}; rules were not loaded."
    if not names:
        return None, f"session-preferences: {index} lists no modules; rules were not loaded."

    sections: list[str] = []
    missing: list[str] = []
    for name in names:
        path = REFERENCES / name
        try:
            sections.append(f"<!-- module: {name} -->\n{path.read_text(encoding='utf-8').strip()}")
        except (OSError, ValueError):
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
