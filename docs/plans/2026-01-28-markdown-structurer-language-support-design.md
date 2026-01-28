# Markdown Structurer: Language & Translation Support

**Date:** 2026-01-28
**Status:** Approved
**Author:** Claude Sonnet 4.5 (with user collaboration)

## Background

Current `markdown-structurer` skill outputs structured Markdown but lacks language control. Users need ability to:
- Specify output language for structural elements
- Choose between structure-only vs full-translation modes
- Have sensible defaults when language not specified

## Requirements

### Functional Requirements

1. **Two operation modes:**
   - **Structure-only:** Translate headers, table headers, section labels, tags; preserve original content
   - **Full-translation:** Translate entire document including content

2. **Language specification:**
   - Support natural language descriptions ("English", "英文", "日本語", etc.)
   - No predefined language list - leverage Claude's multilingual capabilities
   - Flexible parsing from user requests

3. **Default behavior:**
   - When not specified: preserve original language, use structure-only mode
   - Smart detection from context

4. **User interaction:**
   - Mixed approach: parse natural language → use defaults → ask if ambiguous
   - Clear confirmation of detected language and mode

5. **No bilingual output:**
   - User must choose single language (simplifies implementation)
   - Can run skill twice for two versions

### Non-Functional Requirements

1. **Backward compatibility:** Existing behavior (no language specified) continues to work
2. **Error handling:** Graceful degradation if translation fails
3. **User experience:** Minimal friction, natural language interface
4. **Testability:** Clear test cases for both modes

## Design

### Architecture

```
User Request
    ↓
Parse Intent (language + mode)
    ↓
Missing info? → Ask User
    ↓
Confirm Settings
    ↓
Execute Structuring (with language/mode)
    ↓
Output Result
```

### Language & Mode Detection

#### Language Detection Rules

```
Keywords to detect:
- English: "English", "英文", "en", "in English"
- Traditional Chinese: "Traditional Chinese", "繁體中文", "繁中", "zh-TW"
- Japanese: "Japanese", "日文", "日本語", "ja"
- Others: Use user's natural description directly

Fallback: Detect from original content language
```

#### Mode Detection Rules

```
Structure-only keywords:
- "標題用...", "headers in...", "只改標題", "structure only"
- "用...語言的標題"

Full-translation keywords:
- "翻譯成...", "translate to...", "翻譯並結構化"
- "轉成...文"

Fallback: Ask user to choose
```

### User Interaction Flow

#### Case 1: Complete specification
```
User: "結構化並翻譯成英文"
→ Detected: language=English, mode=full-translation
→ Execute directly
```

#### Case 2: Language only
```
User: "用英文結構化這個文件"
→ Detected: language=English, mode=?
→ Ask: "要如何處理？
   (1) 只將標題和結構標記改為英文（保留原文內容）
   (2) 翻譯整份文件為英文"
```

#### Case 3: Mode only
```
User: "翻譯並結構化這個文件"
→ Detected: language=?, mode=full-translation
→ Ask: "要翻譯成什麼語言？
   (1) 英文
   (2) 繁體中文
   (3) 其他（請輸入）"
```

#### Case 4: Nothing specified
```
User: "請結構化這個文件"
→ Use defaults: preserve original language, structure-only
→ Execute directly
```

### Implementation Changes

#### 1. Workflow Chapter Updates

Add step 1.5 after "Read and clean":

```markdown
1.5. **Detect language and mode**
   - Parse user request for language intent
   - Parse user request for mode (structure-only vs full-translation)
   - If missing info → Ask user with AskUserQuestion
   - Confirm: "Processing in [language], [mode] mode"
```

#### 2. New Chapter: Language & Translation

```markdown
## Language & Translation

### Language Detection

**From user request:**
- Natural language keywords (English, 英文, Japanese, etc.)
- If not specified → Detect from original content

### Mode Selection

**Structure-only mode:**
- **Translates:** Headers, table headers, section labels, tags
- **Preserves:** Original content text, code blocks, quotes
- **Use when:** Content already correct, only need structure in target language

**Full-translation mode:**
- **Translates:** Everything including content text
- **Maintains:** Code syntax, technical terms in code blocks
- **Use when:** Need complete document in target language

### Language Handling Rules

| Element | Structure-only | Full-translation |
|---------|---------------|------------------|
| Headers (H1/H2/H3) | Translate | Translate |
| Body text | Preserve original | Translate |
| Table headers | Translate | Translate |
| Table content | Preserve original | Translate |
| Code blocks | Preserve | Preserve |
| Inline code | Preserve | Preserve (technical terms) |
| Tags | Translate | Translate |
| Bold/emphasis | Preserve original | Translate |

### Examples

**Structure-only (English headers, Chinese content):**

Input:
```
技巧 1：使用動詞

使用動作動詞可以讓描述更清楚。常見的動詞包括 create、fix、review。
```

Output:
```markdown
## Technique 1: Use Verbs

使用動作動詞可以讓描述更清楚。常見的動詞包括 create、fix、review。
```

**Full-translation (English):**

Input:
```
技巧 1：使用動詞

使用動作動詞可以讓描述更清楚。常見的動詞包括 create、fix、review。
```

Output:
```markdown
## Technique 1: Use Verbs

Using action verbs makes descriptions clearer. Common verbs include create, fix, and review.
```

### Confirmation Messages

Before processing, confirm detected settings:
```
"Processing document: English headers, Traditional Chinese content (structure-only mode)"
"Processing document: Full translation to English"
"Processing document: Original language preserved (structure-only mode)"
```
```

#### 3. Quick Reference Table Update

Add Language column:

```markdown
| Element | When to Add | Pattern to Match | Language Handling |
|---------|-------------|------------------|-------------------|
| H1 | Main topic | Document title/theme | Follow mode setting |
| H2 | Major sections | Distinct topics, emojis | Follow mode setting |
| Table | Comparisons | ❌ vs ✅, attributes | Headers follow mode, content based on mode |
| Code block | Config, commands | `---` + `name:`, starts with `/` | Always preserve |
```

#### 4. Rationalization Table Update

Add:
```markdown
| "User didn't specify language, so I'll use English" | Use original language as default, ask if unclear |
| "Structure-only means I don't translate anything" | Structure elements (headers, labels) should be translated |
| "Full-translation means translate code blocks too" | Code blocks always preserved, only prose translated |
```

#### 5. Error Handling Updates

Add to Error Handling chapter:

```markdown
### Language & Mode Errors

**Unsupported language:**
- If Claude cannot translate to requested language
- Error: "無法翻譯到 [language]。建議使用常見語言如英文、繁體中文、日文等。"
- Fallback: Ask user to choose another language

**Ambiguous request:**
- If cannot determine language or mode from request
- Ask clarifying question with AskUserQuestion
- Don't assume - explicit is better

**Translation quality issues:**
- If full-translation produces unclear results
- Note in output: "Note: Translation may need manual review for technical accuracy"
- Suggest structure-only mode as alternative

**Mixed content handling:**
- If document has mixed languages
- Detect primary language as default
- Note: "Detected mixed content - using [language] as primary"
```

### Testing Strategy

#### Test Cases

1. **Structure-only + English**
   - Input: 繁中內容
   - Expected: 英文標題 + 繁中內容

2. **Structure-only + Traditional Chinese**
   - Input: 英文內容
   - Expected: 繁中標題 + 英文內容

3. **Full-translation + English**
   - Input: 繁中全文
   - Expected: 英文全文（結構化）

4. **Full-translation + Traditional Chinese**
   - Input: 英文全文
   - Expected: 繁中全文（結構化）

5. **Default (no specification)**
   - Input: 任何語言
   - Expected: 保持原文語言，structure-only

6. **Interactive flow - missing language**
   - Input: "翻譯並結構化"
   - Expected: 詢問目標語言

7. **Interactive flow - missing mode**
   - Input: "用英文結構化"
   - Expected: 詢問 structure-only vs full-translation

8. **Natural language variations**
   - "translate to Japanese"
   - "用日文"
   - "English headers"
   - All should be correctly parsed

#### Edge Cases

- Code-heavy documents (preserve all code)
- Mixed language content (detect primary)
- Technical terms in translation (preserve or translate appropriately)
- Empty document (no language to detect)

### Documentation Updates

#### README.md

Add section:

```markdown
## Language Support

markdown-structurer supports multiple languages with two modes:

**Structure-only mode:**
- Translates headers, labels, and structural elements
- Preserves original content text
- Example: "結構化這份文件，使用英文標題"

**Full-translation mode:**
- Translates entire document
- Maintains code blocks and technical terms
- Example: "翻譯成英文並結構化"

**Supported languages:**
Any language Claude understands - English, Traditional Chinese, Japanese, Korean, etc.

**Default behavior:**
If language not specified, preserves original language.
```

#### Examples Directory

Consider adding:
- `examples/translation-structure-only.md` - 展示 structure-only 模式
- `examples/translation-full.md` - 展示 full-translation 模式

## Trade-offs & Decisions

### Decision 1: Natural language vs parameter syntax
**Chosen:** Natural language
**Rationale:** Fits Claude Code's conversational interface better
**Trade-off:** May require clarification questions, but more user-friendly

### Decision 2: Support bilingual output?
**Chosen:** No (single language only)
**Rationale:** Simplifies implementation, user can run twice for two versions
**Trade-off:** Less convenient for bilingual docs, but keeps scope manageable

### Decision 3: Predefined language list?
**Chosen:** No (free-form description)
**Rationale:** Leverages Claude's multilingual capabilities, more flexible
**Trade-off:** Cannot validate language support upfront, but more future-proof

### Decision 4: Default behavior
**Chosen:** Preserve original language, structure-only mode
**Rationale:** Least surprising, maintains backward compatibility
**Trade-off:** Users wanting translation must specify explicitly

## Success Criteria

- [ ] Users can specify language via natural language
- [ ] Structure-only mode correctly translates only structural elements
- [ ] Full-translation mode correctly translates entire document
- [ ] Default behavior (no specification) works as before
- [ ] Interactive clarification works smoothly
- [ ] All test cases pass
- [ ] Documentation updated (SKILL.md, README.md)
- [ ] Examples demonstrate both modes

## Future Enhancements (Out of Scope)

- Bilingual output support (side-by-side, primary-secondary)
- Glossary/dictionary for consistent term translation
- Language detection confidence scoring
- Batch processing multiple files
- Custom translation rules per project

## Implementation Plan

See separate implementation plan document (to be created after design approval).

## Related Documents

- Original SKILL.md: `/Users/tom_wang/.claude/skills/markdown-structurer/SKILL.md`
- TDD process: Documented in git history (RED-GREEN-REFACTOR)
- Audit report: `markdown-structurer-audit-report.md`
