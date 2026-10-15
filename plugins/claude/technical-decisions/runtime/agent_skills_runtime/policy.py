"""Scoped routing and availability checks over explicit registered provider metadata."""
from __future__ import annotations


def check_superpowers(required_skills: list[str], installed: dict,
                      tested_versions: list[str]) -> list[dict]:
    """Check registered identity, skills and exact tested versions without scanning user data."""
    if not required_skills:
        return [{'provider': 'superpowers', 'status': 'not_required'}]
    providers = installed.get('providers', [])
    matches = [p for p in providers if isinstance(p, dict) and p.get('name') == 'superpowers'
               and p.get('registered') is True] if isinstance(providers, list) else []
    if not matches:
        return [{'provider': 'superpowers', 'status': 'missing', 'skills': required_skills,
                 'message': 'Confirm a registered Superpowers provider before this selected workflow'}]
    if len(matches) != 1:
        return [{'provider': 'superpowers', 'status': 'ambiguous',
                 'message': 'Multiple registered identities; select the actual exposed provider'}]
    provider = matches[0]
    available = provider.get('skills', [])
    if not isinstance(available, list) or not all(isinstance(s, str) for s in available):
        available = []
    missing = [s for s in required_skills if s not in available]
    result = {'provider': 'superpowers', 'version': provider.get('version'), 'skills': required_skills}
    if missing:
        return [{**result, 'status': 'missing_skill', 'missing_skills': missing,
                 'message': 'Registered provider does not satisfy this workflow skill contract'}]
    if provider.get('version') not in tested_versions:
        return [{**result, 'status': 'untested_version',
                 'message': 'This exact provider version has not passed the selected workflow acceptance'}]
    return [{**result, 'status': 'ok'}]


def render_policy(package: dict, surface: str, installed: dict) -> tuple[str, list[str]]:
    """Render only this package's routing; defer conditional dependency checks to selection."""
    if surface not in {'claude', 'codex'}:
        raise ValueError('Unsupported CLI surface')
    name = package['name']
    if name not in {'quality-gates', 'technical-decisions', 'skill-toolbox'}:
        return '', []
    lines = [f'[agent-skills routing: {name}]',
             'Respect explicit user instructions, permissions and higher-priority policy.',
             'Resolve references below to this package’s actual exposed skill identifiers.',
             'Do not invoke an absent skill or substitute an unrelated provider with the same short name.',
             'Check invocation_intent in exposed metadata or the scoped catalog. A user-only step is a',
             'manual checkpoint: require explicit user invocation; workflow confirmation is not that invocation.']
    if name == 'quality-gates':
        reviewer = 'code-review-codex' if surface == 'codex' else 'code-review-claude'
        lines.extend([f'For generic code review, first use {name}:{reviewer}.',
                      f'Before a completion claim, use {name}:completion-gate and report actual evidence.',
                      'The Gemini reviewer is retired; do not invoke it or send it a diff.',
                      'An external reviewer requires explicit model selection and approved diff/data scope.',
                      'Preference-off does not disable these engineering checks.'])
    elif name == 'technical-decisions':
        lines.extend([f'Before new feature design or behavior changes, use {name}:brainstorming.',
                      'Honor a complete approved specification or an explicit user skip; do not restart approved design.',
                      'Keep the requirements/design approval and manual checkpoints in the selected workflow.',
                      'Preference-off does not disable engineering routing.'])
    else:
        lines.extend([f'Use {name}:skill-router for discovery, with installed/available/unavailable states.',
                      'A package index or registry is not evidence of installation.',
                      'skill-sync is a user-only standalone mirror, not a plugin manager.',
                      'Do not write into installed plugin caches.'])
    issues = []
    for dep in package.get('dependencies', []):
        if dep['provider'] != 'superpowers':
            continue
        lines.extend([f"Superpowers ({dep['kind']}): {dep['condition']}.",
                      f"At that boundary, inspect actual exposed registered skills: {', '.join(dep['skills'])}.",
                      'Read identity/version from the exposed provider’s native manifest; a directory name or registry mention is not proof.',
                      'If missing, incomplete or untested, report the affected branch and obtain the needed validation',
                      'before taking it. Unrelated package operations remain available. Do not claim version compatibility from registration alone.'])
        if installed:
            for result in check_superpowers(dep['skills'], installed, dep['tested_versions']):
                if result['status'] != 'ok':
                    issues.append(f"{dep['kind']} workflow ({dep['condition']}): {result['status']}")
    return '\n'.join(lines) + '\n', issues
