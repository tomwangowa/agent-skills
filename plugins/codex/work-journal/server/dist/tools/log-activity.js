import { z } from 'zod';
import { writeFileSync } from 'fs';
import { join } from 'path';
/**
 * The session a record belongs to, in the order `activity-logger/scripts/log_activity.sh` uses:
 * an explicit `CLAUDE_SESSION_ID`, then the host session in the server's environment (Claude
 * Code starts its MCP servers with `CLAUDE_CODE_SESSION_ID`; Codex passes `CODEX_THREAD_ID` to
 * shell commands, not to MCP servers), else an `mcp_` id of this record's time.
 */
export function activitySessionId(env, now) {
    return (env.CLAUDE_SESSION_ID ||
        env.CLAUDE_CODE_SESSION_ID ||
        env.CODEX_THREAD_ID ||
        `mcp_${now.toISOString().replace(/[:-]/g, '').slice(0, 15)}`);
}
export function registerLogActivity(server, config) {
    server.registerTool('log_activity', {
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
    }, async ({ description, type, project_name, project_path, git_branch, context, tags }) => {
        const now = new Date();
        const sessionId = activitySessionId(process.env, now);
        const filename = `${sessionId}_${now.toISOString().replace(/:/g, '')}.json`;
        const entry = {
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
            content: [{ type: 'text', text: `Activity logged: [${type}] ${description}\nSaved to: ${filepath}` }],
        };
    });
}
