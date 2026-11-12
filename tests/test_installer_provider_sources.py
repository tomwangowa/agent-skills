"""Wrong source pairings or incomplete acceptance must never authorize writes."""
import copy
import json
import sys
import tempfile
import unittest
from dataclasses import replace
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / 'runtime'))
from agent_skills_installer.catalog import load_catalog, validate_catalog
from agent_skills_installer.providers import provider_targets, parse_native_acceptance, target_accepted, installation_accepted
from agent_skills_installer.models import ProviderReadiness
from installer_provider_fixtures import provider_data, acceptance_data, COMMIT


class ProviderSourceTests(unittest.TestCase):
    def snapshot(self, spec):
        return tuple(sorted(dict(catalog_name=spec.marketplace, catalog_kind='native-managed',
            catalog_repository=spec.source, catalog_root='/home/.tmp/plugins', catalog_commit=COMMIT,
            entry_hash=spec.provider.entry_hash, payload_kind='catalog-relative', payload_repository='',
            payload_commit='', payload_path='./plugins/superpowers', payload_hash=spec.content_hash).items()))

    def test_ready_label_without_full_observations_cannot_authorize_installation(self):
        spec = provider_targets(provider_data())[1]
        records = parse_native_acceptance(acceptance_data(spec))
        for key in ('catalog_repository', 'payload_kind', 'payload_path', 'payload_hash', 'catalog_root'):
            snapshot = dict(self.snapshot(spec)); snapshot[key] = ''
            ready = ProviderReadiness(spec.name, 'ready', '', tuple(sorted(snapshot.items())))
            self.assertFalse(installation_accepted(spec, ready, records, 'codex-cli 0.167.0', 'macos', 'arm64'))

    def test_wrong_catalog_payload_pair_is_rejected(self):
        changes = [dict(catalog_repository='https://evil.invalid/catalog.git'),
                   dict(payload_path='../outside'), dict(payload_repository='https://evil.invalid/payload.git'),
                   dict(payload_commit='short'), dict(catalog_kind='configured-git')]
        for fields in changes:
            data = provider_data()
            data['external'][1]['provider'].update(fields)
            with self.subTest(fields=fields), self.assertRaises(ValueError):
                provider_targets(data)
        data = provider_data()
        data['external'][0]['provider']['payload_commit'] = None
        with self.assertRaises(ValueError):
            provider_targets(data)
        data = provider_data()
        data['external'][0]['hosts'] = ['claude']
        with self.assertRaises(ValueError):
            provider_targets(data)

    def test_external_missing_provider_cannot_become_writable(self):
        spec = provider_targets(provider_data())[1]
        with self.assertRaises(ValueError):
            validate_catalog((replace(spec, provider=None),))
        with self.assertRaises(ValueError):
            validate_catalog((replace(spec, default_selected=True),))
        empty_hash = replace(spec, content_hash='')
        records = parse_native_acceptance(acceptance_data(spec))
        self.assertFalse(target_accepted(empty_hash, records, 'codex-cli 0.167.0', 'macos', 'arm64'))

    def test_acceptance_requires_exact_tuple(self):
        spec = provider_targets(provider_data())[1]
        records = parse_native_acceptance(acceptance_data(spec))
        ready = ProviderReadiness('superpowers', 'ready', '', self.snapshot(spec))
        self.assertTrue(installation_accepted(spec, ready, records, 'codex-cli 0.167.0', 'macos', 'arm64'))
        for cli, os_name, arch in [('codex-cli 0.167.1', 'macos', 'arm64'), ('codex-cli 0.167.0', 'linux', 'arm64'),
                                   ('codex-cli 0.167.0', 'macos', 'amd64')]:
            self.assertFalse(target_accepted(spec, records, cli, os_name, arch))
        self.assertFalse(target_accepted(replace(spec, version='6.3.1'), records, 'codex-cli 0.167.0', 'macos', 'arm64'))
        self.assertFalse(installation_accepted(spec, replace(ready, status='unverified'), records,
                                              'codex-cli 0.167.0', 'macos', 'arm64'))
        self.assertFalse(target_accepted(spec, (), 'codex-cli 0.167.0', 'macos', 'arm64'))
        with self.assertRaises(ValueError):
            parse_native_acceptance({'schema_version': 1, 'records': [{'host': 'codex'}]})
        for name, value in [('catalog_commit', ''), ('evidence_ref', ''), ('entry_hash', 'bad'), ('platform', 'other')]:
            data = acceptance_data(spec)
            data['records'][0][name] = value
            with self.subTest(name=name), self.assertRaises(ValueError):
                parse_native_acceptance(data)

    def test_unrelated_catalog_revision_keeps_same_payload_acceptance(self):
        spec = provider_targets(provider_data())[1]
        records = parse_native_acceptance(acceptance_data(spec, commit='b' * 40))
        ready = ProviderReadiness('superpowers', 'ready', '', self.snapshot(spec))
        self.assertTrue(installation_accepted(spec, ready, records, 'codex-cli 0.167.0', 'macos', 'arm64'))

    def test_schema_one_catalog_is_rejected(self):
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / 'catalog.json'
            path.write_text(json.dumps({'schema_version': 1, 'plugins': []}))
            with self.assertRaises(ValueError):
                load_catalog(path)


if __name__ == '__main__':
    unittest.main()
