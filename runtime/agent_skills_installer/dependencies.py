"""Dependency proposals use existing managers and never escalate privileges."""
from __future__ import annotations

import json
import shutil
import subprocess
import sys
from pathlib import Path

from .models import Action


def missing_dependencies(catalog, selected, tools):
    return tuple(sorted({tool for p in catalog if (p.host, p.name) in selected
                         for tool in p.commands if not tools.get(tool, False)}))


def dependency_action(tool, platform, managers, mapping):
    """Return no proposal when the platform/manager/package combination is unknown."""
    for manager, packages in mapping.get('managers', {}).get(platform, {}).items():
        if manager not in managers or tool not in packages:
            continue
        package = packages[tool]
        if manager == 'brew':
            argv = ('brew', 'install', package)
        elif manager == 'winget':
            argv = ('winget', 'install', '--exact', '--id', package, '--source', 'winget')
        elif manager == 'apt-get':
            argv = ('apt-get', 'install', package)
        else:
            continue
        return Action(f'dependency/{tool}', 'dependency', None, tool, argv,
                      preconditions=(('manager', manager), ('platform', platform),
                                     ('effect', 'Downloads packages and transitive dependencies; may change system paths and request administrator approval. No manager, privilege escalation or whole-system upgrade is supplied.')))
    return None


def detect_tools(commands):
    """Probe commands without invoking Windows Python download shims."""
    found = {command: shutil.which(command) is not None for command in commands}
    if 'python3' in found:
        # The running interpreter is real, but plugins still need a usable python3 command.
        if sys.platform == 'win32':
            path = shutil.which('python3')
            found['python3'] = bool(path and 'windowsapps' not in path.lower())
        elif found['python3']:
            try:
                result = subprocess.run(('python3', '-c', 'import sys; raise SystemExit(sys.version_info < (3, 11))'),
                                        capture_output=True, text=True, timeout=5)
                found['python3'] = result.returncode == 0
            except (OSError, subprocess.SubprocessError):
                found['python3'] = False
    return found


def render_bootstrap(template, platform, mapping):
    """Render only manager mappings that the minimal pre-Python launcher can use."""
    if platform not in ('macos', 'windows', 'linux'):
        raise ValueError('Unknown bootstrap platform')
    manager = {'macos': 'brew', 'windows': 'winget', 'linux': 'apt-get'}[platform]
    package = mapping.get('managers', {}).get(platform, {}).get(manager, {}).get('python3')
    if not isinstance(package, str) or not package or any(c not in 'abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789@.-' for c in package):
        raise ValueError('Unknown/unsafe Python package mapping')
    result = template.replace('@@PYTHON_PACKAGE@@', package)
    if '@@' in result:
        raise ValueError('Unexpanded bootstrap marker')
    return result
