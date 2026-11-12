# Codex Official Catalog Variants Implementation Plan

> Execute in the current session without subagents. The user selected option 1
> (recognize Codex's actual official catalog and test offline), adding colleagues
> who use an existing company AI endpoint without a ChatGPT login. No new
> native/service operation, installation, commit or release is approved.

**Goal:** Recognize native `openai-curated` and `openai-api-curated` without
requiring ChatGPT login or reading/changing model endpoint credentials.

**Architecture:** Keep one Superpowers menu item and the existing schema 2
primary target. Resolve its effective catalog from exactly one native official
marketplace. Bind manifest, action selector, receipt and acceptance to that exact
name. Main and API catalogs never share acceptance by alias.

**Spec:** User-selected option 1 and
[observed native catalog](../../validation/plugin-installer/superpowers-codex-catalog-result.md).

**Global constraints:** Native inventory chooses the route; no endpoint URL or
auth-file guessing. Preserve existing Superpowers. Both/unknown/conflicting
catalogs withhold writes. Missing catalog guides native preparation. Keep
provider hashes unset, acceptance records empty and R5 immutable. Company
endpoint setup/connectivity and corporate network/proxy support are not inferred
from offline tests; endpoint setup is outside scope: the user clarified that installation must work without account login.

**Alternatives:** Forcing the main catalog fails in observed API mode. Selecting
by parsed auth/config risks credential handling and disagreement with native
policy. Native inventory is the selected approach; ambiguous results stop.

**Review focus:** catalog identity changes after consent; cross-catalog
acceptance reuse; wrong manifest/name/source/path; company settings or secret
leakage; no model/login/bootstrap requests for missing catalog.

## One deliverable: official route recognition

- [x] Add tests: provider-route planning and exact acceptance, selected provider manifest,
  wrong/ambiguous catalog rejection, UI receipt, post-consent route change.
- [x] Run new tests against the current code and retain their failure results.
- [x] Add pure native-route resolution in `providers.py`; use it in
  `hosts.py`, `planning.py` and `ui.py`, including dependencies and receipts.
- [x] Extend synthetic CLI fixtures with the API catalog and existing dummy
  company endpoint config; assert bytes and environment secrets are preserved,
  no login/model/startup command is issued and no secret appears in output.
- [x] Run all offline installer tests and catalog/package checks. Do not run
  network-dependent build/release gates or native CLIs.
- [x] Run same-session Codex review, document evidence/limits, no commit.
