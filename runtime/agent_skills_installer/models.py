"""Immutable decisions shared by preview, execution and reporting."""
from __future__ import annotations

from dataclasses import dataclass
from typing import Literal

Host = Literal['claude', 'codex']
Platform = Literal['macos', 'windows', 'linux']


@dataclass(frozen=True)
class SkillSpec:
    name: str
    purpose: str
    invocation_intent: str
    entry: str


@dataclass(frozen=True)
class ProviderSource:
    catalog_kind: str
    catalog_repository: str
    payload_kind: str
    payload_repository: str | None
    payload_commit: str | None
    payload_path: str | None
    entry_hash: str | None


@dataclass(frozen=True)
class ProviderReadiness:
    name: str
    status: str
    reason: str
    snapshot: tuple[tuple[str, str], ...] = ()


@dataclass(frozen=True)
class NativeAcceptance:
    host: Host
    cli_version: str
    platform: Platform
    architecture: str
    catalog_name: str
    catalog_commit: str
    entry_hash: str
    manifest_version: str
    content_hash: str
    evidence_ref: str


@dataclass(frozen=True)
class PluginSpec:
    host: Host
    name: str
    marketplace: str
    source: str
    version: str
    skills: tuple[SkillSpec, ...] = ()
    commands: tuple[str, ...] = ()
    notices: tuple[str, ...] = ()
    default_selected: bool = True
    content_hash: str = ''
    provider: ProviderSource | None = None


@dataclass(frozen=True)
class InstalledPlugin:
    host: Host
    name: str
    marketplace: str
    source: str | None
    version: str | None
    root: str | None
    enabled: bool | None
    scope: str | None


@dataclass(frozen=True)
class Marketplace:
    name: str
    source: str | None
    root: str | None
    scope: str | None = None
    provenance_kind: str = 'unknown'
    commit: str | None = None


@dataclass(frozen=True)
class Inventory:
    host: Host
    cli_version: str
    plugins: tuple[InstalledPlugin, ...] = ()
    marketplaces: tuple[Marketplace, ...] = ()
    capabilities: tuple[str, ...] = ()
    errors: tuple[str, ...] = ()
    config_root: str | None = None
    provider_readiness: tuple[ProviderReadiness, ...] = ()


@dataclass(frozen=True)
class InstallReceipt:
    plugin_id: str
    cache_version: str
    root: str
    config_root: str
    write_target: str = 'codex-home'


@dataclass(frozen=True)
class Action:
    id: str
    kind: str
    host: Host | None
    target: str
    argv: tuple[str, ...]
    requires: tuple[str, ...] = ()
    preconditions: tuple[tuple[str, str], ...] = ()


@dataclass(frozen=True)
class Outcome:
    action_id: str
    status: str
    detail: str
    cancelled: bool = False
    receipt: InstallReceipt | None = None


@dataclass(frozen=True)
class Plan:
    actions: tuple[Action, ...]
    fingerprint: str = ''
    prior_results: tuple[Outcome, ...] = ()
