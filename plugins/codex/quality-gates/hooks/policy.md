[agent-skills routing: quality-gates]
Respect explicit user instructions, permissions and higher-priority policy.
Resolve references below to this package’s actual exposed skill identifiers.
Do not invoke an absent skill or substitute an unrelated provider with the same short name.
Check invocation_intent in exposed metadata or the scoped catalog. A user-only step is a
manual checkpoint: require explicit user invocation; workflow confirmation is not that invocation.
For generic code review, first use quality-gates:code-review-codex.
Before a completion claim, use quality-gates:completion-gate and report actual evidence.
The Gemini reviewer is retired; do not invoke it or send it a diff.
An external reviewer requires explicit model selection and approved diff/data scope.
Preference-off does not disable these engineering checks.
Superpowers (conditional): Only when the selected integrated development workflow uses these steps.
At that boundary, inspect actual exposed registered skills: test-driven-development, requesting-code-review, finishing-a-development-branch.
Read identity/version from the exposed provider’s native manifest; a directory name or registry mention is not proof.
If missing, incomplete or untested, report the affected branch and obtain the needed validation
before taking it. Unrelated package operations remain available. Do not claim version compatibility from registration alone.
