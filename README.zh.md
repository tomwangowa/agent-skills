# Claude Code Skills

[English](./README.md) | **繁體中文**

一套在實務工作中長出來的 Claude Code 技能集。

這些 skills 不是為了展示 AI 能做什麼，而是為了解決一個具體問題：**當你把越來越多工作交給 AI，如何確保產出的品質不會隨著信任的增加而下降？**

我的做法是把工程紀律嵌入 AI 工作流程本身——用結構化流程對抗 AI 和人類共有的認知盲點。具體來說：

- **Dual-AI Review**：Claude 負責開發，Gemini 擔任獨立 reviewer。不是為了多一個 AI，而是因為任何模型在檢視自己的產出時都會過度合理化。
- **Falsification-first**：研究類 skills 要求先搜尋反面證據，再搜尋支持證據。這不是悲觀，而是對確認偏誤的系統性防禦。
- **Evidence before assertion**：在宣稱任何工作「完成」之前，必須先執行驗證命令並確認輸出。說「通過測試」的前提是真的跑過測試。

這些原則不需要你同意我的做法——它們是可以拆開使用的獨立模組。你可以只用 code review，只用 research，或只用 presentation generator。每個 skill 都是自足的。

---

## Skills 總覽

目前共 **34 個自製 skills**，按用途分為 7 類。

### 品質守門 (5)

把 review 和驗證嵌入開發流程，而不是留到最後。

| Skill | 說明 |
|-------|------|
| [code-review-gemini](./code-review-gemini/) | 使用 Gemini CLI 的深度 code review。分析 staged changes，產出結構化報告。**預設 reviewer。** |
| [code-review-claude](./code-review-claude/) | Claude 原生的快速 code review（< 30 秒）。適合 50 行以下的小改動。 |
| [pr-review-assistant](./pr-review-assistant/) | Pull request 結構化審查。分析 diff、評估風險、提供改善建議。 |
| [codebase-audit](./codebase-audit/) | Claims-first 程式碼庫審計：從文件中提取宣稱，逐一對照原始碼驗證。用來確認文件和程式碼是否一致。 |
| [completion-gate](./completion-gate/) | 完成前的證據關卡。在宣稱「完成」或「通過」之前，強制執行驗證命令並確認輸出。 |

### 研究與批判思考 (9)

讓 AI 幫你做研究時，不只是蒐集支持你想法的資料。

| Skill | 說明 |
|-------|------|
| [tech-research-pipeline](./tech-research-pipeline/) | **完整研究管線調度器**。串接 8 個 skill、2 個閘門，一鍵觸發從範圍界定到決策文件的全流程。適合重大技術決策。 |
| [deep-reading](./deep-reading/) | 系統性文件深讀與知識萃取。從文件集中提取核心心智模型、專家分歧、知識缺口與可教框架。重點是理解，不只是摘要。 |
| [tech-feasibility](./tech-feasibility/) | 技術可行性評估。8 步結構化流程，在投入 POC 之前回答「技術 X 能否解決問題 Y？」 |
| [assumption-extractor](./assumption-extractor/) | 從技術文件中系統性提取顯性與隱性假設。分類風險等級（CRITICAL → LOW），產出含依賴圖的 Assumption Registry。 |
| [micro-poc-validator](./micro-poc-validator/) | 用最小量代碼（≤ 30 行）實證驗證技術假設。5-30 分鐘的 time-boxed 實驗，產出 PASS/FAIL/PARTIAL 結果。 |
| [critical-research](./critical-research/) | Falsification-first 研究：先搜尋反面證據，再搜尋支持證據。系統性消除確認偏誤。 |
| [narrative-auditor](./narrative-auditor/) | 敘事審計：將文章、行銷文案、技術宣稱與一手資料對照查證。也可以作為你的 AI proxy 代為發言。 |
| [research-cross-validator](./research-cross-validator/) | 用 2-3 種獨立策略（官方文件、反證搜尋、原始碼檢查等）交叉驗證技術主張，防止單一來源偏見。 |
| [research-synthesis](./research-synthesis/) | 多源研究綜合。在跑完 2+ 個研究類 skills 後，將發現整合為 ADR 風格的決策文件。 |

### 多 Agent 角色 (3)

以獨立 subagent 模擬團隊中 PM 和 RD 的分工合作。

| Skill | 說明 |
|-------|------|
| [role-orchestrator](./role-orchestrator/) | **管線協調者。** 以 subagent dispatch 串接 PM → RD，每階段都有使用者審核閘門。讀取 `project-profile.yaml` 依專案規模（small/medium/large）校準產出深度。適用中大型專案。 |
| [role-pm](./role-pm/) | PM 角色：將目標轉化為按規模校準的需求 artifact（Bullet + AC → User stories → 完整 PRD）。 |
| [role-rd](./role-rd/) | RD 角色：將 PM 需求轉化為按規模校準的設計 artifact（Code plan → Design doc → Architecture doc）。 |

### 設計與規劃 (3)

在動手之前先想清楚。

| Skill | 說明 |
|-------|------|
| [brainstorming](./brainstorming/) | 蘇格拉底式設計對話。透過一次一個問題探索需求，提出 2-3 個方案及其取捨，產出設計文件。偵測到中大型專案時自動建議切換至 `role-orchestrator`。 |
| [spec-gap-finder](./spec-gap-finder/) | 開發前 spec/wireframe 審查。用 RD 視角跑 10 類、60+ 項 checklist，找出 spec 缺口和未定義的 edge case。產出分優先級的問題清單，帶進一次對齊會議就能搞定。 |
| [ui-design-analyzer](./ui-design-analyzer/) | UI/UX 截圖分析。從可用性、無障礙、視覺設計等 6 個維度評估介面設計。 |

### 內容生成 (7)

把重複性的文件、簡報、筆記工作標準化。

| Skill | 說明 |
|-------|------|
| [presentation-planner](./presentation-planner/) | 簡報敘事策略規劃。在製作投影片之前，先完成受眾分析、故事線設計、逐頁內容規劃。 |
| [interactive-presentation-generator](./interactive-presentation-generator/) | 互動式簡報生成。支援 reveal.js / Marp / Slidev，內建 20 種專業樣式。 |
| [qa-to-notes](./qa-to-notes/) | 將 Claude Code 對話存為 Obsidian 筆記（Standard / Direct write），或改寫 fact-check 為公司群組可分享的「延伸分析」格式（Teams publish）。三種模式，同一份 note 統一管理。 |
| [report-generator](./report-generator/) | 從活動紀錄和 git 歷史生成結構化報告。支援週報、月報、專案總結、回顧等格式。 |
| [ai-weekly-insight](./ai-weekly-insight/) | TrendLife AI Taskforce 專用的每週/每日 AI 新聞深度分析。Weekly: Top 5；Daily: Top 3。三維分析（技術/業務/競爭），輸出至 Obsidian + Confluence 或 ai_news repo。支援 `--dest` 和 `daily` 模式。 |
| [arxiv-digest](./arxiv-digest/) | 將 arXiv AI 論文消化為工程師友善的分享格式，供 Taskforce 會議使用。支援 URL、搜尋、多篇比較三種模式。 |
| [newsletter-digest](./newsletter-digest/) | 電子報批次消化。讀取整個資料夾的 `.eml` 檔，自動分群歸類，產出含主題摘要、逐篇速覽、深讀推薦的結構化 digest。支援遞迴子資料夾與日期篩選。 |

### 生產力與追蹤 (3)

跨 session 的工作記錄和歷史分析。

| Skill | 說明 |
|-------|------|
| [activity-logger](./activity-logger/) | 記錄當次 session 的工作活動，供跨 session 聚合與報告生成使用。 |
| [work-log-analyzer](./work-log-analyzer/) | 分析工作日誌。追蹤任務進度、查詢專案歷史、理解決策演變。支援活動聚合、時間軸、TODO、決策追溯、通用搜尋等查詢模式。 |
| [code-story-teller](./code-story-teller/) | 分析 git 歷史，講述程式碼的演化故事。理解設計決策的來龍去脈。 |

### MCP Server

將 skills 的資料查詢能力結構化為 MCP 工具，讓 Claude Code 能直接查詢你的工作歷史。

| Server | 說明 |
|--------|------|
| [skills-query-server](./skills-query-server/) | 提供 7 個結構化查詢工具：活動查詢、全文搜尋、活動記錄、時間軸追蹤、TODO 提取、決策追溯、工作儀表板。整合 activity-logger、work-log-analyzer、qa-to-notes 的資料來源（活動紀錄 + QA 知識筆記），透過 MCP 協議讓 Claude 直接存取。 |

**快速設定：**

```bash
cd ~/.claude/skills/skills-query-server && npm install
claude mcp add -s user skills-query -- npx tsx ~/.claude/skills/skills-query-server/src/index.ts
```

詳見 [skills-query-server/README.md](./skills-query-server/README.md)。

### 工具與元技能 (3)

管理 skills 本身的工具。

| Skill | 說明 |
|-------|------|
| [skill-auditor](./skill-auditor/) | 審計 skills 的品質、安全性與最佳實踐。建立或修改 skill 後用來驗證。 |
| [skillshare](./skillshare/) | 跨 AI CLI 工具同步 skills（Claude Code、Cursor、Windsurf 等）。單一來源、多處使用。 |
| [skill-router](./skill-router/) | **技能發現與路由中心。** 三種模式：智慧推薦（描述需求自動匹配 skill）、分類瀏覽（列出所有 skill）、工作流瀏覽（查看預設多 skill 組合流程）。不確定該用什麼 skill 時的第一站。 |

---

## 關於 Dual-AI Review

這個 repo 裡有一個可能看起來奇怪的設計：code review 預設交給 Gemini 而不是 Claude 自己。

原因很簡單——**任何模型在檢視自己產生的程式碼時，都傾向對既有結構過度合理化**。Claude 負責開發和上下文理解，Gemini 扮演相對保守的 reviewer，特別擅長抓邏輯漏洞、邊界條件與防禦性不足的問題。

這模擬的是實際團隊中「作者與 reviewer 分工」的狀態。目前的做法是每完成一個小任務就自動調用 Gemini review，依回饋修正直到 fully approved。價值不在於多一個 AI，而在於把 review 前移、系統化，在風險累積之前攔下問題。

如果你不使用 Gemini，`code-review-claude` 提供了純 Claude 的快速 review 替代方案。

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

## 關於 Standard Procedures (sp-*)

Superpowers 插件的 skills（brainstorming、writing-plans、executing-plans、systematic-debugging、TDD 等）現在直接從 [superpowers](https://github.com/obra/superpowers) 插件載入，不再需要本地副本或 symlink。啟用插件後，它們會以 `sp-*` 的形式自動出現在你的 session 中。

---

## Quick Start

### 前置需求

- [Claude Code CLI](https://docs.anthropic.com/en/docs/claude-code)
- [Node.js](https://nodejs.org/)（for Gemini CLI）
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

### 設定 Gemini CLI

Gemini CLI 用於 code-review-gemini、code-story-teller、pr-review-assistant 等需要外部 review 的 skills。

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

# 測試 Gemini CLI
gemini "Hello, test"
```

---

## 使用範例

### Code Review（Gemini）

```bash
# 1. Stage 你的改動
git add src/app.js

# 2. 在 Claude Code 中用自然語言觸發
> review the staged files
> 幫我 review 一下
> check code quality before commit
```

Claude 會調用 Gemini 分析你的改動，產出包含以下面向的結構化報告：
- 潛在 bug 或安全問題
- 程式碼品質與最佳實踐
- 可讀性與可維護性
- 改善建議

### Activity Logger

```bash
# 初始化（首次使用）
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

**紀錄位置**：`~/.claude/activities/`（進行中）、`~/.claude/activities/processed/`（已歸檔）

Activity records 可與 `work-log-analyzer` 搭配使用，跨專案和 session 聚合分析。

---

## 各 Skill 依賴

| Skill | 依賴 |
|-------|------|
| code-review-gemini | [Gemini CLI](https://github.com/google-gemini/gemini-cli)、Git |
| code-review-claude | 無外部依賴 |
| code-story-teller | [Gemini CLI](https://github.com/google-gemini/gemini-cli)、Git |
| pr-review-assistant | [Gemini CLI](https://github.com/google-gemini/gemini-cli)、[GitHub CLI](https://cli.github.com/)、Git |
| ui-design-analyzer | 無外部依賴（使用 Claude 原生多模態能力） |
| interactive-presentation-generator | 無外部依賴（內建 20 種樣式模板） |
| activity-logger | `jq`、Git |
| work-log-analyzer | `jq`、`date`（核心功能無外部依賴） |
| skill-auditor | Bash 4.0+（可選：Gemini CLI 用於語義分析） |
| newsletter-digest | Python 3（內建 `parse_emls.py` 腳本） |
| skills-query-server | Node.js、`tsx`（透過 `claude mcp add` 註冊） |
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

### Skill 目錄結構

```
skill-name/
├── SKILL.md           # 必要：skill 定義與指令
├── scripts/           # 選用：輔助 shell 腳本
│   └── my_script.sh
└── other_files/       # 選用：其他資源
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
