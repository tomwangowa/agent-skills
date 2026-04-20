# Skills & Workflows 速查表

> **注意：** 前綴為 `superpowers:` 的技能由 [superpowers](https://github.com/obra/superpowers) plugin 提供。`brainstorming` 技能有個人版覆蓋 superpowers 版本。

## 開發流程 (Development)

### 完整功能開發（從零到完成）

```
小型專案：
  brainstorming → superpowers:writing-plans → superpowers:test-driven-development → superpowers:executing-plans
      → superpowers:requesting-code-review → superpowers:receiving-code-review → superpowers:finishing-a-development-branch

中大型專案：
  role-orchestrator (PM → RD) → superpowers:writing-plans → superpowers:subagent-driven-development
      → superpowers:requesting-code-review → superpowers:receiving-code-review → superpowers:finishing-a-development-branch
```

| 情境 | 使用技能 | 範例 |
|------|----------|------|
| 中大型專案，需要結構化的 PM→RD 流水線 | `role-orchestrator` | 「Start role pipeline for 建立電商結帳系統」 |
| 只需要 PM 需求分析 | `role-pm` | 「PM analysis for 建立通知系統」 |
| 只需要 RD 技術設計 | `role-rd` | 「RD design for 這組需求」 |
| 有新想法，還沒想清楚怎麼做 | `brainstorming` | 「我想加通知系統，但還沒想好架構」 |
| 拿到 PM spec / wireframe，開發前要找缺口 | `spec-gap-finder` | 「幫我審查這份 spec，開發前先找出漏洞」 |
| 需求明確，要拆解成實作步驟 | `superpowers:writing-plans` | 「幫我寫一個加入 JWT 認證的實作計畫」 |
| 要開始寫 code（先寫測試） | `superpowers:test-driven-development` | 「用 TDD 方式實作登入 endpoint」 |
| 有計畫，要逐步執行並檢查 | `superpowers:executing-plans` | 「執行 plan.md 裡的認證實作計畫」 |
| 功能完成，要請人 review | `superpowers:requesting-code-review` | 「Review 我的認證功能，準備合併了」 |
| 收到 review 回饋，要處理 | `superpowers:receiving-code-review` | 「處理 PR #42 上的 review 意見」 |
| 分支做完了，要 merge / PR | `superpowers:finishing-a-development-branch` | 「分支做完了，幫我建 PR」 |

### 除錯

| 情境 | 使用技能 | 範例 |
|------|----------|------|
| 遇到 bug 或測試失敗 | `superpowers:systematic-debugging` | 「auth.ts 跑測試出現 'undefined is not a function'」 |
| 修完要確認真的修好了 | `completion-gate` | 「我修完 auth 的 bug 了，幫我確認真的修好了」 |

### 並行任務

| 情境 | 使用技能 | 範例 |
|------|----------|------|
| 多個獨立任務可以同時做 | `superpowers:dispatching-parallel-agents` | 「同時跑 lint、測試和型別檢查」 |
| 計畫中有獨立子任務要分派 | `superpowers:subagent-driven-development` | 「把計畫中的步驟 2、3、5 同時執行」 |
| 需要隔離的 feature 分支環境 | `superpowers:using-git-worktrees` | 「幫 payment-refactor 建一個 worktree」 |

---

## 研究流程 (Research)

### 完整研究管線（8 階段嚴格評估）

```
tech-research-pipeline（一鍵觸發完整流程）:
  brainstorming → tech-feasibility → assumption-extractor → micro-poc-validator
    → GATE A → critical-research → narrative-auditor → research-cross-validator
    → GATE B → research-synthesis → 決策文件
```

| 情境 | 使用技能 | 範例 |
|------|----------|------|
| 重大技術決策，需要嚴格多角度評估 | `tech-research-pipeline` | 「用完整 research pipeline 評估從 nodriver 遷移到 Playwright」 |
| 評估某技術能否解決問題 | `tech-feasibility` | 「Bun 能取代 Node.js 用在我們的正式環境嗎？」 |
| 從技術文件中提取隱含假設 | `assumption-extractor` | 「幫我從這份設計文件中提取所有假設」 |
| 用代碼驗證技術假設（5-30 分鐘） | `micro-poc-validator` | 「驗證 nodriver 能不能連 wss:// URL」 |
| 驗證某個說法是否正確 | `critical-research` | 「React Server Components 真的不能用 hooks 嗎？」 |
| 查核外部文章/行銷文案的真實性 | `narrative-auditor` | 「幫我查核這篇 Redis vs Memcached 的文章」 |
| 用多策略交叉驗證技術主張 | `research-cross-validator` | 「交叉驗證這份可行性報告中的關鍵主張」 |
| 驗證文件是否與程式碼一致 | `codebase-audit` | 「檢查 README 裡的 API 說明跟實際程式碼是否一致」 |
| 跑完 2+ 研究技能，要整合結論 | `research-synthesis` | 「把資料庫選型的研究結果整合成決策文件」 |

### Narrative Auditor 完整工作流

```
narrative-auditor (fact-check + 短評)
    → qa-to-notes「存成 notes」 (Fact-Check + 短評存檔)
    → qa-to-notes「改寫成 Teams 版」 (Teams 發佈版，追加到同一份 note)
```

| 步驟 | 說什麼 | 做什麼 |
|------|--------|--------|
| 1. Fact-check | `/narrative-auditor` + 貼文章連結 | 產出 fact-check 報告 |
| 2. 短評 | 「寫個短評」 | 產出可分享的評論 |
| 3. 存檔 | 「存成 notes」或 `/qa-to-notes` | Fact-check + 短評存為 Obsidian 筆記 |
| 4. Teams 版 | 「改寫成 Teams 版」或 `/qa-to-notes publish` | 降火改寫，追加到同一份 note，同時顯示在對話中供複製 |

**Teams 版自動轉換規則：**
- 去除 verdict 標籤（ACCURATE/MISLEADING/FALSE）、severity 等級、confidence tags
- 去除個人名字、TrendLife 品牌名、🦤 Dodo 人設標記
- 負面發現改框架為「另一面也值得知道」
- 強制包含「💡 論點」段落（含具體場景舉例）
- 原始分享者留佔位字 `@_____`（自行填入）

---

## 知識管理 (Knowledge Management)

### 電子報消化

| 情境 | 使用技能 | 範例 |
|------|----------|------|
| 一次消化整個資料夾的電子報 | `newsletter-digest` | 「幫我消化 ~/Downloads/newsletters 裡的電子報」 |
| 遞迴處理含子資料夾的信箱 | `newsletter-digest`（遞迴模式） | 「~/Mail/subscriptions 裡有很多子資料夾，一起消化」 |
| 只消化特定日期範圍的信件 | `newsletter-digest`（日期篩選） | 「只消化這週的電子報」 |

> **設計精神：** 把散落的 `.eml` 檔轉化為結構化知識。自動分群歸類，每個主題有合成摘要（不是逐篇貼上），每篇有獨立速覽讓你不讀原文也能掌握七八成內容。暖色調語氣，像同事在分享觀察而非 AI 在做報告。

### qa-to-notes 三種模式

| 模式 | 觸發語 | 行為 | 輸出 |
|------|--------|------|------|
| **Standard** | 「存成筆記」「整理成筆記」 | 重組為百科式知識文章 | 寫入檔案 |
| **Direct write** | 「直接存」「原文存檔」 | 原文保存不改寫 | 寫入檔案 |
| **Teams publish** | 「改寫成 Teams 版」「publish」 | 降火改寫為公司群組可分享的格式 | 顯示在對話 + 追加到 note 檔案 |

| 情境 | 模式 | 範例 |
|------|------|------|
| 對話中有值得保存的知識 | Standard | 「把這段 React hooks 的討論存成筆記」 |
| fact-check 報告要原封不動保存 | Direct write | 「把這篇 fact-check 直接存下來」 |
| 已存檔的 fact-check 要改成可分享版本 | Teams publish | 「改寫成 Teams 版」 |
| 追加內容到現有筆記 | Standard / Direct write | 「把這段追加到之前那篇 OpenClaw 筆記」 |

---

## 簡報流程 (Presentation)

### 從主題到完成投影片

```
presentation-planner → interactive-presentation-generator → 投影片檔案
```

| 情境 | 使用技能 | 範例 |
|------|----------|------|
| 只有主題，需要規劃敘事和大綱 | `presentation-planner` | 「規劃一場『為什麼我們要遷移到 TypeScript』的簡報」 |
| 有現成大綱，要優化結構 | `presentation-planner`（Optimize 模式） | 「優化這個大綱的敘事節奏」 |
| 有完整 Slide Plan，要產出投影片 | `interactive-presentation-generator` | 「用 Marp 產出投影片」 |
| 要分析現有 UI 設計截圖 | `ui-design-analyzer` | 「分析這張 dashboard 截圖的 UX 問題」 |

---

## 報告流程 (Report)

| 情境 | 使用技能 | 範例 |
|------|----------|------|
| 產出每週 AI 新聞深度分析 | `ai-weekly-insight` | 「AI 週報」或 `/ai-weekly-insight` |
| 產出每日 AI 新聞深度分析 | `ai-weekly-insight` (daily mode) | 「AI 日報」或 `/ai-weekly-insight daily` |
| 指定發布目的地（Confluence 或 repo） | `ai-weekly-insight --dest` | `/ai-weekly-insight --dest repo` |
| 消化 arXiv 論文並產出分享材料 | `arxiv-digest` | 「arXiv 導讀」或 `/arxiv-digest <url>` |
| 產出週報/月報/專案摘要 | `report-generator` | 「產出這個 sprint 的週報」 |
| 查詢工作日誌、追蹤 TODO | `work-log-analyzer` | 「上週還有哪些 TODO 沒完成？」 |
| 記錄當前工作活動（跨 session） | `activity-logger` | 「記錄今天的工作：重構 auth 模組、修了 3 個 bug」 |
| 了解程式碼的演進故事 | `code-story-teller` | 「說說 auth.ts 這個檔案的演進故事」 |

---

## Code Review

| 情境 | 使用技能 | 範例 |
|------|----------|------|
| 任何 code review（預設） | `code-review-claude` | 「review 一下 src/auth/ 的改動」 |
| 深度 review / 要 refactored patch / pre-commit 驗證 | `code-review-gemini` | 「gemini review 這個模組，給我 refactored patch」 |
| 要 review 一個 PR | `pr-review-assistant` | 「Review PR #42」 |

> **Review 技能選用指引（2026-04 起）：**
> - **日常開發中（預設）：** 直接用 `/code-review-claude` — 廣度 + adversarial + assumptions + syntax 驗證，0 hallucination（benchmark n=6）
> - **想要外部第二意見 / 完整可複製的 refactored patch：** 追加 `/code-review-gemini`（可在 claude review 後串接）
> - **重大功能要 merge 前：** 用 `/superpowers:requesting-code-review` 做雙層審查（自動調度 subagent，合併結果）
> - **收到別人 review 意見時：** `/superpowers:receiving-code-review` 幫你避免盲目同意，要求技術驗證後再改

---

## Meta / 技能管理

| 情境 | 使用技能 | 範例 |
|------|----------|------|
| 不確定該用哪個 skill | `skill-router` | 「/skill-router 我想評估用 Redis 做 session store」 |
| 瀏覽所有可用 skills（按分類） | `skill-router list` | 「/skill-router list」 |
| 查看預設多 skill 組合工作流 | `skill-router workflows` | 「/skill-router workflows」 |
| 建立或編輯新技能 | `superpowers:writing-skills` | 「建立一個資料庫遷移的新技能」 |
| 審計技能品質（建立/修改後必跑） | `skill-auditor` | 「審計剛建的 db-migrator 技能」 |
| 跨 AI 工具同步技能 | `skillshare` | 「把技能同步到 Cursor 和 Windsurf」 |

> **skill-router 設計精神：** 當 skills 超過 30 個，記住每個的用途和觸發詞變得不切實際。skill-router 是統一入口——描述你的需求，它從 registry 中語義匹配最適合的 skill 或 workflow，但**不會自動執行**，一定等你確認。三種模式：智慧推薦（預設）、分類瀏覽、工作流瀏覽。

---

## 自動觸發規則

這些技能會在特定條件下自動建議或要求使用：

| 觸發條件 | 自動觸發的技能 |
|----------|---------------|
| 實作新功能前 | `brainstorming`（CLAUDE.md 路由規則） |
| RD 收到 PM spec / wireframe | `spec-gap-finder`（建議） |
| brainstorming 偵測到中大型範圍 | `role-orchestrator`（建議升級） |
| 宣稱工作完成前 | `completion-gate` |
| 建立/修改技能後 | `skill-auditor` |
| brainstorming Phase 3 遇到技術抉擇 | `tech-feasibility`（必須） |
| brainstorming Phase 3 遇到事實主張 | `critical-research`（必須） |
| tech-feasibility 產出報告後 | `assumption-extractor`（建議） |
| assumption-extractor 找到 CRITICAL 假設 | `micro-poc-validator`（建議） |
| 跑完 2+ 研究技能後 | `research-synthesis`（建議） |
| 重大技術決策需嚴格評估 | `tech-research-pipeline`（建議） |
| 完成分支工作後 | `report-generator`（建議） |
| 查完工作日誌後 | `report-generator`（建議） |
