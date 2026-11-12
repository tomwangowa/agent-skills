"""Native JSON boundaries never turn uncertainty into permission to install."""
import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / 'runtime'))
from agent_skills_installer.hosts import read_inventory, plugin_action, source_action
from agent_skills_installer.models import PluginSpec

SOURCE = 'https://github.com/tomwangowa/agent-skills.git'


class NativeRunner:
    def __init__(self, plugins, marketplaces, code=0):
        self.plugins, self.marketplaces, self.code = plugins, marketplaces, code
        self.calls = []

    def __call__(self, argv):
        self.calls.append(argv)
        if argv[1:] == ('--version',):
            return subprocess.CompletedProcess(argv, 0, '2.1.319', '')
        data = self.marketplaces if 'marketplace' in argv else self.plugins
        return subprocess.CompletedProcess(argv, self.code, json.dumps(data), '')


class HostTests(unittest.TestCase):
    def claude(self, **changes):
        plugin = dict(id='quality-gates@tomwangowa', version='0.2.0', enabled=True,
                      scope='user', installPath='/fixture/installed')
        plugin.update(changes)
        return NativeRunner([plugin], [dict(name='tomwangowa', source='github',
                                           repo='tomwangowa/agent-skills', installLocation='/fixture/market')])

    def test_observed_inventory_normalization(self):
        native = self.claude()
        inv = read_inventory('claude', native)
        self.assertFalse(inv.errors)
        self.assertEqual(inv.plugins[0].source, SOURCE)
        self.assertEqual(inv.plugins[0].root, '/fixture/installed')
        self.assertEqual(inv.plugins[0].scope, 'user')
        data = json.loads((ROOT / 'tests/fixtures/installer/observed-codex.json').read_text())['output']
        runner = NativeRunner(data, {'marketplaces': [dict(name='tomwangowa', root='/fixture/market',
                  marketplaceSource=dict(sourceType='git', source=SOURCE))]})
        codex = read_inventory('codex', runner)
        self.assertFalse(codex.errors)
        self.assertIsNone(codex.plugins[0].root)
        self.assertIsNone(codex.plugins[0].scope)
        self.assertEqual(codex.plugins[0].version, '0.1.0')
        self.assertTrue(all('--marketplace' in c for c in runner.calls if c[1:3] == ('plugin', 'list')))

    def test_unknown_inventory_never_means_absent(self):
        for field in ('version', 'enabled', 'scope', 'installPath'):
            runner = self.claude()
            del runner.plugins[0][field]
            with self.subTest(field=field):
                self.assertTrue(read_inventory('claude', runner).errors)
        for native in (NativeRunner({}, []), NativeRunner([], [], 1),
                       NativeRunner([{'id': 'broken'}], [])):
            self.assertTrue(read_inventory('claude', native).errors)
        native = self.claude()
        native.marketplaces[0].pop('repo')
        self.assertTrue(read_inventory('claude', native).errors)
        native = self.claude()
        native.plugins.append(dict(native.plugins[0], scope='project'))
        observed = read_inventory('claude', native)
        self.assertFalse(observed.errors)
        self.assertEqual([p.scope for p in observed.plugins], ['user', 'project'])
        def malformed(argv):
            return subprocess.CompletedProcess(argv, 0, 'not json', '')
        self.assertTrue(read_inventory('claude', malformed).errors)

    def test_superpowers_provider_identity_across_marketplaces(self):
        native = NativeRunner([dict(id='superpowers@upstream-alias', version='7.0.2', enabled=True,
                                   scope='user', installPath='/fixture/superpowers')],
                             [dict(name='upstream-alias', source='github', repo='obra/superpowers', installLocation='/fixture/market')])
        inv = read_inventory('claude', native)
        self.assertEqual(inv.plugins[0].source, 'https://github.com/obra/superpowers.git')
        self.assertEqual(inv.plugins[0].name, 'superpowers')

    def test_commands_are_host_specific_and_scope_explicit(self):
        for host, command in [('claude', 'update'), ('codex', 'add')]:
            spec = PluginSpec(host, 'quality-gates', 'tomwangowa', SOURCE, '0.2.0')
            action = plugin_action(spec, 'update')
            self.assertEqual(action.argv[0:3], (host, 'plugin', command))
            if host == 'claude':
                self.assertIn('--scope', action.argv)
                self.assertIn('user', action.argv)
        with self.assertRaises(ValueError):
            plugin_action(PluginSpec('claude', '--bad', 'tomwangowa', SOURCE, '0.2.0'), 'install')
        with self.assertRaises(ValueError):
            source_action('claude', 'untrusted/source', 'add_marketplace')

    def test_registered_superpowers_uses_manifest_identity(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            (root / '.claude-plugin').mkdir()
            (root / '.claude-plugin/plugin.json').write_text(json.dumps({
                'name': 'superpowers', 'version': '7.0.2',
                'repository': 'https://github.com/obra/superpowers'}))
            (root / 'skills/writing-plans').mkdir(parents=True)
            (root / 'skills/writing-plans/SKILL.md').write_text('---\nname: writing-plans\n---\n')
            native = NativeRunner([dict(id='superpowers@superpowers-marketplace', version='7.0.2',
                                       enabled=True, scope='user', installPath=str(root))],
                                 [dict(name='superpowers-marketplace', source='github',
                                       repo='obra/superpowers-marketplace', installLocation='/fixture/market')])
            inv = read_inventory('claude', native)
            self.assertEqual(inv.plugins[0].source, 'https://github.com/obra/superpowers.git')

    def test_claude_git_url_source_is_not_mistaken_for_missing_repo(self):
        rows = json.loads((ROOT / 'tests/fixtures/installer/observed-claude-git.json').read_text())['output']
        native = NativeRunner([], rows)
        inv = read_inventory('claude', native)
        self.assertFalse(inv.errors)
        self.assertEqual(inv.marketplaces[0].source, SOURCE)
        self.assertEqual(inv.plugins, ())
        for value in (None, '', 5):
            broken = NativeRunner([], [dict(rows[0], url=value)])
            self.assertTrue(read_inventory('claude', broken).errors)


if __name__ == '__main__':
    unittest.main()
