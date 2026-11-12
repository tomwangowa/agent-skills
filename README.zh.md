# Claude Code Skills

[English](./README.md) | **繁體中文**

一套在實務工作中長出來的 Claude Code 技能集。

這些 skills 不是為了展示 AI 能做什麼，而是為了解決一個具體問題：**當你把越來越多工作交給 AI，如何確保產出的品質不會隨著信任的增加而下降？**

我的做法是把工程紀律嵌入 AI 工作流程本身——用結構化流程對抗 AI 和人類共有的認知盲點。具體來說：

- **結構化 Code Review**：任何模型在檢視自己的產出時都會過度合理化——所以 review 是 skill 觸發的明確步驟，不是口頭承諾。一般 review 依目前 runtime 選原生 reviewer：Claude Code 用 `code-review-claude`，Codex 用 `code-review-codex`。`code-review-gemini` 已退役，不會自動執行。
- **Falsification-first**：研究類 skills 要求先搜尋反面證據，再搜尋支持證據。這不是悲觀，而是對確認偏誤的系統性防禦。
- **Evidence before assertion**：在宣稱任何工作「完成」之前，必須先執行驗證命令並確認輸出。說「通過測試」的前提是真的跑過測試。

這些原則不需要你同意我的做法——它們是可以拆開使用的獨立模組。你可以只用 code review，只用 research，或只用 presentation generator。每個 skill 都是自足的。

---

## CLI Plugin 套件

七包定義涵蓋 48 個來源 skills，支援 Claude Code CLI 與 Codex CLI。2026-10-15 的原生驗收在 macOS 隔離 fixture 上，使用 Claude Code CLI 2.1.300 與 Codex CLI 0.162.1 涵蓋七包；七包在那之後都有修改，發布前需要重新驗收。2026-10-17 另以 Claude Code CLI 2.1.302 驗證 GitHub marketplace 安裝與更新檢查；Codex CLI 的遠端 Git marketplace 尚未測試，發布也尚未核准。詳見[驗收紀錄](docs/validation/skill-plugins/acceptance.json)與 [plugin 文件](docs/plugins/README.md)。來源生命週期保留；standalone hooks 與 journal 工具也需要 bundled runtime 和下方的外部共用設定。

## 安裝包候選版本

用以下命令產生一份可交給同事的壓縮包；建置過程不下載工具，也不重建 plugins：

```bash
python3 scripts/build_plugin_installer.py --output dist/agent-skills-installer.zip
```

最近一次有紀錄的壓縮包驗收是 [R19](docs/validation/plugin-installer/candidate-r19.md)。ZIP 與校驗檔只存在本機 QA 目錄，沒有放進 repo 或發布。R19 尚未包含此分支後續新增的 Codex 原生移除能力判斷，不能代表目前安裝器原始碼。R19 僅允許 Superpowers 在兩個已逐檔比對的 Claude 官方目錄快照之間變更後通過安裝後驗證；未知快照仍會標示未驗證。首次設定 work-journal 時，工作紀錄預設存到 `~/.agent-skills/activities`，筆記路徑可略過；有效的既有設定會沿用，寫入新設定前也會重新確認已安裝版本。目前原始碼尚不適合交給同事安裝：work-journal 0.2.1 與 session-preferences 0.1.5 目前只存在這個工作目錄，Claude／Codex 原生驗收綁定也已過期。先前候選包與 R11 專屬的原生驗證紀錄均保留。

完整解壓後，macOS 開啟 `install-macos.command`，Ubuntu／Debian 執行 `bash install-linux.sh`，Windows 在既有 PowerShell 政策下執行 `./install-windows.ps1`。需要真正可用的 Python 3.11+，以及已安裝的 Claude Code CLI 或 Codex CLI；入口可透過現有且受支援的管理工具提出 Python 補裝方案，不代裝主程式、套件管理工具或登入認證。操作方式見[壓縮包說明](installer/README.md)，證據範圍見[驗證紀錄](docs/validation/plugin-installer/README.md)。

選單會分別預覽並確認來源下載、缺少的工具、plugin 安裝與選用的日誌設定。本 repo 適用套件預設勾選；既有 plugins 預設保留，更新要另外選。Superpowers 強烈建議安裝，但不預選。取消會停止後續工作，先前已批准的寫入仍保留。Windows 偏好寫入／遷移仍有 POSIX 鎖限制。**這是安裝包候選版本，尚未完成三平台原生驗收。** Codex 在已檢查的 CLI 0.167.0 上，新增安裝會核對實際 JSON 結果與完整安裝內容；既有安裝仍暫停更新。Superpowers 優先使用各 CLI 官方目錄：Claude 的 `claude-plugins-official` 是 `7.0.0`、來源固定在上游 Git commit；Codex 的 `openai-curated` 或原生選用的 `openai-api-curated` 是 `6.3.0`、內容位於官方目錄內，兩邊版本可以不同。既有 provider（包含 `7.0.2`）一律保留，不更新、啟用、重複安裝或降版。Codex 官方目錄需由原生 `/plugins` 流程準備，安裝器不補寫受管理狀態，也不新增或刷新這個保留目錄。缺少完整內容指紋或精確 CLI／平台／架構驗收時，只暫停 Superpowers 與其依賴補裝；R7 的能力紀錄只開放已驗證的 macOS arm64 Claude 2.1.322 官方目錄與 Codex 0.167.0 API 官方目錄情境，其他環境仍暫停 Superpowers。安裝結果、重啟後入口與實際工作流程分開驗證，後兩項尚未驗證。目前沒有宣稱已發布的下載網址。

同事若已透過公司 AI endpoint 使用 Codex、沒有登入 ChatGPT，R7 會依 Codex 原生回報的官方目錄處理，保留既有 endpoint 與認證設定。公司模型服務可用，不代表套件下載來源也可連線。離線測試與 [macOS Codex 0.167.0 原生測試](docs/validation/plugin-installer/codex-no-account-native-results.md)已涵蓋這個情境；原生測試在未登入時成功安裝 Superpowers，並保留假的公司模型設定。真實公司連線與其他平台尚未驗收，R5 尚未包含此修改；操作方式見[公司 endpoint 情境](installer/README.md)。 Claude Code 2.1.322 在 macOS arm64 也已通過[已登入／未登入兩組原生安裝](docs/validation/plugin-installer/claude-login-matrix-results.md)，兩組都是 Superpowers 7.0.0；R7 已納入這些能力紀錄與去除敏感資訊的證據摘要；同一份 ZIP 隨後通過三組 macOS arm64 的[原生安裝與重跑驗收](docs/validation/plugin-installer/r7-native-acceptance-results.md)。

## 從工作場景選套件

R5 已在 macOS 26.6.2 arm64／Claude Code 2.1.322 與 Codex 0.167.0 分輪驗證
全部 16 個自有套件安裝項目：Claude 九包、Codex 七包。實測見
[quality-gates 紀錄](docs/validation/plugin-installer/macos-r5-native-results.md)與
[其餘套件紀錄](docs/validation/plugin-installer/macos-r5-remaining-results.md)。
範圍限於安裝與完整檔案內容；Superpowers、其他平台與 hooks／MCP／skills 執行仍未驗證。

以下使用實際打包的入口。Claude Code 用 `/套件:skill`，Codex 用 `$套件:skill`；明列入口的例子要由使用者親自呼叫，流程推薦另一包不代表已安裝，也不等於已經手動呼叫。

### 場景：把模糊需求做成可驗證的修改

需求還像「幫同事加一個入門流程」時，搭配 `technical-decisions`、Superpowers 與 `quality-gates`。先說：「實作前先釐清需求與替代方案，一次問一個問題。」核准設計後，再選計畫與執行方式；修改後請 agent 審查，會依目前宿主使用 `code-review-claude` 或 `code-review-codex`。預期取得已核准設計、工作計畫、審查過的修改，以及驗證證據與缺口。Superpowers 步驟要另外安裝並確認可用；沒裝時，其他兩包仍有獨立的研究與審查用途。查資料、模型呼叫與專案測試依選定流程確認範圍。

### 場景：看懂陌生專案，下次能接著做

動不熟悉的模組之前，先用 `repo-workflow`。手動執行 `/repo-workflow:understand-repo <路徑>` 或 `$repo-workflow:understand-repo <路徑>`，再用 `/repo-workflow:task-bootstrap <任務>` 或 `$repo-workflow:task-bootstrap <任務>` 預覽新分支與 worktree。離開前手動呼叫這包的 `handoff`，下次呼叫 `session-start`，例如 `$repo-workflow:session-start`。預期取得有原始碼依據的專案理解、隔離的工作目錄與重驗前提的交接。需要 Git；建立分支、複製本機檔案有各自的預覽，這些手動入口不會因流程推薦就自行執行。

### 場景：長時間使用 Claude Code，回來時看得懂進度

在 Claude Code 加裝 `attention-mod` 與 `handoff-mod`。`/attention` 開啟注意事項面板，`/handoff-mod:handoff` 手動建立交接，`/handoff-resume` 列出可接續的工作。預期看到進度面板與留給下個 session 的紀錄。Attention 摘要會把對話／工具節錄交給 `haiku`，消耗模型 token；handoff mod 本身不呼叫模型，手動執行其 skill 才使用目前 session 的模型。自動筆記、store 寫入與遮蔽限制見[交接說明](plugins/handoff-mod/README.md)。Attention 需要 Claude Code 2.1.312+；兩包仍是原型，不列為 Codex 選項，也和 `repo-workflow` 的交接入口分開。

### 場景：把工作紀錄整理成週報

用 `work-journal` 說：「記錄今天已完成的工作與實際參考過的文件」，之後再問：「整理本週工作，包含決定與未完成事項。」預期取得帶日期的活動紀錄與可回查來源的報告。首次設定時，工作紀錄預設存到 `~/.agent-skills/activities`；加入自己的筆記資料夾後，`work-log-analyzer` 也能和工作紀錄一起搜尋筆記。筆記路徑可略過，既有設定會沿用，安裝器不會搬移或讀取資料夾內容。查詢需要 Node.js／Python 與已宣告的命令工具；MCP 註冊改變後要重啟宿主。需要把報告做成簡報時，再搭配 `content-tools`。

### 場景：把技術工作講給不同對象聽

用 `content-tools` 說：「依這份大綱，替新同事規劃十分鐘的簡報」，或手動呼叫 `/content-tools:presentation-planner`／`$content-tools:presentation-planner` 並附上內容。預期先取得按聽眾需求安排的投影片計畫，再產生選定格式。說「把這份 Markdown 翻成英文與繁體中文」會用 `md-translate`，保留程式碼與連結。可搭配 `work-journal` 的工作證據，或 `technical-decisions` 的技術分析。Office 內容抽取可能需要 markitdown 與另行批准的依賴下載；發布與外部服務是另外的動作。

### 場景：讓回應規則前後一致

想固定語言、說明深度或歸還控制權時的選項，用 `session-preferences`。手動呼叫 `/session-preferences:session-preferences` 或 `$session-preferences:session-preferences` 重新檢視／套用規則，也可以提出新偏好；`control-return` 管理後續選項的呈現方式。預期取得本 session 的指示，需要儲存個人覆寫時再另外確認。共用設定放在 plugin 快取外；這次安裝器不提供原生 Windows 的偏好寫入／遷移修補。

### 場景：找適合的 skill，或檢查自己寫的 skill

用 `skill-toolbox` 說：「列出我的 skills，分清楚已安裝、可取得與不可用」，或呼叫 `/skill-toolbox:skill-router list`／`$skill-toolbox:skill-router list`。自己寫了 skill，可以請 `skill-auditor` 審查，取得問題與逐項處理結果。清單有名字不代表已安裝。`skill-sync` 是另一個必須手動執行的 standalone 鏡像同步流程，可能刪除目的端檔案；安裝器不會執行。`claude-workflow-designer` 僅供 Claude，Codex 套件不包含它。

| 套件 | 使用場景 |
| --- | --- |
| `technical-decisions` | 釐清需求、形成設計，也可替內容提供技術分析 |
| Superpowers | 選定的計畫、TDD 與執行步驟，需另外安裝／確認 |
| `quality-gates` | 審查修改與驗證結果 |
| `repo-workflow` | 理解專案、開新任務、交接與接續 |
| `attention-mod`、`handoff-mod` | Claude Code 進度面板與 session 交接 |
| `work-journal` | 活動紀錄與週報 |
| `content-tools` | 簡報、翻譯與對外文字 |
| `session-preferences` | 回應規則與後續選項 |
| `skill-toolbox` | 尋找 skills 與審查品質 |

## Skills Catalog

完整、生成式的 inventory，以及 lifecycle／surface 政策，都在 [SKILLS_CATALOG.md](./SKILLS_CATALOG.md)。若想依需求取得推薦，請用 `skill-router`。

### 手動研讀程式碼

`understand-repo`、`understand-file`、`understand-function` 都需要手動呼叫。Claude Code 與 Codex 已停用自動呼叫；路由器推薦也不會直接啟動它們。

| 研讀範圍 | Claude Code | Codex |
|----------|-------------|-------|
| 整個 repository | `/understand-repo` | `$understand-repo` |
| 單一程式檔案 | `/understand-file` | `$understand-file` |
| 函式或方法 | `/understand-function` | `$understand-function` |

在指令後加上 repository 路徑、檔案路徑或函式名稱。例如，Claude Code 使用 `/understand-file path/to/models.py`，Codex 使用 `$understand-file path/to/models.py`。

### Skills 維護

`skills-catalog.json` 是已追蹤 top-level skills 的治理來源，`SKILLS_CATALOG.md` 由它產生。改 catalog 後，執行 `python3 scripts/validate_skills_catalog.py --write`；commit 前執行 `python3 scripts/validate_skills_catalog.py --check`，確認 catalog、router、兩份 README、sync excludes 與生成的 index 一致。

若只想預覽同步且不改任何檔案系統內容，執行 `bash skill-sync/scripts/sync.sh --dry-run`；要預覽 additive mode，再加 `--no-delete`。一般 sync 仍是互動式操作，也可能建立設定的 target directories。

### Core Skills

<!-- core-skills:start -->
- [brainstorming](./brainstorming/SKILL.md) — 動手前先探索變更。
- [code-review-claude](./code-review-claude/SKILL.md) — 預設 code review。
- [code-review-codex](./code-review-codex/SKILL.md) — Codex 專用 review 路徑。
- [completion-gate](./completion-gate/SKILL.md) — 宣稱完成前先驗證。
- [handoff](./handoff/SKILL.md) — 留下可接手的 session 交接。
- [role-orchestrator](./role-orchestrator/SKILL.md) — 協調 PM → RD 工作。
- [skill-router](./skill-router/SKILL.md) — 找到適合的 skill 或 workflow。
- [skill-sync](./skill-sync/SKILL.md) — 同步 skills 到其他 agent surface。
- [tech-research-pipeline](./tech-research-pipeline/SKILL.md) — 跑一條嚴謹的研究流程。
<!-- core-skills:end -->

### MCP Server

將 skills 的資料查詢能力結構化為 MCP 工具，讓 Claude Code 能直接查詢你的工作歷史。

| Server | 說明 |
|--------|------|
| [skills-query-server](./skills-query-server/) | 提供 7 個結構化查詢工具：活動查詢、全文搜尋、活動記錄、時間軸追蹤、TODO 提取、決策追溯、工作儀表板。整合 activity-logger、work-log-analyzer、qa-to-notes 的資料來源（活動紀錄 + QA 知識筆記），透過 MCP 協議讓 Claude 直接存取。 |

**快速設定：**

```bash
# From a standalone clone, configure the selected data directories first.
# Review the preview; repeat without --preview to create missing settings.
export AGENT_SKILLS_CONFIG_DIR="$HOME/.config/agent-skills"
PYTHONPATH="$HOME/.claude/skills/runtime" python3 -m agent_skills_runtime.setup \
  --activities "/absolute/activities" --notes "/absolute/notes" --preview
npm --prefix "$HOME/.claude/skills/skills-query-server" ci
npm --prefix "$HOME/.claude/skills/skills-query-server" run build
claude mcp add -s user skills-query -- node "$HOME/.claude/skills/skills-query-server/dist/index.js"
```

詳見 [skills-query-server/README.md](./skills-query-server/README.md)。

## 關於 Code Review 的分層設計

**任何模型在檢視自己產生的程式碼時，都傾向對既有結構過度合理化。** 所以這個 repo 把 review 切成一個獨立步驟——以 skill 觸發、有 adversarial checklist、有 assumptions 清單——而不是靠「Claude 檢查一下自己寫的」這種同步審視。

### 依 runtime 分流的原生 reviewer

- **Claude Code → `code-review-claude`**：Claude 原生 review，包含 syntax 驗證、adversarial 檢查與 assumptions 清單。
- **Codex → `code-review-codex`**：Codex 原生 review，同樣先列 findings，再做本機驗證。
- **`code-review-gemini`**：已退役，只保留遷移參考；router、workflow 與 pre-commit 都不會執行它。

> **pre-commit auto-review** 依目前 runtime 選原生 reviewer。未來 RDSec endpoint reviewer 必須由你明確選擇模型，並確認可送出的 diff／資料範圍，才會向外送出。

---

## 關於研究管線

當 AI 幫你做技術評估時，最常見的失敗模式不是分析能力不足，而是**未經驗證的假設被包裝成結論**。一個看起來很完整的可行性報告，可能建立在 3 個從未測試過的隱性假設之上——直到實作時才發現底層根本不通。

研究管線（`tech-research-pipeline`）就是為了解決這個問題。它把 8 個研究 skills 串接成一條完整的驗證流水線，每個階段的產出成為下一階段的輸入：

```
brainstorming → tech-feasibility → assumption-extractor → micro-poc-validator
    → GATE A → critical-research → narrative-auditor → research-cross-validator
    → GATE B → research-synthesis → 決策文件
```

其中兩個閘門是關鍵設計：

- **Gate A**（micro-poc 之後）：如果 BLOCKING 級假設被實證推翻，**整條管線停止**，不浪費時間在已經失敗的基礎上繼續研究。
- **Gate B**（cross-validation 之後）：檢查所有階段的發現是否收斂一致。如果關鍵主張在不同驗證策略下互相矛盾，標記為 DISPUTED 而非硬下結論。

這條管線的設計來自一次痛苦的教訓：在一個 ScraperAPI 遷移專案中，一份看似完整的可行性報告漏掉了一個隱性假設（nodriver 不支援 WSS 連線），結果在實作數週後才發現整個架構不可行。如果當時有跑管線，Phase 3 的 micro-PoC 會在 Day 1 的 5 分鐘內就抓到這個問題。

你不需要每次都跑完整管線。每個 skill 都可以單獨使用——只是當決策的代價夠高時，完整管線能幫你在投入實作之前就找到那些「你不知道你不知道」的假設。

---

## 關於 Superpowers 插件 Skills

Superpowers 插件的 skills（writing-plans、executing-plans、systematic-debugging、TDD 等）從 [superpowers](https://github.com/obra/superpowers) 插件載入。啟用後以 `superpowers:skill-name` 格式出現（如 `superpowers:writing-plans`、`superpowers:systematic-debugging`），不需要本地副本或 symlink。

---

## Quick Start

### 前置需求

- [Claude Code CLI](https://docs.anthropic.com/en/docs/claude-code)
- [Node.js](https://nodejs.org/)（僅當想使用 Gemini 相關 skills 時需要）
- Git

### 安裝

**選項 1：直接 clone 到 skills 目錄（推薦）**

```bash
git clone https://github.com/tomwangowa/agent-skills.git ~/.claude/skills
```

**選項 2：Symlink 已有的 clone**

```bash
ln -s /path/to/cloned/repo ~/.claude/skills
```

### 設定 Slash Commands

Slash commands 放在 `~/.claude/commands/`，跟 skills 是不同目錄。主安裝完成後，把 repo 內附的 commands symlink 過去：

```bash
mkdir -p ~/.claude/commands
ln -s ~/.claude/skills/commands/sos.md ~/.claude/commands/sos.md
```

少了這一步，在 Claude Code 打 `/sos` 會出現「command not found」——即使背後的 `claude-workflow-designer` skill 已經裝好。

### 設定 Gemini CLI（選配）

任何 code review 流程都不會用 Gemini CLI：`code-review-gemini` 已退役。其他不相關的選配 skill 可能仍會使用它；除非那些 skill 提示需要，否則可跳過本節。

```bash
# 安裝 Gemini CLI
npm install -g @google/gemini-cli

# 設定 API key（從 https://aistudio.google.com/app/apikey 取得）
export GEMINI_API_KEY="your-api-key-here"

# 寫入 shell profile 使其永久生效
echo 'export GEMINI_API_KEY="your-api-key-here"' >> ~/.zshrc  # 或 ~/.bashrc
```

### 驗證安裝

```bash
# 確認 Claude Code 能看到 skills
ls ~/.claude/skills/

# 測試 Gemini CLI（僅當你安裝了 Gemini 相關 skills）
gemini "Hello, test"
```

---

## 使用範例

### Code Review（依目前 runtime）

```bash
# 1. Stage 你的改動
git add src/app.js

# 2. 在 Claude Code 中用自然語言觸發
> review the staged files
> 幫我 review 一下
> check code quality before commit
```

預設會在 Claude Code 觸發 `code-review-claude`，在 Codex 觸發 `code-review-codex`，產出包含以下面向的結構化報告：
- 🔴 High / 🟡 Medium / 🟢 Low 優先級 findings
- 語言別 checklist（Python / Shell / JS / TS / Java / PHP）命中
- **Adversarial quick check**：Assumption exposed / Mirror test / Suppression / What breaks this?
- **Assumptions Identified**：未驗證的契約清單
- **Refactored Patch**（選配，diff ≤ 200 行時自動產出）

`code-review-gemini` 已退役。未來若要用 RDSec endpoint reviewer，必須先選擇模型，並確認送出的 diff／資料範圍。

### Activity Logger

```bash
# 首次使用：替換資料路徑，確認預覽後以相同參數移除 --preview 執行一次。
export AGENT_SKILLS_CONFIG_DIR="$HOME/.config/agent-skills"
PYTHONPATH="$HOME/.claude/skills/runtime" python3 -m agent_skills_runtime.setup \
  --activities "/absolute/activities" --notes "/absolute/notes" --preview

# 共用設定建立後，初始化選定的活動目錄。
~/.claude/skills/activity-logger/scripts/init_activities.sh init

# 透過 Claude Code 記錄
> log this activity
> record what I just did

# 或直接使用 CLI
~/.claude/skills/activity-logger/scripts/log_activity.sh \
  -d "Implemented user authentication" \
  -t task_completed \
  -c "Added OAuth2 support" \
  --tags "security,auth"

# 管理活動紀錄
~/.claude/skills/activity-logger/scripts/init_activities.sh info    # 查看 session 資訊
~/.claude/skills/activity-logger/scripts/init_activities.sh list    # 列出所有紀錄
~/.claude/skills/activity-logger/scripts/init_activities.sh stats   # 依類型統計
~/.claude/skills/activity-logger/scripts/init_activities.sh archive 30  # 歸檔 30 天前的紀錄
```

**活動類型**：`task_completed`、`bug_fixed`、`refactoring`、`research`、`documentation`、`review`

**紀錄位置**：外部 `work-journal.json` 的 `sources.activities`（進行中），其下的 `processed/`（已歸檔）。`CLAUDE_ACTIVITIES_DIR` 可明確覆寫活動路徑；相對路徑從設定根目錄解析。Shell 與 MCP 須使用相同環境。Setup 保留既有設定，不搬移舊紀錄。

Activity records 可與 `work-log-analyzer` 搭配使用，跨專案和 session 聚合分析。

---

## 各 Skill 依賴

| Skill | 依賴 |
|-------|------|
| code-review-gemini | 已退役的遷移參考，不是支援中的 review 路徑 |
| code-review-claude | 無外部依賴 |
| code-story-teller | Git |
| pr-review-assistant | [GitHub CLI](https://cli.github.com/)、Git |
| ui-design-analyzer | 無外部依賴（使用 Claude 原生多模態能力） |
| interactive-presentation-generator | 無外部依賴（內建 20 種樣式模板） |
| activity-logger | Python 3、`jq`、Git、bundled runtime 與外部 journal 設定 |
| work-log-analyzer | Python 3、`jq`、`date`、bundled runtime 與外部 journal 設定 |
| skill-auditor | Bash 4.0+（可選：Gemini CLI 用於語義分析） |
| newsletter-digest | Python 3（內建 `parse_emls.py` 腳本） |
| skills-query-server | Node.js；來源編譯需要 lockfile 依賴與 TypeScript，測試工具版本見 server README |
| pptx-to-md | Python 3 + `uv` 或 `pip`（markitdown；`uvx` 可免安裝直接執行） |
| repo-sync | Git |
| skill-sync | `rsync`（macOS/Linux 預裝） |
| md-translate | 無外部依賴 |
| 其餘 skills | 無外部依賴 |

---

## 建立新 Skill

```bash
# 1. 建立目錄
mkdir my-skill

# 2. 建立 SKILL.md
cat > my-skill/SKILL.md << 'EOF'
---
name: My Skill Name
description: Brief description of when to use this skill.
---

# My Skill Name

## Instructions
Describe when and how Claude should use this skill.

## Examples
Provide example trigger phrases and expected behavior.
EOF

# 3.（選用）加入輔助腳本
mkdir my-skill/scripts

# 4. 用 skill-auditor 驗證品質
> audit my-skill
```

Audit 完成後，逐項檢視 findings：修正問題，或留下明確的 disposition；必要時重新 audit。完成審查後才打包乾淨的 runtime skill。Audit report 與其他驗證 artifact 屬於開發紀錄，除非 skill 在執行時明確需要，否則不要放進 production skill。

### Skill 目錄結構

```
skill-name/
├── SKILL.md           # 必要：skill 定義與指令
├── references/        # 選用：按需載入的 runtime 指引
├── scripts/           # 選用：輔助 shell 腳本
│   └── my_script.sh
└── other_files/       # 選用：僅限 runtime 需要的資源
```

---

## 疑難排解

| 錯誤訊息 | 可能原因 | 快速修復 |
|----------|---------|---------|
| `command not found: gemini` | Gemini CLI 未安裝 | `npm install -g @google/gemini-cli` |
| `GEMINI_API_KEY not set` | API key 未設定 | `export GEMINI_API_KEY="..."` |
| `No staged changes` | 沒有 staged 的檔案 | `git add <files>` |
| `permission denied` | 腳本沒有執行權限 | `chmod +x *.sh` |
| `429 Resource exhausted` | API 配額用盡 | 等待重置或升級方案 |
| `401 Unauthorized` | API key 無效 | 重新產生 key |

---

## 更多文件

- **[SKILLS_ROADMAP.md](./SKILLS_ROADMAP.md)** — Skills 發展路線圖
- **[Cheatsheet (EN)](./cheatsheet/cheatsheet-en.md)** · **[速查表 (中文)](./cheatsheet/cheatsheet-zh.md)** — 快速參考

---

## License

MIT
