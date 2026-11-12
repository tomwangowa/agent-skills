# Codex official catalog initialization result

Date: 2026-11-11. The user approved the exact
[catalog probe](superpowers-codex-catalog-proposal.md). One native App Server
startup completed with exit 0 on macOS arm64, Codex CLI 0.167.0. It prepared
the official catalog without an installation request or model conversation.
This is catalog preparation evidence, not Superpowers installation acceptance.

## VERIFIED

- Fresh isolated HOME/CODEX_HOME/XDG/TMP and cwd outside Git; no personal
  credentials or configuration copied. Only `initialize` and `initialized`
  protocol messages were sent. One initialize response was retained; stderr
  was empty. The native process closed normally after stdin closed.
- The native snapshot is at `CODEX_HOME/.tmp/plugins`, with receipt
  `d420d13051bffe4543ed39e30fa46b87148e47dd` followed by a newline. Its clean
  Git checkout HEAD matches the receipt. No named Git origin exists; the
  matching-version producer initializes Git and fetches directly from a URL.
  The checkout/producer support the native Git path; individual wire requests
  and possible earlier internal transport attempts were not traced.
- Native marketplace inventory exposes **`openai-api-curated`** in this fresh
  unauthenticated state. The matching-version source explains this auth-based
  selection. The installer currently accepts only `openai-curated`; it does
  not yet support this observed route.
- Both `.agents/plugins/marketplace.json` (`openai-curated`) and
  `.agents/plugins/api_marketplace.json` (`openai-api-curated`) contain exactly
  one Superpowers entry, pointing at `./plugins/superpowers`. Both raw entry
  hashes equal the candidate's existing entry hash:
  `fcf75e5ef3e9fb29b75714eaf2727ea32b412037736dd92b744ab437d1a3ddc1`.
- The catalog payload's native manifest is Superpowers **6.3.0**, with 73 files
  and no symlink. Its observed complete tree hash is
  `2bc88a8ad42d3b2a5f2b7f0b6711b0ae4d18895bfa870dcfeb7c9fc5d31fdba0`.
  This is an observation from this download, not an independently accepted
  expected hash or a verified installed payload.
- Each of the three approved final native reads ran once and returned exit 0.
  All 52 protected product/artifact/prior-evidence file hashes, four named
  original settings fingerprints, HEAD, four stashes and staged-file list
  match the pre-run baseline. No commit, cleanup or native retry occurred.

## Query limitation and local verification correction

Both approved `plugin list --marketplace ... --json` commands returned empty
`installed` and `available` arrays. **The proposal omitted `--available`.**
Codex 0.167.0 deliberately omits uninstalled entries without that flag
(`cli/src/plugin_cmd.rs` 105-117, 489-510). These empty arrays do not establish
that Superpowers is absent or ineligible. Physical catalog entries were read
locally instead; no corrected native query was run. A later native proposal
must explicitly include `--available` if it needs that observation.

The local preservation verifier initially expected a named `origin` and
stopped with Git-config exit 1. Inspection of the retained config and the
matching-version producer showed the native checkout has no named remote.
The checker now records that observed absence; no catalog repair, download
or native action was repeated. The corrected local verifier returned exit 0.

## Evidence and NOT VERIFIED

Evidence root:
`.superpowers/sdd/2026-11-11-superpowers-codex-catalog/prepared-wiw4qxz0/`.
It retains the approval/run manifest, once markers, version, sent protocol,
native stdout/stderr, startup result, all three read results, downloaded state,
pre-run hashes and repeatable **local-only** `verify_local.py` with
`verification.json`. Published summary:
[superpowers-codex-catalog-result.json](superpowers-codex-catalog-result.json).

Not verified: native `--available` output; Superpowers install/enable/receipt;
independent Codex payload reference; installer support for API-curated catalogs;
Claude's current-version archive transition; Windows/Linux; exposed workflow,
hook or model behavior. Named-file preservation is not a whole-computer or
complete network side-effect audit. No model request was sent by the observer;
wire-level billing was not audited.

The probe changed no product code, provider descriptor, accepted hash or
acceptance record, and did not rebuild R5. Supporting the observed catalog
name and any further native operation require their own explicit scope.
