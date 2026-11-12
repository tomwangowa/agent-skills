# Cross-platform Plugin Installer Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development or superpowers:executing-plans to implement this plan task-by-task. This session uses inline execution under the approved plan; no delegation, commit or native installation test is authorized. The checklist below is the original task contract; current evidence and remaining gaps are in [validation](../../validation/plugin-installer/README.md).

**Goal:** 交付一份含三平台入口的 plugin 安裝包，以及涵蓋每個套件的雙語 README 使用場景。

**Architecture:** 平台啟動檔處理 CLI／Python 前置檢查；Python 標準函式庫主程式共用盤點、選擇、預覽、執行與結果規則。catalog 由 repo 真正的套件產物生成，每個 CLI 的來源與安裝狀態分開處理。

**Tech Stack:** Python 3.11+ 標準函式庫、macOS／Linux shell、Windows PowerShell、既有 `unittest`；不增加 pip 或 npm runtime 依賴。3.11 是安裝器的實作下限，plugin 個別需求仍另驗。

**Spec:** [已核准設計](../specs/2026-11-09-cross-platform-plugin-installer-design.md)。本計畫與設計都必須閱讀；設計批准不等於本計畫或實際安裝測試批准。

## Global Constraints

- 只在 `feat/cross-platform-plugin-installer` worktree 實作；保留原有四份 stash，不 stage、commit 或 push，除非另有明確批准。
- Claude Code／Codex 只偵測與引導，不代裝；同事選擇一個或兩個已安裝的 CLI。
- 七包與 Claude 額外 `handoff-mod`、`attention-mod` 預選全部適用項目；已安裝者保留，更新另選；Superpowers 強烈推薦但預設不勾選。
- 只透過現有受支援管理工具代裝缺少的依賴，預覽並確認；不代裝管理工具。Python 無法補齊就停在指引，其餘依賴不足只影響對應項目。
- 預覽與執行使用同一份安裝計畫；來源或本機前提改變就暫停受影響項目，重新預覽確認；不主動重試外部動作。
- 不覆蓋同事的設定、停用狀態或其他層級管理項目；不改 `CLAUDE.md`／`AGENTS.md`、hook 信任或 installed plugin cache。
- 日誌設定可略過，寫入前另預覽；設定、安裝與授權結果分開記錄。原生 Windows 的 POSIX 鎖限制不在這次修補範圍。
- 程式輸出與註解使用英文；`README.md` 英文、`README.zh.md` 繁中同步提供實際使用場景。
- 安裝器的離線測試不下載、不接觸真實 plugin 環境。實際下載／安裝與重跑先取得具體批准，不啟動模型 session。
- 原生驗收範圍為 macOS、原生 Windows、Ubuntu／Debian；記錄確切版本與架構，不能以一種通過代表其餘通過。

## Review Focus

1. Windows 的 `python`／`py` 是會自動下載 runtime 的 shim：探測不能自行安裝；Task 6 以有副作用的假 shim 驗證它未被執行。
2. 同名 plugin 的來源、scope 或 enabled 狀態不明：保留且列為待確認；Task 2／3 的混合 inventory 測試固定此行為。
3. 確認後 marketplace 或個人設定被另一程序改動：不得沿用原確認；Task 4／5 注入變動並驗證沒有覆寫或執行受影響命令。
4. 取消發生在已補裝 Python、刷新來源或啟動子程序之後：不能回報零變更；Task 4／7 檢查分階段結果與不確定狀態。
5. 解壓路徑含空白、中文與不同工作目錄：不得執行錯誤程式或洩漏 repo 依賴；Task 6／8 從搬移後的安裝包啟動驗證。

## Files and interfaces

新模組放在 `runtime/agent_skills_installer/`，不加入既有 plugin payload allowlist。`installer/` 放平台入口與明確維護的外部 provider／依賴映射；`scripts/build_plugin_installer.py` 只讀來源、離線建置 ZIP。只重用既有 runtime 的 `__init__.py`、`config.py`、`setup.py`，不修改它們或引入 POSIX-only preference／migration 寫入。

| 檔案 | 責任 |
| --- | --- |
| `models.py`、`catalog.py` | 純資料型別、套件清單生成及驗證 |
| `hosts.py`、`dependencies.py` | 原生 CLI inventory／命令與管理工具規則，不負責互動或自行寫入 |
| `planning.py`、`execution.py` | 純計畫計算、確認憑證與一次性執行 |
| `journal.py`、`ui.py`、`__main__.py` | 日誌設定、文字選單及主流程 |
| `installer/install.py`、三平台入口 | 發行包入口，Python 缺少時的最小引導 |
| `installer/providers.json`、`installer/dependencies.json` | 已核對的來源與平台依賴映射，不存私人設定 |
| `tests/test_installer_*.py`、`tests/fixtures/installer/` | 行為測試與明確標示 synthetic／observed 的資料 |
| `docs/validation/plugin-installer/README.md` | 能力查核、隔離驗收程序與證據界線 |

以下函式路徑均以 `runtime/agent_skills_installer/` 為基準。資料類別使用 frozen dataclasses；`Host = Literal['claude', 'codex']`、`Platform = Literal['macos', 'windows', 'linux']`。只有 `execution.py` 的已確認 executor 及 Task 5 的已確認設定寫入可以呼叫會改動環境的操作；平台 bootstrap 的 Python 補裝另行確認。

新測試檔以 `Path(__file__).resolve().parents[1] / 'runtime'` 加入 import 路徑，從 repo 原始碼測試，不依賴已安裝的私人 plugin。測試名稱與下列斷言為交付契約；同一測試可用 subTest 覆蓋列出的變體。

## Task 0: Establish baseline and capability evidence

**Files:** Create `docs/validation/plugin-installer/README.md`, `tests/fixtures/installer/README.md`.
**Interfaces:** 每份 observed fixture 附 `host`、`cli_version`、`platform`、`architecture`、`command`、`provenance`；fixture 不包含私人完整路徑、認證或工作內容。

- [ ] **Step 1:** 核對 HEAD 與 dirty state，確認只有已批准的設計／計畫文件。重讀本計畫與 spec，檢查 execution method 尚未選定時不開始 Task 1。
- [ ] **Step 2:** 實作前跑現有離線 baseline：`python3 -m unittest discover -s tests -p 'test_plugin_packages.py'` 與 `python3 scripts/validate_skills_catalog.py --check`；先檢查命令入口是否有外部呼叫。既有失敗原樣記錄，不歸因新改動。
- [ ] **Step 3:** 以本機 help 與可唯讀取得的 native inventory 核對現有命令。不得為了取樣新增或刷新 marketplace；若查詢可能連網或寫宿主設定，先提出具體隔離操作供批准。實際 JSON 欄位、enabled、scope、來源與根目錄能力寫入紀錄。
- [ ] **Step 4:** 核對 Superpowers 在兩個 CLI 的正式來源與 manifest identity；從官方發布／套件資料核對 brew、WinGet、APT 的工具 ID 與 Python 版本。未知組合記為 unsupported／unverified，不填猜測值；原生寫入 adapter 必須等相關證據與批准後才可驗收為可用。
- [ ] **Step 5:** 記錄網路界線：既有 `scripts/build_plugins.py --check` 會經 `prepare_server` 呼叫 `npm ci`；完整 `test_build_plugins.py` 也有此路徑。這些檢查不能直接放進離線 baseline。能力查核的退出條件為已觀察的 schema 或可測試的拒絕狀態，沒有證據不能回傳成功。

## Task 1: Build the generated catalog and shared models

**Files:** Create `__init__.py`, `models.py`, `catalog.py`, `installer/providers.json`, `installer/dependencies.json`, `tests/test_installer_catalog.py`.
**Interfaces:** `PluginSpec(host, name, marketplace, source, version, skills, commands, notices, default_selected)`；`InstalledPlugin(host, name, marketplace, source, version, root, enabled, scope)`；`Inventory(host, cli_version, plugins, marketplaces, capabilities, errors)`。名稱／來源為字串，未知已安裝版本／根目錄／scope 可為 `None`；集合使用 tuples。
`Action(id, kind, host, target, argv, requires, preconditions)`；`Plan(actions, fingerprint, prior_results)`；`Outcome(action_id, status, detail)`。`kind` 為 `add_marketplace`, `refresh_marketplace`, `install`, `update`, `dependency`；`status` 為 `installed`, `updated`, `preserved`, `skipped`, `failed`, `unverified`。`prior_results` 記錄尚未執行即已判定的保留、略過與待確認，以穩定的 CLI／來源／套件 key 作 `action_id`，避免執行報告漏掉沒有命令的項目。設定與授權另列，不塞進安裝 status。
`catalog.build_catalog(repo_root: Path, providers: dict, dependencies: dict) -> tuple[PluginSpec, ...]`。

- [ ] **Step 1:** 寫 `test_surface_catalog_and_defaults`：Claude reviewer 清單不含 Codex reviewer，Codex 不含 Claude-only toolbox；額外兩包只屬 Claude；`self.assertFalse(superpowers.default_selected)`。`test_invalid_catalog_inputs_rejected` 以 `self.assertRaises(ValueError)` 固定缺 manifest、未知來源、重複 identity、symlink／逃出來源目錄均拒絕；`test_manual_intent_preserved` 檢查手動呼叫 metadata。
- [ ] **Step 2:** Run `python3 -m unittest discover -s tests -p 'test_installer_catalog.py'`，確認因模組尚未存在失敗，再實作型別與生成器。重用 `scripts.plugin_packaging.catalog.surface_skills` 作交叉檢查，但 ship 清單以實際 manifests／skills 為準；skills 加入可解釋的用途及 invocation intent。
- [ ] **Step 3:** 再跑同命令至通過，驗證資料中有七包、Claude 兩包與強烈推薦的外部項目，且來源 versions 與生成內容一致。此測試不證明外部 provider 已註冊或相容。

## Task 2: Normalize native inventory and construct commands

**Files:** Create `hosts.py`, `tests/test_installer_hosts.py`, fixtures under `tests/fixtures/installer/`.
**Interfaces:** `read_inventory(host: Host, runner: Callable) -> Inventory`；`plugin_action(spec: PluginSpec, kind: Literal['install','update']) -> Action`；`source_action(host: Host, source: str, kind: Literal['add_marketplace','refresh_marketplace']) -> Action`。runner 接收 argv tuple，回傳 `subprocess.CompletedProcess[str]`；此 task 的函式只建命令，mutating action 不自行執行。

- [ ] **Step 1:** 寫 `test_observed_inventory_normalization` 驗證兩種 schema 的精確欄位；`test_unknown_inventory_never_means_absent` 覆蓋缺 source／version／enabled／scope、malformed JSON、非零 exit、同名多 scope 或來源衝突。未知格式不得退回掃 cache 猜狀態；`self.assertTrue(inventory.errors)` 檢查拒絕分支。`test_superpowers_provider_identity_across_marketplaces` 核對已註冊 provider 的 manifest 與來源別名，避免只因 marketplace 名稱不同就誤報未安裝。
- [ ] **Step 2:** Run `python3 -m unittest discover -s tests -p 'test_installer_hosts.py'`，先紅再寫 adapters。argv 以獨立參數交給 subprocess，不用 `shell=True`；限制已核對的來源，保留宿主權限與信任提示，不自動接受未知 command-source 安裝。
- [ ] **Step 3:** 同命令確認通過；額外斷言 Codex 不套用 Claude 的 update 命令，已選 CLI 以外無命令、非 user scope 不被改動。合成 fixtures 只能證明 parser／拒絕行為，須與 observed fixture 分開命名。

## Task 3: Compute one installation plan for preview and execution

**Files:** Create `planning.py`, `tests/test_installer_planning.py`.
**Interfaces:** `make_plan(catalog: tuple[PluginSpec,...], inventories: tuple[Inventory,...], selected: frozenset[tuple[Host,str]], updates: frozenset[tuple[Host,str]], tools: dict[str,bool]) -> Plan`；`fingerprint(plan: Plan) -> str`。fingerprint 使用穩定序列化的實際 actions、前提與 prior_results，不能只 hash 顯示字串或包含 fingerprint 欄位本身；無待執行動作以空 tuple 表達。

- [ ] **Step 1:** 寫 `test_dual_host_preserve_and_install`，斷言相同套件在兩個 CLI 分別產生 `preserved` 與 `install`；`test_selection_and_dependency_boundaries` 覆蓋全選本地套件／不預選 Superpowers、停用或 scope 不明者保留待確認、缺工具只略過受影響項目、來源衝突阻擋同來源項目。`test_plan_fingerprint_changes_with_decision` 固定 Step 3 的 fingerprint 契約。
- [ ] **Step 2:** Run `python3 -m unittest discover -s tests -p 'test_installer_planning.py'`，先紅再實作純函式。依賴 action 透過 `requires` 指向前置 action；保留、略過與原因隨計畫產生，執行端不重新制定選擇。
- [ ] **Step 3:** 確認通過，包含 `self.assertNotEqual(fingerprint(old), fingerprint(changed))`：更新選擇、來源、版本、前提任一改動都使原確認失效；同一份計畫的重複計算結果穩定。

## Task 4: Execute approved actions once and report partial outcomes

**Files:** Create `execution.py`, `dependencies.py`, `tests/test_installer_execution.py`, `tests/test_installer_dependencies.py`.
**Interfaces:** `dependency_action(tool: str, platform: Platform, managers: frozenset[str], mapping: dict) -> Action | None`；`execute(plan: Plan, approved_fingerprint: str, runner: Callable, recheck: Callable[[Action],bool], verify: Callable[[Action],bool]) -> tuple[Outcome,...]`。缺 manager／未驗證映射回傳 `None` 並由 planning 記錄略過；`execute` 合併 prior_results、逐項事前 recheck／事後 verify，不自動重試。取消由 `KeyboardInterrupt` 或 runner 的取消結果傳入。

- [ ] **Step 1:** 寫 `test_reject_stale_approval`，斷言錯誤 fingerprint 執行零個命令；`test_recheck_and_postverify` 固定前提變動拒絕及事後核對。`test_partial_failure_and_cancellation` 斷言 timeout／取消產生 `unverified`、保留先前成果、一包失敗其他獨立包繼續、`self.assertEqual(calls.count(failed_argv), 1)`，且沒有移除或 rollback 命令。
- [ ] **Step 2:** 寫 `test_dependency_action_uses_existing_manager_only`，斷言無 manager 時 `self.assertIsNone(action)`；`test_selected_missing_tools_only` 固定只補選定功能缺少的工具、不執行整體系統升級。管理工具可能帶入的依賴／權限列入預覽，不謊稱全部是 user-only 寫入。
- [ ] **Step 3:** Run `python3 -m unittest discover -s tests -p 'test_installer_execution.py'` 及 `python3 -m unittest discover -s tests -p 'test_installer_dependencies.py'`，先紅再實作；依前置結果與 recheck 處理，事後 inventory／工具版本驗證失敗不回傳 installed。
- [ ] **Step 4:** 重跑兩個測試檔至通過。驗證傳給 runner 的 argv 正是確認的 plan actions；管理工具拒絕升權或需要重啟時保留狀態，沒有內建提權、重設執行政策或信任寫入。

## Task 5: Add optional journal setup without replacing settings

**Files:** Create `journal.py`, `tests/test_installer_journal.py`.
**Interfaces:** `journal_preview(env: Mapping[str,str], home: Path, activities: str, notes: tuple[str,...]) -> dict`；`apply_journal(preview: dict, approved_fingerprint: str) -> dict`。preview 包含 config root、將建立的目錄、既有內容 fingerprint 與 proposed settings；重用 `agent_skills_runtime.config` 與 `setup.setup_work_journal`，不依賴 preference／migration 模組。

- [ ] **Step 1:** 寫 `test_journal_preview_has_no_writes`、`test_existing_settings_preserved`、`test_config_path_contracts`：config root 三層優先序、空白／中文／相對資料路徑、首次建立、略過、保留有效設定、拒絕覆蓋無效設定及 plugin-cache／symlink alias 路徑；斷言預覽後 `self.assertFalse(config_root.exists())`，且沒有讀筆記內文。
- [ ] **Step 2:** 寫 `test_concurrent_settings_change_preserved`，在預覽後及原子建立前注入另一程序寫入：`self.assertEqual(settings.read_bytes(), concurrent_content)`；結果回報 conflict／preserved，不能用舊內容覆蓋或新增未預覽的目錄。
- [ ] **Step 3:** Run `python3 -m unittest discover -s tests -p 'test_installer_journal.py'`，先紅再實作。新設定沿用 runtime 的完整檔案原子建立與不覆蓋行為；既有內容另核對，不改 runtime 程式來逃避 Windows 限制。
- [ ] **Step 4:** 重跑至通過，確認設定狀態與 plugin 安裝狀態分開，略過仍列 pending configuration；macOS 的測試不能作原生 Windows 成功證據。

## Task 6: Implement platform bootstrap and Python entry point

**Files:** Create `installer/install.py`, `installer/install-macos.command`, `installer/install-linux.sh`, `installer/install-windows.ps1`, `tests/test_installer_bootstrap.py`; modify `dependencies.py`.
**Interfaces:** Archive 入口固定從自身目錄定位 `runtime/` 與 `catalog.json`，與當前工作目錄無關；Python 入口呼叫 Task 7 的 `main(argv: list[str] | None = None) -> int`。`render_bootstrap(template: str, platform: Platform, mapping: dict) -> str` 在建置時把已核對的 Python 最小安裝映射寫成各平台的常數 argv；啟動時不靠尚未安裝的 Python、jq 或其他新增工具解析 JSON，不用 eval。bootstrap 只處理 host／Python，成功後交接，不實作 plugin 選擇規則。

- [ ] **Step 1:** 寫 `test_rendered_bootstrap_mapping` 驗證無未展開標記且 argv 與映射一致；`test_bootstrap_prerequisite_paths` 覆蓋無 host 不補裝、Python 3.11+ 引數交接、缺 Python／manager／拒絕／失敗停止。`test_python_probe_does_not_invoke_download_shim` 放入會留下 sentinel 的假 shim，斷言 `self.assertFalse(sentinel.exists())`。
- [ ] **Step 2:** Windows 依實際 runtime／已核對 inventory 找 Python，不以可能自動下載的 shim 做探測；管理工具代裝前顯示來源與權限並詢問，成功後驗證真實 interpreter。PowerShell 政策阻擋時提供指引，不使用 bypass 或持續修改政策。
- [ ] **Step 3:** Run `python3 -m unittest discover -s tests -p 'test_installer_bootstrap.py'`，先紅再實作；tests 對 render 後的兩個 shell 入口各執行 `bash -n`，避免依賴 Bash 4 專屬特性。PowerShell 於 Windows 用 parser 語法檢查與假工具測試。
- [ ] **Step 4:** 從空白／中文目錄與不同 cwd 執行測試，確認引數不被 shell 重解釋。非本平台未執行的 process tests 明列 skipped，不以 syntax pass 宣稱原生入口通過。

## Task 7: Assemble the interactive user flow

**Files:** Create `ui.py`, `__main__.py`, `tests/test_installer_cli.py`.
**Interfaces:** `ui.run(catalog: tuple[PluginSpec,...], input_fn: Callable[[str],str], output: TextIO, runner: Callable) -> int`；`__main__.main(argv: list[str] | None = None) -> int`。支援 `--catalog PATH` 與 `--help`；不提供跳過確認的 `--yes`。回傳 0 表示選定操作已核對且無失敗／待確認，1 表示失敗或不確定，2 表示參數／資料錯誤，130 表示取消；待設定與待信任另行明列，不隱藏。

- [ ] **Step 1:** 寫 `test_selection_transcript`、`test_separate_approval_transcripts`：僅顯示可用 CLI、預選適用項目、強烈建議且未勾選的 Superpowers、額外更新選項、返回修改、來源前置確認與最終確認分開、代裝拒絕後仍可繼續；每個確認前都斷言尚無對應 mutating calls。
- [ ] **Step 2:** 寫 `test_invalid_and_noninteractive_input`、`test_partial_summary_and_prior_side_effects`：空輸入、無效編號、EOF、取消、stdout 非互動、全部已保留、部分成功與待設定／信任；非互動不默認同意。`self.assertNotIn('ALL SUCCESS', output)` 配合具體項目結果斷言，確認部分失敗不會全成功，取消也保留前置階段成果。
- [ ] **Step 3:** Run `python3 -m unittest discover -s tests -p 'test_installer_cli.py'`，先紅再實作六步流程；每次確認對應真實 plan fingerprint。取消仍顯示之前獨立確認的 Python／marketplace 成果。
- [ ] **Step 4:** 同命令通過後，確認主流程只從 Task 4／5 寫入，不另行組合有副作用的 shell 指令；日誌引導在 plugin 安裝之後，既有設定先保留。

## Task 8: Build and validate a relocatable archive

**Files:** Create `scripts/build_plugin_installer.py`, `tests/test_installer_bundle.py`.
**Interfaces:** `build_bundle(repo_root: Path, output: Path) -> Path`；CLI 為 `python3 scripts/build_plugin_installer.py --output PATH`。ZIP 根目錄為 `agent-skills-installer/`，包含三入口、`install.py`、`catalog.json`、兩個 JSON 映射與 `runtime/` 下的新 package 及三個重用 runtime 檔案。

- [ ] **Step 1:** 寫 `test_bundle_allowlist_and_provenance`：無 symlink／私人設定／tests／node_modules／pyc，來源 commit 與檔案雜湊正確；`test_reproducible_bundle` 斷言兩次建置 `self.assertEqual(first.read_bytes(), second.read_bytes())`；`test_existing_output_not_replaced` 確認既有輸出不默默覆蓋。
- [ ] **Step 2:** Run `python3 -m unittest discover -s tests -p 'test_installer_bundle.py'`，先紅再實作標準函式庫 builder，固定 ZIP 內時間與權限；使用 Task 6 的 `render_bootstrap`，拒絕殘留未展開標記。只讀既有生成 plugins，不呼叫會執行 `npm ci` 的 `build_plugins.py`，不修改 plugin payload。
- [ ] **Step 3:** 在兩個不同暫存目錄解壓，清除 repo `PYTHONPATH`，從其他 cwd 執行 `install.py --help`；使用假 CLI 做一次完整取消與部分失敗流程。確認 runtime imports 只來自解壓包，不靠維護者本機安裝。
- [ ] **Step 4:** 同測試檔通過並記錄包內來源版本；ZIP 被 `.gitignore` 忽略，交付檔需明確報告實際輸出路徑，不新增私人路徑進 repo。

## Task 9: Add bilingual scenarios and integrate verification

**Files:** Modify `README.md`, `README.zh.md`; update `docs/validation/plugin-installer/README.md`；必要時補 `tests/test_installer_catalog.py` 的套件與場景對照檢查，不為文字風格寫鏡像測試。
**Interfaces:** 依 spec 的七組工作場景覆蓋七包、兩個 Claude 額外 plugins 與 Superpowers；正文保留實例，附套件反查表。入口依實際打包內容，不能只憑 registry 猜 slash／dollar 名稱。

- [ ] **Step 1:** 逐包讀需要的 skill／mod 說明，撰寫「時機、套件、開始方式、產出」及必要設定、外部服務與平台限制；README 連結至安裝包建置／取得方式，不虛構尚未發布的下載 URL。
- [ ] **Step 2:** Run `PYTHONPATH=runtime python3 -m unittest discover -s tests -p 'test_installer_*.py'`、`python3 scripts/validate_skills_catalog.py --check` 與 `git diff --check`；在支援的本機語法檢查 launcher。以來源與場景對照檢查每包均有覆蓋，人工核對雙語事實一致。
- [ ] **Step 3:** 對 spec 每節逐項對照實作與測試，記錄已驗證／未驗證；先載入 `completion-gate` 分級並依 repo 執行必要的同 session `code-review-codex`。外部 reviewer、模型呼叫與 subagent 不自動啟用。修正後只重跑受影響檢查；不提交。
- [ ] **Step 4:** 既有完整 plugin rebuild、全套測試中會連網的檢查、三平台原生下載／安裝驗收，另列精確命令、隔離目錄、來源／版本、網路與費用範圍取得批准後才執行；重跑需新批准。缺平台環境時保持 unverified，不將 offline suite 擴大成三平台安裝通過。
- [ ] **Step 5:** 若碰到需要修改 plugin payload 的問題，先判斷能否以安裝器限制說明維持本次範圍；確需改動時回報影響，遵守升版、重建與發布 gate。不得為了讓測試全綠繞過權限、設定或來源保護。

## Checkpoints and handoff

實作順序為 Task 0 → 1 → 2 → 3 → 4 → 5 → 6 → 7 → 8 → 9；Task 6 的完整交接測試在 Task 7 入口存在後補跑，先前只驗 bootstrap 假入口。每項交付先做列出的紅綠循環，再核對對應 spec；native 能力缺乏證據時保留拒絕路徑，不能假裝成功。

計畫審閱後由使用者選執行方式。Native 分支由目前 agent 逐項實作，依 repo 用同 session 的 Codex native review；subagent-driven 分支只有明確選擇後才啟用，並依其規則逐項做 spec 與 code-quality review。兩者都不得自動 commit。

原生驗收結果要區分安裝器流程、CLI 安裝清單、設定、hooks／MCP／skills 執行層。這份計畫不授權發布、同步 production、skill-sync、push、修改私人 runtime 或發送真實工作資料。
