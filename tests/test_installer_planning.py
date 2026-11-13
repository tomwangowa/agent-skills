"""Decisions are immutable and cover commands as well as non-command outcomes."""
import sys
import unittest
from dataclasses import replace
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'runtime'))
from agent_skills_installer.models import InstalledPlugin, Inventory, Marketplace, PluginSpec
from agent_skills_installer.planning import make_plan, fingerprint

SOURCE = 'https://github.com/tomwangowa/agent-skills.git'


def inventory(host, plugins=(), source=SOURCE):
    return Inventory(host, 'codex-cli 0.167.0' if host == 'codex' else 'fixture', plugins, (Marketplace('tomwangowa', source, '/fixture'),),
                     ('catalog-verified:tomwangowa',), config_root='/fixture-codex' if host == 'codex' else None)


class PlanningTests(unittest.TestCase):
    def setUp(self):
        self.claude = PluginSpec('claude', 'quality-gates', 'tomwangowa', SOURCE, '0.2.0')
        self.codex = replace(self.claude, host='codex')
        self.installed = InstalledPlugin('claude', 'quality-gates', 'tomwangowa', SOURCE, '0.1.0', '/installed', True, 'user')

    def test_dual_host_preserve_and_install(self):
        plan = make_plan((self.claude, self.codex), (inventory('claude', (self.installed,)), inventory('codex')),
                         frozenset({('claude', 'quality-gates'), ('codex', 'quality-gates')}), frozenset(), {})
        self.assertEqual([(a.host, a.kind) for a in plan.actions], [('codex', 'install')])
        self.assertEqual([r.status for r in plan.prior_results], ['preserved'])
        self.assertEqual(plan.fingerprint, fingerprint(plan))

    def test_selection_and_dependency_boundaries(self):
        work = replace(self.claude, name='work-journal', commands=('node',))
        plan = make_plan((self.claude, work), (inventory('claude'),),
                         frozenset({('claude', 'quality-gates'), ('claude', 'work-journal')}), frozenset(), {'node': False})
        self.assertEqual(len(plan.actions), 1)
        self.assertEqual(plan.prior_results[0].status, 'skipped')
        for item in (replace(self.installed, enabled=False), replace(self.installed, scope=None),
                     replace(self.installed, source='https://other.invalid/source')):
            plan = make_plan((self.claude,), (inventory('claude', (item,)),),
                             frozenset({('claude', 'quality-gates')}), frozenset({('claude', 'quality-gates')}), {})
            self.assertFalse(plan.actions)
            self.assertEqual(plan.prior_results[0].status, 'skipped')
        plan = make_plan((self.claude,), (inventory('claude', source='conflicting-source'),),
                         frozenset({('claude', 'quality-gates')}), frozenset(), {})
        self.assertFalse(plan.actions)
        self.assertEqual(plan.prior_results[0].status, 'skipped')

    def test_missing_own_source_proposes_preparation_without_provider_state(self):
        for spec in (self.claude, self.codex):
            with self.subTest(host=spec.host):
                inv = replace(inventory(spec.host), marketplaces=(), capabilities=())
                plan = make_plan((spec,), (inv,), {(spec.host, spec.name)}, set(), {})
                self.assertEqual([(a.host, a.kind, a.target) for a in plan.actions],
                                 [(spec.host, 'add_marketplace', 'tomwangowa')])
                conditions = dict(plan.actions[0].preconditions)
                self.assertEqual(conditions['source'], SOURCE)
                self.assertEqual(set(conditions), {'source', 'effect'})
                self.assertEqual([r.status for r in plan.prior_results], ['skipped'])
                self.assertIn('separate consent', plan.prior_results[0].detail)

    def test_shared_missing_source_is_proposed_once_per_host(self):
        specs = (self.claude, replace(self.claude, name='work-journal'),
                 self.codex, replace(self.codex, name='work-journal'))
        invs = tuple(replace(inventory(host), marketplaces=(), capabilities=())
                     for host in ('claude', 'codex'))
        plan = make_plan(specs, invs, {(s.host, s.name) for s in specs}, set(), {})
        self.assertEqual([(a.host, a.kind) for a in plan.actions],
                         [('claude', 'add_marketplace'), ('codex', 'add_marketplace')])
        self.assertEqual([r.status for r in plan.prior_results], ['skipped'] * 4)
        self.assertEqual(len({r.action_id for r in plan.prior_results}), 4)

    def test_plan_fingerprint_changes_with_decision(self):
        def plan(spec=self.claude, inv=None, updates=frozenset()):
            return make_plan((spec,), (inv or inventory('claude', (self.installed,)),),
                             frozenset({('claude', 'quality-gates')}), updates, {})
        old = plan()
        changed = plan(updates=frozenset({('claude', 'quality-gates')}))
        self.assertNotEqual(fingerprint(old), fingerprint(changed))
        self.assertEqual(fingerprint(changed), fingerprint(plan(replace(self.claude, version='0.3.0'),
                             updates=frozenset({('claude', 'quality-gates')}))))
        self.assertEqual(fingerprint(old), fingerprint(plan()))
        unsafe = plan(inv=replace(inventory('claude'), errors=('native failure',)))
        self.assertFalse(unsafe.actions)
        self.assertEqual(unsafe.prior_results[0].status, 'skipped')


if __name__ == '__main__':
    unittest.main()
