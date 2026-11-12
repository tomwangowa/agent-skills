"""Qualified native removal plans; uncertainty never authorizes deletion."""
from __future__ import annotations

from collections import Counter
from dataclasses import asdict, dataclass
import json
from pathlib import Path
import re
import subprocess

from .catalog import EXTERNAL, NAME, tree_hash
from .models import Action, Outcome
from .planning import seal
from .providers import CODEX_CATALOG, official_catalog_names
from .receipts import _claude_payload_hash

CLAUDE_REMOVAL_VERSION = '2.1.322 (Claude Code)'
CODEX_REMOVE_INTERFACE = 'qualified-plugin-remove-json-v1'


def codex_removal_supported(runner):
    """Detect the qualified native remove command and its JSON receipt without mutating state."""
    try:
        result = runner(('codex', 'plugin', 'remove', '--help'))
        help_text = re.sub(r'\x1b\[[0-?]*[ -/]*[@-~]', '',
                           f'{result.stdout or ""}\n{result.stderr or ""}').lower()
        compact = re.sub(r'\s+', '', help_text)
        return (result.returncode == 0 and 'usage:' in help_text and 'codexpluginremove' in compact
                and '--json' in help_text and 'plugin[@marketplace]' in compact)
    except (OSError, subprocess.SubprocessError, AttributeError, TypeError):
        return False


@dataclass(frozen=True)
class RemovalOption:
    """One native identity, its registered copies and any reason to keep it."""
    spec: object
    plugin: object
    records: tuple
    cli_version: str
    config_root: str
    protected_trees: tuple
    reason: str = ''
    config_identity: tuple = ()
    default_selected: bool = False
    cache_state: tuple = ()

    @property
    def key(self):
        return (self.plugin.host, self.plugin.name, self.plugin.marketplace)

    @property
    def host(self):
        return self.plugin.host

    @property
    def name(self):
        return f'{self.plugin.name}@{self.plugin.marketplace}'

    @property
    def skills(self):
        return self.spec.skills


def _state(records):
    return json.dumps(sorted((asdict(p) for p in records), key=lambda p: json.dumps(p, sort_keys=True)),
                      sort_keys=True, separators=(',', ':'))


def _config_identity(config_root):
    base = Path(config_root)
    if not base.is_absolute() or '..' in base.parts:
        raise ValueError('Unidentified configuration directory')
    physical = base.resolve(strict=True)
    info = physical.stat()
    if not physical.is_dir():
        raise ValueError('Configuration directory is unavailable')
    # Keep legitimate stable ancestor links (including platform aliases), but
    # seal their destination and filesystem identity before user confirmation.
    return (str(physical), str(info.st_dev), str(info.st_ino))


def removal_config_matches(action, config_root):
    """Reject a redirected/replaced profile before querying or mutating it."""
    try:
        conditions = dict(action.preconditions)
        return (conditions['config_root'] == str(config_root)
                and conditions['config_identity'] == json.dumps(_config_identity(config_root), separators=(',', ':')))
    except (OSError, ValueError, TypeError, KeyError, RuntimeError):
        return False


def _cache_root(plugin, config_root):
    root = Path(plugin.root or '')
    base = Path(config_root)
    if (not root.is_absolute() or not base.is_absolute() or '..' in root.parts or '..' in base.parts
            or not NAME.fullmatch(plugin.name) or not NAME.fullmatch(plugin.marketplace)
            or not isinstance(plugin.version, str) or not plugin.version
            or Path(plugin.version).name != plugin.version or plugin.version in ('.', '..')):
        raise ValueError('Unidentified installed location')
    expected = base / 'plugins/cache' / plugin.marketplace / plugin.name / plugin.version
    if root != expected:
        raise ValueError('Installed location is outside the identified native cache')
    path = base
    for part in ('', 'plugins', 'cache', plugin.marketplace, plugin.name, plugin.version):
        if part:
            path /= part
        if path.is_symlink() or not path.is_dir():
            raise ValueError('Installed location contains a link or is unavailable')
    manifest_path = root / '.claude-plugin/plugin.json'
    if (root / '.claude-plugin').is_symlink() or manifest_path.is_symlink():
        raise ValueError('Installed manifest is linked')
    manifest = json.loads(manifest_path.read_text(encoding='utf-8'))
    if manifest.get('name') != plugin.name or manifest.get('version') != plugin.version:
        raise ValueError('Installed manifest does not match the native record')
    return root


def _codex_cache_root(plugin, config_root):
    base = Path(config_root)
    if (not base.is_absolute() or '..' in base.parts
            or not NAME.fullmatch(plugin.name) or not NAME.fullmatch(plugin.marketplace)
            or not isinstance(plugin.version, str) or not plugin.version
            or Path(plugin.version).name != plugin.version or plugin.version in ('.', '..')):
        raise ValueError('Unidentified Codex plugin cache')
    root = base / 'plugins/cache' / plugin.marketplace / plugin.name
    path = base
    for part in ('plugins', 'cache', plugin.marketplace, plugin.name):
        path /= part
        if path.is_symlink() or not path.is_dir():
            raise ValueError('Codex plugin cache contains a link or is unavailable')
    version_root = root / plugin.version
    if version_root.is_symlink() or not version_root.is_dir():
        raise ValueError('Codex installed version is unavailable or linked')
    return root


def _source_matches(spec, plugin):
    if spec.name == 'superpowers':
        if plugin.source == EXTERNAL:
            return True
        return (plugin.host == 'codex' and plugin.source == CODEX_CATALOG
                and plugin.marketplace in official_catalog_names('codex'))
    return plugin.source == spec.source and plugin.marketplace == spec.marketplace


def _protected(records, config_root):
    # A user and project can share a cache. Seal the project payload too, so a
    # successful command cannot hide collateral deletion of that shared copy.
    return tuple(sorted({(str(_cache_root(p, config_root)),
                          _claude_payload_hash(_cache_root(p, config_root), CLAUDE_REMOVAL_VERSION))
                         for p in records if p.scope != 'user'}))


def removal_options(catalog, inventories, claude_root, *, codex_remove_supported=False):
    """List installed catalog names without equating a name with trusted origin."""
    options = []
    specs = {(s.host, s.name): s for s in catalog}
    for inv in inventories:
        groups = {}
        for plugin in inv.plugins:
            if (inv.host, plugin.name) in specs:
                groups.setdefault((plugin.name, plugin.marketplace), []).append(plugin)
        for key, values in sorted(groups.items()):
            records = tuple(values)
            users = [p for p in records if p.scope == 'user']
            plugin = users[0] if users else records[0]
            spec = specs[(inv.host, plugin.name)]
            config_root = str(claude_root) if inv.host == 'claude' else inv.config_root or ''
            reason, trees, identity, cache_state = '', (), (), ()
            if inv.errors:
                reason = 'The installed-plugin list could not be read reliably. Nothing will be removed.'
            elif inv.host == 'codex' and not codex_remove_supported:
                reason = ('This Codex CLI does not expose the qualified plugin removal command with JSON output. '
                          'Kept unchanged.')
            elif inv.host == 'claude' and inv.cli_version != CLAUDE_REMOVAL_VERSION:
                reason = 'Personal removal is not verified for this Claude Code version. Kept unchanged.'
            elif inv.host == 'claude' and (len(users) != 1
                                           or any(p.scope not in ('user', 'project', 'local', 'managed') for p in records)):
                reason = ('Only project/local/managed installations were found; they will be kept.' if not users
                          else 'The personal installation is ambiguous. All copies will be kept.')
            elif inv.host == 'codex' and (len(records) != 1 or plugin.scope is not None
                                          or not isinstance(plugin.version, str) or not plugin.version):
                reason = 'The Codex installation identity is ambiguous. Kept unchanged.'
            elif (not NAME.fullmatch(plugin.marketplace)
                  or any(not _source_matches(spec, p) for p in records)):
                reason = 'The installed source could not be identified as this package. Kept unchanged.'
            else:
                try:
                    identity = _config_identity(config_root)
                    if inv.host == 'claude':
                        _cache_root(plugin, config_root)
                        trees = _protected(records, config_root)
                    else:
                        cache_root = _codex_cache_root(plugin, config_root)
                        cache_state = (str(cache_root), tree_hash(cache_root))
                    if identity != _config_identity(config_root):
                        raise ValueError('Configuration directory changed during preview')
                except (OSError, ValueError, TypeError, AttributeError, RuntimeError):
                    reason = 'The installed files or project copies could not be checked safely. Kept unchanged.'
            options.append(RemovalOption(spec, plugin, records, inv.cli_version, config_root, trees, reason,
                                         config_identity=identity, cache_state=cache_state))
    return tuple(options)


def make_removal_plan(options, selected):
    """Seal selected, identified native targets; never infer a provider."""
    keys = {o.key for o in options}
    if not selected <= keys:
        raise ValueError('Removal selection contains an unknown target')
    actions, prior = [], []
    for option in options:
        if option.key not in selected:
            continue
        p = option.plugin
        action_id = f'remove/{p.host}/{p.marketplace}/{p.name}'
        if option.reason:
            prior.append(Outcome(action_id, 'preserved', option.reason))
            continue
        target = f'{p.name}@{p.marketplace}'
        if p.host == 'claude':
            argv = ('claude', 'plugin', 'uninstall', target, '--scope', 'user', '--keep-data', '--json')
            extra = (('scope', 'user'),
                     ('protected_trees', json.dumps(option.protected_trees, separators=(',', ':'))))
        else:
            argv = ('codex', 'plugin', 'remove', target, '--json')
            extra = (('scope', 'shared-cache'), ('remove_interface', CODEX_REMOVE_INTERFACE),
                     ('cache_root', option.cache_state[0]),
                     ('cache_hash', option.cache_state[1]))
        preconditions = (('cli_version', option.cli_version), ('config_root', option.config_root),
                         ('config_identity', json.dumps(option.config_identity, separators=(',', ':'))),
                         ('version', p.version or ''), ('source', p.source or ''),
                         ('plugin_state', _state(option.records)), *extra)
        actions.append(Action(action_id, 'remove', p.host, target, argv, preconditions=preconditions))
    return seal(actions, tuple(prior))


def recheck_removal(action, inventory, config_root, *, codex_remove_supported=False):
    """Require the same native identity, profile, registration and cache state."""
    try:
        c = dict(action.preconditions)
        name, market = action.target.split('@')
        records = tuple(p for p in inventory.plugins if p.name == name and p.marketplace == market)
        if (action.kind != 'remove' or inventory.host != action.host or inventory.errors
                or c['cli_version'] != inventory.cli_version or c['config_root'] != str(config_root)
                or not removal_config_matches(action, config_root) or c['plugin_state'] != _state(records)):
            return False
        if action.host == 'claude':
            users = [p for p in records if p.scope == 'user']
            if (inventory.cli_version != CLAUDE_REMOVAL_VERSION or c['scope'] != 'user'
                    or len(users) != 1
                    or action.argv != ('claude', 'plugin', 'uninstall', action.target, '--scope', 'user', '--keep-data', '--json')):
                return False
            _cache_root(users[0], config_root)
            return c['protected_trees'] == json.dumps(_protected(records, config_root), separators=(',', ':'))
        if action.host == 'codex':
            if (not codex_remove_supported or c['remove_interface'] != CODEX_REMOVE_INTERFACE
                    or c['scope'] != 'shared-cache'
                    or len(records) != 1 or records[0].scope is not None
                    or records[0].version != c['version'] or records[0].source != c['source']
                    or action.argv != ('codex', 'plugin', 'remove', action.target, '--json')):
                return False
            root = _codex_cache_root(records[0], config_root)
            return (str(root) == c['cache_root'] and tree_hash(root) == c['cache_hash'])
        return False
    except (OSError, ValueError, TypeError, KeyError, AttributeError, RuntimeError):
        return False


def verify_removal(action, result, before, after):
    """Corroborate native success with target absence and preserved other copies."""
    try:
        c = dict(action.preconditions)
        name, market = action.target.split('@')
        data = json.loads(result.stdout if action.host == 'codex'
                          else result.stdout.strip().splitlines()[-1])
        if (action.kind != 'remove' or action.host not in ('claude', 'codex')
                or before.host != action.host or after.host != action.host
                or result.returncode != 0 or before.errors or after.errors
                or before.cli_version != c['cli_version'] or after.cli_version != before.cli_version
                or (action.host == 'codex' and (before.config_root != c['config_root']
                                                or after.config_root != c['config_root']))
                or not removal_config_matches(action, c['config_root'])):
            return False
        target = lambda p: p.name == name and p.marketplace == market
        if c['plugin_state'] != _state(tuple(p for p in before.plugins if target(p))):
            return False
        if action.host == 'claude':
            if (before.cli_version != CLAUDE_REMOVAL_VERSION or data.get('command') != 'uninstall'
                    or data.get('outcome') != 'ok' or data.get('pluginId') != action.target
                    or data.get('scope') != 'user' or data.get('keptData') is not True):
                return False
            removed = [p for p in before.plugins if target(p) and p.scope == 'user']
            if len(removed) != 1:
                return False
            expected = [p for p in before.plugins if not (target(p) and p.scope == 'user')]
            if Counter(after.plugins) != Counter(expected):
                return False
            records = tuple(p for p in after.plugins if target(p))
            return c['protected_trees'] == json.dumps(_protected(records, c['config_root']), separators=(',', ':'))
        if (c['remove_interface'] != CODEX_REMOVE_INTERFACE or data.get('pluginId') != action.target
                or data.get('name') != name or data.get('marketplaceName') != market
                or action.argv != ('codex', 'plugin', 'remove', action.target, '--json')):
            return False
        removed = [p for p in before.plugins if target(p)]
        expected = [p for p in before.plugins if not target(p)]
        if (len(removed) != 1 or Counter(after.plugins) != Counter(expected)
                or Counter(after.marketplaces) != Counter(before.marketplaces)):
            return False
        cache_root = Path(c['cache_root'])
        return not cache_root.exists() and not cache_root.is_symlink()
    except (OSError, ValueError, TypeError, KeyError, AttributeError, IndexError, RuntimeError):
        return False
