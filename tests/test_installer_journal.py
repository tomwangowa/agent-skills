"""Journal setup never overwrites invalid, racing or existing user settings."""
import json
import os
import sys
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'runtime'))
from agent_skills_installer.journal import journal_preview, apply_journal


class JournalTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.home = Path(self.temp.name)
        self.root = self.home / 'config'
        self.env = {'AGENT_SKILLS_CONFIG_DIR': str(self.root)}

    def preview(self):
        return journal_preview(self.env, self.home, '活動 records', ('筆記',))

    def test_journal_preview_has_no_writes(self):
        preview = self.preview()
        self.assertFalse(self.root.exists())
        self.assertIn(str(self.root / '活動 records'), preview['directories'])
        result = apply_journal(preview, preview['fingerprint'])
        self.assertEqual(result['status'], 'created')
        data = json.loads((self.root / 'work-journal.json').read_text())
        self.assertEqual(data['sources']['activities'], str(self.root / '活動 records'))
        self.assertTrue((self.root / '筆記').is_dir())

    def test_new_user_can_use_default_activities_without_notes(self):
        preview = journal_preview(self.env, self.home, '~/.agent-skills/activities', ())
        self.assertEqual(preview['proposed']['sources']['activities'], str(self.home / '.agent-skills/activities'))
        self.assertEqual(preview['proposed']['sources']['notes']['paths'], [])
        self.assertEqual(apply_journal(preview, preview['fingerprint'])['status'], 'created')
        self.assertTrue((self.home / '.agent-skills/activities').is_dir())
        saved = json.loads((self.root / 'work-journal.json').read_text())
        self.assertEqual(saved['sources']['notes']['paths'], [])

    def test_existing_settings_preserved(self):
        preview = self.preview()
        apply_journal(preview, preview['fingerprint'])
        settings = self.root / 'work-journal.json'
        before = settings.read_bytes()
        preview = journal_preview(self.env, self.home, 'new-activities', ('new-notes',))
        self.assertEqual(apply_journal(preview, preview['fingerprint'])['status'], 'preserved')
        self.assertEqual(settings.read_bytes(), before)
        self.assertFalse((self.root / 'new-notes').exists())
        settings.write_text('invalid json')
        with self.assertRaises(ValueError):
            self.preview()
        self.assertEqual(settings.read_text(), 'invalid json')

    def test_config_path_contracts(self):
        xdg = self.home / 'xdg'
        p = journal_preview({'XDG_CONFIG_HOME': str(xdg)}, self.home, '~/activities', ('relative notes',))
        self.assertEqual(p['config_root'], str(xdg / 'agent-skills'))
        p = journal_preview({}, self.home, '~/activities', ('~/notes',))
        self.assertEqual(p['config_root'], str(self.home / '.config/agent-skills'))
        plugin = self.home / 'plugin'
        (plugin / '.codex-plugin').mkdir(parents=True)
        (plugin / '.codex-plugin/plugin.json').write_text('{}')
        alias = self.home / 'alias'
        alias.symlink_to(plugin, target_is_directory=True)
        for forbidden in (plugin, alias):
            with self.assertRaises(ValueError):
                journal_preview({'AGENT_SKILLS_CONFIG_DIR': str(forbidden)}, self.home, 'a', ('n',))

    def test_concurrent_settings_change_preserved(self):
        preview = self.preview()
        self.root.mkdir()
        concurrent_content = b'{"sources":{"activities":"keep","notes":{"paths":["keep-notes"]}}}\n'
        settings = self.root / 'work-journal.json'
        settings.write_bytes(concurrent_content)
        self.assertEqual(apply_journal(preview, preview['fingerprint'])['status'], 'conflict')
        self.assertEqual(settings.read_bytes(), concurrent_content)
        self.assertFalse((self.root / '活動 records').exists())

    def test_atomic_creation_race_does_not_create_data_directories(self):
        preview = self.preview()
        settings = self.root / 'work-journal.json'
        other = b'{"sources":{"activities":"other","notes":{"paths":["other"]}}}'
        real_link = os.link
        def race(src, dst):
            settings.write_bytes(other)
            real_link(src, dst)
        with patch('agent_skills_installer.journal.os.link', side_effect=race):
            result = apply_journal(preview, preview['fingerprint'])
        self.assertEqual(result['status'], 'conflict')
        self.assertEqual(settings.read_bytes(), other)
        self.assertFalse((self.root / '筆記').exists())

    def test_stale_or_edited_preview_rejected(self):
        preview = self.preview()
        preview['directories'].append(str(self.home / 'unapproved'))
        with self.assertRaises(ValueError):
            apply_journal(preview, preview['fingerprint'])
        self.assertFalse(self.root.exists())

    def test_preview_lists_missing_ancestor_directories(self):
        preview = journal_preview({'AGENT_SKILLS_CONFIG_DIR': str(self.home / 'new-parent/config')},
                                  self.home, 'nested/activity', ('other/notes',))
        self.assertIn(str(self.home / 'new-parent'), preview['directories'])
        self.assertIn(str(self.home / 'new-parent/config/nested'), preview['directories'])

    def test_preview_does_not_echo_unrelated_settings_values(self):
        self.root.mkdir()
        settings = {'sources': {'activities': 'a', 'notes': {'paths': ['n']}},
                    'private_extension': 'do-not-echo-this-extension'}
        (self.root / 'work-journal.json').write_text(json.dumps(settings))
        preview = self.preview()
        self.assertNotIn('do-not-echo-this-extension', json.dumps(preview))

    def test_unavailable_filesystem_anchor_is_rejected(self):
        visits = []
        def unavailable(path):
            if path.parent == path:
                visits.append(path)
                if len(visits) > 1:
                    raise AssertionError('Repeated an unavailable filesystem anchor')
            return False
        with patch.object(Path, 'exists', unavailable):
            with self.assertRaises(ValueError):
                self.preview()


if __name__ == '__main__':
    unittest.main()
