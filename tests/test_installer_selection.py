"""Exercise compact package output and real keyboard selection without host access."""
import errno
import io
import json
import os
from pathlib import Path
import select
import signal
import struct
import subprocess
import sys
import tempfile
import time
import unittest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / 'runtime'))
from agent_skills_installer.catalog import build_catalog
from agent_skills_installer.ui import run


class Terminal(io.StringIO):
    def isatty(self):
        return True


class CompactSelectionTests(unittest.TestCase):
    def test_selection_lists_names_without_descriptions_or_source_details(self):
        catalog = build_catalog(ROOT, json.loads((ROOT / 'installer/providers.json').read_text()),
                                json.loads((ROOT / 'installer/dependencies.json').read_text()))
        output = Terminal()
        before_selection = []
        answers = iter(['1', 'q'])
        def answer(prompt):
            if prompt.startswith('Packages'):
                before_selection.append(output.getvalue())
            return next(answers)
        def native(argv):
            if argv[0] != 'claude':
                return subprocess.CompletedProcess(argv, 1, '', '')
            if argv[1:] == ('--version',):
                return subprocess.CompletedProcess(argv, 0, '2.1.322 (Claude Code)', '')
            if argv[1:] in (('plugin', 'list', '--json'), ('plugin', 'marketplace', 'list', '--json')):
                return subprocess.CompletedProcess(argv, 0, '[]', '')
            raise AssertionError('No mutation is permitted before selection.')
        self.assertEqual(run(catalog, answer, output, native), 130)
        menu = before_selection[0]
        self.assertIn('quality-gates', menu)
        self.assertIn('secure-ai-development-gate', menu)
        self.assertIn('superpowers (strongly recommended)', menu)
        self.assertNotIn('https://', menu)
        self.assertNotIn('pinned commit', menu)
        self.assertNotIn('Native inventory', menu)
        self.assertNotIn('0.2.0', menu)
        self.assertLess(len(menu.splitlines()), 40)

    def test_inventory_failure_is_reported_after_selection_and_never_installs(self):
        catalog = build_catalog(ROOT, json.loads((ROOT / 'installer/providers.json').read_text()),
                                json.loads((ROOT / 'installer/dependencies.json').read_text()))
        specs = tuple(p for p in catalog if p.host == 'claude' and p.name == 'quality-gates')
        output, calls = Terminal(), []
        def native(argv):
            calls.append(argv)
            if argv[0] != 'claude':
                return subprocess.CompletedProcess(argv, 1, '', '')
            if argv[1:] == ('--version',):
                return subprocess.CompletedProcess(argv, 0, '2.1.322 (Claude Code)', '')
            if argv[1:] == ('plugin', 'marketplace', 'list', '--json'):
                rows = [{'name': 'tomwangowa', 'source': 'github', 'repo': 'tomwangowa/agent-skills',
                         'installLocation': '/fixture/market'}]
            elif argv[1:] == ('plugin', 'list', '--json'):
                rows = [{'id': 'quality-gates@tomwangowa', 'version': '0.2.0',
                         'enabled': 'unknown', 'scope': 'user', 'installPath': '/fixture/installed'}]
            else:
                raise AssertionError('Inventory uncertainty must never permit a mutation.')
            return subprocess.CompletedProcess(argv, 0, json.dumps(rows), '')
        answers = iter(['1', '1', '', 'y'])
        def answer(prompt):
            if prompt.startswith('Packages'):
                self.assertNotIn('Incomplete plugin metadata', output.getvalue())
            return next(answers)
        self.assertEqual(run(specs, answer, output, native), 1)
        self.assertIn('Inventory unverified: Incomplete plugin metadata', output.getvalue())
        self.assertNotIn('installed:', output.getvalue())
        self.assertFalse(any(argv[1:3] in (('plugin', 'install'), ('plugin', 'update')) for argv in calls))


@unittest.skipIf(os.name == 'nt', 'POSIX PTY unavailable; native Windows console is NOT VERIFIED')
class KeyboardSelectionTests(unittest.TestCase):
    def setUp(self):
        import fcntl
        import termios
        self.termios = termios
        self.temp = tempfile.TemporaryDirectory(prefix='installer keyboard ')
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name)
        tools = self.root / 'bin'
        tools.mkdir()
        self.log = self.root / 'native.jsonl'
        fake = tools / 'claude'
        fake.write_text('#!' + sys.executable + '\n' + '''import json,os,sys
from pathlib import Path
args=sys.argv[1:]
with open(os.environ['FIXTURE_LOG'],'a') as stream:stream.write(json.dumps(args)+'\\n')
if args==['--version']:print('2.1.322 (Claude Code)')
elif args in [['plugin','list','--json'],['plugin','marketplace','list','--json']]:print('[]')
else:raise SystemExit('Unapproved fake host operation')
''')
        fake.chmod(0o755)
        catalog = build_catalog(ROOT, json.loads((ROOT / 'installer/providers.json').read_text()),
                                json.loads((ROOT / 'installer/dependencies.json').read_text()))
        from dataclasses import asdict
        (self.root / 'catalog.json').write_text(json.dumps({'schema_version': 2, 'plugins': [asdict(x) for x in catalog]}))
        self.master, self.slave = os.openpty()
        self.addCleanup(os.close, self.master)
        self.addCleanup(os.close, self.slave)
        fcntl.ioctl(self.slave, termios.TIOCSWINSZ, struct.pack('HHHH', 18, 80, 0, 0))
        self.mode_snapshot = self.root / 'mode-before-checkboxes.json'
        self.mode_after = self.root / 'mode-after-checkboxes.json'
        program = """import json,sys,termios
from pathlib import Path
sys.path.insert(0,sys.argv[1])
import agent_skills_installer.__main__ as entry
original=entry.select_packages
def observe(specs,defaults,output):
    mode=termios.tcgetattr(sys.stdin.fileno())
    mode[6]=[x.hex() if isinstance(x,bytes) else x for x in mode[6]]
    Path(sys.argv[3]).write_text(json.dumps(mode))
    try:
        return original(specs,defaults,output)
    finally:
        mode=termios.tcgetattr(sys.stdin.fileno())
        mode[6]=[x.hex() if isinstance(x,bytes) else x for x in mode[6]]
        Path(sys.argv[4]).write_text(json.dumps(mode))
entry.select_packages=observe
raise SystemExit(entry.main(['--catalog',sys.argv[2]]))
"""
        env = dict(os.environ, PATH=str(tools), HOME=str(self.root / 'home'),
                   CLAUDE_CONFIG_DIR=str(self.root / 'claude'), CODEX_HOME=str(self.root / 'codex'),
                   FIXTURE_LOG=str(self.log), TERM='xterm-256color')
        self.process = subprocess.Popen([sys.executable, '-I', '-c', program, str(ROOT / 'runtime'),
                                         str(self.root / 'catalog.json'), str(self.mode_snapshot), str(self.mode_after)], stdin=self.slave,
                                        stdout=self.slave, stderr=self.slave, env=env,
                                        cwd=self.root, start_new_session=True)
        self.addCleanup(self.stop)
        self.transcript = b''

    def stop(self):
        if self.process.poll() is None:
            os.killpg(self.process.pid, signal.SIGTERM)
            self.process.wait(timeout=5)

    def until(self, *needles, timeout=4):
        start = len(self.transcript)
        deadline = time.monotonic() + timeout
        while time.monotonic() < deadline:
            if any(needle in self.transcript[start:] for needle in needles):
                return self.transcript[start:]
            if select.select([self.master], [], [], .05)[0]:
                try:
                    data = os.read(self.master, 65536)
                except OSError as error:
                    if error.errno == errno.EIO:
                        break
                    raise
                if not data:
                    break
                self.transcript += data
            if self.process.poll() is not None:
                break
        return self.transcript[start:]

    def enter_packages(self):
        self.assertIn(b'Operation (', self.until(b'Operation ('))
        os.write(self.master, b'\n')
        self.assertIn(b'Hosts (', self.until(b'Hosts ('))
        os.write(self.master, b'1\n')
        menu = self.until(b'Space toggle', b'Packages (Enter = checked defaults; none; q): ')
        self.assertIn(b'quality-gates', menu if b'quality-gates' in menu else self.transcript)

    def assert_terminal_restored(self):
        before = json.loads(self.mode_snapshot.read_text())
        after = json.loads(self.mode_after.read_text())
        mode = self.termios.tcgetattr(self.slave)
        mode[6] = [x.hex() if isinstance(x, bytes) else x for x in mode[6]]
        # Darwin tcsetattr itself sets PENDIN when restoring canonical mode;
        # a minimal openpty/setraw/tcsetattr experiment reproduces this bit.
        pending = getattr(self.termios, 'PENDIN', 0) if sys.platform == 'darwin' else 0
        for value in (before, after, mode):
            value[3] &= ~pending
        self.assertEqual(after, before)
        self.assertEqual(mode, before)

    def assert_no_mutations(self):
        calls = [json.loads(line) for line in self.log.read_text().splitlines()]
        self.assertTrue(all(row == ['--version'] or row in [
            ['plugin', 'list', '--json'], ['plugin', 'marketplace', 'list', '--json']
        ] for row in calls))

    def test_keyboard_deselects_every_default_and_selects_superpowers(self):
        self.enter_packages()
        os.write(self.master, b' \x1b[B' * 9 + b' \r')
        updates = self.until(b'Updates (')
        self.assertIn(b'Updates (', updates, updates[-900:].decode(errors='replace'))
        os.write(self.master, b'\n')
        proposal = self.until(b'Approve source preparation?')
        self.assertIn(b'add_marketplace: claude / claude-plugins-official', proposal)
        self.assertNotIn(b'add_marketplace: claude / tomwangowa', proposal)
        os.write(self.master, b'q\n')
        self.process.wait(timeout=5)
        self.assertEqual(self.process.returncode, 130)
        self.assert_terminal_restored()
        self.assert_no_mutations()

    def test_keyboard_cancel_restores_terminal_without_source_or_install(self):
        self.enter_packages()
        os.write(self.master, b'q')
        # Drain PTY output while the child leaves raw mode and flushes stdout.
        self.assertIn(b'Cancelled.', self.until(b'Cancelled.', timeout=2))
        self.process.wait(timeout=2)
        self.assertEqual(self.process.returncode, 130)
        self.assert_terminal_restored()
        self.assert_no_mutations()

    def test_control_c_cancels_and_restores_terminal(self):
        self.enter_packages()
        os.write(self.master, b'\x03')
        self.assertIn(b'Cancelled.', self.until(b'Cancelled.', timeout=2))
        self.process.wait(timeout=2)
        self.assertEqual(self.process.returncode, 130)
        self.assert_terminal_restored()
        self.assert_no_mutations()

    def test_unchecking_all_does_not_reinstate_defaults_or_request_installation(self):
        self.enter_packages()
        os.write(self.master, b' \x1b[B' * 9 + b'\r')
        self.assertIn(b'No packages selected.', self.until(b'No packages selected.'))
        self.process.wait(timeout=2)
        self.assertEqual(self.process.returncode, 0)
        self.assertNotIn(b'Approve installation', self.transcript)
        self.assert_no_mutations()
