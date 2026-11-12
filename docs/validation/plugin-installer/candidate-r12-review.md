# R12 bounded fix review

No findings. Adversarial check: no additional issues found in the bounded fix.

Self-review in same Codex session: commitment / recency / framing bias not
fully controlled. No subagent, external reviewer or native host was used.

## Review scope

R11 archive to R12 changes in `removal.py`, `removal_ui.py`, `hosts.py`, the new
`tests/test_installer_removal_regressions.py`, and the installer README. The
builder and other runtime modules are unchanged. This is L2 behavior because
the checks gate deletion, even though this batch is entirely offline.

## Adversarial checks and assumptions

1. A lexical path is not a profile identity. Identical registrations and
   payload bytes in a second profile previously passed. New preconditions
   include the physical destination and filesystem identity. Regression tests
   redirect the ancestor link and replace the directory at the same name;
   both now reject. Stable links still pass. The packaged replay switches
   profiles at confirmation and observes zero fake uninstall calls.
2. Unknown origin does not grant ownership. The parser retains complete
   untrusted records; removal still checks canonical source/provider and the
   exact cache/manifest. Same-name local origin remains withheld. Missing
   `version` still causes a host error with zero mutation. Fresh post-removal
   inventory must preserve every other record, including local plugins.
3. Success must refer to the approved profile. UI identity guards run before
   native recheck/verification queries, and core checks reject a profile switch
   even if another profile reports the target absent. They do not prevent a
   change between the final check and the native command. No atomicity claim
   is made; adversarial inode reuse and platform-specific filesystem identity
   semantics are not established.
4. Tests must fail without the fix. Nine new behavior tests were run against
   R11 first: seven failed. Assertions cover plan rejection, zero uninstall
   calls, successful identified removal, retained unrelated files/records and
   refusal of malformed metadata. Stable-link and malformed-input tests also
   preserve behavior that already worked.

## Verification and limits

The complete installer suite passed 158 of 159 tests, with one PowerShell
skip; 42 targeted tests, 14 package tests and 15 config tests passed. Python
AST parsing, catalog validation and tracked whitespace checks passed. The
relocated archive passed four fake removal cases and the installation replay.
See [candidate verification](candidate-r12.md) for archive checks and limits.

This review does not establish native R12 behavior, Windows/Linux execution,
real credential cleanup, full data-directory retention or concurrent-change
atomicity. Earlier R11 native evidence has not been reused as R12 acceptance.
