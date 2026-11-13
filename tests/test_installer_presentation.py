"""Package progress, protocol-output capture, native cache markers and journal guidance."""
import json
import os
from pathlib import Path
import shutil
import subprocess
import sys
import tempfile
import unittest
from dataclasses import replace
from unittest.mock import patch

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / 'runtime'))
from agent_skills_installer.catalog import build_catalog, tree_hash
from agent_skills_installer.models import Action, InstalledPlugin, Inventory, PluginSpec
from agent_skills_installer.receipts import verify_claude_install
from agent_skills_installer.ui import run
from test_installer_cli import FixtureCLI, Terminal


class CacheMarkerTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name).resolve()
        (self.root / '.claude-plugin').mkdir()
        (self.root / '.claude-plugin/plugin.json').write_text(json.dumps({'name': 'quality-gates', 'version': '0.2.0'}))
        (self.root / 'payload.txt').write_text('frozen package bytes')
        source = 'https://github.com/tomwangowa/agent-skills.git'
        self.spec = PluginSpec('claude', 'quality-gates', 'tomwangowa', source, '0.2.0', content_hash=tree_hash(self.root))
        self.action = Action('quality', 'update', 'claude', 'quality-gates@tomwangowa', (),
                             preconditions=(('source', source), ('version', '0.2.0'), ('cli_version', '2.1.322 (Claude Code)')))
        self.inv = Inventory('claude', '2.1.322 (Claude Code)',
                             (InstalledPlugin('claude', 'quality-gates', 'tomwangowa', source, '0.2.0', str(self.root), True, 'user'),))

    def marker(self, name='123', value=None):
        folder = self.root / '.in_use'
        folder.mkdir(exist_ok=True)
        path = folder / name
        path.write_text(json.dumps(value if value is not None else {'pid': 123, 'procStart': 'native-start-token'}))
        return path

    def test_native_in_use_marker_does_not_invalidate_unchanged_package(self):
        self.marker()
        self.assertTrue(verify_claude_install(self.action, self.spec, self.inv))

    def test_payload_change_is_not_hidden_by_native_marker(self):
        self.marker()
        (self.root / 'payload.txt').write_text('changed')
        self.assertFalse(verify_claude_install(self.action, self.spec, self.inv))

    def test_arbitrary_extra_file_is_not_a_native_marker(self):
        self.marker('extra.py')
        self.assertFalse(verify_claude_install(self.action, self.spec, self.inv))

    def test_marker_pid_must_match_filename(self):
        self.marker(value={'pid': 999, 'procStart': 'native-start-token'})
        self.assertFalse(verify_claude_install(self.action, self.spec, self.inv))

    def test_marker_symlink_is_rejected(self):
        (self.root / '.in_use').mkdir()
        (self.root / '.in_use/123').symlink_to(self.root / 'payload.txt')
        self.assertFalse(verify_claude_install(self.action, self.spec, self.inv))

    def test_unknown_cli_does_not_get_marker_exception(self):
        self.marker()
        version = '2.1.323 (Claude Code)'
        action = replace(self.action, preconditions=tuple((k, version if k == 'cli_version' else v)
                         for k, v in self.action.preconditions))
        self.assertFalse(verify_claude_install(action, self.spec, replace(self.inv, cli_version=version)))

    def test_invalid_native_metadata_is_never_ignored(self):
        cases = [({'pid': True}, False), ({'pid': 123, 'extra': 'payload'}, False),
                 ({'pid': 123, 'procStart': []}, False), ({'pid': 123}, True)]
        for value, expected in cases:
            with self.subTest(value=value):
                self.marker(value=value)
                self.assertEqual(verify_claude_install(self.action, self.spec, self.inv), expected)
        self.marker().chmod(0o755)
        self.assertFalse(verify_claude_install(self.action, self.spec, self.inv))


class PresentationTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name).resolve()
        self.catalog = build_catalog(ROOT, json.loads((ROOT / 'installer/providers.json').read_text()),
                                     json.loads((ROOT / 'installer/dependencies.json').read_text()))

    def specs(self, *names):
        result = tuple(p for p in self.catalog if p.host == 'claude' and p.name in names)
        for spec in result:
            shutil.copytree(ROOT / 'plugins/claude' / spec.name, self.root / 'plugins/claude' / spec.name)
        return result

    def test_each_package_has_progress_and_a_separated_result_block(self):
        specs = self.specs('quality-gates', 'technical-decisions')
        answers = iter(['1', '1,2', '', 'y'])
        output = Terminal()
        code = run(specs, lambda _: next(answers), output, FixtureCLI(self.root))
        self.assertEqual(code, 0, output.getvalue())
        text = output.getvalue()
        self.assertRegex(text, r'quality-gates[^\n]*\[[#= .>\-]+\]')
        self.assertRegex(text, r'technical-decisions[^\n]*\[[#= .>\-]+\]')
        self.assertIn('\n\ntechnical-decisions', text)
        self.assertNotIn('Native result and postconditions verified.', text)

    def test_existing_journal_settings_are_reused_without_path_questions(self):
        specs = self.specs('work-journal')
        config = self.root / 'config'
        config.mkdir()
        file = config / 'work-journal.json'
        raw = json.dumps({'sources': {'activities': 'existing-work', 'notes': {'paths': ['notes-a', 'notes-b']}},
                          'private_extension': 'never-print-this'}).encode()
        file.write_bytes(raw)
        answers = iter(['1', '', '', 'y'])
        prompts = []
        def answer(prompt):
            prompts.append(prompt)
            return next(answers) if len(prompts) <= 4 else 'q'
        output = Terminal()
        with patch.dict(os.environ, {'AGENT_SKILLS_CONFIG_DIR': str(config)}):
            code = run(specs, answer, output, FixtureCLI(self.root))
        self.assertEqual(code, 0, output.getvalue())
        self.assertEqual(len(prompts), 4)
        self.assertEqual(file.read_bytes(), raw)
        self.assertIn('activity-logger', output.getvalue())
        self.assertIn('work-log-analyzer', output.getvalue())
        self.assertNotIn('never-print-this', output.getvalue())
        self.assertFalse((config / 'existing-work').exists())

    def test_missing_journal_config_explains_consumer_skills_before_asking(self):
        specs = self.specs('work-journal')
        config = self.root / 'missing-config'
        answers = iter(['1', '', '', 'y', 'n'])
        output = Terminal()
        def answer(prompt):
            if 'Configure' in prompt:
                self.assertIn('activity-logger saves your work records', output.getvalue())
                self.assertIn('work-log-analyzer searches those records', output.getvalue())
            return next(answers)
        with patch.dict(os.environ, {'AGENT_SKILLS_CONFIG_DIR': str(config)}):
            code = run(specs, answer, output, FixtureCLI(self.root))
        self.assertEqual(code, 0, output.getvalue())
        self.assertFalse(config.exists())

    def test_first_setup_uses_default_activities_and_optional_notes(self):
        specs = self.specs('work-journal')
        config = self.root / 'new-config'
        fake_home = self.root / 'user-home'
        answers = iter(['1', '', '', 'y', '', '', 'y'])
        output = Terminal()
        with patch.dict(os.environ, {'AGENT_SKILLS_CONFIG_DIR': str(config)}, clear=False), \
             patch('pathlib.Path.home', return_value=fake_home):
            code = run(specs, lambda _: next(answers), output, FixtureCLI(self.root))
        self.assertEqual(code, 0, output.getvalue())
        data = json.loads((config/'work-journal.json').read_text())
        self.assertEqual(data['sources']['activities'], str(fake_home/'.agent-skills/activities'))
        self.assertEqual(data['sources']['notes']['paths'], [])
        self.assertTrue((fake_home/'.agent-skills/activities').is_dir())
        self.assertIn('search your own notes alongside your work records', output.getvalue())

    def test_journal_settings_not_created_if_runtime_changes_during_approval(self):
        specs = self.specs('work-journal')
        config = self.root / 'config-race'
        fake_home = self.root / 'fake-home'
        native = FixtureCLI(self.root)
        answers = iter(['1', '', '', 'y', '', '', 'y'])
        def answer(prompt):
            if 'Approve these settings' in prompt:
                native.installed[0]['enabled'] = False
            return next(answers)
        output = Terminal()
        with patch.dict(os.environ, {'AGENT_SKILLS_CONFIG_DIR':str(config), 'CLAUDE_ACTIVITIES_DIR':''}), \
             patch('pathlib.Path.home', return_value=fake_home):
            code = run(specs, answer, output, native)
        self.assertEqual(code,1,output.getvalue())
        self.assertFalse(config.exists())
        self.assertFalse((fake_home/'.agent-skills/activities').exists())
        self.assertIn('work-journal changed', output.getvalue().lower())

    def test_current_existing_work_journal_can_start_setup_without_update(self):
        specs = self.specs('work-journal')
        config = self.root / 'no-journal-config'
        native = FixtureCLI(self.root)
        native.installed = [{'id':'work-journal@tomwangowa','version':specs[0].version,
                             'enabled':True,'scope':'user','installPath':str(self.root/'plugins/claude/work-journal')}]
        answers = iter(['1', '', '', 'n'])
        prompts = []
        def answer(prompt):
            prompts.append(prompt)
            return next(answers)
        output = Terminal()
        with patch.dict(os.environ, {'AGENT_SKILLS_CONFIG_DIR':str(config)}, clear=False):
            code = run(specs, answer, output, native)
        self.assertEqual(code, 0, output.getvalue())
        self.assertTrue(any('Set up work journal' in prompt for prompt in prompts))
        self.assertFalse(config.exists())
        self.assertEqual(native.mutations, [])

    def test_existing_work_journal_version_does_not_block_optional_setup(self):
        specs = self.specs('work-journal')
        config = self.root / 'no-journal-config'
        native = FixtureCLI(self.root)
        native.installed = [{'id':'work-journal@tomwangowa','version':'0.2.0',
                             'enabled':True,'scope':'user','installPath':str(self.root/'plugins/claude/work-journal')}]
        answers = iter(['1', '', '', 'n'])
        output = Terminal()
        with patch.dict(os.environ, {'AGENT_SKILLS_CONFIG_DIR':str(config)}, clear=False):
            code = run(specs, lambda _: next(answers), output, native)
        self.assertEqual(code, 0, output.getvalue())
        self.assertFalse(config.exists())
        self.assertIn('Journal: pending configuration', output.getvalue())
        self.assertEqual(native.mutations, [])

    def test_native_json_stdout_is_captured_instead_of_dumped(self):
        tools = self.root / 'bin'
        tools.mkdir()
        fake = tools / 'claude'
        fake.write_text('#!' + sys.executable + '\nprint(\'{"command":"install","outcome":"ok","message":"done"}\')\n')
        fake.chmod(0o755)
        program = "import sys,json;sys.path.insert(0,sys.argv[1]);from agent_skills_installer.ui import native_runner;r=native_runner(('claude','plugin','install','quality-gates@tomwangowa','--scope','user','--json'));assert json.loads(r.stdout)['outcome']=='ok';print('receipt captured')"
        result = subprocess.run([sys.executable, '-I', '-c', program, str(ROOT / 'runtime')],
                                env=dict(os.environ, PATH=str(tools)), capture_output=True, text=True)
        self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
        self.assertEqual(result.stdout.strip(), 'receipt captured')

    def test_invalid_existing_journal_is_preserved_without_new_path_prompts(self):
        specs = self.specs('work-journal')
        config = self.root / 'config'
        config.mkdir()
        path = config / 'work-journal.json'
        path.write_bytes(b'{invalid')
        answers = iter(['1', '', '', 'y'])
        output = Terminal()
        with patch.dict(os.environ, {'AGENT_SKILLS_CONFIG_DIR': str(config)}):
            code = run(specs, lambda _: next(answers), output, FixtureCLI(self.root))
        self.assertEqual(code, 1)
        self.assertEqual(path.read_bytes(), b'{invalid')
        self.assertIn('kept unchanged', output.getvalue())


class NativePromptTests(unittest.TestCase):
    def test_no_newline_prompt_is_forwarded_before_stdin_answer(self):
        # The worker may receive its answer only after its parent observes the
        # prompt: capturing stderr until exit would deadlock this exchange.
        child = "import sys;sys.stderr.write('Permission? ');sys.stderr.flush();answer=input();print('{\\\"outcome\\\":\\\"'+answer+'\\\"}')"
        worker = """import sys
from agent_skills_installer.process import run_json_command
r=run_json_command((sys.executable,'-c',sys.argv[1]),lambda s:(sys.stdout.write(s),sys.stdout.flush()),lambda:None,timeout=5)
assert r.returncode==0
assert 'yes' in r.stdout
print('captured without raw JSON')
"""
        process = subprocess.Popen([sys.executable, '-c', worker, child], env=dict(os.environ, PYTHONPATH=str(ROOT / 'runtime')),
                                   stdin=subprocess.PIPE, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        try:
            import select
            if os.name == 'nt':
                self.skipTest('PTY/pipe readiness is POSIX-specific')
            self.assertTrue(select.select([process.stdout], [], [], 5)[0], 'Native prompt was hidden')
            self.assertEqual(os.read(process.stdout.fileno(), 12), b'Permission? ')
            output, errors = process.communicate(b'yes\n', timeout=5)
            self.assertEqual(process.returncode, 0, errors)
            self.assertEqual(output.strip(), b'captured without raw JSON')
        finally:
            if process.poll() is None:
                process.kill()
                process.communicate()

    def test_timeout_kills_only_the_started_command_and_does_not_retry(self):
        from agent_skills_installer.process import run_json_command
        with self.assertRaises(subprocess.TimeoutExpired):
            run_json_command((sys.executable, '-c', 'import time;time.sleep(5)'), lambda _: None,
                             lambda: None, timeout=0.15)

    def test_error_json_becomes_a_message_in_its_own_package_block(self):
        from agent_skills_installer.execution import execute
        from agent_skills_installer.planning import seal
        from agent_skills_installer.progress import PackageProgress
        first = Action('one', 'install', 'claude', 'first@market', ())
        second = Action('two', 'install', 'claude', 'second@market', ())
        plan = seal((first, second))
        output = Terminal()
        progress = PackageProgress(output)
        outcomes = execute(plan, plan.fingerprint,
                           lambda argv: subprocess.CompletedProcess(argv, 1, '{"message":"Network unavailable"}', ''),
                           lambda _: True, lambda *_: True, on_event=progress.event)
        self.assertEqual([r.status for r in outcomes], ['failed', 'failed'])
        self.assertIn('Network unavailable\n\nsecond', output.getvalue())
        self.assertNotIn('{"message"', output.getvalue())
