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

## 共用設定與啟動

Claude Code CLI、Codex CLI 與 shell logger 使用同一份 `work-journal.json`。設定根目錄依序採用 `AGENT_SKILLS_CONFIG_DIR`、`XDG_CONFIG_HOME/agent-skills`、目前使用者的 `~/.config/agent-skills`；明確環境根目錄必須是絕對路徑或 `~/` 路徑。

從 repo 根目錄，先預覽並確認你選定的活動與筆記目錄，再執行首次設定：

```sh
PYTHONPATH=runtime python3 -m agent_skills_runtime.setup --activities "<selected-activity-directory>" --notes "<selected-notes-directory>" --preview
```

替換範例中的兩個目錄，確認預覽後以相同參數移除 `--preview` 執行一次。可以直接指定既有資料目錄；setup 保留已存在的設定，不自動搬移活動紀錄。

```json
{
  "sources": {
    "activities": "journal",
    "notes": { "paths": ["notes"], "recursive": true, "exclude_hidden": true }
  }
}
```

相對資料路徑從設定根目錄解析，與啟動時所在目錄無關。`CLAUDE_ACTIVITIES_DIR` 覆寫活動目錄；相對的覆寫值也從設定根目錄解析。兩個程序必須使用相同環境。變更設定或環境後，重啟 MCP process，讓它取得新設定。

來源開發需要先安裝 lockfile 的依賴並編譯；正式發佈包已帶 JavaScript 與正式依賴，不在每次啟動時下載或編譯：

```sh
npm --prefix skills-query-server ci
npm --prefix skills-query-server run build
node skills-query-server/dist/index.js
```

正式入口不需要 server 旁的私人 `config.json`、`tsx` 或 TypeScript compiler。缺設定、空筆記路徑或不可讀寫的活動目錄，會在 stderr 回報具體問題並退出；stdout 留給 MCP 協定，不會假裝啟動成功。

只供來源開發與隔離測試的明確設定入口仍保留：

```sh
node skills-query-server/dist/index.js --config "<explicit-development-config.json>"
```

這條入口只讀明確指定的設定，保留原本 `loadConfig(configPath)` 行為；正式入口不會以它作為隱藏的 fallback。Plugin 的 MCP 註冊與安裝格式由後續產生器處理；本節命令不會修改你的全域 MCP 設定。

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

## Development toolchain

Source tests use Vitest 5 and require a supported Node version: Node 22.x at 22.12 or later, Node 24.x, or Node 26+. This branch was tested with an isolated Node 24.21.0 toolchain; the user's global Node remains unchanged. Compiled production stdio also passes on the existing Node 23.7.0; this is an observation, not a minimum support claim. YAML/JSON frontmatter is parsed as data only; executable language engines are rejected.
