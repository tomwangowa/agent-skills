import { describe, it, expect, beforeEach, afterEach } from 'vitest';
import { loadConfig } from './config.js';
import { writeFileSync, mkdirSync, rmSync } from 'fs';
import { join } from 'path';
import { tmpdir } from 'os';

describe('loadConfig', () => {
  const testDir = join(tmpdir(), 'skills-query-test-config');

  beforeEach(() => {
    mkdirSync(testDir, { recursive: true });
  });

  afterEach(() => {
    rmSync(testDir, { recursive: true, force: true });
  });

  it('loads valid config file', () => {
    const configPath = join(testDir, 'config.json');
    writeFileSync(configPath, JSON.stringify({
      sources: {
        activities: '/tmp/activities',
        notes: '/tmp/notes'
      }
    }));
    const config = loadConfig(configPath);
    expect(config.sources.activities).toBe('/tmp/activities');
    expect(config.sources.notes).toBe('/tmp/notes');
  });

  it('expands ~ in paths', () => {
    const configPath = join(testDir, 'config.json');
    writeFileSync(configPath, JSON.stringify({
      sources: {
        activities: '~/.claude/activities',
        notes: '~/notes'
      }
    }));
    const config = loadConfig(configPath);
    expect(config.sources.activities).not.toContain('~');
    expect(config.sources.activities).toContain('.claude/activities');
  });

  it('throws on missing config file', () => {
    expect(() => loadConfig('/nonexistent/config.json'))
      .toThrow('Config file not found');
  });

  it('throws on missing sources field', () => {
    const configPath = join(testDir, 'config.json');
    writeFileSync(configPath, JSON.stringify({}));
    expect(() => loadConfig(configPath)).toThrow();
  });
});
