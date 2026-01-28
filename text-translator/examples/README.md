# Examples

This directory demonstrates text-translator skill capabilities.

## Available Examples

### Plain Text Translation

**File:** `plain-text-example.md`

**Demonstrates:**
- Direct text translation
- Technical term preservation (API, JSON, HTTP)
- Structure maintenance

**Use case:** Translating notes, documentation without Markdown

### Markdown Translation

**File:** `markdown-example.md`

**Demonstrates:**
- Markdown structure preservation
- Code block protection (bash, javascript)
- Inline code preservation
- Table translation
- Technical term handling
- Blockquote translation

**Use case:** Translating technical documentation, README files, guides

## Quick Test

Try translating the examples yourself:

```bash
# Copy example to test file
cp plain-text-example.md test-translation.md

# Ask Claude
"Translate test-translation.md to English"
```

Compare result with the "Translated" section in the example.

## What Gets Preserved

**Always preserved:**
- Code blocks (bash, python, javascript, etc.)
- Inline code (`` `code` ``)
- Technical acronyms (API, HTTP, JSON, REST, etc.)
- Proper nouns (GitHub, React, Node.js)
- URLs and file paths
- Programming keywords

**Always translated:**
- Headers and titles
- Paragraph content
- List items
- Table content
- Link text
- Blockquote content
- General descriptions

## Real-World Scenarios

### Scenario 1: README Translation
- Original: Chinese README
- Need: English version for open source
- Use: text-translator → English
- Result: All docs translated, code examples preserved

### Scenario 2: Multilingual Documentation
- Original: English technical spec
- Need: Japanese version for team
- Use: text-translator → Japanese
- Result: Complete Japanese docs with original code

### Scenario 3: With Structuring
- Original: Unstructured Chinese notes
- Need: Structured English document
- Use: "翻譯成英文並結構化"
- Result: markdown-structurer calls translator, then structures
