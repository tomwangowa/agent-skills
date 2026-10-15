import { McpServer } from '@modelcontextprotocol/sdk/server/mcp.js';
import { StdioServerTransport } from '@modelcontextprotocol/sdk/server/stdio.js';
import { homedir } from 'os';
import { loadConfig, loadRuntimeConfig } from './config.js';
import { registerQueryActivities } from './tools/query-activities.js';
import { registerSearch } from './tools/search.js';
import { registerLogActivity } from './tools/log-activity.js';
import { registerQueryTimeline } from './tools/query-timeline.js';
import { registerQueryTodos } from './tools/query-todos.js';
import { registerQueryDecisions } from './tools/query-decisions.js';
import { registerDashboard } from './tools/dashboard.js';
// Development fixtures can select a config explicitly; normal hosts share user settings.
let config;
try {
    if (process.argv.length > 2 && (process.argv[2] !== '--config' || process.argv.length !== 4)) {
        throw new Error('Usage: index.js [--config <development-config.json>]');
    }
    config = process.argv[2] === '--config'
        ? loadConfig(process.argv[3]) : loadRuntimeConfig(process.env, homedir());
}
catch (error) {
    console.error(`skills-query startup failed: ${String(error)}`);
    process.exit(1);
}
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
