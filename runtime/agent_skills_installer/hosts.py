"""Native host adapters: inventory reads and argument-vector construction only."""
from __future__ import annotations

import json
import hashlib
import os
import subprocess
from pathlib import Path

from .catalog import EXTERNAL, NAME, REPOSITORY, validate_catalog, safe_path, tree_hash
from .providers import (CLAUDE_CATALOG, CODEX_CATALOG, CODEX_MARKETPLACE_FILES, CODEX_SETUP_GUIDANCE,
                        SNAPSHOT_KEYS, canonical_hash, is_hex, resolve_provider)
from .models import Action, InstalledPlugin, Inventory, Marketplace, PluginSpec, ProviderReadiness
from dataclasses import replace

CODEX_RECEIPT_VERSIONS = frozenset(('codex-cli 0.167.0', '0.167.0'))
CLAUDE_ARCHIVE_TREES = {
    'dceb15d50832e6adf380bedc26dde03d251324b9': 'cd386993659390165dd164509073f60916b11238b8f932ef83dc55e016f903f4',
    'e37d307bd9f85dab6fea5dfb5e3dc146753b2d2d': 'd82a1a4cfbf569201da7a97f9acbf6fc8a495aa83755a8b3518d2c5e570bc2fe',
}


def _verified_claude_archive(root):
    """Match the complete observed tree to an independently compared snapshot."""
    raw_config = os.environ.get('CLAUDE_CONFIG_DIR')
    if raw_config is not None and (not raw_config or raw_config != raw_config.strip()):
        raise ValueError('Claude configuration location is ambiguous')
    base = Path(raw_config) if raw_config is not None else Path.home() / '.claude'
    if not base.is_absolute() or '..' in base.parts:
        raise ValueError('Claude configuration location is not absolute')
    expected = base / 'plugins/marketplaces/claude-plugins-official'
    if expected.resolve() != root:
        raise ValueError('Official archive is outside the active Claude profile')
    for path in (base, base / 'plugins', base / 'plugins/marketplaces', expected):
        if path.is_symlink() or not path.is_dir():
            raise ValueError('Official archive location is linked or unavailable')
    marker = safe_path(root, '.gcs-sha').read_bytes()
    if len(marker) != 40:
        raise ValueError('Official archive marker is invalid')
    commit = marker.decode('ascii')
    if commit not in CLAUDE_ARCHIVE_TREES:
        raise ValueError('Official archive version has not been independently verified')
    entries = []
    for path in sorted(root.rglob('*')):
        if path.is_symlink():
            raise ValueError('Official archive contains a link')
        if path.is_file() and path != root / '.gcs-sha':
            entries.append((path.relative_to(root).as_posix(), hashlib.sha256(path.read_bytes()).hexdigest()))
        elif path != root / '.gcs-sha' and not path.is_dir():
            raise ValueError('Official archive contains an unsupported file')
    digest = hashlib.sha256(json.dumps(entries, separators=(',', ':')).encode()).hexdigest()
    if digest != CLAUDE_ARCHIVE_TREES[commit]:
        raise ValueError('Official archive files differ from the verified snapshot')
    return commit


def codex_config_root() -> str:
    """Resolve the native write target without interpreting plugin/skill scope."""
    raw = os.environ.get('CODEX_HOME')
    if raw is not None and (not raw or raw != raw.strip()):
        raise ValueError('CODEX_HOME is empty or ambiguous')
    root = Path(raw) if raw is not None else Path.home() / '.codex'
    if not root.is_absolute():
        raise ValueError('CODEX_HOME must be absolute for verified installation')
    try:
        return str(root.resolve())
    except RuntimeError as error:
        raise ValueError('CODEX_HOME cannot be resolved safely') from error


def normalize_source(source: str | None) -> str | None:
    if not isinstance(source, str):
        return None
    source = source.rstrip('/')
    if source in ('tomwangowa/agent-skills', 'obra/superpowers', 'obra/superpowers-marketplace', 'anthropics/claude-plugins-official', 'openai/plugins'):
        source = 'https://github.com/' + source
    if source.startswith('https://github.com/') and not source.endswith('.git'):
        source += '.git'
    return source


def _json(runner, argv):
    result = runner(tuple(argv))
    if result.returncode:
        raise ValueError(f'{argv[0]} native inventory exited {result.returncode}')
    return json.loads(result.stdout)


def read_inventory(host, runner, *, provider_specs=()) -> Inventory:
    """Treat malformed/native failure as uncertainty, never an empty installation."""
    if host not in ('claude', 'codex'):
        raise ValueError('Unknown host')
    plugins, markets, errors = [], [], []
    local_uncertainty = False
    version, config_root = '', None
    try:
        if host == 'codex':
            config_root = codex_config_root()
        result = runner((host, '--version'))
        if result.returncode:
            raise ValueError('CLI version unavailable')
        version = result.stdout.strip()
        data = _json(runner, (host, 'plugin', 'marketplace', 'list', '--json'))
        rows = data if host == 'claude' else data['marketplaces']
        if not isinstance(rows, list):
            raise ValueError('Unknown marketplace schema')
        for row in rows:
            if not isinstance(row, dict) or not NAME.fullmatch(row['name']):
                raise ValueError('Invalid marketplace identity')
            if host == 'claude':
                kind = row.get('source')
                raw_source = row.get('repo') if kind == 'github' else row.get('url') if kind in ('git', 'url') else None
            else:
                raw = row.get('marketplaceSource')
                raw_source = raw.get('source') if isinstance(raw, dict) else None
            source = normalize_source(raw_source)
            if not source and row['name'] == 'tomwangowa':
                raise ValueError('Marketplace source is unknown')
            markets.append(Marketplace(row['name'], source,
                                       row.get('installLocation') if host == 'claude' else row.get('root'),
                                       row.get('scope'), 'configured-git' if source else 'unknown'))
        if len({m.name for m in markets}) != len(markets):
            raise ValueError('Duplicate marketplace identity')
        if host == 'claude':
            rows = _json(runner, (host, 'plugin', 'list', '--json'))
            if not isinstance(rows, list):
                raise ValueError('Unknown plugin schema')
            for row in rows:
                identity = row['id'].split('@')
                if len(identity) != 2:
                    raise ValueError('Unknown plugin identity')
                name, marketplace = identity
                source = next((m.source for m in markets if m.name == marketplace), None)
                if name == 'superpowers' and not all((isinstance(row.get('enabled'), bool), isinstance(row.get('scope'), str),
                                                       isinstance(row.get('version'), str), isinstance(row.get('installPath'), str))):
                    plugins.append(InstalledPlugin(host, name, marketplace, source,
                        row.get('version') if isinstance(row.get('version'), str) else None,
                        row.get('installPath') if isinstance(row.get('installPath'), str) else None,
                        row.get('enabled') if isinstance(row.get('enabled'), bool) else None,
                        row.get('scope') if isinstance(row.get('scope'), str) else None))
                    local_uncertainty = True
                    continue
                if (not isinstance(row['enabled'], bool) or not isinstance(row['scope'], str)
                        or not isinstance(row['version'], str) or not isinstance(row['installPath'], str)):
                    raise ValueError('Incomplete plugin metadata')
                if name == 'superpowers':
                    root = Path(row.get('readFromFolder') or row['installPath'])
                    try:
                        manifest = json.loads((root / '.claude-plugin/plugin.json').read_text())
                        if (manifest.get('name') == name and manifest.get('version') == row['version']
                                and normalize_source(manifest.get('repository')) == EXTERNAL
                                and (root / 'skills/writing-plans/SKILL.md').is_file()):
                            source = EXTERNAL
                    except (OSError, ValueError):
                        pass
                # Local/file/unknown origins stay untrusted, but their complete
                # records still protect existing installs. Target planners can
                # keep that package without blocking unrelated known sources.
                plugins.append(InstalledPlugin(host, name, marketplace, source, row['version'],
                                               row.get('readFromFolder') or row['installPath'], row['enabled'], row['scope']))
        else:
            # A scoped query avoids the authenticated remote global catalog.
            # Unknown providers are not candidates for writes by this installer.
            for market in markets:
                try:
                    data = _json(runner, (host, 'plugin', 'list', '--marketplace', market.name, '--json'))
                    observed = _codex_plugins(data, market)
                except (ValueError, KeyError, TypeError, AttributeError, OSError, subprocess.SubprocessError):
                    if market.name == 'tomwangowa':
                        raise
                    local_uncertainty = True
                    continue
                plugins.extend(observed)
        identities = [(p.name, p.marketplace) for p in plugins]
        duplicates = {key for key in identities if identities.count(key) > 1}
        if host != 'claude' and any(name != 'superpowers' for name, _ in duplicates):
            raise ValueError('Multiple scopes for one plugin identity')
        # Claude lists user/project copies separately. Preserve every record;
        # target-specific planning still refuses to update ambiguous copies.
        local_uncertainty = local_uncertainty or any(name == 'superpowers' for name, _ in duplicates)
    except (ValueError, KeyError, TypeError, AttributeError, OSError, subprocess.SubprocessError) as error:
        errors.append(f'Inventory unverified: {error}')
    inv = Inventory(host, version, tuple(plugins), tuple(markets),
                    ('scoped-list',) + (('superpowers-inventory-unverified',) if local_uncertainty else ()), tuple(errors), config_root)
    readiness = tuple(inspect_provider(p, inv) for p in provider_specs if p.host == host and p.provider)
    verified = {dict(r.snapshot)['catalog_name']: dict(r.snapshot) for r in readiness if r.status == 'ready'}
    inv = replace(inv, marketplaces=tuple(replace(m, provenance_kind=verified[m.name]['catalog_kind'],
                  commit=verified[m.name]['catalog_commit']) if m.name in verified else m for m in inv.marketplaces))
    return replace(inv, provider_readiness=readiness)


def _codex_plugins(data, market):
    if not isinstance(data, dict) or not isinstance(data.get('installed'), list) or not isinstance(data.get('available'), list):
        raise ValueError('Unknown Codex plugin schema')
    observed = []
    for row in data['installed']:
        if (not isinstance(row['name'], str) or not NAME.fullmatch(row['name'])
                or row['pluginId'] != f"{row['name']}@{row['marketplaceName']}"
                or row['marketplaceName'] != market.name or row['installed'] is not True
                or not isinstance(row['enabled'], bool)
                or (market.source is not None and normalize_source(row.get('marketplaceSource', {}).get('source')) != market.source)):
            raise ValueError('Conflicting Codex plugin metadata')
        # source.path is a catalog path, never an installed cache root/scope.
        observed.append(InstalledPlugin('codex', row['name'], market.name, market.source, row.get('version'), None, row['enabled'], None))
    return observed


def plugin_action(spec: PluginSpec, kind: str) -> Action:
    """Construct a qualified user-level action without accepting command sources."""
    validate_catalog((spec,))
    if kind not in ('install', 'update'):
        raise ValueError('Unsupported plugin action')
    selector = f'{spec.name}@{spec.marketplace}'
    argv = ((spec.host, 'plugin', 'install' if kind == 'install' else 'update', selector, '--scope', 'user', '--json')
            if spec.host == 'claude' else ('codex', 'plugin', 'add', selector, '--json'))
    return Action(f'{spec.host}/{spec.source}/{spec.name}', kind, spec.host, selector, argv,
                  preconditions=(('source', spec.source), ('version', spec.version)))


def source_action(host: str, source: str, kind: str) -> Action:
    """Only approved providers may be added/refreshed; never replace a source."""
    source = normalize_source(source)
    if host not in ('claude', 'codex') or source not in (REPOSITORY, CLAUDE_CATALOG) or (host == 'codex' and source != REPOSITORY):
        raise ValueError('Unknown host/source')
    market = 'tomwangowa' if source == REPOSITORY else 'claude-plugins-official'
    if kind == 'add_marketplace':
        argv = ((host, 'plugin', 'marketplace', 'add', source, '--scope', 'user', '--json') if host == 'claude'
                else (host, 'plugin', 'marketplace', 'add', source, '--ref', 'main', '--json'))
    elif kind == 'refresh_marketplace':
        argv = (host, 'plugin', 'marketplace', 'update' if host == 'claude' else 'upgrade', market, '--json')
    else:
        raise ValueError('Unsupported source action')
    return Action(f'{host}/marketplace/{market}', kind, host, market, argv,
                  preconditions=(('source', source), ('effect', 'Downloads source metadata and writes host marketplace state.')))


def _git_catalog(root):
    """Read only local Git identity; never fetch or initialize a repository."""
    safe_path(root, '.git/config')
    safe_path(root, '.git/HEAD')
    def read(*args):
        result = subprocess.run(('git', '-C', str(root), *args), capture_output=True, text=True, timeout=10)
        if result.returncode:
            raise ValueError('Local catalog Git identity unavailable')
        return result.stdout.strip()
    return normalize_source(read('config', '--local', '--get', 'remote.origin.url')), read('rev-parse', '--verify', 'HEAD')


def inspect_provider(spec: PluginSpec, inventory: Inventory) -> ProviderReadiness:
    """Observe the selected catalog and payload without repairing host state."""
    descriptor = spec.provider
    state = {key: '' for key in SNAPSHOT_KEYS}
    def result(status, reason):
        return ProviderReadiness(spec.name, status, reason, tuple(sorted(state.items())))
    if inventory.errors:
        return result('unverified', 'Native inventory failed.')
    if any(p.name == spec.name for p in inventory.plugins):
        return result('preserved', 'Existing Superpowers provider retained without update, enable or replacement.')
    if 'superpowers-inventory-unverified' in inventory.capabilities:
        return result('unverified', 'A named provider could not be inventoried; absence is unknown.')
    if spec.host == 'codex' and sum(m.name in CODEX_MARKETPLACE_FILES for m in inventory.marketplaces) > 1:
        return result('unverified', 'Multiple official catalogs are exposed; native catalog selection is ambiguous.')
    spec = resolve_provider(spec, inventory)
    markets = [m for m in inventory.marketplaces if m.name == spec.marketplace]
    if not markets:
        return result('needs-native-setup', CODEX_SETUP_GUIDANCE if spec.host == 'codex' else 'Official catalog is not configured.')
    if len(markets) != 1 or descriptor is None:
        return result('unverified', 'Official catalog identity is ambiguous.')
    market = markets[0]
    state.update(catalog_name=market.name, catalog_root=market.root or '')
    try:
        if not market.root or not Path(market.root).is_absolute():
            raise ValueError('Catalog root is missing or relative')
        if Path(market.root).is_symlink():
            raise ValueError('Catalog root is a symlink')
        root = Path(market.root).resolve()
        if spec.host == 'codex':
            if not inventory.config_root or root != Path(inventory.config_root) / '.tmp/plugins':
                raise ValueError('Official catalog is outside native managed location')
            if market.source not in (None, CODEX_CATALOG):
                raise ValueError('Official catalog source conflict')
            # The audited native location and commit receipt establish the managed
            # origin; a raw URL absent from native output stays absent there.
            commit = safe_path(Path(inventory.config_root), '.tmp/plugins.sha').read_text().strip()
            safe_path(root, CODEX_MARKETPLACE_FILES[spec.marketplace])
            kind, origin = 'native-managed', CODEX_CATALOG
        else:
            if market.source != spec.source:
                raise ValueError('Configured catalog source conflict')
            marker = root / '.gcs-sha'
            git_dir = root / '.git'
            if (not git_dir.exists() and not git_dir.is_symlink()
                    and marker.is_file() and not marker.is_symlink()):
                try:
                    commit = _verified_claude_archive(root)
                except (OSError, ValueError, UnicodeError):
                    return result('unverified', 'The official catalog appears to be stored as an archive; its source cannot yet be verified. Superpowers cannot be verified using this archive. Other selected packages can continue.')
                origin, kind = market.source, 'verified-archive'
            else:
                origin, commit = _git_catalog(root)
                kind = 'configured-git'
            if origin != spec.source:
                raise ValueError('Local Git origin differs from native inventory')
        if not is_hex(commit, 40):
            raise ValueError('Catalog commit is missing or invalid')
        state.update(catalog_kind=kind, catalog_repository=origin, catalog_commit=commit)
        relative = '.claude-plugin/marketplace.json' if spec.host == 'claude' else CODEX_MARKETPLACE_FILES[spec.marketplace]
        data = json.loads(safe_path(root, relative).read_text(encoding='utf-8'))
        entries = [e for e in data['plugins'] if e['name'] == spec.name]
        if data['name'] != spec.marketplace or len(entries) != 1:
            raise ValueError('Selected catalog entry is ambiguous')
        raw = entries[0]
        state['entry_hash'] = canonical_hash(raw)
        if not descriptor.entry_hash or state['entry_hash'] != descriptor.entry_hash:
            raise ValueError('Selected raw catalog entry differs from candidate')
        source = raw['source']
        if spec.host == 'claude':
            if source != {'source': 'url', 'url': descriptor.payload_repository, 'sha': descriptor.payload_commit}:
                raise ValueError('Pinned payload origin differs')
            state.update(payload_kind='git', payload_repository=source['url'], payload_commit=source['sha'])
        else:
            if source != {'source': 'local', 'path': descriptor.payload_path}:
                raise ValueError('Relative payload entry differs')
            payload = root / descriptor.payload_path
            manifest = json.loads(safe_path(root, f'{descriptor.payload_path}/.codex-plugin/plugin.json').read_text())
            if manifest.get('name') != spec.name or manifest.get('version') != spec.version:
                raise ValueError('Managed payload manifest differs')
            state.update(payload_kind='catalog-relative', payload_path=source['path'], payload_hash=tree_hash(payload))
            if not spec.content_hash or state['payload_hash'] != spec.content_hash:
                raise ValueError('Managed payload hash is unknown or differs')
        return result('ready', 'Catalog provenance and selected entry verified; installation still requires exact native acceptance.')
    except (OSError, ValueError, KeyError, TypeError, RuntimeError, subprocess.SubprocessError) as error:
        return result('unverified', str(error))
