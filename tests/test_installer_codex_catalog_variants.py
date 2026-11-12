"""Synthetic official-route decisions; no company service or native CLI is called."""
import json
import os
import sys
import tempfile
import subprocess
import unittest
from dataclasses import replace
from pathlib import Path
from unittest.mock import patch

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / 'runtime'))
from agent_skills_installer.hosts import inspect_provider, read_inventory
from agent_skills_installer.models import Inventory, Marketplace
from agent_skills_installer.planning import make_plan
from agent_skills_installer.providers import parse_native_acceptance, validate_provider_spec
from installer_provider_fixtures import prepared_codex, acceptance_data, entry
import test_installer_superpowers_cli as cli_fixtures

API = 'openai-api-curated'


def prepared_api(base):
    spec, home, root, payload = prepared_codex(base.resolve())
    (root / '.agents/plugins/api_marketplace.json').write_text(json.dumps({'name': API, 'plugins': [entry('codex')]}))
    inv = Inventory('codex', 'codex-cli 0.167.0', marketplaces=(Marketplace(API, None, str(root)),), config_root=str(home))
    return spec, home, root, payload, inv


class CodexCatalogVariantTests(unittest.TestCase):
    def test_api_manifest_selected_without_reading_main_manifest(self):
        with tempfile.TemporaryDirectory() as tmp:
            spec, home, root, payload, inv = prepared_api(Path(tmp))
            (root / '.agents/plugins/marketplace.json').write_text('invalid main manifest')
            ready = inspect_provider(spec, inv)
            self.assertEqual(ready.status, 'ready', ready.reason)
            self.assertEqual(dict(ready.snapshot)['catalog_name'], API)

    def test_api_action_and_acceptance_are_bound_to_native_catalog(self):
        with tempfile.TemporaryDirectory() as tmp:
            spec, home, root, payload, inv = prepared_api(Path(tmp))
            api_spec = replace(spec, marketplace=API)
            validate_provider_spec(api_spec)
            records = parse_native_acceptance(acceptance_data(api_spec))
            inv = replace(inv, provider_readiness=(inspect_provider(spec, inv),))
            plan = make_plan((spec,), (inv,), {('codex', 'superpowers')}, set(), {'git': True}, acceptance=records, platform='macos', architecture='arm64')
            self.assertEqual(len(plan.actions), 1, plan.prior_results)
            self.assertEqual(plan.actions[0].argv, ('codex', 'plugin', 'add', 'superpowers@'+API, '--json'))
            main_records = parse_native_acceptance(acceptance_data(spec))
            rejected = make_plan((spec,), (inv,), {('codex', 'superpowers')}, set(), {'git': True}, acceptance=main_records, platform='macos', architecture='arm64')
            self.assertEqual(rejected.actions, ())

    def test_wrong_api_manifest_and_ambiguous_official_names_are_rejected(self):
        with tempfile.TemporaryDirectory() as tmp:
            spec, home, root, payload, inv = prepared_api(Path(tmp))
            path = root / '.agents/plugins/api_marketplace.json'
            original = path.read_bytes()
            for data in ({'name': 'openai-curated', 'plugins': [entry('codex')]},
                         {'name': API, 'plugins': []},
                         {'name': API, 'plugins': [entry('codex'), entry('codex')]},
                         {'name': API, 'plugins': [{**entry('codex'), 'source': {'source':'local','path':'../escape'}}]}):
                with self.subTest(data=data):
                    path.write_text(json.dumps(data))
                    self.assertNotEqual(inspect_provider(spec, inv).status, 'ready')
            path.write_bytes(original)
            ambiguous = replace(inv, marketplaces=inv.marketplaces+(Marketplace('openai-curated', None, str(root)),))
            self.assertEqual(inspect_provider(spec, ambiguous).status, 'unverified')
            conflict = replace(inv, marketplaces=(Marketplace(API, 'https://wrong.invalid/catalog.git', str(root)),))
            self.assertEqual(inspect_provider(spec, conflict).status, 'unverified')

    def test_company_endpoint_config_survives_api_install_transcript(self):
        with tempfile.TemporaryDirectory() as tmp:
            spec, home, root, payload, inv = prepared_api(Path(tmp))
            config = home / 'config.toml'
            original = b'model_provider = "company"\n[model_providers.company]\nbase_url = "https://company.invalid/v1"\nenv_key = "COMPANY_AI_TEST_TOKEN"\nrequires_openai_auth = false\nwire_api = "responses"\n'
            config.write_bytes(original)
            native = cli_fixtures.OfficialCLI(home, root, payload, marketplace=API)
            records = parse_native_acceptance(acceptance_data(replace(spec, marketplace=API)))
            with patch.dict(os.environ, COMPANY_AI_TEST_TOKEN='dummy-secret-not-a-real-key'):
                code, output = cli_fixtures.SuperpowersCLITests().transcript((spec,), native, records)
                self.assertEqual(os.environ['COMPANY_AI_TEST_TOKEN'], 'dummy-secret-not-a-real-key')
            self.assertEqual(code, 0, output)
            self.assertIn('installed:', output)
            self.assertIn('superpowers@'+API, output)
            self.assertNotIn('dummy-secret-not-a-real-key', output)
            self.assertNotIn('company.invalid', output)
            self.assertEqual(config.read_bytes(), original)
            self.assertEqual(len(native.mutations), 1)
            self.assertTrue(all(c[1:] == ('--version',) or c[1:2] == ('plugin',) for c in native.calls))
            self.assertTrue(all('--marketplace' in c for c in native.calls if c[1:3] == ('plugin','list')))
            self.assertFalse((home / 'auth.json').exists())

    def test_catalog_switch_after_consent_prevents_install(self):
        with tempfile.TemporaryDirectory() as tmp:
            spec, home, root, payload, inv = prepared_api(Path(tmp))
            native = cli_fixtures.OfficialCLI(home, root, payload, marketplace=API)
            records = parse_native_acceptance(acceptance_data(replace(spec, marketplace=API)))
            code, output = cli_fixtures.SuperpowersCLITests().transcript((spec,), native, records, on_approve=lambda: setattr(native, 'marketplace', 'openai-curated'))
            self.assertEqual(code, 1, output)
            self.assertEqual(native.mutations, [])
            self.assertIn('Preconditions changed', output)

    def test_api_receipt_cannot_claim_main_catalog_installation(self):
        class WrongReceipt(cli_fixtures.OfficialCLI):
            def __call__(self, argv):
                result = super().__call__(argv)
                if argv[1:3] == ('plugin', 'add'):
                    data = json.loads(result.stdout)
                    data.update(pluginId='superpowers@openai-curated', marketplaceName='openai-curated')
                    return subprocess.CompletedProcess(argv, 0, json.dumps(data), '')
                return result
        with tempfile.TemporaryDirectory() as tmp:
            spec, home, root, payload, inv = prepared_api(Path(tmp))
            native = WrongReceipt(home, root, payload, marketplace=API)
            records = parse_native_acceptance(acceptance_data(replace(spec, marketplace=API)))
            code, output = cli_fixtures.SuperpowersCLITests().transcript((spec,), native, records)
            self.assertEqual(code, 1, output)
            self.assertIn('unverified:', output)
            self.assertTrue(native.target.exists())
            self.assertEqual(len(native.mutations), 1)

    def test_api_manifest_absence_never_falls_back_to_main(self):
        with tempfile.TemporaryDirectory() as tmp:
            spec, home, root, payload, inv = prepared_api(Path(tmp))
            (root / '.agents/plugins/api_marketplace.json').unlink()
            self.assertEqual(inspect_provider(spec, inv).status, 'unverified')
            self.assertFalse((root / '.agents/plugins/api_marketplace.json').exists())

    def test_existing_disabled_api_superpowers_is_preserved(self):
        with tempfile.TemporaryDirectory() as tmp:
            spec, home, root, payload, inv = prepared_api(Path(tmp))
            native = cli_fixtures.OfficialCLI(home, root, payload, marketplace=API)
            native.installed = [dict(pluginId='superpowers@'+API, name='superpowers', marketplaceName=API,
                                     installed=True, enabled=False, version='newer-existing')]
            code, output = cli_fixtures.SuperpowersCLITests().transcript((spec,), native)
            self.assertEqual(code, 0, output)
            self.assertIn('preserved:', output)
            self.assertEqual(native.mutations, [])

    def test_missing_catalog_for_company_user_does_not_attempt_login_or_startup(self):
        with tempfile.TemporaryDirectory() as tmp:
            spec, home, root, payload, inv = prepared_api(Path(tmp))
            native = cli_fixtures.OfficialCLI(home, None, None)
            code, output = cli_fixtures.SuperpowersCLITests().transcript((spec,), native)
            self.assertEqual(code, 1, output)
            self.assertIn('ChatGPT login is not required', output)
            self.assertIn('/plugins', output)
            self.assertEqual(native.mutations, [])
            self.assertTrue(all(c[1:] == ('--version',) or c[1:4] == ('plugin','marketplace','list') for c in native.calls))
