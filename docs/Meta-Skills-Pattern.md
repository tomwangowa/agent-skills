# Meta-Skills Design Pattern

> **Document Status (2026-04):** This is a design-thinking document that explores the *pattern* of routing across multiple similar skills. It uses the code-review family as the running example.
>
> Specific defaults referenced in the examples below were updated in 2026-04: `code-review-claude` is now the **default reviewer** and the **pre-commit auto-reviewer** (not Gemini, as older examples here may say). Routing reason: the 2026-04 n=6 benchmark showed Claude broader coverage (2.3×–5.0×) + 0/6 verified hallucinations vs. Gemini's 3/6 P0/P1 hallucinations.
>
> The *pattern* described below (meta-skill router, fallback chains, context-aware dispatch) is still valid — just read the concrete routing table in the current `global/CLAUDE.md` and `skill-router/skill-registry.yaml` as the authoritative source, not the examples baked into this doc.

## 概述

**Meta-Skill Pattern** 是一種進階的 Claude Code Skills 架構設計模式，用於解決當多個 skills 提供相似功能時的選擇和路由問題。

**適用場景：**
- 存在多個提供類似功能但實作方式不同的 skills
- 需要根據情境自動選擇最佳工具
- 希望提供統一的用戶介面而隱藏底層複雜度

---

## 問題陳述

### 場景：多個 Code Review Skills

假設你有三個程式碼審查 skills：

1. **code-review-claude** - 快速內建審查（< 30 秒）
2. **code-review-gemini** - 深度外部視角審查（使用 Gemini AI）
3. **code-review-checklist** - 結構化人工檢查清單

### 挑戰

**用戶困境：**
- "我應該用哪一個？"
- "什麼情境下該用哪個工具？"
- "我需要記住三個不同的觸發詞嗎？"

**維護困境：**
- Skills 功能重疊造成混淆
- 難以設定「預設」或「偏好」
- 新增第四個 reviewer 時，複雜度倍增

---

## 解決方案：Meta-Skill + Preferences

### 架構概覽

```
用戶請求
    ↓
Meta-Skill (Dispatcher)
    ↓
[讀取 CLAUDE.md 偏好設定]
    ↓
[分析情境：檔案大小、複雜度、時間限制]
    ↓
路由到適當的 Skill
    ↓
    ├─→ code-review-claude
    ├─→ code-review-gemini
    └─→ code-review-checklist
```

### 組成元素

#### 1. Meta-Skill (Dispatcher)

**檔案位置：** `code-reviewer/SKILL.md`

**職責：**
- 接收用戶統一的觸發指令
- 讀取用戶偏好設定
- 分析當前情境
- 選擇並呼叫適當的底層 skill

**範例實作：**

```yaml
---
name: code-reviewer
description: Intelligent code review dispatcher - automatically selects best reviewer
---

# code-reviewer (Meta-Skill)

## Purpose
Automatically routes code review requests to the most appropriate reviewer based on context and user preferences.

## Trigger Phrases
- "review", "code review", "review my code"
- "check the code", "review changes"

## Decision Logic

### Step 1: Check User Preferences
Read from `~/.claude/CLAUDE.md` section 9 (Notice):
- Preferred reviewer
- Fallback options
- Context-specific overrides

### Step 2: Analyze Context
- **File count**: Number of staged/modified files
- **Line count**: Total lines changed
- **Complexity**: Language, framework usage
- **Time constraint**: User mentions "quick" or "thorough"

### Step 3: Route to Appropriate Skill

| Condition | Route To | Reason |
|-----------|----------|--------|
| User preference explicitly set | Preferred skill | Respect user choice |
| Default case | code-review-claude | 2026-04 benchmark: broader coverage, 0/6 verified hallucinations |
| User asks for "deep", "thorough", "gemini", or "refactored patch" | code-review-gemini | Depth / refactored-patch / optional second opinion |
| Pre-commit auto-review | code-review-claude | As of 2026-04: pre-commit is highest-cost for hallucinations, routes to benchmark-most-reliable reviewer |
| User says "checklist" | code-review-checklist | Explicit request |

### Step 4: Execute & Report
1. Invoke the selected skill using the Skill tool
2. Report to user: "Using {skill_name} for this review..."
3. Pass through the results

## Examples

**Example 1: Quick review**
```
User: "Quick review of my changes"
Meta: Analyzing... 23 lines changed, user wants speed
Meta: Using code-review-claude (fast, < 30s)
→ Executes code-review-claude
```

**Example 2: Default review**
```
User: "Review my code"
Meta: Analyzing... no depth keyword → default path
Meta: Using code-review-claude (default reviewer, 2026-04)
→ Executes code-review-claude
```

**Example 3: Explicit choice**
```
User: "Give me the review checklist"
Meta: User explicitly requested checklist
Meta: Using code-review-checklist
→ Executes code-review-checklist
```

## Implementation Notes

- The meta-skill does NOT duplicate functionality
- It only handles routing logic
- All actual review work is done by specialized skills
- User can still call specialized skills directly if needed
```

#### 2. User Preferences (in CLAUDE.md)

**檔案位置：** `~/.claude/CLAUDE.md`

在 Section 9 (Notice) 中加入：

```markdown
## 9. Notice
...existing content...

### Skill Preferences

#### Code Review
- **Default reviewer**: code-review-claude (as of 2026-04)
- **Depth / refactored patch / external second opinion**: code-review-gemini
- **Pre-commit auto-review**: code-review-claude (as of 2026-04; pre-commit is highest-cost hallucination scenario, so it uses the most reliable reviewer)
- **Learning mode**: code-review-checklist
- **Rationale**: 2026-04 benchmark showed Claude's native reviewer had broader coverage (2.3×–5.0× Gemini's findings) and 0/6 verified hallucinations vs. Gemini's 3/6 P0/P1 hallucinations; Gemini remains valuable for fully worked refactored patches and cross-model second opinions

#### [Other skill categories can be added here]
```

---

## 設計原則

### 1. 單一入口點 (Single Entry Point)
- 用戶只需記住一個觸發詞："review my code"
- 減少認知負擔

### 2. 功能互補而非重疊 (Complementary, Not Redundant)
每個底層 skill 應該有明確的獨特價值：
- **code-review-claude**: 預設 reviewer — 廣度、adversarial、assumptions、syntax 驗證，0 hallucination（2026-04 benchmark）
- **code-review-gemini**: 選配 — 外部模型視角、完整 refactored patch 生成
- **code-review-checklist**: 教學用途

### 3. 決策透明化 (Transparent Decision Making)
Meta-skill 應該告知用戶：
- "Using gemini for this review..."
- 讓用戶理解為何選擇這個工具

### 4. 保留直接存取 (Direct Access Preserved)
用戶仍可直接呼叫特定 skill：
- `/skill code-review-gemini` (繞過 meta-skill)
- 不會因為 meta-skill 而失去控制權

### 5. 偏好可覆寫 (Preferences Override-able)
情境可以覆寫預設偏好：
- 用戶說 "gemini review" 或 "refactored patch" → 即使預設是 claude，也改派 gemini
- 尊重當下的需求

---

## 實作步驟

### Step 1: 識別重疊的 Skills
```bash
# 列出所有 skills，找出功能相似的
ls ~/.claude/skills/ | grep "review"
```

### Step 2: 分析差異性
為每個 skill 定義獨特價值：
| Skill | 獨特價值 | 使用場景 |
|-------|----------|----------|
| skill-a | 速度 | 快速檢查 |
| skill-b | 深度 | 完整審查 |
| skill-c | 教學 | 學習用途 |

### Step 3: 創建 Meta-Skill
```bash
mkdir ~/.claude/skills/code-reviewer
```

撰寫 `SKILL.md`，參考上面的範例。

### Step 4: 定義偏好設定
在 `~/.claude/CLAUDE.md` 加入偏好設定。

### Step 5: 測試路由邏輯
```bash
# 測試不同情境
claude "review my code"          # 應該使用預設
claude "quick review"            # 應該使用快速版本
claude "give me review checklist" # 應該使用檢查清單
```

### Step 6: 文檔化
更新 README，說明：
- Meta-skill 的存在
- 如何自訂偏好
- 如何直接存取特定 skill

---

## 最佳實踐

### ✅ 應該做的

1. **清楚命名**
   - Meta-skill: `code-reviewer` (通用名稱)
   - Specialized skill: `code-review-gemini` (明確實作)

2. **文檔化決策邏輯**
   - 在 meta-skill 中用表格說明路由規則
   - 讓其他人可以理解和修改

3. **提供覆寫機制**
   - 允許用戶在 CLAUDE.md 中設定偏好
   - 允許情境關鍵字覆寫（如 "quick"）

4. **保持簡單**
   - 路由邏輯不要超過 5-7 條規則
   - 如果太複雜，考慮減少 skill 數量

5. **告知用戶**
   - Meta-skill 應該輸出："Using code-review-gemini for this review..."
   - 提高透明度

### ❌ 不應該做的

1. **複製功能**
   - Meta-skill 不應該包含任何實際的審查邏輯
   - 只做路由，不做工作

2. **隱藏錯誤**
   - 如果底層 skill 失敗，應該透明地報告
   - 不要靜默切換到另一個 skill

3. **過度工程**
   - 不需要複雜的 AI 決策
   - 簡單的 if-then 規則就足夠

4. **強制使用**
   - 不要禁止用戶直接呼叫特定 skill
   - Meta-skill 是輔助，不是限制

---

## 進階模式

### 模式 A：分層 Meta-Skills

```
meta-reviewer (頂層)
    ├─→ code-reviewer (程式碼)
    │       ├─→ code-review-claude
    │       └─→ code-review-gemini
    │
    └─→ design-reviewer (設計)
            ├─→ ui-design-analyzer
            └─→ accessibility-checker
```

**適用場景：** 有多個類別的審查工具

### 模式 B：Context-Aware Routing

根據專案類型自動選擇：
```yaml
# In CLAUDE.md
## Project Context
current_project: frontend-react

## Skill Routing Rules
when:
  project: frontend-react
  task: review
then:
  use: code-review-gemini
  reason: Better at React patterns
```

### 模式 C：Fallback Chain

定義失敗時的備援方案：
```
嘗試 code-review-gemini
  ├─ 成功 → 完成
  └─ 失敗 → 嘗試 code-review-claude
            ├─ 成功 → 完成
            └─ 失敗 → 使用 code-review-checklist (永遠可用)
```

---

## 何時使用 / 不使用

### ✅ 使用 Meta-Skill 當：

1. **有 2+ 個功能相似的 skills**
   - 例如：3 個 code reviewers

2. **用戶經常需要選擇**
   - "我應該用哪一個？" 是常見問題

3. **選擇邏輯清晰且穩定**
   - 可以用簡單規則表達
   - 不會經常改變

4. **希望提供統一的用戶體驗**
   - 對外隱藏內部複雜度

### ❌ 不使用 Meta-Skill 當：

1. **只有 1 個 skill**
   - 沒有選擇問題

2. **Skills 功能完全不同**
   - 例如：code-review vs commit-message
   - 沒有路由需求

3. **選擇邏輯過於複雜**
   - 需要 AI 推理才能決定
   - 不如讓用戶直接選擇

4. **用戶偏好非常個人化**
   - 每次都不同
   - 沒有預設值的意義

---

## 實例研究：Code Reviewer Meta-Skill

### 背景
有三個 code review skills，用戶不知道何時該用哪一個。

### 實作

**1. 創建 meta-skill**
```bash
mkdir ~/.claude/skills/code-reviewer
```

**2. 定義路由邏輯 (code-reviewer/SKILL.md)**
```markdown
## Decision Logic

1. Check CLAUDE.md preferences (default: claude, as of 2026-04)
2. If user says "gemini" / "refactored patch" → use gemini
3. If user says "checklist" → use checklist
4. Otherwise → use preference
```

**3. 設定偏好 (CLAUDE.md)**
```markdown
### Code Review
- Default: code-review-claude
- Deep / refactored-patch fallback: code-review-gemini
```

**4. 測試**
```bash
# Test 1: Default routing
claude "review my code"
# Expected: Uses code-review-claude (default, 2026-04)

# Test 2: Quick override
claude "quick review"
# Expected: Uses claude

# Test 3: Explicit request
claude "show me the review checklist"
# Expected: Uses checklist
```

### 結果
- 用戶只需記住 "review my code"
- 大多數情況使用 claude（預設，2026-04 起）
- 需要外部視角或 refactored patch 時切換到 gemini
- 學習時可明確要求 checklist
- 減少選擇疲勞，提高效率

---

## 總結

**Meta-Skill Pattern 的核心價值：**

1. **簡化用戶體驗** - 單一入口點
2. **智能路由** - 自動選擇最佳工具
3. **尊重偏好** - 可自訂預設行為
4. **保持靈活** - 可覆寫、可直接存取
5. **易於擴展** - 新增 skill 時，只需更新路由邏輯

**記住：** Meta-skill 不是為了複雜化，而是為了簡化。如果你發現自己在寫複雜的路由邏輯，可能需要重新思考 skills 的劃分。

---

## 相關文檔

- [Skills Roadmap](../SKILLS_ROADMAP.md)
- [UI/UX Skills 架構方案](./UI-UX-Skills-Plan.md)

---

**版本：** 1.1
**創建日期：** 2026-01-22
**更新日期：** 2026-02-12
**作者：** Tom Wang
**狀態：** Archived — `code-reviewer` meta-skill 已於 2026-02-12 退役，路由邏輯已移至 `~/.claude/CLAUDE.md` 中的指令。本文保留作為設計模式參考。
