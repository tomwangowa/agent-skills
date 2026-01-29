---
name: commit-msg-generator
description: Generate high-quality commit messages following Conventional Commits specification. Use this Skill when the user asks to generate commit message, write commit message, or create commit description.
---

# Commit Message Generator

## Purpose

This Skill generates well-structured commit messages that follow the Conventional Commits specification by:
1. Analyzing staged changes (`git diff --cached`)
2. Understanding the changes and their purpose
3. Generating a properly formatted commit message
4. Providing the message in a ready-to-use format

The Skill helps maintain consistent commit history and saves time writing descriptive commit messages.

---

## Instructions

When the user expresses intent to generate a commit message (for example: "generate commit message", "write commit message", "help me commit"), follow the steps below strictly.

### Execution steps

1. **Check for staged changes**
   ```bash
   git diff --cached --name-only
   ```
   If no staged changes, inform the user and suggest running `git add` first.

2. **Analyze the diff**
   ```bash
   git diff --cached
   ```
   Read and understand:
   - What files were changed
   - What functionality was added, modified, or removed
   - The scope of changes (which component/module)
   - The purpose and intent behind the changes

3. **Analyze recent commit history** for context
   ```bash
   git log --oneline -10
   ```
   This helps maintain consistent commit message style with the repository.

4. **Generate commit message** following Conventional Commits format:

   **Structure:**
   ```
   type(scope): subject line

   Optional body explaining what and why, not how.
   Can include bullet points for multiple changes.

   Co-Authored-By: [Your Model Name] <noreply@example.com>
   ```

   **Guidelines:**
   - **Type**: Choose appropriate type (feat, fix, docs, refactor, etc.)
   - **Scope**: Identify the affected component/module
   - **Subject**: 50 characters or less, imperative mood, lowercase start, no period
   - **Body**: Optional, explain what and why (not how), wrap at 72 characters
   - **Co-Author**: Credit yourself using your actual model name (e.g., "Claude Sonnet 4.5", "Gemini 2.0", etc.)

5. **Present the message** to the user:
   - Display the full commit message clearly
   - Explain the type and scope chosen
   - Explain why this accurately describes the changes
   - Provide usage instructions

6. **Offer options**:
   - Use as-is
   - Request modifications
   - Regenerate with different emphasis

### Output requirements

Your response should include:

- **Generated commit message**
  Display the full commit message in a code block

- **Explanation**
  - Why this type was chosen (feat/fix/docs/etc.)
  - Why this scope was selected
  - How it accurately reflects the changes

- **Usage instructions**
  Show the user how to use it:
  ```bash
  # Option 1: Copy and paste the message
  git commit -m "..."

  # Option 2: Use your editor
  git commit
  # Then paste the message
  ```

- **Alternative options**
  Offer to modify or regenerate if needed

---

## Constraints

- Only works when there are staged changes (`git add` must be run first)
- Message format strictly follows Conventional Commits specification
- Subject line must be 50 characters or less
- Body lines wrapped at 72 characters
- Must be in a git repository

---

## Commit Message Format

### Types

- `feat`: New feature for the user
- `fix`: Bug fix
- `docs`: Documentation only changes
- `style`: Formatting, missing semicolons, etc (no code change)
- `refactor`: Code change that neither fixes a bug nor adds a feature
- `perf`: Performance improvement
- `test`: Adding or updating tests
- `chore`: Changes to build process or auxiliary tools
- `ci`: CI/CD configuration changes
- `build`: Changes to build system or dependencies

### Best Practices

- **Subject in imperative mood**: "add" not "added" or "adds"
- **Subject starts with lowercase**: "add feature" not "Add feature"
- **No period at end of subject**: "add feature" not "add feature."
- **Body explains "what" and "why"**: not "how"
- **Blank line between subject and body**: Required
- **Wrap body at 72 characters**: For readability

### Examples

**Simple feature:**
```
feat(auth): add password reset functionality

Allow users to reset their password via email link.
Implements password reset flow with token expiration.

Co-Authored-By: [Your Model Name] <noreply@example.com>
```

**Bug fix:**
```
fix(api): handle null user in authentication

Prevent crash when user object is null during auth check.
Adds null check before accessing user.email property.

Co-Authored-By: [Your Model Name] <noreply@example.com>
```

**Documentation:**
```
docs(readme): update installation instructions

Add prerequisites section and clarify setup steps.

Co-Authored-By: [Your Model Name] <noreply@example.com>
```

---

## Common Mistakes to Avoid

❌ **Too vague**: "update code", "fix things"
✅ **Specific**: "fix null check in login handler"

❌ **Past tense**: "added feature", "fixed bug"
✅ **Imperative**: "add feature", "fix bug"

❌ **Uppercase start**: "Add feature"
✅ **Lowercase**: "add feature"

❌ **Period at end**: "add feature."
✅ **No period**: "add feature"

❌ **No scope**: "fix bug"
✅ **With scope**: "fix(auth): handle null user"

❌ **Explaining how**: "use try-catch to handle errors"
✅ **Explaining what/why**: "prevent crash on invalid input"

---

## Workflow Example

**User request:**
> Generate a commit message for my staged changes

**Your workflow:**
1. Run `git diff --cached --name-only` → See which files changed
2. Run `git diff --cached` → Understand the changes
3. Run `git log --oneline -10` → Check commit style
4. Analyze changes:
   - Added null check in auth/login.ts
   - Prevents crash when user is null
   - Type: fix (bug fix)
   - Scope: auth (authentication module)
5. Generate message:
   ```
   fix(auth): handle null user in login flow

   Add null check before accessing user.email property.
   Prevents crash when user object is null during authentication.

   Co-Authored-By: [Your Model Name] <noreply@example.com>
   ```
6. Present to user with explanation
7. Offer to modify if needed

---

## Tips for Quality Commit Messages

1. **Read the diff carefully** - Don't just summarize file names
2. **Identify the intent** - Why was this change made?
3. **Choose precise type** - Is it really a feature or just a refactor?
4. **Find the right scope** - What component/module is affected?
5. **Be specific in subject** - Avoid generic terms
6. **Add body for complex changes** - Explain context and reasoning
7. **Keep it concise** - Respect character limits
8. **Match repository style** - Check recent commits for patterns

---

## When NOT to Use This Skill

- No staged changes (nothing to commit)
- User wants to write message manually (respect their preference)
- Changes are too complex to summarize (ask for user input on intent)
- User explicitly provides a commit message (use theirs)
