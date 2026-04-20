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

- [Gemini CLI](https://github.com/google-gemini/gemini-cli): `npm install -g @google/gemini-cli`
- Git repository with commit history
- `GEMINI_API_KEY` environment variable set

## Usage

### Step 1: Identify a file to analyze

Choose a file you want to understand:
- Core modules you're unfamiliar with
- Frequently changed files
- Complex legacy code
- Files you're about to refactor

### Step 2: Run the analysis

**Using Claude Code** (Recommended):

```
> Tell me the story of src/api/auth.js
> Show me how database/models/user.js evolved
> Explain the history of this file
```

**Direct script usage**:

```bash
cd /path/to/your/project
bash ~/.claude/skills/code-story-teller/scripts/tell_code_story.sh src/api/auth.js
```

### Step 3: Read the story

The tool generates a comprehensive narrative including:
- Origin story (when & why created)
- Evolution timeline (major milestones)
- Design decisions (architectural choices)
- Current state (present structure)
- Patterns & insights (what can we learn)
- Notable contributors (who shaped the code)

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

```bash
# Analyze the main file
tell_code_story.sh src/legacy/payment-processor.js
```

**Benefits:**
- Understand original design intent
- See how requirements changed
- Learn from past decisions
- Identify technical debt sources

### 2. Pre-Refactoring Research

**Scenario:** Planning a major refactoring.

```bash
# Study the file's history first
tell_code_story.sh src/core/data-processor.js
```

**Benefits:**
- Understand why current design exists
- Learn from previous refactoring attempts
- Avoid repeating past mistakes
- Make informed decisions

### 3. Code Review Context

**Scenario:** Reviewing a complex PR.

```bash
# Get context on the file being changed
tell_code_story.sh src/components/UserProfile.jsx
```

**Benefits:**
- See if changes align with historical patterns
- Understand the file's evolution direction
- Provide more contextual feedback

### 4. Onboarding New Developers

**Scenario:** New team member needs to understand the codebase.

```bash
# Generate stories for key modules
tell_code_story.sh src/api/index.js
tell_code_story.sh src/database/schema.js
```

**Benefits:**
- Faster onboarding
- Understand architectural decisions
- Learn team's coding patterns
- See who to ask for help

### 5. Documentation Generation

**Scenario:** Creating technical documentation.

```bash
# Generate stories for documentation
tell_code_story.sh src/core/engine.js > docs/engine-history.md
```

**Benefits:**
- Auto-generated context documentation
- Architecture Decision Records (ADRs)
- Historical context for future developers

## Configuration

### Adjust Maximum Commits

By default, the tool analyzes the most recent 20 commits. To change this:

```bash
# Edit the script
vim ~/.claude/skills/code-story-teller/scripts/tell_code_story.sh

# Change this line:
MAX_COMMITS=20  # Increase or decrease as needed
```

**Note:** More commits = more context but longer processing time and higher API costs.

### Language Preference

The default output is in Traditional Chinese with English technical terms. To change this, modify the prompt in the script.

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
- Check if the file was recently renamed (tool may not track renames beyond git's defaults)

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

### Output is truncated

**Cause:** Too many commits or large diffs.

**Solution:**
- Reduce MAX_COMMITS in the script
- Focus on specific time periods
- Analyze smaller, more focused files

### API quota exceeded

**Cause:** Analyzed too many files in a short time.

**Solution:**
- Wait for quota reset
- Use a different API key
- Reduce analysis frequency
- Cache results for frequently analyzed files

## Advanced Usage

### Analyze Specific Time Period

```bash
# Modify the script to use date ranges
git log --follow --since="2023-01-01" --until="2023-12-31" -- <file>
```

### Compare Two Time Periods

```bash
# Run analysis for different periods and compare
tell_code_story.sh --since="2023-01-01" --until="2023-06-30" file.js
tell_code_story.sh --since="2023-07-01" --until="2023-12-31" file.js
```

### Export to Markdown

```bash
# Save story as documentation
tell_code_story.sh src/core/app.js | sed 's/^===.*===/---/' > docs/app-history.md
```

### Batch Analysis

```bash
# Analyze multiple files
for file in src/core/*.js; do
  echo "Analyzing $file..."
  tell_code_story.sh "$file" > "docs/stories/$(basename $file .js)-story.txt"
done
```

## Example Workflow

### Scenario: Understanding a Complex Module Before Refactoring

```bash
# 1. Analyze the main file
tell_code_story.sh src/modules/payment/processor.js

# 2. Read the story and understand design decisions
# (Output appears in terminal and saved to temp file)

# 3. Check related files
tell_code_story.sh src/modules/payment/validator.js
tell_code_story.sh src/modules/payment/gateway.js

# 4. Make refactoring changes
vim src/modules/payment/processor.js

# 5. Stage and review changes
git add src/modules/payment/processor.js

# In Claude Code:
# > Review the staged files
# (Default: code-review-claude. For a refactored patch, chain code-review-gemini afterwards.)

# 6. Commit changes
git commit -m "refactor(payment): improve error handling for edge cases"

# 7. Commit
git commit -F /tmp/commit_msg_result.txt

# 8. Generate updated story (optional)
tell_code_story.sh src/modules/payment/processor.js > docs/payment-refactoring.md
```

## FAQ

**Q: How far back does it analyze?**
A: By default, the most recent 20 commits. Configurable via MAX_COMMITS.

**Q: Does it work with renamed files?**
A: Yes, uses `git log --follow` to track renames.

**Q: Can I analyze deleted files?**
A: No, the file must currently exist in the working directory.

**Q: What languages are supported?**
A: All languages tracked by git. The analysis focuses on commit history, not code syntax.

**Q: How much does it cost?**
A: Depends on your Gemini API usage. Each analysis sends ~2-5KB of data.

**Q: Can I analyze an entire directory?**
A: No, analyze one file at a time. Use a bash loop for batch processing.

**Q: How long does analysis take?**
A: Usually 5-15 seconds per file, depending on history complexity and API latency.

## Related Skills

- **code-review-claude** (default) - Native code review with adversarial pass + assumptions list
- **code-review-gemini** - Optional second-opinion / refactored patch generator
- **work-log-analyzer** - Combine code history with work log context
- **release-notes-generator** - Generate release documentation (coming soon)

## License

MIT
