"""Collect files named in the package whitelist; never walk a directory for shipping."""
from __future__ import annotations

from pathlib import Path, PurePosixPath

PRIVATE_NAMES = frozenset({'config.json', 'work-journal.json', '.base-hashes.json',
                           '.skill-sync-targets', 'hooks.state', 'auth.json'})
DEVELOPMENT_PARTS = frozenset({'tests', '__pycache__', 'node_modules', '.git', '.superpowers',
                               'docs', 'validation', 'activities', 'logs'})


def collect_resources(repo_root: Path, package: dict) -> list[Path]:
    """Resolve explicit regular files, rejecting private files, traversal and all symlinks."""
    root = repo_root.resolve()
    declared = [f'{skill}/SKILL.md' for skill in package['skills']] + package['runtime_resources']
    if len(declared) != len(set(declared)):
        raise ValueError('Resource whitelist contains duplicates')
    paths = []
    for name in declared:
        if not isinstance(name, str) or not name:
            raise ValueError('Resource path must be a nonempty string')
        relative = PurePosixPath(name)
        if (relative.is_absolute() or any(part in {'..', '.'} for part in name.split('/'))
                or '\\' in name or name.startswith('~') or '//' in name):
            raise ValueError(f'Resource must be repo-relative: {name}')
        public_docs = relative.parts[:2] == ('docs', 'plugins')
        if (relative.name in PRIVATE_NAMES or relative.name.startswith('.env')
                or any(part in DEVELOPMENT_PARTS for part in (relative.parts[2:] if public_docs else relative.parts))
                or relative.name.endswith(('.pyc', '.log', '.test.ts', '.test.mjs'))):
            raise ValueError(f'Private or development resource is forbidden: {name}')
        path = root.joinpath(*relative.parts)
        for ancestor in (path, *path.parents):
            if ancestor == root:
                break
            if ancestor.is_symlink():
                raise ValueError(f'Symlink resource is forbidden: {name}')
        if not path.is_file() or not path.resolve().is_relative_to(root):
            raise ValueError(f'Missing or unsafe resource: {name}')
        paths.append(path)
    return sorted(paths)
