import { readFileSync, readdirSync, existsSync } from 'fs';
import { join } from 'path';
import type { ActivityFile } from '../types.js';

export function loadActivities(basePath: string): ActivityFile[] {
  const results: ActivityFile[] = [];

  const dirs = [basePath];
  const processedDir = join(basePath, 'processed');
  if (existsSync(processedDir)) {
    dirs.push(processedDir);
  }

  for (const dir of dirs) {
    const files = readdirSync(dir).filter((f) => f.endsWith('.json'));
    for (const file of files) {
      try {
        const raw = readFileSync(join(dir, file), 'utf-8');
        const parsed = JSON.parse(raw) as ActivityFile;
        if (parsed.session_id && parsed.timestamp) {
          results.push(parsed);
        }
      } catch {
        // Skip malformed files
      }
    }
  }

  return results.sort(
    (a, b) => new Date(b.timestamp).getTime() - new Date(a.timestamp).getTime()
  );
}

export interface ActivityFilter {
  project?: string;
  type?: string;
  tag?: string;
  since?: Date;
  until?: Date;
}

export function filterActivities(
  activities: ActivityFile[],
  filter: ActivityFilter
): ActivityFile[] {
  return activities.filter((a) => {
    if (filter.project && a.project_name !== filter.project) return false;
    if (filter.type && !a.activities.some((e) => e.type === filter.type)) return false;
    if (filter.tag && !a.tags?.includes(filter.tag)) return false;
    if (filter.since && new Date(a.timestamp) < filter.since) return false;
    if (filter.until && new Date(a.timestamp) > filter.until) return false;
    return true;
  });
}
