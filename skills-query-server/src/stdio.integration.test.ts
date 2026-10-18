/** Exercise the compiled server and shell logger using only disposable shared data. */
import { afterEach, describe, expect, it } from 'vitest';
import { cpSync, existsSync, mkdtempSync, mkdirSync, writeFileSync, rmSync, symlinkSync, realpathSync, chmodSync } from 'node:fs';
import { join, resolve } from 'node:path';
import { tmpdir } from 'node:os';
import { spawnSync } from 'node:child_process';
import { Client } from '@modelcontextprotocol/sdk/client/index.js';
import { StdioClientTransport } from '@modelcontextprotocol/sdk/client/stdio.js';
import { runSmoke } from '../scripts/smoke_client.mjs';

const repo = resolve(import.meta.dirname, '../..');
const serverRoot = join(repo, 'skills-query-server');
const fixtures: string[] = [];
afterEach(() => { for (const root of fixtures.splice(0)) rmSync(root, { recursive: true, force: true }); });

function fixture(override = false, bundle?: string) {
  const root = realpathSync(mkdtempSync(join(tmpdir(), 'shared journal 中文 ')));
  fixtures.push(root);
  const settings = join(root, 'personal settings');
  const server = join(root, 'server bundle');
  const cwd = join(root, 'unrelated cwd');
  for (const path of [settings, server, cwd, join(settings, 'journal'), join(settings, 'notes'), join(settings, 'override')]) mkdirSync(path);
  if (bundle) {
    // A generated plugin bundle must run on its own production dependencies.
    cpSync(bundle, server, { recursive: true });
  } else {
    cpSync(join(serverRoot, 'dist'), join(server, 'dist'), { recursive: true });
    symlinkSync(join(serverRoot, 'node_modules'), join(server, 'node_modules'), 'dir');
    writeFileSync(join(server, 'package.json'), '{"type":"module"}');
  }
  writeFileSync(join(settings, 'work-journal.json'), JSON.stringify({ sources: {
    activities: 'journal', notes: { paths: ['notes'] },
  } }));
  const env: Record<string, string> = Object.fromEntries(Object.entries(process.env).filter((entry): entry is [string, string] => entry[1] !== undefined));
  delete env.CLAUDE_ACTIVITIES_DIR;
  env.AGENT_SKILLS_CONFIG_DIR = settings;
  env.CLAUDE_SESSION_ID = 'shared-fixture';
  const bin = join(root, 'guard bin');
  mkdirSync(bin);
  cpSync(join(repo, 'tests/fixtures/guarded_mkdir.py'), join(bin, 'mkdir'));
  chmodSync(join(bin, 'mkdir'), 0o755);
  env.GUARDED_FIXTURE_ROOT = root;
  env.GUARDED_REAL_MKDIR = spawnSync('/bin/sh', ['-c', 'command -v mkdir'], { encoding: 'utf8' }).stdout.trim();
  env.PATH = `${bin}:${env.PATH}`;
  if (override) env.CLAUDE_ACTIVITIES_DIR = 'override';
  return { root, settings, server, cwd, env, entry: join(server, bundle ? 'launch.mjs' : 'dist/index.js'),
    activities: join(settings, override ? 'override' : 'journal') };
}

describe('production stdio shared configuration', () => {
  it('starts with only external shared settings and performs a real round trip', async () => {
    const f = fixture();
    const result = await runSmoke(process.execPath, [f.entry], f.env);
    expect(result.tools).toContain('log_activity');
    expect(result.tools).toContain('query_activities');
    expect(result.roundTrip).toBe(true);
  }, 15000);

  for (const surface of ['claude', 'codex']) {
    it(`the generated ${surface} work-journal bundle runs on its own production dependencies`, async () => {
      const f = fixture(false, join(repo, 'plugins', surface, 'work-journal/server'));
      expect(existsSync(join(f.server, 'node_modules/.package-lock.json'))).toBe(false);
      expect(existsSync(join(f.server, 'node_modules/vitest'))).toBe(false);
      const result = await runSmoke(process.execPath, [f.entry], f.env);
      expect(result.tools).toContain('log_activity');
      expect(result.roundTrip).toBe(true);
    }, 20000);
  }

  for (const override of [false, true]) {
    it(`finds the actual shell logger record using ${override ? 'an environment override' : 'shared relative paths'}`, async () => {
      const f = fixture(override);
      const marker = `shell-shared-${override}-${Date.now()}`;
      const logged = spawnSync('bash', [join(repo, 'activity-logger/scripts/log_activity.sh'), '-d', marker, '-t', 'documentation'],
        { cwd: f.cwd, env: f.env, encoding: 'utf8', timeout: 10000 });
      expect(logged.status, logged.stderr + logged.stdout).toBe(0);
      expect(logged.stdout).toContain(f.activities);
      const client = new Client({ name: 'shared-config-fixture', version: '1.0.0' });
      try {
        await client.connect(new StdioClientTransport({ command: process.execPath, args: [f.entry], env: f.env, cwd: f.cwd }));
        const result = await client.callTool({ name: 'query_activities', arguments: { range: 'all' } });
        expect(result.isError).not.toBe(true);
        expect(JSON.stringify(result)).toContain(marker);
      } finally { await client.close(); }
    }, 15000);
  }

  it('rejects missing and malformed shared settings without a private-config fallback', () => {
    const f = fixture();
    // Even a valid private decoy must not silently replace missing shared settings.
    writeFileSync(join(f.server, 'config.json'), JSON.stringify({ sources: {
      activities: f.activities, notes: { paths: [join(f.settings, 'notes')] },
    } }));
    const path = join(f.settings, 'work-journal.json');
    rmSync(path);
    let result = spawnSync(process.execPath, [f.entry], { cwd: f.cwd, env: f.env, encoding: 'utf8', timeout: 5000 });
    expect(result.status).toBe(1);
    expect(result.stderr).toMatch(/work-journal.json/);
    expect(result.stdout).toBe('');
    writeFileSync(path, '{"sources":{"activities":"journal","notes":{"paths":[]}}}');
    result = spawnSync(process.execPath, [f.entry], { cwd: f.cwd, env: f.env, encoding: 'utf8', timeout: 5000 });
    expect(result.status).toBe(1);
    expect(result.stderr).toMatch(/notes.paths/);
  });

  it.skipIf(process.getuid?.() === 0)('reports a non-writable selected activity directory before starting', () => {
    const f = fixture();
    for (const mode of [0o555, 0o666]) {
      chmodSync(f.activities, mode);
      try {
        const result = spawnSync(process.execPath, [f.entry], { cwd: f.cwd, env: f.env, encoding: 'utf8', timeout: 5000 });
        expect(result.status).toBe(1);
        expect(result.stderr).toMatch(/activity directory.*writ|writ.*activity directory/i);
      } finally { chmodSync(f.activities, 0o755); }
    }
  });
});
