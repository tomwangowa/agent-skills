---
name: code-story-teller
description: Analyze git history to tell the story of how code evolved. Use this Skill when the user asks to understand code history, explain evolution, show file timeline, or understand design decisions behind code.
---

# Code Story Teller

## Purpose

This Skill analyzes the git history of a file to tell its evolutionary story by:
1. Collecting complete commit history for the file
2. Analyzing major changes and design decisions
3. Generating a narrative story about the code's evolution
4. Presenting the evolution in an engaging, informative format

The Skill helps developers understand:
- Why code was written the way it is
- What design decisions were made and why
- How the code evolved over time
- Who contributed what to the codebase

---

## Instructions

When the user expresses intent to understand code history (for example: "tell the story of this file", "explain how this code evolved", "show me the history"), follow the steps below strictly.

### Execution steps

1. **Identify the file** the user wants to analyze
   - If the user mentions a specific file path, use it
   - If the user says "this file" or "current file", ask for clarification
   - If the user is discussing code in context, try to infer the file

2. **Validate the file exists**
   ```bash
   # Check if file exists and is tracked by git
   git ls-files <file-path> --error-unmatch
   ```

3. **Collect commit history** for the file
   ```bash
   # Get detailed commit history with diffs (automatically handles renames)
   # Using -p flag to include patches (diffs) inline
   git log --follow -p -20 --pretty=format:"%H|%ai|%an|%s" -- <file-path>
   ```

   **Note**: The `--follow` flag tracks file renames, and `-p` includes diffs inline.
   This is more reliable than running separate `git show` commands, which don't
   automatically handle renamed files.

4. **Analyze the history**:
   - **Origin**: When was the file created? What was the initial purpose?
   - **Key Milestones**: What major changes occurred? (rewrites, major features, bug fixes)
   - **Design Evolution**: How did the architecture change over time?
   - **Contributors**: Who were the main contributors and what did they add?
   - **Patterns**: Are there recurring themes? (refactoring, bug fixes, feature additions)

5. **Read current state** of the file for comparison:
   ```bash
   # Read the current file content
   cat <file-path>
   ```

6. **Generate narrative story**:
   - Start with creation context ("Initially created to...")
   - Describe evolution chronologically
   - Highlight key design decisions with commit references
   - Explain current state and how it evolved
   - Use Traditional Chinese for narrative, English for technical terms

7. **Present the story** in structured format (see Output Format below)

8. **Offer follow-up options**:
   - Analyze another related file
   - Dive deeper into specific commits
   - Generate Architecture Decision Record (ADR)
   - Compare with similar files

### Output requirements

Your response should include:

- **Origin Story** (起源故事)
  When and why the file was created, initial purpose

- **Evolution Timeline** (演進時間軸)
  Chronological milestones with commit hashes and dates

- **Design Insights** (設計洞察)
  Notable architectural or design decisions, explained with context

- **Current State** (當前狀態)
  How the file looks now compared to its origin

- **Patterns & Learnings** (模式與學習)
  What can we learn from this history

- **Key Contributors** (重要貢獻者)
  Who shaped this code and their main contributions

---

## Constraints

- File must exist in the git repository
- File must have commit history
- Analysis is limited to the most recent 20 commits (to avoid context overflow)
- Large diffs may need to be summarized rather than shown in full
- Must be run in a git repository

---

## Output Format

Present the story in this structure:

```markdown
# 📖 Code Story: <file-path>

## 🌱 Origin Story (起源)
[When created, by whom, initial purpose]

## 📅 Evolution Timeline (演進時間軸)

### 2024-01-15: Initial Creation
- Commit: abc1234
- Author: John Doe
- Purpose: [What was added and why]

### 2024-03-20: Major Refactoring
- Commit: def5678
- Author: Jane Smith
- Changes: [What changed and why]

[... more milestones ...]

## 🏗️ Design Insights (設計洞察)

### Decision 1: [Design choice]
- **Context**: [Why this was needed]
- **Approach**: [What was chosen]
- **Commit**: abc1234 (2024-01-15)

[... more insights ...]

## 📊 Current State (當前狀態)

[Describe current structure and how it differs from origin]

## 🔍 Patterns & Learnings (模式與學習)

- **Pattern 1**: [Observed pattern]
- **Learning 1**: [What we can learn]

## 👥 Key Contributors (重要貢獻者)

- **John Doe**: Initial implementation, authentication logic
- **Jane Smith**: Performance optimization, refactoring
```

---

## Examples

### Example 1: Simple File History

**User:**
> Tell me the story of src/utils/validator.ts

**Your workflow:**
1. Check file exists: `git ls-files src/utils/validator.ts`
2. Get commit history: `git log --follow --pretty=format:"%H|%ai|%an|%s" -20 -- src/utils/validator.ts`
3. Analyze key commits (creation, major changes)
4. Read current file: `cat src/utils/validator.ts`
5. Generate story focusing on:
   - Why validator was created
   - How validation rules evolved
   - When edge cases were added
   - Current validation capabilities

### Example 2: File with Rich History

**User:**
> How did the authentication module evolve?

**Your workflow:**
1. Identify specific file (e.g., src/auth/login.ts)
2. Get full commit history
3. Identify major milestones:
   - Initial basic auth
   - Added OAuth support
   - Implemented 2FA
   - Security hardening
4. Explain design decisions for each milestone
5. Show how security improved over time

---

## Tips for Quality Stories

1. **Focus on "Why" not "What"**
   - ❌ "Added error handling"
   - ✅ "Added error handling after production crash revealed edge case"

2. **Connect commits to context**
   - Reference commit messages for rationale
   - Link related commits together
   - Explain the broader picture

3. **Identify patterns**
   - Recurring bug fixes → potential design smell
   - Gradual complexity increase → evolution of requirements
   - Multiple contributors → collaborative decisions

4. **Make it narrative**
   - Tell a story, not just list commits
   - Use engaging language
   - Highlight interesting moments

5. **Use Traditional Chinese for narrative**
   - Technical terms in English
   - Commit hashes and dates in English
   - Narrative explanation in Chinese

---

## Use Cases

### Understanding Legacy Code
When joining a new project or working with unfamiliar code:
- Understand the original intent
- See how requirements changed over time
- Learn from previous design decisions

### Code Review Context
Before reviewing changes:
- Understand the file's history
- See if the change aligns with previous patterns
- Check if there were similar attempts before

### Refactoring Decisions
Before major refactoring:
- Understand why the current design exists
- Learn from previous refactoring attempts
- Avoid repeating past mistakes

### Documentation
Generate historical documentation:
- Create Architecture Decision Records (ADRs)
- Document design rationale
- Onboard new team members

### Technical Debt Analysis
Identify patterns:
- Recurring bug fixes in the same area
- Gradual complexity increase
- Signs of technical debt accumulation

---

## Common Mistakes to Avoid

❌ **Just listing commits**: "Commit A, then B, then C"
✅ **Tell the story**: "Initially simple, became complex as edge cases emerged"

❌ **Ignoring commit messages**: Missing valuable context
✅ **Use commit messages**: Extract the "why" from messages

❌ **Too much detail**: Overwhelming with every small change
✅ **Focus on major milestones**: Highlight significant changes

❌ **No current state**: Ending with history only
✅ **Show current state**: Compare then vs now

---

## Advanced: Multi-File Analysis

For analyzing related files together:

```bash
# Get history for multiple related files
for file in src/auth/*.ts; do
  echo "=== $file ==="
  git log --follow --oneline -10 -- "$file"
done
```

Then synthesize a broader story about how the module evolved as a whole.

---

## When NOT to Use This Skill

- File has no commits (newly created, not yet committed)
- User wants current code explanation (use code review instead)
- Binary files or generated code (history not meaningful)
- Directory instead of file (ask for specific file)
