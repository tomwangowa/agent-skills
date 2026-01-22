---
name: code-reviewer
description: Intelligent code review dispatcher - automatically selects best reviewer based on context and preferences
---

# Code Reviewer (Meta-Skill)

## Purpose

Automatically routes code review requests to the most appropriate reviewer based on context and user preferences. This meta-skill provides a unified interface for accessing multiple code review implementations.

## Available Reviewers

1. **code-review-claude** - Fast, native code review (< 30 seconds)
   - Best for: Quick validation checks during development
   - Strength: Speed and immediate feedback

2. **code-review-gemini** - Deep, external perspective review
   - Best for: Thorough reviews with alternative AI viewpoint
   - Strength: Different perspective, catches different issues

## Trigger Phrases

When the user mentions any of these, activate this skill:
- "review"
- "code review"
- "review my code"
- "review the code"
- "check the code"
- "review changes"
- "review staged files"

## Decision Logic

### Step 1: Check User Preferences

Read from `~/.claude/CLAUDE.md` section 9 (Notice) → Skill Preferences → Code Review:
- Default reviewer preference
- Fallback options
- Any context-specific overrides

### Step 2: Analyze Context

Examine the current situation:

| Factor | How to Check | Impact |
|--------|--------------|--------|
| **File count** | `git diff --cached --name-only \| wc -l` | Many files → prefer thorough review |
| **Line count** | `git diff --cached --shortstat` | Few lines → quick review acceptable |
| **User keywords** | Check for "quick", "fast", "thorough", "checklist" | Override preferences |
| **Complexity** | File types, languages involved | Complex → prefer thorough review |

### Step 3: Apply Routing Rules

Execute routing logic in priority order:

| Priority | Condition | Action | Reason |
|----------|-----------|--------|--------|
| 1 | User says "quick" or "fast" | → `code-review-claude` | Speed required |
| 2 | User says "thorough" or "deep" or "gemini" | → `code-review-gemini` | Depth required |
| 3 | CLAUDE.md preference set | → Use preferred reviewer | Respect user default |
| 4 | < 50 lines changed AND < 3 files | → `code-review-claude` | Small change, quick check |
| 5 | Default (no preference set) | → `code-review-gemini` | Best balance |

### Step 4: Execute and Report

1. **Inform user**: "Using {skill_name} for this review..."
2. **Invoke skill**: Use the Skill tool to call the selected reviewer
3. **Pass through results**: Return the review output to the user

## Implementation

When this skill is triggered:

```markdown
1. Parse user request for keywords (quick, thorough, checklist)
2. Check for staged changes: git diff --cached --shortstat
3. Read CLAUDE.md preferences (if they exist)
4. Apply routing rules (priority order above)
5. Report decision: "Using code-review-gemini for this review..."
6. Execute: Skill tool with selected reviewer
7. Return results to user
```

## Examples

### Example 1: Default Review (with preference)

```
User: "Review my code"
Assistant: [Checks CLAUDE.md, sees gemini is preferred]
Assistant: "Using code-review-gemini for this review..."
Assistant: [Calls Skill tool with skill="code-review-gemini"]
```

### Example 2: Quick Review Override

```
User: "Quick review of my changes"
Assistant: [Detects "quick" keyword]
Assistant: "Using code-review-claude for fast feedback..."
Assistant: [Calls Skill tool with skill="code-review-claude"]
```

### Example 3: Small Change Auto-Detection

```
User: "Review this"
Assistant: [Checks: 15 lines changed in 1 file, no preference set]
Assistant: "Small change detected. Using code-review-claude for quick check..."
Assistant: [Calls Skill tool with skill="code-review-claude"]
```

### Example 4: Large Change Auto-Detection

```
User: "Review changes"
Assistant: [Checks: 250 lines changed across 8 files]
Assistant: "Substantial changes detected. Using code-review-gemini for thorough review..."
Assistant: [Calls Skill tool with skill="code-review-gemini"]
```

## Configuration

Users can set preferences in `~/.claude/CLAUDE.md`:

```markdown
## 9. Notice

### Skill Preferences

#### Code Review
- **Default reviewer**: code-review-gemini
- **Quick review fallback**: code-review-claude
- **Rationale**: Gemini provides external perspective, Claude for speed
```

## Direct Access

Users can still bypass this meta-skill and call specific reviewers directly:

```bash
/skill code-review-gemini     # Force gemini
/skill code-review-claude     # Force claude
/skill code-review-checklist  # Force checklist
```

This preserves user control while providing intelligent defaults.

## Design Principles

1. **Single Entry Point** - Users remember one command: "review my code"
2. **Transparent Decision** - Always tell user which reviewer is being used
3. **Respect Preferences** - Honor user's CLAUDE.md settings
4. **Context-Aware** - Consider file count, line count, complexity
5. **Override-Friendly** - Keywords (quick, thorough) override defaults
6. **Direct Access Preserved** - Users can still call specific skills

## Implementation Notes

- This meta-skill does **NOT** contain review logic
- It only performs **routing and delegation**
- All actual review work is done by specialized skills
- Decision logic is simple and rule-based (no complex AI needed)
- Routing rules are listed in priority order for clarity

## Related Documentation

- [Meta-Skills Design Pattern](../docs/Meta-Skills-Pattern.md)
- [Code Review Claude](../code-review-claude/SKILL.md)
- [Code Review Gemini](../code-review-gemini/SKILL.md)

---

**Pattern**: Meta-Skill (Dispatcher)
**Version**: 1.0
**Created**: 2026-01-22
