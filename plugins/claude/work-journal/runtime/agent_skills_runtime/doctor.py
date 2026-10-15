"""Read-only checks scoped to the components a selected package actually needs."""
from __future__ import annotations

import argparse
import json
import os
import shutil
from pathlib import Path

from .config import read_work_journal, resolve_config_root


def check_environment(config_root: Path, requirements: dict) -> list[dict]:
    results = []
    for command in requirements.get("commands", []):
        found = shutil.which(command)
        results.append({"component": command, "status": "ok" if found else "missing",
                        "message": "Available" if found else f"Install {command} for the selected package"})
    for name in requirements.get("config", []):
        if name == "work-journal":
            try:
                read_work_journal(config_root)
                status, message = "ok", "Settings are valid; data contents were not read"
            except FileNotFoundError:
                status, message = "missing", "Run work-journal setup with your selected data directories"
            except (OSError, ValueError):
                status, message = "invalid", "Fix work-journal.json before starting the server"
        elif name == "preferences":
            status, message = "ok", "Packaged defaults are available; personal overrides are optional"
            if requirements.get("preferences_defaults"):
                from .preferences import check_preference_updates, load_preferences
                defaults = Path(requirements["preferences_defaults"])
                _, warnings = load_preferences(defaults, config_root)
                if warnings:
                    status, message = "invalid", "; ".join(warnings)
                control_skill = requirements.get("control_return_skill")
                results.extend(check_preference_updates(defaults, config_root,
                                                        Path(control_skill) if control_skill else None))
        else:
            status, message = "unsupported", f"Unknown config component: {name}"
        results.append({"component": name, "status": status, "message": message})
    return results


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--config-root", type=Path)
    parser.add_argument("--commands", nargs="*", default=[])
    parser.add_argument("--config", nargs="*", default=[])
    parser.add_argument("--preferences-defaults", type=Path)
    parser.add_argument("--control-return-skill", type=Path)
    args = parser.parse_args(argv)
    env = dict(os.environ)
    if args.config_root is not None:
        env['AGENT_SKILLS_CONFIG_DIR'] = str(args.config_root)
    try:
        root = resolve_config_root(env, Path.home())
    except (OSError, ValueError) as error:
        parser.exit(1, f"Doctor failed: {error}\n")
    results = check_environment(root,
                                {"commands": args.commands, "config": args.config,
                                 "preferences_defaults": args.preferences_defaults,
                                 "control_return_skill": args.control_return_skill})
    print(json.dumps(results))
    return int(any(r["status"] != "ok" for r in results))


if __name__ == "__main__":
    raise SystemExit(main())
