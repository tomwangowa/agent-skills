"""Installed-copy updates preserve external data and identify changed hook inputs."""
import hashlib
import shutil
import tempfile
import unittest
from pathlib import Path

from runtime.agent_skills_runtime.migration import check_updates, check_hook_updates
from runtime.agent_skills_runtime.preferences import save_module_override

ROOT=Path(__file__).resolve().parents[1]


class UpdateTests(unittest.TestCase):
    def test_new_defaults_preserve_external_settings_and_personal_copy(self):
        with tempfile.TemporaryDirectory() as tmp:
            root=Path(tmp).resolve(); installed=root/'installed'; settings=root/'personal'; settings.mkdir()
            shutil.copytree(ROOT/'session-preferences',installed/'session-preferences')
            shutil.copytree(ROOT/'control-return',installed/'control-return')
            defaults=installed/'session-preferences/references'
            base=hashlib.sha256((defaults/'deai-voice.md').read_bytes()).hexdigest()
            save_module_override(settings,'deai-voice.md','Personal fixture rule',base,None)
            journal=settings/'work-journal.json'; journal.write_text('Existing settings bytes')
            snapshot={p:p.read_bytes() for p in settings.rglob('*') if p.is_file()}
            (defaults/'deai-voice.md').write_text('New package default')
            updates=check_updates(settings,defaults)
            self.assertTrue(any(u['status']=='default_changed' for u in updates))
            self.assertTrue(all(p.read_bytes()==data for p,data in snapshot.items()))

    def test_changed_hook_and_runtime_inputs_require_review_without_inventing_native_trust(self):
        with tempfile.TemporaryDirectory() as tmp:
            root=Path(tmp); before=root/'old'; after=root/'new'
            for p in [before,after]:
                (p/'hooks').mkdir(parents=True); (p/'hooks/hooks.json').write_text('{"fixture":"old"}')
                (p/'runtime').mkdir(); (p/'runtime/helper.py').write_text('old fixture')
            self.assertEqual(check_hook_updates(before,after),[])
            (after/'runtime/helper.py').write_text('new fixture')
            result=check_hook_updates(before,after)
            self.assertEqual(result[0]['status'],'review_required')
            self.assertIn('runtime/helper.py',result[0]['changed_resources'])
            self.assertEqual(result[0]['native_trust'],'not_verified')


if __name__=='__main__': unittest.main()
