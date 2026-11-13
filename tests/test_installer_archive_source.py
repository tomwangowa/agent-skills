"""Fixed archive evidence must be checked before it authorizes a plan."""
import json
import tempfile
import unittest
from pathlib import Path
from dataclasses import replace, asdict
from unittest.mock import patch
from agent_skills_installer.catalog import tree_hash
from agent_skills_installer.hosts import inspect_provider
from agent_skills_installer.planning import make_plan
from agent_skills_installer.receipts import provider_state_matches, verify_claude_install
from agent_skills_installer.models import Inventory, Marketplace, InstalledPlugin
from agent_skills_installer.providers import provider_targets, parse_native_acceptance, installation_accepted
from installer_provider_fixtures import provider_data, acceptance_data, entry


class ArchiveSourceTest(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.config = Path(self.tmp.name) / 'home'
        self.root = self.config / 'plugins/marketplaces/claude-plugins-official'
        (self.root / '.claude-plugin').mkdir(parents=True)
        (self.root / '.claude-plugin/marketplace.json').write_text(json.dumps({'name':'claude-plugins-official','plugins':[entry('claude')]}))
        (self.root / 'other.txt').write_text('verified catalog content')
        # Path-component order differs from string order for these two paths.
        (self.root / 'a').mkdir()
        (self.root / 'a/x').write_text('nested')
        (self.root / 'a-foo').write_text('sibling')
        self.commit = 'b' * 40
        self.spec = provider_targets(provider_data())[0]
        self.inv = Inventory('claude','2.1.322 (Claude Code)',marketplaces=(Marketplace(self.spec.marketplace,self.spec.source,str(self.root)),))
        self.trusted = tree_hash(self.root)
        (self.root / '.gcs-sha').write_text(self.commit)
        self.env = patch.dict('os.environ', {'CLAUDE_CONFIG_DIR':str(self.config)})
        self.env.start(); self.addCleanup(self.env.stop)
        self.anchor = patch('agent_skills_installer.hosts.CLAUDE_ARCHIVE_TREES', {self.commit:self.trusted}, create=True)
        self.anchor.start(); self.addCleanup(self.anchor.stop)

    def test_verified_archive_can_be_approved_but_modified_content_cannot(self):
        ready = inspect_provider(self.spec,self.inv)
        self.assertEqual(ready.status,'ready')
        records=parse_native_acceptance(acceptance_data(self.spec,cli=self.inv.cli_version))
        self.assertTrue(installation_accepted(self.spec,ready,records,self.inv.cli_version,'macos','arm64'))
        inv = replace(self.inv, provider_readiness=(ready,))
        plan = make_plan((self.spec,), (inv,), {('claude','superpowers')}, set(), {'git': True}, acceptance=records, platform='macos', architecture='arm64')
        self.assertEqual(len(plan.actions), 1)
        action = replace(plan.actions[0], preconditions=plan.actions[0].preconditions + (('version', self.spec.version), ('cli_version', self.inv.cli_version), ('provider_target', json.dumps(asdict(self.spec.provider), sort_keys=True, separators=(',', ':'))), ('provider_state', json.dumps(ready.snapshot, separators=(',', ':')))))
        self.assertTrue(provider_state_matches(action, self.spec, ready))
        (self.root/'other.txt').write_text('changed')
        changed = inspect_provider(self.spec,self.inv)
        self.assertNotEqual(changed.status,'ready')
        self.assertFalse(provider_state_matches(plan.actions[0], self.spec, changed))

    def test_verified_archive_revision_change_is_allowed_only_after_install(self):
        payload = Path(self.tmp.name) / 'installed'
        (payload / '.claude-plugin').mkdir(parents=True)
        (payload / '.claude-plugin/plugin.json').write_text(json.dumps({'name':'superpowers','version':'7.0.0'}))
        spec = replace(self.spec, content_hash=tree_hash(payload))
        before = inspect_provider(spec, self.inv)
        records = parse_native_acceptance(acceptance_data(spec,cli=self.inv.cli_version))
        plan = make_plan((spec,), (replace(self.inv, provider_readiness=(before,)),),
                         {('claude','superpowers')}, set(), {'git':True}, acceptance=records,
                         platform='macos', architecture='arm64')
        action = replace(plan.actions[0], preconditions=plan.actions[0].preconditions + (('version', spec.version), ('cli_version', self.inv.cli_version), ('provider_target', json.dumps(asdict(spec.provider), sort_keys=True, separators=(',', ':'))), ('provider_state', json.dumps(before.snapshot, separators=(',', ':')))))
        new_commit = 'c' * 40
        with patch('agent_skills_installer.hosts.CLAUDE_ARCHIVE_TREES',
                   {self.commit:self.trusted, new_commit:self.trusted}):
            (self.root / '.gcs-sha').write_text(new_commit)
            after = inspect_provider(spec, self.inv)
            self.assertFalse(provider_state_matches(action, spec, after))
            installed = InstalledPlugin('claude','superpowers',spec.marketplace,
                                        spec.provider.payload_repository,spec.version,str(payload),True,'user')
            self.assertTrue(verify_claude_install(action,spec,replace(self.inv,plugins=(installed,)),readiness=after))
            (payload / 'unexpected').write_text('modified')
            self.assertFalse(verify_claude_install(action,spec,replace(self.inv,plugins=(installed,)),readiness=after))

    def test_unknown_commit_and_symlink_do_not_authorize_installation(self):
        (self.root/'.gcs-sha').write_text('c'*40)
        self.assertNotEqual(inspect_provider(self.spec,self.inv).status,'ready')
        (self.root/'.gcs-sha').write_text(self.commit)
        (self.root/'other.txt').unlink()
        (self.root/'other.txt').symlink_to(self.root/'.gcs-sha')
        self.assertNotEqual(inspect_provider(self.spec,self.inv).status,'ready')

    def test_wrong_native_profile_does_not_authorize_archive(self):
        with patch.dict('os.environ',{'CLAUDE_CONFIG_DIR':str(self.config/'other')}):
            self.assertNotEqual(inspect_provider(self.spec,self.inv).status,'ready')
