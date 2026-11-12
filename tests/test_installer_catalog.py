"""Catalog behavior: use shipped surfaces and reject unsafe source trees."""
import json
import shutil
import sys
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / 'runtime'))
from agent_skills_installer.catalog import build_catalog, load_catalog


class CatalogTests(unittest.TestCase):
    def setUp(self):
        self.providers = json.loads((ROOT / 'installer/providers.json').read_text())
        self.dependencies = json.loads((ROOT / 'installer/dependencies.json').read_text())

    def catalog(self, root=ROOT):
        return build_catalog(root, self.providers, self.dependencies)

    def test_surface_catalog_and_defaults(self):
        specs = self.catalog()
        by_key = {(p.host, p.name): p for p in specs}
        self.assertEqual(len(specs), 18)
        self.assertNotIn('code-review-codex', {s.name for s in by_key['claude', 'quality-gates'].skills})
        self.assertNotIn('code-review-claude', {s.name for s in by_key['codex', 'quality-gates'].skills})
        self.assertNotIn('claude-workflow-designer', {s.name for s in by_key['codex', 'skill-toolbox'].skills})
        for name in ('handoff-mod', 'attention-mod'):
            self.assertIn(('claude', name), by_key)
            self.assertNotIn(('codex', name), by_key)
        handoff = by_key['claude', 'handoff-mod']
        self.assertEqual([(s.name, s.invocation_intent, s.entry) for s in handoff.skills],
                         [('handoff', 'user', '/handoff-mod:handoff')])
        for p in specs:
            self.assertEqual(p.default_selected, p.name != 'superpowers')
            self.assertTrue(p.version)
            self.assertTrue(p.notices)
        superpowers = by_key['claude', 'superpowers']
        self.assertFalse(superpowers.default_selected)
        self.assertTrue(any('STRONGLY RECOMMENDED' in n for n in superpowers.notices))

    def test_manual_intent_preserved(self):
        p = next(p for p in self.catalog() if (p.host, p.name) == ('codex', 'repo-workflow'))
        skill = next(s for s in p.skills if s.name == 'understand-repo')
        self.assertEqual(skill.invocation_intent, 'user')
        self.assertEqual(skill.entry, '$repo-workflow:understand-repo')
        self.assertTrue(skill.purpose)
        journal = next(p for p in self.catalog() if (p.host, p.name) == ('claude', 'work-journal'))
        report = next(s for s in journal.skills if s.name == 'report-generator')
        self.assertGreater(len(report.purpose.split()), 3)

    def test_invalid_catalog_inputs_rejected(self):
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp) / 'repo'
            root.mkdir()
            for f in ('plugin-packages.json', 'skills-catalog.json'):
                shutil.copyfile(ROOT / f, root / f)
            for d in ('plugins', '.agents', '.claude-plugin'):
                shutil.copytree(ROOT / d, root / d, ignore=shutil.ignore_patterns('node_modules', '__pycache__'))
            manifest = root / 'plugins/claude/quality-gates/.claude-plugin/plugin.json'
            original = manifest.read_bytes()
            manifest.unlink()
            with self.assertRaises(ValueError):
                self.catalog(root)
            manifest.write_bytes(original)
            manifest.unlink()
            manifest.symlink_to(ROOT / 'plugins/claude/quality-gates/.claude-plugin/plugin.json')
            with self.assertRaises(ValueError):
                self.catalog(root)
        bad = dict(self.providers, repository='unknown/source')
        with self.assertRaises(ValueError):
            build_catalog(ROOT, bad, self.dependencies)

    def test_invalid_bundle_data_rejected(self):
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / 'catalog.json'
            for payload in ([], {}, {'schema_version': 1, 'plugins': None},
                            {'schema_version': 1, 'plugins': [{}]}):
                path.write_text(json.dumps(payload))
                with self.subTest(payload=payload), self.assertRaises(ValueError):
                    load_catalog(path)
        bad = dict(self.providers, external=self.providers['external'] * 2)
        with self.assertRaises(ValueError):
            build_catalog(ROOT, bad, self.dependencies)


if __name__ == '__main__':
    unittest.main()
