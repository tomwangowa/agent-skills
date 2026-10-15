export function searchActivities(activities, keyword) {
    const lower = keyword.toLowerCase();
    const results = [];
    for (const a of activities) {
        const matches = a.context?.toLowerCase().includes(lower) ||
            a.activities.some((e) => e.description.toLowerCase().includes(lower)) ||
            a.tags?.some((t) => t.toLowerCase().includes(lower)) ||
            a.project_name?.toLowerCase().includes(lower);
        if (matches) {
            const desc = a.activities.map((e) => e.description).join('; ');
            results.push({
                source: 'activity',
                date: a.timestamp.slice(0, 10),
                title: `[${a.project_name}] ${desc.slice(0, 80)}`,
                snippet: a.context?.slice(0, 200) ?? desc.slice(0, 200),
                tags: a.tags ?? [],
            });
        }
    }
    return results;
}
export function searchNotesUnified(notes, keyword) {
    const lower = keyword.toLowerCase();
    return notes
        .filter((n) => n.title.toLowerCase().includes(lower) ||
        n.content.toLowerCase().includes(lower) ||
        n.tags.some((t) => t.toLowerCase().includes(lower)))
        .map((n) => ({
        source: 'note',
        date: n.date,
        title: n.title,
        snippet: n.summary.slice(0, 200) || n.content.slice(0, 200),
        tags: n.tags,
    }));
}
