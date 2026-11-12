"""Only selected missing commands and explicitly mapped existing managers."""
import json
import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / 'runtime'))
from agent_skills_installer.dependencies import dependency_action, missing_dependencies
from agent_skills_installer.models import PluginSpec


class DependencyTests(unittest.TestCase):
    def setUp(self):
        self.mapping = json.loads((ROOT / 'installer/dependencies.json').read_text())

    def test_dependency_action_uses_existing_manager_only(self):
        self.assertIsNone(dependency_action('jq', 'macos', frozenset(), self.mapping))
        self.assertIsNone(dependency_action('unknown', 'windows', frozenset({'winget'}), self.mapping))
        self.assertIsNone(dependency_action('bash', 'windows', frozenset({'winget'}), self.mapping))
        action = dependency_action('jq', 'macos', frozenset({'brew'}), self.mapping)
        self.assertEqual(action.argv, ('brew', 'install', 'jq'))
        self.assertTrue(any('dependencies' in value for _, value in action.preconditions))
        self.assertNotIn('sudo', action.argv)

    def test_selected_missing_tools_only(self):
        catalog = (PluginSpec('claude', 'one', 'tomwangowa', 'source', '1.0.0', commands=('jq',)),
                   PluginSpec('codex', 'two', 'tomwangowa', 'source', '1.0.0', commands=('rsync',)))
        missing = missing_dependencies(catalog, frozenset({('claude', 'one')}), {'jq': False, 'rsync': False})
        self.assertEqual(missing, ('jq',))
        self.assertEqual(missing_dependencies(catalog, frozenset({('claude', 'one')}), {'jq': True}), ())


if __name__ == '__main__':
    unittest.main()
