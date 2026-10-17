# Skills 七包 Plugin 設計

日期：2026-10-13

狀態：使用者已於 2026-10-13 核准本書面規格；兩個 CLI 的完整七包運作仍待實作與驗收。

適用環境：Claude Code CLI、Codex CLI。使用者於 2026-10-13 明確縮減支援範圍，不支援 Codex 桌面版；桌面探測的來源衝突保留為失敗記錄。

## 1. 目的與範圍

將現有 skills 按使用者要完成的工作包裝為七個可選 plugins，透過 Git marketplace 分發。團隊共用工具與預設規則，每位使用者的 MCP server 在本機啟動，查詢自己的活動紀錄與筆記。第一版不建中央服務，也不以官方公開目錄上架作為交付條件。

來源範圍是 `skills-catalog.json` 中 34 個 `promoted`，加上 `code-review-codex`、`work-log-analyzer`、`session-preferences`、`control-return`，合計 38 個候選 skills；另包含 `skills-query-server`。這四個例外保留目前生命週期標記，打包不等於改成 `promoted`。

Superpowers 是沿用上游安裝的外部依賴，不計入這 38 個 skills。必要依賴按流程定義，不能因文件的 Related Skills 提及某個 skill，就把它列成必裝項目。既有 `attention-mod`、`handoff-mod` 留在 marketplace，維持原本的功能與發布流程。

發佈包及安裝指示不得依賴維護者的帳號路徑、私有設定或個人語氣檔。使用者自己的資料路徑只存在本機設定；程式可以在執行時解析當前使用者的家目錄。

## 2. 七包成員

下表的名稱是第一版提議的 plugin 識別名稱，書面審核時可調整。數量計算的是來源 skills，不表示每個平台都載入同一組元件。

| Plugin | 用途 | Skills | 數量 |
| --- | --- | --- | ---: |
| `quality-gates` | 審查程式碼、核對文件、驗證完成結果 | `code-review-claude`、`code-review-codex`、`completion-gate`、`codebase-audit`、`pr-review-assistant`、`secure-ai-development-gate` | 6 |
| `technical-decisions` | 從想法、研究走到需求與技術設計 | `brainstorming`、`assumption-extractor`、`critical-research`、`deep-reading`、`micro-poc-validator`、`narrative-auditor`、`research-cross-validator`、`research-synthesis`、`tech-feasibility`、`tech-research-pipeline`、`role-orchestrator`、`role-pm`、`role-rd`、`spec-gap-finder`、`technical-proposal-review`、`ui-design-analyzer` | 16 |
| `repo-workflow` | 理解歷史、同步 repo、交接工作 | `code-story-teller`、`repo-sync`、`handoff` | 3 |
| `content-tools` | 規劃簡報、產生內容、翻譯與轉換 | `presentation-planner`、`interactive-presentation-generator`、`sepia`、`md-translate`、`pptx-to-md` | 5 |
| `work-journal` | 記錄與查詢本機工作資料 | `activity-logger`、`work-log-analyzer` | 2 |
| `session-preferences` | 自訂整個 session 的互動方式 | `session-preferences`、`control-return` | 2 |
| `skill-toolbox` | 建立、檢查、探索與維護 skills | `skill-auditor`、`skill-router`、`skill-sync`、`claude-workflow-designer` | 4 |

`work-journal` 另外帶 MCP server；`session-preferences` 另外帶兩個偏好 hooks。

`brainstorming` 要求在特定情況呼叫研究 skills，`tech-research-pipeline` 又以 `brainstorming` 開始。把它們放在 `technical-decisions` 內，可避免按原 catalog 分類拆開後形成雙向 plugin 依賴。`technical-decisions` 有 16 個入口，README 要按「探索需求／評估技術／審查提案／PM→RD」提供範例，減少使用者的選擇負擔。

平台配置：Claude Code 的品質套件載入 `code-review-claude`，Codex 載入 `code-review-codex`。`claude-workflow-designer` 標示為 Claude Code 專用；Codex 的套件說明要列出這項差異。保留來源的手動呼叫限制，plugin 命名空間與 router 推薦不構成啟動 user-only skill 的授權。

## 3. 原始內容、套件定義與發佈包

維持現有頂層 skill 目錄，每個 skill 只有一份維護來源。一般可攜性修改在來源處理；平台專用內容由明確的適配規則處理，不手工維護兩份副本。

新增 `plugin-packages.json`，記錄七包的成員、版本、平台適用性、必要資源、依賴種類與平台適配。`skills-catalog.json` 仍是生命週期與呼叫意圖的來源；套件清單只記錄打包資訊。

產生結果存放於 `plugins/claude/<plugin-name>/` 與 `plugins/codex/<plugin-name>/`。這些是產生的發佈目錄，不直接編輯。Git marketplace 指向已存在於發布 commit 的完整目錄，安裝者不需要先建置 repo。

```text
現有 skills／scripts／references + skills-catalog.json
                         │
                plugin-packages.json
                         │
                  產生與驗證發佈包
                  ┌──────┴──────┐
           plugins/claude/  plugins/codex/
                  │             │
      .claude-plugin/       .agents/plugins/
      marketplace.json      marketplace.json
```

Claude 發佈包使用 `.claude-plugin/plugin.json`。Codex 首版使用 `.codex-plugin/plugin.json` 與 `.mcp.json` 相容格式，skills、hooks 與 server 資源仍放在 plugin 根目錄。Codex `0.162.1` 實測會略過 Agent Plugins 根目錄 manifest 的 hooks；使用者已確認改採相容格式。不得同時加入會優先選用的根目錄 `plugin.json`；日後恢復 portable 格式需重新通過平台 hooks 驗證。MCP 與 hooks 分別產生平台所需格式，詳見 [實測記錄](../../validation/skill-plugins/README.md)。

包內包含實際執行所需的 skills、腳本、references、assets 與執行依賴。不得透過 `../` 或外部 symlink 讀取未打包資源。開發文件、測試產物、私人 `config.json`、本機紀錄及憑證不進發佈包。

發佈驗證需檢查套件清單與 catalog 的對應、遺漏及重複成員、資源是否完整、原始內容與產生結果是否一致。平台必要的複製不算來源成員重複。來源變更後，產生結果未更新就不能通過發佈檢查。

## 4. Superpowers 與必要路由

沿用 [Superpowers 官方安裝方式](https://github.com/obra/superpowers)，各執行環境分別安裝。Claude Code 官方 marketplace 與 Superpowers 自有 marketplace 都有安裝入口；Codex CLI 也有上游 plugin 入口。

依賴按用途分類：

| 關係 | 處理方式 |
| --- | --- |
| `brainstorming` 的多步驟設計轉實作 | 需要 `superpowers:writing-plans`，在交接前檢查可用性 |
| PM／RD 設計後的計畫或執行 | 依選定分支檢查 `writing-plans`、`subagent-driven-development` 等必要 skills |
| 研究結果轉實作計畫 | 選擇該分支時才需要 `writing-plans` |
| `completion-gate` 提及 TDD、review、收尾 | 依整合流程檢查，不能把單獨完成驗證改成一律需要 Superpowers |
| `skill-router` 推薦 Superpowers 流程 | 確認實際可用；未安裝時提供安裝資訊，不推薦不存在的入口 |
| `activity-logger` 的 `lesson`、簡報的 `report-generator` | 保持可選整合，不因此增加第一版成員 |

本機已觀察到 Superpowers `7.0.0`，可作為首輪相容性測試候選；這不構成最低版本或整個版本系列均相容的證據。測試後記錄相容版本與必要 skill 契約，不宣稱未驗證版本可用。

Claude 的 `dependencies` 與版本約束可作為原生安裝機制，但跨 marketplace 來源及允許清單須按官方規則處理。Codex 的等價依賴行為尚未確認，先把跨平台的可用性檢查列為必要條件，不假設同一份宣告會自動安裝全部依賴。

團隊版需自行攜帶必要路由：需求探索用本套件的 `brainstorming`；完成驗證用本套件的 `completion-gate`；一般 review 使用當前平台的原生 reviewer。保留 Gemini reviewer 退役規則及外部 reviewer 的明確選擇與資料範圍確認要求。

書面規格提議將這些路由隨受影響套件的 SessionStart hook 注入，作用範圍只涵蓋該套件；不依賴可選的對話偏好 plugin 或維護者全域 AGENTS.md。這是必要路由載入的實作提議，需隨本書面規格確認及實測。偏好 hooks 仍屬於獨立的 `session-preferences` plugin。使用者明確指示與上層 policy 優先；驗收需確認路由能在同時安裝 Superpowers 的乾淨環境生效。

`skill-router` 使用打包後的 registry 與套件資訊，區分已安裝可用的入口、可安裝的套件與可選整合，保留每個 skill 的呼叫意圖。`skill-sync` 管理使用者的獨立 skill 來源；plugin 的更新由各平台管理，不能透過同步產生第二份同名 plugin skills。

## 5. 共用個人設定與偏好覆寫

同一位使用者的 Claude Code 與 Codex 讀取同一份個人設定。設定根目錄優先採用 `AGENT_SKILLS_CONFIG_DIR`；未設定時採用 `XDG_CONFIG_HOME/agent-skills`；兩者都未設定時，使用目前使用者家目錄下的 `.config/agent-skills`。兩個平台採用相同解析契約，使用者可在首次設定時確認有效目錄。偏好與資料設定不放在 plugin 的版本快取中。

```text
使用者設定目錄/agent-skills/
├── work-journal.json       活動紀錄與筆記的資料來源
└── preferences/
    ├── INDEX.md            個人模組與覆寫清單
    └── <module>.md         個人規則
```

載入時先依套件 `references/INDEX.md` 讀預設模組，再套用個人清單：同名模組整份覆寫，不同名模組追加。按需讀取的 references 也要能找到對應的個人覆寫或套件檔案，並提供模型可讀的實際路徑。

`add-rule`／`add-deai` 維持先提議、使用者確認才寫入的流程。已有個人模組時更新該檔；首次覆寫既有模組時建立個人副本後修改；新增模組時更新個人 INDEX。記錄副本採用的預設版本或內容雜湊，以便更新時列出有個人覆寫且預設已變更的模組。套件更新保留個人副本，不自動合併規則。

同名覆寫的代價是新版預設修改可能被遮住，因此更新提示需讓使用者決定維持副本或重新採用預設。規則之間的衝突按既有流程回報，不以 INDEX 載入順序偷偷決定優先權。

`control-return` 的個人覆寫使用 `preferences/control-return.md`，完整檔案內容作為規則；它由自己的 hook 讀取，不列入 session-preferences 的個人 INDEX。未覆寫時使用套件的既有規則。兩個偏好 hooks 保留 `AGENT_SESSION_PREFS=off`，且這個開關只控制偏好注入，不控制工程路由或 MCP server。

## 6. MCP 與 SessionStart hooks

### MCP

`work-journal` 攜帶編譯後 JavaScript、必要執行依賴與平台 MCP 宣告。建置在發佈前執行；使用者需要 Node.js，正常啟動不依賴 `npx tsx` 或本機 TypeScript 建置。由平台管理 stdio server 的生命週期，不另設常駐中央服務。

`work-journal.json` 保留現有 `sources.activities`、`sources.notes.paths`、`recursive`、`exclude_hidden` 契約。首次設定選擇活動紀錄與至少一個筆記目錄；可建立空的個人資料目錄，不要求事先有資料。設定存在套件之外，取代目前 server 從程式旁讀取私人 `config.json` 的方式。

Logger 與 MCP 從同一份資料設定取得活動目錄。既有 `CLAUDE_ACTIVITIES_DIR` 保留為明確覆寫入口；使用時查詢與寫入必須得到相同的有效目錄，設定檢查顯示解析結果。

各平台 renderer 使用已驗證的 MCP 工作目錄與路徑解析契約，不能把 shell 變數當成一定會在 JSON 的 `args` 中展開。包裝後從不同工作目錄啟動、含空白路徑與缺少執行環境都列入驗證。

首次設定提供檢查與設定腳本，列出缺少的 Node.js、Python、外部 plugin、設定或資源。MCP 未設定時回報具體設定方式，不填入維護者的私人路徑。正常已設定的使用者開新 session 不需重新設定。

### 偏好 hooks

打包現有兩個 Python 腳本及其規則資源，維持從安裝位置定位檔案的方式；需要 Python。覆寫載入與錯誤回報須在共用設定層處理，避免兩個平台讀不同版本的個人規則。

使用 SessionStart 的 `startup`、`resume`、`clear`、`compact` 來源。規則載入成功才回報有效；缺檔、無效模組或個人規則解析失敗時，按可辨識的狀態回報，不能聲稱完整套用。沿用目前不因規則檔問題阻擋 session 啟動的行為。

Codex 的非受管 hooks 要由使用者檢視並信任，更新後定義有變更可能需要重新信任。安裝與更新指引納入這項平台流程；安裝成功不等於 hooks 已執行。

舊全域 hooks 與 plugin hooks 可能同時載入。檢查腳本需列出同一功能的重複註冊，遷移時處理舊入口；不能用新設定優先權假設舊 hooks 已被取代。

## 7. 驗收與最小驗證

在實作完整產生器前，先以最小包裝實驗確認 MCP 路徑解析、必要依賴可用性、路由注入及兩個偏好 hooks 在兩個 CLI 的載入方式。這是實作計畫的第一道門檻；不是本次文件工作已完成的測試。

若某環境不能載入必要元件，需回到設計調整包裝或安裝方式，不能把減少該環境支援當成通過驗收。缺少依賴、無效設定及未信任 hooks 必須有具體回報，不能默默省略流程。

| 驗收項目 | 成功條件 |
| --- | --- |
| 兩個 CLI | Claude Code CLI、Codex CLI 從乾淨配置安裝並發現各自適用的元件 |
| 個人路徑 | 在不同帳號／安裝根目錄與含空白路徑下執行；發佈包不含固定維護者路徑或私人配置 |
| MCP | 平台完成初始化、列出工具，並以測試資料完成一次活動寫入及查詢；資料來源一致 |
| Hooks | 各支援 SessionStart 來源能注入規則；停用開關有效；缺檔及未信任狀態能辨識 |
| 模型行為 | 代表性情境遵守路由與偏好：釐清需求不硬附三步、交還控制權提供三個具體選項與推薦理由 |
| 上游依賴 | 已安裝相容 Superpowers 時可找到需要的 skills；缺少或不相容時指出受影響流程 |
| 呼叫意圖 | 手動限定的 skills 不因 router 推薦、一般確認或 hook 載入就被自動呼叫 |
| 更新 | 個人規則與資料設定保留；能辨識被覆寫模組的預設變更；需要重新信任的 hooks 有提示 |
| 清單與資源 | 38 個候選都有歸屬，沒有額外來源成員；資源完整，平台配置與產生結果符合定義 |
| 遷移 | 舊入口切換後沒有重複載入；保留備份及恢復方式，測試能回到原配置 |

驗證分三層：純檔案與宣告的 deterministic checks、腳本／設定／MCP 的行為測試、兩個 CLI 的安裝與模型行為驗收。前兩層通過不能當成第三層已通過。每個平台保留實測版本與結果；未測的平台或情境標為 `NOT VERIFIED`。

## 8. 遷移與發布

遷移前盤點舊 user-level skills、hooks、MCP 註冊與全域路由。區分本套件相關項目與使用者其他工具，列出需要切換的檔案和設定。

```text
盤點與預覽 → 備份原設定 → 安裝新 plugins → 驗證新功能
                                           │
                             切換舊入口、檢查重複載入
                                           │
                              保留備份與恢復方式
```

舊個人資料目錄可直接由新設定引用；搬移資料不是必要步驟。舊全域指示若指向獨立 skill 目錄，遷移清單需指出並提供替換方式。提供去除個人語氣及私有設定的團隊指示範本，不把維護者目前的完整全域設定當成團隊預設。

七包各自記錄版本，發佈時重新產生兩個平台的產物及 marketplace，執行相應驗證。改動 hooks 或執行行為時升版，避免快取未刷新。Source、manifest、marketplace 與版本記錄需一致。Commit、push 與發布仍各自需要使用者明確同意。

## 9. 證據、取捨與尚未驗證項目

可行性評估為 `Conditional-Go`。`tech-feasibility` 檢查平台能力、啟動與設定保存；`critical-research` 檢查快取、資源邊界及依賴差異等反例；`research-synthesis` 將結果整理為本規格。這些是文件與程式碼的研究，不是兩個 CLI 的完整實測。

| 證據 | 設計影響 |
| --- | --- |
| `brainstorming` 必要研究步驟與 `tech-research-pipeline` 第一階段互相呼叫 | 放進同一個 `technical-decisions` plugin |
| Claude 會快取 plugin，跨出根目錄的資源不隨包裝複製 | 產生完整實體發佈目錄，不依賴 repo 外連結 |
| Claude 有 plugin 依賴及版本約束；Codex 等價行為未確認 | 共用依賴資料，平台分別產生宣告與可用性檢查 |
| Codex hooks 文件支持 plugin hooks 與 CLI 信任流程；包裝頁另有手動桌面安裝的範圍說明 | 兩個 CLI 均保留實測門檻，不從單一頁面推論全部安裝路徑等價 |
| MCP 現有程式從程式旁讀 `config.json`，偏好修改也直接改 references | 個人設定與覆寫移到版本快取之外 |

七包方案比五包方案多兩組版本與驗收工作，但入口更貼近使用目的。五包方案會把品質、技術決策與 repo 工作合成 25 個 skills 的工程大包；使用者已選擇七包。

主要失敗情境是發佈包遺漏資源、來源變更沒有重新產生、上游更新改變契約，或舊入口與新 plugin 重複載入。對應控制是資源與一致性檢查、版本相容性記錄，以及可回復的遷移驗收。

`NOT VERIFIED`：兩個 CLI 的完整七包乾淨安裝、Codex 的依賴解析與本機 MCP 路徑展開、實際 hook 注入及模型遵守、更新後設定保存、遷移與回復。最低 Node.js／Python／平台版本以實測及執行依賴契約決定；目前觀察到的本機版本不當作最低支援版本。

## 10. 參考來源

- [Skills catalog](../../../skills-catalog.json)
- [Brainstorming 流程](../../../brainstorming/SKILL.md)
- [完整研究流程](../../../tech-research-pipeline/SKILL.md)
- [MCP 啟動入口](../../../skills-query-server/src/index.ts)
- [Session preferences hook](../../../session-preferences/scripts/session_start_hook.py)
- [Control return hook](../../../control-return/scripts/session_start_hook.py)
- [Claude plugin manifest](https://code.claude.com/docs/en/plugins-reference)
- [Claude plugin dependencies](https://code.claude.com/docs/en/plugin-dependencies)
- [Claude plugin loading](https://code.claude.com/docs/en/plugins/loading)
- [OpenAI plugin packaging](https://developers.openai.com/plugins/build/plugins)
- [Codex hooks](https://learn.chatgpt.com/docs/hooks)
- [Superpowers](https://github.com/obra/superpowers)

下一階段：使用者檢視並確認本書面規格後，進入實作計畫；第一項工作是最小跨平台驗證。
