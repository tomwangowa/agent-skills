"""Pure installation decisions; the executor cannot invent new work."""
from __future__ import annotations

import hashlib
import json
from dataclasses import asdict, replace

from .hosts import plugin_action, source_action
from .models import Outcome, Plan
from .providers import CODEX_CATALOG, CODEX_MARKETPLACE_FILES, CODEX_SETUP_GUIDANCE, resolve_provider


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
    """Plan native installs from marketplace identity and user selection."""
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
            results.append(Outcome(action_id, 'skipped', 'The installed package list could not be read; this package was left unchanged.'))
            continue
        matches = tuple(p for p in inv.plugins if p.name == spec.name)
        source = next((m for m in inv.marketplaces if m.name == spec.marketplace), None)
        if spec.provider:
            if matches:
                results.append(Outcome(action_id, 'preserved', 'Existing Superpowers installation retained.'))
                continue
            if spec.host == 'codex' and sum(m.name in CODEX_MARKETPLACE_FILES for m in inv.marketplaces) > 1:
                results.append(Outcome(action_id, 'skipped', 'More than one official Codex Superpowers catalog is configured. Choose one in /plugins, then try again.'))
                continue
            if spec.host == 'codex' and source is None:
                results.append(Outcome(action_id, 'skipped', CODEX_SETUP_GUIDANCE))
                continue

        if source and source.source != spec.source and not (spec.provider and spec.host == 'codex'
                                                             and source.name in CODEX_MARKETPLACE_FILES
                                                             and source.source in (None, CODEX_CATALOG)):
            results.append(Outcome(action_id, 'skipped', 'Marketplace source conflict; no replacement.'))
            continue
        if source and not source.root:
            results.append(Outcome(action_id, 'skipped', 'The marketplace location is unavailable; this package was left unchanged.'))
            continue
        if matches:
            p = matches[0]
            if spec.host == 'codex':
                results.append(Outcome(action_id, 'skipped', 'Existing Codex installation is preserved; updates are not available here.'))
                continue
            if len(matches) != 1:
                results.append(Outcome(action_id, 'skipped',
                    f'{spec.name} has more than one installed copy. All copies will be kept; manage this plugin in Claude Code if an update is needed.'))
                continue
            if p.source != spec.source or p.enabled is not True or p.scope != 'user' or not p.root:
                results.append(Outcome(action_id, 'skipped', 'Existing provider preserved: disabled, conflicting or unknown scope/root.'))
                continue
            if key not in updates:
                results.append(Outcome(action_id, 'preserved', 'Existing installation retained; update not selected.'))
                continue
        if spec.host == 'codex' and not inv.config_root:
            results.append(Outcome(action_id, 'skipped', 'Codex settings location could not be determined.'))
            continue
        if not source:
            if spec.provider and spec.host == 'codex':
                results.append(Outcome(action_id, 'skipped', CODEX_SETUP_GUIDANCE))
                continue
            identity = (spec.host, spec.source)
            if identity not in pending_sources:
                action = source_action(spec.host, spec.source, 'add_marketplace')
                actions.append(action)
                pending_sources.add(identity)
            results.append(Outcome(action_id, 'skipped', 'Source preparation requires separate consent, then a new installation preview.'))
            continue
        missing = tuple(tool for tool in spec.commands if not tools.get(tool, False))
        if missing:
            results.append(Outcome(action_id, 'skipped', 'Missing tools: ' + ', '.join(missing)))
            continue
        action = plugin_action(spec, 'update' if matches else 'install')
        action = replace(action, preconditions=action.preconditions + (
            ('plugin_state', plugin_state(matches)),
            ('market_root', source.root or ''), ('tools', json.dumps(spec.commands)),
        ))
        if spec.host == 'codex':
            action = replace(action, preconditions=action.preconditions + (('config_root', inv.config_root),))
        actions.append(action)
    return seal(actions, results)
