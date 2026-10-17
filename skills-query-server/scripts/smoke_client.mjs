import { Client } from '@modelcontextprotocol/sdk/client/index.js';
import { StdioClientTransport } from '@modelcontextprotocol/sdk/client/stdio.js';
import { randomUUID } from 'node:crypto';
import { spawnSync } from 'node:child_process';
import { fileURLToPath } from 'node:url';
import { resolve, dirname } from 'node:path';

const expectedTools = ['dashboard', 'log_activity', 'query_activities', 'query_decisions',
  'query_timeline', 'query_todos', 'search'];

/**
 * Verify protocol discovery and a real write/read cycle using a disposable server's data.
 * @param {string} command Server executable.
 * @param {string[]} args Server arguments, without shell interpolation.
 * @param {Record<string, string | undefined>} env Server environment.
 * @returns {Promise<{tools: string[], roundTrip: boolean, fixtureIsolation?: object}>}
 */
export async function runSmoke(command, args, env) {
  const client = new Client({ name: 'skill-plugins-smoke', version: '0.1.0' });
  const transport = new StdioClientTransport({ command, args,
    env: Object.fromEntries(Object.entries(env).filter(([, value]) => typeof value === 'string')),
    stderr: 'pipe' });
  try {
    await client.connect(transport, { timeout: 10000 });
    const listed = await client.listTools({}, { timeout: 10000 });
    const tools = listed.tools.map(tool => tool.name).sort();
    if (expectedTools.some(name => !tools.includes(name))) {
      throw new Error(`Server is missing required tools: ${expectedTools.filter(n => !tools.includes(n)).join(', ')}`);
    }
    let fixtureIsolation;
    if (tools.includes('probe_identity')) {
      const identity = await client.callTool({ name: 'probe_identity', arguments: {} },
        undefined, { timeout: 10000 });
      fixtureIsolation = JSON.parse(identity.content.find(item => item.type === 'text')?.text ?? '{}');
      if (identity.isError || fixtureIsolation.isolated !== true || !fixtureIsolation.probe_id
          || !fixtureIsolation.activities_dir || !['claude-cli', 'codex-cli'].includes(fixtureIsolation.surface)) {
        throw new Error('Probe fixture identity is not verified; refusing data access');
      }
    }
    const description = `skill-plugins-smoke-${randomUUID()}`;
    const written = await client.callTool({ name: 'log_activity', arguments: {
      description, type: 'documentation', project_name: 'runtime-probe', tags: ['smoke'],
    } }, undefined, { timeout: 10000 });
    if (written.isError) throw new Error('MCP activity write failed');
    const queried = await client.callTool({ name: 'query_activities', arguments: { range: 'all' } },
      undefined, { timeout: 10000 });
    const text = queried.content.filter(item => item.type === 'text').map(item => item.text).join('\n');
    if (queried.isError || !text.includes(description)) throw new Error('MCP written activity was not returned by query');
    return { tools, roundTrip: true, ...(fixtureIsolation ? { fixtureIsolation } : {}) };
  } finally {
    await client.close();
  }
}

async function main(args) {
  if (args[0] === '--contract' && args.length === 2) {
    const checker = resolve(dirname(fileURLToPath(import.meta.url)), '../../scripts/probe_plugin_runtimes.py');
    const result = spawnSync('python3', [checker, 'check-contract', resolve(args[1])], { stdio: 'inherit' });
    if (result.error) throw result.error;
    process.exitCode = result.status ?? 1;
    return;
  }
  if (args[0] !== '--' || args.length < 2) {
    throw new Error('Usage: smoke_client.mjs -- <server-command> [args...] | --contract <file>');
  }
  console.log(JSON.stringify(await runSmoke(args[1], args.slice(2), process.env)));
}

if (process.argv[1] && resolve(process.argv[1]) === fileURLToPath(import.meta.url)) {
  main(process.argv.slice(2)).catch(error => {
    console.error(`Smoke failed: ${error.message}`);
    process.exitCode = 1;
  });
}
