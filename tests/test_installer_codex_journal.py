"""A new Codex journal must be verified before creating optional-note settings."""
import json
import os
import shutil
import subprocess
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch
from agent_skills_installer.catalog import build_catalog
from installer_ui_fixtures import run_with_fixture_hosts as run
from test_installer_codex_receipts import CodexCLI, Terminal, ROOT


class CodexJournalCLI(CodexCLI):
    def __init__(self, root, spec):
        self.root, self.spec, self.change, self.version = root, spec, None, 'codex-cli 0.167.0'
        self.market, self.home = root/'market', root/'codex-home'
        self.cache_version = spec.version
        self.installed, self.calls, self.code = [], [], 0
        self.target = self.home/'plugins/cache/tomwangowa/work-journal'/self.cache_version
        shutil.copytree(ROOT/'plugins/codex/work-journal', self.market/'plugins/codex/work-journal')

    def row(self):
        data = json.loads((ROOT/'tests/fixtures/installer/observed-codex.json').read_text())['output']['installed'][0]
        data.update(pluginId='work-journal@tomwangowa', name='work-journal', version=self.cache_version)
        data['source']['path'] = str(self.market/'plugins/codex/work-journal')
        return data

    def __call__(self, argv):
        if argv[1:] == ('plugin','add','work-journal@tomwangowa','--json'):
            self.calls.append(argv)
            shutil.copytree(self.market/'plugins/codex/work-journal', self.target)
            self.installed = [self.row()]
            data = dict(pluginId='work-journal@tomwangowa', name='work-journal', marketplaceName='tomwangowa',
                        version=self.cache_version, installedPath=str(self.target), authPolicy='ON_INSTALL')
            return subprocess.CompletedProcess(argv,0,json.dumps(data),'')
        return super().__call__(argv)


class CodexJournalTest(unittest.TestCase):
    def test_new_install_accepts_empty_notes_and_creates_default_in_fixture(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp).resolve()
            specs = build_catalog(ROOT, json.loads((ROOT/'installer/providers.json').read_text()),
                                  json.loads((ROOT/'installer/dependencies.json').read_text()))
            spec = next(p for p in specs if (p.host,p.name)==('codex','work-journal'))
            native = CodexJournalCLI(root,spec)
            answers = iter(['1','','','y','','','y'])
            out = Terminal()
            env = {'CODEX_HOME':str(native.home),'AGENT_SKILLS_CONFIG_DIR':str(root/'config'),
                   'CLAUDE_ACTIVITIES_DIR':''}
            with patch.dict(os.environ,env), patch('pathlib.Path.home',return_value=root/'home'), \
                 patch('agent_skills_installer.ui.detect_tools',side_effect=lambda cs:{c:True for c in cs}):
                code=run((spec,),lambda _:next(answers),out,native)
            self.assertEqual(code,0,out.getvalue())
            data=json.loads((root/'config/work-journal.json').read_text())
            self.assertEqual(data['sources']['notes']['paths'],[])
            self.assertEqual(data['sources']['activities'],str(root/'home/.agent-skills/activities'))
            self.assertEqual(len(native.mutations),1)
