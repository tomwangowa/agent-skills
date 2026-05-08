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

  const NEW_SHAPE = {
    sources: {
      activities: '/tmp/activities',
      notes: {
        paths: ['/tmp/notes', '/tmp/notes2'],
        recursive: true,
        exclude_hidden: true,
      },
    },
  };

  it('loads valid config (new shape)', () => {
    const configPath = join(testDir, 'config.json');
    writeFileSync(configPath, JSON.stringify(NEW_SHAPE));
    const config = loadConfig(configPath);
    expect(config.sources.activities).toBe('/tmp/activities');
    expect(config.sources.notes.paths).toEqual(['/tmp/notes', '/tmp/notes2']);
    expect(config.sources.notes.recursive).toBe(true);
    expect(config.sources.notes.exclude_hidden).toBe(true);
  });

  it('expands ~ in all paths', () => {
    const configPath = join(testDir, 'config.json');
    writeFileSync(configPath, JSON.stringify({
      sources: {
        activities: '~/.claude/activities',
        notes: { paths: ['~/notes', '~/other'], recursive: false, exclude_hidden: true },
      },
    }));
    const config = loadConfig(configPath);
    expect(config.sources.activities).not.toContain('~');
    config.sources.notes.paths.forEach(p => expect(p).not.toContain('~'));
  });

  it('throws on missing config file', () => {
    expect(() => loadConfig('/nonexistent/config.json'))
      .toThrow('Config file not found');
  });

  it('throws on missing notes.paths', () => {
    const configPath = join(testDir, 'config.json');
    writeFileSync(configPath, JSON.stringify({
      sources: { activities: '/tmp/a', notes: { recursive: true } },
    }));
    expect(() => loadConfig(configPath)).toThrow();
  });

  it('defaults recursive=true and exclude_hidden=true if omitted', () => {
    const configPath = join(testDir, 'config.json');
    writeFileSync(configPath, JSON.stringify({
      sources: { activities: '/tmp/a', notes: { paths: ['/tmp/n'] } },
    }));
    const config = loadConfig(configPath);
    expect(config.sources.notes.recursive).toBe(true);
    expect(config.sources.notes.exclude_hidden).toBe(true);
  });
});
