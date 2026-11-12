"""Launcher tests run relocated files and observe calls, including refusal paths."""
import json
import os
import shutil
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / 'runtime'))
from agent_skills_installer.dependencies import render_bootstrap


class BootstrapTests(unittest.TestCase):
    def setUp(self):
        self.mapping = json.loads((ROOT / 'installer/dependencies.json').read_text())

    def rendered(self, platform):
        name = {'macos': 'install-macos.command', 'linux': 'install-linux.sh', 'windows': 'install-windows.ps1'}[platform]
        return render_bootstrap((ROOT / 'installer' / name).read_text(), platform, self.mapping)

    def test_rendered_bootstrap_mapping(self):
        for platform, package in [('macos', 'python@3.13'), ('linux', 'python3'), ('windows', 'Python.Python.3.13')]:
            rendered = self.rendered(platform)
            self.assertNotIn('@@', rendered)
            self.assertIn(package, rendered)
            if platform != 'windows':
                p = subprocess.run(['/bin/bash', '-n'], input=rendered, capture_output=True, text=True)
                self.assertEqual(p.returncode, 0, p.stderr)

    def test_bootstrap_prerequisite_paths(self):
        for platform in ('macos', 'linux'):
            with self.subTest(platform=platform), tempfile.TemporaryDirectory(prefix='installer 空白 ') as tmp:
                root = Path(tmp)
                script = root / 'launch.sh'
                script.write_text(self.rendered(platform))
                tools = root / 'bin'
                tools.mkdir()
                # Only the launcher dependencies are available on PATH.
                for tool in ('dirname',):
                    (tools / tool).symlink_to(shutil.which(tool))
                env = dict(os.environ, PATH=str(tools))
                result = subprocess.run(['/bin/bash', str(script)], cwd='/', env=env, text=True, capture_output=True)
                self.assertEqual(result.returncode, 1)
                self.assertIn('Claude Code or Codex', result.stdout)
                (tools / 'claude').write_text('#!/bin/sh\nexit 0\n')
                (tools / 'claude').chmod(0o755)
                result = subprocess.run(['/bin/bash', str(script)], cwd='/', env=env, text=True, capture_output=True)
                self.assertEqual(result.returncode, 1)
                self.assertIn('Python', result.stdout)
                python = tools / 'python3.13'
                python.write_text('#!/bin/sh\nexec ' + str(sys.executable) + ' "$@"\n')
                python.chmod(0o755)
                (root / 'install.py').write_text('import sys\nprint(repr(sys.argv[1:]))\n')
                result = subprocess.run(['/bin/bash', str(script), 'space 中文', '$(touch ignored)'], cwd='/', env=env, text=True, capture_output=True)
                self.assertEqual(result.returncode, 0, result.stderr)
                self.assertIn("'space 中文', '$(touch ignored)'", result.stdout)

    @unittest.skipUnless(shutil.which('pwsh'), 'Native PowerShell is unavailable; Windows launcher is NOT VERIFIED')
    def test_python_probe_does_not_invoke_download_shim(self):
        # A host-less launch must return before invoking any Python alias.
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            sentinel = root / 'downloaded'
            for name in ('python', 'py', 'python3'):
                tool = root / name
                tool.write_text(f'#!/bin/sh\ntouch "{sentinel}"\nexit 1\n')
                tool.chmod(0o755)
            script = root / 'install.ps1'
            script.write_text(self.rendered('windows'))
            p = subprocess.run([shutil.which('pwsh'), '-NoProfile', '-File', str(script)],
                               env=dict(os.environ, PATH=str(root)), capture_output=True, text=True)
            self.assertNotEqual(p.returncode, 0)
            self.assertFalse(sentinel.exists())

    def test_python_install_decline_failure_and_interrupt(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            tools = root / 'bin'
            tools.mkdir()
            (tools / 'dirname').symlink_to(shutil.which('dirname'))
            (tools / 'claude').write_text('#!/bin/sh\nexit 0\n')
            (tools / 'claude').chmod(0o755)
            sentinel = root / 'installed'
            script = root / 'launch.sh'
            script.write_text(self.rendered('macos'))
            manager = tools / 'brew'
            for answer, exit_code, expected in [('n', 0, 130), ('y', 1, 1), ('y', 130, 130)]:
                manager.write_text(f'#!/bin/sh\necho attempted > "{sentinel}"\nexit {exit_code}\n')
                manager.chmod(0o755)
                sentinel.unlink(missing_ok=True)
                result = subprocess.run(['/bin/bash', str(script)], input=answer + '\n',
                                        env=dict(os.environ, PATH=str(tools)), capture_output=True, text=True)
                self.assertEqual(result.returncode, expected, result.stdout + result.stderr)
                self.assertEqual(sentinel.exists(), answer == 'y')


if __name__ == '__main__':
    unittest.main()
