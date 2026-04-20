---
name: work-log-analyzer
description: Use when the user wants to query their work journal, track task progress, or understand how decisions evolved over time. Analyzes activity-logger records and work logs to answer questions about project history, decisions, TODOs, and timeline evolution.
---

# Work Log Analyzer

Analyzes activity-logger records (`~/.claude/activities/`) and user-supplied work logs to answer questions about project history, TODOs, decisions, and topic evolution. Read-only.

---

## References

Load these files on demand — they are not needed for every query:

| File | Read when |
|------|-----------|
| `references/examples.md` | You need the expected output format for a Timeline, TODO Management, Decision Tracking, or General Search query. |
| `references/log-formats.md` | The user supplies non-structured log content, or you need to verify a TODO / date / decision format variant before parsing. |
| `README.md` | Human-facing usage guide (use cases, best practices, tips). Usually not needed for agent execution; point the user there if they ask *how* to write their logs. |

---

## Instructions

When the user asks about their work journal, TODOs, project history, or past decisions, follow the workflow below.

### Workflow

**Step 0 — Data Access Priority: PREFER `mcp__skills-query__*` tools when available**

This skill has two backends for querying activity records:

- **Primary (preferred)**: `mcp__skills-query__*` MCP tools, exposed by the **Skills Query MCP Server** at `~/.claude/skills/skills-query-server/`. Structured, typed, cross-source (activities + QA notes).
- **Fallback**: the shell script `<skill_base_directory>/scripts/aggregate_activities.sh`. Only supports Activity Aggregation.

**Decision rule (concrete procedure)**:

1. **Detect MCP availability** — scan the session's available tools list for any tool whose name starts with `mcp__skills-query__`. The list is visible in the system reminder delivered at session start.
   - ✅ Found → use MCP tools for all query types. Skip steps 2–3.
   - ❌ Not found → continue to step 2.

2. **Handle "MCP not found" gracefully**:
   - Tell the user explicitly: *"Skills Query MCP server 沒有在這個 session 掛載，改用 shell script fallback。功能仍可用，但 cross-source search（notes + activities）和 dashboard 不會運作。"*
   - Fall back to `<skill_base_directory>/scripts/aggregate_activities.sh` for Activity Aggregation.
   - For Timeline / TODO / Decision Tracking / General Search: use `jq` + `grep` against `~/.claude/activities/*.json` directly.
   - For Recent Overview (dashboard): tell the user this query type requires the MCP server; offer a manual aggregation instead.

3. **Offer recovery path** (only if the user wants full functionality):
   - Provide the one-liner to register the MCP server:
     ```bash
     claude mcp add -s user skills-query -- npx tsx ~/.claude/skills/skills-query-server/src/index.ts
     ```
   - A new session is required after registration.
   - Do NOT auto-run this command — confirm with the user first.
   - After offering recovery, **end here** — do not retry `mcp__skills-query__*` tools in the same session. Ask the user to restart Claude Code and re-issue the query.

**Do NOT** attempt to call `mcp__skills-query__*` speculatively when it is not in the tool list; it will fail with `InputValidationError` rather than a clean "not found" signal.

**Tool mapping** (query type → MCP tool + fallback + reference):

| Query Type | MCP Tool | Fallback | Output format |
|------------|----------|----------|---------------|
| Activity Aggregation | `mcp__skills-query__query_activities` | `aggregate_activities.sh` | see [Inline Example](#inline-example-activity-aggregation) below |
| Timeline | `mcp__skills-query__query_timeline` | grep + manual sort | `references/examples.md#timeline` |
| TODO Management | `mcp__skills-query__query_todos` | grep TODO/FIXME patterns | `references/examples.md#todo-management` |
| Decision Tracking | `mcp__skills-query__query_decisions` | keyword search + manual synthesis | `references/examples.md#decision-tracking` |
| General Search | `mcp__skills-query__search` | grep across activity JSONs | `references/examples.md#general-search` |
| Recent Overview | `mcp__skills-query__dashboard` | N/A | — |

**Step 1 — Identify input source**

- User names an activity-logger query (date range / project / tag / keyword) → use MCP tool or shell fallback per Step 0
- User provides a log file path → Read the file
- User pastes content directly → analyze the provided text
- User says "my journal" / "my work log" without specifics → ask for the path or date range

**Step 2 — Parse and classify the query** into one of these 5 types (matching the Tool mapping table above):

| Query Type | Trigger phrases |
|------------|----------------|
| **Activity Aggregation** | "aggregate my activities", "本週做了什麼", "this month's bug fixes" |
| **Timeline** | "X 的演進", "how did X evolve", "X 的時間線" |
| **TODO Management** | "未完成的 TODO", "過期的任務", "pending tasks" |
| **Decision Tracking** | "為什麼選擇 X", "X 的決策過程", "when was X decided" |
| **General Search** | keyword or topic search without structural intent |

If the query needs a parser hint (unusual log format, non-ISO dates, TODO variants), Read `references/log-formats.md` first.

**Step 3 — Execute**

- Call the preferred MCP tool with the required params (see Tool mapping table)
- Before generating output for Timeline / TODO Management / Decision Tracking / General Search, Read `references/examples.md` to match the expected format
- Never silently fail — see Error Handling below

**Step 4 — Analyze and present**

- Connect entries across dates; identify patterns
- Cite dates / sections for traceability
- For TODO queries: always state the reference date used for overdue calculation (e.g., "分析日期: 2026-04-20")
- For Timeline / Decision Tracking: present chronologically
- For ambiguous dates resolved by the skill: show the absolute date so the user can verify
- Suggest follow-up queries only when the answer is partial or spans related topics

### Output Requirements

- **Structured**: headings, bullets, quotes
- **Chronological** for Timeline / Decision Tracking
- **Action-oriented** for TODOs with status + due dates + reference date
- **Cited**: every claim traces to a date or activity record

---

## Inline Example: Activity Aggregation

The most common query type. Full examples for the other 4 types live in `references/examples.md`.

**User:** "本週做了什麼？"

**Execute:** `mcp__skills-query__query_activities` with `range: "this-week"`
(or fallback: `aggregate_activities.sh -r this-week`)

**Output shape** (N = actual count; replace with real numbers):
```markdown
# 本週工作摘要 (2026-04-14 ~ 2026-04-20)

## 完成的任務
- 實作 work-log-analyzer MCP 路由規則 (2026-04-20)
  - 專案：claude-skills

## 修復的問題
- Seller Check ScraperAPI 404 for non-US Amazon (2026-04-16)
  - 專案：fb-seller-check

## 統計
- 總活動數：N
- 涉及專案：N
```

---

## Limitations

- Cannot access external files / URLs referenced inside logs
- Read-only — does not modify activity records or user logs
- Date parsing is most reliable with ISO format (`YYYY-MM-DD`); ambiguous formats will be resolved and the resolution stated
- Very large logs (>10,000 lines) should be filtered / chunked before analysis
- Cannot track TODOs across multiple log files simultaneously — analyze one at a time
- Assumes the Skills Query MCP server is installed at `~/.claude/skills/skills-query-server/`. If the server is relocated or uninstalled, the recovery command in Step 0 must be updated accordingly

---

## Error Handling

This skill is read-only and query-oriented. Handle these common failure modes:

- **Log file not found** (user-supplied path): report the exact path tried and ask the user to confirm or paste the log content directly.
- **Empty result set** (e.g., project name typo, wrong date range): surface the exact filter used and suggest 1–2 corrections (alternative project names seen in recent activities, or expanding the range).
- **Malformed activity record JSON**: skip the malformed record, continue aggregating, and list the skipped file path at the end so the user can investigate.
- **MCP server unavailable**: follow the three-step procedure in Step 0 (detect → degrade → offer recovery). Never silently fail.
- **Ambiguous date phrase** (e.g., "last Thursday" crossing a week boundary): state the absolute date(s) the skill resolved to (e.g., "interpreting 'last Thursday' as 2026-04-16") so the user can correct before trusting the output.
- **Large log file (>10,000 lines)**: inform the user before reading; offer to read in chunks or to filter the scope first.

---

## Security Considerations

The skill operates on the user's local work logs and activity records, which may contain sensitive context.

- **Read-only by default**: the skill does not modify activity records. If the user asks it to rewrite or purge logs, require explicit confirmation and show the exact file path before acting.
- **Path safety**: when the user supplies a log file path, validate it resolves within expected directories (`~/.claude/activities/`, the user's project, or the path the user explicitly named). Reject relative paths containing `../` that escape the intended root.
- **Sensitive tags**: activity records may carry tags like `credentials`, `secret`, `api-key`, `auth`, or `token`. If a query surfaces records with these tags, warn the user before including the record content in output, especially when producing a report destined for external sharing.
- **No network egress**: the skill runs locally against `~/.claude/activities/` and user-supplied log files; it does not POST logs to external services. If a downstream skill (e.g., `report-generator` → DOCX/PDF conversion) might upload content, warn the user.
- **Report output sanitization**: when generating shareable output (weekly / monthly reports), redact tokens matching common credential patterns (`AKIA[0-9A-Z]{16}`, `xox[baprs]-`, `ghp_`, `Bearer `) and ask the user to confirm before saving.
- **No execution of log content**: never `eval` or shell-execute strings extracted from activity records, even if they look like commands.

---

> Want to turn this into a formal report? Try `report-generator`.
