"""Codex receipts must corroborate real package bytes and effective inventory."""
import io
import json
import os
import shutil
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / 'runtime'))
from agent_skills_installer.catalog import build_catalog
from agent_skills_installer.ui import run


class Terminal(io.StringIO):
    def isatty(self):
        return True


class CodexCLI:
    """Only the external process is replaced; real files and installer run remain."""
    def __init__(self, root, spec, change=None, version='codex-cli 0.167.0'):
        self.root, self.spec, self.change, self.version = root, spec, change, version
        self.market, self.home = root / 'market', root / 'codex home'
        self.cache_version = spec.version
        self.installed, self.calls, self.code = [], [], 0
        self.target = self.home / 'plugins/cache/tomwangowa/quality-gates' / self.cache_version
        shutil.copytree(ROOT / 'plugins/codex/quality-gates', self.market / 'plugins/codex/quality-gates')

    @property
    def mutations(self):
        return [a for a in self.calls if a[1:3] == ('plugin', 'add')]

    def row(self):
        data = json.loads((ROOT / 'tests/fixtures/installer/observed-codex.json').read_text())['output']['installed'][0]
        data['version'] = self.cache_version
        data['source']['path'] = str(self.market / 'plugins/codex/quality-gates')
        return data

    def __call__(self, argv):
        self.calls.append(argv)
        if argv[0] == 'claude':
            return subprocess.CompletedProcess(argv, 1, '', '')
        if argv[1:] == ('--version',):
            return subprocess.CompletedProcess(argv, 0, self.version, '')
        if argv[1:] == ('plugin', 'marketplace', 'list', '--json'):
            data = {'marketplaces': [{'name': 'tomwangowa', 'root': str(self.market),
                    'marketplaceSource': {'sourceType': 'git', 'source': self.spec.source}}]}
        elif argv[1:] == ('plugin', 'list', '--marketplace', 'tomwangowa', '--json'):
            data = {'installed': self.installed, 'available': []}
        elif argv[1:] == ('plugin', 'add', 'quality-gates@tomwangowa', '--json'):
            shutil.copytree(self.market / 'plugins/codex/quality-gates', self.target)
            self.installed = [self.row()]
            data = json.loads((ROOT / 'tests/fixtures/installer/observed-codex-add.json').read_text())['output']
            data.update(version=self.cache_version, installedPath=str(self.target))
            if self.change:
                data = self.change(self, data)
            return subprocess.CompletedProcess(argv, self.code,
                None if data is None else data if isinstance(data, str) else json.dumps(data), '')
        else:
            raise AssertionError(f'Unexpected native command: {argv}')
        return subprocess.CompletedProcess(argv, 0, json.dumps(data), '')


class CodexReceiptTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory(prefix='codex receipt 中文 ')
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name).resolve()
        specs = build_catalog(ROOT, json.loads((ROOT / 'installer/providers.json').read_text()),
                              json.loads((ROOT / 'installer/dependencies.json').read_text()))
        self.spec = next(p for p in specs if (p.host, p.name) == ('codex', 'quality-gates'))

    def transcript(self, native, updates=''):
        answers = iter(['1', '', updates, 'y'])
        output = Terminal()
        with patch.dict(os.environ, {'CODEX_HOME': str(native.home)}), patch(
                'agent_skills_installer.ui.detect_tools', side_effect=lambda cs: {c: True for c in cs}):
            code = run((self.spec,), lambda _: next(answers), output, native)
        return code, output.getvalue()

    def test_new_install_uses_receipt_with_unknown_inventory_scope_and_root(self):
        native = CodexCLI(self.root, self.spec)
        code, output = self.transcript(native)
        self.assertEqual(code, 0, output)
        self.assertIn('installed:', output)
        self.assertEqual(len(native.mutations), 1)
        self.assertTrue((native.target / '.codex-plugin/plugin.json').is_file())
        self.assertIn('Installed root: ' + str(native.target), output)

    def test_cache_version_is_checked_separately_from_manifest_version(self):
        native = CodexCLI(self.root, self.spec)
        native.cache_version = 'local'
        native.target = native.target.parent / 'local'
        code, output = self.transcript(native)
        self.assertEqual(code, 0, output)

    def test_invalid_receipts_never_verify_or_retry(self):
        def modified_manifest(n, d):
            (n.target / '.codex-plugin/plugin.json').write_text('{"name":"quality-gates","version":"9.0.0"}')
            return d
        def modified_payload(n, d):
            (n.target / 'extra.txt').write_text('changed payload')
            return d
        def disabled(n, d):
            n.installed[0]['enabled'] = False
            return d
        def conflicting_inventory(n, d):
            n.installed[0]['version'] = 'other'
            return d
        def source_conflict(n, d):
            n.installed[0]['marketplaceSource']['source'] = 'https://other.invalid/repo'
            return d
        def missing_root(n, d):
            shutil.rmtree(n.target)
            return d
        def symlink_root(n, d):
            alternate = n.root / 'other'
            n.target.rename(alternate)
            n.target.symlink_to(alternate, target_is_directory=True)
            return d
        def nonzero(n, d):
            n.code = 1
            return d
        cases = {
            'missing-json': lambda n, d: None,
            'malformed-json': lambda n, d: 'not JSON',
            'array': lambda n, d: [],
            'missing-path': lambda n, d: {k: v for k, v in d.items() if k != 'installedPath'},
            'wrong-id': lambda n, d: dict(d, pluginId='other@tomwangowa'),
            'wrong-name': lambda n, d: dict(d, name='other'),
            'wrong-market': lambda n, d: dict(d, marketplaceName='other'),
            'wrong-version': lambda n, d: dict(d, version='other'),
            'wrong-type': lambda n, d: dict(d, installedPath=5),
            'relative-path': lambda n, d: dict(d, installedPath='plugins/cache/quality-gates'),
            'marketplace-path': lambda n, d: dict(d, installedPath=str(n.market / 'plugins/codex/quality-gates')),
            'unknown-auth': lambda n, d: dict(d, authPolicy='unknown'),
            'manifest': modified_manifest, 'payload': modified_payload,
            'disabled': disabled, 'inventory-version': conflicting_inventory,
            'source-conflict': source_conflict, 'missing-root': missing_root,
            'symlink-root': symlink_root, 'native-nonzero': nonzero,
        }
        for name, change in cases.items():
            with self.subTest(case=name):
                native = CodexCLI(self.root / name, self.spec, change)
                code, output = self.transcript(native)
                self.assertEqual(code, 1, output)
                self.assertIn('failed:' if name == 'native-nonzero' else 'unverified:', output)
                self.assertEqual(len(native.mutations), 1)
                self.assertFalse(any('remove' in a or 'uninstall' in a for a in native.calls))

    def test_unsupported_cli_is_blocked_before_installation(self):
        native = CodexCLI(self.root, self.spec, version='codex-cli 9.0.0')
        code, output = self.transcript(native)
        self.assertEqual(code, 1, output)
        self.assertEqual(native.mutations, [])

    def test_config_target_change_after_approval_blocks_installation(self):
        native = CodexCLI(self.root, self.spec)
        answers = iter(['1', '', '', 'y'])
        def answer(prompt):
            if 'Approve installation' in prompt:
                os.environ['CODEX_HOME'] = str(self.root / 'another home')
            return next(answers)
        with patch.dict(os.environ, {'CODEX_HOME': str(native.home)}), patch(
                'agent_skills_installer.ui.detect_tools', side_effect=lambda cs: {c: True for c in cs}):
            code = run((self.spec,), answer, Terminal(), native)
        self.assertEqual(code, 1)
        self.assertEqual(native.mutations, [])

    def test_existing_install_is_preserved_when_unavailable_update_is_requested(self):
        native = CodexCLI(self.root, self.spec)
        native.installed = [native.row()]
        # No Codex update can be offered without verified update ownership.
        # Reject the unavailable number, then let Enter preserve the package.
        answers = iter(['1', '', '1', '', 'y'])
        output = Terminal()
        with patch.dict(os.environ, {'CODEX_HOME': str(native.home)}), patch(
                'agent_skills_installer.ui.detect_tools', side_effect=lambda cs: {c: True for c in cs}):
            code = run((self.spec,), lambda _: next(answers), output, native)
        self.assertEqual(code, 1, output.getvalue())
        self.assertIn('Choose valid comma-separated numbers', output.getvalue())
        self.assertIn('unverified:', output.getvalue())
        self.assertEqual(native.mutations, [])

    def test_unregistered_cache_is_preserved_before_native_install(self):
        native = CodexCLI(self.root, self.spec)
        native.target.mkdir(parents=True)
        personal = native.target / 'retained.txt'
        personal.write_text('existing unregistered cache')
        code, output = self.transcript(native)
        self.assertEqual(code, 1, output)
        self.assertEqual(native.mutations, [])
        self.assertEqual(personal.read_text(), 'existing unregistered cache')

    def test_ambiguous_config_home_blocks_writes(self):
        for value in ('', 'relative', ' /ambiguous '):
            with self.subTest(value=value):
                native = CodexCLI(self.root / str(len(value)), self.spec)
                answers = iter(['1', '', '', 'y'])
                with patch.dict(os.environ, {'CODEX_HOME': value}), patch(
                        'agent_skills_installer.ui.detect_tools', side_effect=lambda cs: {c: True for c in cs}):
                    code = run((self.spec,), lambda _: next(answers), Terminal(), native)
                self.assertEqual(code, 1)
                self.assertEqual(native.mutations, [])

    def test_cache_parent_symlink_blocks_writes_outside_previewed_target(self):
        native = CodexCLI(self.root, self.spec)
        outside = self.root / 'outside'
        outside.mkdir()
        (native.home / 'plugins').mkdir(parents=True)
        (native.home / 'plugins/cache').symlink_to(outside, target_is_directory=True)
        code, output = self.transcript(native)
        self.assertEqual(code, 1, output)
        self.assertEqual(native.mutations, [])
        self.assertEqual(list(outside.iterdir()), [])

    @unittest.skipIf(os.name == 'nt', 'Executable fixture uses a POSIX shebang')
    def test_native_runner_captures_receipt_and_leaves_stderr_visible(self):
        tools = self.root / 'bin'
        tools.mkdir()
        fake = tools / 'codex'
        fake.write_text('#!' + sys.executable + '\nimport sys\nprint(\'{"installedPath":"/fixture"}\')\nprint("native diagnostic",file=sys.stderr)\n')
        fake.chmod(0o755)
        program = "from agent_skills_installer.ui import native_runner; r=native_runner(('codex','plugin','add','quality-gates@tomwangowa','--json')); assert r.stdout is not None; print('CAPTURED='+r.stdout.strip())"
        result = subprocess.run([sys.executable, '-c', program], cwd=self.root,
            env=dict(os.environ, PATH=str(tools), PYTHONPATH=str(ROOT / 'runtime')),
            capture_output=True, text=True)
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertEqual(result.stdout.strip(), 'CAPTURED={"installedPath":"/fixture"}')
        self.assertEqual(result.stderr.strip(), 'native diagnostic')


if __name__ == '__main__':
    unittest.main()
