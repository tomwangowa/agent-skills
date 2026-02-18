# Skills Query MCP Server — Design Document

**Date:** 2026-02-18
**Status:** Approved

---

## 1. Overview

A TypeScript MCP server that lets Claude Code query work history and knowledge notes using natural language. Users don't need to remember any syntax — just say "what did I do this week" or "what was the conclusion on that PicoClaw fact-check", and Claude invokes the right tool.

### Problem

- **Query syntax is hard to remember** — 5 query types, multiple flags, different scripts
- **Results are hard to digest** — raw Markdown/JSON output in terminal
- **Cross-session context is fragmented** — activity logs, work logs, and knowledge notes live in separate silos

### Solution

A single MCP server that unifies three data sources and exposes 7 structured tools. Claude Code handles natural language → tool selection → result formatting.

---

## 2. Data Sources

| Source | Path | Format | Content |
|--------|------|--------|---------|
| Activities | `~/.claude/activities/*.json` | JSON | Structured work records (type, description, tags, commits) |
| Activities (archived) | `~/.claude/activities/processed/` | JSON | Archived historical records |
| QA Notes | Configurable (Obsidian vault) | Markdown + YAML frontmatter | Knowledge notes (tags, date, structured content) |

### Activity Schema

```typescript
interface ActivityFile {
  session_id: string;
  timestamp: string;
  project_path: string;
  project_name: string;
  git_branch: string;
  git_remote: string;
  activities: {
    type: string;       // task_completed, bug_fixed, refactoring, research, documentation, review
    description: string;
    files_changed: string[];
    commits: string[];
  }[];
  context: string;
  tags: string[];
}
```

### QA Note Schema

```typescript
interface QANote {
  filename: string;
  date: string;         // from frontmatter
  tags: string[];       // from frontmatter
  source: string;       // from frontmatter (e.g. "claude-code")
  title: string;        // first H1
  content: string;      // full text
  summary: string;      // first paragraph under "概述" or "Overview"
}
```

---

## 3. MCP Tools

### Query Tools (5)

| Tool | Parameters | Description |
|------|-----------|-------------|
| `query_activities` | `range` (today/yesterday/this-week/last-week/this-month/all), `project?`, `type?`, `tag?`, `group_by?` (date/project/type) | Aggregate activity records with filtering and grouping |
| `query_timeline` | `topic` | Track how a topic evolved over time (across activities + notes) |
| `query_todos` | `status?` (pending/in-progress/completed/all) | Extract TODO items from activity records |
| `query_decisions` | `keyword` | Trace decisions: why was X chosen, when was it decided |
| `search` | `keyword`, `source?` (activities/notes/all) | Cross-source full-text search |

### Record Tool (1)

| Tool | Parameters | Description |
|------|-----------|-------------|
| `log_activity` | `description`, `type`, `context?`, `tags?` | Log an activity entry (replaces direct shell script invocation) |

### Overview Tool (1)

| Tool | Parameters | Description |
|------|-----------|-------------|
| `dashboard` | `range?` (default: this-week) | Weekly summary: activity count, project distribution, recent notes, pending TODOs |

### Design Decisions

- `search` is the unified cross-source entry point. Searches JSON fields for activities, full-text + frontmatter tags for notes.
- `query_timeline` and `query_decisions` also cross sources — a decision may appear in an activity record and have deeper analysis in a QA note.
- `dashboard` is a compound tool that combines multiple queries internally, ideal for getting context at the start of a session.

---

## 4. Data Access Layer

### Activities — Direct Read

MCP server reads JSON files directly via Node.js `fs`. No shell script invocation.

Rationale:
- Rewriting `aggregate_activities.sh` logic in TypeScript is cleaner
- No shell process spawn overhead
- Type-safe, easy to add indexing or caching later

### QA Notes — Parse with gray-matter

Use `gray-matter` to parse YAML frontmatter, extract `tags`, `date`, `source`. Full text serves as search content.

### Caching Strategy

Build an in-memory index on startup (file path → metadata). Read full content on demand per query. File count is in the hundreds — no database needed.

### Configuration

Data source paths are specified in a config file, not hardcoded:

```json
{
  "sources": {
    "activities": "~/.claude/activities",
    "notes": "~/Library/CloudStorage/GoogleDrive-.../QA-TO-NOTES"
  }
}
```

---

## 5. Project Structure

```
skills-query-server/
├── package.json
├── tsconfig.json
├── src/
│   ├── index.ts              # MCP server entry, register tools
│   ├── config.ts             # Read config, resolve paths
│   ├── sources/
│   │   ├── activities.ts     # Activities JSON read, filter, aggregate
│   │   └── notes.ts          # QA Notes parsing (gray-matter + full-text)
│   ├── tools/
│   │   ├── query-activities.ts
│   │   ├── query-timeline.ts
│   │   ├── query-todos.ts
│   │   ├── query-decisions.ts
│   │   ├── search.ts
│   │   ├── log-activity.ts
│   │   └── dashboard.ts
│   └── utils/
│       ├── date-range.ts     # Date range parsing (today, this-week, etc.)
│       └── text-search.ts    # Simple full-text search (keyword matching)
├── config.json               # Data source path configuration
└── README.md
```

### Dependencies (3 only)

- `@modelcontextprotocol/sdk` — MCP server SDK
- `gray-matter` — YAML frontmatter parsing
- `glob` — File scanning (or Node.js built-in `fs.glob` on Node 22+)

### Installation

Add to Claude Code MCP settings:

```json
{
  "mcpServers": {
    "skills-query": {
      "command": "npx",
      "args": ["tsx", "/path/to/skills-query-server/src/index.ts"],
      "env": {}
    }
  }
}
```

Use `tsx` for development; build to JS once stable.

---

## 6. Error Handling & Edge Cases

### Startup

- config.json missing or invalid paths → clear error message guiding user to configure
- Empty data directories → tools work normally, return empty results (not errors)

### Query Time

- No data in date range → return "no records in this range" with the date of the most recent record for reference
- QA Note with malformed frontmatter → skip file, log warning, don't break the query
- Search returns no results → suggest broadening criteria (different keywords or wider time range)

### Performance

- Hundreds of files, all in-memory operations. No need to defend against large data scenarios.
- If file count exceeds expectations in the future, add LRU cache. Not now.

### Out of Scope

- No writing to QA Notes (that's qa-to-notes skill's responsibility)
- No deleting or modifying activity records (append-only)
- No real-time file watching (re-scan on each query — simple and reliable)
