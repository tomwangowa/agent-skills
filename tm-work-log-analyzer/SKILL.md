---
name: Work Log Analyzer
description: Analyze work logs and journals to answer questions about project history, decisions, TODOs, and timeline evolution. Use this Skill when the user wants to query their work journal, track task progress, or understand how decisions evolved over time.
id: tm-work-log-analyzer
namespace: tm
domain: work
action: log
qualifier: analyzer
version: "1.1.0"
updated: "2026-01-18"
---

# Work Log Analyzer

## Purpose

This Skill analyzes work logs, journals, and development notes to help developers:
1. **Track project evolution** - Understand how implementations, features, or decisions evolved over time
2. **Manage TODOs** - Find pending, in-progress, and overdue tasks from logs
3. **Extract Action Items** (NEW) - Automatically identify and track action items from discussions, decisions, and implicit mentions
4. **Extract insights** - Discover patterns, decisions, and rationale behind implementations
5. **Answer questions** - Query logs with natural language to find specific information

The Skill helps developers:
- Quickly find information in lengthy work logs
- Track decision evolution and rationale
- Manage TODOs and Action Items without external tools
- Generate status reports from logs
- Maintain project continuity
- Identify implicit action items from team discussions
- Track who's responsible for what across time

---

## Instructions

When the user provides a log file and asks a question (for example: "關於 SellerCheck 實作方案的演進", "我還有哪些 TODO 還沒完成？", "Lite Engagement 在何時才把 L10n 翻譯確定"), follow the steps below.

### Execution Steps

1. **Identify the log file**
   - User provides explicit file path: use it directly
   - User says "my work log" or "my journal": ask for the file path
   - User pastes content directly: analyze the provided text

2. **Read and parse the log**
   - Read the file content using the available file reading tool
   - Parse the structure (dates, sections, TODOs, etc.)
   - Identify the format (Markdown, plain text, structured, unstructured)

3. **Understand the query**
   - **Activity queries** (NEW): "aggregate my activities", "show me today's work", "what did I do this week"
     - Use the `scripts/aggregate_activities.sh` helper script
     - Aggregates structured activity records from activity-logger
     - Supports filtering by date range, project, type, and tags
     - Formats output as readable work log or structured report
     - Query types:
       - Date range: today, yesterday, this-week, last-week, this-month, all
       - By project: specific project activities
       - By type: task_completed, bug_fixed, refactoring, research, documentation, review
       - By tag: activities with specific tags
     - Output modes:
       - by-date: Chronological daily report
       - by-project: Grouped by project
       - by-type: Grouped by activity type
       - json: Raw JSON for further processing

   - **Timeline queries**: "X 的演進", "how did X evolve", "X 的變化"
     - Extract all entries related to the topic
     - Sort chronologically
     - Summarize major milestones and decisions
     - Can now also query activity records for technical evolution

   - **TODO queries**: "未完成的 TODO", "過期的任務", "pending tasks"
     - Extract all TODO items
     - Categorize by status (pending, in-progress, completed)
     - Identify the current date from system context to accurately calculate overdue tasks (if system date unavailable, use the latest date found in the log file as reference)
     - Check due dates against current date and resolve relative dates (e.g., "yesterday", "last week")
     - Prioritize overdue items

   - **Action Items queries** (NEW): "萃取 action items", "整理待辦事項", "extract action items"
     - Use AI semantic understanding to identify action items from:
       - Discussions: "Tom 會處理 API 設計", "需要 Mary 協助測試"
       - Decisions: "決定使用 PostgreSQL" → infer "需要設計 schema", "評估效能"
       - Explicit TODOs: Integrate with existing TODO detection
       - Implicit actions: "下一步", "待辦", "需要", "計劃"
     - Track action item status by analyzing:
       - Completion markers: [x], "completed", "done", "finished"
       - Progress indicators: [~], "in progress", "working on"
       - Blocking issues: "blocked by", "waiting for"
     - Extract metadata:
       - Owner/assignee: Person names or teams mentioned
       - Due dates: Explicit dates or inferred urgency
       - Source: Date and context where action item originated
       - Status: Not started, In progress, Completed, Blocked
       - Priority: Inferred from urgency indicators
     - Present as table format:
       | 負責人 | 行動項目 | 期限 | 狀態 | 來源 |

   - **Decision queries**: "為什麼選擇 X", "X 的決策過程", "when was X decided"
     - Find relevant discussions and decisions
     - Extract rationale and context
     - Identify decision makers or influencing factors
     - Can now also search activity contexts for decision rationale

   - **Search queries**: General keyword search
     - Find all mentions of the topic
     - Provide context around each mention
     - Group related entries

4. **Analyze and synthesize**
   - Connect related entries across different dates
   - Identify patterns and trends
   - Highlight important context
   - Note any gaps or missing information

5. **Present findings**
   - Structure the answer clearly
   - Include dates and references
   - Quote relevant excerpts
   - Summarize key insights
   - Suggest follow-up questions if appropriate

### Output Requirements

Your response should be:

- **Clear and structured**: Use headings, bullet points, and quotes
- **Chronological when appropriate**: Timeline queries should show progression
- **Action-oriented for TODOs**: Show status, due dates, and priorities. Always state the reference date used for calculating overdue tasks (e.g., "分析日期: 2026-01-13")
- **Structured tables for Action Items** (NEW): Use Markdown tables with columns: 負責人 | 行動項目 | 期限 | 狀態 | 來源
  - Group by priority/status (🔴 High priority & Overdue, 🟡 In Progress, 🟢 Pending, ✅ Completed)
  - Include summary statistics and actionable recommendations
  - Use clear status icons: ⏰ (overdue), 🔄 (in progress), 📝 (not started), ✅ (completed), 🚫 (blocked)
- **Context-rich**: Include surrounding information to aid understanding
- **Referenced**: Cite dates or log sections for traceability

id: tm-work-log-analyzer
namespace: tm
domain: work
action: log
qualifier: analyzer
version: "1.1.0"
updated: "2026-01-18"
---

## Supported Log Formats

### Recommended Format (Structured Markdown)

```markdown
# 2026-01-13

## SellerCheck Implementation

- Decided to use PostgreSQL for seller verification data
- Considered Redis but concerned about persistence
- Next: prototype the schema

## TODOs

- [ ] TODO: Implement SellerCheck API (due: 2026-01-20) #high-priority
- [x] TODO: Fix L10n issues in Lite Engagement (completed: 2026-01-10)
- [ ] TODO: Code review for PR #123

## Decisions

**Decision**: Use PostgreSQL for SellerCheck
**Rationale**: Need ACID guarantees and complex queries
**Alternatives considered**: Redis, MongoDB
**Date**: 2026-01-13
```

### Also Supports

- **Plain text logs**: Less structured but still analyzable
- **Bullet point journals**: Simple daily logs
- **Unstructured notes**: Will extract information best-effort
- **Mixed formats**: Adapts to varying styles

### TODO Format Recognition

The Skill recognizes these TODO patterns:

```markdown
- [ ] TODO: Task description
- [x] TODO: Completed task
- TODO: Task without checkbox
- [ ] Task (due: YYYY-MM-DD)
- [ ] Task #priority-tag
- FIXME: Code fix needed
- HACK: Technical debt item
```

**Format Tolerance**: The Skill attempts to be lenient with common formatting variations:
- Checkboxes with missing spaces: `- []` or `- [X]` (though `- [ ]` and `- [x]` are preferred)
- Various completion markers: `[x]`, `[X]`, `[✓]`, `[✔]`
- In-progress markers: `[~]`, `[→]`, `[...]`
- Different TODO keywords: `TODO`, `FIXME`, `HACK`, `BUG`, `NOTE`

For best results, maintain consistent formatting throughout your logs.

---

## Constraints

- **File size**: Large files (>10,000 lines) may need to be split
- **Date parsing**: Works best with ISO format (YYYY-MM-DD) or clear date headers
- **TODO detection**: Most accurate with consistent formatting
- **Context**: Cannot access files or code references mentioned in logs (only the log content itself)
- **No write operations**: This Skill only reads and analyzes, does not modify logs

id: tm-work-log-analyzer
namespace: tm
domain: work
action: log
qualifier: analyzer
version: "1.1.0"
updated: "2026-01-18"
---

## Examples

### Example 1: Activity Aggregation Query (NEW)

**User:**
> Aggregate my activities from this week

**Expected behavior:**
1. Run `scripts/aggregate_activities.sh -r this-week`
2. Parse the Markdown output
3. Present a formatted summary of the week's activities

**Example output:**
```markdown
# 本週工作摘要 (2026-01-08 ~ 2026-01-13)

## 完成的任務 ✅
- 實作 activity-logger skill (2026-01-13)
  - 跨 session 活動追蹤功能
  - Git 整合和自動 context 捕捉
  - 專案：agent-skills

## 修復的問題 🐛
- 修正 Git 路徑一致性 (2026-01-13)
- 移除 credentials 安全性問題 (2026-01-13)
- 優化 ARG_MAX 處理 (2026-01-13)

## 重構工作 ♻️
- 優化 jq 批次處理效能 (2026-01-13)

## 統計
- 總活動數：6
- 涉及專案：1 (agent-skills)
- 變更檔案：約 30 個
```

---

**User:**
> Show me all bug fixes from last month

**Expected behavior:**
1. Run `scripts/aggregate_activities.sh -r this-month -t bug_fixed`
2. Filter activities by type "bug_fixed"
3. Present chronologically with context

id: tm-work-log-analyzer
namespace: tm
domain: work
action: log
qualifier: analyzer
version: "1.1.0"
updated: "2026-01-18"
---

**User:**
> What did I work on in the security-project yesterday?

**Expected behavior:**
1. Run `scripts/aggregate_activities.sh -r yesterday -p security-project`
2. Show project-specific activities
3. Include file changes and tags

---

### Example 2: Action Items Extraction (NEW)

**User:**
> 從我的 worklog.md 萃取所有 action items

**Expected behavior:**
1. Read `worklog.md`
2. Use AI semantic understanding to identify:
   - Explicit TODOs and tasks
   - Implicit action items from discussions
   - Follow-up actions from decisions
3. Extract metadata (owner, due date, status, priority)
4. Track completion status across time
5. Present as structured table

**Example output:**
```markdown
## Action Items 摘要

### 🔴 高優先級 & 過期

| 負責人 | 行動項目 | 期限 | 狀態 | 來源 |
|--------|----------|------|------|------|
| Tom | 實作 SellerCheck API endpoints | 2026-01-10 | ⏰ 已逾期 | 2026-01-05 決策 |
| Mary | 完成 L10n 翻譯審查 | 2026-01-12 | ⏰ 已逾期 | 2026-01-08 討論 |

### 🟡 進行中

| 負責人 | 行動項目 | 期限 | 狀態 | 來源 |
|--------|----------|------|------|------|
| Tom | 設計 PostgreSQL schema | 2026-01-15 | 🔄 進行中 | 2026-01-08 決策後續 |
| Alex | 評估 Redis 快取策略 | 2026-01-18 | 🔄 進行中 | 2026-01-10 討論 |
| Team | 準備 Sprint Demo | 2026-01-20 | 📝 待開始 | 2026-01-13 會議 |

### 🟢 待處理

| 負責人 | 行動項目 | 期限 | 狀態 | 來源 |
|--------|----------|------|------|------|
| Mary | 撰寫 API 文件 | 2026-01-25 | 📝 待開始 | 2026-01-11 需求 |
| Tom | Code review PR #456 | - | 📝 待開始 | 2026-01-09 提及 |
| Team | 規劃 Q2 Roadmap | 2026-02-01 | 📝 待開始 | 2026-01-12 會議 |

### ✅ 近期完成 (last 7 days)

| 負責人 | 行動項目 | 完成日期 | 來源 |
|--------|----------|----------|------|
| Tom | 修復 security vulnerability | 2026-01-12 | 2026-01-10 TODO |
| Mary | Setup CI/CD pipeline | 2026-01-11 | 2026-01-08 討論 |
| Alex | Performance benchmarking | 2026-01-13 | 2026-01-09 決策後續 |

**統計:**
- 總計 Action Items: 11 項
- 已完成: 3 項 (27%)
- 進行中: 3 項 (27%)
- 待處理: 3 項 (27%)
- 已逾期: 2 項 (18%) ⚠️

**建議:**
- ⚠️ Tom 的 SellerCheck API 已逾期 3 天，建議優先處理
- ⚠️ Mary 的 L10n 審查已逾期，可能影響發布時程
- 📅 本週有 3 個 action items 到期，請留意時程
```

**AI 語意理解範例:**

從以下 log 條目：
```markdown
# 2026-01-08
## Architecture Discussion

討論了 SellerCheck 的資料庫選擇。Tom 提到需要 ACID 保證，
最後決定使用 PostgreSQL。接下來 Tom 會設計 schema，
Mary 協助評估效能影響。Alex 建議加入 Redis 做快取層。

## L10n Status

Mary 回報 L10n 翻譯已送出，預計下週完成審查。
```

AI 會自動識別：
1. **Tom: 設計 PostgreSQL schema** (從 "Tom 會設計 schema" 推斷)
2. **Mary: 評估效能影響** (從 "Mary 協助評估" 推斷)
3. **Alex: 規劃 Redis 快取** (從 "Alex 建議" 推斷)
4. **Mary: 完成 L10n 翻譯審查** (從 "預計下週完成審查" 推斷)

---

### Example 3: Timeline Evolution Query

**User:**
> 我有一個 work.md 檔案，幫我分析「關於 SellerCheck 實作方案的演進」

**Expected behavior:**
1. Read the `work.md` file
2. Search for all entries mentioning "SellerCheck"
3. Extract entries chronologically
4. Summarize the evolution:
   - Initial consideration (date, initial thoughts)
   - Design iterations (what changed and why)
   - Final decision (current approach)
5. Present as a timeline with key milestones

**Example output:**
```
## SellerCheck 實作方案演進

### 2026-01-05: 初步討論
- 考慮使用 Redis 做快取層
- 擔心資料持久性問題

### 2026-01-08: 架構調整
- 決定改用 PostgreSQL 作為主要儲存
- 原因：需要 ACID 保證和複雜查詢能力
- Redis 仍用於快取層

### 2026-01-13: 最終方案
- 實作混合架構：PostgreSQL + Redis
- 已完成 schema 設計
- 下一步：實作 API endpoints
```

id: tm-work-log-analyzer
namespace: tm
domain: work
action: log
qualifier: analyzer
version: "1.1.0"
updated: "2026-01-18"
---

### Example 2: TODO Management Query

**User:**
> 檢查我的 journal.md，哪些 TODO 還沒完成？哪些已經過期？

**Expected behavior:**
1. Read `journal.md`
2. Extract all TODO items
3. Parse status ([ ] vs [x])
4. Parse due dates if present
5. Compare with current date (2026-01-13)
6. Categorize and present

**Example output:**
```
## TODO 狀態報告

### ⚠️ 過期任務 (2 items)
1. **Implement SellerCheck API** (due: 2026-01-10)
   - Status: Not started
   - Priority: High
   - 來源: 2026-01-05 entry

2. **Review PR #456** (due: 2026-01-12)
   - Status: Not started

### 📋 待處理任務 (3 items)
1. **Fix L10n in Lite Engagement** (due: 2026-01-20)
   - Status: In progress
   - 最後更新: 2026-01-11

2. **Write unit tests for auth module**
   - No due date
   - 提到於: 2026-01-09

3. **Update documentation** (due: 2026-01-25)
   - Status: Not started

### ✅ 近期完成 (last 7 days)
1. **Setup CI/CD pipeline** (completed: 2026-01-08)
2. **Fix security vulnerability** (completed: 2026-01-12)
```

---

### Example 3: Decision Query

**User:**
> 從 devlog.txt 找出「Lite Engagement 的 L10n 翻譯何時確定的？」

**Expected behavior:**
1. Read `devlog.txt`
2. Search for "Lite Engagement" AND "L10n" or "翻譯"
3. Find decision-related entries
4. Extract timeline and rationale
5. Present with context

**Example output:**
```
## Lite Engagement L10n 翻譯決策時間線

### 2026-01-03: 初步討論
> "開始考慮 Lite Engagement 的多語系支援，尚未確定翻譯範圍"

### 2026-01-08: 範圍確認
> "與 PM 確認 L10n 範圍：支援英文、中文（繁簡）、日文"
> "決定使用 i18next 作為翻譯框架"

### 2026-01-11: **最終確定** ✓
> "L10n 翻譯已經確定完成，所有字串已交付翻譯團隊"
> "預計 2026-01-20 收到翻譯結果"

**答案**: L10n 翻譯在 **2026-01-11** 確定完成並送出。
```

id: tm-work-log-analyzer
namespace: tm
domain: work
action: log
qualifier: analyzer
version: "1.1.0"
updated: "2026-01-18"
---

### Example 4: General Search Query

**User:**
> 搜尋 notes.md 中關於「authentication」的所有提及

**Expected behavior:**
1. Read `notes.md`
2. Find all mentions of "authentication"
3. Extract surrounding context
4. Group by relevance or date
5. Present findings

---

## Use Cases

### Daily Standup Preparation
- Query: "昨天完成了什麼？" or "yesterday's completed tasks"
- Get a quick summary of recent work

### Action Items Management (NEW)
- Query: "萃取所有 action items" or "誰需要做什麼？"
- Get a comprehensive view of all pending actions
- Track who's responsible for what
- Identify overdue items requiring attention
- Generate team accountability reports

### Sprint Planning & Tracking (NEW)
- Query: "本週的 action items" or "show this sprint's action items"
- See what's in progress and what's blocked
- Identify capacity and bottlenecks
- Track sprint progress across team members

### Sprint Retrospective
- Query: "過去兩週的重要決策" or "decisions made in the last 2 weeks"
- Review and discuss team decisions
- Extract action items from retro discussions

### Meeting Follow-ups (NEW)
- Query: "從會議記錄萃取 action items"
- Automatically convert meeting discussions into trackable action items
- Assign ownership from meeting notes
- Ensure nothing falls through the cracks

### Technical Debt Tracking
- Query: "所有 HACK 和 FIXME 項目"
- Identify technical debt from logs

### Decision Documentation
- Query: "為什麼選擇 X 架構？"
- Generate Architecture Decision Records from log entries

### Onboarding New Team Members
- Query: "Y 功能的演進過程"
- Help new members understand project history

### Personal Productivity
- Query: "這個月我完成了哪些任務？"
- Track personal accomplishments

### Team Accountability (NEW)
- Query: "Mary 負責哪些 action items？"
- Track individual responsibilities
- Review workload distribution
- Identify blockers for specific team members

id: tm-work-log-analyzer
namespace: tm
domain: work
action: log
qualifier: analyzer
version: "1.1.0"
updated: "2026-01-18"
---

## Best Practices for Log Writing

To get the most from this Skill, consider these logging practices:

### 1. Use Consistent Date Headers
```markdown
# 2026-01-13
## Morning Session
```

### 2. Structure TODOs Clearly
```markdown
- [ ] TODO: Clear task description (due: 2026-01-20) #tag
```

### 3. Document Decisions Explicitly
```markdown
## Decision: Use PostgreSQL
**Why**: Need ACID guarantees
**Alternatives**: Redis, MongoDB
**Trade-offs**: Slower than Redis, but more reliable
```

### 4. Use Contextual Tags
```markdown
#SellerCheck #architecture #database
```

### 5. Link Related Entries
```markdown
See 2026-01-10 entry for initial discussion
```

### 6. Regular Updates
- Update TODOs when status changes
- Add completion dates for finished tasks
- Document rationale for decisions

---

## Advanced Queries

### Combining Criteria
- "過期的 high-priority TODOs"
- "Last week's decisions about authentication"

### Trend Analysis
- "How did the SellerCheck design change over time?"
- "What were the main concerns in January?"

### Cross-Topic Analysis
- "All decisions related to database choices"
- "TODOs blocked by external dependencies"

### Status Reports
- "Generate a weekly summary"
- "What's the current status of Project X?"

id: tm-work-log-analyzer
namespace: tm
domain: work
action: log
qualifier: analyzer
version: "1.1.0"
updated: "2026-01-18"
---

## Tips for Users

1. **Keep logs consistently**: Regular logging makes analysis more valuable
2. **Use clear dates**: ISO format (YYYY-MM-DD) works best
3. **Tag important entries**: Use hashtags for easy filtering
4. **Be specific in queries**: More context = better results
5. **Review TODO format**: Consistent format improves detection
6. **Include "why" not just "what"**: Decisions are more useful with rationale
7. **Update completion status**: Mark tasks as done to track progress
8. **Split large logs**: Consider monthly or quarterly files for better performance

---

## Integration with Other Skills

- **commit-msg-generator**: Use log insights to write better commit messages
- **code-story-teller**: Combine code history with work log context
- **spec-generator**: Reference log decisions when generating specs
- **spec-review-assistant**: Check if implementation matches log decisions

id: tm-work-log-analyzer
namespace: tm
domain: work
action: log
qualifier: analyzer
version: "1.1.0"
updated: "2026-01-18"
---

## Limitations

- Cannot access external files referenced in logs
- No automatic log updating (read-only)
- Date parsing may fail on ambiguous formats
- Very unstructured logs may yield less precise results
- Cannot track TODOs across multiple files simultaneously (analyze one at a time)

---

## Output Language

- **Analysis and answers**: Traditional Chinese (matches user's CLAUDE.md preference)
- **Code snippets and technical terms**: English
- **Dates and times**: ISO format or as they appear in logs
- **Quotes from logs**: Original language preserved
