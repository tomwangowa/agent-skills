# Code Story Teller

Analyze git history to tell the evolutionary story of your code. Understand why code exists, how it evolved, and what design decisions shaped it.

## Features

- **Narrative History** - Tells the story of code evolution in an engaging way
- **Design Insights** - Explains architectural decisions and their rationale
- **Timeline View** - Shows major milestones chronologically
- **Pattern Detection** - Identifies recurring themes and evolution patterns
- **Contributor Analysis** - Highlights key contributors and their impact
- **Traditional Chinese Output** - Easy to understand for Chinese-speaking teams

## Dependencies

- Git repository with commit history
- Claude Code (analysis runs natively inside Claude — no external API keys required)

## Usage

The skill is invoked in Claude Code using natural language. Point it at a single file you want to understand:

```
> Tell me the story of src/api/auth.js
> Show me how database/models/user.js evolved
> Explain the history of this file
```

The skill then:

1. Verifies the file is tracked by git
2. Collects up to the 20 most recent commits (`git log --follow -p`)
3. Analyzes origin, milestones, design decisions, contributors
4. Reads the current file for comparison
5. Presents a structured narrative (see *Output Format* in `SKILL.md`)

## Example Output

```
================ Code Story ================

檔案起源故事
───────────
這個驗證模組誕生於 2023 年 3 月，當時專案需要從簡單的 session-based
認證遷移到更安全的 JWT 機制。原始作者 John Doe 建立了第一版，
包含基本的登入和登出功能。

演化時間軸
─────────
📅 2023-03-15: 初始版本 - 實作基本 JWT 認證
📅 2023-05-20: 重要轉折 - 加入 refresh token 機制
📅 2023-08-10: 安全強化 - 實作 token rotation 防止重放攻擊
📅 2024-01-12: 架構重構 - 將驗證邏輯抽離成獨立服務

設計決策
───────
• JWT vs Session: 選擇 JWT 因為需要支援多個前端應用
• Refresh Token: 採用 rotation 策略，平衡安全性與使用者體驗
• Token 儲存: 使用 httpOnly cookie，防止 XSS 攻擊
...

============================================
```

## Use Cases

### 1. Understanding Legacy Code

**Scenario:** You inherit a complex module and need to understand it.

```
> Tell me the story of src/legacy/payment-processor.js
```

**Benefits:**
- Understand original design intent
- See how requirements changed
- Learn from past decisions
- Identify technical debt sources

### 2. Pre-Refactoring Research

**Scenario:** Planning a major refactoring.

```
> Tell me the story of src/core/data-processor.js
```

**Benefits:**
- Understand why current design exists
- Learn from previous refactoring attempts
- Avoid repeating past mistakes
- Make informed decisions

### 3. Code Review Context

**Scenario:** Reviewing a complex PR.

```
> Tell me the story of src/components/UserProfile.jsx
```

**Benefits:**
- See if changes align with historical patterns
- Understand the file's evolution direction
- Provide more contextual feedback

### 4. Onboarding New Developers

**Scenario:** New team member needs to understand the codebase.

```
> Tell me the story of src/api/index.js
> Now tell me the story of src/database/schema.js
```

**Benefits:**
- Faster onboarding
- Understand architectural decisions
- Learn team's coding patterns
- See who to ask for help

### 5. Documentation Generation

**Scenario:** Creating technical documentation.

```
> Tell me the story of src/core/engine.js and save the result to docs/engine-history.md
```

**Benefits:**
- Auto-generated context documentation
- Architecture Decision Records (ADRs)
- Historical context for future developers

## Behavior

- **Commit depth:** The skill analyzes up to the 20 most recent commits per file (hard-coded in `SKILL.md` to avoid context overflow). For longer windows, ask Claude to split the analysis by date range — see *Advanced Usage* below.
- **Rename handling:** `git log --follow` tracks renames automatically.
- **Language:** Narrative in Traditional Chinese, technical terms / commit hashes / dates in English. Ask in English to override.

## Tips & Best Practices

### 1. Start with Core Files

Analyze the most important files first:
- Main entry points
- Core business logic
- Frequently modified files
- Complex modules

### 2. Look for Patterns

When analyzing multiple files, look for:
- Similar evolution patterns
- Common refactoring themes
- Shared contributors
- Architectural trends

### 3. Share with Your Team

Generated stories are valuable documentation:
- Add to project wiki
- Include in onboarding materials
- Share in code review discussions
- Use for technical talks

### 4. Combine with Other Tools

Use alongside other skills:
- **Before refactoring:** Tell story → Make changes → Review with code-review-claude (default; chain code-review-gemini afterwards for a refactored patch)
- **After major work:** Tell story → Commit with Conventional Commits format
- **For releases:** Tell story → Use for release notes

### 5. Regular Analysis

Periodically analyze key files:
- After major releases
- When technical debt grows
- During architecture reviews
- For quarterly retrospectives

## Troubleshooting

### "No commit history found"

**Cause:** File is too new or not tracked by git.

**Solution:**
- Verify the file exists and is committed
- Check if the file was recently renamed (rare cases where `--follow` heuristics don't catch the rename)

### "File not tracked by git"

**Cause:** File is in .gitignore or not yet added.

**Solution:**
```bash
git add <file>
git commit -m "Initial commit"
```

### Story is too generic

**Cause:** Commit messages lack detail.

**Solution:**
- Improve commit message quality going forward
- Manually add context in the story output
- Combine with issue/PR links for more context

### Output is truncated or history feels clipped

**Cause:** File has more than 20 commits; the skill intentionally caps depth.

**Solution:**
- Scope by time range (see Advanced Usage)
- Analyze smaller, more focused files
- Ask for a narrative on a specific phase ("what happened in 2024 Q1?")

## Advanced Usage

### Analyze a specific time period

```
> Tell me the story of src/core/app.js focusing on commits between 2024-01-01 and 2024-06-30
```

When the prompt specifies a date range, Claude typically passes `--since` / `--until` through to `git log` on the fly. Behavior is not encoded in `SKILL.md`, so treat it as best-effort rather than a guarantee — rerun the prompt if the returned history ignores your window.

### Compare two time periods

```
> Tell me the story of src/core/app.js in two parts: 2023 H1 vs 2023 H2, and highlight how the design direction changed
```

### Export to Markdown

```
> Tell me the story of src/core/app.js and write it to docs/app-history.md
```

### Batch analysis

Ask Claude to iterate:

```
> For each file under src/core/, tell me a short one-paragraph story and save to docs/stories/<basename>.md
```

## Example Workflow

### Scenario: Understanding a Complex Module Before Refactoring

1. **Analyze the main file** in Claude Code:
   ```
   > Tell me the story of src/modules/payment/processor.js
   ```

2. **Read the narrative** and internalize the design decisions.

3. **Check related files** the same way:
   ```
   > Tell me the story of src/modules/payment/validator.js
   > Tell me the story of src/modules/payment/gateway.js
   ```

4. **Refactor** `processor.js`.

5. **Stage + review** the changes:
   ```
   > Review the staged files
   ```
   (Default: code-review-claude. For a fully-worked refactored patch, chain code-review-gemini afterwards.)

6. **Commit** using Conventional Commits format, e.g.:
   ```
   refactor(payment): improve error handling for edge cases
   ```

7. **Optionally regenerate the story** to capture the refactoring in docs:
   ```
   > Tell me the updated story of src/modules/payment/processor.js and save it to docs/payment-refactoring.md
   ```

## FAQ

**Q: How far back does it analyze?**
A: The 20 most recent commits per file (hard-coded in `SKILL.md` to protect the context window). For wider windows, request a time-bounded analysis — see *Advanced Usage*.

**Q: Does it work with renamed files?**
A: Yes, uses `git log --follow` to track renames.

**Q: Can I analyze deleted files?**
A: No, the file must currently exist in the working directory.

**Q: What languages are supported?**
A: All languages tracked by git. The analysis focuses on commit history, not code syntax.

**Q: How much does it cost?**
A: No external API cost — analysis runs natively inside Claude Code. Counts against your regular Claude Code usage.

**Q: Can I analyze an entire directory?**
A: Not directly, but you can ask Claude to loop over files — see *Batch analysis* in Advanced Usage.

**Q: How long does analysis take?**
A: Usually a few seconds per file, depending on history length and diff complexity.

## Related Skills

- **code-review-claude** (default) - Native code review with adversarial pass + assumptions list
- **code-review-gemini** - Optional second-opinion / refactored patch generator
- **work-log-analyzer** - Combine code history with work log context
- **release-notes-generator** - Generate release documentation (coming soon)

## License

MIT
