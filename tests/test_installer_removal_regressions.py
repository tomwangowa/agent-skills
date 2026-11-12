"""Review regressions: physical profile changes and unrelated local plugins."""
from dataclasses import replace
import json
import os
from pathlib import Path
import shutil
import subprocess
import sys
import tempfile
import unittest
from unittest.mock import patch

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / 'runtime'))
from agent_skills_installer.models import InstalledPlugin, Inventory, PluginSpec
from agent_skills_installer.hosts import read_inventory
from agent_skills_installer.removal import make_removal_plan, removal_options, recheck_removal, verify_removal
from agent_skills_installer.removal_ui import run_removal
from test_installer_removal import RemovalCLI, Terminal

SOURCE = 'https://github.com/tomwangowa/agent-skills.git'
VERSION = '2.1.322 (Claude Code)'


class ProfileIdentityTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name).resolve()
        self.profile = self.root / 'profile-a'
        self.config = self.profile / 'claude'
        target = self.config / 'plugins/cache/tomwangowa/quality-gates/0.2.0'
        (target / '.claude-plugin').mkdir(parents=True)
        (target / '.claude-plugin/plugin.json').write_text('{"name":"quality-gates","version":"0.2.0"}')
        (target / 'payload.txt').write_text('identical package bytes in both profiles')
        self.alias = self.root / 'current'
        self.alias.symlink_to(self.profile, target_is_directory=True)
        self.config_alias = self.alias / 'claude'
        row = InstalledPlugin('claude','quality-gates','tomwangowa',SOURCE,'0.2.0',
                              str(self.config_alias / target.relative_to(self.config)), True, 'user')
        self.inv = Inventory('claude', VERSION, (row,))
        self.spec = PluginSpec('claude','quality-gates','tomwangowa',SOURCE,'0.2.0')
        options = removal_options((self.spec,), (self.inv,), self.config_alias)
        self.plan = make_removal_plan(options, frozenset(o.key for o in options if not o.reason))
        self.assertEqual(len(self.plan.actions), 1)

    def switch_profile(self):
        other = self.root / 'profile-b'
        shutil.copytree(self.profile, other)
        self.alias.unlink()
        self.alias.symlink_to(other, target_is_directory=True)

    def test_stable_ancestor_link_is_usable_without_relaxing_cache_link_checks(self):
        self.assertTrue(recheck_removal(self.plan.actions[0], self.inv, self.config_alias))

    def test_profile_link_changed_before_recheck_rejects_same_looking_records(self):
        self.switch_profile()
        self.assertFalse(recheck_removal(self.plan.actions[0], self.inv, self.config_alias))

    def test_config_directory_replaced_at_same_path_invalidates_approval(self):
        previous = self.profile / 'previous'
        self.config.rename(previous)
        shutil.copytree(previous, self.config)
        self.assertFalse(recheck_removal(self.plan.actions[0], self.inv, self.config_alias))

    def test_profile_switch_cannot_turn_target_absence_into_verified_success(self):
        self.switch_profile()
        action = self.plan.actions[0]
        result = subprocess.CompletedProcess(action.argv, 0, json.dumps({
            'command':'uninstall','outcome':'ok','pluginId':'quality-gates@tomwangowa','scope':'user','keptData':True}), '')
        self.assertFalse(verify_removal(action, result, self.inv, replace(self.inv, plugins=())))

    def test_profile_switch_at_confirmation_executes_no_uninstall(self):
        answers = iter(['1','1','y'])
        mutations = []
        def answer(prompt):
            if 'Approve removal' in prompt:
                self.switch_profile()
            return next(answers)
        def runner(argv):
            if argv[0]=='codex':
                return subprocess.CompletedProcess(argv,1,'','')
            if argv[1:]==('--version',):
                return subprocess.CompletedProcess(argv,0,VERSION,'')
            if argv[1:]==('plugin','marketplace','list','--json'):
                value=[{'name':'tomwangowa','source':'github','repo':'tomwangowa/agent-skills','installLocation':str(self.root/'market')}]
            elif argv[1:]==('plugin','list','--json'):
                value=[{'id':'quality-gates@tomwangowa','version':'0.2.0','scope':'user','enabled':True,'installPath':self.inv.plugins[0].root}]
            else:
                mutations.append(argv)
                return subprocess.CompletedProcess(argv,1,'{"message":"unexpected mutation"}','')
            return subprocess.CompletedProcess(argv,0,json.dumps(value),'')
        with patch.dict(os.environ, {'CLAUDE_CONFIG_DIR':str(self.config_alias)}):
            code=run_removal((self.spec,),answer,Terminal(),runner)
        self.assertEqual(code,1)
        self.assertEqual(mutations,[])


class UnknownSourceTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name).resolve()
        self.native = RemovalCLI(self.root)
        self.foreign = {'id':'local-helper@local-tools','version':'1.0.0','enabled':True,'scope':'user',
                        'installPath':str(self.root/'local-plugin')}
        (self.root/'local-plugin').mkdir()
        (self.root/'local-plugin/personal.txt').write_text('keep local plugin')
        self.spec = PluginSpec('claude','quality-gates','tomwangowa',SOURCE,'0.2.0')

    def runner(self, argv):
        result = self.native(argv)
        if result.returncode or argv[0]!='claude' or argv[1:]==('--version',):
            return result
        data = json.loads(result.stdout)
        if argv[1:]==('plugin','marketplace','list','--json'):
            data.append({'name':'local-tools','source':'directory','path':str(self.root/'local-market'),
                         'installLocation':str(self.root/'local-market')})
        elif argv[1:]==('plugin','list','--json'):
            data.append(self.foreign)
        return subprocess.CompletedProcess(argv,result.returncode,json.dumps(data),result.stderr)

    def test_unrelated_local_source_remains_present_and_does_not_poison_inventory(self):
        inv = read_inventory('claude', self.runner)
        self.assertFalse(inv.errors)
        local = next(p for p in inv.plugins if p.name=='local-helper')
        self.assertIsNone(local.source)
        self.assertEqual(local.root,self.foreign['installPath'])
        options = removal_options((self.spec,), (inv,), self.native.claude)
        self.assertTrue(any(not option.reason for option in options))

    def test_valid_target_is_removed_while_unrelated_local_plugin_is_preserved(self):
        answers=iter(['1','1','y'])
        with patch.dict(os.environ, {'CLAUDE_CONFIG_DIR':str(self.native.claude)}):
            code=run_removal((self.spec,),lambda _:next(answers),Terminal(),self.runner)
        self.assertEqual(code,0)
        self.assertEqual(len(self.native.mutations),1)
        self.assertEqual((self.root/'local-plugin/personal.txt').read_text(),'keep local plugin')
        inv=read_inventory('claude',self.runner)
        self.assertTrue(any(p.name=='local-helper' for p in inv.plugins))
        self.assertFalse(any(p.name=='quality-gates' and p.scope=='user' for p in inv.plugins))

    def test_same_name_unknown_source_is_kept_while_identified_provider_remains_eligible(self):
        self.foreign['id']='quality-gates@local-tools'
        inv=read_inventory('claude',self.runner)
        self.assertFalse(inv.errors)
        options=removal_options((self.spec,), (inv,), self.native.claude)
        self.assertEqual(len(options),2)
        self.assertTrue(next(o for o in options if o.plugin.marketplace=='local-tools').reason)
        self.assertFalse(next(o for o in options if o.plugin.marketplace=='tomwangowa').reason)

    def test_missing_required_fields_still_block_all_mutations(self):
        del self.foreign['version']
        inv=read_inventory('claude',self.runner)
        self.assertTrue(inv.errors)
        answers=iter(['1'])
        with patch.dict(os.environ, {'CLAUDE_CONFIG_DIR':str(self.native.claude)}):
            code=run_removal((self.spec,),lambda _:next(answers),Terminal(),self.runner)
        self.assertEqual(code,1)
        self.assertEqual(self.native.mutations,[])
