#!/usr/bin/env python3
"""SessionStart hook: inject the control-return rule as model context.

The rule text is extracted from SKILL.md so the skill file stays the single
source of truth. Always exits 0; problems surface through systemMessage.
"""

from __future__ import annotations

import json
import os
import re
import sys
from pathlib import Path

# Resolved from this file so each runtime reads its own installed copy.
SKILL_MD = Path(__file__).resolve().parent.parent / "SKILL.md"
OFF_VARIABLE = "AGENT_SESSION_PREFS"

HEADER = (
    "[control-return — auto-applied by SessionStart hook]\n"
    "Apply the following rule for this session. Do not announce activation.\n"
    "If it conflicts with the active output style, CLAUDE.md, or AGENTS.md, "
    "those take precedence."
)

# The first ```text block inside the "## Rule" section, before the next "## " heading.
RULE_BLOCK = re.compile(
    r"^## Rule[ \t]*\n(?:(?!^## ).)*?^```text[ \t]*\n(.*?)^```", re.DOTALL | re.MULTILINE
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
    try:
        text = SKILL_MD.read_text(encoding="utf-8")
    except (OSError, ValueError):
        return None, f"control-return: cannot read {SKILL_MD}; rule was not loaded."
    match = RULE_BLOCK.search(text)
    if not match or not match.group(1).strip():
        return None, f"control-return: no ```text block under '## Rule' in {SKILL_MD}; rule was not loaded."
    return f"{HEADER}\n\n{match.group(1).strip()}", None


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
        context, warning = None, f"control-return hook failed: {error}"
    emit(context, warning)
    return 0


if __name__ == "__main__":
    sys.exit(main())
