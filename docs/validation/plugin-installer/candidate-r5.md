# Installer candidate R5

Date: 2026-11-10. Scope: build and verify a new local archive containing the
[own-source regression repair](own-source-regression-fix.md). No product code
was changed during packaging. The later [2026-11-11 native cases](macos-r5-native-results.md)
verified `quality-gates` installation on both macOS CLIs. The subsequent
[14-item batch](macos-r5-remaining-results.md) verified the remaining own packages.
Overall release, Superpowers, other platforms and runtime behavior remain
unverified. The packaging evidence below describes the earlier, offline-only
build step.

## Artifact

- Archive: `dist/agent-skills-installer-fe55c04-candidate-r5.zip`.
- Size: 51,800 bytes; 25 ZIP entries.
- SHA-256: `3047be151e9e89644a35d6542356badf90bf4e34dd3f7497d14a13c05a932ace`.
- Checksum file: `dist/agent-skills-installer-fe55c04-candidate-r5.zip.sha256`.
- Source HEAD: `fe55c04bf9202fe82f1a68b7f5985305c82249f0`.
- This is a build from uncommitted working-tree inputs. HEAD alone does not
  identify the archive; its embedded provenance records exact input hashes.
- Machine-readable results: [candidate-r5-evidence.json](candidate-r5-evidence.json).

Build command:

```bash
python3 scripts/build_plugin_installer.py --output dist/agent-skills-installer-fe55c04-candidate-r5.zip
```

The existing builder refuses an occupied output path. A second build went to a
separate temporary path and matched the saved R5 archive byte for byte.

## Difference from R4

The entry list is identical. Only two entry contents changed:

- `runtime/agent_skills_installer/planning.py`: the approved own-source fix.
- `provenance.json`: the changed planner's input and packaged-file hashes.

The catalog, dependencies, launchers, provider settings and native acceptance
index are identical to R4. All 16 own-package payload hashes still match their
local source trees. The two Superpowers targets remain unchecked with unknown
expected content hashes, and production acceptance records remain empty.
The proposed archive-source policy was not implemented or enabled.

## VERIFIED

The saved R5 archive itself was checked, not just another test-built archive:

| Check | Result |
| --- | --- |
| ZIP CRC, unique safe entry paths, regular-file modes and exact allowlist | 25 entries passed; no tests, private settings, credentials files or Git history included by the allowlist |
| Embedded packaged-file hashes | All 24 hashes passed; provenance excludes itself |
| Embedded source-input hashes | All 28 inputs matched the working tree |
| Catalog | Schema 2; 18 entries; 16 own-package payload hashes independently recomputed and matched |
| Planner | Packaged bytes exactly match the repaired working-tree file |
| Reproduction | A separate temporary build matched R5 byte for byte |
| Relocated help | Isolated Python, cleared `PYTHONPATH`, cwd outside the repo, path with spaces/CJK; exit 0 |
| Relocated own-source cases | Real bundled UI/planner/executor with synthetic CLI boundaries, both Claude and Codex: missing shared source proposed once; source refusal followed by installation approval returned partial exit 1 with zero native mutation calls and retained files |
| Provider gate | Superpowers hashes remain unknown, defaults unchecked and acceptance records empty |
| POSIX launcher syntax | Both packaged shell launchers passed `bash -n` |
| Existing bundle suite | `PYTHONPATH=runtime python3 -m unittest discover -s tests -p 'test_installer_bundle.py'`: 6 passed, exit 0 |
| Secret scan | Gitleaks 8.30.1, `dir` mode on the extracted archive, redacted output: 0 findings, exit 0 |
| Checksum sidecar | `shasum -a 256 -c agent-skills-installer-fe55c04-candidate-r5.zip.sha256` from `dist/`: passed |

The source-fix regression suite is recorded separately in the repair report.
It was not rerun during this packaging-only step, since product code did not
change; the six bundle checks and exact-artifact exercises above ran fresh.

The first preservation audit omitted the newly authorized checksum sidecar
from its expected-new-file set. That audit assertion failed; the expected set
was corrected and rechecked without changing any product input or archive.

## Preserved state

All four older ZIP files remain unchanged. In particular, R4 SHA-256 remains
`46994537305c0f97268aa9cfbed825378b9b485130ff25732b57a3b8e304a549` and it
still contains the pre-repair planner. Existing runtime/plugin inputs, saved
native evidence, HEAD, staged state and four stash entries were retained.
No commit, push, source refresh, native installer or model call was performed.

## NOT VERIFIED

- No new native Claude/Codex installation or external service operation ran.
- Native Windows/PowerShell and Linux installation, real dependency managers,
  hook trust, MCP, restarted-host entries and model workflows remain unverified.
- Source refusal was exercised with synthetic process boundaries; no claim is
  made that a real native inventory command has no remote side effects.
- Launcher syntax and isolated Python exercise do not establish three-platform
  acceptance. R5 is a local candidate, not an accepted colleague release.
- No new acceptance record or expected Superpowers payload hash was supplied.
- Repository-wide gates that may run `npm ci` were not executed; they remain
  outside the explicitly offline scope.
