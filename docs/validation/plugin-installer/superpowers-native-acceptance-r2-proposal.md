# Corrected Claude official-source capability proposal

Status: **APPROVED AND EXECUTED; NATIVE INSTALL SUCCEEDED, SOURCE CONTRACT NOT ACCEPTED**.
See the [partial native result](superpowers-native-claude-run-2.md). Source-add and
install each ran once; no repeat or further mutation is authorized by this proposal.
This proposal replaces only the inconsistent CLI-version expectation and
isolated case directory in the original Claude capability case. The actual
binary hash was already correct. See [stopped result](superpowers-native-preflight-1.md).

The [concrete manifest](superpowers-native-case-r2.json) records the exact
binary target/hash, fresh isolated cwd/config/HOME paths, environment policy,
selected target, local observers and command vectors. The expected complete
version output is now **`2.1.321 (Claude Code)`**, verified by one local command
on the approved binary. Its SHA-256 remains
`abc9feeeca8091d51b623291e044cf0528c2f6b74e0c1d6ef671d52c73f7cd3c`.
A binary/hash/full-version mismatch still stops before downloads.

The only external mutation vectors are, in this order, at most once each:

```text
~/.local/bin/claude plugin marketplace add https://github.com/anthropics/claude-plugins-official.git --scope user --json
~/.local/bin/claude plugin install superpowers@claude-plugins-official --scope user --json
```

The displayed `~` means the launching account's home; actual argv uses the
absolute binary sealed in the manifest, before setting the child's isolated
HOME. No shell expansion or credentials from the personal environment are
used. Keep the minimal OS/executable environment plus the isolated overrides;
put temporary native files inside the case directory.

After source-add, stop before installation unless actual Git origin, full
catalog commit and the raw selected entry agree with the sealed target.
Selected payload URL: `https://github.com/obra/superpowers.git`; full pinned
commit: `bb92a77741419a4ab5f06e711a283343f1ada0c3`; expected manifest `7.0.0`;
entry hash:
`d85f0111dd6cfcd54268f46dbadbd54d4df344c160cda075134e2d35aae9f888`.
Do not refresh, substitute another catalog, or change the pin if the live
entry differs. A changed unrelated catalog commit alone is acceptable only
with the exact unchanged selected entry.

The original proposal's [local observer allowlist, write boundaries,
materialization checks and stop rules](superpowers-native-acceptance-proposal.md)
continue to apply: Python stdlib and isolated native list/version reads,
local Git origin/HEAD reads, complete returned-tree observation without links,
manifest/user-scope/enabled-state checks and full-tree hashing. Compare known
personal registry/config fingerprints before/after without copying contents.
Unexpected prerequisites, prompts, writes, bookkeeping or failures stop the
case with partial state retained. Do not retry, repair, uninstall or roll back.

Expected effects: catalog and fixed-payload network downloads, native
marketplace/registry/cache writes confined to the new isolated directories,
and local evidence files. No model session/token cost, hook trust, actual
skill execution, existing-provider change, Codex operation, integration,
commit/push or publishing is included. The original preflight evidence and
R4 archive remain unchanged.

This is a direct capability probe, not an unmodified candidate installer run.
After a successful probe, review the full content contract and proposed exact
native acceptance tuple before changing target hashes/records. Then prepare a
new candidate and separate installation proposal. Functional/model cases and
Codex native setup retain their independent approval boundaries.
