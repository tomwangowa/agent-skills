"""An existing official archive must explain why it cannot be used."""
import sys
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / 'runtime'))
from agent_skills_installer.hosts import inspect_provider
from agent_skills_installer.models import Inventory, Marketplace, PluginSpec, ProviderSource


class ArchiveMessageTest(unittest.TestCase):
    def test_existing_archive_is_preserved_with_actionable_explanation(self):
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp)
            source = 'https://github.com/anthropics/claude-plugins-official.git'
            provider = ProviderSource('configured-git', source, 'git',
                                      'https://github.com/obra/superpowers.git', 'a' * 40, None, 'b' * 64)
            spec = PluginSpec('claude', 'superpowers', 'claude-plugins-official', source, '7.0.0', provider=provider)
            market = path / 'official'
            market.mkdir()
            (market / '.gcs-sha').write_text('a' * 40)
            inv = Inventory('claude', '2.1.322 (Claude Code)', marketplaces=(Marketplace(spec.marketplace, spec.source, str(market)),))
            result = inspect_provider(spec, inv)
            self.assertEqual(result.status, 'unverified')
            self.assertIn('archive', result.reason.lower())
            self.assertIn('cannot be verified', result.reason.lower())
            self.assertTrue((market / '.gcs-sha').is_file())
