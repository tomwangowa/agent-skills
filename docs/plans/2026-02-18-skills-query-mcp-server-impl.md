# Skills Query MCP Server — Implementation Plan

> **For Claude:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task.

**Goal:** Build a TypeScript MCP server that lets Claude Code query activity logs, archived activities, and QA-to-notes via 7 structured tools.

**Architecture:** A single MCP server process reads JSON activity files and Markdown notes from configurable paths. Each query tool parses files on demand, returns structured text for Claude to present. Uses stdio transport for Claude Code integration.

**Tech Stack:** TypeScript, `@modelcontextprotocol/sdk`, `gray-matter`, `zod`, `vitest`

**Design doc:** `docs/plans/2026-02-18-skills-query-mcp-server-design.md`

---

### Task 1: Project Scaffolding

**Files:**
- Create: `skills-query-server/package.json`
- Create: `skills-query-server/tsconfig.json`
- Create: `skills-query-server/.gitignore`

**Step 1: Create project directory**

```bash
mkdir -p skills-query-server/src/{sources,tools,utils}
```

**Step 2: Initialize package.json**

Create `skills-query-server/package.json`:

```json
{
  "name": "skills-query-server",
  "version": "0.1.0",
  "private": true,
  "type": "module",
  "scripts": {
    "dev": "tsx src/index.ts",
    "build": "tsc",
    "test": "vitest run",
    "test:watch": "vitest"
  }
}
```

**Step 3: Install dependencies**

```bash
cd skills-query-server
npm install @modelcontextprotocol/sdk gray-matter glob zod
npm install -D typescript tsx vitest @types/node
```

**Step 4: Create tsconfig.json**

Create `skills-query-server/tsconfig.json`:

```json
{
  "compilerOptions": {
    "target": "ES2022",
    "module": "Node16",
    "moduleResolution": "Node16",
    "outDir": "dist",
    "rootDir": "src",
    "strict": true,
    "esModuleInterop": true,
    "skipLibCheck": true,
    "declaration": true
  },
  "include": ["src"],
  "exclude": ["node_modules", "dist"]
}
```

**Step 5: Create .gitignore**

Create `skills-query-server/.gitignore`:

```
node_modules/
dist/
```

**Step 6: Verify setup compiles**

```bash
npx tsc --noEmit
```

Expected: No errors (no source files yet, should pass cleanly).

**Step 7: Commit**

```bash
git add skills-query-server/
git commit -m "feat(skills-query-server): scaffold project with deps"
```

---

### Task 2: Config and Types

**Files:**
- Create: `skills-query-server/src/types.ts`
- Create: `skills-query-server/src/config.ts`
- Create: `skills-query-server/config.json`
- Test: `skills-query-server/src/config.test.ts`

**Step 1: Write types**

Create `skills-query-server/src/types.ts`:

```typescript
// Activity file schema (from ~/.claude/activities/*.json)
export interface ActivityEntry {
  type: string;
  description: string;
  files_changed: string[];
  commits: string[];
}

export interface ActivityFile {
  session_id: string;
  timestamp: string;
  project_path: string;
  project_name: string;
  git_branch: string;
  git_remote: string;
  activities: ActivityEntry[];
  context: string;
  tags: string[];
}

// QA Note schema (from Obsidian vault)
export interface QANote {
  filename: string;
  filepath: string;
  date: string;
  tags: string[];
  source: string;
  title: string;
  content: string;
  summary: string;
}

// Config schema
export interface Config {
  sources: {
    activities: string;
    notes: string;
  };
}
```

**Step 2: Write the failing test for config**

Create `skills-query-server/src/config.test.ts`:

```typescript
import { describe, it, expect, beforeEach, afterEach } from 'vitest';
import { loadConfig } from './config.js';
import { writeFileSync, mkdirSync, rmSync } from 'fs';
import { join } from 'path';
import { tmpdir } from 'os';

describe('loadConfig', () => {
  const testDir = join(tmpdir(), 'skills-query-test-config');

  beforeEach(() => {
    mkdirSync(testDir, { recursive: true });
  });

  afterEach(() => {
    rmSync(testDir, { recursive: true, force: true });
  });

  it('loads valid config file', () => {
    const configPath = join(testDir, 'config.json');
    writeFileSync(configPath, JSON.stringify({
      sources: {
        activities: '/tmp/activities',
        notes: '/tmp/notes'
      }
    }));
    const config = loadConfig(configPath);
    expect(config.sources.activities).toBe('/tmp/activities');
    expect(config.sources.notes).toBe('/tmp/notes');
  });

  it('expands ~ in paths', () => {
    const configPath = join(testDir, 'config.json');
    writeFileSync(configPath, JSON.stringify({
      sources: {
        activities: '~/.claude/activities',
        notes: '~/notes'
      }
    }));
    const config = loadConfig(configPath);
    expect(config.sources.activities).not.toContain('~');
    expect(config.sources.activities).toContain('.claude/activities');
  });

  it('throws on missing config file', () => {
    expect(() => loadConfig('/nonexistent/config.json'))
      .toThrow('Config file not found');
  });

  it('throws on missing sources field', () => {
    const configPath = join(testDir, 'config.json');
    writeFileSync(configPath, JSON.stringify({}));
    expect(() => loadConfig(configPath)).toThrow();
  });
});
```

**Step 3: Run test to verify it fails**

```bash
cd skills-query-server && npx vitest run src/config.test.ts
```

Expected: FAIL — `loadConfig` not found.

**Step 4: Implement config**

Create `skills-query-server/src/config.ts`:

```typescript
import { readFileSync, existsSync } from 'fs';
import { homedir } from 'os';
import { resolve } from 'path';
import type { Config } from './types.js';

function expandHome(p: string): string {
  if (p.startsWith('~/')) {
    return resolve(homedir(), p.slice(2));
  }
  return resolve(p);
}

export function loadConfig(configPath: string): Config {
  if (!existsSync(configPath)) {
    throw new Error(
      `Config file not found: ${configPath}\n` +
      'Create a config.json with:\n' +
      '{\n  "sources": {\n    "activities": "~/.claude/activities",\n    "notes": "~/path/to/QA-TO-NOTES"\n  }\n}'
    );
  }

  const raw = JSON.parse(readFileSync(configPath, 'utf-8'));

  if (!raw.sources?.activities || !raw.sources?.notes) {
    throw new Error('Config must have sources.activities and sources.notes');
  }

  return {
    sources: {
      activities: expandHome(raw.sources.activities),
      notes: expandHome(raw.sources.notes),
    },
  };
}
```

**Step 5: Run test to verify it passes**

```bash
cd skills-query-server && npx vitest run src/config.test.ts
```

Expected: All 4 tests PASS.

**Step 6: Create default config.json**

Create `skills-query-server/config.json`:

```json
{
  "sources": {
    "activities": "~/.claude/activities",
    "notes": "~/Library/CloudStorage/GoogleDrive-tomwang.owa@gmail.com/My Drive/Obsidian KEEP/Working notes/Journal 2005/私人資訊/QA-TO-NOTES"
  }
}
```

**Step 7: Commit**

```bash
git add skills-query-server/src/types.ts skills-query-server/src/config.ts skills-query-server/src/config.test.ts skills-query-server/config.json
git commit -m "feat(skills-query-server): add types and config loader with tests"
```

---

### Task 3: Activities Data Source

**Files:**
- Create: `skills-query-server/src/sources/activities.ts`
- Test: `skills-query-server/src/sources/activities.test.ts`

**Step 1: Write the failing test**

Create `skills-query-server/src/sources/activities.test.ts`:

```typescript
import { describe, it, expect, beforeEach, afterEach } from 'vitest';
import { loadActivities, filterActivities } from './activities.js';
import { writeFileSync, mkdirSync, rmSync } from 'fs';
import { join } from 'path';
import { tmpdir } from 'os';

const SAMPLE_ACTIVITY = {
  session_id: 'session_001',
  timestamp: '2026-02-18T10:00:00Z',
  project_path: '/test/project',
  project_name: 'test-project',
  git_branch: 'main',
  git_remote: 'https://github.com/test/repo',
  activities: [
    {
      type: 'task_completed',
      description: 'Added feature X',
      files_changed: ['src/x.ts'],
      commits: ['abc123'],
    },
  ],
  context: 'Implemented feature X with tests',
  tags: ['feature', 'typescript'],
};

describe('loadActivities', () => {
  const testDir = join(tmpdir(), 'skills-query-test-activities');

  beforeEach(() => {
    mkdirSync(testDir, { recursive: true });
    mkdirSync(join(testDir, 'processed'), { recursive: true });
  });

  afterEach(() => {
    rmSync(testDir, { recursive: true, force: true });
  });

  it('loads JSON files from directory', () => {
    writeFileSync(join(testDir, 'a.json'), JSON.stringify(SAMPLE_ACTIVITY));
    const results = loadActivities(testDir);
    expect(results).toHaveLength(1);
    expect(results[0].session_id).toBe('session_001');
  });

  it('includes processed/ subdirectory', () => {
    writeFileSync(join(testDir, 'a.json'), JSON.stringify(SAMPLE_ACTIVITY));
    const archived = { ...SAMPLE_ACTIVITY, session_id: 'session_old', timestamp: '2026-01-01T00:00:00Z' };
    writeFileSync(join(testDir, 'processed', 'b.json'), JSON.stringify(archived));
    const results = loadActivities(testDir);
    expect(results).toHaveLength(2);
  });

  it('skips malformed JSON files', () => {
    writeFileSync(join(testDir, 'good.json'), JSON.stringify(SAMPLE_ACTIVITY));
    writeFileSync(join(testDir, 'bad.json'), 'not json{{{');
    const results = loadActivities(testDir);
    expect(results).toHaveLength(1);
  });

  it('returns empty array for empty directory', () => {
    const results = loadActivities(testDir);
    expect(results).toHaveLength(0);
  });
});

describe('filterActivities', () => {
  const activities = [
    { ...SAMPLE_ACTIVITY, timestamp: '2026-02-18T10:00:00Z', project_name: 'alpha', tags: ['feat'] },
    { ...SAMPLE_ACTIVITY, timestamp: '2026-02-17T10:00:00Z', project_name: 'beta', tags: ['fix'],
      activities: [{ type: 'bug_fixed', description: 'Fixed Y', files_changed: [], commits: [] }] },
  ];

  it('filters by project', () => {
    const result = filterActivities(activities, { project: 'alpha' });
    expect(result).toHaveLength(1);
  });

  it('filters by activity type', () => {
    const result = filterActivities(activities, { type: 'bug_fixed' });
    expect(result).toHaveLength(1);
  });

  it('filters by tag', () => {
    const result = filterActivities(activities, { tag: 'fix' });
    expect(result).toHaveLength(1);
  });

  it('returns all when no filters', () => {
    const result = filterActivities(activities, {});
    expect(result).toHaveLength(2);
  });
});
```

**Step 2: Run test to verify it fails**

```bash
cd skills-query-server && npx vitest run src/sources/activities.test.ts
```

Expected: FAIL — modules not found.

**Step 3: Implement activities source**

Create `skills-query-server/src/sources/activities.ts`:

```typescript
import { readFileSync, readdirSync, existsSync } from 'fs';
import { join } from 'path';
import type { ActivityFile } from '../types.js';

export function loadActivities(basePath: string): ActivityFile[] {
  const results: ActivityFile[] = [];

  const dirs = [basePath];
  const processedDir = join(basePath, 'processed');
  if (existsSync(processedDir)) {
    dirs.push(processedDir);
  }

  for (const dir of dirs) {
    const files = readdirSync(dir).filter((f) => f.endsWith('.json'));
    for (const file of files) {
      try {
        const raw = readFileSync(join(dir, file), 'utf-8');
        const parsed = JSON.parse(raw) as ActivityFile;
        if (parsed.session_id && parsed.timestamp) {
          results.push(parsed);
        }
      } catch {
        // Skip malformed files
      }
    }
  }

  return results.sort(
    (a, b) => new Date(b.timestamp).getTime() - new Date(a.timestamp).getTime()
  );
}

export interface ActivityFilter {
  project?: string;
  type?: string;
  tag?: string;
  since?: Date;
  until?: Date;
}

export function filterActivities(
  activities: ActivityFile[],
  filter: ActivityFilter
): ActivityFile[] {
  return activities.filter((a) => {
    if (filter.project && a.project_name !== filter.project) return false;
    if (filter.type && !a.activities.some((e) => e.type === filter.type)) return false;
    if (filter.tag && !a.tags?.includes(filter.tag)) return false;
    if (filter.since && new Date(a.timestamp) < filter.since) return false;
    if (filter.until && new Date(a.timestamp) > filter.until) return false;
    return true;
  });
}
```

**Step 4: Run test to verify it passes**

```bash
cd skills-query-server && npx vitest run src/sources/activities.test.ts
```

Expected: All tests PASS.

**Step 5: Commit**

```bash
git add skills-query-server/src/sources/activities.ts skills-query-server/src/sources/activities.test.ts
git commit -m "feat(skills-query-server): add activities data source with tests"
```

---

### Task 4: Notes Data Source

**Files:**
- Create: `skills-query-server/src/sources/notes.ts`
- Test: `skills-query-server/src/sources/notes.test.ts`

**Step 1: Write the failing test**

Create `skills-query-server/src/sources/notes.test.ts`:

```typescript
import { describe, it, expect, beforeEach, afterEach } from 'vitest';
import { loadNotes, searchNotes } from './notes.js';
import { writeFileSync, mkdirSync, rmSync } from 'fs';
import { join } from 'path';
import { tmpdir } from 'os';

const SAMPLE_NOTE = `---
tags: [fact-check, AI, PicoClaw]
date: 2026-02-16
source: claude-code
---

# PicoClaw：輕量 AI 助理的真相

## 概述

PicoClaw 是一個開源專案，宣稱是超輕量個人 AI 助理。

## 核心問題

Thin client vs 本地推理的差異。
`;

describe('loadNotes', () => {
  const testDir = join(tmpdir(), 'skills-query-test-notes');

  beforeEach(() => {
    mkdirSync(testDir, { recursive: true });
  });

  afterEach(() => {
    rmSync(testDir, { recursive: true, force: true });
  });

  it('loads markdown files with frontmatter', () => {
    writeFileSync(join(testDir, 'test-note.md'), SAMPLE_NOTE);
    const notes = loadNotes(testDir);
    expect(notes).toHaveLength(1);
    expect(notes[0].title).toBe('PicoClaw：輕量 AI 助理的真相');
    expect(notes[0].date).toBe('2026-02-16');
    expect(notes[0].tags).toContain('fact-check');
    expect(notes[0].source).toBe('claude-code');
  });

  it('extracts summary from 概述 section', () => {
    writeFileSync(join(testDir, 'test-note.md'), SAMPLE_NOTE);
    const notes = loadNotes(testDir);
    expect(notes[0].summary).toContain('PicoClaw 是一個開源專案');
  });

  it('skips non-markdown files', () => {
    writeFileSync(join(testDir, 'test-note.md'), SAMPLE_NOTE);
    writeFileSync(join(testDir, 'debug.log'), 'not a note');
    const notes = loadNotes(testDir);
    expect(notes).toHaveLength(1);
  });

  it('handles notes without frontmatter gracefully', () => {
    writeFileSync(join(testDir, 'plain.md'), '# Just a Title\n\nSome content.');
    const notes = loadNotes(testDir);
    expect(notes).toHaveLength(1);
    expect(notes[0].title).toBe('Just a Title');
    expect(notes[0].tags).toEqual([]);
  });
});

describe('searchNotes', () => {
  const notes = [
    { filename: 'a.md', filepath: '/a.md', date: '2026-02-16', tags: ['AI'], source: 'claude-code', title: 'PicoClaw', content: 'thin client architecture', summary: 'About PicoClaw' },
    { filename: 'b.md', filepath: '/b.md', date: '2026-02-17', tags: ['API'], source: 'claude-code', title: 'API Migration', content: 'scraping to API transition', summary: 'About migration' },
  ];

  it('searches by keyword in content', () => {
    const results = searchNotes(notes, 'thin client');
    expect(results).toHaveLength(1);
    expect(results[0].title).toBe('PicoClaw');
  });

  it('searches by keyword in title', () => {
    const results = searchNotes(notes, 'Migration');
    expect(results).toHaveLength(1);
  });

  it('searches by tag', () => {
    const results = searchNotes(notes, 'API');
    expect(results).toHaveLength(1);
    expect(results[0].title).toBe('API Migration');
  });

  it('is case insensitive', () => {
    const results = searchNotes(notes, 'picoclaw');
    expect(results).toHaveLength(1);
  });
});
```

**Step 2: Run test to verify it fails**

```bash
cd skills-query-server && npx vitest run src/sources/notes.test.ts
```

Expected: FAIL — modules not found.

**Step 3: Implement notes source**

Create `skills-query-server/src/sources/notes.ts`:

```typescript
import { readFileSync, readdirSync } from 'fs';
import { join } from 'path';
import matter from 'gray-matter';
import type { QANote } from '../types.js';

export function loadNotes(basePath: string): QANote[] {
  const files = readdirSync(basePath).filter((f) => f.endsWith('.md'));
  const notes: QANote[] = [];

  for (const file of files) {
    try {
      const filepath = join(basePath, file);
      const raw = readFileSync(filepath, 'utf-8');
      const { data, content } = matter(raw);

      // Extract title from first H1
      const titleMatch = content.match(/^#\s+(.+)$/m);
      const title = titleMatch?.[1] ?? file.replace(/\.md$/, '');

      // Extract summary from 概述 or Overview section
      const summaryMatch = content.match(
        /##\s+(?:概述|Overview)\s*\n+([\s\S]*?)(?=\n##|\n---|\Z)/
      );
      const summary = summaryMatch?.[1]?.trim() ?? '';

      notes.push({
        filename: file,
        filepath,
        date: String(data.date ?? ''),
        tags: Array.isArray(data.tags) ? data.tags.map(String) : [],
        source: String(data.source ?? ''),
        title,
        content,
        summary,
      });
    } catch {
      // Skip unparseable files
    }
  }

  return notes.sort((a, b) => b.date.localeCompare(a.date));
}

export function searchNotes(notes: QANote[], keyword: string): QANote[] {
  const lower = keyword.toLowerCase();
  return notes.filter(
    (n) =>
      n.title.toLowerCase().includes(lower) ||
      n.content.toLowerCase().includes(lower) ||
      n.tags.some((t) => t.toLowerCase().includes(lower))
  );
}
```

**Step 4: Run test to verify it passes**

```bash
cd skills-query-server && npx vitest run src/sources/notes.test.ts
```

Expected: All tests PASS.

**Step 5: Commit**

```bash
git add skills-query-server/src/sources/notes.ts skills-query-server/src/sources/notes.test.ts
git commit -m "feat(skills-query-server): add QA notes data source with tests"
```

---

### Task 5: Utility Modules

**Files:**
- Create: `skills-query-server/src/utils/date-range.ts`
- Create: `skills-query-server/src/utils/text-search.ts`
- Test: `skills-query-server/src/utils/date-range.test.ts`

**Step 1: Write the failing test**

Create `skills-query-server/src/utils/date-range.test.ts`:

```typescript
import { describe, it, expect, vi, afterEach } from 'vitest';
import { parseDateRange } from './date-range.js';

describe('parseDateRange', () => {
  afterEach(() => {
    vi.useRealTimers();
  });

  it('parses "today"', () => {
    vi.useFakeTimers();
    vi.setSystemTime(new Date('2026-02-18T15:00:00Z'));
    const { since, until } = parseDateRange('today');
    expect(since.toISOString()).toContain('2026-02-18');
    expect(until.getTime()).toBeGreaterThan(since.getTime());
  });

  it('parses "this-week"', () => {
    vi.useFakeTimers();
    vi.setSystemTime(new Date('2026-02-18T15:00:00Z')); // Wednesday
    const { since } = parseDateRange('this-week');
    // Monday of this week
    expect(since.getDay()).toBe(1);
  });

  it('parses "this-month"', () => {
    vi.useFakeTimers();
    vi.setSystemTime(new Date('2026-02-18T15:00:00Z'));
    const { since } = parseDateRange('this-month');
    expect(since.getDate()).toBe(1);
    expect(since.getMonth()).toBe(1); // Feb = 1
  });

  it('parses "all" as very wide range', () => {
    const { since } = parseDateRange('all');
    expect(since.getFullYear()).toBeLessThan(2000);
  });

  it('throws on unknown range', () => {
    expect(() => parseDateRange('invalid')).toThrow();
  });
});
```

**Step 2: Run test to verify it fails**

```bash
cd skills-query-server && npx vitest run src/utils/date-range.test.ts
```

Expected: FAIL.

**Step 3: Implement date-range**

Create `skills-query-server/src/utils/date-range.ts`:

```typescript
export interface DateRange {
  since: Date;
  until: Date;
}

export function parseDateRange(range: string): DateRange {
  const now = new Date();
  const startOfDay = new Date(now.getFullYear(), now.getMonth(), now.getDate());
  const endOfDay = new Date(startOfDay.getTime() + 86400000 - 1);

  switch (range) {
    case 'today':
      return { since: startOfDay, until: endOfDay };

    case 'yesterday': {
      const yesterday = new Date(startOfDay.getTime() - 86400000);
      return { since: yesterday, until: startOfDay };
    }

    case 'this-week': {
      const day = now.getDay();
      const diff = day === 0 ? 6 : day - 1; // Monday = start
      const monday = new Date(startOfDay.getTime() - diff * 86400000);
      return { since: monday, until: endOfDay };
    }

    case 'last-week': {
      const day = now.getDay();
      const diff = day === 0 ? 6 : day - 1;
      const thisMonday = new Date(startOfDay.getTime() - diff * 86400000);
      const lastMonday = new Date(thisMonday.getTime() - 7 * 86400000);
      return { since: lastMonday, until: thisMonday };
    }

    case 'this-month': {
      const firstOfMonth = new Date(now.getFullYear(), now.getMonth(), 1);
      return { since: firstOfMonth, until: endOfDay };
    }

    case 'all':
      return { since: new Date(0), until: endOfDay };

    default:
      throw new Error(`Unknown date range: "${range}". Use: today, yesterday, this-week, last-week, this-month, all`);
  }
}
```

**Step 4: Implement text-search**

Create `skills-query-server/src/utils/text-search.ts`:

```typescript
import type { ActivityFile, QANote } from '../types.js';

export interface SearchResult {
  source: 'activity' | 'note';
  date: string;
  title: string;
  snippet: string;
  tags: string[];
}

export function searchActivities(
  activities: ActivityFile[],
  keyword: string
): SearchResult[] {
  const lower = keyword.toLowerCase();
  const results: SearchResult[] = [];

  for (const a of activities) {
    const matches =
      a.context?.toLowerCase().includes(lower) ||
      a.activities.some((e) => e.description.toLowerCase().includes(lower)) ||
      a.tags?.some((t) => t.toLowerCase().includes(lower)) ||
      a.project_name?.toLowerCase().includes(lower);

    if (matches) {
      const desc = a.activities.map((e) => e.description).join('; ');
      results.push({
        source: 'activity',
        date: a.timestamp.slice(0, 10),
        title: `[${a.project_name}] ${desc.slice(0, 80)}`,
        snippet: a.context?.slice(0, 200) ?? desc.slice(0, 200),
        tags: a.tags ?? [],
      });
    }
  }

  return results;
}

export function searchNotesUnified(
  notes: QANote[],
  keyword: string
): SearchResult[] {
  const lower = keyword.toLowerCase();
  return notes
    .filter(
      (n) =>
        n.title.toLowerCase().includes(lower) ||
        n.content.toLowerCase().includes(lower) ||
        n.tags.some((t) => t.toLowerCase().includes(lower))
    )
    .map((n) => ({
      source: 'note' as const,
      date: n.date,
      title: n.title,
      snippet: n.summary.slice(0, 200) || n.content.slice(0, 200),
      tags: n.tags,
    }));
}
```

**Step 5: Run all tests**

```bash
cd skills-query-server && npx vitest run
```

Expected: All tests PASS.

**Step 6: Commit**

```bash
git add skills-query-server/src/utils/
git commit -m "feat(skills-query-server): add date-range and text-search utils"
```

---

### Task 6: Core Query Tools (query-activities, search, log-activity)

**Files:**
- Create: `skills-query-server/src/tools/query-activities.ts`
- Create: `skills-query-server/src/tools/search.ts`
- Create: `skills-query-server/src/tools/log-activity.ts`

**Step 1: Implement query-activities tool**

Create `skills-query-server/src/tools/query-activities.ts`:

```typescript
import { z } from 'zod';
import type { McpServer } from '@modelcontextprotocol/sdk/server/mcp.js';
import type { Config } from '../types.js';
import { loadActivities, filterActivities } from '../sources/activities.js';
import { parseDateRange } from '../utils/date-range.js';

export function registerQueryActivities(server: McpServer, config: Config) {
  server.registerTool(
    'query_activities',
    {
      title: 'Query Activities',
      description:
        'Aggregate and filter work activity records. Supports date ranges, project/type/tag filtering, and grouping.',
      inputSchema: z.object({
        range: z
          .enum(['today', 'yesterday', 'this-week', 'last-week', 'this-month', 'all'])
          .default('this-week')
          .describe('Date range to query'),
        project: z.string().optional().describe('Filter by project name'),
        type: z.string().optional().describe('Filter by activity type (task_completed, bug_fixed, refactoring, research, documentation, review)'),
        tag: z.string().optional().describe('Filter by tag'),
        group_by: z
          .enum(['date', 'project', 'type'])
          .default('date')
          .describe('How to group results'),
      }),
    },
    async ({ range, project, type, tag, group_by }) => {
      const activities = loadActivities(config.sources.activities);
      const { since, until } = parseDateRange(range);
      const filtered = filterActivities(activities, { project, type, tag, since, until });

      if (filtered.length === 0) {
        const latest = activities[0];
        const hint = latest ? ` Most recent record: ${latest.timestamp.slice(0, 10)}` : '';
        return { content: [{ type: 'text', text: `No activities found for range "${range}".${hint}` }] };
      }

      // Group results
      const groups = new Map<string, typeof filtered>();
      for (const a of filtered) {
        let key: string;
        if (group_by === 'date') key = a.timestamp.slice(0, 10);
        else if (group_by === 'project') key = a.project_name;
        else key = a.activities.map((e) => e.type).join(', ');

        const list = groups.get(key) ?? [];
        list.push(a);
        groups.set(key, list);
      }

      // Format output
      const lines: string[] = [`## Activities (${range}, grouped by ${group_by})`, `Total: ${filtered.length} records`, ''];
      for (const [key, items] of groups) {
        lines.push(`### ${key}`);
        for (const item of items) {
          for (const entry of item.activities) {
            lines.push(`- **${entry.type}**: ${entry.description}`);
          }
          if (item.tags?.length) lines.push(`  Tags: ${item.tags.join(', ')}`);
        }
        lines.push('');
      }

      return { content: [{ type: 'text', text: lines.join('\n') }] };
    }
  );
}
```

**Step 2: Implement search tool**

Create `skills-query-server/src/tools/search.ts`:

```typescript
import { z } from 'zod';
import type { McpServer } from '@modelcontextprotocol/sdk/server/mcp.js';
import type { Config } from '../types.js';
import { loadActivities } from '../sources/activities.js';
import { loadNotes } from '../sources/notes.js';
import { searchActivities, searchNotesUnified } from '../utils/text-search.js';

export function registerSearch(server: McpServer, config: Config) {
  server.registerTool(
    'search',
    {
      title: 'Search Work History & Notes',
      description:
        'Cross-source full-text search across activity logs and QA knowledge notes.',
      inputSchema: z.object({
        keyword: z.string().describe('Search keyword or phrase'),
        source: z
          .enum(['activities', 'notes', 'all'])
          .default('all')
          .describe('Which sources to search'),
      }),
    },
    async ({ keyword, source }) => {
      const results = [];

      if (source === 'all' || source === 'activities') {
        const activities = loadActivities(config.sources.activities);
        results.push(...searchActivities(activities, keyword));
      }

      if (source === 'all' || source === 'notes') {
        const notes = loadNotes(config.sources.notes);
        results.push(...searchNotesUnified(notes, keyword));
      }

      // Sort by date descending
      results.sort((a, b) => b.date.localeCompare(a.date));

      if (results.length === 0) {
        return { content: [{ type: 'text', text: `No results found for "${keyword}". Try different keywords or broaden the source.` }] };
      }

      const lines: string[] = [`## Search: "${keyword}" (${results.length} results)`, ''];
      for (const r of results) {
        const icon = r.source === 'activity' ? '📋' : '📝';
        lines.push(`${icon} **${r.title}** (${r.date})`);
        lines.push(`  ${r.snippet}`);
        if (r.tags.length) lines.push(`  Tags: ${r.tags.join(', ')}`);
        lines.push('');
      }

      return { content: [{ type: 'text', text: lines.join('\n') }] };
    }
  );
}
```

**Step 3: Implement log-activity tool**

Create `skills-query-server/src/tools/log-activity.ts`:

```typescript
import { z } from 'zod';
import { writeFileSync } from 'fs';
import { join } from 'path';
import type { McpServer } from '@modelcontextprotocol/sdk/server/mcp.js';
import type { Config, ActivityFile } from '../types.js';

export function registerLogActivity(server: McpServer, config: Config) {
  server.registerTool(
    'log_activity',
    {
      title: 'Log Activity',
      description: 'Record a work activity entry to the activity log.',
      inputSchema: z.object({
        description: z.string().describe('What was done'),
        type: z
          .enum(['task_completed', 'bug_fixed', 'refactoring', 'research', 'documentation', 'review'])
          .describe('Activity type'),
        context: z.string().optional().describe('Additional context'),
        tags: z.array(z.string()).optional().describe('Tags for categorization'),
      }),
    },
    async ({ description, type, context, tags }) => {
      const now = new Date();
      const sessionId = `mcp_${now.toISOString().replace(/[:-]/g, '').slice(0, 15)}`;
      const filename = `${sessionId}_${now.toISOString().replace(/:/g, '')}Z.json`;

      const entry: ActivityFile = {
        session_id: sessionId,
        timestamp: now.toISOString(),
        project_path: process.cwd(),
        project_name: 'mcp-logged',
        git_branch: '',
        git_remote: '',
        activities: [{ type, description, files_changed: [], commits: [] }],
        context: context ?? description,
        tags: tags ?? [],
      };

      const filepath = join(config.sources.activities, filename);
      writeFileSync(filepath, JSON.stringify(entry, null, 2));

      return {
        content: [{ type: 'text', text: `Activity logged: [${type}] ${description}\nSaved to: ${filepath}` }],
      };
    }
  );
}
```

**Step 4: Run all tests**

```bash
cd skills-query-server && npx vitest run
```

Expected: All existing tests PASS.

**Step 5: Commit**

```bash
git add skills-query-server/src/tools/query-activities.ts skills-query-server/src/tools/search.ts skills-query-server/src/tools/log-activity.ts
git commit -m "feat(skills-query-server): add query-activities, search, and log-activity tools"
```

---

### Task 7: Advanced Query Tools (timeline, todos, decisions, dashboard)

**Files:**
- Create: `skills-query-server/src/tools/query-timeline.ts`
- Create: `skills-query-server/src/tools/query-todos.ts`
- Create: `skills-query-server/src/tools/query-decisions.ts`
- Create: `skills-query-server/src/tools/dashboard.ts`

**Step 1: Implement query-timeline**

Create `skills-query-server/src/tools/query-timeline.ts`:

```typescript
import { z } from 'zod';
import type { McpServer } from '@modelcontextprotocol/sdk/server/mcp.js';
import type { Config } from '../types.js';
import { loadActivities } from '../sources/activities.js';
import { loadNotes, searchNotes } from '../sources/notes.js';
import { searchActivities } from '../utils/text-search.js';

export function registerQueryTimeline(server: McpServer, config: Config) {
  server.registerTool(
    'query_timeline',
    {
      title: 'Query Timeline',
      description:
        'Track how a topic evolved over time across activities and notes. Shows chronological entries with milestones.',
      inputSchema: z.object({
        topic: z.string().describe('Topic or keyword to trace over time'),
      }),
    },
    async ({ topic }) => {
      const activities = loadActivities(config.sources.activities);
      const notes = loadNotes(config.sources.notes);

      const activityHits = searchActivities(activities, topic);
      const noteHits = searchNotes(notes, topic).map((n) => ({
        source: 'note' as const,
        date: n.date,
        title: n.title,
        snippet: n.summary.slice(0, 200) || n.content.slice(0, 200),
        tags: n.tags,
      }));

      const all = [...activityHits, ...noteHits].sort((a, b) =>
        a.date.localeCompare(b.date)
      );

      if (all.length === 0) {
        return { content: [{ type: 'text', text: `No timeline entries found for "${topic}".` }] };
      }

      const lines: string[] = [`## Timeline: "${topic}" (${all.length} entries)`, ''];
      for (const entry of all) {
        const icon = entry.source === 'activity' ? '🔨' : '📝';
        lines.push(`**${entry.date}** ${icon} ${entry.title}`);
        lines.push(`  ${entry.snippet}`);
        lines.push('');
      }

      return { content: [{ type: 'text', text: lines.join('\n') }] };
    }
  );
}
```

**Step 2: Implement query-todos**

Create `skills-query-server/src/tools/query-todos.ts`:

```typescript
import { z } from 'zod';
import type { McpServer } from '@modelcontextprotocol/sdk/server/mcp.js';
import type { Config } from '../types.js';
import { loadActivities } from '../sources/activities.js';

export function registerQueryTodos(server: McpServer, config: Config) {
  server.registerTool(
    'query_todos',
    {
      title: 'Query TODOs',
      description: 'Extract TODO items from activity records and contexts.',
      inputSchema: z.object({
        status: z
          .enum(['pending', 'in-progress', 'completed', 'all'])
          .default('all')
          .describe('Filter by TODO status'),
      }),
    },
    async ({ status }) => {
      const activities = loadActivities(config.sources.activities);
      const todoPattern = /(?:TODO|FIXME|HACK|XXX)[\s:]+(.+)/gi;

      const todos: { text: string; date: string; project: string }[] = [];

      for (const a of activities) {
        const text = [a.context, ...a.activities.map((e) => e.description)].join('\n');
        let match;
        while ((match = todoPattern.exec(text)) !== null) {
          todos.push({
            text: match[1].trim(),
            date: a.timestamp.slice(0, 10),
            project: a.project_name,
          });
        }
      }

      if (todos.length === 0) {
        return { content: [{ type: 'text', text: 'No TODO items found in activity records.' }] };
      }

      const lines: string[] = [`## TODOs (${todos.length} items)`, ''];
      for (const t of todos) {
        lines.push(`- [ ] **${t.text}** (${t.project}, ${t.date})`);
      }

      return { content: [{ type: 'text', text: lines.join('\n') }] };
    }
  );
}
```

**Step 3: Implement query-decisions**

Create `skills-query-server/src/tools/query-decisions.ts`:

```typescript
import { z } from 'zod';
import type { McpServer } from '@modelcontextprotocol/sdk/server/mcp.js';
import type { Config } from '../types.js';
import { loadActivities } from '../sources/activities.js';
import { loadNotes, searchNotes } from '../sources/notes.js';
import { searchActivities } from '../utils/text-search.js';

export function registerQueryDecisions(server: McpServer, config: Config) {
  server.registerTool(
    'query_decisions',
    {
      title: 'Query Decisions',
      description:
        'Trace decisions: find when and why something was decided. Searches both activity context and knowledge notes.',
      inputSchema: z.object({
        keyword: z.string().describe('Decision topic to trace (e.g. "chose TypeScript", "switched to Gemini")'),
      }),
    },
    async ({ keyword }) => {
      const activities = loadActivities(config.sources.activities);
      const notes = loadNotes(config.sources.notes);

      // Search for decision-related context
      const decisionTerms = [keyword, `chose ${keyword}`, `decided ${keyword}`, `switched to ${keyword}`, `選擇 ${keyword}`, `決定 ${keyword}`];
      const activityHits = new Set<string>();
      const results: { date: string; source: string; text: string }[] = [];

      for (const term of decisionTerms) {
        for (const hit of searchActivities(activities, term)) {
          const key = `${hit.date}-${hit.title}`;
          if (!activityHits.has(key)) {
            activityHits.add(key);
            results.push({ date: hit.date, source: 'activity', text: `${hit.title}: ${hit.snippet}` });
          }
        }
      }

      const noteHits = searchNotes(notes, keyword);
      for (const n of noteHits) {
        results.push({ date: n.date, source: 'note', text: `${n.title}: ${n.summary || n.content.slice(0, 200)}` });
      }

      results.sort((a, b) => a.date.localeCompare(b.date));

      if (results.length === 0) {
        return { content: [{ type: 'text', text: `No decision records found for "${keyword}".` }] };
      }

      const lines: string[] = [`## Decision Trace: "${keyword}" (${results.length} entries)`, ''];
      for (const r of results) {
        const icon = r.source === 'activity' ? '📋' : '📝';
        lines.push(`**${r.date}** ${icon} ${r.text}`);
        lines.push('');
      }

      return { content: [{ type: 'text', text: lines.join('\n') }] };
    }
  );
}
```

**Step 4: Implement dashboard**

Create `skills-query-server/src/tools/dashboard.ts`:

```typescript
import { z } from 'zod';
import type { McpServer } from '@modelcontextprotocol/sdk/server/mcp.js';
import type { Config } from '../types.js';
import { loadActivities, filterActivities } from '../sources/activities.js';
import { loadNotes } from '../sources/notes.js';
import { parseDateRange } from '../utils/date-range.js';

export function registerDashboard(server: McpServer, config: Config) {
  server.registerTool(
    'dashboard',
    {
      title: 'Work Dashboard',
      description:
        'Overview of recent work: activity count, project distribution, recent notes, pending TODOs. Great for starting a session.',
      inputSchema: z.object({
        range: z
          .enum(['today', 'yesterday', 'this-week', 'last-week', 'this-month', 'all'])
          .default('this-week')
          .describe('Date range'),
      }),
    },
    async ({ range }) => {
      const activities = loadActivities(config.sources.activities);
      const notes = loadNotes(config.sources.notes);
      const { since, until } = parseDateRange(range);
      const filtered = filterActivities(activities, { since, until });

      // Activity stats
      const byProject = new Map<string, number>();
      const byType = new Map<string, number>();
      for (const a of filtered) {
        byProject.set(a.project_name, (byProject.get(a.project_name) ?? 0) + 1);
        for (const e of a.activities) {
          byType.set(e.type, (byType.get(e.type) ?? 0) + 1);
        }
      }

      // Recent notes (within range)
      const sinceStr = since.toISOString().slice(0, 10);
      const recentNotes = notes.filter((n) => n.date >= sinceStr);

      // Format
      const lines: string[] = [
        `## Dashboard (${range})`,
        '',
        `### Activities: ${filtered.length} records`,
        '',
      ];

      if (byProject.size > 0) {
        lines.push('**By Project:**');
        for (const [p, c] of byProject) lines.push(`- ${p}: ${c}`);
        lines.push('');
      }

      if (byType.size > 0) {
        lines.push('**By Type:**');
        for (const [t, c] of byType) lines.push(`- ${t}: ${c}`);
        lines.push('');
      }

      if (recentNotes.length > 0) {
        lines.push(`### Recent Notes: ${recentNotes.length}`);
        for (const n of recentNotes.slice(0, 5)) {
          lines.push(`- **${n.title}** (${n.date}) — ${n.tags.join(', ')}`);
        }
        lines.push('');
      }

      if (filtered.length === 0 && recentNotes.length === 0) {
        lines.push('No activity or notes in this period.');
      }

      return { content: [{ type: 'text', text: lines.join('\n') }] };
    }
  );
}
```

**Step 5: Run all tests**

```bash
cd skills-query-server && npx vitest run
```

Expected: All tests PASS.

**Step 6: Commit**

```bash
git add skills-query-server/src/tools/
git commit -m "feat(skills-query-server): add timeline, todos, decisions, and dashboard tools"
```

---

### Task 8: MCP Server Entry Point + Integration Test

**Files:**
- Create: `skills-query-server/src/index.ts`
- Test: `skills-query-server/src/index.test.ts`

**Step 1: Implement server entry**

Create `skills-query-server/src/index.ts`:

```typescript
import { McpServer } from '@modelcontextprotocol/sdk/server/mcp.js';
import { StdioServerTransport } from '@modelcontextprotocol/sdk/server/stdio.js';
import { resolve, dirname } from 'path';
import { fileURLToPath } from 'url';
import { loadConfig } from './config.js';
import { registerQueryActivities } from './tools/query-activities.js';
import { registerSearch } from './tools/search.js';
import { registerLogActivity } from './tools/log-activity.js';
import { registerQueryTimeline } from './tools/query-timeline.js';
import { registerQueryTodos } from './tools/query-todos.js';
import { registerQueryDecisions } from './tools/query-decisions.js';
import { registerDashboard } from './tools/dashboard.js';

const __dirname = dirname(fileURLToPath(import.meta.url));
const configPath = resolve(__dirname, '..', 'config.json');

const config = loadConfig(configPath);

const server = new McpServer({
  name: 'skills-query',
  version: '0.1.0',
});

// Register all tools
registerQueryActivities(server, config);
registerSearch(server, config);
registerLogActivity(server, config);
registerQueryTimeline(server, config);
registerQueryTodos(server, config);
registerQueryDecisions(server, config);
registerDashboard(server, config);

// Start server
const transport = new StdioServerTransport();
await server.connect(transport);
```

**Step 2: Write integration test**

Create `skills-query-server/src/index.test.ts`:

```typescript
import { describe, it, expect } from 'vitest';
import { loadConfig } from './config.js';
import { loadActivities } from './sources/activities.js';
import { loadNotes } from './sources/notes.js';
import { resolve, dirname } from 'path';
import { fileURLToPath } from 'url';
import { existsSync } from 'fs';

const __dirname = dirname(fileURLToPath(import.meta.url));
const configPath = resolve(__dirname, '..', 'config.json');

describe('integration: real data sources', () => {
  it('loads config from config.json', () => {
    if (!existsSync(configPath)) return; // Skip in CI
    const config = loadConfig(configPath);
    expect(config.sources.activities).toBeTruthy();
    expect(config.sources.notes).toBeTruthy();
  });

  it('reads real activities if available', () => {
    if (!existsSync(configPath)) return;
    const config = loadConfig(configPath);
    if (!existsSync(config.sources.activities)) return;
    const activities = loadActivities(config.sources.activities);
    expect(Array.isArray(activities)).toBe(true);
    // Should have at least some records
    expect(activities.length).toBeGreaterThan(0);
  });

  it('reads real notes if available', () => {
    if (!existsSync(configPath)) return;
    const config = loadConfig(configPath);
    if (!existsSync(config.sources.notes)) return;
    const notes = loadNotes(config.sources.notes);
    expect(Array.isArray(notes)).toBe(true);
    expect(notes.length).toBeGreaterThan(0);
    // Verify QA note structure
    expect(notes[0].title).toBeTruthy();
    expect(notes[0].tags).toBeDefined();
  });
});
```

**Step 3: Run all tests**

```bash
cd skills-query-server && npx vitest run
```

Expected: All tests PASS (integration tests skip gracefully if data not available).

**Step 4: Verify server starts**

```bash
cd skills-query-server && echo '{}' | npx tsx src/index.ts &
sleep 2 && kill %1
```

Expected: No crash. Server starts and waits for stdio input.

**Step 5: Commit**

```bash
git add skills-query-server/src/index.ts skills-query-server/src/index.test.ts
git commit -m "feat(skills-query-server): add MCP server entry point and integration test"
```

---

### Task 9: Claude Code MCP Configuration

**Files:**
- Modify: `~/.claude/settings.json` (or project MCP config)

**Step 1: Add MCP server to Claude Code**

Add to Claude Code's MCP settings (via `claude mcp add` or manual edit):

```bash
claude mcp add skills-query -- npx tsx /Users/tom_wang/.claude/skills/skills-query-server/src/index.ts
```

**Step 2: Verify in Claude Code**

Start a new Claude Code session and try:

```
> what did I do this week?
> search for PicoClaw
> show my dashboard
```

Expected: Claude invokes the appropriate MCP tools and formats the results.

**Step 3: Commit config documentation**

Update `skills-query-server/README.md` with setup instructions and commit.

```bash
git add skills-query-server/README.md
git commit -m "docs(skills-query-server): add setup and usage instructions"
```

---

## Summary

| Task | Description | Est. Steps |
|------|-------------|-----------|
| 1 | Project scaffolding | 7 |
| 2 | Config + types (TDD) | 7 |
| 3 | Activities data source (TDD) | 5 |
| 4 | Notes data source (TDD) | 5 |
| 5 | Utility modules (TDD) | 6 |
| 6 | Core query tools (3 tools) | 5 |
| 7 | Advanced query tools (4 tools) | 6 |
| 8 | Server entry + integration test | 5 |
| 9 | Claude Code MCP config | 3 |
| **Total** | | **49 steps** |

**Dependencies:** Tasks 1→2→3,4 (parallel)→5→6,7 (parallel)→8→9
