import { readFileSync, readdirSync, statSync } from 'fs';
import { join, basename } from 'path';
import matter from 'gray-matter';
import type { QANote, NotesConfig } from '../types.js';

function walkMarkdown(dir: string, recursive: boolean, excludeHidden: boolean): string[] {
  let results: string[] = [];
  let entries: string[];
  try {
    entries = readdirSync(dir);
  } catch {
    return results;
  }

  for (const entry of entries) {
    if (excludeHidden && entry.startsWith('.')) continue;
    const full = join(dir, entry);
    let stat;
    try {
      stat = statSync(full);
    } catch {
      continue;
    }
    if (stat.isDirectory()) {
      if (recursive) {
        results = results.concat(walkMarkdown(full, recursive, excludeHidden));
      }
    } else if (entry.endsWith('.md')) {
      results.push(full);
    }
  }
  return results;
}

export function loadNotes(config: NotesConfig): QANote[] {
  const allFiles: string[] = [];
  for (const root of config.paths) {
    allFiles.push(...walkMarkdown(root, config.recursive, config.exclude_hidden));
  }

  const notes: QANote[] = [];
  for (const filepath of allFiles) {
    try {
      const raw = readFileSync(filepath, 'utf-8');
      const { data, content } = matter(raw);

      // Extract title from first H1
      const titleMatch = content.match(/^#\s+(.+)$/m);
      const title = titleMatch?.[1] ?? basename(filepath).replace(/\.md$/, '');

      // Extract summary from 概述 or Overview section
      const summaryMatch = content.match(
        /##\s+(?:概述|Overview)\s*\n+([\s\S]*?)(?=\n##|\n---|$)/
      );
      const summary = summaryMatch?.[1]?.trim() ?? '';

      notes.push({
        filename: basename(filepath),
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
