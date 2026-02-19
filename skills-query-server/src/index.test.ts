import { describe, it, expect } from 'vitest';
import { loadConfig } from './config.js';
import { loadActivities } from './sources/activities.js';
import { loadNotes } from './sources/notes.js';
import { resolve, dirname } from 'path';
import { fileURLToPath } from 'url';
import { existsSync } from 'fs';

const __dirname = dirname(fileURLToPath(import.meta.url));
const configPath = resolve(__dirname, '..', 'config.json');

describe('integration: real data sources', () => {
  it('loads config from config.json', () => {
    if (!existsSync(configPath)) return; // Skip in CI
    const config = loadConfig(configPath);
    expect(config.sources.activities).toBeTruthy();
    expect(config.sources.notes).toBeTruthy();
  });

  it('reads real activities if available', () => {
    if (!existsSync(configPath)) return;
    const config = loadConfig(configPath);
    if (!existsSync(config.sources.activities)) return;
    const activities = loadActivities(config.sources.activities);
    expect(Array.isArray(activities)).toBe(true);
    expect(activities.length).toBeGreaterThan(0);
  });

  it('reads real notes if available', () => {
    if (!existsSync(configPath)) return;
    const config = loadConfig(configPath);
    if (!existsSync(config.sources.notes)) return;
    const notes = loadNotes(config.sources.notes);
    expect(Array.isArray(notes)).toBe(true);
    expect(notes.length).toBeGreaterThan(0);
    expect(notes[0].title).toBeTruthy();
    expect(notes[0].tags).toBeDefined();
  });
});
