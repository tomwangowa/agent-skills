# Offline investigation proposal: Claude official archive source

Status: **APPROVED BY USER #1; OFFLINE INVESTIGATION AND DESIGN DRAFT DELIVERED**.
See [findings and alternatives](superpowers-archive-source-investigation.md),
[proposed design](../../superpowers/specs/2026-11-10-claude-archive-source-design.md)
and [test matrix](superpowers-archive-source-test-matrix.md). Approval of this
investigation does not approve the new design, implementation or external runs.
The [approved capability case](superpowers-native-claude-run-2.md) demonstrated
native installation, but invalidated the assumption that official-catalog Git
metadata persists. The next useful outcome is a reviewable source-contract
design and failure-test matrix, not a permissive marker check or another
unapproved download.

Use only the captured case, anonymized observed fixtures, current installer
source, approved design/plan and available local primary documentation. Do not
read personal sessions/credentials or unrelated repositories. Do not invoke a
model host, network service, native source/install command or payload script.
If a primary-source explanation is unavailable locally, state that gap and
prepare an exact additional-research/probe proposal rather than guessing.

The investigation should answer:

1. Which facts survived the transition: configured URI, prior verified Git
   origin/HEAD, native-managed directory, current `.gcs-sha`, unchanged raw
   selected entry, pinned native registry commit and complete payload hash?
   Separate direct observations from inferred host behavior.
2. What can establish official archive provenance without trusting a filename
   or matching directory name alone? Distinguish an observed in-run transition
   from an already archived catalog with no prior verified Git snapshot.
3. What evidence is still needed to explain materialized payload bytes against
   the pinned upstream tree? Do not promote the observed full hash into an
   accepted expected hash without resolving that contract.
4. Which schema/snapshot/recheck/postcondition changes, if any, would be needed?
   Preserve exact CLI/platform/architecture acceptance, existing providers,
   one-attempt consent and provider-local failures. An unknown archive form,
   wrong marker/source/entry/pin/hash/root or stale approval must still refuse.

Deliver a proposed source contract with alternatives/trade-offs, a precise
normal/failure matrix grounded in the genuine fixture, and explicit remaining
native evidence requirements. Obtain design/implementation approval before
editing product behavior or acceptance records. Preserve R4 and native case
files. Any later causal probe should snapshot the local filesystem immediately
after each native vector; the current case cannot identify the transition's
single triggering command.
