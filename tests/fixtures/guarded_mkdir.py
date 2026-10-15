#!/usr/bin/env python3
"""A test-only mkdir boundary: legacy scripts must never create real user data."""
import os
import subprocess
import sys
from pathlib import Path

root = Path(os.environ["GUARDED_FIXTURE_ROOT"]).resolve()
for arg in sys.argv[1:]:
    if arg.startswith("-"):
        continue
    if not Path(arg).resolve().is_relative_to(root):
        print("Test guard refused mkdir outside the disposable fixture", file=sys.stderr)
        sys.exit(2)
sys.exit(subprocess.run([os.environ["GUARDED_REAL_MKDIR"], *sys.argv[1:]]).returncode)
