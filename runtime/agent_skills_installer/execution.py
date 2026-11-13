"""Execute exactly the consented plan, without retries or implicit rollback."""
from __future__ import annotations

import subprocess
import json

from .models import InstallReceipt, Outcome
from .planning import fingerprint

# Keep the plan alive so an object id cannot be reused during this process.
_consumed = {}


def execute(plan, approved_fingerprint, runner, recheck, verify, *, on_event=None):
    """Consume consent once; report uncertain writes and stop dependents/cancellation."""
    if plan.fingerprint != approved_fingerprint or fingerprint(plan) != approved_fingerprint:
        raise ValueError('Approval does not match the actual plan')
    if id(plan) in _consumed:
        raise ValueError('This plan was already attempted; inspect state and approve a new plan')
    _consumed[id(plan)] = plan
    results = list(plan.prior_results)
    states = {r.action_id: r.status for r in results}
    cancelled = False
    def emit(stage, action, outcome=None):
        if on_event is not None:
            on_event(stage, action, outcome)
    for action in plan.actions:
        status, detail = 'skipped', ''
        started = False
        receipt = None
        try:
            emit('preparing', action)
            if cancelled:
                detail = 'Cancelled; no further command executed.'
            elif any(states.get(key) not in ('installed', 'updated') for key in action.requires):
                detail = 'Prerequisite did not complete with verified evidence.'
            elif not recheck(action):
                detail = 'Preconditions changed or are unknown; review a new preview.'
            else:
                emit('running', action)
                started = True
                result = runner(action.argv)
                if result.returncode:
                    status, detail = 'failed', f'Native command exited {result.returncode}; no automatic retry or rollback.'
                    try:
                        message = json.loads(result.stdout).get('message')
                        if isinstance(message, str):
                            detail += ' ' + ''.join(c for c in ' '.join(message.split()) if c.isprintable())[:400]
                    except (ValueError, TypeError, AttributeError):
                        pass
                elif action.kind in ('install', 'update'):
                    status = 'updated' if action.kind == 'update' else 'installed'
                    detail = 'Update succeeded.' if action.kind == 'update' else 'Installation succeeded.'
                    if action.kind == 'update':
                        try:
                            if json.loads(result.stdout).get('updateOutcome') == 'up_to_date':
                                detail = 'Already up to date.'
                        except (ValueError, TypeError, AttributeError):
                            pass
                else:
                    emit('verifying', action)
                    verified = verify(action, result)
                    if verified is not True and not isinstance(verified, InstallReceipt):
                        status = 'unverified'
                        detail = ('The command finished, but removal or preservation of other installations could not be confirmed. Keep this result before another attempt.'
                                  if action.kind == 'remove' else
                                  'The command finished, but the installed files, version or enabled state could not be confirmed. Keep this result for troubleshooting before another attempt.')
                    else:
                        receipt = verified if isinstance(verified, InstallReceipt) else None
                        status = 'removed' if action.kind == 'remove' else 'updated' if action.kind == 'update' else 'installed'
                        detail = 'Command completed successfully.'
                        if action.kind == 'remove':
                            detail = ('Codex shared cache and user entry removed; other plugins checked, project configs unchanged and plugin data kept.'
                                      if action.host == 'codex' else
                                      'Personal installation removed; other registered installations checked and plugin data kept.')
        except KeyboardInterrupt:
            cancelled = True
            if started and action.kind in ('install', 'update'):
                status, detail = 'failed', 'Interrupted before the native command reported success; check the host before retrying.'
            else:
                status = 'unverified' if started else 'skipped'
                detail = 'Cancelled; current command may have written data.' if started else 'Cancelled before execution.'
        except (OSError, subprocess.SubprocessError, ValueError) as error:
            if started and action.kind in ('install', 'update'):
                status = 'failed'
                detail = f'{type(error).__name__}; the native command did not report success.'
            else:
                status = 'unverified' if started else 'skipped'
                detail = f'{type(error).__name__}; inspect actual state before a new attempt.'
        outcome = Outcome(action.id, status, detail, cancelled=cancelled, receipt=receipt)
        results.append(outcome)
        states[action.id] = status
        emit('finished', action, outcome)
    return tuple(results)
