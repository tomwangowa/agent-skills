---
name: md-translate
description: Translate markdown files to English and Traditional Chinese. Automatically detects source language and generates both -en.md and -zh.md versions. Preserves markdown formatting, code blocks, frontmatter, and links.
compatibility: Designed for Claude Code. Works with any markdown file.
allowed-tools: Read Write
---

# Markdown Translation Skill

Automatically translate markdown documents into English and Traditional Chinese (zh-TW) versions.

## Usage

```
/md-translate <file-path>              → Generate both EN and ZH versions
/md-translate <file-path> --lang en    → Only generate English version
/md-translate <file-path> --lang zh    → Only generate Chinese version
/md-translate docs/**/*.md             → Batch translate all .md files
/md-translate <file-path> --force      → Overwrite existing translations without prompting
```

**Note on `--lang` with same-language source:** If `--lang en` is passed but the source is already English, translate it to Chinese instead (the other language) and note the swap. Same applies to `--lang zh` on a Chinese source. If unsure, ask the user to confirm intent.

---

## How It Works

### Step 1: Read Source File

Read the specified markdown file to translate.

**Important checks:**
- File must exist
- File must be a `.md` file
- Skip if file already has `-en.md` or `-zh.md` suffix (prevent double translation)

### Step 2: Detect Source Language

Analyze the content to determine the primary language:
- If significant CJK content (>30% of characters are CJK) → Source is Chinese
- If predominantly English (<30% CJK) → Source is English
- If borderline (roughly 30–50% CJK with substantial English) → Ask user which language to treat as source

### Step 3: Preserve Special Elements

Before translation, identify and mark these elements to preserve them:

**Do NOT translate:**
- YAML frontmatter (`---` blocks at top of file)
- Code blocks (` ``` ` fenced blocks)
- URLs and link targets `[text](url)` — only translate link text
- File paths and code references
- HTML tags and attributes
- Markdown syntax (`#`, `*`, `-`, `>`, etc.)
- Email addresses
- Proper nouns in English (company names, product names, tool names)
- Variable names, function names, API endpoints

**DO translate:**
- All body text
- Headings
- List items
- Table content
- Link text (but not URLs)
- Image alt text
- Blockquote content

### Step 4: Translation Strategy

**English Translation Principles:**
- Use clear, professional technical writing
- Preserve technical terms in English (don't re-translate)
- Keep acronyms (API, SDK, etc.) as-is
- Use American English spelling
- Maintain parallel structure in lists

**Chinese Translation Principles:**
- Use Traditional Chinese (繁體中文 zh-TW)
- Keep technical terms in English with Chinese explanation in parentheses when first mentioned
  - Example: "API Gateway (API 閘道)"
- Use professional technical vocabulary
- Maintain clarity and readability
- For UI/UX terms, use commonly accepted translations
- Product names stay in English

### Step 5: Generate Output Files

Create translated files with appropriate suffixes:

**File naming convention:**
- Original: `document.md`
- English: `document-en.md`
- Chinese: `document-zh.md`

**Overwrite guard (default behavior):**
Before writing, check if the output file(s) already exist. If they do, show a warning and ask for confirmation:
```
⚠️  Output file already exists: document-en.md
Overwrite? (yes / no)
```
Skip this check only when `--force` was passed.

**Preserve:**
- Original file structure (same directory)
- Frontmatter (copy as-is to both versions)
- Line breaks and spacing
- Markdown formatting

### Step 6: Summary Report

After translation, display a summary:

```
✅ Translation Complete

Source file: docs/design/overview.md
Detected language: Chinese

Generated files:
  📄 docs/design/overview-en.md (English)
  📄 docs/design/overview-zh.md (Traditional Chinese)

Summary:
  - Source lines: 245
  - Code blocks preserved: 12
  - Links preserved: 18
  - Headings: 24
```

---

## Translation Guidelines

### Technical Terms Reference

Common technical terms to keep consistent:

| English | Traditional Chinese |
|---------|---------------------|
| Onboarding | 引導流程 |
| Feature | 功能 |
| User Flow | 使用者流程 |
| Architecture | 架構 |
| API | API |
| Frontend | 前端 |
| Backend | 後端 |
| Dashboard | 儀表板 |
| Authentication | 身份驗證 |
| Authorization | 授權 |
| Package | 方案 / 套餐 |
| Subscription | 訂閱 |
| Repository | 儲存庫 |
| Pull Request | 拉取請求 |
| Deployment | 部署 |
| Microservice | 微服務 |

### Quality Checks

Before finalizing, verify:
- [ ] All headings are translated
- [ ] Code blocks remain unchanged
- [ ] URLs are preserved
- [ ] Frontmatter is intact
- [ ] List formatting is consistent
- [ ] Tables are properly formatted
- [ ] No markdown syntax is broken
- [ ] Technical terms are consistent
- [ ] Tone is professional and clear

---

## Error Handling

**If source file doesn't exist:**
```
❌ Error: File not found
Path: <file-path>

Please check the file path and try again.
```

**If file is already a translated version:**
```
⚠️  Warning: This file appears to be a translated version
File: document-en.md

Translate the original file (document.md) instead.
```

**If translation is ambiguous:**
```
❓ Ambiguous Content Detected

The document contains mixed languages. Which should be the source?
1. Chinese → Translate to English only (-en.md)
2. English → Translate to Chinese only (-zh.md)
3. Keep original as-is, generate both -en and -zh versions

Please choose (1/2/3):
```

---

## Notes

- **Do not edit generated files manually** — they will be overwritten if source is re-translated
- Keep source files as the "source of truth"
- If you need to update content, edit the source file and re-run translation
- Generated files are intended for distribution and should be committed to git
- For batch translation with `docs/**/*.md`, files already ending in `-en.md` or `-zh.md` are automatically skipped

---

## Implementation Notes

When implementing this skill, use Claude's native multilingual capabilities to:
1. Accurately detect source language
2. Perform high-quality translation that preserves technical meaning
3. Maintain context across paragraphs and sections
4. Ensure consistency in terminology throughout the document

The translation should feel natural to native speakers while preserving all technical accuracy and markdown structure.
