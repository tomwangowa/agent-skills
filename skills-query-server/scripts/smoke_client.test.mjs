import assert from 'node:assert/strict';
import { cp, mkdir, mkdtemp, readFile, rm, symlink, writeFile } from 'node:fs/promises';
import { existsSync } from 'node:fs';
import { tmpdir } from 'node:os';
import { dirname, join } from 'node:path';
import { fileURLToPath } from 'node:url';
import { spawnSync } from 'node:child_process';
import test from 'node:test';

const root = join(dirname(fileURLToPath(import.meta.url)), '..');
const implementation = join(root, 'scripts', 'smoke_client.mjs');

async function loadClient() {
  assert.ok(existsSync(implementation), 'Real MCP smoke client is missing');
  return import(implementation);
}

test('real stdio client discovers tools and reads back its written activity', async () => {
  const { runSmoke } = await loadClient();
  const directory = await mkdtemp(join(tmpdir(), 'mcp smoke 中文 '));
  try {
    await cp(join(root, 'dist'), join(directory, 'dist'), { recursive: true });
    await symlink(join(root, 'node_modules'), join(directory, 'node_modules'), 'dir');
    await mkdir(join(directory, 'activities'));
    await mkdir(join(directory, 'notes'));
    await writeFile(join(directory, 'package.json'), '{"type":"module"}');
    await writeFile(join(directory, 'config.json'), JSON.stringify({
      sources: {
        activities: join(directory, 'activities'),
        notes: { paths: [join(directory, 'notes')], recursive: true, exclude_hidden: true },
      },
    }));
    const result = await runSmoke(process.execPath,
      [join(directory, 'dist', 'index.js'), '--config', join(directory, 'config.json')], process.env);
    assert.deepEqual(result.tools, ['dashboard', 'log_activity', 'query_activities', 'query_decisions',
      'query_timeline', 'query_todos', 'search']);
    assert.equal(result.roundTrip, true);
    const { readdir } = await import('node:fs/promises');
    const records = (await readdir(join(directory, 'activities'))).filter(name => name.endsWith('.json'));
    assert.equal(records.length, 1);
    const record = JSON.parse(await readFile(join(directory, 'activities', records[0]), 'utf8'));
    assert.equal(record.activities[0].type, 'documentation');
    assert.match(record.activities[0].description, /^skill-plugins-smoke-/);
  } finally {
    await rm(directory, { recursive: true, force: true });
  }
});

test('server startup failure is reported instead of a successful smoke result', async () => {
  const { runSmoke } = await loadClient();
  await assert.rejects(runSmoke(process.execPath, ['-e', 'process.exit(5)'], process.env));
});

test('importing the smoke module does not start a server or emit protocol output', async () => {
  await loadClient();
  const child = spawnSync(process.execPath, ['--input-type=module', '-e',
    `await import(${JSON.stringify(implementation)});`], { encoding: 'utf8', timeout: 5000 });
  assert.equal(child.status, 0);
  assert.equal(child.stdout, '');
  assert.equal(child.stderr, '');
});

test('contract mode cannot mark an unverified surface as passing', async () => {
  await loadClient();
  const directory = await mkdtemp(join(tmpdir(), 'smoke contract '));
  try {
    const contract = join(directory, 'contract.json');
    await writeFile(contract, JSON.stringify({ schema_version: 1, surfaces: {
      'codex-cli': { status: 'not_verified' },
    } }));
    const child = spawnSync(process.execPath, [implementation, '--contract', contract],
      { encoding: 'utf8', timeout: 5000 });
    assert.notEqual(child.status, 0);
    assert.match(child.stderr, /not_verified|not verified|incomplete/i);
  } finally {
    await rm(directory, { recursive: true, force: true });
  }
});
