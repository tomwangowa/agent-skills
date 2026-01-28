# Examples

This directory contains before/after examples demonstrating the markdown-structurer skill.

## Quick Comparison

**View the difference:**
```bash
# Side-by-side diff
diff -u before.md after.md

# Or use your preferred diff tool
code --diff before.md after.md
```

## Before (Unstructured)

File: `before.md`

**Characteristics:**
- No header hierarchy
- Plain text YAML blocks (no code formatting)
- Flat list structure
- No tables for comparisons
- No tags for categorization
- Missing technical term highlighting

**Use case:** Raw notes, draft documentation, plain text exports

## After (Structured)

File: `after.md`

**Improvements:**
- ✅ **H1 main title** + **H2 sections** + **H3 subsections**
- ✅ **Tags** at top for categorization
- ✅ **YAML code blocks** with syntax highlighting
- ✅ **Bash code blocks** for commands
- ✅ **Tables** for verb categories and error/correct comparisons
- ✅ **Inline code** for technical terms (`keywords`, `description`)
- ✅ **Bold labels** for category markers
- ✅ **Structured comparisons** (陷阱 1, 2) using tables

## Changes Summary

| Element | Before | After |
|---------|--------|-------|
| Headers | None | H1 (1) + H2 (5) + H3 (6) |
| Code blocks | 0 | 8 (YAML + bash) |
| Tables | 0 | 3 (verbs, comparisons) |
| Inline code | 0 | 15+ terms |
| Tags | None | 5 relevant tags |
| Bold emphasis | Minimal | Strategic key terms |

## How These Were Created

1. **before.md**: Original unstructured text (real example from testing)
2. **after.md**: Processed with markdown-structurer skill
3. **Process**: Agent applied decision framework from SKILL.md
   - Pattern matched headers (策略 1/2, 技巧 1/2/3)
   - Identified table patterns (verb lists, ❌ vs ✅)
   - Wrapped YAML and commands in code blocks
   - Added inline code for technical terms
   - Created tags based on content

## Try It Yourself

1. Copy `before.md` to a new file
2. Ask Claude: "請使用 markdown-structurer 處理這個文件"
3. Compare result with `after.md`

## Real-World Use Cases

These examples demonstrate structuring:
- **Documentation notes** → Professional docs
- **Meeting notes** → Structured minutes
- **Draft specs** → Formatted specifications
- **Plain text exports** → Markdown documents

## Expected Results

When you run markdown-structurer on `before.md`, you should get output very similar to `after.md`, with:
- Consistent header hierarchy
- Properly formatted code blocks
- Strategic use of tables
- Technical term highlighting
- Categorization tags
