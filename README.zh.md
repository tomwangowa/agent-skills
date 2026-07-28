# Claude Code Skills

[English](./README.md) | **繁體中文**

一套在實務工作中長出來的 Claude Code 技能集。

這些 skills 不是為了展示 AI 能做什麼，而是為了解決一個具體問題：**當你把越來越多工作交給 AI，如何確保產出的品質不會隨著信任的增加而下降？**

我的做法是把工程紀律嵌入 AI 工作流程本身——用結構化流程對抗 AI 和人類共有的認知盲點。具體來說：

- **結構化 Code Review**：任何模型在檢視自己的產出時都會過度合理化——所以 review 是 skill 觸發的明確步驟，不是口頭承諾。2026-04 起預設使用 `code-review-claude`（廣度 + adversarial + assumptions + syntax 驗證，0/6 hallucination）；需要完整 refactored patch 或外部第二意見時，追加 `code-review-gemini`。
- **Falsification-first**：研究類 skills 要求先搜尋反面證據，再搜尋支持證據。這不是悲觀，而是對確認偏誤的系統性防禦。
- **Evidence before assertion**：在宣稱任何工作「完成」之前，必須先執行驗證命令並確認輸出。說「通過測試」的前提是真的跑過測試。

這些原則不需要你同意我的做法——它們是可以拆開使用的獨立模組。你可以只用 code review，只用 research，或只用 presentation generator。每個 skill 都是自足的。

---

## Skills Catalog

完整、生成式的 inventory，以及 lifecycle／surface 政策，都在 [SKILLS_CATALOG.md](./SKILLS_CATALOG.md)。若想依需求取得推薦，請用 `skill-router`。

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
cd ~/.claude/skills/skills-query-server && npm install
claude mcp add -s user skills-query -- npx tsx ~/.claude/skills/skills-query-server/src/index.ts
```

詳見 [skills-query-server/README.md](./skills-query-server/README.md)。

## 關於 Code Review 的分層設計

**任何模型在檢視自己產生的程式碼時，都傾向對既有結構過度合理化。** 所以這個 repo 把 review 切成一個獨立步驟——以 skill 觸發、有 adversarial checklist、有 assumptions 清單——而不是靠「Claude 檢查一下自己寫的」這種同步審視。

### 兩個 reviewer，兩個角色（2026-04 起）

- **`code-review-claude`（預設 reviewer）**：原生 Claude < 30 秒完成。流程包含 Step 3.3 syntax-checker 驗證（消除 whitespace / regex / 字元類別這類 hallucination）、Step 3.4 語言別 checklist、Step 3.5 adversarial quick check（Assumption / Mirror test / Suppression / What breaks this?）、Step 3.6 Assumptions Identified。Step 4.5 可選擇性產出 refactored patch。2026-04 對 6 種語言的 HTTP retry client 做 n=6 benchmark，Claude 每次的 findings 廣度是 Gemini 的 2.3–5.0 倍，且 0/6 出現需修正的 hallucination。
- **`code-review-gemini`（選配）**：Gemini CLI 外部 review，適合想要完整可套用的 refactored patch、或在 claude review 之後再來一次外部第二意見。不是預設，但保留下來作為 patch 生成器與 cross-check 工具。

> **pre-commit auto-review** 也預設走 `code-review-claude`。pre-commit 是 hallucination 成本最高的場景，所以用 benchmark 上最可靠的 reviewer。

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

預設 reviewer `code-review-claude` 是原生 Claude，不需要 Gemini。Gemini CLI 僅在以下 skills 使用：`code-review-gemini`（選配深度 reviewer / refactored patch 生成器）、`pr-review-assistant` 的 keyword-triggered Gemini 路徑（選配，詳見該 skill 文件）。如果你只跑預設流程，可以跳過本節。

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

### Code Review（預設：Claude）

```bash
# 1. Stage 你的改動
git add src/app.js

# 2. 在 Claude Code 中用自然語言觸發
> review the staged files
> 幫我 review 一下
> check code quality before commit
```

預設會觸發 `code-review-claude`，< 30 秒完成，產出包含以下面向的結構化報告：
- 🔴 High / 🟡 Medium / 🟢 Low 優先級 findings
- 語言別 checklist（Python / Shell / JS / TS / Java / PHP）命中
- **Adversarial quick check**：Assumption exposed / Mirror test / Suppression / What breaks this?
- **Assumptions Identified**：未驗證的契約清單
- **Refactored Patch**（選配，diff ≤ 200 行時自動產出）

想要更深度的外部視角或完整 refactored patch？在 claude review 之後追加：

```
> gemini review 這次的改動，給我 refactored patch
> detailed review with gemini
```

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
| code-story-teller | Git |
| pr-review-assistant | [GitHub CLI](https://cli.github.com/)、Git；[Gemini CLI](https://github.com/google-gemini/gemini-cli)（僅選配深度路徑） |
| ui-design-analyzer | 無外部依賴（使用 Claude 原生多模態能力） |
| interactive-presentation-generator | 無外部依賴（內建 20 種樣式模板） |
| activity-logger | `jq`、Git |
| work-log-analyzer | `jq`、`date`（核心功能無外部依賴） |
| skill-auditor | Bash 4.0+（可選：Gemini CLI 用於語義分析） |
| newsletter-digest | Python 3（內建 `parse_emls.py` 腳本） |
| skills-query-server | Node.js、`tsx`（透過 `claude mcp add` 註冊） |
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
