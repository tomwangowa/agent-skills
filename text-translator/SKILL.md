---
name: text-translator
description: Translate text content to target language. For Markdown files, preserves structure and code. Triggers on "translate to", "翻譯成", "convert to". Supports any language Claude understands.
---

# Text Translator

## Overview

Translates text content to target language while intelligently preserving technical elements.

**Handles multiple formats:**
- **Plain text:** Direct translation
- **Markdown:** Preserves structure (headers, lists, tables) and code blocks
- **Other text files:** Full translation

**Core principle:** Translate content while preserving code and technical formatting.

## When to Use

**Use this skill when:**
- Need document in different language
- Working with multilingual documentation
- Preparing content for international audiences
- Converting notes to target language

**Do NOT use for:**
- Code-only files (no translation needed)
- Binary files
- Already in target language

## Language Detection

**From user request:**

Natural language keywords are parsed to detect target language:
- English: "English", "英文", "en", "in English", "translate to English"
- Traditional Chinese: "Traditional Chinese", "繁體中文", "繁中", "zh-TW"
- Japanese: "Japanese", "日文", "日本語", "ja"
- Korean: "Korean", "韓文", "한국어", "ko"
- Spanish: "Spanish", "西班牙文", "español", "es"
- French: "French", "法文", "français", "fr"
- German: "German", "德文", "Deutsch", "de"
- Others: Any language description Claude understands

**If not specified:**
- Ask user: "要翻譯成什麼語言？"
- Provide common options: (1) 英文 (2) 繁體中文 (3) 日本語 (4) 其他

**Confirmation:**
Before translating, confirm detected language:
```
"Translating to English..."
"翻譯成繁體中文中..."
"日本語に翻訳します..."
```

## Translation Rules

### Format Detection

**Automatic detection:**
- Check for Markdown markers (`#`, ` ``` `, `- `, `| |`)
- If Markdown detected → Apply Markdown preservation rules
- If no Markdown → Treat as plain text

### Plain Text Translation

**Rules:**
- Translate all content directly
- Preserve line breaks and paragraph structure
- No special handling needed

### Markdown Translation

**Element handling:**

| Element | Action | Example |
|---------|--------|---------|
| Headers (`#`, `##`, `###`) | Translate text | `## 技巧` → `## Techniques` |
| Paragraphs | Translate content | Full paragraph translation |
| Lists (`-`, `*`, `1.`) | Translate items | `- 使用動詞` → `- Use verbs` |
| Tables | Translate cell content | All cells translated |
| Bold/Italic (`**`, `*`) | Translate marked text | `**重要**` → `**Important**` |
| Links (`[text](url)`) | Translate text, preserve URL | `[文檔](url)` → `[Documentation](url)` |
| Code blocks (` ``` `) | **Preserve completely** | No changes to code |
| Inline code (`` ` ``) | **Preserve completely** | `` `variableName` `` unchanged |
| Blockquotes (`>`) | Translate content | `> 注意` → `> Note` |

### Technical Term Preservation

**Always preserve:**
- Common acronyms: API, HTTP, REST, CRUD, SQL, JSON, XML, HTML, CSS
- Proper nouns: GitHub, Claude, React, Python, JavaScript
- Programming keywords: function, class, return, import, export
- Technical commands: git, npm, bash, curl
- File extensions: .md, .py, .js, .json

**Translate:**
- Descriptive text and explanations
- General concepts (not technical jargon)
- User-facing content

**When uncertain:**
- Preserve technical terms by default (safer)
- Note: "Some technical terms preserved for accuracy"

## Workflow

### Step-by-Step

1. **Parse language intent**
   - Extract language keywords from user request
   - If unclear → Ask user with AskUserQuestion
   - Confirm target language to user

2. **Read content**
   - Use Read tool to load file
   - Or accept content directly from calling skill

3. **Detect format**
   - Check for Markdown markers
   - Set preservation rules accordingly

4. **Translate content**
   - Apply translation to appropriate elements
   - Preserve code blocks and inline code
   - Preserve technical terms
   - Maintain structure

5. **Output result**
   - Use Write or Edit tool (if file-based)
   - Or return translated content (if called by other skill)
   - Confirm completion to user

## Examples

### Example 1: Plain Text Translation

**Input:**
```
這是一段技術說明。我們使用 API 來處理 HTTP 請求。系統會返回 JSON 格式的回應。
```

**User request:**
```
"翻譯成英文"
```

**Output:**
```
This is a technical description. We use API to handle HTTP requests. The system returns JSON formatted responses.
```

**Note:** API, HTTP, JSON preserved as technical terms.

### Example 2: Markdown Translation

**Input:**
```markdown
## 安裝指南

使用以下指令安裝：

```bash
npm install package-name
```

常見問題：
- 確保 Node.js 已安裝
- 檢查網路連線
```

**User request:**
```
"translate to English"
```

**Output:**
```markdown
## Installation Guide

Install using the following command:

```bash
npm install package-name
```

Common issues:
- Ensure Node.js is installed
- Check network connection
```

**Note:** Code block completely preserved, Markdown structure maintained.

### Example 3: Technical Document Translation

**Input:**
```markdown
# API 使用說明

## 驗證方式

使用 OAuth 2.0 進行驗證。首先取得 access token：

```javascript
const token = await getAccessToken();
```

然後在 header 中加入 `Authorization: Bearer ${token}`。
```

**User request:**
```
"translate to Japanese"
```

**Output:**
```markdown
# API 使用説明

## 認証方法

OAuth 2.0 を使用して認証します。まず access token を取得します：

```javascript
const token = await getAccessToken();
```

その後、header に `Authorization: Bearer ${token}` を追加します。
```

**Note:** OAuth 2.0, access token, header, Authorization, Bearer preserved. Code blocks unchanged. Inline code preserved.

## Error Handling

### Language Detection Errors

**Unsupported or unclear language:**
- Error message: "無法確認翻譯目標語言。請明確指定語言，例如：英文、繁體中文、日文等。"
- Action: Ask user to specify language with AskUserQuestion

**No language specified:**
- Ask user: "要翻譯成什麼語言？
  (1) 英文 (English)
  (2) 繁體中文 (Traditional Chinese)
  (3) 日本語 (Japanese)
  (4) 한국어 (Korean)
  (5) 其他（請輸入語言名稱）"

### Content Processing Errors

**File not found:**
- Check file path is correct
- Error: "File not found at [path]. Please verify the path."

**Empty content:**
- Error: "Content is empty. Nothing to translate."

**Translation quality issues:**
- Complete translation anyway
- Add warning: "Note: Translation completed. Please review for technical accuracy."
- Suggest manual review for critical documents

**Mixed language detection:**
- Translate all text portions
- Note: "Detected mixed language content - translated all text portions"

**Format detection failure:**
- Fallback to plain text translation
- Note: "Processed as plain text"

### Graceful Degradation

**If translation partially fails:**
- Output what was successfully translated
- Mark untranslated sections with: `[Translation failed: original text]`
- Inform user: "Partial translation completed. Some sections could not be translated."

## Integration

### Called by Other Skills

**markdown-structurer integration:**

markdown-structurer can automatically call text-translator when it detects translation keywords:

```markdown
User: "翻譯成英文並結構化"

markdown-structurer:
1. Detects "翻譯" + "英文"
2. Calls text-translator(target=English, content=original)
3. Receives translated content
4. Applies structuring rules
5. Outputs structured English document
```

**Standalone usage:**

```markdown
User: "翻譯這份文件成英文"

text-translator:
1. Detects target=English
2. Reads file
3. Translates with Markdown preservation
4. Outputs translated file
```

### Return Format (for calling skills)

When called by other skills, return:
```
{
  "translated_content": "...",
  "source_language": "Traditional Chinese",
  "target_language": "English",
  "format": "markdown",
  "notes": ["Preserved 3 code blocks", "Preserved 12 technical terms"]
}
```

## Security Considerations

### Input Validation

- Validate file paths (no directory traversal)
- Check file size (max 10MB recommended)
- Sanitize user input in language requests

### Safe Operations

- Read-only by default
- Confirm before overwriting files
- Don't execute embedded code
- Validate file extensions

### Content Safety

- Don't translate credentials or secrets in code blocks
- Preserve security-sensitive code comments
- Don't alter security configurations

## Rationalization Table

| Excuse | Reality |
|--------|---------|
| "No language specified, so I'll use English" | Ask user to specify target language |
| "Code comments should be translated too" | Code blocks preserved completely, including comments |
| "Inline code is just text" | Inline code preserved - it's technical syntax |
| "Technical terms should be translated for clarity" | Preserve technical terms - they're standardized internationally |
| "User said translate, so translate everything" | Code and technical syntax always preserved |
| "Mixed languages are confusing, I'll pick one" | Translate all text, note mixed content to user |

## Common Mistakes

### ❌ Mistake 1: Translating code blocks

**Problem:** Translating code content breaks functionality.

**Bad example:**
```javascript
// Before
function getUserData() {
  return data;
}

// After (WRONG)
function 取得使用者資料() {
  return 資料;
}
```

**Fix:** Code blocks NEVER translated, regardless of language.

### ❌ Mistake 2: Translating inline code

**Problem:** Technical terms in inline code lose meaning.

**Bad example:**
```
Use `getUser` function → 使用 `取得使用者` 函式
```

**Fix:** Preserve inline code completely.

### ❌ Mistake 3: Translating technical acronyms

**Problem:** API, HTTP, REST are international standards.

**Bad example:**
```
Use the API → 使用應用程式介面
```

**Fix:** Preserve technical acronyms: "Use the API" → "使用 API"

### ❌ Mistake 4: Breaking Markdown structure

**Problem:** Changing Markdown syntax during translation.

**Bad example:**
```
## 標題 → ## Title (missing # count, wrong spacing)
- 項目 → * Item (changed list marker)
```

**Fix:** Preserve exact Markdown syntax, only translate text content.

### ❌ Mistake 5: Not asking for language

**Problem:** Assuming target language without confirmation.

**Fix:** Always ask if target language unclear from request.
