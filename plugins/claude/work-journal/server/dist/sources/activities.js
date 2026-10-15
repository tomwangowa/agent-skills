import { readFileSync, readdirSync, existsSync } from 'fs';
import { join } from 'path';
export function loadActivities(basePath) {
    const results = [];
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
                const parsed = JSON.parse(raw);
                if (parsed.session_id && parsed.timestamp) {
                    results.push(parsed);
                }
            }
            catch {
                // Skip malformed files
            }
        }
    }
    return results.sort((a, b) => new Date(b.timestamp).getTime() - new Date(a.timestamp).getTime());
}
export function filterActivities(activities, filter) {
    return activities.filter((a) => {
        if (filter.project && a.project_name !== filter.project)
            return false;
        if (filter.type && !a.activities.some((e) => e.type === filter.type))
            return false;
        if (filter.tag && !a.tags?.includes(filter.tag))
            return false;
        if (filter.since && new Date(a.timestamp) < filter.since)
            return false;
        if (filter.until && new Date(a.timestamp) > filter.until)
            return false;
        return true;
    });
}
