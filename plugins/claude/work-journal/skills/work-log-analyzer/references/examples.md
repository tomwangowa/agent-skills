> **Read this when**: you need the expected output format for Timeline / TODO Management / Decision Tracking / General Search queries. The 5th query type (Activity Aggregation) has its inline example in SKILL.md.

# Work Log Analyzer — Query Examples

## Timeline

**User:**
> 我有一個 work.md 檔案，幫我分析「關於 SellerCheck 實作方案的演進」

**Expected behavior:**
1. Read the `work.md` file (or call `mcp__skills-query__query_timeline` with `topic: "SellerCheck"`)
2. Extract all mentions of the topic chronologically
3. Summarize the evolution:
   - Initial consideration (date, initial thoughts)
   - Design iterations (what changed and why)
   - Final decision (current approach)
4. Present as a timeline with key milestones

**Example output:**

```markdown
## SellerCheck 實作方案演進

### 2026-01-05: 初步討論
- 考慮使用 Redis 做快取層
- 擔心資料持久性問題

### 2026-01-08: 架構調整
- 決定改用 PostgreSQL 作為主要儲存
- 原因：需要 ACID 保證和 joins across multiple tables
- Redis 仍用於快取層

### 2026-01-13: 最終方案
- 實作混合架構：PostgreSQL + Redis
- 已完成 schema 設計
- 下一步：實作 API endpoints
```

---

## TODO Management

**User:**
> 檢查我的 journal.md，哪些 TODO 還沒完成？哪些已經過期？

**Expected behavior:**
1. Read `journal.md` (or call `mcp__skills-query__query_todos` with `status: "pending"`)
2. Extract all TODO items
3. Parse status (`[ ]` vs `[x]`) and due dates
4. Compare with current system date
5. Categorize into overdue / pending / recently completed and present

**State the reference date explicitly** so the user can verify overdue calculations (e.g., "分析日期: 2026-04-20").

**Example output:**

```markdown
## TODO 狀態報告 (分析日期: 2026-01-13)

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

## Decision Tracking

**User:**
> 從 devlog.txt 找出「Lite Engagement 的 L10n 翻譯何時確定的？」

**Expected behavior:**
1. Read `devlog.txt` (or call `mcp__skills-query__query_decisions` with `keyword: "L10n Lite Engagement"`)
2. Find decision-related entries matching both "Lite Engagement" and "L10n" / "翻譯"
3. Extract timeline and rationale
4. Present the answer with the specific confirming date highlighted

**Example output:**

```markdown
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

---

## General Search

**User:**
> 搜尋 notes.md 中關於「authentication」的所有提及

**Expected behavior:**
1. Read `notes.md` (or call `mcp__skills-query__search` with `keyword: "authentication"`)
2. Find all mentions of the keyword
3. Extract surrounding context (2-3 lines per hit)
4. Group by date or by relevance
5. Present findings with citations back to date / section

**Output shape**: grouped hits with date headers, each quote followed by a one-line summary of context. If hits span many dates, offer a follow-up: "Want me to drill into a specific date range, or convert these into a Timeline view?"
