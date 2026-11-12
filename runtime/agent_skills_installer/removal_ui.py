"""Separate unchecked removal flow; no source, dependency or journal setup."""
from __future__ import annotations

import os
from pathlib import Path
import subprocess

from .execution import execute
from .hosts import read_inventory
from .progress import PackageProgress
from .removal import (codex_removal_supported, make_removal_plan, recheck_removal,
                      removal_config_matches, removal_options, verify_removal)
from .selection import SelectionCancelled, package_lines


class _Cancelled(Exception):
    pass


def choose_operation(input_fn, output):
    """Choose a mode before host reads; Enter preserves the installation default."""
    print('1. Install / update packages\n2. Remove packages\n', file=output)
    while True:
        try:
            answer = input_fn('Operation (Enter = 1; q = cancel): ').strip().lower()
        except (EOFError, KeyboardInterrupt):
            return None
        if answer in ('', '1'):
            return 'install'
        if answer == '2':
            return 'remove'
        if answer == 'q':
            return None
        print('Choose 1, 2, or q.', file=output)


def _claude_root():
    raw = os.environ.get('CLAUDE_CONFIG_DIR')
    if raw is not None and (not raw or raw != raw.strip() or not Path(raw).is_absolute()):
        raise ValueError('CLAUDE_CONFIG_DIR must be a clear absolute path for personal removal')
    return Path(raw) if raw is not None else Path.home() / '.claude'


def run_removal(catalog, input_fn, output, runner, *, package_selector=None, progress=None):
    """Preview and execute one confirmed host-specific removal plan with no retries."""
    def say(text):
        print(text, file=output)

    def ask(prompt):
        try:
            answer = input_fn(prompt).strip()
        except (EOFError, KeyboardInterrupt):
            raise _Cancelled() from None
        if answer.lower() == 'q':
            raise _Cancelled()
        return answer

    def numbers(prompt, size, default):
        while True:
            answer = ask(prompt)
            if not answer:
                return default
            if answer.lower() == 'none':
                return frozenset()
            try:
                indices = frozenset(int(p.strip()) - 1 for p in answer.split(','))
                if not indices or not indices <= frozenset(range(size)):
                    raise ValueError()
                return indices
            except ValueError:
                say('Choose valid comma-separated numbers, none, or q.')

    if not output.isatty():
        say('Interactive terminal required. Nothing removed.')
        return 2
    progress = progress or PackageProgress(output)
    outcomes = ()
    try:
        say('Remove packages: Claude personal installs and Codex shared-cache entries. Every package starts unchecked.')
        hosts = []
        for host in ('claude', 'codex'):
            try:
                result = runner((host, '--version'))
                if result.returncode == 0:
                    hosts.append(host)
                    say(f'{len(hosts)}. {host}: {result.stdout.strip()}')
            except (OSError, subprocess.SubprocessError):
                continue
        if not hosts:
            say('No supported CLI was found. Nothing removed.')
            return 1
        chosen = numbers('Hosts (numbers; q to cancel): ', len(hosts), frozenset())
        if not chosen:
            say('No hosts selected. Nothing removed.')
            return 0
        selected_hosts = tuple(hosts[i] for i in sorted(chosen))
        claude_root = _claude_root() if 'claude' in selected_hosts else None
        inventories = tuple(read_inventory(host, runner) for host in selected_hosts)
        for inv in inventories:
            if inv.errors:
                say(f'{inv.host}: cannot read the installed-plugin list. Its packages will be kept.\n')
        codex_supported = any(inv.host == 'codex' and not inv.errors for inv in inventories)
        if codex_supported:
            codex_supported = codex_removal_supported(runner)
        options = removal_options(catalog, inventories, claude_root,
                                  codex_remove_supported=codex_supported)
        blocked = {}
        for option in options:
            if option.reason:
                blocked.setdefault((option.host, option.reason), []).append(option.name)
        for (host, reason), names in blocked.items():
            say(f'{host}: {reason}')
            say('  Kept: ' + ', '.join(names) + '\n')
        eligible = tuple(o for o in options if not o.reason)
        if not eligible:
            say('No eligible packages to remove. Nothing changed.')
            return 1 if blocked or any(inv.errors for inv in inventories) else 0
        if package_selector is None:
            lines, spans = package_lines(eligible, frozenset())
            starts = {start: i for i, (start, _) in enumerate(spans)}
            for i, line in enumerate(lines):
                say(f'{starts[i] + 1}. {line.strip()}' if i in starts else line)
            selected = numbers('Packages to remove (Enter = none; q = cancel): ', len(eligible), frozenset())
        else:
            selected = package_selector(eligible, frozenset(), output)
            if not isinstance(selected, frozenset) or not selected <= frozenset(range(len(eligible))):
                raise ValueError('Unknown removal selection')
        if not selected:
            say('No packages selected. Nothing removed.')
            return 0
        plan = make_removal_plan(eligible, frozenset(eligible[i].key for i in selected))
        say('\nRemoval preview:')
        for action in plan.actions:
            scope = 'Claude personal installation' if action.host == 'claude' else 'Codex shared cache'
            say(f'  {action.target} / installed version {dict(action.preconditions)["version"]} / {scope}')
        if any(action.host == 'claude' for action in plan.actions):
            say('Claude project/local/managed installations, work-journal settings, work records, notes and shared tools are kept.')
        if any(action.host == 'codex' for action in plan.actions):
            say('Codex shared cache and its user plugin entry will be removed. Project configs remain and may no longer load this plugin until it is installed again.')
        say('Plugin data directories are kept. Claude Code may clear the removed plugin\'s saved options/secrets.')
        say('No marketplace or dependency cleanup will run.\n')
        if ask('Approve removal of these packages? [y/N/q] ').lower() != 'y':
            raise _Cancelled()
        before = {}

        def recheck(action):
            inv = read_inventory(action.host, runner)
            if action.host == 'claude':
                if _claude_root() != claude_root:
                    return False
                config_root = str(claude_root)
            else:
                config_root = inv.config_root or ''
            codex_supported = action.host != 'codex' or codex_removal_supported(runner)
            if (not removal_config_matches(action, config_root)
                    or not recheck_removal(action, inv, config_root,
                                           codex_remove_supported=codex_supported)):
                return False
            before[action.id] = inv
            return True

        def verify(action, result):
            inv = read_inventory(action.host, runner)
            if action.host == 'claude':
                if _claude_root() != claude_root:
                    return False
                config_root = str(claude_root)
            else:
                config_root = inv.config_root or ''
            if not removal_config_matches(action, config_root):
                return False
            return verify_removal(action, result, before[action.id], inv)

        outcomes = execute(plan, plan.fingerprint, runner, recheck, verify, on_event=progress.event)
        if any(result.cancelled for result in outcomes):
            raise _Cancelled()
        labels = {'claude': 'Claude Code', 'codex': 'Codex'}
        affected = ' and '.join(labels[host] for host in sorted({action.host for action in plan.actions}))
        say(f'Start a new {affected} session before checking which skills remain available.')
        return 1 if any(result.status != 'removed' for result in outcomes) else 0
    except (_Cancelled, SelectionCancelled, KeyboardInterrupt):
        say('Cancelled. No further removal will run; completed changes are retained. No automatic retry or rollback.')
        return 130
    except (OSError, ValueError, KeyError, TypeError, RuntimeError, subprocess.SubprocessError) as error:
        say(f'Cannot verify removal state: {type(error).__name__}: {error}')
        say('Earlier changes may remain. Inspect actual state before another attempt; no automatic retry or rollback.')
        return 1
