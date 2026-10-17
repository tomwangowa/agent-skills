# Skills 七包 Plugins Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** 將 38 個來源 skills 與本機 MCP、hooks 包裝成七個可選 plugins，在 Claude Code CLI、Codex CLI 安裝、使用及更新。

**Architecture:** 保留既有來源，以 `plugin-packages.json` 定義七包，產生兩平台的完整發佈目錄與 marketplace。個人設定位於套件快取之外，由 Python／Node.js 共用解析契約；必要路由隨受影響套件載入。先驗證平台契約，再實作設定、來源適配、產生器與遷移。

**Tech Stack:** Python 標準函式庫與 unittest、現有 Bash／jq／Git、TypeScript／Node.js、既有 MCP SDK、Vitest；保留現有 lockfile。最低執行版本由實際依賴及 Task 1 實測確定。

**Spec:** [2026-10-13-skill-plugins-design.md](../specs/2026-10-13-skill-plugins-design.md)，使用者已核准。

## Global Constraints

- 七包與成員完全依規格第 2 節，來源總數 38；四個例外不改生命週期。
- 支援 Claude Code CLI、Codex CLI。使用者已明確取消桌面版支援；保留先前探測失敗證據。
- 發佈為 Git marketplace；原有 `attention-mod`、`handoff-mod` 保留。
- 發佈包不得含固定個人帳號路徑、私人 `config.json`、本機紀錄或憑證；資源必須在包內。
- 共用設定根目錄依序採用 `AGENT_SKILLS_CONFIG_DIR`、`XDG_CONFIG_HOME/agent-skills`、當前使用者家目錄下的 `.config/agent-skills`。
- Logger 與 MCP 使用同一有效活動目錄；保留 `CLAUDE_ACTIVITIES_DIR` 明確覆寫。
- 個人模組整份覆寫同名預設，新增模組追加；`control-return.md` 不列入 session-preferences 的 INDEX。
- 保留 `AGENT_SESSION_PREFS=off`，只停用偏好 hooks；user-only skills 保留手動限定。
- 需求探索用自有 brainstorming、完成驗證用自有 completion-gate、review 用當前平台原生 reviewer；Superpowers 沿用上游並依流程檢查。
- 程式註解與執行輸出使用英文；說明文件使用繁體中文。公共 API 的 TypeScript 函式補 JSDoc。
- 每項可執行變更採先失敗、後通過的行為驗證；純說明文字使用 deterministic checks。
- 修改 skill 後必須執行 `skill-auditor`，報告放開發驗證目錄，逐項處理結果。
- 每次 commit、push、發布前另取得使用者同意；計畫中的任務完成不構成授權。Commit 前依 completion-gate 分級：L0 deterministic checks；L1／L2 一次 Codex 原生 review；L2 完整驗證。
- 在執行階段使用 using-git-worktrees 決定隔離方式；測試不重設 HOME 或 CODEX_HOME，使用專用測試設定、暫存目錄與唯一測試 marketplace。

## Review Focus

1. 空白或非 ASCII 安裝路徑、不同工作目錄：MCP／hooks 找到包內資源，Task 1／6 測試。
2. 無設定、無效 JSON、空筆記路徑、活動目錄覆寫：明確報錯，寫入與查詢不能各用不同目錄，Task 2／4 測試。
3. 個人模組損壞、預設模組更新、兩個程序同時寫規則：回報局部狀態、保留副本，衝突寫入不能互相覆蓋，Task 3 測試。
4. Superpowers 缺少／版本變動及 hooks 未信任：指出受影響流程，不假裝完整可用，Task 1／7 測試。
5. 已有舊 skills／hooks／MCP、使用者另有同名或不相關設定：遷移只切換清單中的項目，備份可恢復，Task 8 測試。

## 檔案分工與任務順序

| 位置 | 責任 |
| --- | --- |
| `scripts/probe_plugin_runtimes.py`、`skills-query-server/scripts/smoke_client.mjs` | 最小包裝實驗與實際 MCP client |
| `runtime/agent_skills_runtime/` | 設定、偏好、路由、首次設定／檢查與遷移，隨需要的包裝複製 |
| `plugin-packages.json`、`scripts/plugin_packaging/` | 七包定義、平台適配、資源與產物驗證 |
| `scripts/build_plugins.py`、`scripts/check_plugin_release.py` | 產生及檢查的命令入口 |
| `plugins/claude/`、`plugins/codex/` | 產生的發佈包，禁止直接修改 |
| `docs/validation/skill-plugins/` | 平台契約、驗收及 skill audit 記錄，不進 runtime 包 |
| `docs/plugins/` | 安裝、套件用途、依賴、更新與遷移文件 |

任務順序：1 → 2 →（3、4）→ 5 → 6 → 7 → 8。3、4 共用 Task 2 的介面；未選擇執行方式前，不派遣代理或開始實作。

---

### Task 1：驗證兩個 CLI 的最小包裝契約

**Files:** Create `scripts/probe_plugin_runtimes.py`、`skills-query-server/scripts/smoke_client.mjs`、`skills-query-server/scripts/smoke_client.d.mts`、`tests/test_plugin_runtime_probe.py`、`docs/validation/skill-plugins/runtime-contracts.json`；更新 `skills-query-server/package.json` 增加 `smoke` 命令。

**Interfaces:** `build_probe_fixture(repo_root: Path, destination: Path, surface: str) -> Path` 產生唯一命名的臨時 plugin；`validate_runtime_contracts(path: Path) -> list[str]` 回傳不完整或失敗項目。Node `runSmoke(command: string, args: string[], env: Record<string,string>) -> Promise<{tools: string[], roundTrip: boolean}>` 啟動真實 stdio server，對應 declaration 提供 TypeScript 測試型別；匯入模組不啟動 CLI。

- [x] 寫 `test_rejects_unverified_surface`、`test_probe_fixture_contains_only_runtime_files`：兩個 CLI surface 任一狀態不是 `verified` 時驗證失敗；fixture 不含來源私人配置、repo 外連結或執行時需要的遺漏資源。

```python
with TemporaryDirectory() as directory:
    assert validate_runtime_contracts(Path(directory) / "missing.json")
```

- [x] 執行 `python3 -m unittest discover -s tests -p 'test_plugin_runtime_probe.py' -v`，確認測試因待實作介面或缺少契約檢查而失敗。
- [x] 實作 fixture 產生與證據驗證。使用既有 server 編譯結果、測試用 config／資料目錄，以及兩個真實偏好腳本；另外帶自有路由測試入口。測試 server 使用平台專屬名稱與只读 probe_identity 預檢，確認實際 fixture 綁定後，MCP client 列出七個正式工具、呼叫 `log_activity` 寫入唯一測試字串，再以 `query_activities` 的 `range: all` 查回同一字串。
- [x] 在兩個 CLI surface 以平台正式安裝入口測試：Claude 的本機 `--plugin-dir`；Codex 的唯一測試 marketplace／plugin與 hooks 信任。保留安裝／清理指引，記錄實際命令與版本、manifest／MCP 路徑格式、Superpowers 版本、四種 SessionStart 來源、路由選擇與偏好停用結果。不得將手動欄位預填為已驗證。
- [x] 契約 JSON 每個 surface 含 `status`、`client_version`、`manifest_format`、`mcp_launch`、`hook_events`、`routing_result`、`superpowers_version`、`evidence`。重跑單元測試、`npm --prefix skills-query-server run smoke -- --contract ../docs/validation/skill-plugins/runtime-contracts.json`；任何 surface 不完整就停在此任務，修正設計後再繼續。

**Deliverable:** 有可重現證據的兩個 CLI 包裝契約。套件管理的 Superpowers 安裝來源與檢查方式以此契約為準，不能由 Codex 缺少文件推論它一定沒有自動依賴能力。

### Task 2：共用設定、首次設定與檢查入口

**Files:** Create `runtime/agent_skills_runtime/__init__.py`、`config.py`、`setup.py`、`doctor.py`、`skills-query-server/src/runtime-config.ts`、`tests/test_agent_skills_config.py`、`skills-query-server/src/runtime-config.test.ts`、`tests/fixtures/plugin-config-cases.json`。

**Interfaces:** Python `resolve_config_root(env: Mapping[str,str], home: Path) -> Path`、`resolve_activities_dir(env: Mapping[str,str], settings: dict, config_root: Path, home: Path) -> Path`；Node 同名 camelCase 函式回傳 `string`。`setup_work_journal(config_root: Path, activities: Path, notes: list[Path]) -> Path` 明確建立使用者選定的目錄及 config；`check_environment(config_root: Path, requirements: dict) -> list[dict]` 回傳 `{component,status,message}`。

- [x] 寫兩語言共用案例：專用設定路徑優先於 XDG、XDG 優先於 home fallback；活動覆寫優先；相對資料路徑從 config root 解析、`~/` 從 home 解析；缺檔、壞 JSON、空 `sources.notes.paths` 明確失敗。

```python
base = Path(gettempdir())
env = {"AGENT_SKILLS_CONFIG_DIR": str(base / "custom"), "XDG_CONFIG_HOME": str(base / "xdg")}
assert resolve_config_root(env, base / "home") == base / "custom"
```

- [x] 跑 `python3 -m unittest discover -s tests -p 'test_agent_skills_config.py' -v` 與 `npm --prefix skills-query-server run test:unit -- src/runtime-config.test.ts`，確認失敗。
- [x] 實作解析契約與明確 setup／doctor CLI。預設 doctor 只讀；setup 已有 config 時保留内容，變更前產生可檢視的差異。Node.js／Python／jq／Git 需求按所選功能列出，不把偏好套件誤判成需要全部工具。
- [x] 重跑上述測試；以同一 fixture 比較 Python／Node 的有效根目錄與活動目錄，兩者完全相同。以臨時空目錄確認首次設定成功，第二次執行保留已有設定。

**Deliverable:** 不依賴任何特定帳號的共用設定介面；後續任務不得另寫自己的優先順序。

### Task 3：個人偏好覆寫及兩個 hooks

**Files:** Create `runtime/agent_skills_runtime/preferences.py`、`tests/test_preferences_overrides.py`；Modify `session-preferences/scripts/session_start_hook.py`、`control-return/scripts/session_start_hook.py`、兩個 `SKILL.md`、`session-preferences/README.md`、`tests/test_session_start_hooks.py`。

**Interfaces:** `load_preferences(default_dir: Path, config_root: Path) -> tuple[str,list[str]]` 回傳有效內容與警告；`load_control_return(skill_md: Path, config_root: Path) -> tuple[str,list[str]]`；`save_module_override(config_root: Path, module: str, content: str, base_hash: str | None, expected_hash: str | None) -> Path`。

- [x] 寫行為測試：同名個人模組整份取代、不同名追加；deferred reference 指向正確版本；`control-return.md` 僅由自己的 hook 讀取；壞模組不能讓有效模組消失或聲稱完整載入；`off` 輸出為空。兩個寫入程序用相同舊 hash 修改時，只能有一個成功，另一個回報衝突。

```python
code, stdout = self.run_hook(AGENT_SESSION_PREFS="off")
self.assertEqual((code, stdout), (0, ""))
```

- [x] 執行 `python3 -m unittest discover -s tests -p 'test_preferences_overrides.py' -v`，確認失敗。
- [x] 實作覆寫、base hash 與 expected hash 檢查；採臨時檔、排他鎖及原子替換，讀整檔寫回不能覆蓋其他程序的新內容。Hook bootstrap 必須在原始 repo 與產生的 plugin 中都找到包內 runtime。更新 skill 指示使確認後的 add-rule 寫入個人目錄，保留人工確認與局部失敗回報。
- [x] 重跑兩組偏好測試；替換預設模組內容後，確認個人副本不變且 doctor 回報預設變更；兩次相同輸入輸出一致。對兩個已修改 skills 執行 skill-auditor，結果與處置存開發驗證目錄。

**Deliverable:** 語氣與下一步規則可個人化，更新及並行寫入不遺失個人內容。

### Task 4：MCP 與 logger 使用同一資料設定

**Files:** Modify `skills-query-server/src/config.ts`、`src/index.ts`、`src/index.test.ts`、`package.json`、`README.md`、`activity-logger/scripts/log_activity.sh`、`init_activities.sh`、`activity-logger/SKILL.md`、`work-log-analyzer/SKILL.md`；Create `runtime/agent_skills_runtime/journal_cli.py`、`activity-logger/tests/test_shared_config.sh`、`skills-query-server/src/stdio.integration.test.ts`。

**Interfaces:** 保留 `loadConfig(configPath: string): Config`，新增 `loadRuntimeConfig(env: NodeJS.ProcessEnv, home: string): Config` 使用 Task 2 的解析函式；Python `journal_cli.main(argv: list[str]) -> int` 提供 `activities-dir` 與 `config-root` 子命令，stdout 只輸出機器可讀的路徑。

- [x] 寫測試：只提供外部 `work-journal.json` 時真實 server 可啟動；logger 寫入後 MCP 查到同一字串；活動覆寫的結果兩者一致；不存在設定、空 notes list、不可寫活動目錄有明確錯誤。使用臨時資料，不把缺少私人 config 的 early return 算成功。

```typescript
const result = await runSmoke(command, args, fixtureEnv);
expect(result.tools).toContain('log_activity');
expect(result.tools).toContain('query_activities');
expect(result.roundTrip).toBe(true);
```

- [x] 執行 `npm --prefix skills-query-server run test:unit -- src/stdio.integration.test.ts` 與 `bash activity-logger/tests/test_shared_config.sh`，確認失敗。
- [x] 更新啟動入口、兩個 logger 腳本與初始化設定。使用 Task 2 的有效設定，不再從程式旁讀私人 config 作團隊啟動的必要條件；保留來源開發時明確傳入 config 的測試能力。Logger 記錄格式、reference locator 與現有 MCP 工具 schema 保持相容。
- [x] 跑 MCP 測試、`npm --prefix skills-query-server run build`、兩個 logger shell 測試（含 `test_reference_logging.sh`）、真實 smoke client。打包前使用 lockfile 安裝 production dependencies，不在使用者每次啟動時下載或編譯。對已修改 skills 執行 skill-auditor。

**Deliverable:** 本機寫入／查詢的行為證據；現有資料可直接被新設定引用。

### Task 5：七包定義與來源可攜性

**Files:** Create `plugin-packages.json`、`scripts/plugin_packaging/__init__.py`、`catalog.py`、`resources.py`、`tests/test_plugin_packages.py`；Modify 38 個候選中確實含固定 runtime 路徑或不可攜指示的 `SKILL.md`／references，包含 `skill-router`、`skill-sync`、`skill-auditor` 的安裝定位指示。

**Interfaces:** `load_packages(repo_root: Path) -> list[dict]`；`validate_packages(packages: list[dict], catalog: list[dict]) -> list[str]`；`collect_resources(repo_root: Path, package: dict) -> list[Path]`。套件欄位為 `name`、`version`、`skills`、`platforms`、`runtime_resources`、`requirements`、`dependencies`；七個新包初始版本為 `0.1.0`，既有 mods 的版本保持原值。requirements 提供 Task 2 的執行環境檢查輸入。依賴欄位為 `kind`（required／conditional／optional）、`provider`、`skills`、`condition`、`tested_versions`。

- [x] 寫 `test_exact_approved_membership`：七個名稱與每包成員等於規格；來源總數 38、無重複；生命週期不變。另測未知 skill、缺少資源、repo 外 symlink、私人 config 及 retired reviewer 被列成成員／依賴時拒絕產生；退役說明文字仍可保留。

```python
packages = load_packages(Path.cwd())
assert {p["name"] for p in packages} == {
    "quality-gates", "technical-decisions", "repo-workflow", "content-tools",
    "work-journal", "session-preferences", "skill-toolbox",
}
```

- [x] 跑 `python3 -m unittest discover -s tests -p 'test_plugin_packages.py' -v`，確認失敗。
- [x] 實作七包清單、白名單資源收集與依賴檢查。按原始內容逐處適配固定 runtime 路徑；保留程式識別字、引用來源、呼叫意圖及可選整合，不做全文盲目替換。toolbox 路由區分已安裝、可安裝及不可用入口；同步使用者來源與 plugin 管理的界線清楚寫入指示。
- [x] 重跑 package 測試及 `python3 scripts/validate_skills_catalog.py --check`；執行每個已修改 skill 的 audit，逐項修正或明確處置，報告不進發佈包。

**Deliverable:** 七包清單與可攜來源；沒有暗中新增 skills 或更改 catalog 生命週期。

### Task 6：產生完整發佈包與兩個 marketplaces

**Files:** Create `scripts/plugin_packaging/render.py`、`verify.py`、`scripts/build_plugins.py`、`scripts/check_plugin_release.py`、`tests/test_build_plugins.py`、`tests/test_check_plugin_release.py`、`plugins/claude/<七個名稱>/`、`plugins/codex/<七個名稱>/`、`.agents/plugins/marketplace.json`；Modify `.claude-plugin/marketplace.json`。

**Interfaces:** `render_package(repo_root: Path, package: dict, surface: str, destination: Path, contracts: dict) -> None`；`verify_release(repo_root: Path, contracts: dict) -> list[str]`。CLI `build_plugins.py --write` 產生受管目錄，`--check` 以臨時重建比較；`check_plugin_release.py` 檢查來源、manifest、marketplace、版本與資源。測試例的 repo_root 使用臨時 fixture repo，package 選擇 quality-gates，destination 位於該 fixture 的 `plugins/codex/quality-gates`。

- [x] 寫測試：原有兩個 mods 的 entries 保留；七包 sources 存在；品質包各平台只含對應 reviewer；Codex toolbox 不載入 Claude-only skill；user-only metadata 保留；缺資源、產物過期、含固定個人路徑、private config 或包外 symlink 時退出非零。

```python
render_package(repo_root, package, "codex", destination, contracts)
(destination / "skills" / "completion-gate" / "SKILL.md").unlink()
assert verify_release(repo_root, contracts)
```

- [x] 跑 `python3 -m unittest discover -s tests -p 'test_build_plugins.py' -v` 與 `test_check_plugin_release.py`，確認失敗。
- [x] 依 Task 1 的契約實作各平台 manifest／MCP／hooks；Codex 首版用使用者已確認的 `.codex-plugin/plugin.json`＋`.mcp.json` 相容格式，不同時加入根目錄 `plugin.json`。實測 `0.162.1` 的 portable 分支略過 hooks；恢復 portable 格式前需重新驗證。複製必要 runtime 檔案、已編譯 server 與 production dependencies。每包攜帶適用的 catalog／registry 資料，不暴露維護者設定。
- [x] 執行 `python3 scripts/build_plugins.py --write`、`python3 scripts/build_plugins.py --check`、`python3 scripts/check_plugin_release.py` 及 `claude plugin validate` 對各 Claude 包和 marketplace；重建兩次無差異。將產物複製到含空白／非 ASCII 的新根目錄，以 smoke client 從不同工作目錄驗證真實 server。

**Deliverable:** 可由 Git marketplace 直接安裝的完整產物，不需要安裝者建置 repo。

### Task 7：必要路由與 Superpowers 相容性

**Files:** Create `runtime/agent_skills_runtime/policy.py`、`tests/test_plugin_policy.py`、`docs/plugins/superpowers-compatibility.md`；Modify 受影響套件的產生模板及七包依賴清單。

**Interfaces:** `render_policy(package: dict, surface: str, installed: dict) -> tuple[str,list[str]]` 產生限該套件的路由內容與問題；`check_superpowers(required_skills: list[str], installed: dict, tested_versions: list[str]) -> list[dict]` 依 Task 1 的正式發現方式取得 plugin 資訊，不掃描私人內容。

- [x] 寫測試：technical-decisions 使用自有 brainstorming，quality-gates 使用自有 completion-gate 與平台 reviewer；偏好 `off` 不移除工程路由；只裝 content／journal／preferences 不會硬要求 Superpowers。未安裝、缺必要 skill、未測版本分別回報，不能偽造相容。

```python
package = next(p for p in load_packages(Path.cwd()) if p["name"] == "quality-gates")
content, issues = render_policy(package, "codex", {})
assert "code-review-codex" in content and "code-review-claude" not in content
```

- [x] 跑 `python3 -m unittest discover -s tests -p 'test_plugin_policy.py' -v`，確認失敗。
- [x] 實作包內政策注入及相容性檢查，依必要／條件／可選關係回報。上游 source 不同但實際 identity 與版本相容時可辨識；Claude 跨 marketplace 依賴按官方允許機制處理。路由明確尊重使用者及上層指示，保留 manual checkpoint。
- [x] 重跑政策與產生器測試、重新產生包裝；在兩個 CLI 的乾淨配置測試自然語言的需求探索／review／完成驗證，記錄實際被選 skill、Superpowers 版本及 hooks 信任狀態。人工限定入口用一般確認與明確呼叫分別驗證。

**Deliverable:** 不依賴維護者全域 AGENTS.md 的路由，及按實際版本取得的相容性結果。

### Task 8：可回復遷移、更新與團隊發佈指引

**Files:** Create `runtime/agent_skills_runtime/migration.py`、`tests/test_plugin_migration.py`、`tests/test_plugin_update.py`、`docs/plugins/README.md`、`installation.md`、`migration.md`、`team-instructions.md`、`docs/validation/skill-plugins/acceptance.json`；Modify `README.md`、`README.zh.md`；產生七包各自的 README。

**Interfaces:** `plan_migration(existing: dict, selected_packages: list[str]) -> dict` 回傳 `{operations, confirmed: false}`；operations 每項含 path、action、before_hash 與備份資訊。`apply_migration(plan: dict, backup_root: Path) -> Path` 僅執行已確認清單；`restore_migration(manifest_path: Path) -> None` 恢復已備份項目。`check_updates(config_root: Path, defaults: Path) -> list[dict]` 列出被覆寫且預設已變更的模組。

- [x] 寫測試：預覽完整列出全部要處理的項目，未確認時無寫入；不相關設定及 user skills 保留；相同功能的舊 hook／MCP 入口被切換；活動資料不搬移；恢復後配置內容與原始一致。舊設定在預覽後有變更時拒絕套用，避免覆蓋新內容。

```python
plan = plan_migration(existing, ["work-journal"])
assert plan["confirmed"] is False
with self.assertRaises(PermissionError):
    apply_migration(plan, backup_root)
```

- [x] 跑 `python3 -m unittest discover -s tests -p 'test_plugin_migration.py' -v` 與 `test_plugin_update.py`，確認失敗。
- [x] 實作備份、清單確認與恢復；提供無私人語氣及路徑的團隊指示範本。更新測試先安裝初始包，再換新版預設／hook 定義，確認個人副本與資料設定保留、預設變更提示及 Codex 重新信任流程可辨識。
- [x] 寫兩個 CLI 的精確安裝、首次設定、檢查、更新、停用、移除、恢復指令與七包用途範例，使用 Task 1 的實測格式。重新產生及檢查完整產物；整理兩個 CLI 的所有驗收項目為 `verified`／`failed`／`not_verified`，只有真實驗證可列 `verified`。
- [x] 跑所有受影響的 Python／Node／shell 測試、catalog check、build check、release check、必要 skill audits；依 completion-gate 檢查實際差異與風險。先取得完整兩個 CLI 驗收證據，再提出具體 commit／發布內容請使用者批准。

**Deliverable:** 同事可按文件安裝、更新及恢復，且完整發布結果有實測依據。

## 計畫自查與交接

| 規格 | 實作任務 |
| --- | --- |
| 範圍、七包、平台差異與來源管理（1–3） | 1、5、6 |
| Superpowers、必要路由、呼叫意圖（4） | 1、5、7 |
| 共用設定、個人覆寫（5） | 2、3、8 |
| MCP、logger、hooks（6） | 1、3、4、6、7 |
| 三層驗收與最小驗證（7） | 1、各任務行為測試、8 |
| 遷移、更新、團隊範本與發布（8） | 8 |
| 證據差異與不確定性（9） | 1 的停止條件與 8 的驗收狀態 |

Task 1–8 的實作與驗收已完成，證據整理在 `docs/validation/skill-plugins/`。本分支仍未提交；提交須另取得使用者明確同意。

`NOT VERIFIED`：Git 遠端 marketplace 安裝／更新、Claude 在 strict fixture 外的自動 MCP 發現、其他 Superpowers 版本與其他作業系統尚未驗證。隔離驗收清理後，Codex 設定檔與 Claude plugin registry 有未選套件的語意雜湊差異；目前兩個 CLI 都查不到測試套件或測試 marketplace，但因未保留原始欄位值，無法判定這些差異由哪個 CLI 操作造成。未手動還原或改寫原生設定。細節見 `docs/validation/skill-plugins/acceptance.json` 與 `native-acceptance-cleanup.json`。
