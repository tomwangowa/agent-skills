# Official-source same-session review

Later evidence: the [archive investigation](superpowers-archive-source-investigation.md)
reproduced an own-marketplace-missing planning regression introduced by source
sealing. It remains unfixed in R4 and was outside the earlier passing cases.
The original no-open-findings assessment below was the state of that earlier
self-review; it is not a current clean-review claim.


Self-review in same Codex session: commitment / recency / framing bias not fully controlled.

Risk: **L2**. The installer constructs writes to host marketplace/installation
state and must preserve existing providers and user caches. Review used
`quality-gates:code-review-codex` in the current session, as explicitly selected
in the approved plan. No agent, external reviewer or retired Gemini was used.
No commit is proposed or authorized by this report.

## Findings resolved during implementation

- A `ready` label with only catalog name/entry/commit could satisfy installation
  acceptance without full provenance observations. The pure gate now requires
  the complete snapshot and exact descriptor/payload values. Regression cases
  remove each required observation and fail before the fix.
- A malformed installed row in an unknown Codex provider could poison global
  inventory and block an unrelated own package. Parsing now contains that
  provider-local failure, marks Superpowers absence unknown and continues
  known own-package inventory. Actual global native/schema failure remains
  host-wide uncertainty. The malformed-row regression failed before the fix.
- A provider appearing at the source-consent checkpoint could still trigger
  redundant official source-add. Source actions now seal the provider target,
  snapshot, CLI/platform/architecture and plugin state; the UI rereads them
  before mutation. A filesystem-backed transcript reproduces the race and
  asserts zero attempted mutations after the fix.
- A malformed native acceptance index escaped the UI's error handling. The UI
  now reports failure before invoking a native command. A real temporary
  malformed index demonstrates the pre-fix exception and post-fix zero calls.
- External defaults were not enforced when loading a bundled catalog. A
  Superpowers target with `default_selected=True` is now rejected. The
  regression failed before the validator change.
- Planning's fallback called filesystem provider inspection, violating its
  pure decision boundary. It now consumes observations or returns conservative
  unknown/missing-source status. The regression forces filesystem access to
  fail and verifies that planning does not touch it.

No unresolved High or Medium finding remains after the checks recorded in the
offline evidence report. This is a local self-review, not independent review.

## Adversarial checks and assumptions

1. **Native catalog shape/origin** could drift or be incomplete. Tests exercise
   missing raw source, missing/invalid commit receipt, wrong entry/payload,
   alternative providers and provider-local malformed output. Only the audited
   Codex CLI is writable; no URL is manufactured in native inventory. Real
   official-source materialization and initialization remain unverified.
2. **State can change after consent.** Real temporary transcripts change the
   catalog commit/payload/config root, add a competing provider and add orphan
   or symlinked caches. They verify zero native install/source attempts after
   rejection. Concurrent changes inside the native command remain a race;
   postconditions detect mismatches without automatic rollback or retry.
3. **Native zero exit may describe a partial installation.** Receipt tests
   check malformed/empty output, wrong ID/cache prefix/root/manifest/content,
   source/state mismatch, disabled installation and links. Claude partial
   result transcripts preserve actual files, report unverified and attempt
   installation once. No passing exit alone establishes success.
4. **Synthetic acceptance is not evidence.** Real bundle relocation imports
   only the bundled runtime and confirms schema 2, both observed target
   versions, unchecked defaults, unknown payload hashes and empty production
   acceptance. No synthetic fixture is copied into a production record.
5. **Compatibility must be exact.** Pure tests change CLI, platform,
   architecture, entry, version and content tuple members; only an unrelated
   historical catalog commit may differ. Registration and common major
   version are not compatibility evidence.
6. **Tests must observe effects.** Red/green failures established the missing
   behavior; filesystem-backed tests assert real file retention/creation,
   actual plans, attempted native vectors and returned exit/status. Only the
   external process boundary is replaced in UI cases. None proves that the
   actual host exposes or follows a skill.

## Scope and verification boundary

Reviewed installer models/providers/catalog/hosts/planning/receipts/UI, their
execution/dependency integration, bundle builder, host-specific metadata,
acceptance index, changed tests, package documentation and native/function
proposals. The original R3 receipt/executor protections were retained and
regression-tested; plugin payloads and shared config/migration runtime were
not modified.

Syntax, regression, bundle/provenance, local-link and scoped source-scan results
are listed in [offline evidence](superpowers-official-sources-offline.md).
Windows PowerShell, native Linux/other architectures, new native/model calls,
hooks/MCP, every real workflow branch, repository-wide server/npm gates and
independent review remain **NOT VERIFIED**.
