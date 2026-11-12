"""Synthetic official Codex receipts separate cache revision from manifest version."""
import json
import shutil
import subprocess
import tempfile
import unittest
from dataclasses import replace
from pathlib import Path
from agent_skills_installer.hosts import inspect_provider
from agent_skills_installer.models import Inventory, Marketplace, InstalledPlugin
from agent_skills_installer.providers import parse_native_acceptance
from agent_skills_installer.planning import make_plan
from agent_skills_installer.receipts import verify_codex_install, verify_claude_install
from installer_provider_fixtures import prepared_codex, acceptance_data, COMMIT


class SuperpowersVerifyTests(unittest.TestCase):
    def setup_case(self, base):
        spec, home, root, payload = prepared_codex(base)
        inv = Inventory('codex', 'codex-cli 0.167.0', marketplaces=(Marketplace('openai-curated', None, str(root)),), config_root=str(home))
        ready = inspect_provider(spec, inv)
        inv = replace(inv, provider_readiness=(ready,))
        plan = make_plan((spec,), (inv,), {('codex', 'superpowers')}, set(), {'git': True}, acceptance=parse_native_acceptance(acceptance_data(spec)), platform='macos', architecture='arm64')
        target = home / 'plugins/cache/openai-curated/superpowers' / COMMIT[:8]
        shutil.copytree(payload, target)
        plugin = InstalledPlugin('codex', 'superpowers', 'openai-curated', None, COMMIT[:8], None, True, None)
        inv = replace(inv, plugins=(plugin,))
        data = dict(pluginId='superpowers@openai-curated', name='superpowers', marketplaceName='openai-curated', version=COMMIT[:8], installedPath=str(target), authPolicy='ON_INSTALL')
        return spec, plan.actions[0], inv, ready, target, data

    def test_codex_catalog_sha_version_is_not_manifest_version(self):
        with tempfile.TemporaryDirectory() as tmp:
            spec, action, inv, ready, target, data = self.setup_case(Path(tmp).resolve())
            receipt = verify_codex_install(action, spec, subprocess.CompletedProcess([], 0, json.dumps(data)), inv, readiness=ready)
            self.assertTrue(receipt)
            self.assertEqual(receipt.cache_version, COMMIT[:8])
            self.assertNotEqual(receipt.cache_version, spec.version)
            for value in (spec.version, 'wrongsha'):
                bad = subprocess.CompletedProcess([], 0, json.dumps(dict(data, version=value)))
                self.assertFalse(verify_codex_install(action, spec, bad, inv, readiness=ready))

    def test_partial_and_mismatched_results_remain_unverified(self):
        changes = ('manifest', 'payload', 'symlink', 'relative', 'foreign', 'config', 'commit', 'empty', 'disabled')
        for change in changes:
            with self.subTest(change=change), tempfile.TemporaryDirectory() as tmp:
                spec, action, inv, ready, target, data = self.setup_case(Path(tmp).resolve())
                if change == 'manifest':
                    (target / '.codex-plugin/plugin.json').write_text('{"name":"superpowers","version":"9.0.0"}')
                elif change == 'payload': (target / 'extra').write_text('partial')
                elif change == 'symlink':
                    outside = target.parent / 'elsewhere'
                    target.rename(outside); target.symlink_to(outside, target_is_directory=True)
                elif change == 'relative': data['installedPath'] = 'relative'
                elif change == 'foreign': data['installedPath'] = str(target.parent)
                elif change == 'config': inv = replace(inv, config_root=str(target.parent))
                elif change == 'commit': ready = replace(ready, snapshot=tuple((k, 'b'*40 if k == 'catalog_commit' else v) for k, v in ready.snapshot))
                elif change == 'empty': data = {}
                elif change == 'disabled': inv = replace(inv, plugins=(replace(inv.plugins[0], enabled=False),))
                self.assertFalse(verify_codex_install(action, spec, subprocess.CompletedProcess([], 0, json.dumps(data)), inv, readiness=ready))
