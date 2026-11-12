"""Standard-library installer entry; no noninteractive consent shortcut."""
from __future__ import annotations

import argparse
import sys
from functools import partial
from pathlib import Path

from .catalog import load_catalog
from .ui import native_runner, run
from .selection import select_packages
from .progress import PackageProgress
from .removal_ui import choose_operation, run_removal


def main(argv=None):
    parser = argparse.ArgumentParser(description='Preview and explicitly approve CLI plugin installation.')
    parser.add_argument('--catalog', type=Path, default=Path(__file__).resolve().parents[2] / 'catalog.json')
    args = parser.parse_args(argv)
    try:
        catalog = load_catalog(args.catalog)
    except (OSError, ValueError, KeyError, TypeError) as error:
        print(f'Invalid installer catalog: {error}', file=sys.stderr)
        return 2
    if not sys.stdin.isatty():
        print('Interactive terminal required. No operation was approved or executed.')
        return 2
    progress = PackageProgress(sys.stdout)
    runner = partial(native_runner, on_stderr=progress.native_message, on_wait=progress.pulse)
    operation = choose_operation(input, sys.stdout)
    if operation is None:
        print('Cancelled. No operation executed.')
        return 130
    if operation == 'remove':
        return run_removal(catalog, input, sys.stdout, runner, package_selector=select_packages, progress=progress)
    return run(catalog, input, sys.stdout, runner, package_selector=select_packages, progress=progress)


if __name__ == '__main__':
    raise SystemExit(main())
