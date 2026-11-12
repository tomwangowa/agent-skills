#!/usr/bin/env python3
"""Locate the unpacked runtime independently of cwd and user PYTHONPATH."""
from pathlib import Path
import sys

base = Path(__file__).resolve().parent
sys.path.insert(0, str(base / 'runtime'))
from agent_skills_installer.__main__ import main

if __name__ == '__main__':
    raise SystemExit(main(['--catalog', str(base / 'catalog.json'), *sys.argv[1:]]))
