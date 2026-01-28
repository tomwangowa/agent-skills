# Text-Translator Skill Design

**Date:** 2026-01-28
**Status:** Approved
**Author:** Claude Sonnet 4.5 (with user collaboration)

## Background

Need a standalone translation skill that can:
- Translate any text content to target language
- Preserve technical elements (code, structure) in Markdown
- Be called by other skills (e.g., markdown-structurer)
- Support natural language interface

## Requirements

### Functional Requirements

1. **Universal text translation**
   - Plain text: Direct translation
   - Markdown: Preserve structure and code
   - Other text files: Full translation

2. **Language specification**
   - Natural language keywords (English, 英文, Japanese, etc.)
   - Mixed approach: parse intent → ask if unclear
   - Support any language Claude understands

3. **Markdown intelligence**
   - Preserve headers, lists, tables, blockquotes
   - Never translate code blocks or inline code
   - Preserve links (translate text, keep URL)
   - Preserve technical terms and proper nouns

4. **Integration**
   - Can be called by markdown-structurer automatically
   - Works standalone for pure translation

### Non-Functional Requirements

1. **Simple interface:** Single responsibility, easy to use
2. **Separation of concerns:** Translation only, no structuring
3. **Reusability:** Can be called by other skills
4. **Error handling:** Graceful degradation if translation fails

## Design

### Architecture

```
User Request
    ↓
Parse language intent
    ↓
Missing language? → Ask user
    ↓
Detect input format (plain text vs Markdown)
    ↓
Apply translation rules
    ↓
Output translated content
```

### Core Components

#### 1. Language Detection

**From user request:**
- Keywords: "English", "英文", "Japanese", "日本語", "translate to", "翻譯成"
- If unclear → Ask user with AskUserQuestion

**Supported languages:**
- Any language Claude understands
- No predefined list

#### 2. Format Detection

**Automatic detection:**
- Check for Markdown markers (headers, code blocks, lists)
- If found → Apply Markdown preservation rules
- If not → Direct text translation

#### 3. Translation Rules

**For Plain Text:**
- Translate all content directly
- No special handling

**For Markdown:**

| Element | Action |
|---------|--------|
| Headers (`#`, `##`, `###`) | Translate text |
| Paragraphs | Translate content |
| Lists (`-`, `*`, `1.`) | Translate items |
| Tables | Translate cell content |
| Bold/Italic (`**`, `*`) | Translate marked text |
| Links (`[text](url)`) | Translate text, preserve URL |
| Code blocks (` ``` `) | **Preserve completely** |
| Inline code (`` ` ``) | **Preserve completely** |
| Blockquotes (`>`) | Translate content |

**Technical Term Handling:**
- Preserve: API, HTTP, REST, GitHub, React, function, class, etc.
- Translate: Descriptive text and explanations

### Integration with markdown-structurer

**Detection in markdown-structurer:**

```markdown
Keywords to detect:
- "翻譯", "translate", "轉成", "convert to"
- Plus language name (English, 日文, etc.)

If detected:
  1. Call text-translator with target language
  2. Get translated content
  3. Apply structuring rules to translated content

If NOT detected:
  - Preserve original language
  - Only apply structuring
```

**Example workflow:**

```
User: "翻譯成英文並結構化"

markdown-structurer detects:
- Translation keyword: "翻譯"
- Target language: "英文" (English)

Actions:
1. Call text-translator(target=English, content=original)
2. Receive translated Markdown
3. Apply markdown-structurer rules
4. Output: Structured English document
```

### User Interface

**Triggering examples:**

```
# Standalone use
"翻譯成英文"
"translate this to Japanese"
"用繁體中文翻譯這份文件"

# Via markdown-structurer
"翻譯成英文並結構化"
"translate to Japanese and add structure"
```

**Confirmation messages:**

```
"Translating to English..."
"翻譯成繁體中文中..."
"Translation to Japanese complete"
```

### Error Handling

**Unsupported or unclear language:**
```
Error: "無法確認翻譯目標語言。建議使用：英文、繁體中文、日文等。"
Action: Ask user to specify language
```

**Translation quality issues:**
```
Warning: "Translation completed. Please review for technical accuracy."
Action: Output translation with warning
```

**Mixed language content:**
```
Note: "Detected mixed language content - translated all text portions"
Action: Translate all text, note to user
```

**Format detection failure:**
```
Fallback: Treat as plain text, translate directly
```

## File Structure

```
text-translator/
├── SKILL.md           # Main skill definition
├── README.md          # Quick start guide
└── examples/
    ├── plain-text.md  # Plain text translation example
    ├── markdown.md    # Markdown translation example
    └── README.md      # Examples overview
```

## SKILL.md Outline

```markdown
---
name: text-translator
description: Translate text content to target language. For Markdown files, preserves structure and code. Triggers on "translate to", "翻譯成", "convert to". Supports any language Claude understands.
---

# Text Translator

## Overview
- Universal text translation
- Markdown structure preservation
- Code protection

## When to Use
- Need document in different language
- Multilingual documentation
- International content preparation

## Language Detection
- Natural language keywords
- Interactive clarification if unclear

## Translation Rules
[Table of element handling]

## Format Detection
- Automatic Markdown detection
- Plain text fallback

## Examples
- Plain text translation
- Markdown translation (preserving structure)
- Technical document translation

## Error Handling
- Unsupported languages
- Quality warnings
- Mixed content

## Integration
- Standalone usage
- Called by markdown-structurer
- Extensible for other skills
```

## Integration Changes

### markdown-structurer/SKILL.md

Add new section after "Workflow":

```markdown
## Translation Integration

If user request includes translation:
- Keywords: "翻譯", "translate", "轉成"
- Plus target language

markdown-structurer will:
1. Automatically call text-translator skill
2. Get translated content
3. Apply structuring rules

**Example:**
User: "翻譯成英文並結構化"
→ Translates to English
→ Adds structure
→ Output: Structured English document

**Default (no translation):**
User: "請結構化這個文件"
→ Preserves original language
→ Adds structure only
```

## Example Scenarios

### Scenario 1: Plain Text Translation

**Input:**
```
這是一段技術說明。我們使用 API 來處理請求。
```

**Request:**
```
"翻譯成英文"
```

**Output:**
```
This is a technical description. We use API to handle requests.
```

### Scenario 2: Markdown Translation

**Input:**
```markdown
## 技巧

使用動詞可以讓描述更清楚。

```python
def example():
    return "code"
```

常見動詞：create, fix, review
```

**Request:**
```
"translate to English"
```

**Output:**
```markdown
## Techniques

Using verbs makes descriptions clearer.

```python
def example():
    return "code"
```

Common verbs: create, fix, review
```

### Scenario 3: Via markdown-structurer

**Input:**
```
技巧 1：使用動詞

使用動作動詞可以讓描述更清楚。
```

**Request:**
```
"翻譯成英文並結構化"
```

**Process:**
1. markdown-structurer detects translation need
2. Calls text-translator → English translation
3. Applies structuring rules

**Output:**
```markdown
## Technique 1: Use Verbs

Using action verbs makes descriptions clearer.
```

## Trade-offs & Decisions

### Decision 1: Universal vs Markdown-only
**Chosen:** Universal (handles any text)
**Rationale:** More flexible, broader use cases
**Trade-off:** Slightly more complex, but not significantly

### Decision 2: Automatic format detection
**Chosen:** Yes (detect Markdown automatically)
**Rationale:** Better UX, no user input needed
**Trade-off:** May misdetect edge cases, but rare

### Decision 3: Technical term preservation
**Chosen:** Preserve common technical terms
**Rationale:** Maintains technical accuracy
**Trade-off:** Some terms may be preserved when translation preferred, but safer default

### Decision 4: Integration approach
**Chosen:** Automatic detection in markdown-structurer
**Rationale:** Seamless UX, single command workflow
**Trade-off:** markdown-structurer needs detection logic, but minimal

## Success Criteria

- [ ] Translates plain text correctly
- [ ] Preserves Markdown structure and code
- [ ] Detects target language from natural language
- [ ] Interactive clarification works smoothly
- [ ] Can be called by markdown-structurer
- [ ] Error handling is graceful
- [ ] Documentation complete with examples

## Future Enhancements (Out of Scope)

- Glossary/dictionary for consistent term translation
- Batch processing multiple files
- Translation memory for consistency
- Custom preservation rules per project

## Implementation Notes

- Uses Claude Code's native translation capabilities
- No external dependencies
- Simple, focused responsibility
- Extensible for other skills to call

## Related Documents

- markdown-structurer: Will be updated to detect and call this skill
- Design emerged from reconsidering integrated i18n approach
