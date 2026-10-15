import { describe, it, expect, beforeEach, afterEach } from 'vitest';
import { loadRuntimeConfig } from './config.js';
import { loadActivities } from './sources/activities.js';
import { loadNotes } from './sources/notes.js';
import { mkdtempSync, mkdirSync, writeFileSync, rmSync } from 'node:fs';
import { tmpdir } from 'node:os';
import { join } from 'node:path';

describe('integration: disposable external data sources', () => {
  let root: string;
  beforeEach(() => {
    root = mkdtempSync(join(tmpdir(), 'skills-query-source-fixture '));
    mkdirSync(join(root, 'journal'));
    mkdirSync(join(root, 'notes'));
    writeFileSync(join(root, 'work-journal.json'), JSON.stringify({ sources: {
      activities: 'journal', notes: { paths: ['notes'] },
    } }));
  });
  afterEach(() => rmSync(root, { recursive: true, force: true }));

  it('resolves external sources independently of launch cwd', () => {
    const config = loadRuntimeConfig({ AGENT_SKILLS_CONFIG_DIR: root }, '/fixture/home');
    expect(config.sources.activities).toBe(join(root, 'journal'));
    expect(config.sources.notes.paths).toEqual([join(root, 'notes')]);
  });

  it('reads a known activity from the selected fixture directory', () => {
    writeFileSync(join(root, 'journal/fixture.json'), JSON.stringify({
      session_id: 'fixture', timestamp: '2026-10-14T12:00:00Z', project_name: 'fixture',
      project_path: '/fixture', git_branch: 'fixture', git_remote: '', context: '', tags: [],
      activities: [{ type: 'documentation', description: 'Known fixture activity', files_changed: [], commits: [] }],
    }));
    const config = loadRuntimeConfig({ AGENT_SKILLS_CONFIG_DIR: root }, '/fixture/home');
    const activities = loadActivities(config.sources.activities);
    expect(activities).toHaveLength(1);
    expect(activities[0].activities[0].description).toBe('Known fixture activity');
  });

  it('reads a known note without accessing private user sources', () => {
    writeFileSync(join(root, 'notes/fixture.md'), '---\ntitle: Fixture note\ntags: [fixture]\n---\n\n# Fixture note\n\nKnown fixture body.\n');
    const config = loadRuntimeConfig({ AGENT_SKILLS_CONFIG_DIR: root }, '/fixture/home');
    const notes = loadNotes(config.sources.notes);
    expect(notes).toHaveLength(1);
    expect(notes[0].title).toBe('Fixture note');
    expect(notes[0].tags).toContain('fixture');
  });
});
