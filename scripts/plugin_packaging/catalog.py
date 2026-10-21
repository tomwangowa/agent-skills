"""Package metadata is separate from source lifecycle and invocation intent."""
from __future__ import annotations

import json
import re
from pathlib import Path

PACKAGE_NAMES = frozenset({'quality-gates', 'technical-decisions', 'repo-workflow',
                          'content-tools', 'work-journal', 'session-preferences', 'skill-toolbox'})
FIELDS = frozenset({'name', 'display_name', 'version', 'skills', 'platforms', 'runtime_resources',
                    'requirements', 'dependencies'})
DEPENDENCY_FIELDS = frozenset({'kind', 'provider', 'skills', 'condition', 'tested_versions'})
PLATFORMS = frozenset({'claude', 'codex'})
SURFACE_EXCLUSIONS = {'claude': {'code-review-codex'},
                      'codex': {'code-review-claude', 'claude-workflow-designer'}}


def load_packages(repo_root: Path) -> list[dict]:
    """Read and validate package metadata without changing source catalog entries."""
    data = json.loads((repo_root / 'plugin-packages.json').read_text(encoding='utf-8'))
    if not isinstance(data, dict) or data.get('schema_version') != 1:
        raise ValueError('Unsupported package schema')
    packages = data.get('packages')
    catalog = json.loads((repo_root / 'skills-catalog.json').read_text(encoding='utf-8'))['skills']
    errors = validate_packages(packages, catalog)
    if errors:
        raise ValueError('; '.join(errors))
    return packages


def _strings(value: object, *, nonempty: bool = False) -> bool:
    return (isinstance(value, list) and (bool(value) or not nonempty)
            and all(isinstance(s, str) and bool(s.strip()) for s in value)
            and len(value) == len(set(value)))


def validate_packages(packages: list[dict], catalog: list[dict]) -> list[str]:
    """Return schema, lifecycle, duplicate and dependency errors for the seven packages."""
    if not isinstance(packages, list):
        return ['packages must be a list']
    entries = {s['id']: s for s in catalog}
    errors, names, members = [], [], []
    display_names = []
    for package in packages:
        if not isinstance(package, dict) or set(package) != FIELDS:
            errors.append('Package fields must match the documented schema'); continue
        name = package['name']
        if not isinstance(name, str) or name not in PACKAGE_NAMES:
            errors.append('Unknown package name'); continue
        names.append(name)
        display_name = package['display_name']
        if (not isinstance(display_name, str) or not display_name.startswith('Towa: ')
                or not display_name[6:].strip() or display_name != display_name.strip()):
            errors.append(f'{name}: display_name must start with "Towa: "')
        else:
            display_names.append(display_name)
        if not isinstance(package['version'], str) or not re.fullmatch(r'\d+\.\d+\.\d+', package['version']):
            errors.append(f'{name}: version must be a release version')
        for field in ['skills', 'platforms', 'runtime_resources']:
            if not _strings(package[field], nonempty=field != 'runtime_resources'):
                errors.append(f'{name}: invalid {field}')
        if _strings(package['platforms']) and set(package['platforms']) != PLATFORMS:
            errors.append(f'{name}: both CLI platforms are required')
        if _strings(package['skills']):
            for skill in package['skills']:
                members.append(skill)
                if skill not in entries or entries[skill]['lifecycle'] == 'deprecated':
                    errors.append(f'{name}: unknown or retired skill {skill}')
        requirements = package['requirements']
        if (not isinstance(requirements, dict) or set(requirements) != {'commands', 'config'}
                or not _strings(requirements.get('commands')) or not _strings(requirements.get('config'))
                or any(c not in {'work-journal', 'preferences'} for c in requirements.get('config', []))):
            errors.append(f'{name}: invalid requirements')
        dependencies = package['dependencies']
        if not isinstance(dependencies, list):
            errors.append(f'{name}: dependencies must be a list'); continue
        for dep in dependencies:
            if not isinstance(dep, dict) or set(dep) != DEPENDENCY_FIELDS:
                errors.append(f'{name}: invalid dependency fields'); continue
            kind, provider = dep['kind'], dep['provider']
            if not isinstance(kind, str) or kind not in {'required', 'conditional', 'optional'}:
                errors.append(f'{name}: invalid dependency kind')
            if not isinstance(provider, str) or not provider.strip():
                errors.append(f'{name}: dependency provider is required')
            if (not isinstance(dep['condition'], str)
                    or kind == 'conditional' and not dep['condition'].strip()):
                errors.append(f'{name}: conditional dependency needs an explicit condition')
            if not _strings(dep['skills'], nonempty=True) or not _strings(dep['tested_versions']):
                errors.append(f'{name}: invalid dependency skills or tested versions'); continue
            if any(s == 'code-review-gemini' or s.endswith(':code-review-gemini') for s in dep['skills']):
                errors.append(f'{name}: retired reviewer cannot be a dependency')
            if any(not re.fullmatch(r'\d+\.\d+\.\d+', v) for v in dep['tested_versions']):
                errors.append(f'{name}: invalid tested dependency version')
            if isinstance(provider, str) and provider in PACKAGE_NAMES:
                offered = next((p.get('skills', []) for p in packages if isinstance(p, dict) and p.get('name') == provider), [])
                if any(s not in offered for s in dep['skills']):
                    errors.append(f'{name}: dependency skill is absent from {provider}')
    if len(names) != 7 or set(names) != PACKAGE_NAMES:
        errors.append('Exactly the seven approved packages are required')
    if len(display_names) != len(set(display_names)):
        errors.append('Package display names must be unique')
    if len(members) != 40 or len(set(members)) != 40:
        errors.append('Exactly 40 distinct source skills are required')
    return errors


def surface_skills(package: dict, surface: str) -> list[str]:
    """Apply the explicitly approved runtime differences without changing source membership."""
    if surface not in PLATFORMS or surface not in package['platforms']:
        raise ValueError(f'Unsupported surface: {surface}')
    return [s for s in package['skills'] if s not in SURFACE_EXCLUSIONS[surface]]
