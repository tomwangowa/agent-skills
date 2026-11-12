"""Archives are deterministic, minimal, exclusive and runnable after relocation."""
import hashlib
import json
import os
import subprocess
import sys
import tempfile
import unittest
import zipfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from scripts.build_plugin_installer import build_bundle


class BundleTests(unittest.TestCase):
    def test_bundle_allowlist_and_provenance(self):
        with tempfile.TemporaryDirectory() as tmp:
            archive = build_bundle(ROOT, Path(tmp) / 'bundle.zip')
            with zipfile.ZipFile(archive) as z:
                names = z.namelist()
                self.assertTrue(all(n.startswith('agent-skills-installer/') for n in names))
                self.assertFalse(any(part in n.split('/') for n in names for part in ('tests', 'node_modules', '__pycache__')))
                self.assertFalse(any(n.endswith(('.pyc', 'work-journal.json', 'config.json')) for n in names))
                provenance = json.loads(z.read('agent-skills-installer/provenance.json'))
                self.assertRegex(provenance['source_commit'], r'^[a-f0-9]{40}$')
                for name, digest in provenance['files'].items():
                    self.assertEqual(hashlib.sha256(z.read('agent-skills-installer/' + name)).hexdigest(), digest)
                runtime = {n for n in names if '/runtime/agent_skills_runtime/' in n}
                self.assertEqual(len(runtime), 3)
                self.assertTrue(any(n.endswith('/setup.py') for n in runtime))

    def test_reproducible_bundle(self):
        with tempfile.TemporaryDirectory() as tmp:
            first = build_bundle(ROOT, Path(tmp) / 'first.zip')
            second = build_bundle(ROOT, Path(tmp) / 'second.zip')
            self.assertEqual(first.read_bytes(), second.read_bytes())

    def test_existing_output_not_replaced(self):
        with tempfile.TemporaryDirectory() as tmp:
            output = Path(tmp) / 'existing.zip'
            output.write_bytes(b'keep existing')
            with self.assertRaises(FileExistsError):
                build_bundle(ROOT, output)
            self.assertEqual(output.read_bytes(), b'keep existing')

    def test_relocated_help_uses_only_bundled_runtime(self):
        with tempfile.TemporaryDirectory(prefix='bundle 中文 ') as tmp:
            archive = build_bundle(ROOT, Path(tmp) / 'bundle.zip')
            for name in ('first unpack', '另一份'):
                location = Path(tmp) / name
                with zipfile.ZipFile(archive) as z:
                    z.extractall(location)
                entry = location / 'agent-skills-installer/install.py'
                result = subprocess.run([sys.executable, '-I', str(entry), '--help'], cwd='/',
                                        env=dict(os.environ, PYTHONPATH=''), capture_output=True, text=True)
                self.assertEqual(result.returncode, 0, result.stderr)
                self.assertIn('--catalog', result.stdout)
                self.assertNotIn('--yes', result.stdout)

    def test_bundled_cancel_and_partial_failure_with_fake_cli(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            archive = build_bundle(ROOT, root / 'bundle.zip')
            with zipfile.ZipFile(archive) as z:
                z.extractall(root)
            bundle = root / 'agent-skills-installer'
            tools = root / 'bin'
            tools.mkdir()
            log = root / 'calls.jsonl'
            fake = tools / 'claude'
            fake.write_text('#!' + sys.executable + '\n' + '''import json, os, sys
from pathlib import Path
a=sys.argv[1:]
with open(os.environ['FIXTURE_LOG'], 'a') as f: f.write(json.dumps(a)+'\\n')
if a==['--version']: print('2.1.319')
elif a[:3]==['plugin','marketplace','list']:
 print(json.dumps([{'name':'tomwangowa','source':'github','repo':'tomwangowa/agent-skills','installLocation':os.environ['FIXTURE_MARKET']}]))
elif a[:2]==['plugin','list']: print('[]')
elif a[:2]==['plugin','install']: sys.exit(1)
else: sys.exit(2)
''')
            fake.chmod(0o755)
            for name, target in [('python3', sys.executable), ('git', '/usr/bin/git'), ('bash', '/bin/bash')]:
                (tools / name).symlink_to(target)
            program = '''import io,sys
from pathlib import Path
sys.path.insert(0,sys.argv[1]+'/runtime')
from agent_skills_installer.catalog import load_catalog
from agent_skills_installer.ui import run,native_runner
class Terminal(io.StringIO):
 def isatty(self): return True
answers=iter(sys.argv[2:])
out=Terminal()
code=run(load_catalog(Path(sys.argv[1])/'catalog.json'),lambda _:next(answers),out,native_runner)
print(out.getvalue())
raise SystemExit(code)
'''
            env = dict(os.environ, PATH=str(tools), PYTHONPATH='', FIXTURE_LOG=str(log), FIXTURE_MARKET=str(ROOT))
            cancel = subprocess.run([sys.executable, '-I', '-c', program, str(bundle), '1', '1,3', '', 'q'], cwd='/', env=env, capture_output=True, text=True)
            self.assertEqual(cancel.returncode, 130, cancel.stdout + cancel.stderr)
            self.assertFalse(any(json.loads(line)[:2] == ['plugin', 'install'] for line in log.read_text().splitlines()))
            failed = subprocess.run([sys.executable, '-I', '-c', program, str(bundle), '1', '1,3', '', 'y'], cwd='/', env=env, capture_output=True, text=True)
            self.assertEqual(failed.returncode, 1, failed.stdout + failed.stderr)
            self.assertEqual(sum(json.loads(line)[:2] == ['plugin', 'install'] for line in log.read_text().splitlines()), 2)
            self.assertIn('failed:', failed.stdout)


if __name__ == '__main__':
    unittest.main()


class ProviderBundleTests(unittest.TestCase):
    def test_relocated_bundle_has_provider_runtime_and_acceptance(self):
        with tempfile.TemporaryDirectory(prefix='official bundle 中文 ') as tmp:
            root = Path(tmp)
            archive = build_bundle(ROOT, root / 'r4.zip')
            with zipfile.ZipFile(archive) as z:
                z.extractall(root / 'elsewhere')
            bundle = root / 'elsewhere/agent-skills-installer'
            program = '''import json,sys
from pathlib import Path
sys.path.insert(0,sys.argv[1]+'/runtime')
from agent_skills_installer.catalog import load_catalog
from agent_skills_installer.providers import parse_native_acceptance,target_accepted
from dataclasses import replace
root=Path(sys.argv[1])
specs=load_catalog(root/'catalog.json')
providers=[s for s in specs if s.provider]
assert [(s.host,s.marketplace,s.version) for s in providers]==[('claude','claude-plugins-official','7.0.0'),('codex','openai-curated','6.3.0')]
assert all(not s.default_selected and s.content_hash for s in providers)
records=parse_native_acceptance(json.loads((root/'provider-acceptance.json').read_text()))
assert len(records)==2
claude,codex=providers
assert target_accepted(claude,records,'2.1.322 (Claude Code)','macos','arm64')
assert target_accepted(replace(codex,marketplace='openai-api-curated'),records,'codex-cli 0.167.0','macos','arm64')
assert not target_accepted(codex,records,'codex-cli 0.167.0','macos','arm64')
assert not target_accepted(claude,records,'2.1.322 (Claude Code)','windows','arm64')
assert all((root/r.evidence_ref).is_file() for r in records)
print('schema2 providers imported; exact native capability records and evidence resolved')
'''
            result = subprocess.run((sys.executable, '-I', '-c', program, str(bundle)), cwd='/', env=dict(os.environ, PYTHONPATH=''), capture_output=True, text=True)
            self.assertEqual(result.returncode, 0, result.stdout+result.stderr)
            self.assertIn('exact native capability records and evidence resolved', result.stdout)
