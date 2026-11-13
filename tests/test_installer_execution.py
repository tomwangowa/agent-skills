"""Consent, once-only execution, partial failure and uncertain side effects."""
import subprocess
import sys
import unittest
from dataclasses import replace
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'runtime'))
from agent_skills_installer.execution import execute
from agent_skills_installer.models import Action, Outcome
from agent_skills_installer.planning import seal


class ExecutionTests(unittest.TestCase):
    def plan(self):
        return seal((Action('a', 'install', 'claude', 'first', ('fake', 'first')),
                     Action('b', 'install', 'codex', 'independent', ('fake', 'independent')),
                     Action('c', 'install', 'claude', 'dependent', ('fake', 'dependent'), ('a',))),
                    (Outcome('old', 'preserved', 'Kept original.'),))

    def test_reject_stale_approval(self):
        calls = []
        plan = self.plan()
        with self.assertRaises(ValueError):
            execute(plan, 'wrong', calls.append, lambda a: True, lambda a, result: True)
        self.assertEqual(calls, [])
        forged = replace(plan, actions=plan.actions[:1])
        with self.assertRaises(ValueError):
            execute(forged, plan.fingerprint, calls.append, lambda a: True, lambda a, result: True)

    def test_recheck_and_native_success(self):
        calls = []
        def runner(argv):
            calls.append(argv)
            return subprocess.CompletedProcess(argv, 0)
        plan = self.plan()
        results = execute(plan, plan.fingerprint, runner, lambda a: a.id != 'a', lambda a, result: False)
        self.assertEqual(calls, [('fake', 'independent')])
        self.assertEqual([r.status for r in results], ['preserved', 'skipped', 'installed', 'skipped'])
        with self.assertRaises(ValueError):
            execute(plan, plan.fingerprint, runner, lambda a: True, lambda a, result: True)

    def test_partial_failure_and_cancellation(self):
        for exception in (None, subprocess.TimeoutExpired(('fake',), 1), KeyboardInterrupt()):
            calls = []
            def runner(argv):
                calls.append(argv)
                if argv == ('fake', 'first'):
                    if exception is not None:
                        raise exception
                    return subprocess.CompletedProcess(argv, 1)
                return subprocess.CompletedProcess(argv, 0)
            plan = self.plan()
            results = execute(plan, plan.fingerprint, runner, lambda a: True, lambda a, result: True)
            self.assertEqual(calls.count(('fake', 'first')), 1)
            self.assertEqual(results[0].status, 'preserved')
            self.assertEqual(results[1].status, 'failed')
            self.assertEqual(results[2].status, 'skipped' if isinstance(exception, KeyboardInterrupt) else 'installed')
            self.assertEqual(results[3].status, 'skipped')
            self.assertFalse(any('remove' in arg or 'rollback' in arg for argv in calls for arg in argv))


if __name__ == '__main__':
    unittest.main()
