import { readFileSync, existsSync, statSync, accessSync, constants } from 'fs';
import { homedir } from 'os';
import { resolve } from 'path';
import type { Config } from './types.js';
import { readWorkJournal, resolveConfigRoot, resolveActivitiesDir, resolveDataPath } from './runtime-config.js';

function expandHome(p: string): string {
  if (p.startsWith('~/')) {
    return resolve(homedir(), p.slice(2));
  }
  return resolve(p);
}

/** Load an explicitly selected development config; never use it as a hidden runtime fallback. */
export function loadConfig(configPath: string): Config {
  if (!existsSync(configPath)) {
    throw new Error(
      `Config file not found: ${configPath}\n` +
      'Create a config.json with:\n' +
      '{\n  "sources": {\n    "activities": "~/.claude/activities",\n    "notes": { "paths": ["~/path/to/QA-TO-NOTES"] }\n  }\n}'
    );
  }

  const raw = JSON.parse(readFileSync(configPath, 'utf-8'));

  if (!raw.sources?.activities) {
    throw new Error('Config must have sources.activities');
  }
  if (!raw.sources?.notes?.paths || !Array.isArray(raw.sources.notes.paths) || raw.sources.notes.paths.length === 0) {
    throw new Error('Config must have sources.notes.paths (non-empty array of strings)');
  }

  return {
    sources: {
      activities: expandHome(raw.sources.activities),
      notes: {
        paths: raw.sources.notes.paths.map(expandHome),
        recursive: raw.sources.notes.recursive ?? true,
        exclude_hidden: raw.sources.notes.exclude_hidden ?? true,
      },
    },
  };
}

/** Resolve the same external settings and activity override as the Python logger. */
export function loadRuntimeConfig(env: NodeJS.ProcessEnv, home: string): Config {
  const root = resolveConfigRoot(env, home);
  let settings;
  try {
    settings = readWorkJournal(root);
  } catch (error) {
    throw new Error(`Journal settings error at ${resolve(root, 'work-journal.json')}: ${String(error)}. Run work-journal setup first.`);
  }
  const activities = resolveActivitiesDir(env, settings, root, home);
  try {
    if (!statSync(activities).isDirectory()) throw new Error('Not a directory');
    accessSync(activities, constants.R_OK | constants.W_OK | constants.X_OK);
  } catch {
    throw new Error(`Selected activity directory is missing or not writable: ${activities}. Run work-journal setup or fix its permissions.`);
  }
  return { sources: {
    activities,
    notes: {
      paths: settings.sources.notes.paths.map(path => resolveDataPath(path, root, home)),
      recursive: settings.sources.notes.recursive ?? true,
      exclude_hidden: settings.sources.notes.exclude_hidden ?? true,
    },
  } };
}
