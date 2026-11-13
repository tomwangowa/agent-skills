"""Real UI transcripts with synthetic process boundaries and temporary files."""
import json
import os
import shutil
import subprocess
import tempfile
import unittest
from dataclasses import replace
from pathlib import Path
from unittest.mock import patch
from installer_ui_fixtures import run_with_fixture_hosts as run
from agent_skills_installer.providers import provider_targets, parse_native_acceptance
from installer_provider_fixtures import prepared_codex, provider_data, acceptance_data, COMMIT
from test_installer_codex_receipts import CodexCLI, Terminal, ROOT
from agent_skills_installer.catalog import build_catalog


class OfficialCLI:
    def __init__(self, home, root, payload, version='codex-cli 0.167.0', marketplace='openai-curated'):
        self.home, self.root, self.payload, self.version = home, root, payload, version
        self.marketplace = marketplace
        self.calls, self.installed = [], []
        self.target = home / f'plugins/cache/{marketplace}/superpowers' / COMMIT[:8]
    @property
    def mutations(self):
        return [a for a in self.calls if a[1:3] == ('plugin', 'add') or ('marketplace' in a and 'add' in a)]
    def __call__(self, argv):
        self.calls.append(argv)
        if argv[0] != 'codex': return subprocess.CompletedProcess(argv, 1, '', '')
        if argv[1:] == ('--version',): return subprocess.CompletedProcess(argv, 0, self.version, '')
        if argv[1:4] == ('plugin', 'marketplace', 'list'):
            data = {'marketplaces': [dict(name=self.marketplace, root=str(self.root))] if self.root else []}
        elif argv[1:3] == ('plugin', 'list'):
            data = {'installed': self.installed, 'available': []}
        elif argv[1:3] == ('plugin', 'add'):
            shutil.copytree(self.payload, self.target)
            self.installed = [dict(pluginId=f'superpowers@{self.marketplace}', name='superpowers', marketplaceName=self.marketplace, installed=True, enabled=True, version=COMMIT[:8])]
            data = dict(pluginId=f'superpowers@{self.marketplace}', name='superpowers', marketplaceName=self.marketplace, version=COMMIT[:8], installedPath=str(self.target), authPolicy='ON_INSTALL')
        else: raise AssertionError(argv)
        return subprocess.CompletedProcess(argv, 0, json.dumps(data), '')


class SuperpowersCLITests(unittest.TestCase):
    def transcript(self, specs, native, records=(), on_approve=None, tools=True):
        answers = iter(['1', ','.join(str(i+1) for i in range(len(specs))), '', 'y'])
        output = Terminal()
        def answer(prompt):
            if on_approve and 'Approve installation' in prompt: on_approve()
            return next(answers)
        with patch.dict(os.environ, CODEX_HOME=str(native.home)), patch('agent_skills_installer.ui.detect_tools', side_effect=lambda cs: {c: tools for c in cs}):
            code = run(specs, answer, output, native, acceptance=records, platform_name='macos', architecture='arm64')
        return code, output.getvalue()

    def test_codex_missing_official_catalog_guides_without_writing(self):
        with tempfile.TemporaryDirectory() as tmp:
            spec = provider_targets(provider_data())[1]
            native = OfficialCLI(Path(tmp), None, None)
            code, output = self.transcript((spec,), native)
            self.assertEqual(code, 1, output)
            self.assertIn('/plugins', output)
            self.assertEqual(native.mutations, [])
            self.assertFalse((native.home / '.tmp').exists())

    def test_unknown_superpowers_allows_selected_own_package(self):
        with tempfile.TemporaryDirectory() as tmp:
            own = next(p for p in build_catalog(ROOT, json.loads((ROOT/'installer/providers.json').read_text()), json.loads((ROOT/'installer/dependencies.json').read_text())) if (p.host,p.name)==('codex','quality-gates'))
            native = CodexCLI(Path(tmp).resolve(), own)
            external = provider_targets(provider_data())[1]
            code, output = self.transcript((own, external), native)
            self.assertEqual(code, 1, output)
            self.assertTrue((native.target / '.codex-plugin/plugin.json').is_file())
            self.assertFalse((native.home / 'plugins/cache/openai-curated/superpowers').exists())
            self.assertEqual(len(native.mutations), 1)

    def test_unavailable_superpowers_does_not_install_dependencies(self):
        with tempfile.TemporaryDirectory() as tmp:
            native = OfficialCLI(Path(tmp), None, None)
            code, output = self.transcript((provider_targets(provider_data())[1],), native, tools=False)
            self.assertEqual(code, 1, output)
            self.assertNotIn('dependency:', output)
            self.assertNotIn('Missing git:', output)
            self.assertEqual(native.mutations, [])

    def test_changed_config_or_existing_cache_stops_native_add(self):
        for change in ('home', 'orphan', 'parent-link'):
            with self.subTest(change=change), tempfile.TemporaryDirectory() as tmp:
                spec, home, root, payload = prepared_codex(Path(tmp).resolve())
                native = OfficialCLI(home, root, payload)
                def mutate():
                    if change == 'commit': (home / '.tmp/plugins.sha').write_text('b'*40)
                    elif change == 'payload': (payload / 'extra').write_text('changed')
                    elif change == 'home': os.environ['CODEX_HOME'] = str(home.parent / 'elsewhere')
                    elif change == 'orphan': native.target.mkdir(parents=True)
                    else:
                        outside = home.parent / 'outside'; outside.mkdir()
                        (home / 'plugins').mkdir(); (home / 'plugins/cache').symlink_to(outside, target_is_directory=True)
                code, output = self.transcript((spec,), native, parse_native_acceptance(acceptance_data(spec)), mutate)
                self.assertEqual(code, 1, output)
                self.assertEqual(native.mutations, [])
                self.assertFalse((native.target / '.codex-plugin/plugin.json').exists())

    def test_native_install_reports_success_without_final_warnings(self):
        with tempfile.TemporaryDirectory() as tmp:
            spec, home, root, payload = prepared_codex(Path(tmp).resolve())
            native = OfficialCLI(home, root, payload)
            code, output = self.transcript((spec,), native, parse_native_acceptance(acceptance_data(spec)))
            self.assertEqual(code, 0, output)
            self.assertEqual(len(native.mutations), 1)
            self.assertTrue((native.target / '.codex-plugin/plugin.json').is_file())
            self.assertIn('[############] success', output)
            self.assertNotIn('NOT VERIFIED', output)


class OfficialClaudeCLI:
    def __init__(self, root, market, payload, spec):
        self.root, self.market, self.payload, self.spec = root, market, payload, spec
        self.present, self.installed, self.calls = False, [], []
    @property
    def mutations(self):
        return [a for a in self.calls if 'add' in a or 'install' in a]
    def __call__(self, argv):
        self.calls.append(argv)
        if argv[0] != 'claude': return subprocess.CompletedProcess(argv, 1, '', '')
        if argv[1:] == ('--version',): return subprocess.CompletedProcess(argv, 0, '2.1.319', '')
        if argv[1:4] == ('plugin', 'marketplace', 'list'):
            data = [dict(name=self.spec.marketplace, source='git', url=self.spec.source, installLocation=str(self.market))] if self.present else []
        elif argv[1:4] == ('plugin', 'marketplace', 'add'):
            self.present = True; data = {}
        elif argv[1:3] == ('plugin', 'list'): data = self.installed
        elif argv[1:3] == ('plugin', 'install'):
            target = self.root / 'installed'
            shutil.copytree(self.payload, target)
            self.installed = [dict(id='superpowers@claude-plugins-official', version=self.spec.version, enabled=True, scope='user', installPath=str(target))]
            data = {}
        else: raise AssertionError(argv)
        return subprocess.CompletedProcess(argv, 0, json.dumps(data), '')


class OfficialClaudeCLITests(unittest.TestCase):
    def case(self, root):
        from installer_provider_fixtures import entry, UPSTREAM, SKILLS
        from agent_skills_installer.catalog import tree_hash
        spec = provider_targets(provider_data())[0]
        payload = root / 'payload'
        (payload / '.claude-plugin').mkdir(parents=True)
        (payload / '.claude-plugin/plugin.json').write_text(json.dumps(dict(name='superpowers', version='7.0.0', repository=UPSTREAM)))
        for name in SKILLS:
            path = payload / 'skills' / name / 'SKILL.md'; path.parent.mkdir(parents=True); path.write_text('Synthetic fixture')
        spec = replace(spec, content_hash=tree_hash(payload))
        market = root / 'catalog'
        (market / '.claude-plugin').mkdir(parents=True)
        (market / '.claude-plugin/marketplace.json').write_text(json.dumps(dict(name=spec.marketplace, plugins=[entry('claude')])))
        for args in [('init',), ('config', 'user.email', 'fixture@example.invalid'), ('config', 'user.name', 'Fixture'), ('remote', 'add', 'origin', spec.source), ('add', '.'), ('commit', '-m', 'fixture')]:
            subprocess.run(('git', '-C', str(market), *args), capture_output=True, check=True)
        return spec, OfficialClaudeCLI(root, market, payload, spec)

    def test_no_native_install_before_source_and_install_consent(self):
        for final in ('q', 'y'):
            with self.subTest(final=final), tempfile.TemporaryDirectory() as tmp:
                spec, native = self.case(Path(tmp).resolve())
                answers = iter(['1', '1', '', 'y', final])
                def answer(prompt):
                    if 'Approve source' in prompt: self.assertEqual(native.mutations, [])
                    if 'Approve installation' in prompt:
                        self.assertEqual(len(native.mutations), 1)
                        self.assertEqual(native.mutations[0][3:5], ('add', spec.source))
                    return next(answers)
                with patch('agent_skills_installer.ui.detect_tools', side_effect=lambda cs: {c: True for c in cs}):
                    output = Terminal()
                    code = run((spec,), answer, output, native, acceptance=parse_native_acceptance(acceptance_data(spec, cli='2.1.319')), platform_name='macos', architecture='arm64')
                self.assertEqual(code, 130 if final == 'q' else 0, output.getvalue())
                self.assertEqual(len(native.mutations), 1 if final == 'q' else 2)
                self.assertEqual((native.root / 'installed').exists(), final == 'y')


class SourceConsentRaceTests(unittest.TestCase):
    case = OfficialClaudeCLITests.case
    def test_provider_appearing_after_source_consent_blocks_source_add(self):
        with tempfile.TemporaryDirectory() as tmp:
            spec, native = self.case(Path(tmp).resolve())
            answers = iter(['1', '1', '', 'y', 'y'])
            def answer(prompt):
                if 'Approve source' in prompt:
                    native.installed = [dict(id='superpowers@maintainer', version='7.0.2', enabled=False, scope='user', installPath='/synthetic/existing')]
                return next(answers)
            with patch('agent_skills_installer.ui.detect_tools', side_effect=lambda cs: {c: True for c in cs}):
                code = run((spec,), answer, Terminal(), native, acceptance=parse_native_acceptance(acceptance_data(spec, cli='2.1.319')), platform_name='macos', architecture='arm64')
            self.assertEqual(len(native.mutations), 1)
            self.assertEqual(code, 0)  # Source consent remains valid; existing plugin is retained.

    def test_malformed_historical_acceptance_does_not_block_menu(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            (root / 'provider-acceptance.json').write_text('{"schema_version":1,"records":[{}]}')
            native = OfficialCLI(root / 'home', None, None)
            output = Terminal()
            with patch('agent_skills_installer.ui.__file__', str(root / 'runtime/agent_skills_installer/ui.py')):
                code = run((), lambda _: self.fail('No prompt expected'), output, native)
            self.assertEqual(code, 1)
            self.assertEqual(native.calls, [])
            self.assertNotIn('Invalid native acceptance', output.getvalue())


class ClaudePartialResultTests(unittest.TestCase):
    case = OfficialClaudeCLITests.case

    def test_native_success_does_not_postverify_payload_origin_scope_or_state(self):
        for change in ('origin', 'payload', 'scope', 'disabled', 'relative'):
            with self.subTest(change=change), tempfile.TemporaryDirectory() as tmp:
                spec, native = self.case(Path(tmp).resolve())
                native.present = True
                def runner(argv):
                    result = native(argv)
                    if argv[1:3] == ('plugin', 'install'):
                        target = native.root / 'installed'
                        if change == 'origin':
                            (target / '.claude-plugin/plugin.json').write_text(json.dumps(dict(name='superpowers', version='7.0.0', repository='https://wrong.invalid/repo')))
                        elif change == 'payload': (target / 'extra').write_text('unexpected bookkeeping')
                        elif change == 'scope': native.installed[0]['scope'] = 'project'
                        elif change == 'disabled': native.installed[0]['enabled'] = False
                        else: native.installed[0]['installPath'] = 'relative/installed'
                    return result
                answers = iter(['1', '1', '', 'y'])
                output = Terminal()
                with patch('agent_skills_installer.ui.detect_tools', side_effect=lambda cs: {c: True for c in cs}):
                    code = run((spec,), lambda _: next(answers), output, runner, acceptance=parse_native_acceptance(acceptance_data(spec, cli='2.1.319')), platform_name='macos', architecture='arm64')
                self.assertEqual(code, 0, output.getvalue())
                self.assertIn('[############] success', output.getvalue())
                self.assertEqual(len(native.mutations), 1)
                self.assertTrue((native.root / 'installed').is_dir())
