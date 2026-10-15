#!/usr/bin/env python3
"""Check artifact integrity. Native acceptance and vulnerability gates remain separate."""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from scripts.plugin_packaging.verify import verify_release, verify_acceptance
from scripts.probe_plugin_runtimes import validate_runtime_contracts


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--repo-root', type=Path, default=Path(__file__).resolve().parents[1])
    parser.add_argument('--require-acceptance', action='store_true', help='Also require current native and production-security evidence')
    args = parser.parse_args(argv)
    root = args.repo_root.resolve()
    path = root / 'docs/validation/skill-plugins/runtime-contracts.json'
    try:
        errors = validate_runtime_contracts(path)
        errors.extend(verify_release(root, json.loads(path.read_text())))
        if args.require_acceptance:
            errors.extend(verify_acceptance(root, json.loads((root / 'docs/validation/skill-plugins/acceptance.json').read_text())))
    except (OSError, ValueError) as error:
        errors = [str(error)]
    for error in errors:
        print(error, file=sys.stderr)
    if not errors:
        print('Artifact integrity checks passed; native host acceptance and dependency security are separate gates')
    return int(bool(errors))


if __name__ == '__main__':
    raise SystemExit(main())
