"""Corroborate a new Codex installation without promoting cache paths to scope."""
from __future__ import annotations

import json
import re
import hashlib
import stat
from pathlib import Path

from .catalog import REPOSITORY, safe_path, tree_hash
from .hosts import CODEX_RECEIPT_VERSIONS
from .models import InstallReceipt
from .providers import is_hex
from dataclasses import asdict


def verify_codex_install(action, spec, result, inventory, *, readiness=None):
    """Return evidence only when the native receipt, target and package agree."""
    try:
        conditions = dict(action.preconditions)
        if (action.host != 'codex' or action.kind != 'install' or spec.host != 'codex'
                or (spec.provider is None and (spec.source != REPOSITORY or spec.marketplace != 'tomwangowa'))
                or action.target != f'{spec.name}@{spec.marketplace}'
                or conditions.get('plugin_state') != '[]'
                or conditions.get('source') != spec.source or conditions.get('version') != spec.version
                or inventory.errors or inventory.cli_version not in CODEX_RECEIPT_VERSIONS
                or inventory.cli_version != conditions.get('cli_version')
                or not inventory.config_root or inventory.config_root != conditions.get('config_root')
                or result.returncode != 0 or not isinstance(result.stdout, str)):
            return False
        if spec.provider and not provider_state_matches(action, spec, readiness):
            return False
        data = json.loads(result.stdout)
        if not isinstance(data, dict):
            return False
        expected_id = f'{spec.name}@{spec.marketplace}'
        if (data.get('pluginId') != expected_id or data.get('name') != spec.name
                or data.get('marketplaceName') != spec.marketplace
                or data.get('authPolicy') not in ('ON_INSTALL', 'ON_USE')):
            return False
        version, raw_root = data.get('version'), data.get('installedPath')
        if spec.provider and version != dict(readiness.snapshot)['catalog_commit'][:8]:
            return False
        if (not isinstance(version, str) or not re.fullmatch(r'[A-Za-z0-9][A-Za-z0-9._+-]*', version)
                or not isinstance(raw_root, str)):
            return False
        root, config_root = Path(raw_root), Path(inventory.config_root)
        if not root.is_absolute() or not config_root.is_absolute() or '..' in root.parts:
            return False
        relative = f'plugins/cache/{spec.marketplace}/{spec.name}/{version}'
        # The receipt supplies the root; the audited native store layout only
        # constrains it to the previewed write target, never discovers installs.
        if root != config_root / relative:
            return False
        manifest_path = safe_path(config_root, f'{relative}/.codex-plugin/plugin.json')
        manifest = json.loads(manifest_path.read_text(encoding='utf-8'))
        if not isinstance(manifest, dict) or manifest.get('name') != spec.name or manifest.get('version') != spec.version:
            return False
        matches = [p for p in inventory.plugins if p.name == spec.name]
        markets = [m for m in inventory.marketplaces if m.name == spec.marketplace]
        if (len(matches) != 1 or len(markets) != 1 or markets[0].source not in ((None, spec.source) if spec.provider else (spec.source,))
                or markets[0].root != conditions.get('market_root')):
            return False
        plugin = matches[0]
        if (plugin.host != 'codex' or plugin.marketplace != spec.marketplace
                or plugin.source not in ((None, spec.source) if spec.provider else (spec.source,)) or plugin.version != version or plugin.enabled is not True
                or not spec.content_hash or tree_hash(root) != spec.content_hash):
            return False
        return InstallReceipt(expected_id, version, str(root), str(config_root))
    except (OSError, ValueError, TypeError, KeyError):
        return False


def provider_state_matches(action, spec, readiness, *, allow_archive_advance=False):
    """Require the same observed source sealed at the installation checkpoint."""
    conditions = dict(action.preconditions)
    if not (spec.provider and readiness and readiness.status == 'ready'
            and is_hex(dict(readiness.snapshot).get('catalog_commit'), 40)
            and conditions.get('provider_target') == json.dumps(asdict(spec.provider), sort_keys=True, separators=(',', ':'))):
        return False
    if conditions.get('provider_state') == json.dumps(readiness.snapshot, separators=(',', ':')):
        return True
    if not (allow_archive_advance and action.kind == 'install' and action.host == 'claude'
            and spec.name == 'superpowers' and spec.marketplace == 'claude-plugins-official'):
        return False
    try:
        from . import hosts
        old = dict(json.loads(conditions['provider_state']))
        new = dict(readiness.snapshot)
        old_commit, new_commit = old.pop('catalog_commit'), new.pop('catalog_commit')
        return (old.get('catalog_kind') == new.get('catalog_kind') == 'verified-archive'
                and old_commit in hosts.CLAUDE_ARCHIVE_TREES and new_commit in hosts.CLAUDE_ARCHIVE_TREES
                and old == new)
    except (ValueError, TypeError, KeyError):
        return False


def verify_claude_install(action, spec, inventory, *, readiness=None):
    """Verify user-scope inventory and the entire expected payload after native install."""
    try:
        conditions = dict(action.preconditions)
        if (action.host != 'claude' or spec.host != 'claude' or inventory.errors
                or inventory.cli_version != conditions.get('cli_version')
                or conditions.get('source') != spec.source or conditions.get('version') != spec.version
                or action.target != f'{spec.name}@{spec.marketplace}'
                or (spec.provider and not provider_state_matches(action, spec, readiness, allow_archive_advance=True))):
            return False
        matches = [p for p in inventory.plugins if p.name == spec.name]
        if len(matches) != 1:
            return False
        p = matches[0]
        expected_source = spec.provider.payload_repository if spec.provider else spec.source
        if (p.marketplace != spec.marketplace or p.source != expected_source or p.version != spec.version
                or p.enabled is not True or p.scope != 'user' or not p.root or not spec.content_hash):
            return False
        root = Path(p.root)
        if not root.is_absolute():
            return False
        manifest = json.loads(safe_path(root, '.claude-plugin/plugin.json').read_text())
        return bool(manifest.get('name') == spec.name and manifest.get('version') == spec.version
                    and _claude_payload_hash(root, inventory.cli_version) == spec.content_hash)
    except (OSError, ValueError, TypeError, KeyError):
        return False


def _claude_payload_hash(root, cli_version):
    """Ignore only the usage-marker schema inspected in Claude Code 2.1.322.

    Source/catalog hashes remain complete hashes. Cache bookkeeping is accepted
    only here, after native inventory establishes the installed package identity.
    """
    if cli_version != '2.1.322 (Claude Code)':
        return tree_hash(root)
    if root.is_symlink() or not root.is_dir():
        raise ValueError('Unsafe installed root')
    entries = []
    for path in sorted(root.rglob('*')):
        relative = path.relative_to(root)
        if path.is_symlink():
            raise ValueError('Symlink in installed payload')
        if relative.parts[0] == '.in_use':
            if len(relative.parts) == 1:
                if not path.is_dir():
                    raise ValueError('Invalid native usage directory')
                continue
            mode = path.stat().st_mode
            if (len(relative.parts) != 2 or not re.fullmatch(r'[1-9][0-9]{0,9}', path.name)
                    or not stat.S_ISREG(mode) or mode & 0o111):
                raise ValueError('Unexpected native usage entry')
            raw = path.read_bytes()
            if len(raw) > 4096:
                raise ValueError('Oversized native usage marker')
            data = json.loads(raw)
            if (not isinstance(data, dict) or set(data) - {'pid', 'procStart', 'procStartFt'}
                    or type(data.get('pid')) is not int or data['pid'] != int(path.name)
                    or any(not isinstance(data[key], str) for key in ('procStart', 'procStartFt') if key in data)):
                raise ValueError('Invalid native usage marker')
            continue
        if path.is_file():
            entries.append((relative.as_posix(), hashlib.sha256(path.read_bytes()).hexdigest()))
    return hashlib.sha256(json.dumps(entries, separators=(',', ':')).encode()).hexdigest()
