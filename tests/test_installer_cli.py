"""User transcripts exercise real decisions and filesystem-backed fake native CLIs."""
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


class FixtureCLI:
    def __init__(self, root, source_present=True, fail=False):
        self.root, self.source_present, self.fail = root, source_present, fail
        self.installed = []
        self.calls = []

    @property
    def mutations(self):
        return [a for a in self.calls if 'add' in a or 'install' in a or 'update' in a]

    def __call__(self, argv):
        self.calls.append(argv)
        if argv[0] != 'claude':
            return subprocess.CompletedProcess(argv, 1, '', '')
        if argv[1:] == ('--version',):
            return subprocess.CompletedProcess(argv, 0, '2.1.319', '')
        if argv[1:4] == ('plugin', 'marketplace', 'list'):
            data = [dict(name='tomwangowa', source='github', repo='tomwangowa/agent-skills', installLocation=str(self.root))] if self.source_present else []
        elif argv[1:4] == ('plugin', 'marketplace', 'add'):
            self.source_present = True
            data = {}
        elif argv[1:3] == ('plugin', 'list'):
            data = self.installed
        elif argv[1:3] == ('plugin', 'install'):
            if self.fail:
                return subprocess.CompletedProcess(argv, 1, '', '')
            name = argv[3].split('@')[0]
            target = self.root / 'installed' / name
            shutil.copytree(self.root / 'plugins/claude' / name, target)
            manifest = json.loads((target / '.claude-plugin/plugin.json').read_text())
            self.installed.append(dict(id=argv[3], version=manifest['version'], enabled=True,
                                       scope='user', installPath=str(target)))
            data = {}
        else:
            raise AssertionError(f'Unexpected native command: {argv}')
        return subprocess.CompletedProcess(argv, 0, json.dumps(data), '')


class MissingSourceCLI:
    """No source exists; any command beyond inventory is a consent violation."""
    def __init__(self, host):
        self.host, self.calls = host, []

    def __call__(self, argv):
        self.calls.append(argv)
        if argv[0] != self.host:
            if argv[1:] != ('--version',):
                raise AssertionError(f'Unexpected host command: {argv}')
            return subprocess.CompletedProcess(argv, 1, '', '')
        if argv[1:] == ('--version',):
            version = '2.1.319' if self.host == 'claude' else 'codex-cli 0.167.0'
            return subprocess.CompletedProcess(argv, 0, version, '')
        if argv[1:] == ('plugin', 'marketplace', 'list', '--json'):
            data = [] if self.host == 'claude' else {'marketplaces': []}
        elif self.host == 'claude' and argv[1:] == ('plugin', 'list', '--json'):
            data = []
        else:
            raise AssertionError(f'Unexpected native command after source refusal: {argv}')
        return subprocess.CompletedProcess(argv, 0, json.dumps(data), '')


class CLITests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name)
        providers = json.loads((ROOT / 'installer/providers.json').read_text())
        dependencies = json.loads((ROOT / 'installer/dependencies.json').read_text())
        specs = build_catalog(ROOT, providers, dependencies)
        self.quality_specs = tuple(p for p in specs if p.name == 'quality-gates')
        self.catalog = tuple(p for p in specs if p.host == 'claude' and p.name == 'quality-gates')
        shutil.copytree(ROOT / 'plugins/claude/quality-gates', self.root / 'plugins/claude/quality-gates')
        self.output = Terminal()
        self.tools = patch('agent_skills_installer.ui.detect_tools', side_effect=lambda commands: {c: True for c in commands})
        self.tools.start()
        self.addCleanup(self.tools.stop)

    def transcript(self, answers, native=None):
        native = native or FixtureCLI(self.root)
        items = iter(answers)
        code = run(self.catalog, lambda prompt: next(items), self.output, native)
        return code, native

    def test_host_menu_omits_hosts_without_catalog_packages(self):
        codex_specs = tuple(spec for spec in self.quality_specs if spec.host == 'codex')
        with patch('agent_skills_installer.ui.shutil.which', return_value='/fake/cli'):
            code = run(codex_specs, lambda _: 'q', self.output,
                       lambda argv: self.fail(f'Unexpected native command: {argv}'))
        self.assertEqual(code, 130)
        self.assertIn('1. codex', self.output.getvalue())
        self.assertNotIn('claude', self.output.getvalue())

    def test_selection_transcript(self):
        code, native = self.transcript(['1', '', '', 'y'])
        self.assertEqual(code, 0, self.output.getvalue())
        self.assertEqual(len(native.mutations), 1)
        self.assertEqual(native.mutations[0], ('claude', 'plugin', 'install', 'quality-gates@tomwangowa', '--scope', 'user', '--json'))
        self.assertTrue((self.root / 'installed/quality-gates/.claude-plugin/plugin.json').is_file())
        self.assertIn('[############] success', self.output.getvalue())

    def test_clearing_selection_after_back_reports_prior_source_writes(self):
        code, native = self.transcript(['1', '', '', 'y', 'b', 'none'],
                                       FixtureCLI(self.root, source_present=False))
        self.assertEqual(code, 0, self.output.getvalue())
        self.assertEqual(len(native.mutations), 1)
        self.assertIn('marketplace', native.mutations[0])
        self.assertIn('Earlier confirmed operations', self.output.getvalue())
        self.assertNotIn('No changes made.', self.output.getvalue())

    def test_separate_approval_transcripts(self):
        native = FixtureCLI(self.root, source_present=False)
        answers = iter(['1', '', '', 'y', 'q'])
        def answer(prompt):
            if 'Approve source' in prompt:
                self.assertEqual(native.mutations, [])
            if 'Approve installation' in prompt:
                self.assertEqual(len(native.mutations), 1)
            return next(answers)
        code = run(self.catalog, answer, self.output, native)
        self.assertEqual(code, 130)
        self.assertEqual(len(native.mutations), 1)
        self.assertIn('marketplace', native.mutations[0])
        self.assertIn('Earlier confirmed operations', self.output.getvalue())

    def test_declined_source_remains_skipped_after_installation_approval(self):
        for host in ('claude', 'codex'):
            with self.subTest(host=host), tempfile.TemporaryDirectory() as tmp:
                root = Path(tmp)
                retained = root / 'personal.txt'
                retained.write_bytes(b'keep personal files')
                before = {p.relative_to(root): p.read_bytes() for p in root.rglob('*') if p.is_file()}
                native, output = MissingSourceCLI(host), Terminal()
                answers = iter(['1', '', '', 'n', 'y'])
                prompts = []
                def answer(prompt):
                    prompts.append(prompt)
                    if 'Approve installation' in prompt:
                        installation_preview = output.getvalue().split('Installation preview:')[-1]
                        self.assertNotIn('add_marketplace:', installation_preview)
                        self.assertNotIn('Command:', installation_preview)
                    return next(answers)
                specs = tuple(s for s in self.quality_specs if s.host == host)
                with patch.dict(os.environ, {'CODEX_HOME': str(root / 'codex home')}):
                    code = run(specs, answer, output, native, acceptance=())
                self.assertEqual(code, 1, output.getvalue())
                self.assertEqual(len(prompts), 4)
                self.assertFalse(any('Approve installation' in p for p in prompts))
                self.assertIn('skipped:', output.getvalue())
                self.assertIn('Source preparation requires separate consent', output.getvalue())
                self.assertNotIn('installed:', output.getvalue())
                self.assertFalse(any('add' in a or 'install' in a or 'update' in a for a in native.calls))
                self.assertFalse((root / 'codex home').exists())
                self.assertEqual(before, {p.relative_to(root): p.read_bytes() for p in root.rglob('*') if p.is_file()})

    def test_pending_source_does_not_block_independent_host_installation(self):
        claude, codex = FixtureCLI(self.root), MissingSourceCLI('codex')
        def native(argv):
            return (claude if argv[0] == 'claude' else codex)(argv)
        answers = iter(['1,2', '', '', 'n', 'y'])
        with patch.dict(os.environ, {'CODEX_HOME': str(self.root / 'codex home')}):
            code = run(self.quality_specs, lambda _: next(answers), self.output, native, acceptance=())
        self.assertEqual(code, 1, self.output.getvalue())
        self.assertEqual(claude.mutations,
                         [('claude', 'plugin', 'install', 'quality-gates@tomwangowa', '--scope', 'user', '--json')])
        self.assertIn('[############] success', self.output.getvalue())
        self.assertIn('skipped:', self.output.getvalue())
        self.assertTrue((self.root / 'installed/quality-gates/.claude-plugin/plugin.json').is_file())
        self.assertFalse((self.root / 'codex home').exists())
        self.assertFalse(any('add' in a or 'install' in a or 'update' in a for a in codex.calls))

    def test_invalid_and_noninteractive_input(self):
        native = FixtureCLI(self.root)
        self.assertEqual(run(self.catalog, lambda _: 'y', io.StringIO(), native), 2)
        self.assertFalse(native.calls)
        code, native = self.transcript(['', '99', 'q'])
        self.assertEqual(code, 130)
        self.assertFalse(native.mutations)
        def eof(_):
            raise EOFError()
        self.assertEqual(run(self.catalog, eof, Terminal(), FixtureCLI(self.root)), 130)

    def test_partial_summary_and_prior_side_effects(self):
        code, native = self.transcript(['1', '', '', 'y'], FixtureCLI(self.root, fail=True))
        self.assertEqual(code, 1)
        self.assertIn('failed:', self.output.getvalue())
        self.assertNotIn('ALL SUCCESS', self.output.getvalue())
        with patch.dict(os.environ, {'AGENT_SKILLS_BOOTSTRAP_RESULT': 'Python manager was attempted.'}):
            output = Terminal()
            self.assertEqual(run(self.catalog, lambda _: 'q', output, FixtureCLI(self.root)), 130)
            self.assertIn('Python manager was attempted.', output.getvalue())

    def test_marketplace_content_change_does_not_block_installation(self):
        native = FixtureCLI(self.root)
        answers = iter(['1', '', '', 'y'])
        def answer(prompt):
            if 'Approve installation' in prompt:
                file = self.root / 'plugins/claude/quality-gates/.claude-plugin/plugin.json'
                file.write_text('{"name":"quality-gates","version":"9.0.0"}')
            return next(answers)
        code = run(self.catalog, answer, self.output, native)
        self.assertEqual(code, 0)
        self.assertEqual(len(native.mutations), 1)

    def test_execution_interrupt_returns_cancelled_exit(self):
        native = FixtureCLI(self.root)
        def interrupted(argv):
            if argv[1:3] == ('plugin', 'install'):
                raise KeyboardInterrupt()
            return native(argv)
        code, _ = self.transcript(['1', '', '', 'y'], interrupted)
        self.assertEqual(code, 130, self.output.getvalue())
        self.assertIn('failed:', self.output.getvalue())

    def test_journal_conflict_reports_incomplete_operation(self):
        providers = json.loads((ROOT / 'installer/providers.json').read_text())
        dependencies = json.loads((ROOT / 'installer/dependencies.json').read_text())
        self.catalog = tuple(p for p in build_catalog(ROOT, providers, dependencies)
                             if (p.host, p.name) == ('claude', 'work-journal'))
        shutil.copytree(ROOT / 'plugins/claude/work-journal', self.root / 'plugins/claude/work-journal')
        config = self.root / 'config'
        answers = iter(['1', '', '', 'y', 'y', 'notes', 'y'])
        concurrent = b'{"sources":{"activities":"other","notes":{"paths":["other"]}}}'
        def answer(prompt):
            if 'Approve these settings' in prompt:
                config.mkdir()
                (config / 'work-journal.json').write_bytes(concurrent)
            return next(answers)
        with patch.dict(os.environ, {'AGENT_SKILLS_CONFIG_DIR': str(config),
                                    'CLAUDE_ACTIVITIES_DIR': str(self.root / 'activities')}):
            code = run(self.catalog, answer, self.output, FixtureCLI(self.root))
        self.assertEqual(code, 1, self.output.getvalue())
        self.assertEqual((config / 'work-journal.json').read_bytes(), concurrent)
        self.assertFalse((config / 'notes').exists())


if __name__ == '__main__':
    unittest.main()
