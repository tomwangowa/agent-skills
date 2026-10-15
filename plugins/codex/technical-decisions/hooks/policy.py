import json
import sys
from pathlib import Path
try:
    context = Path(__file__).with_name("policy.md").read_text(encoding="utf-8")
    print(json.dumps({"hookSpecificOutput": {"hookEventName": "SessionStart", "additionalContext": context}}))
except (OSError, UnicodeError) as error:
    print(f"Package routing not loaded: {error}", file=sys.stderr)
    raise SystemExit(1)
