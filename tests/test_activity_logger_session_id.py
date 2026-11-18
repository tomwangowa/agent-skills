"""The activity logger takes each record's session id from the host session, not a file."""
import json
import os
import subprocess
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SCRIPTS = ROOT / 'activity-logger/scripts'
HOST_VARS = ('CLAUDE_SESSION_ID', 'CLAUDE_CODE_SESSION_ID', 'CODEX_THREAD_ID')


class SessionId(unittest.TestCase):
    def setUp(self):
        temp = tempfile.TemporaryDirectory(); self.addCleanup(temp.cleanup)
        self.root = Path(temp.name).resolve()
        config = self.root / 'config'; config.mkdir()
        (config / 'work-journal.json').write_text(json.dumps({'sources': {
            'activities': 'journal', 'notes': {'paths': ['notes']}}}))
        self.journal = config / 'journal'; self.journal.mkdir()
        # The suite itself may run inside Claude Code or Codex: no host id leaks in.
        self.env = {k: v for k, v in os.environ.items() if k not in HOST_VARS}
        self.env['AGENT_SKILLS_CONFIG_DIR'] = str(config)
        self.env.pop('CLAUDE_ACTIVITIES_DIR', None)

    def run_script(self, script, *args, **host):
        result = subprocess.run(['bash', str(SCRIPTS / script), *args], capture_output=True,
                                text=True, env=dict(self.env, **host), cwd=self.root)
        self.assertEqual(result.returncode, 0, result.stderr)
        return result.stdout

    def log(self, **host):
        before = set(self.journal.glob('*.json'))
        self.run_script('log_activity.sh', '-d', 'record', **host)
        (record,) = set(self.journal.glob('*.json')) - before
        session_id = json.loads(record.read_text())['session_id']
        self.assertTrue(record.name.startswith(session_id + '_'), record.name)
        return session_id

    def stale_file(self):
        (self.journal / '.session_id').write_text('session_20260113_142037_a568b5ea\n')

    def test_explicit_id_wins_over_host_ids(self):
        self.stale_file()
        self.assertEqual(self.log(CLAUDE_SESSION_ID='chosen', CLAUDE_CODE_SESSION_ID='claude',
                                  CODEX_THREAD_ID='codex'), 'chosen')

    def test_claude_code_session_wins_over_a_stale_file(self):
        self.stale_file()
        self.assertEqual(self.log(CLAUDE_CODE_SESSION_ID='claude-uuid'), 'claude-uuid')

    def test_codex_thread_is_used_inside_codex(self):
        self.stale_file()
        self.assertEqual(self.log(CODEX_THREAD_ID='codex-thread'), 'codex-thread')

    def test_without_a_host_each_record_gets_its_own_id_and_no_file(self):
        first, second = self.log(), self.log()
        self.assertNotEqual(first, second)
        self.assertRegex(first, r'^session_\d{8}_\d{6}_[0-9a-f]{8}$')
        self.assertFalse((self.journal / '.session_id').exists())

    def test_a_stale_file_is_never_read(self):
        self.stale_file()
        self.assertNotEqual(self.log(), 'session_20260113_142037_a568b5ea')

    def test_info_shows_the_host_session(self):
        self.stale_file()
        self.log(CLAUDE_CODE_SESSION_ID='claude-uuid')
        out = self.run_script('init_activities.sh', 'info', CLAUDE_CODE_SESSION_ID='claude-uuid')
        self.assertIn('Session ID: claude-uuid', out)
        self.assertIn('Activities in this session: 1', out)
        self.assertNotIn('a568b5ea', out)

    def test_info_without_a_host_session(self):
        self.stale_file()
        self.assertIn('Session ID: No host session', self.run_script('init_activities.sh', 'info'))

    def test_reset_removes_the_legacy_file(self):
        self.stale_file()
        self.run_script('init_activities.sh', 'reset')
        self.assertFalse((self.journal / '.session_id').exists())


if __name__ == '__main__':
    unittest.main()
