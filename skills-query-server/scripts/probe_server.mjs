// Probe-only entry point: use production handlers, but refuse unverified data access.
import { McpServer } from '@modelcontextprotocol/sdk/server/mcp.js';
import { StdioServerTransport } from '@modelcontextprotocol/sdk/server/stdio.js';
import { readFileSync, realpathSync } from 'node:fs';
import { createHash } from 'node:crypto';
import { dirname, join } from 'node:path';
import { fileURLToPath } from 'node:url';

const directory = realpathSync(dirname(fileURLToPath(import.meta.url)));
const root = realpathSync(join(directory, '..'));
process.chdir(directory);
const identity = JSON.parse(readFileSync(join(directory, 'probe-identity.json'), 'utf8'));
if (!['claude-cli', 'codex-cli'].includes(identity.surface)
    || typeof identity.probe_id !== 'string' || !identity.probe_id
    || typeof identity.plugin !== 'string' || !identity.plugin) {
  throw new Error('Invalid disposable probe identity');
}
const { loadConfig } = await import('./dist/config.js');
const config = loadConfig(join(directory, 'config.json'));
const expectedActivities = join(root, 'data/activities');
const expectedNotes = join(root, 'data/notes');

function assertFixture() {
  // Recheck real paths before every access so a later symlink cannot redirect a write.
  if (config.sources.activities !== expectedActivities
      || realpathSync(config.sources.activities) !== expectedActivities
      || config.sources.notes.paths.length !== 1
      || config.sources.notes.paths[0] !== expectedNotes
      || realpathSync(expectedNotes) !== expectedNotes) {
    throw new Error('Probe isolation failed: data paths must stay in the disposable fixture');
  }
}
assertFixture();
let identified = false;
const server = new McpServer({ name: identity.plugin, version: '0.0.3' });
const register = server.registerTool.bind(server);
server.registerTool = (name, options, handler) => register(name, options, async (...args) => {
  assertFixture();
  if (!identified) throw new Error('Call probe_identity and verify the fixture before data tools');
  return handler(...args);
});
for (const [file, functionName] of [
  ['query-activities', 'registerQueryActivities'], ['search', 'registerSearch'],
  ['log-activity', 'registerLogActivity'], ['query-timeline', 'registerQueryTimeline'],
  ['query-todos', 'registerQueryTodos'], ['query-decisions', 'registerQueryDecisions'],
  ['dashboard', 'registerDashboard'],
]) {
  const module = await import(`./dist/tools/${file}.js`);
  module[functionName](server, config);
}
register('probe_identity', {
  description: 'Read only: identify the disposable fixture before calling any activity tools.',
  inputSchema: {},
}, async () => {
  assertFixture();
  identified = true;
  return { content: [{ type: 'text', text: JSON.stringify({
    ...identity, isolated: true, activities_dir: expectedActivities,
    notes_dirs: [expectedNotes], plugin_root: root,
    config_sha256: createHash('sha256').update(readFileSync(join(directory, 'config.json'))).digest('hex'),
  }) }] };
});
await server.connect(new StdioServerTransport());
