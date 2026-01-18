# Work Log Analyzer

A Claude Code Skill that helps you analyze work logs, journals, and development notes to track project evolution, manage TODOs, extract action items, and extract insights.

## Quick Start

### Basic Usage

Simply mention the file and ask a question:

```
幫我分析 work.md 中「SellerCheck 實作方案的演進」
```

```
檢查 journal.txt，哪些 TODO 還沒完成？
```

```
從 devlog.md 找出「何時決定使用 PostgreSQL」
```

**Try it now with the included examples:**

```
分析 example_worklog.md 中「SellerCheck 實作方案的演進」
```

```
從 example_worklog.md 找出所有過期的 TODO
```

```
從 example_action_items.md 萃取所有 action items
```

## Supported Query Types

### 0. Activity Aggregation (NEW - 活動彙整)

Aggregate structured activity records from activity-logger into readable work logs:

```
「彙整我今天的活動」
「Show me this week's activities」
「What bug fixes did I do this month?」
「Generate a daily report from my activities」
```

**Features:**
- Aggregates activity records from `~/.claude/activities/`
- Supports filtering by date range, project, activity type, and tags
- Multiple output formats: by-date, by-project, by-type, or raw JSON
- Integrates with activity-logger skill for cross-session tracking

**Example:**
```bash
# Command line usage
~/.claude/skills/work-log-analyzer/scripts/aggregate_activities.sh -r this-week

# Or via Claude Code
User: Aggregate my activities from this week

Response:
# 本週工作摘要 (2026-01-08 ~ 2026-01-13)

## 2026-01-13

### 06:57 - [bug_fixed] skills
**Fixed ARG_MAX issues and git filename quoting**
- Branch: `main`
- Files changed: 6
- Tags: scalability,robustness

### 06:40 - [refactoring] skills
**Optimized jq performance**
- Branch: `main`
- Files changed: 5
- Tags: performance,optimization

## 統計
- 總活動數：6 項
- 完成任務：1 項
- 修復問題：4 項
- 重構工作：1 項
```

**Available filters:**
- **Date ranges**: `today`, `yesterday`, `this-week`, `last-week`, `this-month`, `all`
- **Projects**: Filter by project name
- **Activity types**: `task_completed`, `bug_fixed`, `refactoring`, `research`, `documentation`, `review`
- **Tags**: Filter by custom tags
- **Output modes**: `by-date`, `by-project`, `by-type`, `json`

**Script usage:**
```bash
# Show today's activities
aggregate_activities.sh -r today

# Show this week's bug fixes
aggregate_activities.sh -r this-week -t bug_fixed

# Show all activities for a specific project
aggregate_activities.sh -p my-project -m by-date

# Export as JSON
aggregate_activities.sh -r this-month -m json > report.json
```

---

### 1. Action Items Extraction (NEW - Action Items 萃取)

Extract and track action items from work logs using AI semantic understanding:

```
「萃取所有 action items」
「誰需要做什麼？」
「本週的 action items」
「從會議記錄萃取 action items」
「Mary 負責哪些 action items？」
```

**Features:**
- AI-powered identification from discussions, decisions, and TODOs
- Automatically infer action items from:
  - Discussions: "Tom 會處理 API 設計"
  - Decisions: "決定使用 PostgreSQL" → "需要設計 schema"
  - Explicit TODOs and implicit actions
- Track status, owner, due dates, and priorities
- Structured table output grouped by priority/status
- Includes statistics and actionable recommendations

**Example:**
```
User: 從 example_action_items.md 萃取所有 action items

Response:
## Action Items 摘要

### 🔴 高優先級 & 過期

| 負責人 | 行動項目 | 期限 | 狀態 | 來源 |
|--------|----------|------|------|------|
| Tom | 實作 SellerCheck API endpoints | 2026-01-20 | ⏰ 已逾期 | 2026-01-15 Sprint Planning |
| Tom | 修正 token expiry 驗證 | 2026-01-16 | ⏰ 已逾期 | 2026-01-16 Code Review |

### 🟡 進行中

| 負責人 | 行動項目 | 期限 | 狀態 | 來源 |
|--------|----------|------|------|------|
| Mary | 撰寫 API 文件 | 2026-01-25 | 🔄 進行中 | 2026-01-15 Sprint Planning |
| Alex | 整合 L10n 到系統 | 2026-01-25 | 🔄 進行中 | 2026-01-15 Sprint Planning |

### 🟢 待處理

| 負責人 | 行動項目 | 期限 | 狀態 | 來源 |
|--------|----------|------|------|------|
| QA team | 驗證 bug 修正 | 2026-01-19 | 📝 待開始 | 2026-01-17 Bug Fixes |
| Tom | 加入 regression test | 2026-01-20 | 📝 待開始 | 2026-01-17 Bug Fixes |

**統計:**
- 總計 Action Items: 18 項
- 已完成: 5 項 (28%)
- 進行中: 6 項 (33%)
- 待處理: 5 項 (28%)
- 已逾期: 2 項 (11%) ⚠️

**建議:**
- ⚠️ Tom 的 SellerCheck API 已逾期，建議優先處理
- 📅 本週有 4 個 action items 到期，請留意時程
```

**Use Cases:**
- Action Items Management: Get comprehensive view of all pending actions
- Sprint Planning & Tracking: Track progress across team members
- Meeting Follow-ups: Convert discussions into trackable action items
- Team Accountability: Track who's responsible for what

**Try it:**
```
從 example_action_items.md 萃取所有 action items
```

---

### 2. Timeline Queries (演進分析)

Track how implementations, features, or decisions evolved:

```
「X 的演進」
「X 如何變化的？」
「X 的時間線」
"How did X evolve?"
"Timeline of X"
```

**Example:**
```
User: 幫我看 work.md，分析「認證系統的演進」

Response:
## 認證系統演進

### 2026-01-05 Monday: 初步設計
- 考慮使用 JWT tokens
- 擔心 refresh token 的儲存問題

### 2026-01-10 Saturday: 架構調整
- 決定加入 Redis 存放 session
- 理由：需要快速撤銷 token 的能力

### 2026-01-15 Thursday: 最終實作
- 實作 JWT + Redis hybrid 方案
- Access token: 15分鐘
- Refresh token: 7天，存於 Redis
```

### 3. TODO Management (任務管理)

Find pending, overdue, and completed tasks:

```
「未完成的 TODO」
「過期的任務」
「本週完成了什麼？」
"Pending TODOs"
"Overdue tasks"
"What did I complete this week?"
```

**Example:**
```
User: 檢查 journal.md，有哪些過期的 TODO？

Response:
## ⚠️ 過期任務

1. **Implement API rate limiting** (due: 2026-01-08)
   - 標記日期: 2026-01-05
   - 優先級: High
   - 狀態: 未開始

2. **Update security documentation** (due: 2026-01-12)
   - 標記日期: 2026-01-07
   - 最後提及: 2026-01-11 (討論需要哪些內容)

建議：這些任務已經過期，請評估是否仍需完成或調整優先級。
```

### 4. Decision Queries (決策追蹤)

Understand when and why decisions were made:

```
「為什麼選擇 X？」
「X 是何時決定的？」
「X 的決策理由」
"Why did we choose X?"
"When was X decided?"
"Decision rationale for X"
```

**Example:**
```
User: 從 notes.md 找出「為什麼選擇 TypeScript 而不是 JavaScript」

Response:
## TypeScript vs JavaScript 決策

### 決策日期: 2026-01-06

### 討論過程:

**2026-01-04 Sunday**: 初步討論
> "Team 討論是否要用 TypeScript，有人擔心學習曲線"

**2026-01-06 Tuesday**: **最終決定** ✓
> "決定採用 TypeScript，主要原因：
> 1. 大型專案需要型別安全
> 2. 更好的 IDE 支援
> 3. 減少 runtime errors
> 4. Team 有 3 人已熟悉 TypeScript"

### 考慮的替代方案:
- Plain JavaScript + JSDoc
- Flow (但生態系不如 TypeScript 活躍)

### Trade-offs:
- ✅ 優點: 型別安全、更好的重構支援
- ⚠️ 缺點: 編譯步驟、初期學習成本

**結論**: 長期收益大於短期成本，決定使用 TypeScript。
```

### 5. General Search (關鍵字搜尋)

Find all mentions of a topic:

```
「搜尋所有關於 X 的記錄」
「找出所有提到 Y 的地方」
"Search for X"
"Find all mentions of Y"
```

## Log Format Guide

### Recommended Format: Structured Markdown

```markdown
# 2026-01-13 Tuesday

## Project: SellerCheck

### Morning Session (09:00-12:00)

- Reviewed PR #123 from Alice
- Discussed database schema with Bob
- Decision: Use composite index on (seller_id, status)

### Afternoon Session (14:00-18:00)

- Implemented SellerCheck API endpoints
- Added rate limiting middleware
- TODO: Write integration tests (due: 2026-01-15) #high-priority

### TODOs
- [ ] TODO: Write integration tests (due: 2026-01-15) #high-priority
- [ ] TODO: Update API documentation (due: 2026-01-20)
- [x] TODO: Fix validation bug (completed: 2026-01-13)

### Decisions

**Decision**: Use Redis for rate limiting
**Rationale**: Need sub-millisecond response time, simple key-value sufficient
**Alternatives Considered**: PostgreSQL with window functions (too slow)
**Date**: 2026-01-13

### Notes
- Performance test shows 1000 req/s on single instance
- Need to discuss scaling strategy in next sprint planning
- Reference: https://redis.io/docs/manual/patterns/rate-limiter/

---
```

### TODO Format Options

All these formats are recognized:

```markdown
✅ With checkboxes (Recommended):
- [ ] TODO: Task description
- [x] TODO: Completed task

✅ With due dates:
- [ ] TODO: Task (due: 2026-01-20)
- [ ] TODO: Task (due: 2026-01-20) #high-priority

✅ With priorities:
- [ ] TODO: Critical bug fix #urgent #security
- [ ] TODO: Refactor code #low-priority

✅ Plain format:
- TODO: Simple task description
- FIXME: Code needs fixing
- HACK: Technical debt item

✅ Status indicators:
- [ ] TODO: Not started
- [~] TODO: In progress
- [x] TODO: Completed
```

### Decision Format Template

```markdown
## Decision: [Title]

**Context**: What situation led to this decision?
**Decision**: What did you decide?
**Rationale**: Why this decision?
**Alternatives**: What else was considered?
**Consequences**: What are the implications?
**Date**: YYYY-MM-DD
**Status**: [Proposed/Accepted/Deprecated/Superseded]
```

## Example Log File

Here's a complete example of a well-formatted work log:

```markdown
# Work Log 2026-01

## 2026-01-13 Tuesday

### SellerCheck Implementation

**Status**: In progress (Day 3 of 5)

#### Morning (09:00-12:00)
- Implemented seller verification API
- Added PostgreSQL schema for seller_info table
- Performance test: 500ms avg response time (too slow!)

**Decision**: Add Redis caching layer
- Without cache: 500ms
- With cache: 15ms (hit rate: 85% expected)
- Trade-off: Cache invalidation complexity

#### Afternoon (14:00-18:00)
- Implemented Redis caching
- Added cache invalidation logic
- New performance: 20ms avg (96% improvement!)

#### Blockers
- Waiting for Product team to confirm seller status enum values
- Asked via Slack, expecting response tomorrow

#### TODOs
- [ ] TODO: Add integration tests for SellerCheck API (due: 2026-01-15) #high
- [ ] TODO: Write API documentation (due: 2026-01-17)
- [ ] TODO: Code review with senior dev (due: 2026-01-16) #review
- [x] TODO: Implement caching layer (completed: 2026-01-13)

---

## 2026-01-12 Monday

### Weekend Research

- Researched Redis vs Memcached for caching
- Decision: Use Redis
  - Reason 1: Support for complex data structures
  - Reason 2: Better persistence options
  - Reason 3: Team already familiar with Redis

#### TODOs
- [ ] TODO: Set up Redis in staging environment (due: 2026-01-13)
- [x] TODO: Read Redis best practices documentation (completed: 2026-01-12)

---

## 2026-01-10 Saturday

### SellerCheck Design Meeting

**Attendees**: Alice (PM), Bob (Backend), Carol (Frontend), Me

**Key Decisions**:
1. **API Design**: RESTful over GraphQL
   - Simpler for this use case
   - Frontend team more familiar with REST

2. **Database Choice**: PostgreSQL over MongoDB
   - Need strong consistency
   - Complex relational queries required
   - ACID guarantees important for seller verification

3. **Caching Strategy**: TBD (researching options)

#### Action Items
- [x] TODO: Research caching solutions (completed: 2026-01-12)
- [ ] TODO: Create database schema proposal (due: 2026-01-13)
- [ ] TODO: Draft API specification (due: 2026-01-14)

#### Notes
- Carol mentioned frontend needs real-time updates
- Consider WebSocket for status changes
- Need to check with DevOps about Redis infrastructure

---

## 2026-01-05 Monday

### New Project: SellerCheck

**Objective**: Build a system to verify and track seller authenticity

**Initial Ideas**:
- Use ML for fraud detection? (Maybe phase 2)
- Manual review workflow for edge cases
- Integration with existing user management system

**Questions to Resolve**:
- What's the expected QPS?
- How many sellers in the system?
- What's the SLA for verification time?

#### TODOs
- [ ] TODO: Schedule kickoff meeting with PM (due: 2026-01-06)
- [x] TODO: Review existing seller data structure (completed: 2026-01-05)

---
```

## Usage Examples

### Example 1: Sprint Retrospective

```
User: 幫我分析 work_jan.md，「本週（1/13-1/19）做了哪些重要決策？」

Claude will:
1. Read the log file
2. Filter entries from 2026-01-13 to 2026-01-19
3. Extract all decision-related content
4. Summarize key decisions with dates and rationale
```

### Example 2: Daily Standup Prep

```
User: 從 journal.md 整理「昨天完成了什麼、今天計劃做什麼、有什麼阻礙？」

Claude will:
1. Find yesterday's completed tasks
2. Find today's planned/in-progress tasks
3. Extract any mentioned blockers
4. Format as standup-ready summary
```

### Example 3: Documentation Generation

```
User: 根據 devlog.md 中關於「認證系統」的所有決策，生成 Architecture Decision Record

Claude will:
1. Extract all authentication-related decisions
2. Compile context, rationale, alternatives
3. Generate a structured ADR document
4. Include timeline of decisions
```

### Example 4: Technical Debt Tracking

```
User: 找出 notes.md 中所有的 HACK、FIXME 和 TODO 技術債項目

Claude will:
1. Search for HACK, FIXME, TODO patterns
2. Categorize by urgency/priority
3. Show when each was added
4. Highlight overdue or long-standing issues
```

## Best Practices

### 1. Daily Logging Routine

**End of day template**:
```markdown
## 2026-01-13 Tuesday

### Completed Today
- [x] Implemented feature X
- [x] Fixed bug Y
- [x] Code review for PR Z

### Learned Today
- Redis pipelining can improve performance by 40%
- Always test error paths explicitly

### Tomorrow's Plan
- [ ] Write tests for feature X
- [ ] Deploy to staging
- [ ] Sync with PM about timeline

### Blockers
- Waiting for API key from external service
```

### 2. Decision Documentation

Always include:
- **What** was decided
- **Why** it was decided
- **When** it was decided
- **Who** was involved
- **What alternatives** were considered
- **What are the trade-offs**

### 3. TODO Management

Use consistent format:
```markdown
- [ ] TODO: [Action verb] [specific task] (due: YYYY-MM-DD) #tag
```

Good examples:
- `- [ ] TODO: Implement rate limiting middleware (due: 2026-01-20) #security`
- `- [ ] TODO: Refactor user service to use async/await (due: 2026-01-25) #refactor`

### 4. Tagging Strategy

Use tags for easy filtering:
```markdown
#bug #feature #refactor #security #performance
#database #api #frontend #backend
#urgent #high-priority #low-priority
#blocked #in-review #ready-to-deploy
```

### 5. Link Related Entries

```markdown
See 2026-01-10 for initial discussion
Related to PR #456
Follows up on 2026-01-05 decision about database choice
```

## Integration Ideas

### With Other Skills

1. **commit-msg-generator**
   ```
   幫我根據 work.md 今天的工作記錄生成 commit message
   ```

2. **code-story-teller**
   ```
   結合 work.md 和 src/auth.js 的 git history，說明認證系統的完整演進
   ```

3. **spec-generator**
   ```
   根據 devlog.md 中關於「推薦系統」的討論和決策，生成完整的功能規格
   ```

### With External Tools

1. **Export to Notion/Confluence**
   - Use log analysis to generate documentation

2. **Sync with Jira/Linear**
   - Extract TODOs and create tickets

3. **Generate Reports**
   - Weekly/monthly progress reports
   - Sprint retrospective summaries

## Tips for Effective Logging

1. **Be Consistent**: Log daily, even if just a few lines
2. **Be Specific**: "Implemented auth" < "Implemented JWT-based authentication with Redis session store"
3. **Include Context**: Not just what, but why and how
4. **Document Failures**: Failed experiments are valuable knowledge
5. **Update TODOs**: Mark them complete, adjust dates, add new ones
6. **Use Templates**: Create daily/weekly templates for consistency
7. **Review Regularly**: Weekly review to extract patterns and insights
8. **Keep It Simple**: Don't over-engineer your logging system

## Troubleshooting

### Issue: TODOs not being detected

**Solution**: Ensure consistent format
```markdown
✅ Good: - [ ] TODO: Task description
❌ Bad:  - [] TODO Task description (missing space in checkbox)
❌ Bad:  TODO: Task description (no checkbox)
```

### Issue: Dates not parsed correctly

**Solution**: Use ISO format
```markdown
✅ Good: 2026-01-13
✅ Good: # 2026-01-13 Tuesday
❌ Bad:  Jan 13, 2026 (might work but less reliable)
❌ Bad:  13/01/2026 (ambiguous)
```

### Issue: Cannot find specific topic

**Solution**: Use consistent terminology and tags
```markdown
✅ Good: #authentication #auth (use both)
❌ Bad:  Sometimes "auth", sometimes "authentication", sometimes "login"
```

### Issue: Log file too large

**Solution**: Split by time period
```markdown
work_log_2026_01.md
work_log_2026_02.md
```

## Advanced Use Cases

### 1. Personal Performance Review

```
Query: "分析 2026 Q1 的工作日誌，總結主要成就、學習和改進方向"

Output:
- Major projects and contributions
- Skills learned
- Problems solved
- Areas for improvement
```

### 2. Team Knowledge Base

```
Query: "從過去三個月的 team_log.md 提取所有架構決策，生成 ADR 文件"

Output:
- Structured Architecture Decision Records
- Decision timeline
- Rationale and trade-offs
```

### 3. Project Post-Mortem

```
Query: "分析 SellerCheck 專案從開始到完成的完整時間線，包括所有決策、阻礙和解決方案"

Output:
- Complete project timeline
- Key decisions and their impact
- Challenges faced and solutions
- Lessons learned
```

## Contributing

Have ideas for improving this skill? See [CONTRIBUTING.md](../CONTRIBUTING.md) for how to contribute.

## License

This skill is part of the Claude Code Skills repository.

---

**Note**: This skill analyzes logs but does not modify them. It's read-only for safety.
