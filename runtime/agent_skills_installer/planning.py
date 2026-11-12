"""Pure installation decisions; the executor cannot invent new work."""
from __future__ import annotations

import hashlib
import json
from dataclasses import asdict, replace

from .hosts import CODEX_RECEIPT_VERSIONS, plugin_action, source_action
from .models import Outcome, Plan, ProviderReadiness
from .providers import target_accepted, installation_accepted, SNAPSHOT_KEYS, resolve_provider, CODEX_SETUP_GUIDANCE


def fingerprint(plan: Plan) -> str:
    """Hash every executable decision, precondition and non-command result."""
    data = {'actions': [asdict(a) for a in plan.actions], 'prior_results': [asdict(r) for r in plan.prior_results]}
    return hashlib.sha256(json.dumps(data, sort_keys=True, separators=(',', ':')).encode()).hexdigest()


def seal(actions=(), prior_results=()) -> Plan:
    plan = Plan(tuple(actions), prior_results=tuple(prior_results))
    if len({a.id for a in plan.actions}) != len(plan.actions):
        raise ValueError('Duplicate action identity')
    return replace(plan, fingerprint=fingerprint(plan))


def plugin_state(plugins) -> str:
    return json.dumps([asdict(p) for p in plugins], sort_keys=True, separators=(',', ':'))


def make_plan(catalog, inventories, selected, updates, tools, *, acceptance=(), platform='', architecture='') -> Plan:
    """Preserve uncertain installations; source preparation never implies install consent."""
    inventories = {i.host: i for i in inventories}
    actions, results, pending_sources = [], [], set()
    for spec in catalog:
        key = (spec.host, spec.name)
        action_id = f'{spec.host}/{spec.source}/{spec.name}'
        inv = inventories.get(spec.host)
        if inv is None:
            continue
        spec = resolve_provider(spec, inv)
        if key not in selected:
            results.append(Outcome(action_id, 'skipped', 'Not selected.'))
            continue
        if inv.errors:
            results.append(Outcome(action_id, 'unverified', '; '.join(inv.errors)))
            continue
        matches = tuple(p for p in inv.plugins if p.name == spec.name)
        source = next((m for m in inv.marketplaces if m.name == spec.marketplace), None)
        readiness = None
        if spec.provider:
            if matches:
                results.append(Outcome(action_id, 'preserved', 'Existing Superpowers provider retained; no update, enable, duplicate installation or downgrade.'))
                continue
            readiness = next((r for r in inv.provider_readiness if r.name == spec.name), None)
            if readiness is None:
                missing = source is None and 'superpowers-inventory-unverified' not in inv.capabilities
                reason = (CODEX_SETUP_GUIDANCE if spec.host == 'codex' else 'Official catalog is not configured.') if missing else 'Provider observations are unavailable.'
                readiness = ProviderReadiness(spec.name, 'needs-native-setup' if missing else 'unverified', reason,
                                              tuple(sorted((key, '') for key in SNAPSHOT_KEYS)))
            if not target_accepted(spec, acceptance, inv.cli_version, platform, architecture):
                results.append(Outcome(action_id, 'unverified', 'Superpowers pending: exact native acceptance or complete payload hash is missing. ' + readiness.reason))
                continue
            if not source and spec.host == 'claude' and readiness.status == 'needs-native-setup':
                action = source_action(spec.host, spec.source, 'add_marketplace')
                actions.append(replace(action, preconditions=action.preconditions + (
                    ('plugin_state', plugin_state(matches)), ('cli_version', inv.cli_version),
                    ('provider_state', json.dumps(readiness.snapshot, separators=(',', ':'))),
                    ('provider_target', json.dumps(asdict(spec.provider), sort_keys=True, separators=(',', ':'))),
                    ('platform', platform), ('architecture', architecture))))
                results.append(Outcome(action_id, 'skipped', 'Official source preparation needs separate consent and a new preview.'))
                continue
            if not installation_accepted(spec, readiness, acceptance, inv.cli_version, platform, architecture):
                results.append(Outcome(action_id, 'unverified', 'Superpowers pending: ' + readiness.reason))
                continue

        if source and source.source != spec.source and not (spec.provider and spec.host == 'codex' and source.source is None):
            results.append(Outcome(action_id, 'unverified', 'Marketplace source conflict; no replacement.'))
            continue
        if matches:
            p = matches[0]
            if spec.host == 'codex':
                results.append(Outcome(action_id, 'unverified', 'Existing Codex provider preserved; update ownership is not verified.'))
                continue
            if len(matches) != 1:
                results.append(Outcome(action_id, 'unverified',
                    f'{spec.name} has more than one installed copy. All copies will be kept; manage this plugin in Claude Code if an update is needed.'))
                continue
            if p.source != spec.source or p.enabled is not True or p.scope != 'user' or not p.root or not p.version:
                results.append(Outcome(action_id, 'unverified', 'Existing provider preserved: disabled, conflicting or unknown scope/root/version.'))
                continue
            if key not in updates:
                results.append(Outcome(action_id, 'preserved', f'Existing {p.version} retained; update not selected.'))
                continue
        if spec.host == 'codex' and (inv.cli_version not in CODEX_RECEIPT_VERSIONS or not inv.config_root):
            results.append(Outcome(action_id, 'unverified', 'Codex new-install verification requires audited CLI 0.167.0 and a known config root.'))
            continue
        if not source:
            identity = (spec.host, spec.source)
            if identity not in pending_sources:
                action = source_action(spec.host, spec.source, 'add_marketplace')
                if spec.provider:
                    action = replace(action, preconditions=action.preconditions + (
                        ('plugin_state', plugin_state(matches)), ('cli_version', inv.cli_version),
                        ('provider_state', json.dumps(readiness.snapshot, separators=(',', ':'))),
                        ('provider_target', json.dumps(asdict(spec.provider), sort_keys=True, separators=(',', ':'))),
                        ('platform', platform), ('architecture', architecture)))
                actions.append(action)
                pending_sources.add(identity)
            results.append(Outcome(action_id, 'skipped', 'Source preparation requires separate consent, then a new installation preview.'))
            continue
        if not spec.provider and f'catalog-verified:{spec.marketplace}' not in inv.capabilities:
            results.append(Outcome(action_id, 'unverified', 'Marketplace content has not been verified against this bundle.'))
            continue
        missing = tuple(tool for tool in spec.commands if not tools.get(tool, False))
        if missing:
            results.append(Outcome(action_id, 'skipped', 'Missing tools: ' + ', '.join(missing)))
            continue
        action = plugin_action(spec, 'update' if matches else 'install')
        action = replace(action, preconditions=action.preconditions + (
            ('plugin_state', plugin_state(matches)), ('cli_version', inv.cli_version),
            ('market_root', source.root or ''), ('tools', json.dumps(spec.commands)),
        ))
        if spec.provider:
            action = replace(action, preconditions=action.preconditions + (
                ('provider_state', json.dumps(readiness.snapshot, separators=(',', ':'))),
                ('provider_target', json.dumps(asdict(spec.provider), sort_keys=True, separators=(',', ':'))),
                ('platform', platform), ('architecture', architecture)))
        if spec.host == 'codex':
            action = replace(action, preconditions=action.preconditions + (('config_root', inv.config_root),))
        actions.append(action)
    return seal(actions, results)
