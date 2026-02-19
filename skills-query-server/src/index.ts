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
