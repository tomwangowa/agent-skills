#!/usr/bin/env python3
"""Build an exclusive, deterministic installer ZIP without downloads or npm."""
from __future__ import annotations

import argparse
import hashlib
import io
import json
import subprocess
import sys
import zipfile
from dataclasses import asdict, replace
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(ROOT / 'runtime'))
from agent_skills_installer.catalog import build_catalog, read_json, safe_path
from agent_skills_installer.dependencies import render_bootstrap
from agent_skills_installer.providers import parse_native_acceptance, target_accepted

INSTALLER_MODULES = ('__init__.py', '__main__.py', 'models.py', 'catalog.py', 'hosts.py',
                     'dependencies.py', 'planning.py', 'execution.py', 'journal.py', 'receipts.py', 'providers.py', 'ui.py', 'selection.py', 'progress.py', 'process.py', 'removal.py', 'removal_ui.py')
SHARED_MODULES = ('__init__.py', 'config.py', 'setup.py')
LAUNCHERS = {'install-macos.command': 'macos', 'install-linux.sh': 'linux', 'install-windows.ps1': 'windows'}
ACCEPTANCE_EVIDENCE = {
    'acceptance-evidence/claude-login-matrix-evidence.json': 'docs/validation/plugin-installer/claude-login-matrix-evidence.json',
    'acceptance-evidence/codex-no-account-native-evidence.json': 'docs/validation/plugin-installer/codex-no-account-native-evidence.json',
}


def evidence_matches(record, proof, spec):
    """Keep capability records tied to the actual tested content and auth cases."""
    def matches(row, hash_key):
        return all(row.get(key) == getattr(record, key) for key in
                   ('cli_version', 'platform', 'architecture', 'catalog_commit', 'manifest_version')) and (
                       row.get(hash_key) == record.content_hash and row.get('enabled') is True
                       and row.get('executable_modes_match') is True)
    if record.host == 'claude':
        if proof.get('status') != 'both-native-auth-state-installations-passed':
            return False
        for name, logged_in in (('no-account', False), ('signed-in-isolated', True)):
            row = proof.get('cases', {}).get(name, {})
            method = 'claude.ai' if logged_in else 'none'
            if not (matches(row, 'content_hash') and row.get('scope') == 'user'
                    and row.get('payload_commit') == spec.provider.payload_commit
                    and row.get('catalog_stayed_git_at_all_observation_points') is True
                    and row.get('source_add_exit') == 0 and row.get('plugin_install_exit') == 0
                    and row.get('auth_before', {}).get('loggedIn') is logged_in
                    and row.get('auth_after', {}).get('loggedIn') is logged_in
                    and row.get('auth_before', {}).get('authMethod') == method
                    and row.get('auth_after', {}).get('authMethod') == method):
                return False
        return True
    return (proof.get('status') == 'verified-native-no-account-capability'
            and matches(proof, 'tree_hash') and proof.get('catalog') == record.catalog_name
            and proof.get('native_install_exit') == 0 and proof.get('final_native_inventory_exit') == 0
            and proof.get('auth_json_absent') is True
            and proof.get('synthetic_company_config_preserved') is True)


def _json(data):
    return (json.dumps(data, sort_keys=True, indent=2, ensure_ascii=False) + '\n').encode('utf-8')


def build_bundle(repo_root: Path, output: Path) -> Path:
    """Package only maintained runtime inputs; refuse to replace any existing output."""
    if output.exists() or output.is_symlink():
        raise FileExistsError(output)
    providers = read_json(repo_root, 'installer/providers.json')
    dependencies = read_json(repo_root, 'installer/dependencies.json')
    acceptance = parse_native_acceptance(read_json(repo_root, 'installer/provider-acceptance.json'))
    catalog = build_catalog(repo_root, providers, dependencies)
    result = subprocess.run(('git', 'rev-parse', '--verify', 'HEAD'), cwd=repo_root, capture_output=True, text=True, check=True)
    commit = result.stdout.strip()
    files, inputs = {}, {}

    def read(relative):
        content = safe_path(repo_root, relative).read_bytes()
        inputs[relative] = hashlib.sha256(content).hexdigest()
        return content

    for module in INSTALLER_MODULES:
        relative = 'runtime/agent_skills_installer/' + module
        files[relative] = read(relative)
    for module in SHARED_MODULES:
        relative = 'runtime/agent_skills_runtime/' + module
        files[relative] = read(relative)
    for name in ('install.py', 'providers.json', 'provider-acceptance.json', 'dependencies.json', 'README.md'):
        files[name] = read('installer/' + name)
    for record in acceptance:
        if record.evidence_ref not in ACCEPTANCE_EVIDENCE:
            raise ValueError('Native acceptance evidence is not in the reviewed bundle allowlist')
        spec = next(p for p in catalog if p.host == record.host and p.provider)
        spec = replace(spec, marketplace=record.catalog_name)
        if not target_accepted(spec, (record,), record.cli_version, record.platform, record.architecture):
            raise ValueError('Native acceptance record differs from the packaged target')
        content = read(ACCEPTANCE_EVIDENCE[record.evidence_ref])
        proof = json.loads(content)
        if not evidence_matches(record, proof, spec):
            raise ValueError('Native acceptance evidence disagrees with its record')
        # Raw-log fingerprints and private workspace pointers are useful to the
        # author, while the distributed capability summary needs only the facts.
        public = {k: v for k, v in proof.items() if k not in ('evidence_root', 'raw_file_hashes')}
        if record.host == 'claude':
            public['cases'] = {name: {k: v for k, v in row.items()
                                     if k not in ('evidence_root', 'saved_results_hashes')}
                               for name, row in proof['cases'].items()}
        files[record.evidence_ref] = _json(public)
    for name, platform in LAUNCHERS.items():
        files[name] = render_bootstrap(read('installer/' + name).decode('utf-8'), platform, dependencies).encode('utf-8')
    for relative in ('scripts/build_plugin_installer.py', 'plugin-packages.json', 'skills-catalog.json',
                     '.claude-plugin/marketplace.json', '.agents/plugins/marketplace.json'):
        read(relative)
    files['catalog.json'] = _json({'schema_version': 2, 'source_commit': commit, 'plugins': [asdict(p) for p in catalog]})
    files['provenance.json'] = _json({'schema_version': 1, 'source_commit': commit,
                                    'inputs': inputs,
                                    'files': {name: hashlib.sha256(content).hexdigest() for name, content in sorted(files.items())},
                                    'note': 'Input hashes describe this build, including uncommitted files; source_commit alone is not a clean-source assertion. The provenance file excludes its own hash.'})
    stream = io.BytesIO()
    with zipfile.ZipFile(stream, 'w', compression=zipfile.ZIP_DEFLATED, compresslevel=9) as archive:
        for name, content in sorted(files.items()):
            info = zipfile.ZipInfo('agent-skills-installer/' + name, (1980, 1, 1, 0, 0, 0))
            info.create_system = 3
            info.compress_type = zipfile.ZIP_DEFLATED
            executable = name in LAUNCHERS or name == 'install.py'
            info.external_attr = (0o100755 if executable else 0o100644) << 16
            archive.writestr(info, content)
    output.parent.mkdir(parents=True, exist_ok=True)
    with output.open('xb') as destination:
        destination.write(stream.getvalue())
    return output


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--output', type=Path, required=True)
    args = parser.parse_args(argv)
    try:
        path = build_bundle(ROOT, args.output)
    except (OSError, ValueError, KeyError, subprocess.SubprocessError) as error:
        parser.exit(1, f'Installer build failed: {error}\n')
    print(f'Installer archive: {path}')
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
