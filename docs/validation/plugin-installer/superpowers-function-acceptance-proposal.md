# Superpowers functional acceptance proposal

Status: **NOT RUN**. Seven required skills need independent entry and behavior
evidence for each host's actual installed version. File presence, synthetic
transcripts and a successful native installation are not behavior evidence.
Native capability and an unmodified candidate installation must precede these
cases. Claude `7.0.0` and Codex `6.3.0` do not inherit results from the local
maintainer `7.0.2` provider.

## Session and approval boundary

Use a new isolated fixture repository and the separately accepted host config.
Before any model call, fill and approve a run manifest containing the resolved
CLI binary/hash and full CLI version, exact installed source/pin/hash,
**exact model identifier**, model/provider billing account, prompt text,
fixture file hashes, output limits, cost ceiling and stop condition. No model
identifier or spending limit has been approved yet; therefore there is no
executable model invocation in this proposal. Do not use a floating default
model or an inherited personal session. This missing input blocks only the
model cases; it does not justify reopening the approved offline design.

First restart each isolated host and read its actual exposed skill catalog.
Record the provider-native manifest and exposed qualified entries. Only a real
catalog listing establishes availability; cached files or routing text alone
do not. Do not execute any entry until that run manifest is approved. Required
prompts below name Claude `/superpowers:<skill>` or Codex
`$superpowers:<skill>` explicitly; a manual invocation requirement must be
satisfied by the person, not by an agent pretending that a workflow handoff
counts. Read the installed skill copy selected by the host.

Each row is a separate normal/failure case with a fresh fixture. The model may
write only the indicated isolated artifacts. A case runs once, stops at its
manual checkpoint or first failure, and does not automatically continue to the
next row. Capture actual tokens/cost when available, otherwise mark them
unknown. No network dependencies are needed for the fixture's Python unittest.

| Skill / exact prompt suffix | Normal case and observable result | Failure case and stop point | Allowed writes / additional approval |
| --- | --- | --- | --- |
| `writing-plans`: "Plan the approved add-two-numbers fixture; do not implement." | From a fixed complete requirement, produce a plan with concrete files, test command and completion evidence. | Remove overflow behavior from the requirement: identify the gap before claiming a ready plan; stop for the person's answer. | Plan/document in fixture only; no implementation or commit. |
| `test-driven-development`: "Implement the approved integer addition fixture using this skill." | Observe a failing behavior test, minimal implementation, then a passing Python unittest; save red/green command exits. | Supply a test that passes with a no-op implementation: detect and replace it before a success claim. | Fixture code/tests; no dependency install, commit or network. |
| `systematic-debugging`: "Diagnose the supplied failing boundary test before proposing a fix." | Trace a reproducible off-by-one defect to its cause, then demonstrate failure before and pass after the targeted fix. | Supply an intermittent report with no reproduction: state the missing observation and stop instead of guessing. | Fixture diagnosis and approved local fix; no source/network access outside fixture. |
| `executing-plans`: "Execute the fixed approved two-task plan inline in this session; no agents or commits." | Perform tasks in order, retain evidence and stop at the plan's manual checkpoint. | Change a required interface between tasks: report the mismatch and stop rather than invent scope. | Fixture code/tests/ledger only; same-session execution. |
| `subagent-driven-development`: "Execute the fixed two-task independent fixture plan using this skill." | Observe actual permitted delegation, task boundaries and review evidence. | Seed conflicting ownership between two tasks: detect conflict and stop before competing writes. | **No delegation is authorized now.** Needs a distinct agent-count/model/token budget and data-scope approval; otherwise mark NOT VERIFIED. |
| `requesting-code-review`: "Review the fixture implementation against its approved requirement using this skill." | Report a seeded requirement defect with exact file/line and evidence; no unrelated rewrite. | Include a false-positive suggestion: verify it against the code/test and reject it with evidence. | Review artifact only. Same-session reviewer has known bias; a fresh agent or external reviewer requires separate approval/model/data scope. |
| `finishing-a-development-branch`: "Assess this fixture branch for integration using this skill; do not commit, merge, push or remove anything." | Verify the fixture tests and present integration choices with actual status; stop for the person. | Make a required test fail: stop before presenting an integration-ready conclusion. | Evidence document only; branch integration, worktree deletion, commit/push and publishing are not included. |

## Evaluation and partial results

For each host/version/row, record entry observed, prompt/fixture hashes, model,
normal result, failure result, actual writes, tokens/cost, manual checkpoint and
evidence link. Accept only behavior matching the approved requirement and
scope. Keep failures alongside successes. An unrun row stays **NOT VERIFIED**;
work on independent packages can proceed without claiming this workflow works.

No automatic hook trust, external reviewer, real user data, credentials,
production repository, project history export or integration is included. Each
rerun that reaches a model or outside service requires new approval. The next
concrete model-run proposal must supply the unresolved model/budget fields
above; this document alone authorizes no calls.
