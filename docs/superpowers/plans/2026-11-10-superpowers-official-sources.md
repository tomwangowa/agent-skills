# Superpowers Official Sources Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:executing-plans for the preserved inline execution method. superpowers:subagent-driven-development is not selected; do not delegate. Steps use checkbox syntax. **APPROVED: user #1 on 2026-11-10 authorizes offline implementation. Commit, native/model runs and delegation remain unauthorized.**

**Goal:** 將 Superpowers 改為各 CLI 官方來源優先，分別辨識來源、控制安裝能力與記錄功能驗收，不破壞現有 R3 的自有套件流程。

**Architecture:** 沿用標準函式庫 installer；新增純資料／決策 `providers.py`，由 host adapter 盤點目錄與 provider 的已觀察證據，plan 封存 snapshot，executor 執行一次並以實際結果驗證。未準備好的 Codex 官方目錄只顯示原生指引。

**Tech Stack:** Python 3.11+ stdlib、frozen dataclasses、既有 unittest、原生 CLI；不加 pip/npm 依賴。

**Spec:** [同輪交付的補充設計](../specs/2026-11-10-superpowers-official-sources-design.md)。使用者要求本輪同時完成設計與計畫；兩份共同審閱後才能實作，不能略過書面設計確認。

## Global Constraints

- 保留來源優先、不同版本、分開驗收；Superpowers 預設不勾選；既有 provider 不更新、啟用、替換或降版。
- 所有 source／install 寫入先預覽與確認；不得重試、rollback、改名官方目錄或直接寫入 native managed state／installed cache。
- Codex 官方來源只能用宿主已準備且可核對的目錄；不發出 `marketplace add`／refresh 來冒充原生初始化。具名盤點不擴大到 unqualified/global catalog。
- `7.0.0`／`6.3.0` 是目前 snapshot；候選包固定預期來源證據。缺 commit/hash/native acceptance 時停用該項，不猜值。
- 使用者於 2026-11-10 以 #1 同時核准補充設計、計畫與離線實作；沿用同 session native，不派子代理、不 stage/commit/push，保留四份 stash、R3 與既有證據。
- 原生安裝、模型／子代理、hooks 信任、外部 reviewer 及 integration 各需另列具體批准。不要把文件／離線測試當成這些證據。
- 英文程式輸出／註解；stdlib；其他平台與自有套件的既有界線不擴大。

## Review Focus

1. 官方目錄沒有 `marketplaceSource`：不得填預期 URL 當觀察值；Task 2 固定局部 unverified，其他已知套件可繼續。
2. 維護者 provider `7.0.2` 已存在：不得因官方版本較舊再裝一份；Task 2/3 固定保留與零寫入。
3. 確認後官方目錄 commit 或 CODEX_HOME 改變：Task 3/4 固定 snapshot 失效與零 mutation。
4. Codex receipt cache version 是 SHA 前 `8` 字元、manifest 是 `6.3.0`：Task 3 固定分開核對與錯配拒絕。
5. 原生同步狀態缺少、symlink／cache 或部分安裝已存在：Task 3/4 固定保留、失敗不重試，不能以補寫 metadata 解決。

## Files and interfaces

路徑基準 `runtime/agent_skills_installer/`。保留模組責任，不更動 plugin payload 或 shared preference/migration runtime。

| 檔案 | 預定變更 |
| --- | --- |
| `models.py` | 追加 `ProviderSource`、`ProviderReadiness`、`NativeAcceptance` 及相容的 dataclass 尾端欄位 |
| `providers.py`（新增） | schema 2 target／native acceptance 的純解析、合格組合判定；只依賴 stdlib/models，避免循環 import |
| `catalog.py`、`installer/providers.json` | 分 host 官方 descriptor；catalog schema 2；自有 source 語意不變 |
| `hosts.py` | 觀察 provenance、commit、原生官方 readiness、preserve-only provider；不作寫入 |
| `planning.py`、`receipts.py` | readiness／acceptance／snapshot 門檻；擴充官方 receipt 與 Claude payload 驗證 |
| `ui.py` | 顯示 host-specific 來源、準備／未驗證原因，分開安裝與功能結果 |
| `installer/provider-acceptance.json`（新增） | schema 1、初始 `records: []`；不可把 synthetic case 寫成 native record |
| `scripts/build_plugin_installer.py` | 新模組／驗收索引 allowlist、catalog schema 2、輸入指紋；保持純離線 |
| `installer/README.md`、根目錄雙語 README | 來源差異、既有版本保留、Codex 原生準備及分層結果說明 |
| `tests/test_installer_*.py`、`tests/fixtures/installer/` | 下列來源／plan／receipt／transcript 行為測試；observed 與 synthetic 分開 |

類別欄位以補充設計為準。`ProviderReadiness.status` 是 `ready|needs-native-setup|unverified|preserved`，`snapshot` 是排序後的字串 pair tuple；`Inventory.provider_readiness` 按 plugin 名稱索引，保持既有建構呼叫有效。`PluginSpec.provider=None` 僅可沿用自有套件路徑，不能讓外部套件跳過來源檢查。

原生驗收資料精確使用 `catalog_name`、`catalog_commit`、`entry_hash`、`manifest_version`、`content_hash`、`evidence_ref` 等設計欄位名稱。下文的「entry hash／content hash」是這些欄位的說明，不能另造不同拼法的序列化 key。

後續任務共用介面：

```python
# providers.py — pure parsing/decision; no native or filesystem calls
def provider_targets(data: dict) -> tuple[PluginSpec, ...]: ...
def parse_native_acceptance(data: dict) -> tuple[NativeAcceptance, ...]: ...
def target_accepted(spec, records, cli_version, platform, architecture) -> bool: ...
def installation_accepted(spec, readiness, records, cli_version, platform, architecture) -> bool: ...
# hosts.py — local/native inventory observations only
def inspect_provider(spec: PluginSpec, inventory: Inventory) -> ProviderReadiness: ...
def read_inventory(host, runner, *, provider_specs=()) -> Inventory: ...
# planning.py — original positional inputs retained
def make_plan(catalog, inventories, selected, updates, tools,
              *, acceptance=(), platform='', architecture='') -> Plan: ...
# receipts.py — original R3 call supported; explicit new parameters
def verify_codex_install(action, spec, result, inventory,
                         *, readiness=None) -> InstallReceipt | bool: ...
def verify_claude_install(action, spec, inventory,
                          *, readiness=None) -> bool: ...
```

`installation_accepted` 精確比對 host／CLI／平台／架構／catalog name／entry hash／manifest version／content hash 及非空 evidence reference；不是版本範圍或同 major 推論。紀錄的 catalog commit 是原生證據時點，不能只因其他套件使目錄換了 commit 就要求重驗相同 payload。當前目錄 commit 仍須可驗證並納入 snapshot；確認後的任何 snapshot 改變會停止操作。新安裝 Action 額外封存 `provider_state`（snapshot JSON）、`provider_target`（descriptor JSON）、`platform`、`architecture`；沿用原 `cli_version`／`config_root`。

`target_accepted` 比對相同的靜態 target 組合，供缺少 Claude 官方目錄時決定能否提出 source-add；`installation_accepted` 再要求已觀察的 readiness/source snapshot 相符。兩者不能合併成「任何非空 acceptance 皆可寫入」。`source_action(host, source, kind)` 保持原簽名，以明確 host/URI 對應官方 Claude 名稱；Codex 官方來源與維護者來源的 mutation 直接拒絕，不沿用 `superpowers-dev` 推導。

## Task 1: Versioned targets and exact acceptance metadata

**Files:** Create `providers.py`, `installer/provider-acceptance.json`, `tests/test_installer_provider_sources.py`; modify `models.py`, `catalog.py`, `installer/providers.json`, catalog/bundle tests.
**Consumes:** schema 2 official descriptor table in spec; existing `PluginSpec` and catalog generation.
**Produces:** `provider_targets`, `parse_native_acceptance`, `target_accepted`, `installation_accepted` and data types above; catalog schema 2 serialization/roundtrip. Acceptance schema remains 1.

- [x] **Step 1:** Write `test_wrong_catalog_payload_pair_is_rejected`, `test_external_missing_provider_cannot_become_writable`, `test_acceptance_requires_exact_tuple`, `test_unrelated_catalog_revision_keeps_same_payload_acceptance`, `test_schema_one_catalog_is_rejected`. Use literal wrong-source/payload-commit/entry/CLI/platform cases; expect `ValueError` for malformed descriptors and `False` for absent/mismatched acceptance, not an exception for an empty record list. A changed historical catalog commit alone must not invalidate an otherwise identical fresh-plan target.

  Minimum invalid-record assertion (supplement with the exact/mismatched tuple cases above):
  ```python
  with self.assertRaises(ValueError):
      parse_native_acceptance({'schema_version': 1, 'records': [{'host': 'codex'}]})
  ```
- [x] **Step 2:** Run `PYTHONPATH=runtime python3 -m unittest discover -s tests -p 'test_installer_provider_sources.py' -v`; confirm named tests fail for missing behavior before code changes. No zero-test pass counts.
- [x] **Step 3:** Implement the types and pure parsers; emit two external host targets from the exact source table and schema layout. `PluginSpec.source` becomes catalog URL for those targets. Keep unverified hash/commit absent and `records: []` as explicit disabled states. Validate complete lowercase 40-hex pinned SHA, safe relative path, full canonical entry hash and fixed official repository pairings.
- [x] **Step 4:** Update `build_catalog`/`load_catalog` to schema 2 and nested provider handling; preserve own package payload/skills/defaults. Run Task 1 tests plus `test_installer_catalog.py`; confirm invalid native-managed/Git mixing and injected source URLs fail closed.
- [x] **Step 5:** Review the metadata boundary locally; do not generate acceptance from test fixtures or commit changes.

## Task 2: Observe official readiness without losing existing providers

**Files:** Modify `hosts.py`, `models.py`; create `tests/test_installer_superpowers_inventory.py` and explicitly synthetic fixtures.
**Consumes:** `ProviderSource` targets, original `Inventory.plugins/errors` and `Marketplace` records.
**Produces:** `inspect_provider`, provider-specific readiness and stable snapshots; no new mutation constructor for Codex official source preparation.

- [x] **Step 1:** Write `test_managed_missing_source_field_is_not_invented`, `test_verified_managed_origin_keeps_raw_source_absent`, `test_missing_native_catalog_does_not_poison_own_package_inventory`, `test_maintainer_provider_is_not_absent`, `test_unknown_provider_is_not_treated_as_empty`, and `test_claude_pinned_payload_is_not_relative_to_catalog`. Assert normalized inventory/readiness values, source fields stay absent, and original fixtures/files remain unchanged. A fully corroborated native-managed source may be ready without a raw URL field; a matching name/path alone may not.

  For the missing-source fixture with no corroborating commit/entry/payload evidence, inspect the real adapter output `inv`:
  ```python
  self.assertIsNone(inv.marketplaces[0].source)
  self.assertEqual(inv.provider_readiness[0].status, 'unverified')
  self.assertEqual(inv.errors, ())
  ```
- [x] **Step 2:** Run `PYTHONPATH=runtime python3 -m unittest discover -s tests -p 'test_installer_superpowers_inventory.py' -v`; observe the intended failures.
- [x] **Step 3:** Add official-origin recognition only through audited native identity plus required managed state/content observations. Read a prepared Codex catalog/commit receipt; never create or edit one. Represent missing/inconsistent observations as `needs-native-setup`/`unverified`. Preserve alternative providers without making their catalogs writable.
- [x] **Step 4:** Add missing/duplicate/disabled/cross-marketplace cases. Keep top-level broken inventory as global uncertainty; provider-local gaps affect only Superpowers. Use qualified non-global native queries and local selected-provider metadata, without reading notes, sessions, credentials or unrelated repository contents.
- [x] **Step 5:** Run Task 2 tests and `test_installer_hosts.py`. Confirm no test or probe invokes a real CLI installation or remote global catalog.

## Task 3: Gate plans and verify host-specific installations

**Files:** Modify `planning.py`, `hosts.py`, `receipts.py`; create `tests/test_installer_superpowers_plan.py`, `tests/test_installer_superpowers_verify.py`; adapt affected R3 receipt/plan tests.
**Consumes:** readiness and exact acceptance; spec version/hash; real native command result supplied by executor.
**Produces:** provider-aware sealed actions and postconditions; original executor once-only semantics remain.

- [x] **Step 1:** Write `test_no_codex_official_marketplace_add_is_planned`, `test_claude_source_add_requires_target_acceptance`, `test_existing_newer_provider_never_downgrades`, `test_empty_acceptance_blocks_only_superpowers`, `test_commit_change_invalidates_approval`, and `test_codex_catalog_sha_version_is_not_manifest_version`. Assert actual plan actions/outcomes, then execute with filesystem-backed process doubles and verify zero writes when rejected. Direct `source_action` for Codex official or maintainer mutation must also raise `ValueError`.

  For the existing-provider fixture (`retained` is a real cache file initialized to `b'keep'`), execute the resulting plan and assert both effects and attempted commands:
  ```python
  self.assertEqual(retained.read_bytes(), b'keep')
  self.assertEqual(native.mutations, [])
  ```
- [x] **Step 2:** Run the two Task 3 test files, observe red, then implement the new `make_plan` keyword inputs and snapshot sealing/recheck. Superpowers updates always preserve/withhold; do not reuse the self-repository URL-only check for official entries.
- [x] **Step 3:** Implement Claude verification from user-scope inventory plus pinned payload origin/manifest/full hash. For Codex official, require the managed source snapshot and 40-hex catalog commit, receipt/inventory cache version equal to its first `8` characters, correct cache root, separate manifest `6.3.0` and expected content hash. Keep R3 self-repository receipt verification intact.
- [x] **Step 4:** Add malformed/empty receipt, wrong cache SHA prefix, right cache/wrong manifest, changed payload, relative/foreign/symlink root, orphan cache and config-root-change cases. Assert unverified partial result and a single attempt, with no uninstall/metadata repair. Unexpected native bookkeeping is not an ignore-list update.
- [x] **Step 5:** Run Task 3 tests plus `test_installer_planning.py`, `test_installer_execution.py`, `test_installer_codex_receipts.py`. Confirm the actual receipt still reaches verification and preserve all original cancellation/precondition behavior.

## Task 4: Interactive guidance, isolation and relocated bundle

**Files:** Modify `ui.py`, `scripts/build_plugin_installer.py`, `installer/README.md`, root READMEs; create `tests/test_installer_superpowers_cli.py`; update bundle/CLI tests and fixture documentation.
**Consumes:** provider-ready plans and verification interfaces; empty initial acceptance index.
**Produces:** per-host source display and native setup/pending states, packaged new module/index, unchanged own-package flow.

- [x] **Step 1:** Write `test_codex_missing_official_catalog_guides_without_writing`, `test_unknown_superpowers_allows_selected_own_package`, `test_unavailable_superpowers_does_not_install_dependencies`, `test_changed_provider_snapshot_stops_native_add`, `test_no_native_install_before_source_and_install_consent`, `test_relocated_bundle_has_provider_runtime_and_acceptance`. Exercise real UI and temporary files, not source-text matching.

  For the mixed own-package/pending-Superpowers transcript, assert real temporary files and partial-result status:
  ```python
  self.assertTrue(own_manifest.is_file())
  self.assertFalse(superpowers_root.exists())
  self.assertEqual(code, 1)  # Selected Superpowers remains pending.
  ```
- [x] **Step 2:** Run `test_installer_superpowers_cli.py` and the affected bundle case; verify expected red results.
- [x] **Step 3:** Wire descriptor/readiness/acceptance through UI, without inventing defaults for missing native state. Keep Superpowers unchecked. Show catalog and payload source separately; retain explicit reasons for pending/unverified/preserved and distinguish installation, entry and behavior states.
- [x] **Step 4:** Add `providers.py` and `provider-acceptance.json` to the builder allowlist/provenance; emit schema 2. Keep build deterministic and offline. Build only to a new exclusive candidate path; never overwrite R3. Explain guide-only Codex states and native/behavior validation limits in both README languages.
- [x] **Step 5:** Run `PYTHONPATH=runtime python3 -m unittest discover -s tests -p 'test_installer_*.py'`, `python3 -m unittest discover -s tests -p 'test_agent_skills_config.py'`, `python3 -m unittest discover -s tests -p 'test_plugin_packages.py'`, and `python3 scripts/validate_skills_catalog.py --check`. Record counts/skips/exit codes; PowerShell absence is a skip. Full server/build gates that execute `npm ci` remain outside offline approval.

## Task 5: Native evidence and functional acceptance proposals

**Files:** Create `docs/validation/plugin-installer/superpowers-native-acceptance-proposal.md`, `superpowers-function-acceptance-proposal.md`; update validation index. After separate approvals only, add real observed fixtures and reviewed acceptance records.
**Consumes:** actual offline implementation/evidence and source policy; exact missing native facts listed in spec.
**Produces:** reviewable external-operation proposals, not automatic execution or invented success.

- [ ] **Step 1:** Prepare one-host-at-a-time capability probes with exact binaries/argv, fresh HOME/config roots, source commit/payload identity, expected writes, observer-local probe allowlist and single-attempt budgets. Start with Claude official or an already prepared Codex official catalog; unavailable initialization stops the case. Do not seed managed paths yourself.
- [ ] **Step 2:** Present each native proposal and obtain approval before execution. Keep partial state/evidence and stop on unexpected prerequisites or failure; no retry is included. Confirm the materialization/hash contract, then self-review the observed schema and native acceptance tuple before adding a record. An unexplained payload shape requires a design change, not a permissive comparison.
- [ ] **Step 3:** After native capability evidence exists, propose and obtain separate approval for an unmodified next-candidate installer case. Verify actual source, receipt, every payload file/hash and final enabled state. Probe success alone cannot close this step or the feature.
- [ ] **Step 4:** Prepare the seven-entry functional matrix linked in the spec. For every real-model case, specify model/CLI, fixture prompts/files, normal/failure result, expected writes/token-cost boundary and stop point. Actual delegation, external review, hook trust and integration remain separate explicit decisions. If approval/tooling is absent, record NOT VERIFIED, do not substitute file presence.
- [ ] **Step 5:** Before completion or a proposed commit, reload `quality-gates:completion-gate`, use its applicable risk tier and same-session `quality-gates:code-review-codex` without subagents. Summarize VERIFIED/NOT VERIFIED, archive/input hashes, local links and scoped Gitleaks result. No stage/commit/push is part of this task without new explicit approval.

## Review and execution handoff

The design and plan were jointly approved by user #1 on 2026-11-10 for offline execution. Keep the preserved native inline method; do not ask the user to choose agents again. On approval, execute the offline tasks in order, stopping at their real evidence gates. Native proposals and function/model cases retain separate approvals even after the implementation plan is accepted.

Initial empty native acceptance records and missing hashes intentionally disable automatic Superpowers writes. They are not a completed delivery. A completion report must separately state offline implementation, native capability, candidate installation, exposed entries and per-branch behavior, including every skipped/unverified platform or case.

## Offline execution result — 2026-11-10

User #1 jointly approved this design/plan and offline implementation. Tasks 1–4
are complete within offline scope. Task 5 prepared a concrete Claude capability
proposal and a functional matrix; native setup/probes, unmodified installer
acceptance and model cases remain unexecuted and unchecked above. Exact functional
model/budget/fixture manifests remain for the later case proposal. See
[offline evidence](../../validation/plugin-installer/superpowers-official-sources-offline.md)
and [same-session review](../../validation/plugin-installer/superpowers-official-sources-review.md).
No current-branch stage/commit/push or external run is authorized by this result.
