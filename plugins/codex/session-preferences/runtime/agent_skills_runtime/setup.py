"""Explicit first-run setup; existing settings are never overwritten implicitly."""
from __future__ import annotations

import argparse
import json
import os
import tempfile
from pathlib import Path

from .config import (read_work_journal, resolve_config_root, resolve_data_path,
                     validate_work_journal, require_external_personal_path)


def setup_work_journal(config_root: Path, activities: Path, notes: list[Path]) -> Path:
    config_root = resolve_config_root({'AGENT_SKILLS_CONFIG_DIR': str(config_root)}, Path.home())
    activities = resolve_data_path(str(activities), config_root, Path.home())
    notes = [resolve_data_path(str(p), config_root, Path.home()) for p in notes]
    path = config_root / "work-journal.json"
    settings = {"sources": {"activities": str(activities), "notes": {
        "paths": [str(p) for p in notes], "recursive": True, "exclude_hidden": True,
    }}}
    validate_work_journal(settings)
    for selected in [path, activities, *notes]:
        require_external_personal_path(selected)
    if path.exists():
        read_work_journal(config_root)
        return path
    config_root.mkdir(parents=True, exist_ok=True)
    for directory in [activities, *notes]:
        directory.mkdir(parents=True, exist_ok=True)
    descriptor, temporary = tempfile.mkstemp(prefix=".work-journal-", dir=config_root)
    try:
        with os.fdopen(descriptor, "w", encoding="utf-8") as output:
            json.dump(settings, output, indent=2)
            output.write("\n")
            output.flush()
            os.fsync(output.fileno())
        try:
            # A hard link installs a complete file without replacing a racing setup.
            os.link(temporary, path)
        except FileExistsError:
            read_work_journal(config_root)
        return path
    finally:
        Path(temporary).unlink(missing_ok=True)


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--config-root", type=Path)
    parser.add_argument("--activities", type=Path, required=True)
    parser.add_argument("--notes", type=Path, nargs="+", required=True)
    parser.add_argument("--preview", action="store_true")
    args = parser.parse_args(argv)
    env = dict(os.environ)
    if args.config_root is not None:
        env['AGENT_SKILLS_CONFIG_DIR'] = str(args.config_root)
    try:
        root = resolve_config_root(env, Path.home())
    except (OSError, ValueError) as error:
        parser.exit(1, f"Setup failed: {error}\n")
    activities = resolve_data_path(str(args.activities), root, Path.home())
    notes = [resolve_data_path(str(p), root, Path.home()) for p in args.notes]
    proposed = {"sources": {"activities": str(activities), "notes": {
        "paths": [str(p) for p in notes], "recursive": True, "exclude_hidden": True,
    }}}
    try:
        for selected in [root / 'work-journal.json', activities, *notes]:
            require_external_personal_path(selected)
        path = root / "work-journal.json"
        exists = path.exists()
        current = read_work_journal(root) if exists else None
        if args.preview or exists:
            print(json.dumps({"status": "preserved" if exists else "preview",
                              "current": current, "proposed": proposed}))
        else:
            print(json.dumps({"status": "created", "path": str(setup_work_journal(root, activities, notes))}))
        return 0
    except (OSError, ValueError) as error:
        parser.exit(1, f"Setup failed: {error}\n")


if __name__ == "__main__":
    raise SystemExit(main())
