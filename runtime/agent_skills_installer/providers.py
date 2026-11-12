"""Pure official-target parsing and exact native capability decisions."""
from __future__ import annotations

import hashlib
import json
import re
from dataclasses import replace
from .models import NativeAcceptance, PluginSpec, ProviderSource, SkillSpec

CLAUDE_CATALOG = 'https://github.com/anthropics/claude-plugins-official.git'
CODEX_CATALOG = 'https://github.com/openai/plugins.git'
UPSTREAM = 'https://github.com/obra/superpowers.git'
OFFICIAL = {'claude': ('claude-plugins-official', CLAUDE_CATALOG), 'codex': ('openai-curated', CODEX_CATALOG)}
CODEX_MARKETPLACE_FILES = {'openai-curated': '.agents/plugins/marketplace.json',
                          'openai-api-curated': '.agents/plugins/api_marketplace.json'}
CODEX_SETUP_GUIDANCE = ('Use native /plugins to prepare the official catalog. ChatGPT login is not required; '
                        'keep your existing company model endpoint configuration. '
                        'Official plugin downloads still require access to their source hosts.')
REQUIRED_SKILLS = ('writing-plans', 'test-driven-development', 'systematic-debugging', 'executing-plans',
                   'subagent-driven-development', 'requesting-code-review', 'finishing-a-development-branch')
SNAPSHOT_KEYS = ('catalog_name', 'catalog_kind', 'catalog_repository', 'catalog_root', 'catalog_commit',
                 'entry_hash', 'payload_kind', 'payload_repository', 'payload_commit', 'payload_path', 'payload_hash')


def is_hex(value, length):
    return isinstance(value, str) and re.fullmatch('[0-9a-f]{' + str(length) + '}', value) is not None


def canonical_hash(value):
    return hashlib.sha256(json.dumps(value, sort_keys=True, separators=(',', ':'), ensure_ascii=False).encode()).hexdigest()


def official_catalog_names(host):
    """Keep model-provider configuration outside catalog identity decisions."""
    return tuple(CODEX_MARKETPLACE_FILES) if host == 'codex' else (OFFICIAL[host][0],)


def resolve_provider(spec, inventory):
    """Select only the single official catalog actually exposed by the native CLI."""
    if spec.provider and spec.host == 'codex':
        markets = [m for m in inventory.marketplaces if m.name in CODEX_MARKETPLACE_FILES]
        if len(markets) == 1:
            return replace(spec, marketplace=markets[0].name)
    return spec


def validate_provider_spec(spec):
    """Constrain executable metadata to the reviewed catalog/payload pairings."""
    p = spec.provider
    if (spec.default_selected is not False or not isinstance(p, ProviderSource) or spec.name != 'superpowers' or spec.host not in OFFICIAL
            or spec.marketplace not in official_catalog_names(spec.host) or spec.source != OFFICIAL[spec.host][1]
            or p.catalog_repository != spec.source or not isinstance(spec.version, str)
            or not re.fullmatch(r'\d+\.\d+\.\d+', spec.version)
            or (p.entry_hash is not None and not is_hex(p.entry_hash, 64))
            or (spec.content_hash != '' and not is_hex(spec.content_hash, 64))):
        raise ValueError('Invalid official provider target')
    if spec.host == 'claude':
        valid = (p.catalog_kind == 'configured-git' and p.payload_kind == 'git'
                 and p.payload_repository == UPSTREAM and is_hex(p.payload_commit, 40) and p.payload_path is None)
    else:
        valid = (p.catalog_kind == 'native-managed' and p.payload_kind == 'catalog-relative'
                 and p.payload_repository is None and p.payload_commit is None and p.payload_path == './plugins/superpowers')
    if not valid:
        raise ValueError('Catalog and payload provenance disagree')


def provider_targets(data: dict) -> tuple[PluginSpec, ...]:
    """Parse host-specific schema 2 descriptors; unknown hashes remain disabled."""
    try:
        if (type(data.get('schema_version')) is not int or data['schema_version'] != 2
                or data.get('repository') != 'https://github.com/tomwangowa/agent-skills.git'
                or data.get('marketplace') != 'tomwangowa' or not isinstance(data['external'], list)):
            raise ValueError('Unsupported provider mapping')
        result = []
        for row in data['external']:
            if 'hosts' in row or not isinstance(row['skills'], list) or set(row['skills']) != set(REQUIRED_SKILLS) or len(row['skills']) != len(REQUIRED_SKILLS):
                raise ValueError('Invalid host-specific skills')
            if not isinstance(row['notices'], list) or not all(isinstance(n, str) and n.strip() for n in row['notices']):
                raise ValueError('Invalid provider notices')
            host = row['host']
            skills = tuple(SkillSpec(n, n.replace('-', ' '), 'model', f'{"/" if host == "claude" else "$"}superpowers:{n}') for n in row['skills'])
            spec = PluginSpec(host, row['name'], row['marketplace'], row['source'], row['version'], skills, ('git',),
                              tuple(row['notices']), False, '' if row['content_hash'] is None else row['content_hash'], ProviderSource(**row['provider']))
            validate_provider_spec(spec)
            result.append(spec)
        if len(result) != 2 or {p.host for p in result} != set(OFFICIAL):
            raise ValueError('Exactly one external target per host is required')
        return tuple(result)
    except (KeyError, TypeError, AttributeError) as error:
        raise ValueError('Malformed provider metadata') from error


def parse_native_acceptance(data: dict) -> tuple[NativeAcceptance, ...]:
    """Evidence records describe one exact CLI/platform/payload, never a range."""
    try:
        if type(data.get('schema_version')) is not int or data['schema_version'] != 1 or not isinstance(data['records'], list):
            raise ValueError('Unsupported native acceptance index')
        records = tuple(NativeAcceptance(**r) for r in data['records'])
        for r in records:
            if (r.host not in OFFICIAL or r.catalog_name not in official_catalog_names(r.host)
                    or not isinstance(r.cli_version, str) or not r.cli_version or r.cli_version != r.cli_version.strip()
                    or r.platform not in ('macos', 'windows', 'linux')
                    or not isinstance(r.architecture, str) or not re.fullmatch(r'[a-z0-9_]+', r.architecture)
                    or not is_hex(r.catalog_commit, 40) or not is_hex(r.entry_hash, 64) or not is_hex(r.content_hash, 64)
                    or not isinstance(r.manifest_version, str) or not re.fullmatch(r'\d+\.\d+\.\d+', r.manifest_version)
                    or not isinstance(r.evidence_ref, str) or not r.evidence_ref.strip()):
                raise ValueError('Incomplete native acceptance record')
        return records
    except (TypeError, KeyError, AttributeError) as error:
        raise ValueError('Malformed native acceptance record') from error


def target_accepted(spec, records, cli_version, platform, architecture) -> bool:
    """Only proven static targets may even propose external source preparation."""
    if not spec.provider or not spec.content_hash or not spec.provider.entry_hash:
        return False
    expected = (spec.host, cli_version, platform, architecture, spec.marketplace, spec.provider.entry_hash, spec.version, spec.content_hash)
    return any((r.host, r.cli_version, r.platform, r.architecture, r.catalog_name, r.entry_hash,
                r.manifest_version, r.content_hash) == expected and r.evidence_ref.strip() and is_hex(r.catalog_commit, 40) for r in records)


def installation_accepted(spec, readiness, records, cli_version, platform, architecture) -> bool:
    """Historical catalog commits may differ; the selected entry must not."""
    if not readiness or readiness.name != spec.name or readiness.status != 'ready':
        return False
    state = dict(readiness.snapshot)
    return bool(target_accepted(spec, records, cli_version, platform, architecture)
                and state.get('catalog_name') == spec.marketplace and state.get('entry_hash') == spec.provider.entry_hash
                and is_hex(state.get('catalog_commit'), 40)
                and set(state) == set(SNAPSHOT_KEYS) and all(isinstance(v, str) for v in state.values())
                and state.get('catalog_root')
                and (state.get('catalog_kind') == spec.provider.catalog_kind
                     or (spec.host == 'claude' and spec.marketplace == 'claude-plugins-official'
                         and state.get('catalog_kind') == 'verified-archive'))
                and state.get('catalog_repository') == spec.provider.catalog_repository
                and state.get('payload_kind') == spec.provider.payload_kind
                and state.get('payload_repository') == (spec.provider.payload_repository or '')
                and state.get('payload_commit') == (spec.provider.payload_commit or '')
                and state.get('payload_path') == (spec.provider.payload_path or '')
                and (spec.host == 'claude' or state.get('payload_hash') == spec.content_hash))
