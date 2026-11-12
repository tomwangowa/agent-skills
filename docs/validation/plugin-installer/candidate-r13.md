# Installer candidate R13: a verified Claude catalog archive

R13 permits the identified Claude official catalog archive at commit
`dceb15d50832e6adf380bedc26dde03d251324b9` to enter the existing Superpowers
installation flow. It verifies the complete locally present archive tree
against a fixed SHA-256 digest, requires the active Claude configuration root,
rejects links and unexpected files, and retains the existing pinned entry,
payload, CLI/platform and post-install checks. Unknown commits and changed
files remain unverified. This is a candidate with offline verification; native
R13 Superpowers installation and runtime behavior have not been tested.

The GitHub API returned marketplace JSON blob
`3482b58b0502334f140975834731b9b6984ee98b`, matching the Git blob hash of the
local catalog. A public [fixed-commit source archive](https://github.com/anthropics/claude-plugins-official/tree/dceb15d50832e6adf380bedc26dde03d251324b9)
was compared file by file: all 627 local files matched, while 15 upstream-only
files were under `.github/`. No local files were altered. The fixed tree digest
`cd386993659390165dd164509073f60916b11238b8f932ef83dc55e016f903f4` hashes
exactly the 627 files; only the root `.gcs-sha` is separately validated and
excluded from that tree digest. The implementation does not generally ignore
`.github` or other added files.

The archive is R13 ZIP (local artifact; not included in the repository)
with SHA-256 (local artifact; not included in the repository):
`27c9b51dfe66daeb32ce3d89b13aab37863823f94463c7443d910f17915fa86e`.
A separate build was byte-identical and all bundled input/payload hashes were
verified. The relocated bundle's planner proposed Superpowers for the observed
local archive, without running Claude. An actual terminal replay with fake
hosts passed existing installation and removal flows. Exact extracted archive
Gitleaks scan found zero secrets.

The static archive digest applies only to this snapshot. A different official
catalog revision is withheld until independently compared and added. Native
R13 installation, post-install source behavior, retained credentials or settings,
Windows/Linux and restarted skill behavior are unverified; Git-form acceptance
is not proof that those archive-form scenarios work. No native host command,
model request, personal setting write, commit or push was run in this batch.

Final complete installer suite: **163 tests, 162 passed and one PowerShell
skip**. The focused archive tests cover the accepted fixed tree, modified
files, an unknown commit, a symlink and a different Claude profile. Removing
the new archive acceptance causes the positive test to fail; modified state
is rejected even after an installation plan has been sealed. These synthetic
tests do not establish native archive installation success.
