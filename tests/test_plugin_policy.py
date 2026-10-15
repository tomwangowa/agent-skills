"""Scoped engineering routing and explicit, version-specific dependency evidence."""
import json
import os
import subprocess
import tempfile
import unittest
from pathlib import Path

from scripts.plugin_packaging.catalog import load_packages
from scripts.plugin_packaging.render import render_package
from runtime.agent_skills_runtime.policy import check_superpowers, render_policy

ROOT = Path(__file__).resolve().parents[1]
CONTRACTS = json.loads((ROOT / 'docs/validation/skill-plugins/runtime-contracts.json').read_text())


class PolicyTests(unittest.TestCase):
    def setUp(self):
        self.packages = {p['name']: p for p in load_packages(ROOT)}

    def test_owned_routes_and_platform_reviewer(self):
        content, _ = render_policy(self.packages['quality-gates'], 'codex', {})
        self.assertIn('quality-gates:completion-gate', content)
        self.assertIn('quality-gates:code-review-codex', content)
        self.assertNotIn('code-review-claude', content)
        self.assertIn('higher-priority', content)
        content, _ = render_policy(self.packages['technical-decisions'], 'claude', {})
        self.assertIn('technical-decisions:brainstorming', content)
        self.assertIn('manual checkpoint', content)

    def test_unrelated_packages_do_not_require_superpowers(self):
        for name in ['content-tools', 'work-journal', 'session-preferences', 'repo-workflow']:
            content, issues = render_policy(self.packages[name], 'codex', {})
            self.assertEqual(issues, [])
            self.assertNotIn('Install Superpowers', content)

    def test_missing_skills_unregistered_and_untested_versions_are_distinct(self):
        self.assertEqual(check_superpowers(['writing-plans'], {}, ['7.0.0'])[0]['status'], 'missing')
        provider = {'name': 'superpowers', 'version': '7.0.0', 'skills': ['writing-plans'], 'registered': False}
        inventory = {'providers': [provider]}
        self.assertEqual(check_superpowers(['writing-plans'], inventory, ['7.0.0'])[0]['status'], 'missing')
        provider['registered'] = True; provider['skills'] = []
        self.assertEqual(check_superpowers(['writing-plans'], inventory, ['7.0.0'])[0]['status'], 'missing_skill')
        provider['skills'] = ['writing-plans']; provider['version'] = '99.0.0'
        self.assertEqual(check_superpowers(['writing-plans'], inventory, ['7.0.0'])[0]['status'], 'untested_version')

    def test_same_identity_different_source_and_registered_version_contract(self):
        inventory = {'providers': [{'name':'superpowers','registered':True,'version':'7.0.0',
                                  'skills':['writing-plans'],'source':'another-marketplace'}]}
        self.assertEqual(check_superpowers(['writing-plans'], inventory, ['7.0.0'])[0]['status'], 'ok')
        self.assertEqual(check_superpowers([], {}, [])[0]['status'], 'not_required')
        self.assertEqual(check_superpowers(['writing-plans'], inventory, [])[0]['status'], 'untested_version')

    def test_actual_packaged_hook_ignores_preference_off_and_stays_scoped(self):
        with tempfile.TemporaryDirectory() as tmp:
            destination = Path(tmp).resolve() / 'relocated 包'
            render_package(ROOT, self.packages['quality-gates'], 'codex', destination, CONTRACTS)
            hooks = json.loads((destination / 'hooks/hooks.json').read_text())['hooks']['SessionStart']
            self.assertEqual(hooks[0]['matcher'], 'startup|resume|clear|compact')
            env = dict(os.environ); env['AGENT_SESSION_PREFS'] = 'off'; env['PYTHONDONTWRITEBYTECODE'] = '1'
            result = subprocess.run(['python3', str(destination / 'hooks/policy.py')],
                                    input='{"source":"startup"}', env=env, cwd=tmp, capture_output=True, text=True)
            self.assertEqual(result.returncode, 0, result.stderr)
            context = json.loads(result.stdout)['hookSpecificOutput']['additionalContext']
            self.assertIn('quality-gates:completion-gate', context)
            self.assertNotIn('technical-decisions:brainstorming', context)


if __name__ == '__main__':
    unittest.main()
