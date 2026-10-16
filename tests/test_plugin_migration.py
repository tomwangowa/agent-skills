"""Confirmed, bounded configuration edits with stale-preview rejection and recovery."""
import copy
import json
import tempfile
import os
import subprocess
import unittest
from pathlib import Path
from unittest.mock import patch

from runtime.agent_skills_runtime.migration import plan_migration, apply_migration, restore_migration


class MigrationTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory(); self.addCleanup(self.tmp.cleanup)
        self.root = Path(self.tmp.name).resolve()
        self.backup = self.root / 'backups'
        self.settings = self.root / 'settings.json'
        self.settings.write_text(json.dumps({'model':'keep', 'hooks':{'SessionStart':[{ 'matcher':'startup',
            'hooks':[{'type':'command','command':'python3 /fixture/old-skills/session-preferences/scripts/session_start_hook.py'},
                     {'type':'command','command':'keep-other-hook'}]}]},
            'mcpServers':{'skills-query':{'command':'npx','args':['tsx','/fixture/old-skills/skills-query-server/src/index.ts']},
                          'other':{'command':'keep-server'}}}, indent=4)+'\n')
        self.existing={'files':[{'path':str(self.settings),'format':'json','legacy_roots':['/fixture/old-skills']}],
                       'replacement_verified':True}

    def plan(self):
        return plan_migration(self.existing, ['session-preferences','work-journal'])

    def test_preview_is_complete_and_unconfirmed_has_no_writes(self):
        before=self.settings.read_bytes(); plan=self.plan()
        self.assertFalse(plan['confirmed']); self.assertEqual(len(plan['operations']),1)
        operation=plan['operations'][0]
        self.assertEqual(operation['path'],str(self.settings)); self.assertEqual(operation['action'],'replace')
        self.assertEqual(len(operation['changes']),2); self.assertTrue(operation['before_hash'])
        self.assertIn('backup',operation)
        with self.assertRaises(PermissionError): apply_migration(plan,self.backup)
        self.assertFalse(self.backup.exists()); self.assertEqual(self.settings.read_bytes(),before)

    def test_apply_preserves_unrelated_settings_user_skills_and_data_and_restore_is_exact(self):
        activity=self.root/'activities/record.json'; activity.parent.mkdir(); activity.write_text('Existing activity')
        skill=self.root/'user-skills/custom/SKILL.md'; skill.parent.mkdir(parents=True); skill.write_text('Custom skill')
        before=self.settings.read_bytes(); self.settings.chmod(0o640)
        plan=self.plan(); plan['confirmed']=True
        manifest=apply_migration(plan,self.backup)
        data=json.loads(self.settings.read_text())
        self.assertEqual(data['model'],'keep'); self.assertEqual(data['mcpServers'],{'other':{'command':'keep-server'}})
        self.assertEqual(data['hooks']['SessionStart'][0]['hooks'],[{'type':'command','command':'keep-other-hook'}])
        self.assertEqual(activity.read_text(),'Existing activity'); self.assertEqual(skill.read_text(),'Custom skill')
        restore_migration(manifest)
        self.assertEqual(self.settings.read_bytes(),before); self.assertEqual(self.settings.stat().st_mode&0o777,0o640)

    def test_stale_preview_tampered_plan_and_unverified_replacement_rejected(self):
        plan=self.plan(); plan['confirmed']=True; self.settings.write_text(self.settings.read_text()+' ')
        with self.assertRaises(ValueError): apply_migration(plan,self.backup)
        self.assertFalse(self.backup.exists())
        plan=self.plan(); plan['confirmed']=True; plan['operations'][0]['after']='tampered'
        with self.assertRaises(ValueError): apply_migration(plan,self.backup)
        self.existing['replacement_verified']=False; plan=self.plan(); plan['confirmed']=True
        with self.assertRaises(PermissionError): apply_migration(plan,self.backup)

    def test_restore_refuses_new_edits_before_restoring_any_file(self):
        plan=self.plan(); plan['confirmed']=True; manifest=apply_migration(plan,self.backup)
        self.settings.write_text('New user edit')
        with self.assertRaises(ValueError): restore_migration(manifest)
        self.assertEqual(self.settings.read_text(),'New user edit')

    def test_restore_recreates_deleted_target_with_original_bytes_and_mode(self):
        before = self.settings.read_bytes(); self.settings.chmod(0o640)
        plan = self.plan(); plan['confirmed'] = True
        manifest = apply_migration(plan, self.backup)
        self.settings.unlink()
        restore_migration(manifest)
        self.assertEqual(self.settings.read_bytes(), before)
        self.assertEqual(self.settings.stat().st_mode & 0o777, 0o640)

    def test_backup_snapshot_change_is_rejected_before_any_target_write(self):
        before = self.settings.read_bytes(); plan = self.plan(); plan['confirmed'] = True
        original = Path.read_bytes; reads = 0
        def changing_read(path):
            nonlocal reads
            if path == self.settings:
                reads += 1
                if reads == 3:
                    return b'Concurrent snapshot content'
            return original(path)
        with patch.object(Path, 'read_bytes', changing_read), self.assertRaises(ValueError):
            apply_migration(plan, self.backup)
        self.assertEqual(self.settings.read_bytes(), before)

    def test_only_selected_components_and_exact_legacy_paths_are_removed(self):
        plan=plan_migration(self.existing,['work-journal']); plan['confirmed']=True
        apply_migration(plan,self.backup)
        self.assertIn('session-preferences',self.settings.read_text())
        unrelated=self.root/'unrelated.json'; unrelated.write_text(json.dumps({'mcpServers':{'skills-query':{
            'command':'node','args':['/another-provider/skills-query-server/src/index.ts']}}}))
        existing={'files':[{'path':str(unrelated),'format':'json','legacy_roots':['/fixture/old-skills']}]}
        self.assertEqual(plan_migration(existing,['work-journal'])['operations'],[])

    def test_parent_traversal_paths_are_not_treated_as_legacy_entries(self):
        config = self.root / 'escaped.json'
        config.write_text(json.dumps({
            'hooks': {'SessionStart': [{'hooks': [{
                'type': 'command',
                'command': 'python3 /fixture/old-skills/session-preferences/../../other/session_start_hook.py',
            }]}]},
            'mcpServers': {'skills-query': {
                'command': 'node',
                'args': ['/fixture/old-skills/skills-query-server/../../other/index.js'],
            }},
        }))
        existing = {'files': [{
            'path': str(config),
            'format': 'json',
            'legacy_roots': ['/fixture/old-skills'],
        }]}

        plan = plan_migration(existing, ['session-preferences', 'work-journal'])

        self.assertEqual(plan['operations'], [])

    def test_normalized_paths_inside_legacy_root_are_still_recognized(self):
        config = self.root / 'normalized.json'
        config.write_text(json.dumps({
            'hooks': {'SessionStart': [{'hooks': [{
                'type': 'command',
                'command': 'python3 /fixture/old-skills/session-preferences/scripts/temporary/../session_start_hook.py',
            }]}]},
        }))
        existing = {'files': [{
            'path': str(config),
            'format': 'json',
            'legacy_roots': ['/fixture/old-skills'],
        }]}

        plan = plan_migration(existing, ['session-preferences'])

        self.assertEqual(len(plan['operations']), 1)
        self.assertEqual(plan['operations'][0]['changes'], [{
            'component': 'session-preferences',
            'selector': 'hooks.SessionStart',
            'action': 'remove_entry',
        }])

    def test_toml_and_explicit_routing_changes_keep_other_content(self):
        config=self.root/'config.toml'
        config.write_text('model = "keep"\n# retained\n[mcp_servers.skills-query]\ncommand="npx"\n'
                          'args=["tsx","/fixture/old-skills/skills-query-server/src/index.ts"]\n'
                          '[mcp_servers.skills-query.env]\nFIXTURE="value"\n[mcp_servers.other]\ncommand="keep"\n')
        routing=self.root/'AGENTS.md'; routing.write_text('Keep this.\nOld exact routing.\nKeep this too.\n')
        before={p:p.read_bytes() for p in [config,routing]}
        existing={'replacement_verified':True,'files':[{'path':str(config),'format':'toml','legacy_roots':['/fixture/old-skills']},
             {'path':str(routing),'format':'routing','replacements':[{'package':'work-journal',
                  'before':'Old exact routing.','after':'New reviewed routing.'}]}]}
        plan=plan_migration(existing,['work-journal']); self.assertEqual(len(plan['operations']),2)
        plan['confirmed']=True; manifest=apply_migration(plan,self.backup)
        self.assertEqual(config.read_text(),'model = "keep"\n# retained\n[mcp_servers.other]\ncommand="keep"\n')
        self.assertEqual(routing.read_text(),'Keep this.\nNew reviewed routing.\nKeep this too.\n')
        restore_migration(manifest)
        self.assertTrue(all(p.read_bytes()==text for p,text in before.items()))

    def test_symlink_config_backup_and_changed_backup_are_rejected(self):
        link=self.root/'link.json'; link.symlink_to(self.settings)
        with self.assertRaises(ValueError): plan_migration({'files':[{'path':str(link),'format':'json'}]},['work-journal'])
        backup_link=self.root/'backup-link'; backup_link.symlink_to(self.root,target_is_directory=True)
        plan=self.plan(); plan['confirmed']=True
        with self.assertRaises(ValueError): apply_migration(plan,backup_link)
        manifest=apply_migration(plan,self.backup)
        entry=json.loads(manifest.read_text())['operations'][0]
        (manifest.parent/entry['backup']).write_text('Altered backup')
        current=self.settings.read_bytes()
        with self.assertRaises(ValueError): restore_migration(manifest)
        self.assertEqual(self.settings.read_bytes(),current)

    def test_second_write_failure_rolls_back_first_file(self):
        another=self.root/'another.json'; another.write_bytes(self.settings.read_bytes())
        self.existing['files'].append({'path':str(another),'format':'json','legacy_roots':['/fixture/old-skills']})
        before={p:p.read_bytes() for p in [self.settings,another]}; plan=self.plan(); plan['confirmed']=True
        from runtime.agent_skills_runtime import migration
        original=migration._replace
        def fail_once(path, content, mode):
            if path==another and content!=before[another]: raise OSError('Fixture write failure')
            return original(path,content,mode)
        with patch.object(migration,'_replace',side_effect=fail_once), self.assertRaises(OSError):
            apply_migration(plan,self.backup)
        self.assertTrue(all(p.read_bytes()==data for p,data in before.items()))

    def test_concurrent_second_file_edit_preserved_and_first_file_rolled_back(self):
        another=self.root/'another.json'; another.write_bytes(self.settings.read_bytes())
        self.existing['files'].append({'path':str(another),'format':'json','legacy_roots':['/fixture/old-skills']})
        before=self.settings.read_bytes(); plan=self.plan(); plan['confirmed']=True
        from runtime.agent_skills_runtime import migration
        original=migration._replace
        def concurrent(path,content,mode):
            result=original(path,content,mode)
            if path==self.settings and content!=before: another.write_text('Concurrent user edit')
            return result
        with patch.object(migration,'_replace',side_effect=concurrent), self.assertRaises(ValueError):
            apply_migration(plan,self.backup)
        self.assertEqual(self.settings.read_bytes(),before)
        self.assertEqual(another.read_text(),'Concurrent user edit')

    def test_plugin_cache_targets_and_permission_changes_are_rejected(self):
        cache=self.root/'plugin'; (cache/'.codex-plugin').mkdir(parents=True)
        (cache/'.codex-plugin/plugin.json').write_text('{}')
        target=cache/'settings.json'; target.write_bytes(self.settings.read_bytes())
        with self.assertRaises(ValueError):
            plan_migration({'files':[{'path':str(target),'format':'json'}]},['work-journal'])
        plan=self.plan(); plan['confirmed']=True; self.settings.chmod(0o600)
        if plan['operations'][0]['mode']==0o600: self.settings.chmod(0o640)
        with self.assertRaises(ValueError): apply_migration(plan,self.backup)

    def test_real_cli_requires_the_exact_preview_hash(self):
        from runtime.agent_skills_runtime import migration
        inventory=self.root/'inventory.json'; inventory.write_text(json.dumps(self.existing))
        plan_path=self.root/'plan.json'
        env=dict(os.environ); env['PYTHONPATH']=str(Path(migration.__file__).parents[1])
        command=['python3','-m','agent_skills_runtime.migration']
        result=subprocess.run(command+['preview','--inventory',str(inventory),'--packages','work-journal',
                               '--output',str(plan_path)],env=env,capture_output=True,text=True)
        self.assertEqual(result.returncode,0,result.stderr)
        plan=json.loads(plan_path.read_text()); self.assertEqual(plan_path.stat().st_mode&0o777,0o600)
        before=self.settings.read_bytes()
        result=subprocess.run(command+['apply','--plan',str(plan_path),'--confirm','wrong',
                               '--backup-root',str(self.backup)],env=env,capture_output=True,text=True)
        self.assertNotEqual(result.returncode,0); self.assertEqual(self.settings.read_bytes(),before)
        result=subprocess.run(command+['apply','--plan',str(plan_path),'--confirm',plan['preview_hash'],
                               '--backup-root',str(self.backup)],env=env,capture_output=True,text=True)
        self.assertEqual(result.returncode,0,result.stderr)
        manifest=json.loads(result.stdout)['manifest']
        result=subprocess.run(command+['restore','--manifest',manifest],env=env,capture_output=True,text=True)
        self.assertEqual(result.returncode,0,result.stderr); self.assertEqual(self.settings.read_bytes(),before)


if __name__=='__main__': unittest.main()
