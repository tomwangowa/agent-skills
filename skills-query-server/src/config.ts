import { readFileSync, existsSync } from 'fs';
import { homedir } from 'os';
import { resolve } from 'path';
import type { Config } from './types.js';

function expandHome(p: string): string {
  if (p.startsWith('~/')) {
    return resolve(homedir(), p.slice(2));
  }
  return resolve(p);
}

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
