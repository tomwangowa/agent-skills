[agent-skills routing: skill-toolbox]
Respect explicit user instructions, permissions and higher-priority policy.
Resolve references below to this package’s actual exposed skill identifiers.
Do not invoke an absent skill or substitute an unrelated provider with the same short name.
Check invocation_intent in exposed metadata or the scoped catalog. A user-only step is a
manual checkpoint: require explicit user invocation; workflow confirmation is not that invocation.
Use skill-toolbox:skill-router for discovery, with installed/available/unavailable states.
A package index or registry is not evidence of installation.
skill-sync is a user-only standalone mirror, not a plugin manager.
Do not write into installed plugin caches.
Superpowers (optional): Only when recommending a selected upstream workflow.
At that boundary, inspect actual exposed registered skills: writing-plans, subagent-driven-development, executing-plans.
Read identity/version from the exposed provider’s native manifest; a directory name or registry mention is not proof.
If missing, incomplete or untested, report the affected branch and obtain the needed validation
before taking it. Unrelated package operations remain available. Do not claim version compatibility from registration alone.
