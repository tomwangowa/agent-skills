"""Render native CLI packages from explicit source files and measured contracts."""
from __future__ import annotations

import hashlib
import json
import re
import shutil
from pathlib import Path

from .catalog import load_packages, surface_skills
from .resources import collect_resources
from runtime.agent_skills_runtime.policy import render_policy


def write_json(path: Path, value: object) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(value, ensure_ascii=False, sort_keys=True, indent=2) + '\n', encoding='utf-8')


def digest(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def source_binding(root: Path, package: dict, contracts: dict) -> dict:
    return {'package': package, 'catalog_sha256': digest(root / 'skills-catalog.json'),
            'contracts_sha256': hashlib.sha256(json.dumps(contracts, sort_keys=True).encode()).hexdigest(),
            'resources': {p.relative_to(root.resolve()).as_posix(): digest(p)
                          for p in collect_resources(root, package)}}


def _contract(contracts: dict, surface: str) -> dict:
    record = contracts.get('surfaces', {}).get(f'{surface}-cli', {})
    expected = f'.{surface}-plugin/plugin.json'
    if record.get('status') != 'verified' or record.get('manifest_format') != expected:
        raise ValueError(f'{surface}: measured native manifest contract is required')
    return record


def _scoped_registry(content: str, selected: set[str]) -> str:
    """Filter category entries in the repository's block format; workflows stay contextual."""
    lines = content.splitlines(keepends=True)
    output, include, in_workflows = [], True, False
    for line in lines:
        if re.match(r'^# \d+ skills', line):
            continue
        if line.startswith('workflows:'):
            in_workflows = True; include = True
        match = re.match(r'^      - id: (\S+)\s*$', line)
        if match and not in_workflows:
            include = match.group(1) in selected
        elif line.strip() and not line.lstrip().startswith('#') and len(line) - len(line.lstrip()) <= 4:
            include = True
        if include:
            output.append(line)
    for n, line in enumerate(output):
        if line.strip() == 'skills:':
            next_line = next((s for s in output[n + 1:] if s.strip() and not s.lstrip().startswith('#')), '')
            if not next_line.startswith('      - id:'):
                output[n] = line.rstrip() + ' []\n'
    return '# Generated scoped registry; verify actual runtime availability.\n' + ''.join(output)


def render_package(repo_root: Path, package: dict, surface: str, destination: Path,
                   contracts: dict, *, server_bundle: Path | None = None) -> None:
    """Create a new package; validate all source resources before any output is written."""
    root = repo_root.resolve()
    _contract(contracts, surface)
    selected = surface_skills(package, surface)
    resources = collect_resources(root, package)
    if package['name'] == 'work-journal' and (server_bundle is None or not (server_bundle / 'dist/index.js').is_file()):
        raise ValueError('work-journal requires a prepared compiled production server')
    if destination.exists() or destination.is_symlink():
        raise ValueError('Render destination must be new')
    destination.mkdir(parents=True)
    for source in resources:
        relative = source.relative_to(root)
        first = relative.parts[0]
        if first in package['skills']:
            if first not in selected:
                continue
            target = destination / 'skills' / relative
        elif first == 'skills-query-server':
            continue  # source files/lockfile are build inputs, never runtime downloads
        elif relative.parts[:2] == ('docs', 'plugins'):
            target = destination / relative.name
        else:
            target = destination / relative
        target.parent.mkdir(parents=True, exist_ok=True)
        shutil.copyfile(source, target)
        target.chmod(source.stat().st_mode & 0o777)
    source_catalog = json.loads((root / 'skills-catalog.json').read_text())
    write_json(destination / 'skills/skills-catalog.json', {
        'schema_version': 1, 'skills': [s for s in source_catalog['skills'] if s['id'] in selected]})
    identity = {'name': package['name'], 'version': package['version'],
                'description': f"{package['name']} skills for {surface} CLI"}
    if surface == 'codex':
        identity['skills'] = './skills/'
    hooks = []
    if package['name'] == 'session-preferences':
        hooks = ['skills/session-preferences/scripts/session_start_hook.py',
                 'skills/control-return/scripts/session_start_hook.py']
    policy, _ = render_policy(package, surface, {})
    if policy:
        (destination / 'hooks').mkdir(parents=True, exist_ok=True)
        (destination / 'hooks/policy.md').write_text(policy, encoding='utf-8')
        (destination / 'hooks/policy.py').write_text(
            'import json\nimport sys\nfrom pathlib import Path\n'
            'try:\n'
            '    context = Path(__file__).with_name("policy.md").read_text(encoding="utf-8")\n'
            '    print(json.dumps({"hookSpecificOutput": {"hookEventName": "SessionStart", "additionalContext": context}}))\n'
            'except (OSError, UnicodeError) as error:\n'
            '    print(f"Package routing not loaded: {error}", file=sys.stderr)\n'
            '    raise SystemExit(1)\n', encoding='utf-8')
        hooks.append('hooks/policy.py')
    if hooks:
        write_json(destination / 'hooks/hooks.json', {'hooks': {'SessionStart': [{
            'matcher': 'startup|resume|clear|compact',
            'hooks': [{'type': 'command', 'command': f'python3 "${{CLAUDE_PLUGIN_ROOT}}/{script}"'} for script in hooks]}]}})
        if surface == 'codex':
            identity['hooks'] = './hooks/hooks.json'
    write_json(destination / f'.{surface}-plugin/plugin.json', identity)
    if package['name'] == 'work-journal':
        # A prepared bundle has no symlinks and no private configuration.
        for path in server_bundle.rglob('*'):
            if path.is_symlink():
                raise ValueError('Prepared server must not contain symlinks')
        shutil.copytree(server_bundle, destination / 'server')
        (destination / 'server/launch.mjs').write_text(
            "import { fileURLToPath } from 'node:url';\n"
            "process.chdir(fileURLToPath(new URL('.', import.meta.url)));\n"
            "await import('./dist/index.js');\n", encoding='utf-8')
        launch = {'command': 'node', 'args': ['${CLAUDE_PLUGIN_ROOT}/server/launch.mjs']}
        if surface == 'codex':
            launch = {'command': 'node', 'args': ['launch.mjs'], 'cwd': './server/',
                      'env_vars': ['AGENT_SKILLS_CONFIG_DIR', 'XDG_CONFIG_HOME', 'CLAUDE_ACTIVITIES_DIR']}
        write_json(destination / '.mcp.json', {'mcpServers': {f'agent_skills_work_journal_{surface}': launch}})
    registry = destination / 'skills/skill-router/skill-registry.yaml'
    if registry.exists():
        registry.write_text(_scoped_registry(registry.read_text(), set(selected)), encoding='utf-8')
        packages = load_packages(root)
        index = []
        for p in packages:
            for skill in surface_skills(p, surface):
                row = next(s for s in source_catalog['skills'] if s['id'] == skill)
                index.append({**row, 'package': p['name'], 'provider': f"{p['name']}:{skill}",
                              'availability': 'available_to_install'})
        write_json(destination / 'skills/package-index.json', {'schema_version': 1, 'skills': index})
    readme = f"# {package['name']}\n\nVersion {package['version']}; {surface} CLI.\n\n"
    readme += 'Included skills:\n\n' + ''.join(f'- `{package["name"]}:{s}`\n' for s in selected)
    if (destination / 'installation.md').is_file():
        readme += '\nRead [installation and setup](installation.md), [migration and recovery](migration.md),\n'
        readme += '[Superpowers compatibility](superpowers-compatibility.md) and [team instructions](team-instructions.md).\n'
    readme += ('\nNative acceptance on 2026-10-15 covered all seven packages with Claude Code CLI 2.1.300 '
               'and Codex CLI 0.162.1 on isolated macOS fixtures. session-preferences, work-journal, '
               'repo-workflow and skill-toolbox changed after that run and need native acceptance again '
               'before release. Claude Code CLI '
               '2.1.302 verified GitHub marketplace installation and update checks on 2026-10-17; Codex CLI '
               'remote marketplace installation and release approval remain pending.\n')
    if package['name'] == 'skill-toolbox' and surface == 'codex':
        readme += '\nclaude-workflow-designer is Claude Code-only and is excluded.\n'
    (destination / 'README.md').write_text(readme, encoding='utf-8')
    write_json(destination / '.source.json', source_binding(root, package, contracts))
    write_json(destination / '.generated-files.json', {
        'schema_version': 1, 'files': {p.relative_to(destination).as_posix(): {
            'sha256': digest(p), 'mode': p.stat().st_mode & 0o777}
            for p in sorted(destination.rglob('*')) if p.is_file()}})


def render_marketplaces(repo_root: Path, packages: list[dict]) -> tuple[dict, dict]:
    """Preserve existing Claude mods and replace only the seven managed entries."""
    current = json.loads((repo_root / '.claude-plugin/marketplace.json').read_text())
    names = {p['name'] for p in packages}
    current['plugins'] = [p for p in current['plugins'] if p['name'] not in names] + [
        {'name': p['name'], 'source': f'./plugins/claude/{p["name"]}', 'version': p['version'],
         'description': f"{p['name']} skills"} for p in packages]
    codex = {'name': current['name'], 'interface': {'displayName': 'Agent Skills'}, 'plugins': [
        {'name': p['name'], 'source': {'source': 'local', 'path': f'./plugins/codex/{p["name"]}'},
         'policy': {'installation': 'AVAILABLE', 'authentication': 'ON_INSTALL'},
         'category': 'Developer Tools'} for p in packages]}
    return current, codex
