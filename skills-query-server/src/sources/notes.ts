import { readFileSync, readdirSync, statSync } from 'fs';
import { join, basename } from 'path';
import { parseDocument } from 'yaml';
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

function parseFrontmatter(raw: string): { data: Record<string, unknown>; content: string } {
  const text = raw.replace(/^\uFEFF/, '');
  const opening = text.match(/^---([^\r\n]*)\r?\n/);
  if (!opening) return { data: {}, content: text };
  const language = opening[1].trim();
  // Notes are data; never dispatch an executable frontmatter engine.
  if (!['', 'yaml', 'yml', 'json'].includes(language)) throw new Error('Unsupported frontmatter language');
  const rest = text.slice(opening[0].length);
  const closing = /^---[ \t]*(?:\r?\n|$)/m.exec(rest);
  if (!closing) throw new Error('Unclosed frontmatter');
  const header = rest.slice(0, closing.index);
  let value: unknown;
  if (language === 'json') {
    value = JSON.parse(header);
  } else {
    const document = parseDocument(header, { customTags: ['timestamp'], prettyErrors: false });
    if (document.errors.length || document.warnings.length) throw new Error('Invalid frontmatter');
    value = document.toJS({ maxAliasCount: 100 });
  }
  if (value != null && (typeof value !== 'object' || Array.isArray(value))) {
    throw new Error('Frontmatter must be a mapping');
  }
  return { data: (value ?? {}) as Record<string, unknown>,
    content: rest.slice(closing.index + closing[0].length) };
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
      const { data, content } = parseFrontmatter(raw);

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
