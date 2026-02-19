import { describe, it, expect, beforeEach, afterEach } from 'vitest';
import { loadActivities, filterActivities } from './activities.js';
import { writeFileSync, mkdirSync, rmSync } from 'fs';
import { join } from 'path';
import { tmpdir } from 'os';

const SAMPLE_ACTIVITY = {
  session_id: 'session_001',
  timestamp: '2026-02-18T10:00:00Z',
  project_path: '/test/project',
  project_name: 'test-project',
  git_branch: 'main',
  git_remote: 'https://github.com/test/repo',
  activities: [
    {
      type: 'task_completed',
      description: 'Added feature X',
      files_changed: ['src/x.ts'],
      commits: ['abc123'],
    },
  ],
  context: 'Implemented feature X with tests',
  tags: ['feature', 'typescript'],
};

describe('loadActivities', () => {
  const testDir = join(tmpdir(), 'skills-query-test-activities');

  beforeEach(() => {
    mkdirSync(testDir, { recursive: true });
    mkdirSync(join(testDir, 'processed'), { recursive: true });
  });

  afterEach(() => {
    rmSync(testDir, { recursive: true, force: true });
  });

  it('loads JSON files from directory', () => {
    writeFileSync(join(testDir, 'a.json'), JSON.stringify(SAMPLE_ACTIVITY));
    const results = loadActivities(testDir);
    expect(results).toHaveLength(1);
    expect(results[0].session_id).toBe('session_001');
  });

  it('includes processed/ subdirectory', () => {
    writeFileSync(join(testDir, 'a.json'), JSON.stringify(SAMPLE_ACTIVITY));
    const archived = { ...SAMPLE_ACTIVITY, session_id: 'session_old', timestamp: '2026-01-01T00:00:00Z' };
    writeFileSync(join(testDir, 'processed', 'b.json'), JSON.stringify(archived));
    const results = loadActivities(testDir);
    expect(results).toHaveLength(2);
  });

  it('skips malformed JSON files', () => {
    writeFileSync(join(testDir, 'good.json'), JSON.stringify(SAMPLE_ACTIVITY));
    writeFileSync(join(testDir, 'bad.json'), 'not json{{{');
    const results = loadActivities(testDir);
    expect(results).toHaveLength(1);
  });

  it('returns empty array for empty directory', () => {
    const results = loadActivities(testDir);
    expect(results).toHaveLength(0);
  });
});

describe('filterActivities', () => {
  const activities = [
    { ...SAMPLE_ACTIVITY, timestamp: '2026-02-18T10:00:00Z', project_name: 'alpha', tags: ['feat'] },
    { ...SAMPLE_ACTIVITY, timestamp: '2026-02-17T10:00:00Z', project_name: 'beta', tags: ['fix'],
      activities: [{ type: 'bug_fixed', description: 'Fixed Y', files_changed: [], commits: [] }] },
  ];

  it('filters by project', () => {
    const result = filterActivities(activities, { project: 'alpha' });
    expect(result).toHaveLength(1);
  });

  it('filters by activity type', () => {
    const result = filterActivities(activities, { type: 'bug_fixed' });
    expect(result).toHaveLength(1);
  });

  it('filters by tag', () => {
    const result = filterActivities(activities, { tag: 'fix' });
    expect(result).toHaveLength(1);
  });

  it('returns all when no filters', () => {
    const result = filterActivities(activities, {});
    expect(result).toHaveLength(2);
  });
});
