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
        return { content: [{ type: 'text' as const, text: `No activities found for range "${range}".${hint}` }] };
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

      return { content: [{ type: 'text' as const, text: lines.join('\n') }] };
    }
  );
}
