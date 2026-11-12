"""Generate from real shipped surfaces; read bundled catalogs without repo imports."""
from __future__ import annotations

import json
import hashlib
import re
from dataclasses import asdict
from pathlib import Path

from .models import PluginSpec, SkillSpec, ProviderSource
from .providers import provider_targets, validate_provider_spec

REPOSITORY = 'https://github.com/tomwangowa/agent-skills.git'
EXTERNAL = 'https://github.com/obra/superpowers.git'
NAME = re.compile(r'^[a-z][a-z0-9-]*$')


def tree_hash(root: Path) -> str:
    """Fingerprint the complete plugin payload without following symlinks."""
    if root.is_symlink() or not root.is_dir():
        raise ValueError('Missing/unsafe plugin root')
    entries = []
    for path in sorted(root.rglob('*')):
        if path.is_symlink():
            raise ValueError('Symlink in plugin payload')
        if path.is_file():
            entries.append((path.relative_to(root).as_posix(), hashlib.sha256(path.read_bytes()).hexdigest()))
    return hashlib.sha256(json.dumps(entries, separators=(',', ':')).encode()).hexdigest()


def safe_path(root: Path, relative: str) -> Path:
    """Refuse links and escapes instead of following packaging inputs elsewhere."""
    rel = Path(relative)
    if rel.is_absolute() or '..' in rel.parts:
        raise ValueError('Source path escapes root')
    candidate = root
    for part in rel.parts:
        candidate = candidate / part
        if candidate.is_symlink():
            raise ValueError('Symlink source is not permitted')
    if not candidate.is_file() or not candidate.resolve().is_relative_to(root.resolve()):
        raise ValueError(f'Missing or unsafe source: {relative}')
    return candidate


def read_json(root: Path, relative: str) -> dict:
    return json.loads(safe_path(root, relative).read_text(encoding='utf-8'))


def build_catalog(repo_root: Path, providers: dict, dependencies: dict) -> tuple[PluginSpec, ...]:
    """Build only approved providers and manifest-verified host-specific skills."""
    # Build-time only: the distributed runtime consumes catalog.json instead.
    from scripts.plugin_packaging.catalog import surface_skills
    if providers.get('repository') != REPOSITORY or providers.get('marketplace') != 'tomwangowa':
        raise ValueError('Unknown repository provider')
    if providers.get('schema_version') != 2 or dependencies.get('schema_version') != 1:
        raise ValueError('Unsupported mapping schema')
    packages = read_json(repo_root, 'plugin-packages.json')['packages']
    metadata = {s['id']: s for s in read_json(repo_root, 'skills-catalog.json')['skills']}
    result = []
    for host in ('claude', 'codex'):
        market_file = '.claude-plugin/marketplace.json' if host == 'claude' else '.agents/plugins/marketplace.json'
        market = read_json(repo_root, market_file)
        if market['name'] != 'tomwangowa':
            raise ValueError('Unexpected marketplace identity')
        entries = {p['name']: p for p in market['plugins']}
        if len(entries) != len(market['plugins']):
            raise ValueError('Duplicate marketplace plugin identity')
        for package in packages:
            name = package['name']
            prefix = f'plugins/{host}/{name}'
            manifest = read_json(repo_root, f'{prefix}/.{host}-plugin/plugin.json')
            if manifest['name'] != name or manifest['version'] != package['version'] or name not in entries:
                raise ValueError('Manifest and package identity/version disagree')
            source = entries[name]['source']
            actual = source if host == 'claude' else source.get('path')
            if actual != f'./{prefix}':
                raise ValueError('Unexpected marketplace source')
            expected = set(surface_skills(package, host))
            skill_root = repo_root / prefix / 'skills'
            if skill_root.is_symlink() or {p.name for p in skill_root.iterdir() if p.is_dir()} != expected:
                raise ValueError('Shipped skills differ from declared surface')
            skills = []
            for skill in sorted(expected):
                text = safe_path(repo_root, f'{prefix}/skills/{skill}/SKILL.md').read_text(encoding='utf-8')
                intent = metadata[skill]['invocation_intent']
                if host == 'claude' and intent == 'user' and not re.search(r'^disable-model-invocation:\s*true\s*$', text, re.M):
                    raise ValueError('Manual invocation policy missing')
                if host == 'codex' and intent == 'user':
                    policy = safe_path(repo_root, f'{prefix}/skills/{skill}/agents/openai.yaml').read_text()
                    if not re.search(r'allow_implicit_invocation:\s*false', policy):
                        raise ValueError('Manual invocation policy missing')
                description = re.search(r'^description:[ \t]*(.*)', text, re.M)
                purpose = description.group(1).strip() if description else skill
                if purpose in ('>', '>-', '>+', '|', '|-', '|+'):
                    purpose = ''
                else:
                    purpose = purpose.strip('\"\'')
                if not purpose:
                    lines = text.splitlines()
                    start = next(i for i, line in enumerate(lines) if line.startswith('description:'))
                    block = []
                    for line in lines[start + 1:]:
                        if line.strip() and not line.startswith((' ', '\t')):
                            break
                        block.append(line.strip())
                    purpose = ' '.join(block)
                skills.append(SkillSpec(skill, purpose or skill, intent, f'{"/" if host == "claude" else "$"}{name}:{skill}'))
            commands = tuple(sorted(set(package['requirements']['commands'] + dependencies['package_commands'].get(name, []))))
            result.append(PluginSpec(host, name, 'tomwangowa', REPOSITORY, manifest['version'], tuple(skills), commands,
                                     ('Installation does not authorize hooks or verify every skill.',
                                      'Native Windows preference writes/migration use POSIX locks and are unsupported.',
                                      'Optional workflow tools and external services may require separate setup.'),
                                     content_hash=tree_hash(repo_root / prefix)))
        if host == 'claude':
            for name in ('handoff-mod', 'attention-mod'):
                source = entries[name]['source']
                if source != f'./plugins/{name}':
                    raise ValueError('Unknown mod source')
                manifest = read_json(repo_root, f'plugins/{name}/.claude-plugin/plugin.json')
                if manifest['name'] != name:
                    raise ValueError('Mod manifest identity mismatch')
                mod_skills = ()
                if name == 'handoff-mod':
                    text = safe_path(repo_root, 'plugins/handoff-mod/skills/handoff/SKILL.md').read_text()
                    if not re.search(r'^disable-model-invocation:\s*true\s*$', text, re.M):
                        raise ValueError('Handoff mod manual policy missing')
                    mod_skills = (SkillSpec('handoff', 'Write a handoff note with verified/remaining work.', 'user', '/handoff-mod:handoff'),)
                notice = ('Requires Claude Code 2.1.312+; /attention opens the panel. Summaries invoke haiku on conversation/tool excerpts and consume model tokens.'
                          if name == 'attention-mod' else
                          'Claude Code only; local automatic notes/store writes may occur. The mod itself makes no model call; manually running the handoff skill uses the session model.')
                result.append(PluginSpec(host, name, 'tomwangowa', REPOSITORY, manifest['version'], mod_skills, (),
                                         ('Native mod behavior requires separate acceptance.', notice),
                                         content_hash=tree_hash(repo_root / 'plugins' / name)))
    result.extend(provider_targets(providers))
    validate_catalog(tuple(result))
    return tuple(result)


def validate_catalog(specs: tuple[PluginSpec, ...]) -> None:
    seen = set()
    for spec in specs:
        key = (spec.host, spec.marketplace, spec.name)
        if key in seen or spec.host not in ('claude', 'codex') or not NAME.fullmatch(spec.name) or not NAME.fullmatch(spec.marketplace):
            raise ValueError('Duplicate or invalid plugin identity')
        if spec.source != REPOSITORY:
            validate_provider_spec(spec)
        elif spec.provider is not None or spec.marketplace != 'tomwangowa' or not re.fullmatch(r'\d+\.\d+\.\d+', spec.version):
            raise ValueError('Unknown provider/version')
        if spec.host == 'codex' and spec.name in ('handoff-mod', 'attention-mod'):
            raise ValueError('Claude-only mod')
        seen.add(key)


def load_catalog(path: Path) -> tuple[PluginSpec, ...]:
    """Read an archive catalog, validating every command-generating identity."""
    data = json.loads(path.read_text(encoding='utf-8'))
    if not isinstance(data, dict) or data.get('schema_version') != 2 or not isinstance(data.get('plugins'), list):
        raise ValueError('Unsupported catalog schema')
    specs = []
    try:
        for item in data['plugins']:
            item = dict(item)
            if item.get('provider') is not None:
                item['provider'] = ProviderSource(**item['provider'])
            item['skills'] = tuple(SkillSpec(**s) for s in item['skills'])
            for key in ('commands', 'notices'):
                item[key] = tuple(item[key])
            specs.append(PluginSpec(**item))
        validate_catalog(tuple(specs))
    except (TypeError, KeyError, AttributeError) as error:
        raise ValueError('Malformed bundled plugin metadata') from error
    return tuple(specs)
