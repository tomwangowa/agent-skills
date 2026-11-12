# Superpowers native capability proposal

Status: **APPROVED CASE STOPPED AT LOCAL PREFLIGHT; ZERO SOURCE/INSTALL ATTEMPTS**.
The [result](superpowers-native-preflight-1.md) records a stale expected CLI version.
Use the [corrected concrete proposal](superpowers-native-acceptance-r2-proposal.md)
for a new approval; do not resume this stopped manifest. Offline approval alone does not
approve native operations. Each external command gets one attempt; a retry
needs a new proposal and approval. No model session is included. Start with
Claude; Codex remains conditional on genuinely native-prepared official state.

## First proposed case: Claude official payload materialization

Use the discovered binary `$CLAUDE_BINARY`. Prior inventory
observed Claude Code `2.1.319`; stop if the local `--version` result changes.
The concrete [run manifest](superpowers-native-case.json) records the resolved
binary target/SHA-256, exclusive case directory, exact cwd/environment, selected
target, observer allowlist and single-attempt command vectors. Those directories
have been created empty for review; no native command ran. A changed binary or
version stops the proposed run. Do not copy personal settings, credentials,
notes or session history. Do not inherit Claude/Anthropic authentication or
API-key overrides. No shell aliases, broad logging or telemetry payloads.

These mutation vectors, with the absolute binary substituted for `claude`,
are the entire external budget, in order, at most once each:

```text
claude plugin marketplace add https://github.com/anthropics/claude-plugins-official.git --scope user --json
claude plugin install superpowers@claude-plugins-official --scope user --json
```

After source-add, stop before install unless the selected raw entry is exactly
the bundled Claude descriptor: external payload URL
`https://github.com/obra/superpowers.git`, full pin
`bb92a77741419a4ab5f06e711a283343f1ada0c3`, expected manifest `7.0.0`, and
canonical raw entry hash equal to `installer/providers.json`. Record the full
catalog commit and actual Git origin. A changed unrelated catalog commit is
acceptable only with the unchanged selected entry; a changed entry is not.

Allowed local observations are Python stdlib (`json`, `hashlib`, `pathlib`,
`os`, `platform`, `zipfile`), `git -C <isolated-catalog> config --local --get
remote.origin.url`, `git -C <isolated-catalog> rev-parse --verify HEAD`, and
these isolated native reads: `claude --version`, `claude plugin marketplace
list --json`, `claude plugin list --json`. Observe the complete returned
installation tree without following links; compare every file, manifest,
version, enabled state and user scope. Hash the complete tree using the
installer's `tree_hash` algorithm. Any native bookkeeping added to the tree
must be explained against source; do not add an ignore list to obtain a pass.
Do not execute payload hooks or scripts as observers.

Expected effects: network downloads of catalog and pinned payload, plus native
marketplace/registry/cache writes within the isolated directories and local
evidence files. No model token cost is intended. No real HOME/config write,
hook trust, plugin execution, enable/update/removal or cleanup of partial native
state is approved. Compare the known personal registry/config fingerprints
before/after without copying their contents. Stop on unexpected credential
requirements, writes, errors, identity/content changes or prompts outside this
scope. A zero command exit alone is not acceptance.

This is a direct **capability probe**, not an installer acceptance run. If the
payload materialization contract is understood and corroborated, review a
proposed `NativeAcceptance` tuple for host, full CLI version, macos, arm64,
catalog name/commit, raw entry hash, manifest version, full payload hash and
an evidence reference. Update target hash and add a real record only after that
review. Do not import any synthetic acceptance fixture. The current production
record list remains empty.

## Codex official case: prerequisite not yet met

Discovered binary: `$CODEX_BINARY`.
Audited adapter: `codex-cli 0.167.0`. A future case must use a fresh isolated
`CODEX_HOME` and a catalog prepared by Codex itself through its native `/plugins`
flow. This proposal does **not** approve an interactive model session or an
unknown initialization command. Until a concrete native preparation flow and
its effects can be reviewed, this branch remains **NOT VERIFIED / pending**.
Never copy or seed `.tmp/plugins`, `.tmp/plugins.sha`, installed cache or private
native sync state, and never rename or add `openai-curated` via Git marketplace
commands. Do not use an unqualified/global `plugin list`.

Once a separately approved native setup exists, exact read vectors are:

```text
codex --version
codex plugin marketplace list --json
codex plugin list --marketplace openai-curated --json
```

If any managed identity/commit/selected entry/manifest/hash observation is
missing, stop without install. A separately approved single direct vector
would be `codex plugin add superpowers@openai-curated --json`. Its JSON
receipt, native scoped inventory and cache root must agree; cache version must
be the current catalog commit's first eight characters, while the manifest
must independently be `6.3.0`. Apply the same exact record and full-tree rules.
This conditional description is not approval of setup or installation.

## Later unmodified installer case

After a real capability record and expected payload hash have been reviewed,
build a **new** exclusive candidate and record ZIP size, SHA-256, every input
hash and the selected acceptance evidence. The current R4 with empty acceptance
must remain unchanged. Prepare a new one-host isolated proposal with the exact
candidate hash, CLI binary/hash, environment, observer allowlist, menu answers,
and source/install vectors. Obtain approval before running that unmodified
candidate. Verify the actual native result, all installed bytes and enabled
state. A capability probe cannot close this step.

No existing `7.0.2` provider is touched by either proposed isolated case. Windows,
Linux, other architectures/CLI versions, exposed entries, model behavior,
hooks/MCP, integration and publishing remain outside this proposal.
