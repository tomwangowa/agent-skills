# Markdown Structurer

Transform plain or flat narrative text into well-structured Markdown by adding headers, tables, code blocks, diagrams, and more based on systematic rules.

## Quick Start

**Trigger the skill:**
```
"請將這個文件結構化"
"Add structure to this markdown"
"Structurize this plain text"
```

**Example:**
```
User: "請將 notes.md 結構化，添加適當的標題和表格"
Claude: [Applies markdown-structurer skill]
        → Analyzes content
        → Adds H1/H2/H3 headers
        → Converts patterns to tables
        → Formats code blocks
        → Asks about diagrams if needed
        → Outputs structured document
```

## See It In Action

**Live examples:** Check out `examples/` directory for before/after comparison

- **[before.md](examples/before.md)** - Unstructured text (plain notes)
- **[after.md](examples/after.md)** - Structured result (professional docs)
- **[examples/README.md](examples/README.md)** - Detailed comparison

**Quick comparison:**
```bash
diff -u examples/before.md examples/after.md
```

## Features

### Systematic Structuring
- **Headers:** H1 for main topic, H2 for sections, H3 for subsections
- **Tables:** Converts comparisons, attributes, and key-value pairs
- **Code blocks:** YAML, JSON, bash commands, inline code for technical terms
- **Mermaid diagrams:** Workflows, decision trees (asks before adding)
- **Bold emphasis:** Key concepts, labels, contrasts
- **Tags:** Categorization for reference documents

### Decision Framework
- Pattern matching for headers (方法 1/2/3, 首先...然後)
- Table detection rules (❌ vs ✅, numbered methods, attributes)
- Code formatting rules (YAML markers, commands, technical terms)
- Diagram identification (workflow descriptions, decision logic)

### Quality Rules
- No HTML tags in tables
- Stop at H3 (no H4/H5/H6)
- Ask before adding Mermaid
- Consistent code formatting
- Concise table cells (< 100 chars)

## When to Use

**Use this skill when:**
- Plain text needs Markdown structure
- Content lacks proper heading hierarchy
- Lists or comparisons should be tables
- Technical terms need code formatting
- Process descriptions need flow diagrams

**Do NOT use for:**
- Only cleaning whitespace (use `markdown-formatter` instead)
- Already well-structured documents
- Minimal markup preference

## Workflow

1. **Read and clean** - Load file, remove redundant whitespace
2. **Add headers** - Identify topics → H1/H2/H3
3. **Tableize** - Convert patterns to tables
4. **Format code** - Wrap code blocks, inline technical terms
5. **Consider diagrams** - Ask user if workflow detected
6. **Add emphasis** - Bold key concepts
7. **Add tags** - If reference document
8. **Output** - Provide structured content

## Integration

**With markdown-formatter:**
```
User: "整理並結構化這個文件"
→ Run markdown-formatter (clean whitespace)
→ Run markdown-structurer (add structure)
→ Result: Clean and well-structured
```

**Standalone:**
```
User: "把純文字轉成結構化 Markdown"
→ Run markdown-structurer directly
→ Includes basic cleanup
```

## Examples

### Before
```
⏺ 如何保證 Skill 能被 AI 調用？

簡短答案
沒有專門的 keywords 欄位...

策略 1：直接列出觸發關鍵字
...
```

### After
```markdown
# 如何保證 Skill 能被 AI 調用？

> **Tags:** `skills` `description` `triggers`

## 簡短答案

沒有專門的 `keywords` 欄位...

## 策略

### 策略 1：直接列出觸發關鍵字

```yaml
name: deploy-production
description: Deploy application...
```
...
```

## Troubleshooting

### "File not found"
- Verify file path is correct
- Use absolute path if needed
- Check Read tool has access

### "Content too minimal"
- File needs > 3 lines for meaningful structure
- Consider if structuring is necessary

### "Analysis failed"
- Falls back to basic formatting (headers only)
- Review error message for details

### "Diagram not added"
- Only adds after user confirms
- Check if workflow pattern was detected

## Dependencies

- **Required:** Claude Code Read, Edit, Write tools
- **Optional:** None
- **Integrates with:** markdown-formatter

## Security

- Read-only by default
- Validates file paths (no directory traversal)
- No HTML injection in output
- No execution of embedded code

## Related Skills

- **markdown-formatter:** Clean whitespace and spacing
- **readme-generator:** Generate comprehensive README files
- **spec-generator:** Create specification documents

## License

Part of Claude Code skills collection.
