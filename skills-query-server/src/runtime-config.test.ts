import { describe, expect, it } from 'vitest';
import { readFileSync, mkdtempSync, writeFileSync, rmSync, mkdirSync, symlinkSync } from 'node:fs';
import { join } from 'node:path';
import { tmpdir } from 'node:os';
import { resolveConfigRoot, resolveActivitiesDir, readWorkJournal } from './runtime-config.js';

const cases = JSON.parse(readFileSync(new URL('../../tests/fixtures/plugin-config-cases.json', import.meta.url), 'utf8'));

describe('shared config contract', () => {
  for (const row of cases) {
    it(row.name, () => {
      const root = resolveConfigRoot(row.env, row.home);
      expect(root).toBe(row.root);
      expect(resolveActivitiesDir(row.env, { sources: { activities: row.settings_activity ?? 'data/activities' } }, root, row.home))
        .toBe(row.activities);
    });
  }

  it('rejects relative config roots', () => {
    expect(() => resolveConfigRoot({ AGENT_SKILLS_CONFIG_DIR: 'relative' }, '/fixture/home')).toThrow();
  });

  it('rejects cache ancestors and symlink aliases for personal settings and activity writes', () => {
    const root = mkdtempSync(join(tmpdir(), 'cache guard '));
    try {
      const cache = join(root, 'cache');
      mkdirSync(join(cache, '.codex-plugin'), { recursive: true });
      writeFileSync(join(cache, '.codex-plugin/plugin.json'), '{}');
      const alias = join(root, 'alias'); symlinkSync(cache, alias, 'dir');
      for (const parent of [cache, alias]) {
        const target = join(parent, 'personal');
        expect(() => resolveConfigRoot({ AGENT_SKILLS_CONFIG_DIR: target }, root)).toThrow(/cache/);
        expect(() => resolveActivitiesDir({}, { sources: { activities: target } }, root, root)).toThrow(/cache/);
      }
    } finally { rmSync(root, { recursive: true, force: true }); }
  });

  it('rejects missing, malformed and empty-note settings', () => {
    const root = mkdtempSync(join(tmpdir(), 'runtime config '));
    try {
      expect(() => readWorkJournal(root)).toThrow();
      for (const body of ['{', '[]', '{"sources":{"activities":"data","notes":{"paths":[]}}}',
        '{"sources":{"activities":"data","notes":{"paths":[""]}}}']) {
        writeFileSync(join(root, 'work-journal.json'), body);
        expect(() => readWorkJournal(root)).toThrow();
      }
    } finally {
      rmSync(root, { recursive: true, force: true });
    }
  });
});
