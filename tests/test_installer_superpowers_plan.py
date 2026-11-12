"""External targets need exact evidence; any existing provider is preserved."""
import tempfile
import unittest
from dataclasses import replace
from pathlib import Path
from unittest.mock import patch
from agent_skills_installer.hosts import inspect_provider, source_action
from agent_skills_installer.models import Inventory, Marketplace, InstalledPlugin, PluginSpec
from agent_skills_installer.providers import provider_targets, parse_native_acceptance
from agent_skills_installer.planning import make_plan
from agent_skills_installer.execution import execute
from installer_provider_fixtures import provider_data, prepared_codex, acceptance_data, CODEX_CATALOG
from test_installer_planning import inventory, SOURCE


class SuperpowersPlanTests(unittest.TestCase):
    def plan(self, spec, inv, records=()):
        return make_plan((spec,), (inv,), {(spec.host, spec.name)}, {(spec.host, spec.name)}, {'git': True}, acceptance=records, platform='macos', architecture='arm64')

    def test_no_codex_official_marketplace_add_is_planned(self):
        spec = provider_targets(provider_data())[1]
        plan = self.plan(spec, Inventory('codex', 'codex-cli 0.167.0', config_root='/home'), parse_native_acceptance(acceptance_data(spec)))
        self.assertFalse(plan.actions)
        self.assertEqual(plan.prior_results[0].status, 'unverified')
        for source in (CODEX_CATALOG, 'https://github.com/obra/superpowers.git', 'https://github.com/obra/superpowers-marketplace.git'):
            with self.assertRaises(ValueError):
                source_action('codex', source, 'add_marketplace')

    def test_claude_source_add_requires_target_acceptance(self):
        spec = provider_targets(provider_data())[0]
        inv = Inventory('claude', '2.1.319')
        self.assertFalse(self.plan(spec, inv).actions)
        accepted = parse_native_acceptance(acceptance_data(spec, cli=inv.cli_version))
        actions = self.plan(spec, inv, accepted).actions
        self.assertEqual(len(actions), 1)
        self.assertEqual(actions[0].target, 'claude-plugins-official')
        self.assertEqual(actions[0].argv[4], spec.source)

    def test_existing_newer_provider_never_downgrades(self):
        for host in ('claude', 'codex'):
            spec = next(p for p in provider_targets(provider_data()) if p.host == host)
            with tempfile.TemporaryDirectory() as tmp:
                retained = Path(tmp) / 'keep'
                retained.write_bytes(b'keep')
                installed = InstalledPlugin(host, 'superpowers', 'superpowers-marketplace', 'https://github.com/obra/superpowers.git', '7.0.2', str(retained.parent), False, None)
                plan = self.plan(spec, Inventory(host, 'native', plugins=(installed,)))
                calls = []
                execute(plan, plan.fingerprint, lambda argv: calls.append(argv), lambda _: True, lambda *_: True)
                self.assertEqual(retained.read_bytes(), b'keep')
                self.assertEqual(calls, [])
                self.assertEqual(plan.prior_results[0].status, 'preserved')

    def test_empty_acceptance_blocks_only_superpowers(self):
        external = provider_targets(provider_data())[1]
        own = PluginSpec('codex', 'quality-gates', 'tomwangowa', SOURCE, '0.2.0')
        plan = make_plan((external, own), (inventory('codex'),), {('codex', p.name) for p in (own, external)}, set(), {})
        self.assertEqual([a.target for a in plan.actions], ['quality-gates@tomwangowa'])
        self.assertEqual(plan.prior_results[0].status, 'unverified')

    def test_planning_never_reads_provider_files(self):
        spec = provider_targets(provider_data())[1]
        with patch('pathlib.Path.is_absolute', side_effect=AssertionError('Unexpected filesystem inspection')):
            plan = self.plan(spec, Inventory('codex', 'codex-cli 0.167.0', marketplaces=(Marketplace(spec.marketplace, None, '/home/.tmp/plugins'),), config_root='/home'))
        self.assertFalse(plan.actions)

    def test_commit_change_invalidates_approval(self):
        with tempfile.TemporaryDirectory() as tmp:
            spec, home, root, payload = prepared_codex(Path(tmp).resolve())
            inv = Inventory('codex', 'codex-cli 0.167.0', marketplaces=(Marketplace('openai-curated', None, str(root)),), config_root=str(home))
            ready = inspect_provider(spec, inv)
            inv = replace(inv, provider_readiness=(ready,))
            records = parse_native_acceptance(acceptance_data(spec))
            old = self.plan(spec, inv, records)
            self.assertEqual(len(old.actions), 1)
            (home / '.tmp/plugins.sha').write_text('b' * 40)
            new = self.plan(spec, replace(inv, provider_readiness=(inspect_provider(spec, inv),)), records)
            self.assertNotEqual(old.fingerprint, new.fingerprint)
            self.assertIn('provider_state', dict(old.actions[0].preconditions))
