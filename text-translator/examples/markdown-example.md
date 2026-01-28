# Markdown Translation Example

This example demonstrates translation while preserving Markdown structure and code.

## Original (Traditional Chinese)

```markdown
# API 使用指南

## 快速開始

首先安裝套件：

```bash
npm install api-client
```

然後初始化：

```javascript
const client = new APIClient({
  apiKey: 'your-key',
  baseURL: 'https://api.example.com'
});
```

## 主要功能

### 驗證

使用 `authenticate()` 方法進行驗證：

```javascript
await client.authenticate();
```

### 發送請求

| 方法 | 用途 | 回應格式 |
|------|------|---------|
| `get()` | 取得資料 | JSON |
| `post()` | 建立資料 | JSON |
| `delete()` | 刪除資料 | Status code |

## 注意事項

- 確保 API key 有效
- 所有請求使用 HTTPS
- 處理錯誤回應

> **重要：** 不要將 API key 提交到版本控制系統。
```

## Translated (English)

**User request:** "translate to English"

**Result:**

```markdown
# API Usage Guide

## Quick Start

First, install the package:

```bash
npm install api-client
```

Then initialize:

```javascript
const client = new APIClient({
  apiKey: 'your-key',
  baseURL: 'https://api.example.com'
});
```

## Main Features

### Authentication

Use the `authenticate()` method for authentication:

```javascript
await client.authenticate();
```

### Sending Requests

| Method | Purpose | Response Format |
|--------|---------|-----------------|
| `get()` | Retrieve data | JSON |
| `post()` | Create data | JSON |
| `delete()` | Delete data | Status code |

## Important Notes

- Ensure API key is valid
- All requests use HTTPS
- Handle error responses

> **Important:** Do not commit API key to version control system.
```

## Key Points

- ✅ All headers translated
- ✅ All paragraphs and list items translated
- ✅ Table content translated
- ✅ **Code blocks completely preserved** (bash, javascript)
- ✅ **Inline code preserved** (`authenticate()`, `get()`, etc.)
- ✅ Technical terms preserved (API, JSON, HTTPS, API key)
- ✅ Blockquote content translated
- ✅ Markdown structure maintained

## Preservation Details

**What was NOT translated:**
- Code blocks: 3 blocks (bash, 2x javascript)
- Inline code: `authenticate()`, `get()`, `post()`, `delete()`
- Technical terms: API, JSON, HTTPS, API key, Status code
- URLs: https://api.example.com
- Code variables: apiKey, baseURL, client

**What WAS translated:**
- Headers: "API 使用指南" → "API Usage Guide"
- Paragraphs: All descriptive text
- Lists: "確保 API key 有效" → "Ensure API key is valid"
- Tables: Headers and content
- Blockquotes: "重要：不要將..." → "Important: Do not commit..."
