"""Real capability records enable only their exact tested installation routes."""
import json
import sys
import tempfile
import unittest
import zipfile
from dataclasses import replace
from pathlib import Path
from unittest.mock import patch

ROOT = Path(__file__).resolve().parents[1]
sys.path[:0] = [str(ROOT), str(ROOT / 'runtime')]
from agent_skills_installer.providers import provider_targets, parse_native_acceptance, target_accepted
from scripts.build_plugin_installer import build_bundle
import scripts.build_plugin_installer as builder


def load_records():
    return parse_native_acceptance(json.loads((ROOT / 'installer/provider-acceptance.json').read_text()))


class AcceptanceReleaseTests(unittest.TestCase):
    def test_only_exact_native_capabilities_are_enabled(self):
        specs = provider_targets(json.loads((ROOT / 'installer/providers.json').read_text()))
        records = load_records()
        self.assertEqual(len(records), 2)
        for spec in specs:
            self.assertFalse(spec.default_selected)
            self.assertTrue(spec.content_hash)
            if spec.host == 'codex':
                self.assertFalse(target_accepted(spec, records, 'codex-cli 0.167.0', 'macos', 'arm64'))
                spec = replace(spec, marketplace='openai-api-curated')
                cli = 'codex-cli 0.167.0'
            else:
                cli = '2.1.322 (Claude Code)'
            self.assertTrue(target_accepted(spec, records, cli, 'macos', 'arm64'))
            for platform, arch, version in [('windows','arm64',cli),('linux','arm64',cli),('macos','x86_64',cli),('macos','arm64','unverified-version')]:
                self.assertFalse(target_accepted(spec, records, version, platform, arch))

    def test_archive_includes_resolvable_actual_evidence(self):
        with tempfile.TemporaryDirectory() as tmp:
            with zipfile.ZipFile(build_bundle(ROOT, Path(tmp)/'candidate.zip')) as z:
                prefix = 'agent-skills-installer/'
                records = parse_native_acceptance(json.loads(z.read(prefix+'provider-acceptance.json')))
                self.assertEqual(len(records), 2)
                for record in records:
                    proof = json.loads(z.read(prefix+record.evidence_ref))
                    self.assertNotIn('raw_file_hashes', proof)
                    self.assertNotIn('evidence_root', proof)
                    if record.host == 'claude':
                        self.assertEqual(proof['status'], 'both-native-auth-state-installations-passed')
                        for case, expected in [('no-account',False),('signed-in-isolated',True)]:
                            row = proof['cases'][case]
                            self.assertNotIn('saved_results_hashes', row)
                            self.assertNotIn('evidence_root', row)
                            self.assertIs(row['auth_before']['loggedIn'], expected)
                            self.assertIs(row['auth_after']['loggedIn'], expected)
                            self.assertEqual(row['content_hash'], record.content_hash)
                    else:
                        self.assertTrue(proof['auth_json_absent'])
                        self.assertTrue(proof['synthetic_company_config_preserved'])
                        self.assertEqual(proof['catalog'], record.catalog_name)
                        self.assertEqual(proof['tree_hash'], record.content_hash)
                self.assertFalse(any('/.superpowers/' in name or name.endswith('.credentials.json') for name in z.namelist()))

    def record(self, **changes):
        proof = json.loads((ROOT/'docs/validation/plugin-installer/claude-login-matrix-evidence.json').read_text())['cases']['no-account']
        data = dict(host='claude',cli_version=proof['cli_version'],platform=proof['platform'],architecture=proof['architecture'],catalog_name='claude-plugins-official',catalog_commit=proof['catalog_commit'],entry_hash='d85f0111dd6cfcd54268f46dbadbd54d4df344c160cda075134e2d35aae9f888',manifest_version=proof['manifest_version'],content_hash=proof['content_hash'],evidence_ref='acceptance-evidence/claude-login-matrix-evidence.json')
        data.update(changes)
        return data

    def assert_build_rejected(self, record):
        original = builder.read_json
        def read(root, relative):
            if relative=='installer/provider-acceptance.json':return {'schema_version':1,'records':[record]}
            return original(root,relative)
        with tempfile.TemporaryDirectory() as tmp, patch.object(builder,'read_json',side_effect=read):
            with self.assertRaises(ValueError):build_bundle(ROOT,Path(tmp)/'invalid.zip')
            self.assertFalse((Path(tmp)/'invalid.zip').exists())

    def test_unknown_evidence_reference_blocks_build(self):
        self.assert_build_rejected(self.record(evidence_ref='../private-profile/credentials.json'))

    def test_native_evidence_disagreement_blocks_build(self):
        self.assert_build_rejected(self.record(catalog_commit='a'*40))
