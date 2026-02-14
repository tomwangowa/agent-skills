# Skills & Workflows 速查表

## 開發流程 (Development)

### 完整功能開發（從零到完成）

```
brainstorming → sp-writing-plans → sp-test-driven-development → sp-executing-plans
    → sp-requesting-code-review → sp-receiving-code-review → sp-finishing-a-development-branch
```

| 情境 | 使用技能 |
|------|----------|
| 有新想法，還沒想清楚怎麼做 | `brainstorming` |
| 需求明確，要拆解成實作步驟 | `sp-writing-plans` |
| 要開始寫 code（先寫測試） | `sp-test-driven-development` |
| 有計畫，要逐步執行並檢查 | `sp-executing-plans` |
| 功能完成，要請人 review | `sp-requesting-code-review` |
| 收到 review 回饋，要處理 | `sp-receiving-code-review` |
| 分支做完了，要 merge / PR | `sp-finishing-a-development-branch` |

### 除錯

| 情境 | 使用技能 |
|------|----------|
| 遇到 bug 或測試失敗 | `sp-systematic-debugging` |
| 修完要確認真的修好了 | `verification-before-completion` |

### 並行任務

| 情境 | 使用技能 |
|------|----------|
| 多個獨立任務可以同時做 | `sp-dispatching-parallel-agents` |
| 計畫中有獨立子任務要分派 | `sp-subagent-driven-development` |
| 需要隔離的 feature 分支環境 | `sp-using-git-worktrees` |

---

## 研究流程 (Research)

### 完整研究（多來源綜合決策）

```
critical-research + tech-feasibility → research-synthesis → 決策文件
```

| 情境 | 使用技能 |
|------|----------|
| 驗證某個說法是否正確 | `critical-research` |
| 評估某技術能否解決問題 | `tech-feasibility` |
| 查核外部文章/行銷文案的真實性 | `narrative-auditor` |
| 驗證文件是否與程式碼一致 | `codebase-audit` |
| 跑完 2+ 研究技能，要整合結論 | `research-synthesis` |

---

## 簡報流程 (Presentation)

### 從主題到完成投影片

```
presentation-planner → interactive-presentation-generator → 投影片檔案
```

| 情境 | 使用技能 |
|------|----------|
| 只有主題，需要規劃敘事和大綱 | `presentation-planner` |
| 有現成大綱，要優化結構 | `presentation-planner`（Optimize 模式） |
| 有完整 Slide Plan，要產出投影片 | `interactive-presentation-generator` |
| 要分析現有 UI 設計截圖 | `ui-design-analyzer` |

---

## 報告流程 (Report)

| 情境 | 使用技能 |
|------|----------|
| 產出週報/月報/專案摘要 | `report-generator` |
| 查詢工作日誌、追蹤 TODO | `work-log-analyzer` |
| 記錄當前工作活動（跨 session） | `activity-logger` |
| 了解程式碼的演進故事 | `code-story-teller` |

---

## Code Review

| 情境 | 使用技能 |
|------|----------|
| 需要深度 code review（預設） | `code-review-gemini` |
| 快速 review（< 50 行變更） | `code-review-claude` |
| 要 review 一個 PR | `pr-review-assistant` |

---

## Meta / 技能管理

| 情境 | 使用技能 |
|------|----------|
| 建立或編輯新技能 | `sp-writing-skills` |
| 審計技能品質（建立/修改後必跑） | `skill-auditor` |
| 跨 AI 工具同步技能 | `skillshare` |

---

## 自動觸發規則

這些技能會在特定條件下自動建議或要求使用：

| 觸發條件 | 自動觸發的技能 |
|----------|---------------|
| 實作新功能前 | `brainstorming`（CLAUDE.md 路由規則） |
| 宣稱工作完成前 | `verification-before-completion` |
| 建立/修改技能後 | `skill-auditor` |
| brainstorming Phase 3 遇到技術抉擇 | `tech-feasibility`（必須） |
| brainstorming Phase 3 遇到事實主張 | `critical-research`（必須） |
| 跑完 2+ 研究技能後 | `research-synthesis`（建議） |
| 完成分支工作後 | `report-generator`（建議） |
| 查完工作日誌後 | `report-generator`（建議） |
