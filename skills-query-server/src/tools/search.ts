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
        return { content: [{ type: 'text' as const, text: `No results found for "${keyword}". Try different keywords or broaden the source.` }] };
      }

      const lines: string[] = [`## Search: "${keyword}" (${results.length} results)`, ''];
      for (const r of results) {
        const icon = r.source === 'activity' ? '[Activity]' : '[Note]';
        lines.push(`${icon} **${r.title}** (${r.date})`);
        lines.push(`  ${r.snippet}`);
        if (r.tags.length) lines.push(`  Tags: ${r.tags.join(', ')}`);
        lines.push('');
      }

      return { content: [{ type: 'text' as const, text: lines.join('\n') }] };
    }
  );
}
