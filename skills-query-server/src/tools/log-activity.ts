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
        project_name: z.string().default('general').describe('Project name for categorization'),
        project_path: z.string().optional().describe('Project path (defaults to empty)'),
        git_branch: z.string().optional().describe('Current git branch'),
        context: z.string().optional().describe('Additional context'),
        tags: z.array(z.string()).optional().describe('Tags for categorization'),
      }),
    },
    async ({ description, type, project_name, project_path, git_branch, context, tags }) => {
      const now = new Date();
      const sessionId = `mcp_${now.toISOString().replace(/[:-]/g, '').slice(0, 15)}`;
      const filename = `${sessionId}_${now.toISOString().replace(/:/g, '')}.json`;

      const entry: ActivityFile = {
        session_id: sessionId,
        timestamp: now.toISOString(),
        project_path: project_path ?? '',
        project_name,
        git_branch: git_branch ?? '',
        git_remote: '',
        activities: [{ type, description, files_changed: [], commits: [] }],
        context: context ?? description,
        tags: tags ?? [],
      };

      const filepath = join(config.sources.activities, filename);
      writeFileSync(filepath, JSON.stringify(entry, null, 2));

      return {
        content: [{ type: 'text' as const, text: `Activity logged: [${type}] ${description}\nSaved to: ${filepath}` }],
      };
    }
  );
}
