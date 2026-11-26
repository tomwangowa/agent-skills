"""lesson inside work-journal: shared settings root, session-start hook, packaged copies."""
from __future__ import annotations

import importlib.util
import json
import os
import shutil
import subprocess
import sys
import tempfile
import unittest
import unittest.mock
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SOURCE = ROOT / 'lesson'
COPIES = {
    'source': SOURCE,
    'claude': ROOT / 'plugins/claude/work-journal/skills/lesson',
    'codex': ROOT / 'plugins/codex/work-journal/skills/lesson',
}
LESSON = (
    '---\nrule: "check the body error code, not only the HTTP status"\nscope: global\n'
    'status: active\ncreated: 2026-11-25\nby: "user"\n---\n\n## 背景\n'
)


class LessonPluginTests(unittest.TestCase):
    def setUp(self):
        self.tmp = Path(tempfile.mkdtemp(prefix='lesson plugin '))
        self.addCleanup(lambda: subprocess.run(['rm', '-rf', str(self.tmp)], check=False))
        self.settings = self.tmp / 'settings'
        self.lessons = self.tmp / 'private lessons'
        self.env = {k: v for k, v in os.environ.items()
                    if k not in {'LESSON_CONFIG', 'XDG_CONFIG_HOME', 'AGENT_SKILLS_CONFIG_DIR'}}
        self.env['AGENT_SKILLS_CONFIG_DIR'] = str(self.settings)
        self.env['HOME'] = str(self.tmp / 'home')

    def run_script(self, skill: Path, script: str, *args: str,
                   stdin: str = '{}') -> subprocess.CompletedProcess:
        return subprocess.run([sys.executable, str(skill / 'scripts' / script), *args],
                              cwd=self.tmp, env=self.env, input=stdin, capture_output=True,
                              text=True, timeout=30)

    def standalone_copy(self) -> Path:
        """A copy outside the repository and the plugin: no bundled runtime next to it."""
        copy = self.tmp / 'standalone/lesson'
        shutil.copytree(SOURCE, copy, ignore=shutil.ignore_patterns('config.json', '__pycache__'))
        return copy

    def set_up_lessons(self, skill: Path) -> None:
        done = self.run_script(skill, 'lesson.py', 'setup', '--dir', str(self.lessons), '--create')
        self.assertEqual(done.returncode, 0, done.stderr)
        (self.lessons / '2026-11-25-error-code.md').write_text(LESSON, encoding='utf-8')

    def test_setup_writes_lesson_json_to_the_settings_root(self):
        for name, skill in COPIES.items():
            with self.subTest(copy=name):
                self.set_up_lessons(skill)
                config = self.settings / 'lesson.json'
                self.assertEqual(json.loads(config.read_text())['lessons_dir'], str(self.lessons))
                self.assertIn('全域 1 條', self.run_script(skill, 'lesson.py', 'digest').stdout)
                config.unlink()

    def test_lesson_config_still_overrides(self):
        other = self.tmp / 'elsewhere.json'
        self.env['LESSON_CONFIG'] = str(other)
        done = self.run_script(SOURCE, 'lesson.py', 'setup', '--dir', str(self.lessons), '--create')
        self.assertEqual(done.returncode, 0, done.stderr)
        self.assertTrue(other.is_file())
        self.assertFalse((self.settings / 'lesson.json').exists())

    def test_hook_is_silent_until_lessons_are_set_up(self):
        for name, skill in COPIES.items():
            with self.subTest(copy=name):
                done = self.run_script(skill, 'session_start_hook.py')
                self.assertEqual((done.returncode, done.stdout, done.stderr), (0, '', ''))

    def test_hook_loads_the_digest_without_the_lessons_path(self):
        for name, skill in COPIES.items():
            with self.subTest(copy=name):
                self.set_up_lessons(skill)
                done = self.run_script(skill, 'session_start_hook.py')
                self.assertEqual(done.returncode, 0, done.stderr)
                context = json.loads(done.stdout)['hookSpecificOutput']['additionalContext']
                self.assertIn('lessons: 全域 1 條', context)
                self.assertIn('check the body error code', context)
                self.assertNotIn(str(self.lessons), context)
                (self.settings / 'lesson.json').unlink()

    def test_hook_reports_an_unreadable_folder_and_still_exits_zero(self):
        self.set_up_lessons(SOURCE)
        subprocess.run(['rm', '-rf', str(self.lessons)], check=True)
        done = self.run_script(SOURCE, 'session_start_hook.py')
        self.assertEqual(done.returncode, 0)
        self.assertIn('讀不到資料夾', json.loads(done.stdout)['hookSpecificOutput']['additionalContext'])

    def test_hook_warns_when_lesson_json_is_broken(self):
        self.settings.mkdir(parents=True)
        (self.settings / 'lesson.json').write_text('{"lessons_dir": ', encoding='utf-8')
        for name, skill in COPIES.items():
            with self.subTest(copy=name):
                done = self.run_script(skill, 'session_start_hook.py')
                self.assertEqual(done.returncode, 0, done.stderr)
                payload = json.loads(done.stdout)
                self.assertIn('lesson digest not loaded', payload['systemMessage'])
                self.assertNotIn('hookSpecificOutput', payload)
                self.assertIn('lesson.json 無法讀取', self.run_script(skill, 'lesson.py', 'digest').stdout)

    def test_hook_warns_when_the_settings_root_is_relative(self):
        self.env['AGENT_SKILLS_CONFIG_DIR'] = 'relative/settings'
        done = self.run_script(SOURCE, 'session_start_hook.py')
        self.assertEqual(done.returncode, 0, done.stderr)
        self.assertIn('lesson digest not loaded', json.loads(done.stdout)['systemMessage'])
        self.assertIn('⚠ 找不到設定位置', self.run_script(SOURCE, 'lesson.py', 'digest').stdout)

    def test_warnings_never_show_a_path(self):
        loop = self.tmp / 'loop'
        loop.mkdir()
        (loop / 'x').symlink_to(loop / 'x')
        self.env['AGENT_SKILLS_CONFIG_DIR'] = str(loop / 'x')
        digest = self.run_script(SOURCE, 'lesson.py', 'digest').stdout
        message = json.loads(self.run_script(SOURCE, 'session_start_hook.py').stdout)['systemMessage']
        for text in (digest, message):
            self.assertIn('⚠' if text is digest else 'not loaded', text)
            self.assertNotIn(str(self.tmp), text)
            self.assertNotIn('/', text.split('(', 1)[-1])

    def test_compaction_reloads_rules_without_asking_for_the_quote(self):
        self.set_up_lessons(SOURCE)
        for source, quoted in (('startup', True), ('clear', True), ('resume', False),
                               ('compact', False), ('not json', True)):
            with self.subTest(source=source):
                stdin = source if source == 'not json' else json.dumps({'source': source})
                done = self.run_script(SOURCE, 'session_start_hook.py', stdin=stdin)
                context = json.loads(done.stdout)['hookSpecificOutput']['additionalContext']
                self.assertIn('check the body error code', context)
                self.assertEqual('verbatim' in context, quoted)
                self.assertEqual('do not quote the digest again' in context, not quoted)

    def test_standalone_copy_uses_the_same_settings_root(self):
        copy = self.standalone_copy()
        self.assertFalse((copy.parent / 'runtime').exists())
        self.set_up_lessons(copy)
        self.assertTrue((self.settings / 'lesson.json').is_file())
        self.assertIn('全域 1 條', self.run_script(copy, 'lesson.py', 'digest').stdout)

    def test_fallback_root_matches_the_runtime(self):
        sys.path.insert(0, str(ROOT / 'runtime'))
        self.addCleanup(sys.path.remove, str(ROOT / 'runtime'))
        from agent_skills_runtime.config import resolve_config_root
        spec = importlib.util.spec_from_file_location('lesson_under_test', SOURCE / 'scripts/lesson.py')
        lesson = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(lesson)
        home = self.tmp / 'home'
        plugin = self.tmp / 'cache/pkg'
        (plugin / '.claude-plugin').mkdir(parents=True)
        (plugin / '.claude-plugin/plugin.json').write_text('{}', encoding='utf-8')
        cases = [{}, {'AGENT_SKILLS_CONFIG_DIR': str(self.settings)},
                 {'XDG_CONFIG_HOME': str(self.tmp / 'xdg')}, {'XDG_CONFIG_HOME': '~/xdg'},
                 {'AGENT_SKILLS_CONFIG_DIR': '~'}, {'AGENT_SKILLS_CONFIG_DIR': 'relative'},
                 {'XDG_CONFIG_HOME': 'relative'}, {'AGENT_SKILLS_CONFIG_DIR': str(plugin / 'x')},
                 {'AGENT_SKILLS_CONFIG_DIR': str(self.tmp / 'a/../b')},
                 {'AGENT_SKILLS_CONFIG_DIR': '~other/x'}, {'XDG_CONFIG_HOME': '~'},
                 {'AGENT_SKILLS_CONFIG_DIR': str(self.settings) + '/'},
                 {'AGENT_SKILLS_CONFIG_DIR': '', 'XDG_CONFIG_HOME': str(self.tmp / 'xdg')},
                 {'AGENT_SKILLS_CONFIG_DIR': str(self.settings), 'XDG_CONFIG_HOME': str(self.tmp / 'xdg')}]
        for case in cases:
            with self.subTest(env=case):
                env = {'HOME': str(home), **case}
                try:
                    expected = resolve_config_root(env, home)
                except ValueError:
                    expected = ValueError
                with unittest.mock.patch.dict(os.environ, env, clear=True):
                    try:
                        actual = lesson.fallback_config_root()
                    except ValueError:
                        actual = ValueError
                self.assertEqual(actual, expected)

    def test_old_config_json_gets_a_migration_hint(self):
        copy = self.standalone_copy()
        (copy / 'config.json').write_text(json.dumps({'lessons_dir': str(self.lessons)}), encoding='utf-8')
        self.assertIn('舊的 config.json', self.run_script(copy, 'lesson.py', 'digest').stdout)

    def test_snippet_warns_only_inside_a_plugin(self):
        for name, skill in COPIES.items():
            with self.subTest(copy=name):
                done = self.run_script(skill, 'lesson.py', 'snippet')
                self.assertEqual(done.returncode, 0, done.stderr)
                self.assertIn('## Lessons', done.stdout)
                self.assertEqual('plugin folder' in done.stderr, name != 'source')

    def test_setup_refuses_a_lessons_folder_inside_a_plugin(self):
        plugin = self.tmp / 'cache/pkg'
        (plugin / '.claude-plugin').mkdir(parents=True)
        (plugin / '.claude-plugin/plugin.json').write_text('{}', encoding='utf-8')
        target = plugin / 'lessons'
        done = self.run_script(SOURCE, 'lesson.py', 'setup', '--dir', str(target), '--create')
        self.assertEqual(done.returncode, 1)
        self.assertIn('outside a plugin folder', done.stderr)
        self.assertFalse(target.exists())

    def test_both_packages_register_the_hook(self):
        for surface in ('claude', 'codex'):
            with self.subTest(surface=surface):
                hooks = json.loads((ROOT / f'plugins/{surface}/work-journal/hooks/hooks.json').read_text())
                commands = [h['command'] for entry in hooks['hooks']['SessionStart'] for h in entry['hooks']]
                self.assertTrue(any('skills/lesson/scripts/session_start_hook.py' in c for c in commands))

    def test_shell_suite_passes(self):
        done = subprocess.run(['bash', str(SOURCE / 'tests/test_lesson.sh')], capture_output=True,
                              text=True, timeout=120, env=self.env)
        self.assertEqual(done.returncode, 0, done.stderr + done.stdout)


if __name__ == '__main__':
    unittest.main()
