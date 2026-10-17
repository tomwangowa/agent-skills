import { readFileSync, existsSync, realpathSync } from 'node:fs';
import { isAbsolute, join, resolve, dirname } from 'node:path';

export interface WorkJournalSettings {
  sources: {
    activities: string;
    notes: { paths: string[]; recursive?: boolean; exclude_hidden?: boolean };
  };
}

/** Preserve lexical paths while checking actual cache ancestors through symlink aliases. */
export function requireExternalPersonalPath(path: string): string {
  for (let candidate = resolve(path); ; candidate = dirname(candidate)) {
    if (existsSync(candidate)) {
      for (let parent = realpathSync(candidate); ; parent = dirname(parent)) {
        if (['.claude-plugin/plugin.json', '.codex-plugin/plugin.json', 'plugin.json']
          .some(name => existsSync(join(parent, name)))) {
          throw new Error('Personal settings and data must be outside plugin caches');
        }
        if (dirname(parent) === parent) break;
      }
    }
    if (dirname(candidate) === candidate) break;
  }
  return path;
}

/** Resolve data paths independently of the server's launch working directory. */
export function resolveDataPath(value: string, base: string, home: string): string {
  if (typeof value !== 'string' || !value.trim() || value.includes('\0')) {
    throw new Error('Expected a non-empty data path');
  }
  if (value === '~') return resolve(home);
  if (value.startsWith('~/')) return resolve(home, value.slice(2));
  if (value.startsWith('~')) throw new Error('Named-user home paths are not supported');
  return resolve(base, value);
}

/** Select the shared per-user settings root with explicit, XDG, then home priority. */
export function resolveConfigRoot(env: NodeJS.ProcessEnv, home: string): string {
  const explicit = env.AGENT_SKILLS_CONFIG_DIR;
  const xdg = env.XDG_CONFIG_HOME;
  const value = explicit || xdg;
  if (value) {
    if (!isAbsolute(value) && !value.startsWith('~/') && value !== '~') {
      throw new Error('Config root must be an absolute or ~/ path');
    }
    const root = resolveDataPath(value, home, home);
    return requireExternalPersonalPath(explicit ? root : join(root, 'agent-skills'));
  }
  return requireExternalPersonalPath(resolve(home, '.config/agent-skills'));
}

/** Select the same activity directory used by the Python logger runtime. */
export function resolveActivitiesDir(env: NodeJS.ProcessEnv,
  settings: { sources?: { activities?: string } }, configRoot: string, home: string): string {
  return requireExternalPersonalPath(resolveDataPath(
    env.CLAUDE_ACTIVITIES_DIR || settings.sources?.activities || '', configRoot, home));
}

/** Validate settings without reading activity or note contents. */
export function validateWorkJournal(settings: unknown): WorkJournalSettings {
  const value = settings as WorkJournalSettings | null;
  if (!value || typeof value !== 'object' || Array.isArray(value)
      || !value.sources || typeof value.sources !== 'object') {
    throw new Error('work-journal.json must contain a sources object');
  }
  const { activities, notes } = value.sources;
  if (typeof activities !== 'string' || !activities.trim() || activities.includes('\0')) {
    throw new Error('sources.activities must be a non-empty path');
  }
  if (!notes || !Array.isArray(notes.paths) || notes.paths.length === 0
      || notes.paths.some(p => typeof p !== 'string' || !p.trim() || p.includes('\0'))) {
    throw new Error('sources.notes.paths must contain non-empty paths');
  }
  for (const key of ['recursive', 'exclude_hidden'] as const) {
    if (key in notes && typeof notes[key] !== 'boolean') throw new Error(`sources.notes.${key} must be boolean`);
  }
  return value;
}

/** Read only the selected user's shared journal settings. */
export function readWorkJournal(configRoot: string): WorkJournalSettings {
  requireExternalPersonalPath(join(configRoot, 'work-journal.json'));
  return validateWorkJournal(JSON.parse(readFileSync(join(configRoot, 'work-journal.json'), 'utf8')));
}
