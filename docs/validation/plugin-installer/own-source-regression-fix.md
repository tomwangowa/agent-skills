# Own-package missing-source regression repair

Date: 2026-11-10. Scope: the user selected the independent, offline regression
repair only. Working-tree behavior is verified below. At repair completion,
no new archive, native installation, external operation, commit or release
acceptance was claimed. The later, separately requested [R5 build](candidate-r5.md)
packages this repair without native acceptance.

## Problem and correction

With either Claude Code or Codex, selecting an own package without its
marketplace made `make_plan` read `readiness.snapshot` when `readiness` was
`None`. The UI also reached that branch after the user declined source
preparation and continued to the installation preview.

The [planner](../../../runtime/agent_skills_installer/planning.py) now attaches
provider-specific preconditions only when the selected spec has a provider.
Own-package source proposals keep the ordinary source-action preconditions;
they do not invent provider readiness. Existing external-provider checks and
the UI's separate source/install consent checkpoints are unchanged.

## Reproduction and regression evidence

Before changing production code:

- Pure `make_plan` calls reproduced the `AttributeError` independently on both
  hosts with missing `tomwangowa` marketplaces and valid host metadata.
- The existing installer suite ran 83 tests: 82 passed, one PowerShell test
  skipped. That suite did not detect this regression.
- Four new test methods failed with six subcase errors, all at the original
  `readiness.snapshot` access. After the repair those four methods passed.
- A subsequent in-memory replay of the pre-repair planner made all four new
  methods fail with the same six errors. The working-tree planner was not
  reverted or rewritten for this sensitivity check.

| Required behavior | Offline evidence |
| --- | --- |
| Missing own source on Claude and Codex | Each plans one source-add proposal, keeps the package skipped pending separate consent, and carries no provider preconditions |
| Multiple own packages share a missing source | Exactly one proposal per host/source, with a skipped result for each package |
| Source preparation declined, installation then approved | Both host transcripts return partial exit 1, show skipped results, and execute no source or install command; retained files and the absent Codex config directory are checked |
| One host's source pending, another ready | The Claude fixture installs and verifies real copied package bytes while the Codex fixture remains skipped; overall exit is 1 |
| External-provider isolation | Existing Superpowers planning tests still cover separate acceptance, reserved Codex catalog refusal and preservation of existing providers |

The transcripts exercise the real UI, planner and executor. Only native CLI
processes and tool availability are replaced. Unexpected commands fail the
missing-source fixture immediately. These are synthetic offline cases, not
evidence of native CLI behavior or Windows/Linux compatibility.

## Verification

All commands ran locally in this worktree after the repair unless identified
as pre-repair evidence above.

| Command/check | Result |
| --- | --- |
| `PYTHONPATH=runtime:tests python3 -m unittest -v test_installer_planning test_installer_cli test_installer_superpowers_plan` | 20 passed, exit 0 |
| `PYTHONPATH=runtime python3 -m unittest discover -s tests -p 'test_installer_*.py'` | 87 run: 86 passed, 1 skipped, exit 0 |
| `python3 -m unittest discover -s tests -p 'test_agent_skills_config.py'` | 15 passed, exit 0 |
| `python3 -m unittest discover -s tests -p 'test_plugin_packages.py'` | 14 passed, exit 0 |
| `python3 scripts/validate_skills_catalog.py --check` | Exit 0 |
| Python AST parsing of the three changed Python files | Passed |
| Repair-delta whitespace and documentation links | Passed |

The skipped test is
`BootstrapTests.test_python_probe_does_not_invoke_download_shim`: no native
`pwsh` is available. It is not counted as a passed test.

The first preservation-check script incorrectly classified the existing
tracked `AGENTS.md` symlink as a new file: its baseline excluded symlinks, but
its comparison did not. After confirming Git mode `120000` and target
`CLAUDE.md`, the comparison used the same regular-file filter and passed.
No product or policy file was changed to resolve this verification-script error.

## Findings

No findings in the repair delta.

Self-review in same Codex session: commitment / recency / framing bias not fully controlled.

## Adversarial check

- Missing state is handled by the owning branch, not by catching the exception
  or manufacturing readiness; both host cases exercise this distinction.
- Multiple packages must not create repeated source proposals; the shared
  source test checks action counts and per-package outcomes.
- Final installation consent must not authorize a declined source write;
  transcripts check the installation preview, command history, files and exit.
- A pending source must not suppress an independently approved installation;
  the mixed-host case checks the installed package and the partial result.
- The old implementation fails every new regression method; the tests assert
  real plans and flow results, not a mocked planner's return value.

Adversarial check: no additional issues found.

## Assumptions

- Inventory distinguishes absent marketplaces from inventory errors. Existing
  error/conflict tests remain in the installer suite; this repair does not
  treat uncertain observations as an empty inventory.
- Source preparation and installation retain separate consent checkpoints.
  Refusal followed by installation approval is explicitly tested on both hosts.
- Native schemas and side effects match the existing adapters. The fixtures
  cannot establish that assumption for a real CLI or another platform; native
  verification remains separate.

## Review scope

Only the changes made during this repair were reviewed, relative to the saved
pre-repair working-tree files, including their uncommitted implementation:

- `runtime/agent_skills_installer/planning.py`: missing-source action branch.
- `tests/test_installer_planning.py`: two new regression methods.
- `tests/test_installer_cli.py`: missing-source process fixture and two new
  transcript methods.
- This record and the validation index update.

Nearby source-action construction, UI rechecks, executor behavior and existing
Superpowers tests were read to assess the repair. This is not a fresh review
of the entire uncommitted installer feature.

## VERIFIED

- The missing-own-source regression and the refusal/partial-result paths above
  are repaired in the working tree with fresh offline evidence.
- HEAD, all four stash entries, existing plugin payloads and the saved native
  evidence files are unchanged from the repair baseline. Existing unrelated
  working-tree files were checked by hash rather than reset or replaced.
- `dist/agent-skills-installer-fe55c04-candidate-r4.zip` is unchanged; SHA-256:
  `46994537305c0f97268aa9cfbed825378b9b485130ff25732b57a3b8e304a549`.

## NOT VERIFIED

- The preserved R4 archive is not repaired. No replacement candidate was built
  during the repair; the subsequent R5 build is recorded separately above.
- The proposed archive-source policy, independent upstream payload proof,
  production acceptance records and native installations remain outside this
  repair. No product hashes or acceptance settings were changed.
- Windows/PowerShell, Linux native installation, real CLI effects, hooks, MCP
  and model workflows were not exercised. Tool-availability detection was
  replaced in the new UI transcripts; dependency installation is not proven.
- Repository-wide build/full-test gates were not run: they can execute
  `npm ci` and exceed the explicitly offline scope. No server changes are part
  of this repair; no server test result is claimed.
- Native cross-process timing and concurrent host-state changes were not
  probed; the existing recheck behavior is unchanged.
