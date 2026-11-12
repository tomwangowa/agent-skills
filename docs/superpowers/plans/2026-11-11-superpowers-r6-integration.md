# R6 verified Superpowers integration

Authorization: user selected option 1 to integrate existing native results and
build a new exclusive candidate. No new native/service operation, commit or
release is included. Existing approved source/preservation rules remain.

Use the existing schema and strict source verification. Claude's two actual
2.1.322 cases kept Git metadata; this change does not implement an archive
exception or infer support for untested platforms or versions.

- [x] Add production acceptance tests and watch them fail on empty metadata.
- [x] Promote independently corroborated payload hashes and add exactly two
  macOS/arm64 capability records: Claude 2.1.322, official catalog, both auth
  cases; Codex 0.167.0, API-curated catalog, no-account case. Main Codex catalog
  has no transferable record.
- [x] Include only the two sanitized published evidence summaries in the ZIP,
  with resolvable record references and input/file provenance hashes; never
  include native profiles, auth storage or raw session logs.
- [x] Check exact CLI/catalog/platform/architecture gates, unknown evidence
  references, and record/evidence disagreement. Keep provider selection optional.
- [x] Update packaged README with current enablement and remaining setup limits.
- [x] Run installer suite, package/config checks, same-session Codex review and
  bundle checks. Build R6 exclusively, confirm reproducibility, exact archive
  provenance, relocated runtime/gates, shell syntax and extracted-content leak scan.
- [x] Publish local validation report, checksum and preservation results.

Native capability and an actual unmodified candidate installation remain
separate evidence layers. Windows/Linux, actual company connectivity and skill/
model behavior are not promoted by this change.

The initial R6 ZIP retained four non-secret auth-status file fingerprints that
triggered generic-key scanner findings. All four were recomputed and verified
as hashes. Original evidence stays untouched; the distributed summary now omits
raw-log fingerprints/workspace pointers. Preserve R6; deliver a new R7 ZIP.
