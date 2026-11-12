"""Synthetic official-source fixtures; never native acceptance evidence."""
import copy
import hashlib
import json

CLAUDE_CATALOG = 'https://github.com/anthropics/claude-plugins-official.git'
CODEX_CATALOG = 'https://github.com/openai/plugins.git'
UPSTREAM = 'https://github.com/obra/superpowers.git'
PIN = 'bb92a77741419a4ab5f06e711a283343f1ada0c3'
COMMIT = '12345678' + 'a' * 32
SKILLS = ['writing-plans', 'test-driven-development', 'systematic-debugging', 'executing-plans',
          'subagent-driven-development', 'requesting-code-review', 'finishing-a-development-branch']


def entry(host):
    source = ({'source': 'url', 'url': UPSTREAM, 'sha': PIN} if host == 'claude'
              else {'source': 'local', 'path': './plugins/superpowers'})
    return {'name': 'superpowers', 'source': source, 'description': 'Synthetic fixture'}


def digest(value):
    return hashlib.sha256(json.dumps(value, sort_keys=True, separators=(',', ':'), ensure_ascii=False).encode()).hexdigest()


def provider_data():
    data = {'schema_version': 2, 'repository': 'https://github.com/tomwangowa/agent-skills.git',
            'marketplace': 'tomwangowa', 'external': []}
    for host in ('claude', 'codex'):
        url = CLAUDE_CATALOG if host == 'claude' else CODEX_CATALOG
        data['external'].append({'host': host, 'name': 'superpowers',
            'marketplace': 'claude-plugins-official' if host == 'claude' else 'openai-curated',
            'source': url, 'version': '7.0.0' if host == 'claude' else '6.3.0',
            'skills': list(SKILLS), 'notices': ['STRONGLY RECOMMENDED: fixture only.'], 'content_hash': '2' * 64,
            'provider': {'catalog_kind': 'configured-git' if host == 'claude' else 'native-managed',
                'catalog_repository': url, 'payload_kind': 'git' if host == 'claude' else 'catalog-relative',
                'payload_repository': UPSTREAM if host == 'claude' else None,
                'payload_commit': PIN if host == 'claude' else None,
                'payload_path': None if host == 'claude' else './plugins/superpowers', 'entry_hash': digest(entry(host))}})
    return copy.deepcopy(data)


def acceptance_data(spec, *, commit=COMMIT, cli='codex-cli 0.167.0'):
    return {'schema_version': 1, 'records': [{'host': spec.host, 'cli_version': cli, 'platform': 'macos',
        'architecture': 'arm64', 'catalog_name': spec.marketplace, 'catalog_commit': commit,
        'entry_hash': spec.provider.entry_hash, 'manifest_version': spec.version,
        'content_hash': spec.content_hash, 'evidence_ref': 'synthetic-only: not native evidence'}]}


def prepared_codex(base):
    """Create a synthetic native-managed tree under a temporary CODEX_HOME."""
    from dataclasses import replace
    from agent_skills_installer.catalog import tree_hash
    from agent_skills_installer.providers import provider_targets
    home = base / 'home'
    root = home / '.tmp/plugins'
    (root / '.agents/plugins').mkdir(parents=True)
    (home / '.tmp/plugins.sha').write_text(COMMIT + '\n')
    (root / '.agents/plugins/marketplace.json').write_text(json.dumps({'name': 'openai-curated', 'plugins': [entry('codex')]}))
    payload = root / 'plugins/superpowers'
    (payload / '.codex-plugin').mkdir(parents=True)
    (payload / '.codex-plugin/plugin.json').write_text(json.dumps({'name': 'superpowers', 'version': '6.3.0'}))
    for name in SKILLS:
        target = payload / 'skills' / name / 'SKILL.md'
        target.parent.mkdir(parents=True)
        target.write_text('Synthetic ' + name)
    spec = replace(provider_targets(provider_data())[1], content_hash=tree_hash(payload))
    return spec, home, root, payload
