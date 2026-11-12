# R7: verified Superpowers capabilities integrated

Date: 2026-11-11. The user selected integration and a new exclusive candidate.
Local integration, offline verification and packaging are complete. The later
exact-ZIP native acceptance is linked below; three-platform acceptance remains
incomplete.

Artifact: `dist/agent-skills-installer-fe55c04-candidate-r7.zip`, 56,060 bytes.
SHA-256: `d598a8170b57ba27a29a1ecdcbef3c450ec0acf4f25c9a4edca8f864f8b0f4ea`.
The adjacent `.zip.sha256` sidecar verifies successfully.

## Native follow-up

The unchanged R7 ZIP subsequently passed [all six native install/rerun
invocations](r7-native-acceptance-results.md) for the three macOS arm64 cases.
This closes exact-ZIP native/Python-entry acceptance for those cases only.
The packaging observations below remain the original local-only step.

## Enabled scope

Exactly two schema-1 native capability records and the independently verified
payload hashes were promoted into the existing schema-2 provider/catalog model:

| Host / CLI | Platform / architecture | Native route / payload | Supporting native cases |
| --- | --- | --- | --- |
| Claude Code `2.1.322 (Claude Code)` | macOS arm64 | `claude-plugins-official`, Superpowers 7.0.0 | [Logged in and logged out](claude-login-matrix-results.md) |
| Codex `codex-cli 0.167.0` | macOS arm64 | `openai-api-curated`, Superpowers 6.3.0 | [No-account native case](codex-no-account-native-results.md), synthetic company settings preserved |

Superpowers stays optional and unchecked. Existing installations are preserved.
Other versions, architectures and Windows/Linux do not acquire these records;
neither does Codex `openai-curated`. Codex still needs a native-prepared official
catalog; the installer does not silently initialize it or configure a model
endpoint. Claude uses the existing strict Git-source contract: these two actual
cases stayed Git throughout, so no archive exception or cold-start archive
trust was added. Independently eligible own packages remain available.

The new ZIP includes two minimized JSON evidence summaries under
`acceptance-evidence/`, referenced directly by the capability records. Build-time
validation checks record/target/evidence agreement, the two actual Claude auth
states and the actual Codex API route. Unknown evidence references reject the
build. Only named source summaries are read; native profiles, authentication
stores and raw native logs are not packaged. Original evidence remains intact.

## VERIFIED

- Final installer suite: **101 tests, 100 passed, one skipped**, exit 0. The skip
  is the native Windows launcher probe because PowerShell is unavailable.
- Package checks: 14 passed. Shared configuration checks: 15 passed.
  Skills-catalog validation, changed Python/JSON parsing and whitespace checks
  passed. Network-dependent full-repository release gates were not run.
- Four new release tests first failed against empty/unbound metadata, then
  passed. They check exact enablement and rejection of untested environments,
  self-contained evidence, unknown references and contradictory catalog evidence.
  A later minimization assertion failed before the packaging fix and passed
  after it; this demonstrates that raw-log fingerprints are actually excluded.
- The exact R7 has 27 entries. All 26 packaged-file hashes and 30 source-input
  hashes match provenance. A second exclusive build is byte-for-byte identical.
  All 18 catalog entries load; all 16 own host/package entries are unchanged
  from R5. R7 adds two evidence summaries, changes nine shared paths and removes
  no R5 entries. The four changed runtime paths versus R5 are the previously
  implemented Codex catalog-variant adapter, not additional runtime edits here.
- Relocated `install.py --help` exits 0 with isolated Python imports. Relocated
  runtime replay of the three saved native source observations proposes the
  expected Claude/API-Codex install actions and rejects untested OS/architectures.
  This uses empty plugin inventories to exercise planning; it executes no host
  install command and is not native end-to-end acceptance. Both shell launchers
  pass syntax checks.
- Gitleaks 8.30.1 scanned the actual extracted R7: exit 0, **zero findings**.
  No ignore rules were added. Named personal settings, prior artifacts and native
  evidence remain preserved; no native download/install/model request, stage,
  commit, push or release occurred in this integration step.

Machine-readable archive verification: [candidate-r7-evidence.json](candidate-r7-evidence.json).
Checks ran on Darwin arm64 with Python 3.14.6; Python 3.11 was not separately
executed in this step. The final preservation check confirms 72 prior protected
files unchanged, the validation index intentionally updated, four original
settings unchanged and Git state unchanged.

Detailed local outputs, red/green runs, archive checker and scan reports remain
under `.superpowers/sdd/2026-11-11-r6-integration/`.

## Initial R6 scan and resolution

R6 was built first and is retained unchanged with its checksum. Its complete
scan returned exit 1 with four generic-key findings on `auth-before`/`auth-after`
file fingerprints in the source evidence summary. Each finding was traced to
the sanitized auth-status JSON and independently recomputed as SHA-256; none
was a credential value. The adjudication and redacted scan remain retained.

Those raw-log fingerprints and private workspace pointers are not required by
the colleague-facing capability summary. The builder omits them from
distributed summaries; the committed evidence also omits the auth-state hashes
and keeps the unchanged-state result. R7 is a separate exclusive ZIP; no archive
was overwritten, no scanner rule was suppressed and no native operation was
repeated.

## Same-session review and completion gate

No remaining findings. Self-review in same Codex session: commitment / recency /
framing bias not fully controlled. Scope: capability metadata, builder evidence
allowlist/matching/minimization, release and relocated bundle tests, and README
enablement/limits. Adjacent provider resolution, receipt and plan gates were
inspected; no external reviewer or subagent was used.

Conservative risk: L2, because capability metadata permits previously withheld
native write proposals. Full scoped regression, self-review, archive checks,
source/installed-byte corroboration and secret scan were completed.

Adversarial assumptions checked: main and API catalog identities cannot borrow
acceptance; wrong CLI/OS/architecture has no positive record; malformed evidence
references cannot include arbitrary files; evidence mismatches block packaging;
raw observation pointers/fingerprints do not enter the released summary; moved
source/state still requires the existing recheck. Original-state preservation
was checked independently of successful tests. No additional issues found.

## NOT VERIFIED

Windows/Linux native runs, OS launcher end-to-end behavior,
other host versions/architectures, Codex account-backed main-catalog Superpowers
installation, actual company endpoint connectivity/network policy, exposed
workflow/hook/model behavior, full OS-keychain state or arbitrary filesystem/
network side effects. Earlier native capability results are inputs to the
candidate; the subsequent exact-candidate results are recorded separately above.

This completes the selected integration/packaging step. The original
cross-platform colleague delivery still needs its remaining native acceptance.
