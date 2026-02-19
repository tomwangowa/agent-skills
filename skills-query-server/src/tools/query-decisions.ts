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

      const decisionTerms = [keyword, `chose ${keyword}`, `decided ${keyword}`, `switched to ${keyword}`];
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
        return { content: [{ type: 'text' as const, text: `No decision records found for "${keyword}".` }] };
      }

      const lines: string[] = [`## Decision Trace: "${keyword}" (${results.length} entries)`, ''];
      for (const r of results) {
        const icon = r.source === 'activity' ? '[Activity]' : '[Note]';
        lines.push(`**${r.date}** ${icon} ${r.text}`);
        lines.push('');
      }

      return { content: [{ type: 'text' as const, text: lines.join('\n') }] };
    }
  );
}
