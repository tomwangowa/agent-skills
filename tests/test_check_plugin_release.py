"""Reject stale and unsafe generated packages rather than trusting inventory labels."""
import hashlib
import json
import tempfile
import unittest
from pathlib import Path

from scripts.plugin_packaging.render import render_package, render_marketplaces
from scripts.plugin_packaging.verify import verify_release, verify_acceptance
from test_build_plugins import fixture, CONTRACTS


class ReleaseTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory(); self.addCleanup(self.tmp.cleanup)
        self.root = Path(self.tmp.name).resolve()
        self.packages, server = fixture(self.root)
        for surface in ['claude', 'codex']:
            for p in self.packages:
                render_package(self.root, p, surface, self.root / 'plugins' / surface / p['name'],
                               CONTRACTS, server_bundle=server)
        claude, codex = render_marketplaces(self.root, self.packages)
        (self.root / '.claude-plugin/marketplace.json').write_text(json.dumps(claude))
        path = self.root / '.agents/plugins/marketplace.json'; path.parent.mkdir(parents=True)
        path.write_text(json.dumps(codex))
        self.assertEqual(verify_release(self.root, CONTRACTS), [])

    def test_missing_skill_and_stale_source_fail(self):
        (self.root / 'plugins/codex/quality-gates/skills/completion-gate/SKILL.md').unlink()
        self.assertTrue(any('completion-gate' in e for e in verify_release(self.root, CONTRACTS)))
        (self.root / 'completion-gate/SKILL.md').write_text('New source')
        self.assertTrue(any('source' in e.lower() for e in verify_release(self.root, CONTRACTS)))

    def test_private_config_symlink_and_personal_paths_fail(self):
        package = self.root / 'plugins/codex/quality-gates'
        inventory_path = package / '.generated-files.json'

        def record_generated_file(path):
            inventory = json.loads(inventory_path.read_text())
            inventory['files'][path.relative_to(package).as_posix()] = {
                'sha256': hashlib.sha256(path.read_bytes()).hexdigest(),
                'mode': path.stat().st_mode & 0o777,
            }
            inventory_path.write_text(json.dumps(inventory))

        def forget_generated_file(path):
            inventory = json.loads(inventory_path.read_text())
            del inventory['files'][path.relative_to(package).as_posix()]
            inventory_path.write_text(json.dumps(inventory))

        config = package / 'config.json'; config.write_text('{}')
        record_generated_file(config)
        self.assertTrue(any('private config' in error for error in verify_release(self.root, CONTRACTS)))
        config.unlink()
        forget_generated_file(config)
        self.assertEqual(verify_release(self.root, CONTRACTS), [])
        for personal_path in ['/Users/example-user/private/data', '/home/example-user/private/data']:
            p = package / 'personal.md'; p.write_text(personal_path)
            record_generated_file(p)
            self.assertTrue(any('personal absolute path' in error for error in verify_release(self.root, CONTRACTS)))
            p.unlink()
            forget_generated_file(p)
            self.assertEqual(verify_release(self.root, CONTRACTS), [])
        (package / 'outside').symlink_to(self.root / 'completion-gate/SKILL.md')
        self.assertTrue(any('symlink' in e.lower() for e in verify_release(self.root, CONTRACTS)))

    def test_vendor_documentation_home_paths_do_not_fail_release_validation(self):
        package = self.root / 'plugins/codex/quality-gates'
        path = package / 'server/node_modules/vendor/Readme.md'
        path.parent.mkdir(parents=True)
        path.write_text('/home/example-vendor/repo/example.js')
        inventory_path = package / '.generated-files.json'
        inventory = json.loads(inventory_path.read_text())
        inventory['files']['server/node_modules/vendor/Readme.md'] = {
            'sha256': hashlib.sha256(path.read_bytes()).hexdigest(),
            'mode': path.stat().st_mode & 0o777,
        }
        inventory_path.write_text(json.dumps(inventory))
        self.assertEqual(verify_release(self.root, CONTRACTS), [])

    def test_wrong_version_marketplace_and_shadow_manifest_fail(self):
        manifest = self.root / 'plugins/codex/quality-gates/.codex-plugin/plugin.json'
        data = json.loads(manifest.read_text()); data['version'] = '9.0.0'; manifest.write_text(json.dumps(data))
        self.assertTrue(any('version' in e.lower() or 'changed' in e.lower() for e in verify_release(self.root, CONTRACTS)))
        (manifest.parents[1] / 'plugin.json').write_text('{}')
        self.assertTrue(any('shadow' in e.lower() for e in verify_release(self.root, CONTRACTS)))

    def test_parent_symlink_and_missing_local_reference_are_rejected(self):
        codex = self.root / 'plugins/codex'
        relocated = self.root / 'relocated'; codex.rename(relocated)
        codex.symlink_to(relocated, target_is_directory=True)
        self.assertTrue(any('symlink' in e.lower() for e in verify_release(self.root, CONTRACTS)))
        codex.unlink(); relocated.rename(codex)
        skill = codex / 'quality-gates/skills/completion-gate/SKILL.md'
        skill.write_text(skill.read_text() + '\n[Required reference](missing.md)\n')
        self.assertTrue(any('reference' in e.lower() for e in verify_release(self.root, CONTRACTS)))

    def test_native_verified_labels_need_current_bindings_and_recorded_evidence(self):
        payload={'schema_version':1,'production_security':{'status':'verified'},'surfaces':{
            surface:{'status':'verified','checks':{},'evidence':[]} for surface in ['claude-cli','codex-cli']}}
        errors=verify_acceptance(self.root,payload)
        self.assertTrue(any('evidence' in e.lower() for e in errors))
        self.assertTrue(any('binding' in e.lower() for e in errors))

    def test_current_pending_native_gate_cannot_be_called_release_complete(self):
        payload={'schema_version':1,'production_security':{'status':'failed'},'surfaces':{
            surface:{'status':'not_verified','checks':{},'evidence':[]} for surface in ['claude-cli','codex-cli']}}
        self.assertTrue(verify_acceptance(self.root,payload))


if __name__ == '__main__':
    unittest.main()
