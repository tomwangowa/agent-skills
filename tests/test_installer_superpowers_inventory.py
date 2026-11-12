"""Synthetic local observations must not invent official origin or absence."""
import json
import os
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch
from dataclasses import replace
from agent_skills_installer.hosts import read_inventory, inspect_provider
from agent_skills_installer.models import Inventory, Marketplace
from agent_skills_installer.providers import provider_targets
from installer_provider_fixtures import prepared_codex, provider_data, COMMIT, CODEX_CATALOG, entry
from test_installer_hosts import NativeRunner, SOURCE


class SuperpowersInventoryTests(unittest.TestCase):
    def test_managed_missing_source_field_is_not_invented(self):
        spec = provider_targets(provider_data())[1]
        native = NativeRunner({'installed': [], 'available': []}, {'marketplaces': [dict(name='openai-curated', root='/missing')]})
        inv = read_inventory('codex', native, provider_specs=(spec,))
        self.assertIsNone(inv.marketplaces[0].source)
        self.assertEqual(inv.provider_readiness[0].status, 'unverified')
        self.assertEqual(inv.errors, ())

    def test_verified_managed_origin_keeps_raw_source_absent(self):
        with tempfile.TemporaryDirectory() as tmp:
            spec, home, root, payload = prepared_codex(Path(tmp))
            native = NativeRunner({'installed': [], 'available': []}, {'marketplaces': [dict(name='openai-curated', root=str(root))]})
            with patch.dict(os.environ, CODEX_HOME=str(home)):
                inv = read_inventory('codex', native, provider_specs=(spec,))
            self.assertIsNone(inv.marketplaces[0].source)
            self.assertEqual(inv.provider_readiness[0].status, 'ready')
            self.assertEqual(inv.marketplaces[0].commit, COMMIT)
            self.assertEqual(inv.marketplaces[0].provenance_kind, 'native-managed')
            self.assertTrue(all('--marketplace' in c for c in native.calls if c[1:3] == ('plugin', 'list')))
            original = (home / '.tmp/plugins.sha').read_bytes()
            (home / '.tmp/plugins.sha').unlink()
            bad = inspect_provider(spec, inv)
            self.assertNotEqual(bad.status, 'ready')
            self.assertFalse((home / '.tmp/plugins.sha').exists())
            self.assertEqual(original, (COMMIT + '\n').encode())

    def test_missing_native_catalog_does_not_poison_own_package_inventory(self):
        spec = provider_targets(provider_data())[1]
        native = NativeRunner({'installed': [], 'available': []}, {'marketplaces': [dict(name='tomwangowa', root='/fixture', marketplaceSource=dict(source=SOURCE))]})
        inv = read_inventory('codex', native, provider_specs=(spec,))
        self.assertFalse(inv.errors)
        self.assertEqual(inv.provider_readiness[0].status, 'needs-native-setup')

    def test_maintainer_provider_is_not_absent(self):
        spec = provider_targets(provider_data())[1]
        row = dict(pluginId='superpowers@superpowers-marketplace', name='superpowers', marketplaceName='superpowers-marketplace', installed=True, enabled=False, version='7.0.2', marketplaceSource=dict(source='https://github.com/obra/superpowers-marketplace.git'))
        native = NativeRunner({'installed': [row], 'available': []}, {'marketplaces': [dict(name='superpowers-marketplace', root='/fixture', marketplaceSource=row['marketplaceSource'])]})
        inv = read_inventory('codex', native, provider_specs=(spec,))
        self.assertFalse(inv.errors)
        self.assertEqual(inv.plugins[0].version, '7.0.2')
        self.assertEqual(inv.provider_readiness[0].status, 'preserved')

    def test_unknown_provider_is_not_treated_as_empty(self):
        spec = provider_targets(provider_data())[1]
        native = NativeRunner({'broken': []}, {'marketplaces': [dict(name='unknown-provider', root='/fixture')]})
        inv = read_inventory('codex', native, provider_specs=(spec,))
        self.assertFalse(inv.errors)
        self.assertEqual(inv.provider_readiness[0].status, 'unverified')
        self.assertTrue(any('unknown-provider' in c for c in native.calls))

    def test_claude_pinned_payload_is_not_relative_to_catalog(self):
        spec = provider_targets(provider_data())[0]
        with tempfile.TemporaryDirectory() as tmp:
            import subprocess
            root = Path(tmp)
            (root / '.claude-plugin').mkdir()
            (root / '.claude-plugin/marketplace.json').write_text(json.dumps({'name': spec.marketplace, 'plugins': [entry('claude')]}))
            for args in [('init',), ('config', 'user.email', 'fixture@example.invalid'), ('config', 'user.name', 'Fixture'), ('remote', 'add', 'origin', spec.source), ('add', '.'), ('commit', '-m', 'fixture')]:
                subprocess.run(('git', '-C', str(root), *args), check=True, capture_output=True)
            inv = Inventory('claude', '2.1.319', marketplaces=(Marketplace(spec.marketplace, spec.source, str(root), 'user', 'configured-git'),))
            ready = inspect_provider(spec, inv)
            self.assertEqual(ready.status, 'ready')
            state = dict(ready.snapshot)
            self.assertEqual(state['payload_repository'], spec.provider.payload_repository)
            self.assertEqual(state['payload_commit'], spec.provider.payload_commit)
            self.assertEqual(state['payload_hash'], '')
            self.assertFalse((root / 'plugins/superpowers').exists())


class ProviderLocalFailureTests(unittest.TestCase):
    def test_malformed_unknown_installed_row_does_not_poison_own_inventory(self):
        spec = provider_targets(provider_data())[1]
        class Native(NativeRunner):
            def __call__(self, argv):
                if argv[1:3] == ('plugin', 'list') and 'unknown-provider' in argv:
                    import subprocess
                    self.calls.append(argv)
                    return subprocess.CompletedProcess(argv, 0, json.dumps({'installed': [{'broken': True}], 'available': []}), '')
                return super().__call__(argv)
        native = Native({'installed': [], 'available': []}, {'marketplaces': [dict(name='unknown-provider', root='/fixture'), dict(name='tomwangowa', root='/own', marketplaceSource=dict(source=SOURCE))]})
        inv = read_inventory('codex', native, provider_specs=(spec,))
        self.assertEqual(inv.errors, ())
        self.assertEqual(inv.provider_readiness[0].status, 'unverified')
        self.assertTrue(any('tomwangowa' in c for c in native.calls))
