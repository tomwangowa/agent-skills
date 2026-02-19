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

      return { content: [{ type: 'text' as const, text: lines.join('\n') }] };
    }
  );
}
