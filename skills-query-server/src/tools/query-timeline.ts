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
        return { content: [{ type: 'text' as const, text: `No timeline entries found for "${topic}".` }] };
      }

      const lines: string[] = [`## Timeline: "${topic}" (${all.length} entries)`, ''];
      for (const entry of all) {
        const icon = entry.source === 'activity' ? '[Work]' : '[Note]';
        lines.push(`**${entry.date}** ${icon} ${entry.title}`);
        lines.push(`  ${entry.snippet}`);
        lines.push('');
      }

      return { content: [{ type: 'text' as const, text: lines.join('\n') }] };
    }
  );
}
