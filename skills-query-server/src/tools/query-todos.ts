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
        todoPattern.lastIndex = 0;
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
        return { content: [{ type: 'text' as const, text: 'No TODO items found in activity records.' }] };
      }

      const lines: string[] = [`## TODOs (${todos.length} items)`, ''];
      for (const t of todos) {
        lines.push(`- [ ] **${t.text}** (${t.project}, ${t.date})`);
      }

      return { content: [{ type: 'text' as const, text: lines.join('\n') }] };
    }
  );
}
