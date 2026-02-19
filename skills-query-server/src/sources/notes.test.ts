import { describe, it, expect, beforeEach, afterEach } from 'vitest';
import { loadNotes, searchNotes } from './notes.js';
import { writeFileSync, mkdirSync, rmSync } from 'fs';
import { join } from 'path';
import { tmpdir } from 'os';

const SAMPLE_NOTE = `---
tags: [fact-check, AI, PicoClaw]
date: 2026-02-16
source: claude-code
---

# PicoClaw：輕量 AI 助理的真相

## 概述

PicoClaw 是一個開源專案，宣稱是超輕量個人 AI 助理。

## 核心問題

Thin client vs 本地推理的差異。
`;

describe('loadNotes', () => {
  const testDir = join(tmpdir(), 'skills-query-test-notes');

  beforeEach(() => {
    mkdirSync(testDir, { recursive: true });
  });

  afterEach(() => {
    rmSync(testDir, { recursive: true, force: true });
  });

  it('loads markdown files with frontmatter', () => {
    writeFileSync(join(testDir, 'test-note.md'), SAMPLE_NOTE);
    const notes = loadNotes(testDir);
    expect(notes).toHaveLength(1);
    expect(notes[0].title).toBe('PicoClaw：輕量 AI 助理的真相');
    expect(notes[0].date).toBe('2026-02-16');
    expect(notes[0].tags).toContain('fact-check');
    expect(notes[0].source).toBe('claude-code');
  });

  it('extracts summary from 概述 section', () => {
    writeFileSync(join(testDir, 'test-note.md'), SAMPLE_NOTE);
    const notes = loadNotes(testDir);
    expect(notes[0].summary).toContain('PicoClaw 是一個開源專案');
  });

  it('skips non-markdown files', () => {
    writeFileSync(join(testDir, 'test-note.md'), SAMPLE_NOTE);
    writeFileSync(join(testDir, 'debug.log'), 'not a note');
    const notes = loadNotes(testDir);
    expect(notes).toHaveLength(1);
  });

  it('extracts summary when 概述 is the last section', () => {
    const noteWithOverviewLast = `---
tags: [test]
date: 2026-02-18
source: claude-code
---

# Last Section Test

## 概述

This overview is the last section in the file.
`;
    writeFileSync(join(testDir, 'last-section.md'), noteWithOverviewLast);
    const notes = loadNotes(testDir);
    expect(notes[0].summary).toContain('This overview is the last section');
  });

  it('handles notes without frontmatter gracefully', () => {
    writeFileSync(join(testDir, 'plain.md'), '# Just a Title\n\nSome content.');
    const notes = loadNotes(testDir);
    expect(notes).toHaveLength(1);
    expect(notes[0].title).toBe('Just a Title');
    expect(notes[0].tags).toEqual([]);
  });
});

describe('searchNotes', () => {
  const notes = [
    { filename: 'a.md', filepath: '/a.md', date: '2026-02-16', tags: ['AI'], source: 'claude-code', title: 'PicoClaw', content: 'thin client architecture', summary: 'About PicoClaw' },
    { filename: 'b.md', filepath: '/b.md', date: '2026-02-17', tags: ['API'], source: 'claude-code', title: 'API Migration', content: 'scraping to API transition', summary: 'About migration' },
  ];

  it('searches by keyword in content', () => {
    const results = searchNotes(notes, 'thin client');
    expect(results).toHaveLength(1);
    expect(results[0].title).toBe('PicoClaw');
  });

  it('searches by keyword in title', () => {
    const results = searchNotes(notes, 'Migration');
    expect(results).toHaveLength(1);
  });

  it('searches by tag', () => {
    const results = searchNotes(notes, 'API');
    expect(results).toHaveLength(1);
    expect(results[0].title).toBe('API Migration');
  });

  it('is case insensitive', () => {
    const results = searchNotes(notes, 'picoclaw');
    expect(results).toHaveLength(1);
  });
});
