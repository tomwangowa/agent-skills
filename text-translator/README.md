# Text Translator

Translate text content to any target language while preserving code, structure, and technical formatting.

## Quick Start

**Trigger the skill:**
```
"翻譯成英文"
"translate to Japanese"
"用繁體中文翻譯這份文件"
```

**Example:**
```
User: "Translate this document to English"
Claude: [Applies text-translator skill]
        → Detects target: English
        → Reads content
        → Preserves code and Markdown structure
        → Translates text content
        → Outputs translated document
```

## Features

### Universal Text Translation
- **Plain text:** Direct translation
- **Markdown:** Structure and code preservation
- **Any language:** Leverages Claude's multilingual capabilities

### Smart Preservation
- Code blocks: Completely untouched
- Inline code: Technical syntax preserved
- Technical terms: API, HTTP, REST, etc. maintained
- Links: Text translated, URLs preserved

### Natural Language Interface
- Detect language from keywords (English, 英文, 日本語)
- Interactive clarification if unclear
- Confirmation before processing

## When to Use

**Use this skill when:**
- Need document in different language
- Creating multilingual documentation
- Translating technical content
- Preparing international content

**Works with:**
- Plain text files
- Markdown documents
- Technical documentation
- README files, specs, guides

## Translation Modes

### Plain Text
- All content translated
- Line breaks preserved
- Simple and direct

### Markdown (Smart Mode)
- Translates: Headers, paragraphs, lists, tables, quotes
- Preserves: Code blocks, inline code, URLs, file paths
- Maintains: Markdown structure and formatting

## Examples

### Plain Text

**Before:**
```
這是技術文件。使用 API 處理請求。
```

**After (English):**
```
This is technical documentation. Use API to handle requests.
```

### Markdown Document

**Before:**
```markdown
## 安裝

使用指令：

```bash
npm install
```

確保 Node.js 已安裝。
```

**After (English):**
```markdown
## Installation

Use the command:

```bash
npm install
```

Ensure Node.js is installed.
```

## Integration

### Standalone Usage
```
User: "翻譯這個文件成英文"
→ text-translator translates directly
```

### Called by markdown-structurer
```
User: "翻譯成英文並結構化"
→ markdown-structurer detects translation need
→ Calls text-translator automatically
→ Applies structuring to translated content
```

## Troubleshooting

### "Target language unclear"
- Specify language explicitly: "translate to English"
- Or respond to clarification question

### "Translation quality seems off"
- Review technical terms (may be over-preserved)
- Try rephrasing source content
- Manual review recommended for critical docs

### "Code was translated"
- Report as bug - code should never be translated
- Check if content was in code block format

## Dependencies

- **Required:** Claude Code Read, Write, Edit tools
- **Optional:** None
- **Works with:** markdown-structurer (auto-integration)

## Security

- Read-only by default
- Validates file paths
- No code execution
- Preserves security-sensitive content in code blocks

## Related Skills

- **markdown-structurer:** Calls translator when translation detected
- **markdown-formatter:** Can format before/after translation
- **spec-generator:** Can translate generated specs

## License

Part of Claude Code skills collection.
