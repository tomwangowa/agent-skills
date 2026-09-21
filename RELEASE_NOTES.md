# Release Notes

This file records meaningful changes by release batch. It is not a raw commit
log: entries should describe user-visible behavior, skill contracts, workflow
integration, or maintainer-facing repository changes.

## Label Definitions

Each entry uses two labels:

```text
[impact][area]
```

### Impact

- `major` — broad or contract-level change; may require migration or updated
  usage expectations. This does not automatically mean a SemVer MAJOR release.
- `minor` — backward-compatible capability or behavior expansion.
- `fix` — correction, synchronization, wording repair, or other narrow change.

### Area

- `core` — central skill behavior, workflow, or output contract
- `integration` — handoffs, routing, or cross-skill behavior
- `tooling` — scripts, catalogs, generators, or repository tooling
- `docs` — README, cheatsheet, roadmap, and other documentation
- `security` — security, privacy, license, or trust-boundary behavior

## Maintenance Rules

- Group changes by release batch, not by individual commit.
- Keep the `Unreleased` section at the top for the next release batch.
- Use SemVer with a `v` prefix: `vMAJOR.MINOR.PATCH`.
- Use `Added`, `Changed`, `Fixed`, `Deprecated`, `Removed`, and `Security`
  headings only when that release has entries in the category.
- Every Traditional Chinese entry must have a corresponding English entry in
  the same category with the same labels and meaning.
- Record meaningful changes rather than every commit. Include commit IDs when
  they clarify the release boundary or make a change easy to trace.
- A `major` impact label describes the scope of a change; only a breaking
  change to an established contract requires a SemVer MAJOR bump.

## [Unreleased]

No changes have been collected for the next release batch yet.

## [v0.1.0] — 2026-09-21

**Release baseline:** `7a34b63`, `a249028`

### 繁體中文

#### Changed

- `[major][core]` 將 `deep-reading` 重整為漸進式閱讀流程，加入 Auto、Quick、Deep、Deep Dive 模式，以及文件來源、證據判定、推導、連結與保留重點等階段。
- `[major][integration]` 定義 `arxiv-digest` 與 `deep-reading` 的交接契約；深讀只在使用者確認 Step 5c 後啟動，沿用已驗證的 metadata，避免重複 digest，並把結果附加回同一份筆記。

#### Fixed

- `[fix][docs]` 更新 README、roadmap 與 cheatsheet，反映 `references/` runtime 指引和新的 `deep-reading` 整合方式。

### English

#### Changed

- `[major][core]` Reworked `deep-reading` into a progressive reading workflow with Auto, Quick, Deep, and Deep Dive modes, plus provenance, evidence verdicts, derivation, connection, and retention stages.
- `[major][integration]` Defined the handoff contract between `arxiv-digest` and `deep-reading`; deep reading starts only after the user confirms Step 5c, reuses verified metadata, avoids repeating the digest, and appends the result to the same note.

#### Fixed

- `[fix][docs]` Updated the README, roadmap, and cheatsheets to reflect `references/` runtime guidance and the new `deep-reading` integration.
