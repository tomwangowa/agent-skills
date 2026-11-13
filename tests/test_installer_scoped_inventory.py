"""Scoped existing plugins must not block unrelated installs or invite unsafe updates."""
import io
import json
from pathlib import Path
import shutil
import subprocess
import sys
import tempfile
import unittest
from dataclasses import replace

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / 'runtime'))
from agent_skills_installer.catalog import build_catalog
from agent_skills_installer.hosts import read_inventory
from agent_skills_installer.models import PluginSpec
from agent_skills_installer.planning import make_plan
from agent_skills_installer.ui import run
from test_installer_cli import FixtureCLI, Terminal
from test_installer_hosts import NativeRunner

SOURCE = 'https://github.com/tomwangowa/agent-skills.git'


def scoped_rows(name='skill-creator', marketplace='claude-plugins-official'):
    return [dict(id=f'{name}@{marketplace}', version='1.0.0', enabled=True,
                 scope=scope, installPath='/fixture/' + scope + '/' + name)
            for scope in ('user', 'project')]


def markets():
    return [dict(name='tomwangowa', source='github', repo='tomwangowa/agent-skills',
                 installLocation='/fixture/own'),
            dict(name='claude-plugins-official', source='github', repo='anthropics/claude-plugins-official',
                 installLocation='/fixture/official')]


class ScopedInventoryTests(unittest.TestCase):
    def test_unrelated_personal_and_project_copies_do_not_block_new_package(self):
        native = NativeRunner(scoped_rows(), markets())
        inv = read_inventory('claude', native)
        self.assertFalse(inv.errors)
        self.assertEqual([p.scope for p in inv.plugins], ['user', 'project'])
        self.assertNotIn('superpowers-inventory-unverified', inv.capabilities)
        spec = PluginSpec('claude', 'quality-gates', 'tomwangowa', SOURCE, '0.2.0')
        inv = replace(inv, capabilities=inv.capabilities + ('catalog-verified:tomwangowa',))
        plan = make_plan((spec,), (inv,), {('claude', 'quality-gates')}, set(), {})
        self.assertEqual([(a.kind, a.target) for a in plan.actions], [('install', 'quality-gates@tomwangowa')])

    def test_selected_ambiguous_copies_still_cannot_be_updated(self):
        inv = read_inventory('claude', NativeRunner(scoped_rows('quality-gates', 'tomwangowa'), markets()))
        spec = PluginSpec('claude', 'quality-gates', 'tomwangowa', SOURCE, '0.2.0')
        fresh = replace(spec, name='work-journal')
        inv = replace(inv, capabilities=inv.capabilities + ('catalog-verified:tomwangowa',))
        plan = make_plan((spec, fresh), (inv,), {('claude', p.name) for p in (spec, fresh)},
                         {('claude', 'quality-gates')}, {})
        self.assertEqual([(a.kind, a.target) for a in plan.actions], [('install', 'work-journal@tomwangowa')])
        self.assertEqual(len(inv.plugins), 2)
        self.assertEqual(plan.prior_results[0].status, 'skipped')
        self.assertIn('quality-gates', plan.prior_results[0].detail)
        self.assertIn('All copies will be kept', plan.prior_results[0].detail)


class ScopedFixtureCLI(FixtureCLI):
    def __call__(self, argv):
        result = super().__call__(argv)
        if argv[0] == 'claude' and argv[1:] == ('plugin', 'marketplace', 'list', '--json'):
            rows = json.loads(result.stdout)
            rows.append(markets()[1])
            return subprocess.CompletedProcess(argv, 0, json.dumps(rows), '')
        return result


class ScopedInventoryUITests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name)
        catalog = build_catalog(ROOT, json.loads((ROOT / 'installer/providers.json').read_text()),
                                json.loads((ROOT / 'installer/dependencies.json').read_text()))
        self.specs = tuple(p for p in catalog if p.host == 'claude' and p.name == 'quality-gates')
        shutil.copytree(ROOT / 'plugins/claude/quality-gates', self.root / 'plugins/claude/quality-gates')

    def test_explains_existing_copies_and_installs_unrelated_package(self):
        native = ScopedFixtureCLI(self.root)
        native.installed = scoped_rows()
        answers = iter(['1', '', '', 'y'])
        output = Terminal()
        code = run(self.specs, lambda _: next(answers), output, native)
        self.assertEqual(code, 0, output.getvalue())
        self.assertTrue((self.root / 'installed/quality-gates/.claude-plugin/plugin.json').is_file())
        self.assertEqual(len(native.mutations), 1)
        self.assertEqual(native.mutations[0][3], 'quality-gates@tomwangowa')
        self.assertEqual(native.installed[:2], scoped_rows())
        self.assertNotIn('skill-creator', output.getvalue())
        self.assertNotIn('Multiple scopes for one plugin identity', output.getvalue())

    def test_selected_package_with_multiple_scopes_still_explains_preservation(self):
        native = NativeRunner(scoped_rows('quality-gates', 'tomwangowa'), markets())
        answers = iter(['1', '1', 'q'])
        output = Terminal()
        self.assertEqual(run(self.specs, lambda _: next(answers), output, native), 130)
        self.assertIn('quality-gates', output.getvalue())
        self.assertIn('All existing copies will be kept', output.getvalue())
        self.assertFalse(any('install' in argv or 'update' in argv for argv in native.calls))

    def test_global_read_failure_stops_before_update_or_install_prompts(self):
        native = NativeRunner({}, markets())
        prompts = []
        answers = iter(['1', '1'])
        def answer(prompt):
            prompts.append(prompt)
            return next(answers) if len(prompts) <= 2 else 'q'
        output = Terminal()
        code = run(self.specs, answer, output, native)
        self.assertEqual(code, 1, output.getvalue())
        self.assertEqual(len(prompts), 2, prompts)
        self.assertNotIn('Updates (', output.getvalue())
        self.assertIn('installed plugins', output.getvalue())
        self.assertIn('Other selected hosts can continue', output.getvalue())
        self.assertFalse(any('install' in argv or 'update' in argv for argv in native.calls))

    def test_failed_host_does_not_block_healthy_host(self):
        healthy = FixtureCLI(self.root)
        def native(argv):
            if argv[0] == 'claude':
                return healthy(argv)
            if argv[1:] == ('--version',):
                return subprocess.CompletedProcess(argv, 0, 'codex-cli 0.167.0', '')
            if argv[1:] == ('plugin', 'marketplace', 'list', '--json'):
                return subprocess.CompletedProcess(argv, 0, '{}', '')
            raise AssertionError('The unreadable host must not be mutated.')
        specs = (*self.specs, replace(self.specs[0], host='codex'))
        answers = iter(['1,2', '', '', 'y'])
        output = Terminal()
        code = run(specs, lambda _: next(answers), output, native)
        self.assertEqual(code, 1, output.getvalue())
        self.assertTrue((self.root / 'installed/quality-gates/.claude-plugin/plugin.json').is_file())
        self.assertEqual(len(healthy.mutations), 1)
        self.assertIn('Cannot read the installed plugins from Codex', output.getvalue())
