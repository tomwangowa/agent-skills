"""Separate journal consent with complete-file create-only publication."""
from __future__ import annotations

import hashlib
import json
import os
import tempfile
from pathlib import Path

from agent_skills_runtime.config import (read_work_journal, require_external_personal_path,
                                         resolve_config_root, resolve_data_path, resolve_activities_dir, validate_work_journal)
from agent_skills_runtime.setup import setup_work_journal


def existing_journal(env, home):
    """Read only configuration and expose only the paths used by journal skills."""
    root = resolve_config_root(env, home)
    path = root / 'work-journal.json'
    if not path.exists() and not path.is_symlink():
        return None
    settings = read_work_journal(root)
    return {'settings': str(path), 'activities': str(resolve_activities_dir(env, settings, root, home)),
            'notes': [str(require_external_personal_path(resolve_data_path(p, root, home)))
                      for p in settings['sources']['notes']['paths']]}


def _token(preview):
    payload = {k: v for k, v in preview.items() if k != 'fingerprint'}
    return hashlib.sha256(json.dumps(payload, sort_keys=True, separators=(',', ':')).encode()).hexdigest()


def _digest(path):
    try:
        return hashlib.sha256(path.read_bytes()).hexdigest()
    except FileNotFoundError:
        return None


def journal_preview(env, home, activities, notes):
    """Resolve external settings paths without reading journal/note contents or writing."""
    root = resolve_config_root(env, home)
    activity_dir = resolve_data_path(activities, root, home)
    note_dirs = tuple(resolve_data_path(p, root, home) for p in notes)
    settings = root / 'work-journal.json'
    proposed = {'sources': {'activities': str(activity_dir), 'notes': {
        'paths': [str(p) for p in note_dirs], 'recursive': True, 'exclude_hidden': True}}}
    validate_work_journal(proposed)
    directories = []
    for selected in (root, activity_dir, *note_dirs):
        missing = []
        path = selected
        while not path.exists():
            if path.parent == path:
                raise ValueError('Filesystem anchor is unavailable; choose an accessible drive/share')
            missing.append(path)
            path = path.parent
        for directory in reversed(missing):
            if str(directory) not in directories:
                directories.append(str(directory))
    for path in (settings, root, activity_dir, *note_dirs):
        require_external_personal_path(path)
    existing = _digest(settings)
    if settings.is_symlink() and not settings.exists():
        raise ValueError('Dangling settings symlink')
    current = read_work_journal(root) if existing is not None else None
    if current is not None:
        sources = current['sources']
        note_settings = sources['notes']
        current = {'sources': {'activities': sources['activities'], 'notes': {
            key: note_settings[key] for key in ('paths', 'recursive', 'exclude_hidden') if key in note_settings}}}
    preview = {'status': 'preserved' if existing is not None else 'preview', 'config_root': str(root),
               'settings': str(settings), 'existing_digest': existing, 'current': current,
               'proposed': proposed, 'directories': [] if current is not None else directories,
               'resolved_paths': {str(p): str(p.resolve()) for p in (root, settings, activity_dir, *note_dirs, *(Path(d) for d in directories))}}
    preview['fingerprint'] = _token(preview)
    return preview


def apply_journal(preview, approved_fingerprint):
    """Never replace an existing settings file, including a concurrent creator's file."""
    if preview.get('fingerprint') != approved_fingerprint or _token(preview) != approved_fingerprint:
        raise ValueError('Journal approval is stale')
    settings = Path(preview['settings'])
    root = Path(preview['config_root'])
    for original, resolved in preview['resolved_paths'].items():
        path = Path(original)
        require_external_personal_path(path)
        if str(path.resolve()) != resolved:
            return {'status': 'conflict', 'detail': 'A path changed after preview.'}
    if _digest(settings) != preview['existing_digest']:
        return {'status': 'conflict', 'detail': 'Settings changed; existing contents preserved.'}
    if preview['existing_digest'] is not None:
        read_work_journal(root)
        return {'status': 'preserved', 'detail': 'Existing valid settings retained; no data directories created.'}
    root.mkdir(parents=True, exist_ok=True)
    descriptor, temporary = tempfile.mkstemp(prefix='.installer-journal-', dir=root)
    content = (json.dumps(preview['proposed'], indent=2) + '\n').encode()
    try:
        with os.fdopen(descriptor, 'wb') as output:
            output.write(content)
            output.flush()
            os.fsync(output.fileno())
        # Publish before making data directories. A racing creator owns its file
        # and must not cause us to create directories for the discarded proposal.
        try:
            os.link(temporary, settings)
        except FileExistsError:
            return {'status': 'conflict', 'detail': 'Another process created settings; preserved.'}
        expected = hashlib.sha256(content).hexdigest()
        proposed = preview['proposed']['sources']
        setup_work_journal(root, Path(proposed['activities']), [Path(p) for p in proposed['notes']['paths']])
        for directory in preview['directories']:
            if _digest(settings) != expected:
                return {'status': 'conflict', 'detail': 'Settings changed during setup; previous writes may remain.'}
            require_external_personal_path(Path(directory))
            Path(directory).mkdir(parents=True, exist_ok=True)
        return {'status': 'created', 'detail': 'Settings and planned directories created; journal data was not moved or read.'}
    finally:
        Path(temporary).unlink(missing_ok=True)
