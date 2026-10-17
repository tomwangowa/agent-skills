"""Resolve shared journal paths; stdout is reserved for the selected path."""
from __future__ import annotations

import argparse
import os
import sys
from pathlib import Path

from .config import read_work_journal, resolve_activities_dir, resolve_config_root


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--config-root", type=Path)
    parser.add_argument("command", choices=["activities-dir", "config-root"])
    args = parser.parse_args(argv)
    try:
        env = dict(os.environ)
        if args.config_root:
            env["AGENT_SKILLS_CONFIG_DIR"] = str(args.config_root)
        root = resolve_config_root(env, Path.home())
        if args.command == "config-root":
            print(root)
        else:
            settings = read_work_journal(root)
            print(resolve_activities_dir(env, settings, root, Path.home()))
        return 0
    except (OSError, ValueError) as error:
        print(f"Journal settings error: {error}. Run work-journal setup with your selected activity and note directories.", file=sys.stderr)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
