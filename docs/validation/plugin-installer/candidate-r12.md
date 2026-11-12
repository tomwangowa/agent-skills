# Installer candidate R12: removal profile identity and local-plugin coexistence

Date: 2026-11-12. **Both R11 review findings are fixed and verified offline,
including the relocated archive's installation and removal entry points.
No real Claude/Codex invocation or model request ran in this batch. R11's
native removal acceptance remains specific to R11; R12 native acceptance
has not run.**

## Fixes

The removal preview now seals the configuration directory's resolved path,
device and inode, together with its existing native registration and protected
project payload checks. A stable ancestor symlink remains usable. Redirecting
that link to an otherwise identical profile, or replacing the configuration
directory at the same path, invalidates approval. The UI checks identity before
fresh native queries; the planner and success verifier check it too. Direct
configuration/cache symlinks remain ineligible. A changed target requires a
new preview, without automatic retry or rollback.

Complete installed records from an unrelated local/file/unknown marketplace
now remain in inventory with an untrusted `source=None`, instead of failing
the entire host. An identified package can be removed while those records and
files stay unchanged. This does not authorize unknown-origin targets: a
same-name unknown provider remains withheld. Missing required metadata and an
unidentified `tomwangowa` marketplace still stop writes.

## Artifact

- R12 ZIP (local artifact; not included in the repository)
- SHA-256 (local artifact; not included in the repository)
- Size: **72,221 bytes**; SHA-256:
  `852f66279c69ccaeab3a91971112c660db7a44043a5e7962072b3037a985921a`.
- 32 entries, 31 payload hashes and 35 input hashes. A separate repeat build
  was byte-identical; all provenance hashes matched current inputs/payloads.
- Catalog, provider mapping and provider acceptance are byte-identical to R11.
- [Sanitized evidence](candidate-r12-evidence.json),
  [same-session review](candidate-r12-review.md).

## Verification

| Check | Result |
| --- | --- |
| New regressions against R11 | nine tests ran, seven failed before product changes |
| Targeted regression/removal/inventory checks | 42 passed after both fixes |
| Complete installer suite | 159 tests: 158 passed, one PowerShell skip; exit 0 |
| Package/config checks | 14 package tests and 15 config tests passed |
| Catalog, Python parsing, tracked whitespace | passed |
| Relocated removal, actual keyboard menu, fake native CLI | empty: exit 0 / zero uninstalls; cancel: exit 130 / zero; confirmed: exit 0 / two; profile switch: exit 1 / zero |
| Fake removal preservation | unrelated local plugin, project registration/shared payload, journal settings, notes, work records and plugin data retained |
| Relocated installation | two fake installs and one fake up-to-date update; phase bars, blank separators, live no-newline prompt, JSON capture and existing journal reuse passed |
| Exact archive extraction Gitleaks | zero findings, exit 0; default rules, no ignore file or allow comments |
| Preservation | eleven earlier ZIPs, five personal files, HEAD, four stashes and staged state unchanged |

The relocated launcher tests execute the shipped archive through
`install-macos.command` -> `install.py` -> its bundled runtime in a real PTY.
The only host programs on their PATH are controlled fake CLIs. The profile
switch replay redirects an ancestor symlink after the removal preview and
before approval; both real fixture profiles remain byte-identical, with zero
uninstall calls. These checks prove the two fixes at the process boundary,
without claiming native host acceptance.

**VERIFIED:** the two reported regressions, retained unknown-origin records
without granting removal permission, affected offline behavior, packaged
entry points, deterministic archive/provenance, secret scan and preservation.

**NOT VERIFIED:** native R12 installation/update/removal; native Windows/Linux
and PowerShell; Codex removal ownership; real saved-option/secret cleanup and
data retention; restarted model/hook/MCP behavior; atomic protection against
concurrent filesystem changes or adversarial inode reuse. Path/device/inode
checks detect observed directory changes but do not form an OS transaction.
No commit, push, publication, production sync, credential copy or restoration
of earlier trial state occurred.

The [R11 native batch](r11-native-removal.md) is preserved separately and was
not repeated or relabelled as R12 evidence.
