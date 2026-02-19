# Skills Query MCP Server

A TypeScript MCP server that provides structured query tools for activity logs, QA knowledge notes, and work history.

## Tools

| Tool | Description |
|------|-------------|
| `query_activities` | Filter and group work activity records by date/project/type/tag |
| `search` | Cross-source full-text search across activities and notes |
| `log_activity` | Record a new work activity entry |
| `query_timeline` | Track how a topic evolved over time |
| `query_todos` | Extract TODO/FIXME items from activity records |
| `query_decisions` | Trace when and why decisions were made |
| `dashboard` | Overview of recent work with stats and distribution |

## Setup

### 1. Configure data sources

Edit `config.json`:

```json
{
  "sources": {
    "activities": "~/.claude/activities",
    "notes": "~/path/to/QA-TO-NOTES"
  }
}
```

### 2. Install dependencies

```bash
npm install
```

### 3. Register with Claude Code

```bash
claude mcp add -s user skills-query -- npx tsx /path/to/skills-query-server/src/index.ts
```

### 4. Verify

Start a new Claude Code session and try:

```
> what did I do this week?
> search for PicoClaw
> show my dashboard
```

## Development

```bash
npm test          # run tests
npm run test:watch # watch mode
npm run build     # compile TypeScript
npm run dev       # run server directly
```

## Architecture

```
src/
├── index.ts              # MCP server entry point
├── config.ts             # Config loader with ~ expansion
├── types.ts              # TypeScript interfaces
├── sources/
│   ├── activities.ts     # Activity log reader + filter
│   └── notes.ts          # QA notes reader + search
├── tools/
│   ├── query-activities.ts
│   ├── search.ts
│   ├── log-activity.ts
│   ├── query-timeline.ts
│   ├── query-todos.ts
│   ├── query-decisions.ts
│   └── dashboard.ts
└── utils/
    ├── date-range.ts     # Date range parser
    └── text-search.ts    # Cross-source search
```
