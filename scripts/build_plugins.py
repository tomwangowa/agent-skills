#!/usr/bin/env python3
"""Rebuild managed plugin directories; compare without touching them with --check."""
from __future__ import annotations

import argparse
import json
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from scripts.plugin_packaging.catalog import load_packages
from scripts.plugin_packaging.render import digest, render_marketplaces, render_package, write_json
from scripts.plugin_packaging.resources import collect_resources
from scripts.probe_plugin_runtimes import validate_runtime_contracts


def prepare_server(root: Path, destination: Path) -> None:
    """Compile in a disposable workspace and install lockfile-only production dependencies."""
    source = root / 'skills-query-server'
    compiler = source / 'node_modules/typescript/bin/tsc'
    if not compiler.is_file():
        raise ValueError('Install source development dependencies before building release artifacts')
    destination.mkdir()
    journal = next(p for p in load_packages(root) if p['name'] == 'work-journal')
    for path in collect_resources(root, journal):
        if path.is_relative_to(source):
            target = destination / path.relative_to(source)
            target.parent.mkdir(parents=True, exist_ok=True)
            shutil.copyfile(path, target)
    for name in ['package.json', 'package-lock.json', 'tsconfig.json', 'src/index.ts']:
        if not (destination / name).is_file():
            raise ValueError(f'Missing whitelisted server build input: {name}')
    (destination / 'node_modules').symlink_to(source / 'node_modules', target_is_directory=True)
    try:
        subprocess.run(['node', str(compiler), '--project', str(destination / 'tsconfig.json')], check=True)
    finally:
        (destination / 'node_modules').unlink()
    subprocess.run(['npm', 'ci', '--omit=dev', '--ignore-scripts', '--no-fund',
                    '--cache', str(destination.parent / 'npm-cache')], cwd=destination, check=True)
    # Executable symlinks are for npm commands, not the server's Node imports.
    shutil.rmtree(destination / 'node_modules/.bin', ignore_errors=True)
    # npm's hidden lockfile is npm-only bookkeeping the server does not load; omit it from releases.
    (destination / 'node_modules/.package-lock.json').unlink(missing_ok=True)
    for path in (destination / 'node_modules').rglob('*'):
        if path.is_symlink():
            raise ValueError(f'Unexpected production dependency symlink: {path.relative_to(destination)}')
    if any((destination / 'node_modules' / name).exists() for name in ['tsx', 'typescript', 'vitest']):
        raise ValueError('Development dependencies must not enter a release')
    shutil.rmtree(destination / 'src')
    (destination / 'tsconfig.json').unlink()
    for path in (destination / 'dist').rglob('*.d.ts'):
        path.unlink()


def _tree(root: Path) -> dict:
    result = {}
    if root.is_symlink():
        raise ValueError(f'Symlink output is forbidden: {root.name}')
    if not root.exists():
        return result
    for path in root.rglob('*'):
        if path.is_symlink():
            raise ValueError(f'Symlink output is forbidden: {path.relative_to(root)}')
        if path.is_file():
            result[path.relative_to(root).as_posix()] = (digest(path), path.stat().st_mode & 0o777)
    return result


def build(root: Path, *, check: bool) -> list[str]:
    """Stage a complete rebuild before replacing only explicitly managed package paths."""
    contracts_path = root / 'docs/validation/skill-plugins/runtime-contracts.json'
    errors = validate_runtime_contracts(contracts_path)
    if errors:
        raise ValueError('; '.join(errors))
    contracts = json.loads(contracts_path.read_text())
    packages = load_packages(root)
    for parent in [root / 'plugins', root / 'plugins/claude', root / 'plugins/codex',
                   root / '.claude-plugin', root / '.agents', root / '.agents/plugins']:
        if parent.is_symlink():
            raise ValueError('Managed output parent must not be a symlink')
    with tempfile.TemporaryDirectory(prefix='agent-skills-build-') as tmp:
        staging = Path(tmp).resolve()
        server = staging / 'server'
        prepare_server(root, server)
        managed = []
        for surface in ['claude', 'codex']:
            for package in packages:
                relative = Path('plugins') / surface / package['name']
                render_package(root, package, surface, staging / relative, contracts, server_bundle=server)
                managed.append(relative)
        claude, codex = render_marketplaces(root, packages)
        for relative, data in [(Path('.claude-plugin/marketplace.json'), claude),
                               (Path('.agents/plugins/marketplace.json'), codex)]:
            write_json(staging / relative, data)
            managed.append(relative)
        differences = []
        for relative in managed:
            expected, actual = staging / relative, root / relative
            if actual.is_symlink():
                raise ValueError(f'Symlink output is forbidden: {relative}')
            if expected.is_dir():
                existing = _tree(actual)
                if existing != _tree(expected):
                    differences.append(str(relative))
                if not check and actual.exists():
                    inventory = actual / '.generated-files.json'
                    if not inventory.is_file():
                        raise ValueError(f'Refusing to replace an unmanaged directory: {relative}')
                    known = set(json.loads(inventory.read_text())['files']) | {'.generated-files.json'}
                    if set(existing) - known:
                        raise ValueError(f'Refusing to delete unexpected files in {relative}')
            elif not actual.is_file() or actual.read_bytes() != expected.read_bytes():
                differences.append(str(relative))
        if not check:
            for relative in managed:
                expected, actual = staging / relative, root / relative
                actual.parent.mkdir(parents=True, exist_ok=True)
                if expected.is_dir():
                    if actual.exists():
                        shutil.rmtree(actual)
                    shutil.copytree(expected, actual)
                else:
                    shutil.copyfile(expected, actual)
        return differences


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    group = parser.add_mutually_exclusive_group(required=True)
    group.add_argument('--write', action='store_true')
    group.add_argument('--check', action='store_true')
    parser.add_argument('--repo-root', type=Path, default=Path(__file__).resolve().parents[1])
    args = parser.parse_args(argv)
    try:
        differences = build(args.repo_root.resolve(), check=args.check)
    except (OSError, ValueError, KeyError, subprocess.CalledProcessError) as error:
        print(f'Plugin build failed: {error}', file=sys.stderr)
        return 1
    if args.check and differences:
        print('Stale or missing generated outputs: ' + ', '.join(differences), file=sys.stderr)
        return 1
    print('Generated outputs match source' if args.check else 'Generated 14 native CLI packages and two marketplaces')
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
