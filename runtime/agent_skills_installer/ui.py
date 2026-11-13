"""Interactive source, dependency, installation and journal consent boundaries."""
from __future__ import annotations

import json
import os
import shutil
import subprocess
import sys
from dataclasses import replace
from pathlib import Path

from .catalog import REPOSITORY
from .dependencies import dependency_action, detect_tools, missing_dependencies
from .execution import execute
from .hosts import read_inventory, source_action
from .journal import apply_journal, journal_preview, existing_journal
from .planning import make_plan, plugin_state, seal
from .providers import CODEX_CATALOG, CODEX_MARKETPLACE_FILES, resolve_provider
from .selection import SelectionCancelled, package_lines
from .progress import PackageProgress
from .process import run_json_command


class Cancelled(Exception):
    pass


def native_runner(argv, *, on_stderr=None, on_wait=None):
    """Inventory is captured; mutation keeps native prompts and permissions visible."""
    reading = (argv[1:] == ('--version',)
               or (len(argv) > 2 and argv[1] == 'plugin' and 'list' in argv)
               or argv[1:] == ('plugin', 'remove', '--help'))
    if not reading and len(argv) > 2 and argv[1] == 'plugin' and '--json' in argv:
        if on_stderr is not None and on_wait is not None:
            return run_json_command(argv, on_stderr, on_wait)
        # Direct callers also retain JSON; stderr/stdin remain attached.
        return subprocess.run(argv, text=True, stdout=subprocess.PIPE, timeout=600)
    return subprocess.run(argv, text=True, capture_output=reading, timeout=30 if reading else 600)


def source_matches(spec, market):
    if not market or market.name != spec.marketplace or not market.root:
        return False
    try:
        if spec.provider and spec.host == 'codex':
            return (market.name in CODEX_MARKETPLACE_FILES
                    and market.source in (None, CODEX_CATALOG))
        return market.source == spec.source
    except (TypeError, ValueError):
        return False


def run(catalog, input_fn, output, runner, *, acceptance=None, platform_name=None, architecture=None,
        package_selector=None, progress=None):
    """Run explicit menus; redirected output never implies approval."""
    def say(message):
        print(message, file=output)

    progress = progress or PackageProgress(output)

    prior = []
    configuration_failed = False
    bootstrap = os.environ.get('AGENT_SKILLS_BOOTSTRAP_RESULT')
    if bootstrap:
        say('Earlier confirmed operations: ' + bootstrap)
    if not output.isatty():
        say('Interactive terminal required. No operation was approved or executed.')
        return 2

    def ask(prompt):
        try:
            value = input_fn(prompt).strip()
        except (EOFError, KeyboardInterrupt):
            raise Cancelled() from None
        if value.lower() == 'q':
            raise Cancelled()
        return value

    def numbers(prompt, size, default=frozenset()):
        while True:
            value = ask(prompt)
            if not value and default is not None:
                return default
            if value.lower() == 'none':
                return frozenset()
            try:
                chosen = frozenset(int(s.strip()) - 1 for s in value.split(','))
                if not chosen or min(chosen) < 0 or max(chosen) >= size:
                    raise ValueError()
                return chosen
            except ValueError:
                say('Choose valid comma-separated numbers, none, or q to cancel.')

    def report(results):
        for result in results:
            if result.detail == 'Not selected.':
                continue
            say(f'{result.action_id.rsplit("/", 1)[-1]}: {result.status}: {result.detail}')
            say('')

    def perform(plan):
        # Preserved packages have no command, but still get a separate result.
        for result in plan.prior_results:
            progress.retained(result)
        return execute(plan, plan.fingerprint, runner, recheck, verify, on_event=progress.event)

    def preview(plan):
        for action in plan.actions:
            conditions = dict(action.preconditions)
            say(f'{action.kind}: {action.host or "system"} / {action.target}')
            if 'source' in conditions:
                say('  Source: ' + conditions['source'])
            if 'version' in conditions:
                say('  Expected version: ' + conditions['version'])
            if 'config_root' in conditions:
                say('  Codex settings/cache target: ' + conditions['config_root'])
            if 'effect' in conditions:
                say('  ' + conditions['effect'])
            say('')
        report(plan.prior_results)

    def package_preview(plan):
        say('Packages to install or update:')
        names = [action.target.split('@', 1)[0] for action in plan.actions
                 if action.kind in ('install', 'update')]
        if names:
            for name in names:
                say('  ' + name)
        else:
            say('  None')

    def inventory(hosts):
        return tuple(read_inventory(host, runner, include_version=False,
                                    include_provider_details=False) for host in hosts)

    def journal_runtime_ready(specs, selected):
        """Offer journal setup only when the selected plugin appears installed."""
        targets = tuple(s for s in specs if s.name == 'work-journal' and (s.host, s.name) in selected)
        fresh = {inv.host: inv for inv in inventory(tuple(s.host for s in targets))}
        for spec in targets:
            inv = fresh.get(spec.host)
            if not inv or inv.errors:
                return False
            matches = [p for p in inv.plugins if p.name == spec.name
                       and p.marketplace == spec.marketplace and p.enabled is True]
            if len(matches) != 1:
                return False
        return bool(targets)

    def verify(action, native_result):
        if action.kind == 'dependency':
            return detect_tools((action.target,)).get(action.target, False)
        inv = read_inventory(action.host, runner, include_version=False,
                             include_provider_details=False)
        if inv.errors:
            return False
        conditions = dict(action.preconditions)
        if action.kind in ('add_marketplace', 'refresh_marketplace'):
            return any(m.name == action.target and m.source == conditions['source'] and m.root and Path(m.root).is_dir() for m in inv.marketplaces)
        return True

    def recheck(action):
        conditions = dict(action.preconditions)
        if action.kind == 'dependency':
            return bool(shutil.which(conditions['manager']) == conditions['manager_path']
                        and not detect_tools((action.target,)).get(action.target, False))
        inv = read_inventory(action.host, runner, include_version=False,
                             include_provider_details=False)
        if inv.errors:
            return False
        if action.kind in ('add_marketplace', 'refresh_marketplace'):
            markets = [m for m in inv.marketplaces if m.name == action.target]
            return (not markets if action.kind == 'add_marketplace' else
                    len(markets) == 1 and markets[0].source == conditions['source'])
        name, market_name = action.target.split('@')
        spec = next(p for p in catalog if p.host == action.host and p.name == name)
        spec = resolve_provider(spec, inv)
        market = next((m for m in inv.marketplaces if m.name == market_name), None)
        matches = tuple(p for p in inv.plugins if p.name == name)
        if action.host == 'codex':
            target = Path(inv.config_root)
            for part in ('plugins', 'cache', market_name):
                target /= part
                if target.is_symlink() or (target.exists() and not target.is_dir()):
                    return False
            target /= name
            # An unregistered cache may be personal or incomplete; absence from
            # native inventory is not permission to replace its files.
            if target.exists() or target.is_symlink():
                return False
        source_ok = source_matches(spec, market)
        return bool(source_ok and market and market.root == conditions['market_root']
                    and (action.host != 'codex' or inv.config_root == conditions.get('config_root'))
                    and plugin_state(matches) == conditions['plugin_state']
                    and all(detect_tools(spec.commands).values()))

    try:
        hosts = []
        supported_hosts = {spec.host for spec in catalog}
        for host in ('claude', 'codex'):
            if host not in supported_hosts:
                continue
            if shutil.which(host):
                hosts.append(host)
                say(f'{len(hosts)}. {host}')
            else:
                say(f'{host}: unavailable; install the CLI manually to select it.')
        if not hosts:
            return 1
        indices = numbers('Hosts (numbers; q to cancel): ', len(hosts), None)
        if not indices:
            raise Cancelled()
        hosts = tuple(hosts[i] for i in sorted(indices))
        specs = tuple(p for p in catalog if p.host in hosts)
        invs = inventory(hosts)
        selected_indices = None
        while True:
            specs = tuple(resolve_provider(p, next(inv for inv in invs if inv.host == p.host)) for p in specs)
            defaults = (frozenset(i for i, p in enumerate(specs) if p.default_selected)
                        if selected_indices is None else selected_indices)
            if package_selector is None:
                lines, spans = package_lines(specs, defaults)
                starts = {start: index for index, (start, _) in enumerate(spans)}
                for index, line in enumerate(lines):
                    say(f'{starts[index] + 1}. {line.strip()}' if index in starts else line)
                selected_indices = numbers('Packages (Enter = checked defaults; none; q): ', len(specs), defaults)
            else:
                selected_indices = package_selector(specs, defaults, output)
                if not isinstance(selected_indices, frozenset) or not selected_indices <= frozenset(range(len(specs))):
                    raise ValueError('Invalid package selection; no operation approved.')
            if not selected_indices:
                if prior:
                    say('No packages selected. Earlier confirmed operations are retained:')
                    report(prior)
                else:
                    say('No packages selected. No changes made.')
                return 1 if any(r.status in ('failed', 'unverified') for r in prior) else 0
            selected = frozenset((specs[i].host, specs[i].name) for i in selected_indices)
            blocked_hosts = set()
            for inv in invs:
                if not any(host == inv.host for host, _ in selected):
                    continue
                if inv.errors:
                    blocked_hosts.add(inv.host)
                    app = 'Claude Code' if inv.host == 'claude' else 'Codex'
                    say(f'Cannot read the installed plugins from {app}.')
                    say(f'No selected {app} plugins will be installed or updated.')
                    say('Other selected hosts can continue. Do not remove existing plugins as a workaround.')
                    for error in inv.errors:
                        if 'Multiple scopes for one plugin identity' in error:
                            say('  The host reported the same plugin in more than one install location, so this installer cannot safely decide which copy to change.')
                        else:
                            say('  Details: ' + error)
                    continue
                groups = {}
                for installed in inv.plugins:
                    groups.setdefault((installed.name, installed.marketplace), []).append(installed)
                for (name, _), copies in groups.items():
                    if len(copies) < 2 or (inv.host, name) not in selected:
                        continue
                    locations = list(dict.fromkeys({'user': 'your account', 'project': 'a project',
                                     'local': 'your local project settings'}.get(p.scope, 'an unknown install location')
                                     for p in copies))
                    say(f'{json.dumps(name)}: already installed for {" and ".join(locations)}. All existing copies will be kept.')
                    say('This installer will not update these copies. Other selected packages can continue.')
            if all(host in blocked_hosts for host, _ in selected):
                if prior:
                    say('Earlier confirmed operations are retained:')
                    report(prior)
                return 1
            existing = []
            for spec in specs:
                if (spec.host, spec.name) not in selected or spec.provider or spec.host in blocked_hosts:
                    continue
                inv = next(inv for inv in invs if inv.host == spec.host)
                copies = [p for p in inv.plugins if p.name == spec.name]
                if (spec.host == 'claude' and len(copies) == 1 and copies[0].scope == 'user'
                        and copies[0].source == spec.source and copies[0].enabled is True
                        and copies[0].root):
                    existing.append((spec.host, spec.name))
            existing.sort()
            for i, key in enumerate(existing):
                say(f'{i + 1}. {key[1]}: already installed; the current installation will be kept.')
            if existing:
                say('Press Enter to keep these installations. To request an update instead, enter its number.')
            updates = frozenset(existing[i] for i in numbers('Updates (Enter = keep current installations; q = cancel): ', len(existing)))

            sources = []
            for inv in invs:
                if inv.errors:
                    continue
                for source in sorted({p.source for p in specs if p.host == inv.host and (p.host, p.name) in selected}):
                    chosen = [p for p in specs if p.host == inv.host and p.source == source and (p.host, p.name) in selected]
                    if source != REPOSITORY:
                        proposal = make_plan(chosen, (inv,), selected, updates, {}, acceptance=acceptance,
                                             platform=platform_name, architecture=architecture)
                        sources.extend(a for a in proposal.actions if a.kind == 'add_marketplace')
                        continue
                    market = next((m for m in inv.marketplaces if m.name == 'tomwangowa'), None)
                    if market and market.source != source:
                        say('Marketplace source conflict; affected items will not change.')
                    elif not market or any(not source_matches(p, market) for p in chosen):
                        sources.append(source_action(inv.host, source, 'refresh_marketplace' if market else 'add_marketplace'))
            if sources:
                plan = seal(sources)
                say('Source preparation: downloads and host marketplace writes are separate from plugin installation.')
                preview(plan)
                if ask('Approve source preparation? [y/N/q] ').lower() == 'y':
                    outcomes = perform(plan)
                    prior.extend(outcomes)
                    if any(r.cancelled for r in outcomes):
                        raise Cancelled()
                    invs = inventory(hosts)

            tools = detect_tools({c for p in specs for c in p.commands})
            potential_tools = {tool: True for spec in specs for tool in spec.commands}
            potential = make_plan(specs, invs, selected, updates, potential_tools)
            installable_ids = {action.id for action in potential.actions
                               if action.kind in ('install', 'update')}
            eligible = tuple(spec for spec in specs
                             if spec.host not in blocked_hosts
                             and f'{spec.host}/{spec.source}/{spec.name}' in installable_ids)
            missing = missing_dependencies(eligible, selected, tools)
            if missing:
                bundle_root = Path(__file__).resolve().parents[2]
                file = bundle_root / 'dependencies.json'
                if not file.exists():
                    file = bundle_root / 'installer/dependencies.json'
                mapping = json.loads(file.read_text(encoding='utf-8'))
                platform = 'windows' if sys.platform == 'win32' else 'macos' if sys.platform == 'darwin' else 'linux'
                managers = frozenset(m for m in ('brew', 'winget', 'apt-get') if shutil.which(m))
                if platform == 'linux':
                    os_release = Path('/etc/os-release').read_text() if Path('/etc/os-release').exists() else ''
                    if not any(line in ('ID=ubuntu', 'ID=debian', 'ID="ubuntu"', 'ID="debian"') for line in os_release.splitlines()):
                        managers = frozenset()
                dependencies = []
                for tool in missing:
                    action = dependency_action(tool, platform, managers, mapping)
                    if action:
                        dependencies.append(replace(action, preconditions=action.preconditions + (('manager_path', shutil.which(dict(action.preconditions)['manager'])),)))
                    else:
                        say(f'Missing {tool}: no supported existing manager mapping; install manually.')
                if dependencies:
                    plan = seal(dependencies)
                    preview(plan)
                    if ask('Approve dependency installation? [y/N/q] ').lower() == 'y':
                        outcomes = perform(plan)
                        prior.extend(outcomes)
                        if any(r.cancelled for r in outcomes):
                            raise Cancelled()
                        tools = detect_tools({c for p in specs for c in p.commands})
            invs = inventory(hosts)
            plan = make_plan(specs, invs, selected, updates, tools)
            # Sources were handled at their own checkpoint; a declined source
            # proposal must never run under final installation consent.
            plan = seal((a for a in plan.actions if a.kind in ('install', 'update')), plan.prior_results)
            say('Installation preview:')
            package_preview(plan)
            if not plan.actions:
                pending = tuple(result for result in plan.prior_results
                                if result.detail != 'Not selected.' and result.status not in ('preserved',))
                if pending:
                    say('No packages are ready to install:')
                    report(pending)
                    prior.extend(pending)
                break
            if any(p.name == 'attention-mod' and (p.host, p.name) in selected for p in specs):
                say('When used, attention-mod summaries send conversation/tool excerpts to haiku and consume model tokens.')
            decision = ask('Approve installation? [y/N/b=back/q] ').lower()
            if decision == 'b':
                continue
            if decision != 'y':
                raise Cancelled()
            outcomes = perform(plan)
            prior.extend(outcomes)
            if any(r.cancelled for r in outcomes):
                raise Cancelled()
            break

        if any(p.name == 'work-journal' and (p.host, p.name) in selected for p in specs):
            say('work-journal: optional work-record and notes locations.')
            say('  activity-logger saves your work records in the Activities directory.')
            say('  work-log-analyzer searches those records and your chosen Notes directories.')
            say('  report-generator uses those skills to prepare reports from the same records.')
            say('  This setup does not read or move your records or notes.')
            current = None
            invalid = False
            try:
                current = existing_journal(dict(os.environ), Path.home())
            except (OSError, ValueError, RuntimeError):
                invalid = True
                configuration_failed = True
                say('Existing journal settings cannot be read or contain invalid paths. They were kept unchanged.')
                say('Correct work-journal.json before configuring these locations again.')
            if current:
                say('Using existing journal settings; no settings or directories changed:')
                say('  Activities: ' + current['activities'])
                for path in current['notes']:
                    say('  Notes: ' + path)
                say('')
            elif not invalid and not journal_runtime_ready(specs, selected):
                say('work-journal is not reported as one enabled installation, so no new settings were created.')
                say('Existing settings and data were kept unchanged.')
            elif not invalid and ask('Set up work journal now? [Y/n/q] ').lower() in ('', 'y'):
                say('Add your notes folder to search your own notes alongside your work records.')
                say('Notes are optional; add a folder later in work-journal.json and restart the query server.')
                notes = ask('Notes directory (optional; Enter to skip): ')
                activities = os.environ.get('CLAUDE_ACTIVITIES_DIR') or '~/.agent-skills/activities'
                proposal = journal_preview(dict(os.environ), Path.home(), activities, (notes,) if notes else ())
                if proposal['status'] == 'preserved':
                    say('Journal settings were created by another process. Existing settings will be kept.')
                else:
                    say('Create settings: ' + proposal['settings'])
                    say('  Activities: ' + proposal['proposed']['sources']['activities'])
                    for path in proposal['proposed']['sources']['notes']['paths']:
                        say('  Notes: ' + path)
                    for directory in proposal['directories']:
                        say('  Create directory: ' + directory)
                if ask('Approve these settings/directory writes? [y/N/q] ').lower() == 'y':
                    if not journal_runtime_ready(specs, selected):
                        say('Work-journal changed before setup; no new settings or directories were created.')
                        configuration_failed = True
                    else:
                        result = apply_journal(proposal, proposal['fingerprint'])
                        say('Journal configuration: ' + result['status'] + ': ' + result['detail'])
                        configuration_failed = result['status'] not in ('created', 'preserved')
                else:
                    say('Journal: pending configuration; no settings write approved.')
            elif not invalid:
                say('Journal: pending configuration; existing settings/data retained.')
        return 1 if configuration_failed or any(r.status in ('failed', 'unverified') or (r.status == 'skipped' and r.detail != 'Not selected.') for r in prior) else 0
    except (Cancelled, SelectionCancelled, KeyboardInterrupt):
        say('Cancelled. No further operations will run; earlier confirmed writes are retained.')
        if prior:
            say('Earlier confirmed operations:')
            report(prior)
        return 130
    except (OSError, ValueError, KeyError, TypeError, subprocess.SubprocessError) as error:
        say(f'Unable to verify installer state: {type(error).__name__}: {error}')
        if prior:
            report(prior)
        say('Earlier writes may remain. No automatic retry or rollback.')
        return 1
