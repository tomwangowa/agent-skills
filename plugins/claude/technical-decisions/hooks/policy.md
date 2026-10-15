[agent-skills routing: technical-decisions]
Respect explicit user instructions, permissions and higher-priority policy.
Resolve references below to this package’s actual exposed skill identifiers.
Do not invoke an absent skill or substitute an unrelated provider with the same short name.
Check invocation_intent in exposed metadata or the scoped catalog. A user-only step is a
manual checkpoint: require explicit user invocation; workflow confirmation is not that invocation.
Before new feature design or behavior changes, use technical-decisions:brainstorming.
Honor a complete approved specification or an explicit user skip; do not restart approved design.
Keep the requirements/design approval and manual checkpoints in the selected workflow.
Preference-off does not disable engineering routing.
Superpowers (conditional): Before a multi-step design hands off to implementation planning.
At that boundary, inspect actual exposed registered skills: writing-plans.
Read identity/version from the exposed provider’s native manifest; a directory name or registry mention is not proof.
If missing, incomplete or untested, report the affected branch and obtain the needed validation
before taking it. Unrelated package operations remain available. Do not claim version compatibility from registration alone.
Superpowers (conditional): Only the chosen execution branch after PM/RD or research planning.
At that boundary, inspect actual exposed registered skills: subagent-driven-development, executing-plans.
Read identity/version from the exposed provider’s native manifest; a directory name or registry mention is not proof.
If missing, incomplete or untested, report the affected branch and obtain the needed validation
before taking it. Unrelated package operations remain available. Do not claim version compatibility from registration alone.
