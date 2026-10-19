"""Approved package membership and fail-closed resource selection."""
import copy
import json
import subprocess
import tempfile
import unittest
from pathlib import Path

from scripts.plugin_packaging.catalog import load_packages, validate_packages, surface_skills
from scripts.plugin_packaging.resources import collect_resources

ROOT = Path(__file__).resolve().parents[1]
APPROVED = {
    'quality-gates': 'code-review-claude code-review-codex completion-gate codebase-audit pr-review-assistant secure-ai-development-gate',
    'technical-decisions': 'brainstorming assumption-extractor critical-research deep-reading micro-poc-validator narrative-auditor research-cross-validator research-synthesis tech-feasibility tech-research-pipeline role-orchestrator role-pm role-rd spec-gap-finder technical-proposal-review ui-design-analyzer',
    'repo-workflow': 'code-story-teller repo-sync handoff session-start task-bootstrap',
    'content-tools': 'presentation-planner interactive-presentation-generator sepia md-translate pptx-to-md',
    'work-journal': 'activity-logger work-log-analyzer',
    'session-preferences': 'session-preferences control-return',
    'skill-toolbox': 'skill-auditor skill-router skill-sync claude-workflow-designer',
}


class PackageTests(unittest.TestCase):
    def setUp(self):
        self.packages = load_packages(ROOT)
        self.catalog = json.loads((ROOT / 'skills-catalog.json').read_text())['skills']

    def test_exact_approved_membership(self):
        self.assertEqual({p['name']: p['skills'] for p in self.packages},
                         {name: skills.split() for name, skills in APPROVED.items()})
        members = [s for p in self.packages for s in p['skills']]
        self.assertEqual((len(members), len(set(members))), (40, 40))
        self.assertEqual(validate_packages(self.packages, self.catalog), [])
        for p in self.packages:
            self.assertEqual(p['version'], '0.1.0')
        lifecycles = {s['id']: s['lifecycle'] for s in self.catalog}
        self.assertEqual(lifecycles['code-review-codex'], 'personal')
        self.assertEqual(lifecycles['work-log-analyzer'], 'personal')
        self.assertEqual(lifecycles['session-preferences'], 'experimental')
        self.assertEqual(lifecycles['control-return'], 'experimental')

    def test_unknown_duplicate_retired_and_bad_dependencies_rejected(self):
        for field, value in [('skills', ['missing-skill']), ('skills', ['code-review-gemini']),
                             ('version', 'latest'), ('platforms', ['desktop']),
                             ('dependencies', [{'kind': 'mandatory', 'provider': 'superpowers',
                                                'skills': [], 'condition': '', 'tested_versions': []}]),
                             ('dependencies', [{'kind': 'optional', 'provider': 'quality-gates',
                                                'skills': ['code-review-gemini'], 'condition': '', 'tested_versions': []}])]:
            with self.subTest(field=field, value=value):
                packages = copy.deepcopy(self.packages)
                packages[0][field] = value
                self.assertTrue(validate_packages(packages, self.catalog))
        packages = copy.deepcopy(self.packages)
        packages[1]['skills'].append(packages[0]['skills'][0])
        self.assertTrue(validate_packages(packages, self.catalog))

    def test_dependency_contract_not_just_any_nonempty_object(self):
        for dep in [None, {'kind': 'conditional', 'provider': 'superpowers', 'skills': ['writing-plans'],
                           'condition': '', 'tested_versions': []},
                    {'kind': 'required', 'provider': '', 'skills': ['writing-plans'],
                     'condition': '', 'tested_versions': []},
                    {'kind': 'optional', 'provider': 'superpowers', 'skills': ['writing-plans'],
                     'condition': 'Only when selected', 'tested_versions': '7.0.0'}]:
            packages = copy.deepcopy(self.packages)
            packages[0]['dependencies'] = [dep]
            self.assertTrue(validate_packages(packages, self.catalog))

    def test_malformed_dependency_types_report_errors_instead_of_crashing(self):
        for field, value in [('kind', []), ('provider', {}), ('condition', []),
                             ('skills', {}), ('tested_versions', None)]:
            packages = copy.deepcopy(self.packages)
            packages[0]['dependencies'] = [{'kind': 'optional', 'provider': 'superpowers',
                                            'skills': ['writing-plans'], 'condition': '', 'tested_versions': []}]
            packages[0]['dependencies'][0][field] = value
            with self.subTest(field=field):
                self.assertTrue(validate_packages(packages, self.catalog))

    def test_surface_selection_preserves_source_and_manual_intent(self):
        quality = self.packages[0]
        self.assertNotIn('code-review-claude', surface_skills(quality, 'codex'))
        self.assertNotIn('code-review-codex', surface_skills(quality, 'claude'))
        toolbox = next(p for p in self.packages if p['name'] == 'skill-toolbox')
        self.assertNotIn('claude-workflow-designer', surface_skills(toolbox, 'codex'))
        self.assertIn('claude-workflow-designer', surface_skills(toolbox, 'claude'))
        with self.assertRaises(ValueError):
            surface_skills(toolbox, 'desktop')

    def test_real_resources_are_explicit_and_have_no_development_data(self):
        for package in self.packages:
            paths = collect_resources(ROOT, package)
            self.assertIn(ROOT / package['skills'][0] / 'SKILL.md', paths)
            self.assertEqual(len(paths), len(set(paths)))
            self.assertFalse(any('node_modules' in p.parts or 'tests' in p.parts or '__pycache__' in p.parts for p in paths))
        journal = next(p for p in self.packages if p['name'] == 'work-journal')
        self.assertIn('skills-query-server/package-lock.json', journal['runtime_resources'])

    def test_missing_private_escape_and_symlink_resources_rejected(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp).resolve() / 'repo'; root.mkdir()
            (root / 'safe').mkdir(); (root / 'safe/SKILL.md').write_text('Retired code-review-gemini is not routed.')
            package = {'skills': ['safe'], 'runtime_resources': []}
            self.assertEqual(collect_resources(root, package), [root / 'safe/SKILL.md'])
            outside = Path(tmp) / 'secret'; outside.write_text('private')
            (root / 'safe/outside.md').symlink_to(outside)
            (root / 'safe/local.md').symlink_to(root / 'safe/SKILL.md')
            for path in ['missing.py', 'safe/outside.md', 'safe/local.md', '../secret',
                         str(outside), 'config.json', '.env', 'safe/tests/test.py',
                         'safe/config.json', 'safe/work-journal.json', 'safe/.base-hashes.json']:
                with self.subTest(path=path), self.assertRaises(ValueError):
                    collect_resources(root, dict(package, runtime_resources=[path]))
            with self.assertRaises(ValueError):
                collect_resources(root, dict(package, runtime_resources=['safe']))

    def test_plugin_sync_does_not_treat_installed_package_as_standalone_source(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp); scripts = root / 'skills/skill-sync/scripts'; scripts.mkdir(parents=True)
            (root / '.codex-plugin').mkdir()
            (root / '.codex-plugin/plugin.json').write_text('{}')
            script = scripts / 'sync.sh'
            script.write_bytes((ROOT / 'skill-sync/scripts/sync.sh').read_bytes())
            result = subprocess.run(['bash', str(script), '--dry-run'], capture_output=True, text=True)
            self.assertNotEqual(result.returncode, 0)
            self.assertIn('--source', result.stderr)
            self.assertFalse((root / 'skills/.skill-sync-targets').exists())

    def test_plugin_sync_can_preview_explicit_standalone_source_without_writes(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp); scripts = root / 'plugin/skills/skill-sync/scripts'; scripts.mkdir(parents=True)
            (root / 'plugin/.claude-plugin').mkdir()
            (root / 'plugin/.claude-plugin/plugin.json').write_text('{}')
            script = scripts / 'sync.sh'
            script.write_bytes((ROOT / 'skill-sync/scripts/sync.sh').read_bytes())
            source = root / 'standalone'; (source / 'example').mkdir(parents=True)
            (source / 'example/SKILL.md').write_text('Example')
            target = root / 'missing-target'
            (source / '.skill-sync-targets').write_text(str(target) + '\n')
            before = {p.relative_to(root): p.read_bytes() for p in root.rglob('*') if p.is_file()}
            result = subprocess.run(['bash', str(script), '--source', str(source), '--dry-run'],
                                    capture_output=True, text=True)
            self.assertEqual(result.returncode, 0, result.stderr)
            self.assertIn('skipped', result.stdout)
            self.assertFalse(target.exists())
            self.assertEqual(before, {p.relative_to(root): p.read_bytes() for p in root.rglob('*') if p.is_file()})


if __name__ == '__main__':
    unittest.main()
