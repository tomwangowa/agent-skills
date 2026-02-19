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
      '{\n  "sources": {\n    "activities": "~/.claude/activities",\n    "notes": "~/path/to/QA-TO-NOTES"\n  }\n}'
    );
  }

  const raw = JSON.parse(readFileSync(configPath, 'utf-8'));

  if (!raw.sources?.activities || !raw.sources?.notes) {
    throw new Error('Config must have sources.activities and sources.notes');
  }

  return {
    sources: {
      activities: expandHome(raw.sources.activities),
      notes: expandHome(raw.sources.notes),
    },
  };
}
