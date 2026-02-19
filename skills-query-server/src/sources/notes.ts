import { readFileSync, readdirSync } from 'fs';
import { join } from 'path';
import matter from 'gray-matter';
import type { QANote } from '../types.js';

export function loadNotes(basePath: string): QANote[] {
  const files = readdirSync(basePath).filter((f) => f.endsWith('.md'));
  const notes: QANote[] = [];

  for (const file of files) {
    try {
      const filepath = join(basePath, file);
      const raw = readFileSync(filepath, 'utf-8');
      const { data, content } = matter(raw);

      // Extract title from first H1
      const titleMatch = content.match(/^#\s+(.+)$/m);
      const title = titleMatch?.[1] ?? file.replace(/\.md$/, '');

      // Extract summary from 概述 or Overview section
      const summaryMatch = content.match(
        /##\s+(?:概述|Overview)\s*\n+([\s\S]*?)(?=\n##|\n---|$)/
      );
      const summary = summaryMatch?.[1]?.trim() ?? '';

      notes.push({
        filename: file,
        filepath,
        date: data.date instanceof Date
          ? data.date.toISOString().slice(0, 10)
          : String(data.date ?? ''),
        tags: Array.isArray(data.tags) ? data.tags.map(String) : [],
        source: String(data.source ?? ''),
        title,
        content,
        summary,
      });
    } catch {
      // Skip unparseable files
    }
  }

  return notes.sort((a, b) => b.date.localeCompare(a.date));
}

export function searchNotes(notes: QANote[], keyword: string): QANote[] {
  const lower = keyword.toLowerCase();
  return notes.filter(
    (n) =>
      n.title.toLowerCase().includes(lower) ||
      n.content.toLowerCase().includes(lower) ||
      n.tags.some((t) => t.toLowerCase().includes(lower))
  );
}
