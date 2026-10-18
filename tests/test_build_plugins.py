"""Packaging contracts on a disposable repository, independent of personal settings."""
import json
import tempfile
import unittest
from pathlib import Path

from scripts.plugin_packaging.catalog import load_packages
from scripts.plugin_packaging.render import render_package, render_marketplaces
from scripts.build_plugins import prepare_server

ROOT = Path(__file__).resolve().parents[1]
CONTRACTS = json.loads((ROOT / 'docs/validation/skill-plugins/runtime-contracts.json').read_text())


def fixture(root):
    data = json.loads((ROOT / 'plugin-packages.json').read_text())
    catalog = json.loads((ROOT / 'skills-catalog.json').read_text())
    (root / 'skills-catalog.json').write_text(json.dumps(catalog))
    for p in data['packages']:
        p['runtime_resources'] = []
        for skill in p['skills']:
            path = root / skill / 'SKILL.md'; path.parent.mkdir()
            intent = next(s['invocation_intent'] for s in catalog['skills'] if s['id'] == skill)
            path.write_text(f'---\nname: {skill}\ndescription: Fixture instructions\n'
                            + ('disable-model-invocation: true\n' if intent == 'user' else '')
                            + '---\n\nFixture instructions.\n')
    (root / 'plugin-packages.json').write_text(json.dumps(data))
    marketplace = root / '.claude-plugin/marketplace.json'; marketplace.parent.mkdir()
    marketplace.write_text(json.dumps({'name': 'fixture', 'owner': {'name': 'Fixture'}, 'plugins': [
        {'name': 'attention-mod', 'source': './plugins/attention-mod'},
        {'name': 'handoff-mod', 'source': './plugins/handoff-mod'}]}))
    server = root / 'prepared-server'; (server / 'dist').mkdir(parents=True)
    (server / 'node_modules').mkdir()
    (server / 'dist/index.js').write_text('export {};\n')
    (server / 'package.json').write_text('{"type":"module"}')
    return data['packages'], server


class BuildTests(unittest.TestCase):
    def test_native_manifest_platform_exclusions_and_manual_metadata(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp).resolve(); packages, _ = fixture(root)
            for surface, reviewer, excluded in [('claude', 'code-review-claude', 'code-review-codex'),
                                               ('codex', 'code-review-codex', 'code-review-claude')]:
                dest = root / 'plugins' / surface / 'quality-gates'
                render_package(root, packages[0], surface, dest, CONTRACTS)
                self.assertTrue((dest / 'skills' / reviewer / 'SKILL.md').is_file())
                self.assertFalse((dest / 'skills' / excluded).exists())
                self.assertFalse((dest / 'plugin.json').exists())
                manifest = json.loads((dest / f'.{surface}-plugin/plugin.json').read_text())
                self.assertEqual(manifest['version'], '0.1.0')
            toolbox = next(p for p in packages if p['name'] == 'skill-toolbox')
            dest = root / 'plugins/codex/skill-toolbox'
            render_package(root, toolbox, 'codex', dest, CONTRACTS)
            self.assertFalse((dest / 'skills/claude-workflow-designer').exists())
            self.assertIn('disable-model-invocation: true', (dest / 'skills/skill-sync/SKILL.md').read_text())
            scoped = json.loads((dest / 'skills/skills-catalog.json').read_text())
            self.assertEqual({s['id'] for s in scoped['skills']}, {'skill-router', 'skill-sync', 'skill-auditor'})

    def test_marketplaces_preserve_mods_and_point_to_all_packages(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp).resolve(); packages, _ = fixture(root)
            claude, codex = render_marketplaces(root, packages)
            old = json.loads((root / '.claude-plugin/marketplace.json').read_text())['plugins']
            self.assertEqual(claude['plugins'][:2], old)
            self.assertEqual(len(claude['plugins']), 9)
            self.assertEqual(len(codex['plugins']), 7)
            self.assertTrue(all(p['source']['path'].startswith('./plugins/codex/') for p in codex['plugins']))

    def test_work_journal_launch_uses_measured_platform_contracts(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp).resolve(); packages, server = fixture(root)
            journal = next(p for p in packages if p['name'] == 'work-journal')
            for surface in ['claude', 'codex']:
                dest = root / 'plugins' / surface / 'work-journal'
                render_package(root, journal, surface, dest, CONTRACTS, server_bundle=server)
                entries = json.loads((dest / '.mcp.json').read_text())['mcpServers']
                self.assertEqual(list(entries), [f'agent_skills_work_journal_{surface}'])
                entry = next(iter(entries.values()))
                if surface == 'codex':
                    self.assertEqual(entry['cwd'], './server/')
                    self.assertEqual(entry['args'], ['launch.mjs'])
                    self.assertEqual(entry.get('env_vars'), [
                        'AGENT_SKILLS_CONFIG_DIR', 'XDG_CONFIG_HOME', 'CLAUDE_ACTIVITIES_DIR'])
                else:
                    self.assertEqual(entry['args'], ['${CLAUDE_PLUGIN_ROOT}/server/launch.mjs'])
                self.assertNotIn('--config', entry['args'])
                self.assertIn("import('./dist/index.js')", (dest / 'server/launch.mjs').read_text())

    def test_fail_before_rendering_missing_or_unverified_inputs(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp).resolve(); packages, _ = fixture(root)
            p = packages[0]; p['runtime_resources'] = ['missing.md']
            dest = root / 'destination'
            with self.assertRaises(ValueError):
                render_package(root, p, 'codex', dest, CONTRACTS)
            self.assertFalse(dest.exists())
            p['runtime_resources'] = []
            with self.assertRaises(ValueError):
                render_package(root, p, 'codex', dest, {'surfaces': {}})
            self.assertFalse(dest.exists())

    def test_router_registry_is_scoped_and_index_is_not_installation_evidence(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp).resolve(); packages, _ = fixture(root)
            package = next(p for p in packages if p['name'] == 'skill-toolbox')
            registry = root / 'skill-router/skill-registry.yaml'
            registry.write_text('categories:\n  research:\n    label: Research\n    skills:\n'
                                '      - id: ai-weekly-insight\n        triggers:\n          - news\n'
                                '  meta:\n    label: Meta\n    skills:\n      - id: skill-auditor\n'
                                '        triggers:\n          - audit\nworkflows:\n')
            package['runtime_resources'] = ['skill-router/skill-registry.yaml']
            dest = root / 'plugins/codex/skill-toolbox'
            render_package(root, package, 'codex', dest, CONTRACTS)
            text = (dest / 'skills/skill-router/skill-registry.yaml').read_text()
            self.assertNotIn('ai-weekly-insight', text)
            self.assertIn('skills: []', text)
            self.assertIn('id: skill-auditor', text)
            index = json.loads((dest / 'skills/package-index.json').read_text())['skills']
            self.assertTrue(all(s['availability'] == 'available_to_install' for s in index))
            self.assertNotIn('code-review-gemini', {s['id'] for s in index})

    def test_compile_uses_whitelist_and_does_not_emit_unlisted_source(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp).resolve(); packages, _ = fixture(root)
            source = root / 'skills-query-server'; (source / 'src').mkdir(parents=True)
            (source / 'node_modules').symlink_to(ROOT / 'skills-query-server/node_modules', target_is_directory=True)
            (source / 'package.json').write_text('{"name":"fixture","version":"1.0.0","type":"module"}')
            (source / 'package-lock.json').write_text(json.dumps({'name':'fixture','version':'1.0.0',
                'lockfileVersion':3,'packages':{'':{'name':'fixture','version':'1.0.0'}}}))
            (source / 'tsconfig.json').write_text(json.dumps({'compilerOptions':{'rootDir':'src',
                'outDir':'dist','target':'ES2022','module':'Node16','skipLibCheck':True},'include':['src']}))
            (source / 'src/index.ts').write_text('export const approved = true;\n')
            (source / 'src/private-data.ts').write_text('export const fixtureSecret = "must-not-ship";\n')
            journal = next(p for p in packages if p['name'] == 'work-journal')
            journal['runtime_resources'] = [f'skills-query-server/{p}' for p in [
                'package.json','package-lock.json','tsconfig.json','src/index.ts']]
            (root / 'plugin-packages.json').write_text(json.dumps({'schema_version':1,'packages':packages}))
            destination = root / 'production-bundle'
            prepare_server(root, destination)
            self.assertTrue((destination / 'dist/index.js').is_file())
            self.assertFalse((destination / 'dist/private-data.js').exists())
            self.assertFalse((destination / 'src').exists())

    def test_generated_server_bundles_omit_npm_hidden_lockfile(self):
        for surface in ('claude', 'codex'):
            bundle = ROOT / 'plugins' / surface / 'work-journal/server'
            self.assertTrue((bundle / 'dist/index.js').is_file())
            self.assertFalse((bundle / 'node_modules/.package-lock.json').exists())
            inventory = json.loads((ROOT / 'plugins' / surface / 'work-journal/.generated-files.json').read_text())
            self.assertNotIn('server/node_modules/.package-lock.json', inventory['files'])


if __name__ == '__main__':
    unittest.main()
