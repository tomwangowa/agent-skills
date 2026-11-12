"""Native removal contracts, filesystem preservation and state checks."""
import importlib
import importlib.util
import io
import json
from dataclasses import replace
from pathlib import Path
import subprocess
import shutil
import sys
import tempfile
import unittest
from unittest.mock import patch

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / 'runtime'))
from agent_skills_installer.models import InstalledPlugin, Inventory, Marketplace, PluginSpec
from agent_skills_installer.execution import execute
from agent_skills_installer.progress import PackageProgress

SOURCE = 'https://github.com/tomwangowa/agent-skills.git'
VERSION = '2.1.322 (Claude Code)'


class Terminal(io.StringIO):
    def isatty(self):
        return True


class RemovalTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name).resolve()
        self.claude = self.root / 'claude'
        self.spec = PluginSpec('claude', 'quality-gates', 'tomwangowa', SOURCE, '0.2.0')
        self.user = self.plugin('quality-gates', 'user', '9.0.0')
        self.project = self.plugin('quality-gates', 'project', '0.1.0')
        self.other = self.plugin('unrelated', 'user', '1.0.0')
        self.inv = Inventory('claude', VERSION, (self.user, self.project, self.other),
                             (Marketplace('tomwangowa', SOURCE, str(self.root / 'market')),))

    def api(self):
        self.assertIsNotNone(importlib.util.find_spec('agent_skills_installer.removal'),
                             'Personal removal planner is not implemented')
        return importlib.import_module('agent_skills_installer.removal')

    def plugin(self, name, scope, version, market='tomwangowa', source=SOURCE):
        path = self.claude / 'plugins/cache' / market / name / version
        (path / '.claude-plugin').mkdir(parents=True, exist_ok=True)
        (path / '.claude-plugin/plugin.json').write_text(json.dumps({'name': name, 'version': version}))
        (path / 'skill.txt').write_text('package content: ' + name)
        return InstalledPlugin('claude', name, market, source, version, str(path), True, scope)

    def options(self, inv=None, catalog=None, *, codex_remove_supported=False):
        return self.api().removal_options(catalog or (self.spec,), (inv or self.inv,), self.claude,
                                          codex_remove_supported=codex_remove_supported)

    def plan(self, inv=None):
        options = self.options(inv)
        return self.api().make_removal_plan(options, frozenset(o.key for o in options if not o.reason))

    def receipt(self, action, **changes):
        data = dict(command='uninstall', outcome='ok', plugin=action.target, pluginId=action.target,
                    scope='user', keptData=True, message='Successfully uninstalled plugin')
        data.update(changes)
        return subprocess.CompletedProcess(action.argv, 0, json.dumps(data), '')

    def test_only_catalog_packages_and_no_default_removal(self):
        options = self.options()
        self.assertEqual([(o.plugin.name, o.plugin.scope, o.reason) for o in options], [('quality-gates', 'user', '')])
        self.assertFalse(options[0].default_selected)
        self.assertEqual(self.api().make_removal_plan(options, frozenset()).actions, ())

    def test_newer_manual_install_uses_native_user_scope_and_keeps_data(self):
        action, = self.plan().actions
        self.assertEqual(action.argv, ('claude', 'plugin', 'uninstall', 'quality-gates@tomwangowa',
                                       '--scope', 'user', '--keep-data', '--json'))
        self.assertEqual(dict(action.preconditions)['version'], '9.0.0')
        self.assertTrue(self.api().recheck_removal(action, self.inv, self.claude))

    def test_disabled_personal_install_can_be_removed(self):
        inv = replace(self.inv, plugins=(replace(self.user, enabled=False), self.project))
        self.assertEqual(len(self.plan(inv).actions), 1)

    def test_project_only_and_duplicate_personal_installs_are_kept(self):
        for rows in [(self.project,), (self.user, self.user, self.project)]:
            with self.subTest(rows=len(rows)):
                options = self.options(replace(self.inv, plugins=rows))
                self.assertTrue(all(o.reason for o in options))
                self.assertEqual(self.api().make_removal_plan(options, frozenset(o.key for o in options)).actions, ())

    def test_source_conflict_unknown_cli_and_inventory_failure_cannot_remove(self):
        cases = [replace(self.inv, plugins=(replace(self.user, source='https://other.invalid/repo'),)),
                 replace(self.inv, cli_version='future version'), replace(self.inv, errors=('unreadable',))]
        for inv in cases:
            with self.subTest(inv=inv.cli_version):
                options = self.options(inv)
                self.assertFalse(any(not o.reason for o in options))
                self.assertEqual(self.api().make_removal_plan(options, frozenset(o.key for o in options)).actions, ())

    def test_symlinked_or_foreign_cache_cannot_be_removed(self):
        original = Path(self.user.root)
        moved = original.with_name('saved')
        original.rename(moved)
        original.symlink_to(moved, target_is_directory=True)
        self.assertTrue(self.options()[0].reason)
        foreign = self.root / 'personal-documents'
        inv = replace(self.inv, plugins=(replace(self.user, root=str(foreign)),))
        self.assertTrue(self.options(inv)[0].reason)

    def test_changed_target_or_project_bytes_reject_stale_preview(self):
        action, = self.plan().actions
        changed = replace(self.inv, plugins=(replace(self.user, enabled=False), self.project, self.other))
        self.assertFalse(self.api().recheck_removal(action, changed, self.claude))
        (Path(self.project.root) / 'skill.txt').write_text('changed after preview')
        self.assertFalse(self.api().recheck_removal(action, self.inv, self.claude))

    def test_success_requires_user_absence_and_other_records_and_project_bytes_preserved(self):
        action, = self.plan().actions
        after = replace(self.inv, plugins=(self.other, self.project))
        self.assertTrue(self.api().verify_removal(action, self.receipt(action), self.inv, after))
        self.assertFalse(self.api().verify_removal(action, self.receipt(action), self.inv, self.inv))
        self.assertFalse(self.api().verify_removal(action, self.receipt(action), self.inv, replace(after, plugins=(self.other,))))
        (Path(self.project.root) / 'skill.txt').unlink()
        self.assertFalse(self.api().verify_removal(action, self.receipt(action), self.inv, after))

    def test_receipt_cannot_claim_another_identity_scope_or_data_loss(self):
        action, = self.plan().actions
        after = replace(self.inv, plugins=(self.project, self.other))
        for changes in [{'scope':'project'}, {'pluginId':'another@tomwangowa'}, {'keptData':False},
                        {'outcome':'failed'}, {'command':'install'}]:
            with self.subTest(changes=changes):
                self.assertFalse(self.api().verify_removal(action, self.receipt(action, **changes), self.inv, after))

    def test_codex_shared_cache_removal_uses_qualified_identity_and_postcondition(self):
        spec = replace(self.spec, host='codex')
        codex_home = self.root / 'codex'
        cache_root = codex_home / 'plugins/cache/tomwangowa/quality-gates'
        (cache_root / '9.0.0').mkdir(parents=True)
        (cache_root / '9.0.0/plugin.json').write_text('{}')
        row = replace(self.user, host='codex', root=None, scope=None)
        inv = Inventory('codex', 'codex-cli 0.166.0', (row,), config_root=str(codex_home))
        options = self.options(inv, (spec,), codex_remove_supported=True)
        self.assertFalse(options[0].reason)
        action, = self.api().make_removal_plan(options, frozenset(o.key for o in options)).actions
        self.assertEqual(action.argv, ('codex', 'plugin', 'remove', 'quality-gates@tomwangowa', '--json'))
        self.assertTrue(self.api().recheck_removal(action, inv, str(codex_home), codex_remove_supported=True))
        after = replace(inv, plugins=())
        result = subprocess.CompletedProcess(action.argv, 0, json.dumps({
            'pluginId': 'quality-gates@tomwangowa', 'name': 'quality-gates',
            'marketplaceName': 'tomwangowa'
        }, indent=2), '')
        shutil.rmtree(cache_root)
        self.assertTrue(self.api().verify_removal(action, result, inv, after))

    def test_existing_superpowers_provider_can_be_removed_but_same_name_impostor_cannot(self):
        spec = replace(self.spec, name='superpowers', marketplace='claude-plugins-official')
        real = self.plugin('superpowers', 'user', '7.0.2', 'superpowers-marketplace', 'https://github.com/obra/superpowers.git')
        inv = replace(self.inv, plugins=(real,))
        options = self.options(inv, (spec,))
        self.assertFalse(options[0].reason)
        action, = self.api().make_removal_plan(options, frozenset(o.key for o in options)).actions
        self.assertEqual(action.target, 'superpowers@superpowers-marketplace')
        fake = replace(inv, plugins=(replace(real, source=SOURCE),))
        self.assertTrue(self.options(fake, (spec,))[0].reason)

    def test_verified_removal_is_not_reported_as_installed(self):
        action, = self.plan().actions
        plan = self.plan()
        progress = PackageProgress(Terminal())
        results = execute(plan, plan.fingerprint, lambda _: self.receipt(action), lambda _: True,
                          lambda *_: True, on_event=progress.event)
        self.assertEqual(results[0].status, 'removed')
        self.assertIn('quality-gates [############] removed:', progress.output.getvalue())
        self.assertNotIn('Source / quality-gates', progress.output.getvalue())


class RemovalCLI:
    """Native-shaped inventory backed by disposable cache and registry files."""
    def __init__(self, root, mode='ok'):
        self.root, self.mode, self.calls = root, mode, []
        self.claude = root / 'claude'
        self.registry = root / 'native-rows.json'
        rows = []
        for name in ('quality-gates', 'technical-decisions'):
            path = self.claude / 'plugins/cache/tomwangowa' / name / '9.0.0'
            (path / '.claude-plugin').mkdir(parents=True)
            (path / '.claude-plugin/plugin.json').write_text(json.dumps({'name': name, 'version':'9.0.0'}))
            (path / 'skill.txt').write_text('content: ' + name)
            rows.append(dict(id=name+'@tomwangowa', version='9.0.0', enabled=True, scope='user', installPath=str(path)))
        rows.append(dict(rows[0], scope='project'))
        self.registry.write_text(json.dumps(rows))
        self.personal = [root / 'journal/work-journal.json', root / 'activities/work.txt',
                         root / 'notes/note.md', self.claude / 'plugins/data/quality-gates@tomwangowa/saved.txt']
        for file in self.personal:
            file.parent.mkdir(parents=True, exist_ok=True)
            file.write_text('preserve fixture data')

    @property
    def mutations(self):
        return [a for a in self.calls if a[1:3] == ('plugin', 'uninstall')]

    def __call__(self, argv):
        self.calls.append(argv)
        if argv[0] == 'codex':
            return subprocess.CompletedProcess(argv, 1, '', '')
        rows = json.loads(self.registry.read_text())
        if argv[1:] == ('--version',):
            data = VERSION
            return subprocess.CompletedProcess(argv, 0, data, '')
        if argv[1:] == ('plugin', 'marketplace', 'list', '--json'):
            data = [dict(name='tomwangowa', source='github', repo='tomwangowa/agent-skills', installLocation=str(self.root / 'market'))]
        elif argv[1:] == ('plugin', 'list', '--json'):
            data = rows
        elif argv[1:3] == ('plugin', 'uninstall'):
            if argv[4:] != ('--scope','user','--keep-data','--json'):
                raise AssertionError('Removal changed scope or data retention: '+repr(argv))
            if self.mode == 'fail-first' and argv[3] == 'quality-gates@tomwangowa':
                return subprocess.CompletedProcess(argv, 1, '{"message":"Permission denied"}', '')
            if self.mode != 'lie':
                removed = [r for r in rows if r['id'] == argv[3] and r['scope'] == 'user']
                kept = [r for r in rows if r not in removed]
                self.registry.write_text(json.dumps(kept))
                for row in removed:
                    if not any(k['installPath'] == row['installPath'] for k in kept):
                        shutil.rmtree(row['installPath'])
            if self.mode == 'cancel-after-write':
                raise KeyboardInterrupt()
            data = dict(command='uninstall', outcome='ok', plugin=argv[3], pluginId=argv[3], scope='user', keptData=True,
                        message='Successfully uninstalled plugin')
        else:
            raise AssertionError('Unexpected native command: '+repr(argv))
        return subprocess.CompletedProcess(argv, 0, json.dumps(data), '')


class RemovalUITests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name).resolve()
        self.catalog = tuple(PluginSpec('claude', name, 'tomwangowa', SOURCE, '0.2.0')
                             for name in ('quality-gates','technical-decisions'))
        self.output = Terminal()

    def api(self):
        self.assertIsNotNone(importlib.util.find_spec('agent_skills_installer.removal_ui'),
                             'Separate removal UI is not implemented')
        return importlib.import_module('agent_skills_installer.removal_ui')

    def run_ui(self, answers, native=None, selector=None, before_answer=None):
        native = native or RemovalCLI(self.root)
        responses = iter(answers)
        prompts = []
        def answer(prompt):
            prompts.append(prompt)
            if before_answer:
                before_answer(prompt, native)
            return next(responses)
        with patch.dict('os.environ', {'CLAUDE_CONFIG_DIR':str(native.claude)}):
            code = self.api().run_removal(self.catalog, answer, self.output, native, package_selector=selector)
        return code, native, prompts

    def test_empty_selection_is_safe_default(self):
        code, native, prompts = self.run_ui(['1',''])
        self.assertEqual(code, 0)
        self.assertEqual(native.mutations, [])
        self.assertFalse(any('Approve' in p for p in prompts))

    def test_actual_removal_preserves_project_package_journal_notes_and_plugin_data(self):
        native = RemovalCLI(self.root)
        before = {p:p.read_bytes() for p in native.personal}
        project_root = Path(json.loads(native.registry.read_text())[0]['installPath'])
        code, native, prompts = self.run_ui(['1','1','y'], native)
        self.assertEqual(code, 0, self.output.getvalue())
        rows = json.loads(native.registry.read_text())
        self.assertFalse(any(r['id']=='quality-gates@tomwangowa' and r['scope']=='user' for r in rows))
        self.assertTrue(any(r['id']=='quality-gates@tomwangowa' and r['scope']=='project' for r in rows))
        self.assertEqual((project_root / 'skill.txt').read_text(), 'content: quality-gates')
        self.assertEqual({p:p.read_bytes() for p in native.personal}, before)
        self.assertEqual(len(native.mutations), 1)
        self.assertIn('removed:', self.output.getvalue())
        self.assertNotIn('Configure', ''.join(prompts))
        self.assertFalse(any('install' in a or 'add' in a or 'update' in a for a in native.calls))

    def test_selector_receives_only_installed_options_with_empty_defaults(self):
        def selector(options, defaults, output):
            self.assertEqual(defaults, frozenset())
            self.assertEqual({o.plugin.name for o in options}, {'quality-gates','technical-decisions'})
            return frozenset()
        code, native, _ = self.run_ui(['1'], selector=selector)
        self.assertEqual(code, 0)
        self.assertEqual(native.mutations, [])

    def test_decline_and_cancel_never_execute_uninstall(self):
        for choice in ('n','q'):
            with self.subTest(choice=choice), tempfile.TemporaryDirectory() as tmp:
                native = RemovalCLI(Path(tmp).resolve())
                code, native, _ = self.run_ui(['1','1',choice], native)
                self.assertEqual(code, 130)
                self.assertEqual(native.mutations, [])

    def test_partial_failure_does_not_retry_or_undo_other_success(self):
        native = RemovalCLI(self.root, 'fail-first')
        code, native, _ = self.run_ui(['1','1,2','y'], native)
        self.assertEqual(code, 1)
        self.assertEqual(len(native.mutations), 2)
        rows = json.loads(native.registry.read_text())
        self.assertTrue(any(r['id']=='quality-gates@tomwangowa' and r['scope']=='user' for r in rows))
        self.assertFalse(any(r['id']=='technical-decisions@tomwangowa' for r in rows))
        self.assertIn('Permission denied', self.output.getvalue())
        self.assertIn('\n\ntechnical-decisions', self.output.getvalue())

    def test_misleading_native_success_is_unverified(self):
        code, native, _ = self.run_ui(['1','1','y'], RemovalCLI(self.root, 'lie'))
        self.assertEqual(code, 1)
        self.assertEqual(len(native.mutations), 1)
        self.assertIn('unverified:', self.output.getvalue())

    def test_interrupt_after_a_write_stops_remaining_removals(self):
        code, native, _ = self.run_ui(['1','1,2','y'], RemovalCLI(self.root, 'cancel-after-write'))
        self.assertEqual(code, 130)
        self.assertEqual(len(native.mutations), 1)
        self.assertTrue(any(r['id']=='technical-decisions@tomwangowa' for r in json.loads(native.registry.read_text())))
        self.assertIn('unverified:', self.output.getvalue())

    def test_state_changed_after_preview_is_kept_without_uninstall(self):
        def change(prompt, native):
            if 'Approve removal' in prompt:
                rows = json.loads(native.registry.read_text())
                rows[0]['enabled'] = False
                native.registry.write_text(json.dumps(rows))
        code, native, _ = self.run_ui(['1','1','y'], before_answer=change)
        self.assertEqual(code, 1)
        self.assertEqual(native.mutations, [])

    def test_mode_picker_default_is_install_and_remove_requires_its_own_choice(self):
        for response, expected in [('', 'install'), ('1','install'), ('2','remove'), ('q',None)]:
            self.assertEqual(self.api().choose_operation(lambda _: response, Terminal()), expected)

    def test_codex_ui_warns_about_shared_cache_and_runs_qualified_removal(self):
        calls = []
        codex_home = self.root / 'codex'
        cache_root = codex_home / 'plugins/cache/tomwangowa/quality-gates'
        (cache_root / '0.2.0').mkdir(parents=True)
        (cache_root / '0.2.0/plugin.json').write_text('{}')
        removed = False
        def native(argv):
            nonlocal removed
            calls.append(argv)
            if argv[0] == 'claude':
                return subprocess.CompletedProcess(argv, 1, '', '')
            if argv[1:] == ('--version',):
                return subprocess.CompletedProcess(argv, 0, 'codex-cli 0.166.0', '')
            if argv[1:] == ('plugin','remove','--help'):
                help_text = 'Usage: codex plugin remove [OPTIONS] <PLUGIN[@MARKETPLACE]>\n      --json'
                return subprocess.CompletedProcess(argv, 0, help_text, '')
            if argv[1:] == ('plugin','marketplace','list','--json'):
                data = {'marketplaces':[{'name':'tomwangowa','root':str(self.root/'market'),
                                         'marketplaceSource':{'sourceType':'git','source':SOURCE}}]}
            elif argv[1:] == ('plugin','list','--marketplace','tomwangowa','--json'):
                installed = [] if removed else [{'pluginId':'quality-gates@tomwangowa','name':'quality-gates','marketplaceName':'tomwangowa',
                                                 'installed':True,'enabled':True,'version':'0.2.0','marketplaceSource':{'source':SOURCE}}]
                data = {'installed':installed, 'available':[]}
            elif argv == ('codex','plugin','remove','quality-gates@tomwangowa','--json'):
                removed = True
                shutil.rmtree(cache_root)
                data = {'pluginId':'quality-gates@tomwangowa','name':'quality-gates','marketplaceName':'tomwangowa'}
            else:
                raise AssertionError('Unexpected Codex command: '+repr(argv))
            return subprocess.CompletedProcess(argv, 0, json.dumps(data), '')
        catalog = (replace(self.catalog[0], host='codex'),)
        answers = iter(('1', '1', 'y'))
        with patch.dict('os.environ', {'CODEX_HOME':str(codex_home)}):
            code = self.api().run_removal(catalog, lambda _: next(answers), self.output, native)
        self.assertEqual(code, 0, self.output.getvalue())
        self.assertIn('shared cache', self.output.getvalue())
        self.assertIn('Project configs remain', self.output.getvalue())
        self.assertEqual(calls.count(('codex','plugin','remove','quality-gates@tomwangowa','--json')), 1)
