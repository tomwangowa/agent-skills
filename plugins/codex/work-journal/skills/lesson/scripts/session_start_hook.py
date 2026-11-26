#!/usr/bin/env python3
"""SessionStart hook: load the lesson digest as model context.

Claude Code and Codex accept the same hookSpecificOutput JSON, so one script
serves both runtimes. It always exits 0: a missing or broken lessons folder
must never block a session. Without a lesson configuration it prints nothing,
so installing work-journal does not turn lessons on; a configuration that
exists but cannot be used, or a settings root that cannot be resolved (which
breaks work-journal too), gives a systemMessage instead of silence. The
message names the error, never a path.
"""

from __future__ import annotations

import argparse
import contextlib
import io
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

TITLE = "[lesson — digest loaded by the work-journal SessionStart hook]"
QUOTE = (
    "Begin your first reply with the first line of the digest below, verbatim, "
    "and follow every listed rule this session. If that line starts with "
    "\"lessons: ⚠\", say so in one sentence and continue."
)
RELOAD = (
    "The session was resumed or compacted: keep following every listed rule; "
    "do not quote the digest again."
)
PROPOSE = (
    "When a pitfall is fixed, an assumption is disproved or the user corrects you, "
    "propose at most two lessons at a natural pause and write one only after the "
    "user confirms the exact draft (see the lesson skill)."
)
CONTINUED = {"resume", "compact"}


def read_source() -> str:
    """The SessionStart source (startup, resume, clear, compact); startup when unknown."""
    try:
        if sys.stdin is None or sys.stdin.isatty():
            return "startup"
        data = json.loads(sys.stdin.read() or "{}")
    except Exception:  # noqa: BLE001 - bad input only changes the wording
        return "startup"
    source = data.get("source") if isinstance(data, dict) else None
    return source if isinstance(source, str) else "startup"


def header(source: str) -> str:
    return "\n".join((TITLE, RELOAD if source in CONTINUED else QUOTE, PROPOSE))


def build(source: str) -> str | None:
    import lesson

    path = lesson.config_path()  # raises when the settings root cannot be resolved
    if not path.is_file():
        return None  # lessons not set up: stay silent
    if lesson.load_config() is None:
        raise ValueError("lesson.json is unreadable or has no lessons_dir")
    buffer = io.StringIO()
    with contextlib.redirect_stdout(buffer):
        lesson.cmd_digest(argparse.Namespace(project=None))
    digest = buffer.getvalue().strip()
    return f"{header(source)}\n\n{digest}" if digest else None


def main() -> int:
    source = read_source()
    payload: dict = {}
    try:
        context = build(source)
        if context:
            payload["hookSpecificOutput"] = {
                "hookEventName": "SessionStart",
                "additionalContext": context,
            }
    except Exception as error:  # noqa: BLE001 - any failure must degrade to a warning
        # ValueError text here is fixed wording; other errors can carry a path.
        detail = str(error) if type(error) is ValueError else type(error).__name__
        payload["systemMessage"] = f"lesson digest not loaded ({detail})"
    if payload:
        print(json.dumps(payload, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    sys.exit(main())
