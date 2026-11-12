# R7 full-package installation coexistence proposal

Date: 2026-11-11. **PREPARED; NOT STARTED; NEW NATIVE APPROVAL REQUIRED.**
The user selected multi-package coexistence verification. This batch verifies
installation together in one host configuration and preservation on rerun;
it does not test model workflows, active hook routing or MCP functionality.

## Prepared scope

Use the unchanged 56,060-byte R7 ZIP, SHA-256
`d598a8170b57ba27a29a1ecdcbef3c450ec0acf4f25c9a4edca8f864f8b0f4ea`.
Root: `.superpowers/sdd/2026-11-11-r7-coexistence/prepared-qiw2o6pb/`.
Both host profiles, homes/caches/temp directories and extracted candidates are
new. Both native working directories were verified outside Git. Earlier native
profiles and evidence remain intact and fingerprinted; none is reset or reused.
No personal credentials/settings were copied. No account login is included.

| Package | Claude Code 2.1.322 | Codex 0.167.0 |
| --- | --- | --- |
| quality-gates | 0.2.0 | 0.2.0 |
| technical-decisions | 0.1.3 | 0.1.3 |
| repo-workflow | 0.3.0 | 0.3.0 |
| content-tools | 0.2.0 | 0.2.0 |
| work-journal | 0.2.0 | 0.2.0 |
| session-preferences | 0.1.4 | 0.1.4 |
| skill-toolbox | 0.1.3 | 0.1.3 |
| handoff-mod | 0.2.2 | Not applicable |
| attention-mod | 0.6.1 | Not applicable |
| Superpowers | 7.0.0, official catalog | 6.3.0, API-curated catalog |

Total: **10 Claude packages and 8 Codex packages**, installed together within
their respective profiles. Expected complete native payloads: 4,240 Claude
files and 3,959 Codex files. All 16 own-package source trees were rechecked
locally against R7's frozen hashes before this proposal.

Codex uses a synthetic company provider at `https://company.invalid/v1`, a dummy
environment key and `requires_openai_auth = false`. Plugin/discovery remote
prefetch and analytics are disabled. Real company endpoints or secrets are not
used. Claude's clean profile must remain unauthenticated before/after both runs.

## Actual native budget requiring approval

Run the untouched R7 Python entry twice per host: **four installer invocations**.
Select all host packages (Claude 1–10, Codex 1–8), keep updates blank, approve
only the fixed source/first-install plans and decline optional journal setup.
Do not supply mod personal configuration, grant hook trust, launch a normal
agent session, MCP server, attention panel, feedback handler or workflow skill.

Maximum new native mutations:

- **Three marketplace additions**: `tomwangowa` once per host from
  `https://github.com/tomwangowa/agent-skills.git`, plus
  `https://github.com/anthropics/claude-plugins-official.git` once for Claude.
  Claude uses `--scope user --json`; Codex's own source uses `--ref main --json`.
- **18 plugin installs**, exactly the table above at most once per target.
  Claude: `claude plugin install <name>@<marketplace> --scope user --json`.
  Codex: `codex plugin add <name>@<marketplace> --json`.
  Own packages use `tomwangowa`; Superpowers uses each listed official route.
- **One Codex native catalog startup** through the already tested App Server
  producer, with only `initialize` / `initialized`, no thread/turn. Its native
  Git/GitHub HTTP/missing-snapshot official export fallback chain is included
  for this single startup. No installer-seeded managed catalog is used.
- **Zero mutations on rerun**, and no dependency installation, update, refresh,
  removal, privilege change, package-manager installation or retry.

Downloads reach the public own/official GitHub sources and potentially OpenAI's
official curated export backup. Native caches, registries and enabled settings
are written only inside the new profiles. The observer sends no model request;
no model token charge is planned. Native internal transport/wire counts are not
equated with these command-attempt limits. Existing personal state is protected.

Stock R7 version/inventory/local Python/Git probes are included. Codex inventory
must be named `tomwangowa` or `openai-api-curated`, never unqualified/global.
Observers may read one final native inventory per relevant marketplace after
each run, auth status before/after each Claude run, local payload/source/registry
files, and the Codex startup's version/protocol result. No additional source
refresh or manual install may compensate for a failed/withheld item.

Binary/wrapper, archive, environments, explicit selectors and source vectors
are pinned in `run.json`. Prepared `audited_entry.py` runs the unchanged entry
with native command auditing/budget enforcement and no fake runner or replaced
runtime functions. Its whitelist was tested directly on 105 allowed/denied
vectors without launching a host. An initial dry check caught a six-versus-seven
argument length mistake for named Codex inventory; it was fixed before any
native action. Each installer phase will consume a once marker.

Native startup wait: 180 seconds. Each installer invocation deadline: 1,800
seconds, with stock per-command timeouts still active. Stop the affected case
on binary/source/payload drift, unexpected prompt/dependency, missing install,
failed first-run action or other unapproved behavior. Keep partial state and
logs; terminate only the test process group if needed. No automatic retry or
rollback is included.

## Expected Codex rerun limitation, verified offline first

Frozen R7 deliberately reports existing own Codex packages as `unverified`:
`Existing Codex provider preserved; update ownership is not verified.` It issues
no write, but returns exit 1. This is distinct from its Superpowers preservation
branch. Actual all-installed synthetic inventories through the exact R7 UI
confirmed Claude rerun exit 0 and Codex rerun exit 1, both with zero mutations
and unchanged fixture files. Results are saved as `existing-exit-preflight.json`.

Do not change R7 to hide this limitation or treat every nonzero as a new-install
failure. First installations on both hosts must exit 0 and verify all selected
packages. Claude's rerun must exit 0; Codex's rerun may have only the seven known
own-package ownership warnings and expected exit 1. Any other uncertainty is
a separate failure. Both reruns must attempt no mutation and preserve all
installed content/settings. Record the Codex success-status gap explicitly;
it is not a fully green rerun status.

## Verification and limits

Require one enabled native entry per selected package, the intended source,
actual installed root/cache version, expected manifest version and complete
payload hash. Compare every installed path/byte/permission to the frozen source
and record actual scope only where native metadata provides it. Codex scope
remains unreported; do not invent user scope.

Before/after rerun, compare complete installed payload maps, enabled state,
version/root, registries/settings and native subprocess ledgers. Distinguish
native internal catalog bookkeeping from candidate mutation attempts. Recheck
original personal settings, all archives and old native test files, HEAD,
stashes and staged state. Preserve all results and native profiles unchanged.

Optional journal setup stays declined, so no real activity/note content is read
or moved. Missing handoff/attention userConfig fields remain pending. No agent
restart/model/MCP/hook function is invoked to claim runtime coexistence. These
layers need separately scoped functional tests and any necessary model/cost
approval. Windows/Linux and logged-in coexistence are outside this batch.

This approval does not include a ZIP rebuild, product fix, capability-record
change, commit, push, publication, logout or cleanup of earlier evidence.
