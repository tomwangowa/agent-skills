"""Preview selected legacy configuration edits, then back up, apply and restore them."""
from __future__ import annotations

import hashlib
import argparse
import json
import os
import re
import shlex
import tempfile
import tomllib
import uuid
from pathlib import Path

PACKAGES = {'quality-gates', 'technical-decisions', 'repo-workflow', 'content-tools',
            'work-journal', 'session-preferences', 'skill-toolbox'}


def _hash(content: bytes) -> str:
    return hashlib.sha256(content).hexdigest()


def _plan_hash(plan: dict) -> str:
    fields = {k: v for k, v in plan.items() if k not in {'confirmed', 'preview_hash'}}
    return _hash(json.dumps(fields, sort_keys=True, ensure_ascii=False).encode())


def _safe_file(path: Path, *, allow_missing: bool = False) -> Path:
    if (not path.is_absolute() or path.is_symlink()
            or (not path.is_file() and (not allow_missing or path.exists()))):
        raise ValueError('Configuration must be an explicit absolute regular file, not a symlink')
    resolved = path.resolve()
    _outside_plugin(resolved)
    return resolved


def _outside_plugin(path: Path) -> None:
    for parent in [path.parent, *path.parents]:
        if any((parent / name).is_file() for name in ['.claude-plugin/plugin.json', '.codex-plugin/plugin.json', 'plugin.json']):
            raise ValueError('Migration targets and backups must be outside plugin caches')


def _legacy(command: str | list[str], roots: list[str], component: str) -> bool:
    try:
        tokens = shlex.split(command) if isinstance(command, str) else command
    except ValueError:
        return False
    if (not isinstance(tokens, list) or not tokens or not all(isinstance(t, str) for t in tokens)
            or Path(tokens[0]).name not in {'python', 'python3', 'bash', 'sh', 'node', 'npx', 'npm', 'tsx'}):
        return False
    return any(str(Path(token).expanduser()).startswith(f'{root.rstrip("/")}/{component}/')
               for token in tokens[1:] for root in roots)


def _edit_json(text: str, item: dict, selected: set[str]) -> tuple[str, list[dict]]:
    data = json.loads(text)
    if not isinstance(data, dict):
        raise ValueError('Settings JSON must be an object')
    changes = []
    roots = item.get('legacy_roots', [])
    if 'session-preferences' in selected:
        hooks = data.get('hooks', {})
        if not isinstance(hooks, dict):
            raise ValueError('Unsupported hooks structure')
        for event, groups in hooks.items():
            if not isinstance(groups, list):
                raise ValueError('Unsupported hook group structure')
            remaining_groups = []
            for group in groups:
                if not isinstance(group, dict) or not isinstance(group.get('hooks'), list):
                    raise ValueError('Unsupported hook command structure')
                remaining, removed = [], False
                for hook in group['hooks']:
                    command = hook.get('command', '') if isinstance(hook, dict) else ''
                    matched = [s for s in ['session-preferences', 'control-return'] if _legacy(command, roots, s)]
                    if matched:
                        removed = True
                        changes.append({'component': matched[0], 'selector': f'hooks.{event}', 'action': 'remove_entry'})
                    else:
                        remaining.append(hook)
                if remaining or not removed:
                    remaining_groups.append({**group, 'hooks': remaining})
            hooks[event] = remaining_groups
    if 'work-journal' in selected:
        servers = data.get('mcpServers', {})
        if not isinstance(servers, dict):
            raise ValueError('Unsupported MCP structure')
        name = item.get('legacy_server_name', 'skills-query')
        server = servers.get(name, {})
        if isinstance(server, dict):
            command = [server.get('command', ''), *server.get('args', [])]
            if _legacy(command, roots, 'skills-query-server'):
                del servers[name]
                changes.append({'component': 'work-journal', 'selector': f'mcpServers.{name}', 'action': 'remove_entry'})
    return (json.dumps(data, ensure_ascii=False, indent=2) + '\n' if changes else text), changes


def _edit_toml(text: str, item: dict, selected: set[str]) -> tuple[str, list[dict]]:
    data = tomllib.loads(text)
    if 'work-journal' not in selected:
        return text, []
    name = item.get('legacy_server_name', 'skills-query')
    server = data.get('mcp_servers', {}).get(name, {})
    command = [server.get('command', ''), *server.get('args', [])]
    if not _legacy(command, item.get('legacy_roots', []), 'skills-query-server'):
        return text, []
    if '\"\"\"' in text or "'''" in text:
        raise ValueError('Multiline TOML strings require an explicit reviewed edit')
    lines, keep, output = text.splitlines(keepends=True), True, []
    for line in lines:
        if re.match(r'^\s*\[', line):
            header = tomllib.loads(line)
            keep = name not in header.get('mcp_servers', {})
        if keep:
            output.append(line)
    updated = ''.join(output)
    parsed = tomllib.loads(updated)
    expected = dict(data)
    expected['mcp_servers'] = {k: v for k, v in data.get('mcp_servers', {}).items() if k != name}
    if not expected['mcp_servers']:
        del expected['mcp_servers']
    if parsed != expected:
        raise ValueError('TOML edit would change unrelated settings')
    return updated, [{'component': 'work-journal', 'selector': f'mcp_servers.{name}', 'action': 'remove_entry'}]


def plan_migration(existing: dict, selected_packages: list[str]) -> dict:
    """Read only explicitly inventoried files and return every proposed edit unconfirmed."""
    if not isinstance(selected_packages, list) or any(s not in PACKAGES for s in selected_packages):
        raise ValueError('Select known plugin packages')
    plan = {'schema_version': 1, 'id': uuid.uuid4().hex, 'selected_packages': selected_packages,
            'replacement_verified': existing.get('replacement_verified') is True,
            'operations': [], 'confirmed': False}
    selected, seen = set(selected_packages), set()
    for item in existing.get('files', []):
        path = _safe_file(Path(item['path']))
        if str(path) in seen:
            raise ValueError('Configuration inventory contains duplicate paths')
        seen.add(str(path))
        roots = item.get('legacy_roots', [])
        if not isinstance(roots, list) or any(not isinstance(r, str) or not r.startswith('/') or r == '/' for r in roots):
            raise ValueError('Legacy roots must be explicit absolute paths')
        before = path.read_bytes()
        text = before.decode('utf-8')
        kind = item['format']
        if kind == 'json':
            after, changes = _edit_json(text, item, selected)
        elif kind == 'toml':
            after, changes = _edit_toml(text, item, selected)
        elif kind == 'routing':
            after, changes = text, []
            for change in item.get('replacements', []):
                if change['package'] not in selected:
                    continue
                if not change['before'] or after.count(change['before']) != 1:
                    raise ValueError('Routing replacement must match exactly once')
                after = after.replace(change['before'], change['after'], 1)
                changes.append({'component': change['package'], 'selector': 'exact reviewed text', 'action': 'replace_text'})
        else:
            raise ValueError('Unsupported configuration format; use an explicit reviewed edit')
        if after.encode('utf-8') != before:
            plan['operations'].append({'path': str(path), 'action': 'replace', 'before_hash': _hash(before),
                'after_hash': _hash(after.encode('utf-8')), 'after': after, 'mode': path.stat().st_mode & 0o777,
                'backup': f'{len(plan["operations"]):04d}.before', 'changes': changes})
    plan['preview_hash'] = _plan_hash(plan)
    return plan


def _replace(path: Path, content: bytes, mode: int) -> None:
    descriptor, temp = tempfile.mkstemp(prefix=f'.{path.name}.migration-', dir=path.parent)
    try:
        with os.fdopen(descriptor, 'wb') as stream:
            stream.write(content); stream.flush(); os.fsync(stream.fileno())
        os.chmod(temp, mode)
        os.replace(temp, path)
    finally:
        if os.path.exists(temp):
            os.unlink(temp)


def _validate_snapshot(operations: list[dict]) -> None:
    for operation in operations:
        path = _safe_file(Path(operation['path']))
        if (str(path) != operation['path'] or _hash(path.read_bytes()) != operation['before_hash']
                or path.stat().st_mode & 0o777 != operation['mode']):
            raise ValueError('Settings changed after preview; request a new preview and confirmation')


def apply_migration(plan: dict, backup_root: Path) -> Path:
    """Apply only the exact confirmed preview after verified replacement and full preflight."""
    if plan.get('confirmed') is not True or plan.get('replacement_verified') is not True:
        raise PermissionError('Confirm the exact preview and verify replacement plugins before migration')
    if plan.get('preview_hash') != _plan_hash(plan):
        raise ValueError('Migration preview was changed after review')
    if plan.get('schema_version') != 1 or not re.fullmatch(r'[a-f0-9]{32}', plan.get('id', '')):
        raise ValueError('Invalid migration identity')
    for operation in plan['operations']:
        if (operation.get('action') != 'replace' or not re.fullmatch(r'\d{4}\.before', operation.get('backup', ''))
                or _hash(operation['after'].encode()) != operation['after_hash']):
            raise ValueError('Invalid migration operation')
    _validate_snapshot(plan['operations'])
    if backup_root.is_symlink():
        raise ValueError('Backup root must not be a symlink')
    _outside_plugin(backup_root.resolve() / 'manifest.json')
    try:
        import fcntl
    except ImportError as error:
        raise OSError('Migration writes require POSIX file locking') from error
    backup_root.mkdir(parents=True, exist_ok=True)
    descriptor = os.open(backup_root / '.migration.lock', os.O_CREAT | os.O_RDWR | os.O_NOFOLLOW, 0o600)
    with os.fdopen(descriptor, 'r+') as lock:
        fcntl.flock(lock, fcntl.LOCK_EX)
        _validate_snapshot(plan['operations'])
        run = backup_root / plan['id']; run.mkdir(mode=0o700)
        operations = []
        for operation in plan['operations']:
            content = Path(operation['path']).read_bytes()
            if _hash(content) != operation['before_hash']:
                raise ValueError('Settings changed while creating backup; no target was written')
            _replace(run / operation['backup'], content, 0o600)
            operations.append({k: v for k, v in operation.items() if k != 'after'})
        _validate_snapshot(plan['operations'])
        manifest_path = run / 'manifest.json'
        manifest = {'schema_version': 1, 'status': 'prepared', 'operations': operations, 'applied': []}
        def save():
            _replace(manifest_path, (json.dumps(manifest, indent=2) + '\n').encode(), 0o600)
        save()
        try:
            for operation in plan['operations']:
                _validate_snapshot([operation])
                _replace(Path(operation['path']), operation['after'].encode('utf-8'), operation['mode'])
                manifest['applied'].append(operation['path']); save()
            manifest['status'] = 'applied'; save()
        except (OSError, ValueError) as error:
            try:
                applied = [op for op in operations if op['path'] in manifest['applied']]
                for path, content, mode in _recovery_replacements(manifest_path, applied):
                    _replace(path, content, mode)
                manifest['status'] = 'rolled_back'; save()
            except (OSError, ValueError) as recovery:
                error.add_note(f'Recovery requires {manifest_path}: {recovery}')
            raise
        return manifest_path


def _recovery_replacements(manifest_path: Path, operations: list[dict]) -> list[tuple]:
    replacements = []
    for operation in operations:
        backup_name = operation['backup']
        if not re.fullmatch(r'\d{4}\.before', backup_name):
            raise ValueError('Invalid backup reference')
        backup = _safe_file(manifest_path.parent / backup_name)
        content = backup.read_bytes()
        if _hash(content) != operation['before_hash']:
            raise ValueError('Backup content changed; recovery refused')
        path = _safe_file(Path(operation['path']), allow_missing=True)
        if str(path) != operation['path']:
            raise ValueError('Recovery target path changed')
        actual = _hash(path.read_bytes()) if path.exists() else None
        if path.exists() and (actual not in {operation['before_hash'], operation['after_hash']}
                             or path.stat().st_mode & 0o777 != operation['mode']):
            raise ValueError('Settings changed since migration; recovery refused before any file write')
        if actual != operation['before_hash']:
            replacements.append((path, content, operation['mode']))
    return replacements


def restore_migration(manifest_path: Path) -> None:
    """Preflight every backup and current file; restore byte-for-byte without discarding new edits."""
    manifest_path = _safe_file(manifest_path)
    import fcntl
    descriptor = os.open(manifest_path.parent.parent / '.migration.lock',
                         os.O_CREAT | os.O_RDWR | os.O_NOFOLLOW, 0o600)
    with os.fdopen(descriptor, 'r+') as lock:
        fcntl.flock(lock, fcntl.LOCK_EX)
        manifest = json.loads(manifest_path.read_text())
        replacements = _recovery_replacements(manifest_path, manifest['operations'])
        for path, content, mode in replacements:
            path.parent.mkdir(parents=True, exist_ok=True)
            _replace(path, content, mode)
        manifest['status'] = 'restored'
        _replace(manifest_path, (json.dumps(manifest, indent=2) + '\n').encode(), 0o600)


def check_updates(config_root: Path, defaults: Path) -> list[dict]:
    """Reuse the runtime's original base hashes and preserve every personal file."""
    from .preferences import check_preference_updates
    control = defaults.parents[1] / 'control-return/SKILL.md'
    return check_preference_updates(defaults, config_root, control if control.is_file() else None)


def check_hook_updates(previous: Path, current: Path) -> list[dict]:
    """Compare hook inputs for review; never infer or manufacture native trust hashes."""
    def inputs(root):
        paths = list((root / 'hooks').rglob('*')) + list((root / 'runtime').rglob('*'))
        paths += list((root / 'skills').glob('*/scripts/session_start_hook.py'))
        return {p.relative_to(root).as_posix(): (_hash(p.read_bytes()), p.stat().st_mode & 0o777)
                for p in paths if p.is_file() and not p.is_symlink() and '__pycache__' not in p.parts}
    old, new = inputs(previous), inputs(current)
    changed = sorted(p for p in set(old) | set(new) if old.get(p) != new.get(p))
    return ([{'status': 'review_required', 'changed_resources': changed, 'native_trust': 'not_verified',
              'message': 'Review changed hook inputs, then inspect normal CLI hook trust controls'}] if changed else [])


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    commands = parser.add_subparsers(dest='command', required=True)
    preview = commands.add_parser('preview')
    preview.add_argument('--inventory', type=Path, required=True)
    preview.add_argument('--packages', nargs='+', required=True)
    preview.add_argument('--output', type=Path, required=True)
    apply = commands.add_parser('apply')
    apply.add_argument('--plan', type=Path, required=True)
    apply.add_argument('--confirm', required=True)
    apply.add_argument('--backup-root', type=Path, required=True)
    restore = commands.add_parser('restore')
    restore.add_argument('--manifest', type=Path, required=True)
    updates = commands.add_parser('updates')
    updates.add_argument('--config-root', type=Path, required=True)
    updates.add_argument('--defaults', type=Path, required=True)
    hooks = commands.add_parser('hooks')
    hooks.add_argument('--previous', type=Path, required=True)
    hooks.add_argument('--current', type=Path, required=True)
    args = parser.parse_args(argv)
    try:
        if args.command == 'preview':
            plan = plan_migration(json.loads(_safe_file(args.inventory.absolute()).read_text()), args.packages)
            output = args.output.absolute()
            _outside_plugin(output.resolve())
            descriptor = os.open(output, os.O_CREAT | os.O_EXCL | os.O_WRONLY, 0o600)
            with os.fdopen(descriptor, 'w') as stream:
                stream.write(json.dumps(plan, ensure_ascii=False, indent=2) + '\n')
            print(json.dumps({'confirmed': False, 'preview_hash': plan['preview_hash'],
                'operations': [{k: v for k, v in op.items() if k != 'after'} for op in plan['operations']]}))
        elif args.command == 'apply':
            plan = json.loads(_safe_file(args.plan.absolute()).read_text())
            if args.confirm != plan.get('preview_hash'):
                raise PermissionError('Confirmation must match the exact reviewed preview hash')
            plan['confirmed'] = True
            manifest = apply_migration(plan, args.backup_root.absolute())
            print(json.dumps({'status': 'applied', 'manifest': str(manifest)}))
        elif args.command == 'restore':
            restore_migration(args.manifest.absolute())
            print(json.dumps({'status': 'restored'}))
        elif args.command == 'updates':
            print(json.dumps(check_updates(args.config_root.absolute(), args.defaults.absolute())))
        else:
            print(json.dumps(check_hook_updates(args.previous.absolute(), args.current.absolute())))
        return 0
    except (OSError, ValueError, KeyError, TypeError) as error:
        parser.exit(1, f'Migration check failed: {error}\n')


if __name__ == '__main__':
    raise SystemExit(main())
