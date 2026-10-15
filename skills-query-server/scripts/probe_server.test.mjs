import assert from 'node:assert/strict';
import { cp, mkdir, mkdtemp, readFile, readdir, realpath, rm, symlink, writeFile } from 'node:fs/promises';
import { existsSync } from 'node:fs';
import { tmpdir } from 'node:os';
import { dirname, join } from 'node:path';
import { fileURLToPath } from 'node:url';
import test from 'node:test';
import { Client } from '@modelcontextprotocol/sdk/client/index.js';
import { StdioClientTransport } from '@modelcontextprotocol/sdk/client/stdio.js';

const source = join(dirname(fileURLToPath(import.meta.url)), '..');
const implementation = join(source, 'scripts/probe_server.mjs');

async function fixture() {
  assert.ok(existsSync(implementation), 'Guarded probe server is missing');
  const root = await realpath(await mkdtemp(join(tmpdir(), 'guarded probe 中文 ')));
  const server = join(root, 'server');
  await mkdir(server);
  await cp(join(source, 'dist'), join(server, 'dist'), { recursive: true });
  await cp(implementation, join(server, 'probe_server.mjs'));
  await symlink(join(source, 'node_modules'), join(server, 'node_modules'), 'dir');
  await writeFile(join(server, 'package.json'), '{"type":"module"}');
  await mkdir(join(root, 'data/activities'), { recursive: true });
  await mkdir(join(root, 'data/notes'), { recursive: true });
  await writeFile(join(server, 'config.json'), JSON.stringify({ sources: {
    activities: '../data/activities', notes: { paths: ['../data/notes'] },
  } }));
  await writeFile(join(server, 'probe-identity.json'), JSON.stringify({
    surface: 'codex-cli', probe_id: 'controlled-test-id', plugin: 'controlled-test-plugin',
  }));
  return { root, server };
}

async function connect(server) {
  const client = new Client({ name: 'probe-regression', version: '0.1.0' });
  const transport = new StdioClientTransport({ command: process.execPath,
    args: [join(server, 'probe_server.mjs')], stderr: 'pipe' });
  try {
    await client.connect(transport, { timeout: 5000 });
    return client;
  } catch (error) {
    await client.close();
    throw error;
  }
}

test('data tools refuse calls until fixture identity is checked, then round trip uses only fixture', async () => {
  const { root, server } = await fixture();
  let client;
  try {
    client = await connect(server);
    for (const name of ['log_activity', 'query_activities']) {
      const arguments_ = name === 'log_activity'
        ? { description: 'must-not-write', type: 'documentation' } : { range: 'all' };
      const result = await client.callTool({ name, arguments: arguments_ });
      assert.equal(result.isError, true);
    }
    assert.deepEqual(await readdir(join(root, 'data/activities')), []);
    const identity = await client.callTool({ name: 'probe_identity', arguments: {} });
    const info = JSON.parse(identity.content[0].text);
    assert.equal(info.surface, 'codex-cli');
    assert.equal(info.probe_id, 'controlled-test-id');
    assert.equal(info.isolated, true);
    assert.equal(info.activities_dir, join(root, 'data/activities'));
    const written = await client.callTool({ name: 'log_activity', arguments: {
      description: 'guarded-round-trip', type: 'documentation',
    } });
    assert.ok(!written.isError);
    assert.ok(written.content[0].text.includes(join(root, 'data/activities')));
    const queried = await client.callTool({ name: 'query_activities', arguments: { range: 'all' } });
    assert.ok(!queried.isError && queried.content[0].text.includes('guarded-round-trip'));
    assert.equal((await readdir(join(root, 'data/activities'))).length, 1);
  } finally {
    if (client) await client.close();
    await rm(root, { recursive: true, force: true });
  }
});

test('smoke client checks guarded fixture identity before writing', async () => {
  const { root, server } = await fixture();
  try {
    const { runSmoke } = await import('./smoke_client.mjs');
    const result = await runSmoke(process.execPath, [join(server, 'probe_server.mjs')], process.env);
    assert.equal(result.roundTrip, true);
    assert.equal(result.fixtureIsolation.probe_id, 'controlled-test-id');
    assert.equal(result.fixtureIsolation.activities_dir, join(root, 'data/activities'));
  } finally {
    await rm(root, { recursive: true, force: true });
  }
});

test('a config pointing outside the disposable fixture cannot start', async () => {
  const { root, server } = await fixture();
  const external = await mkdtemp(join(tmpdir(), 'external journal '));
  try {
    await writeFile(join(external, 'canary.txt'), 'private fixture canary');
    await writeFile(join(server, 'config.json'), JSON.stringify({ sources: {
      activities: external, notes: { paths: ['../data/notes'] },
    } }));
    await assert.rejects(connect(server));
    assert.deepEqual(await readdir(external), ['canary.txt']);
  } finally {
    await rm(root, { recursive: true, force: true });
    await rm(external, { recursive: true, force: true });
  }
});

test('swapping a data directory for an external symlink after identity blocks writing', async () => {
  const { root, server } = await fixture();
  const external = await mkdtemp(join(tmpdir(), 'external journal '));
  let client;
  try {
    client = await connect(server);
    await client.callTool({ name: 'probe_identity', arguments: {} });
    await rm(join(root, 'data/activities'), { recursive: true });
    await symlink(external, join(root, 'data/activities'), 'dir');
    const result = await client.callTool({ name: 'log_activity', arguments: {
      description: 'must-not-write', type: 'documentation',
    } });
    assert.equal(result.isError, true);
    assert.deepEqual(await readdir(external), []);
  } finally {
    if (client) await client.close();
    await rm(root, { recursive: true, force: true });
    await rm(external, { recursive: true, force: true });
  }
});
