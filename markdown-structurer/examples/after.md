# 如何保證 Skill 能被 AI 調用？

> **Tags:** `skill-development` `description-writing` `triggers` `best-practices` `claude-code`

## 簡短答案

沒有專門的 `keywords` 欄位，但你應該在 `description` 中明確寫出關鍵字和觸發場景。

## 最佳實踐：在 description 中寫關鍵字

### 策略 1：直接列出觸發關鍵字

```yaml
---
name: deploy-production
description: Deploy application to production environment. Keywords: deploy, push to production, release, go live
disable-model-invocation: true
---
```

### 策略 2：描述使用時機（推薦）⭐

```yaml
---
name: create-api-endpoint
description: Create a new REST API endpoint following project conventions. Use when user asks to "create an endpoint", "add API route", "build new API", or "make a GET/POST endpoint"
---
```

## 提高觸發率的技巧

### 1. 使用動詞 + 名詞組合

**範例：**
```yaml
description: Create git commit with conventional commit message. Triggers: commit, create commit, save changes, commit code
```

**常見動詞：**

| 類別 | 動詞 |
|------|------|
| 創建 | create, build, make, add |
| 修復 | fix, resolve, repair |
| 檢查 | review, check, validate |
| 部署 | deploy, push, release |
| 分析 | analyze, investigate, explore |

### 2. 包含同義詞

```yaml
description: Deploy application (synonyms: push, release, ship, publish, launch to production)
```

### 3. 列出常見錯誤表達

```yaml
description: |
  Fix TypeScript errors and type issues.
  Use when user mentions: "TS error", "type error", "TypeScript complaining", "red squiggly lines", "type mismatch"
```

## 驗證 Skill 可被觸發

### 方法 1：使用 `/context` 檢查

執行：
```bash
/context
```

**查看輸出：**
- ✅ Skill `description` 出現在 "Available skills" 區塊
- ❌ Skill 出現在 "Excluded skills"（超過字元預算）

### 方法 2：測試觸發

說出 `description` 中的關鍵字：

**範例：**
```
你：「幫我 review 這段 code」
→ 如果 description 包含 "review" 和 "code"，應該會觸發
```

## 常見陷阱

### 陷阱 1：Description 太籠統

| 錯誤 | 正確 |
|------|------|
| `description: Help with code`<br>會在任何程式碼討論時觸發 | `description: Refactor code following SOLID principles. Use when user explicitly asks to "refactor" or "improve code structure"`<br>明確使用場景 |

### 陷阱 2：只有關鍵字沒有上下文

| 錯誤 | 正確 |
|------|------|
| `description: Keywords: deploy, push, release`<br>Claude 不知道何時用 | `description: Deploy to production. Use when tests pass and user confirms ready to deploy. Keywords: deploy, push to prod, go live`<br>關鍵字 + 使用場景 |

## 總結

雖然沒有專門的 `keywords` 欄位，但通過在 `description` 中：

1. ✅ 明確列出關鍵字
2. ✅ 描述使用場景
3. ✅ 提供範例語句
4. ✅ 包含同義詞

可以大幅提高 Skill 被正確觸發的機率！
