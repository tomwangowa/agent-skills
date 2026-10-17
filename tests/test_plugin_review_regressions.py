"""Exercise reviewed failures using disposable installations and personal data."""
import contextlib
import importlib
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


class ReviewRegressions(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory(); self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name).resolve()

    def test_flat_skills_mirror_hooks_and_journal_use_own_runtime(self):
        mirror = self.root / 'codex/skills'; mirror.mkdir(parents=True)
        for name in ['runtime', 'session-preferences', 'control-return', 'activity-logger', 'work-log-analyzer']:
            shutil.copytree(ROOT / name, mirror / name, ignore=shutil.ignore_patterns('__pycache__'))
        config = self.root / 'config'; config.mkdir()
        (config / 'work-journal.json').write_text(json.dumps({'sources': {
            'activities': 'journal', 'notes': {'paths': ['notes']}}}))
        env = dict(os.environ, AGENT_SKILLS_CONFIG_DIR=str(config), AGENT_SESSION_PREFS='',
                   CLAUDE_SESSION_ID='flat-mirror-fixture')
        env.pop('CLAUDE_ACTIVITIES_DIR', None)
        for skill in ['session-preferences', 'control-return']:
            result = subprocess.run([sys.executable, str(mirror / skill / 'scripts/session_start_hook.py')],
                                    input='{}', capture_output=True, text=True, env=env)
            self.assertIn('hookSpecificOutput', json.loads(result.stdout), result.stdout)
        for skill, script, arguments in [
            ('activity-logger', 'init_activities.sh', ['init']),
            ('activity-logger', 'log_activity.sh', ['-d', 'Flat mirror record']),
            ('work-log-analyzer', 'aggregate_activities.sh', ['-m', 'json', '-r', 'all']),
        ]:
            result = subprocess.run(['bash', str(mirror / skill / 'scripts' / script), *arguments],
                                    capture_output=True, text=True, env=env, cwd=self.root)
            self.assertEqual(result.returncode, 0, result.stderr)
        records = list((config / 'journal').glob('*.json'))
        self.assertTrue(records)
        self.assertIn('Flat mirror record', records[0].read_text())

    def test_cli_relative_roots_fail_and_quoted_tilde_expands(self):
        env = dict(os.environ, PYTHONPATH=str(ROOT / 'runtime'))
        for name, args in [('setup', ['--activities', 'journal', '--notes', 'notes', '--preview']),
                           ('doctor', [])]:
            result = subprocess.run([sys.executable, '-m', 'agent_skills_runtime.' + name,
                                     '--config-root', 'relative', *args], cwd=self.root,
                                    capture_output=True, text=True, env=env)
            self.assertNotEqual(result.returncode, 0, result.stdout)
        setup = importlib.import_module('agent_skills_runtime.setup')
        output = io.StringIO()
        with patch.object(Path, 'home', return_value=self.root), contextlib.redirect_stdout(output):
            self.assertEqual(setup.main(['--config-root', '~/settings', '--activities', 'journal',
                                         '--notes', 'notes', '--preview']), 0)
        self.assertEqual(json.loads(output.getvalue())['proposed']['sources']['activities'],
                         str(self.root / 'settings/journal'))
        self.assertFalse((self.root / 'settings').exists())

    def test_cache_and_symlink_alias_reject_personal_settings_and_data(self):
        config = importlib.import_module('agent_skills_runtime.config')
        setup = importlib.import_module('agent_skills_runtime.setup')
        prefs = importlib.import_module('agent_skills_runtime.preferences')
        cache = self.root / 'cache'; (cache / '.codex-plugin').mkdir(parents=True)
        (cache / '.codex-plugin/plugin.json').write_text('{}')
        alias = self.root / 'alias'; alias.symlink_to(cache, target_is_directory=True)
        for parent in [cache, alias]:
            target = parent / 'personal'
            with self.subTest(parent=parent):
                with self.assertRaises(ValueError):
                    config.resolve_config_root({'AGENT_SKILLS_CONFIG_DIR': str(target)}, self.root)
                with self.assertRaises(ValueError):
                    setup.setup_work_journal(target, self.root / 'journal', [self.root / 'notes'])
                with self.assertRaises(ValueError):
                    prefs.save_module_override(target, 'custom.md', 'Personal rule', None, None)
                with self.assertRaises(ValueError):
                    config.resolve_activities_dir({}, {'sources': {'activities': str(target)}},
                                                  self.root / 'config', self.root)
        with self.assertRaises(ValueError):
            setup.setup_work_journal(self.root / 'config', cache / 'journal', [self.root / 'notes'])
        with self.assertRaises(ValueError):
            setup.setup_work_journal(self.root / 'config', self.root / 'journal', [cache / 'notes'])
        self.assertFalse((cache / 'personal').exists())
        self.assertFalse((self.root / 'config').exists())
        self.assertFalse((self.root / 'journal').exists())
