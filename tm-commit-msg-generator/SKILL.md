---
name: Commit Message Generator
description: Generate high-quality commit messages following Conventional Commits specification. Use this Skill when the user asks to generate commit message, write commit message, or create commit description.
id: tm-commit-msg-generator
namespace: tm
domain: commit
action: msg
qualifier: generator
version: "1.0.0"
updated: "2026-01-17"
---

# Commit Message Generator

## Purpose

This Skill generates well-structured commit messages that follow the Conventional Commits specification by:
1. Analyzing staged changes (`git diff --cached`)
2. Using Gemini CLI to understand the changes and their purpose
3. Generating a properly formatted commit message
4. Providing the message in a ready-to-use format

The Skill helps maintain consistent commit history and saves time writing descriptive commit messages.

---

## Instructions

When the user expresses intent to generate a commit message (for example: "generate commit message", "write commit message", "help me commit"), follow the steps below strictly.

### Execution steps

1. Run the script `scripts/generate_commit_msg.sh`.

2. The script will:
   - Check that there are staged changes
   - Analyze the diff to understand what changed
   - Use Gemini to generate a commit message following Conventional Commits format
   - Display the generated message

3. Present the generated commit message to the user and explain:
   - The commit type and scope
   - Why this message accurately describes the changes
   - How to use it (copy it or use `git commit -F` command)

4. Optional: Ask if the user wants to:
   - Use the message as-is
   - Make modifications
   - Regenerate with different emphasis

### Output requirements

Your response should include:

- **Generated commit message**
  Display the full commit message clearly

- **Explanation**
  Brief explanation of why this type/scope was chosen

- **Usage instructions**
  How to apply the message to the commit

- **Alternative options**
  Offer to modify or regenerate if needed

id: tm-commit-msg-generator
namespace: tm
domain: commit
action: msg
qualifier: generator
version: "1.0.0"
updated: "2026-01-17"
---

## Constraints

- Only works when there are staged changes (`git add` must be run first)
- Requires Gemini CLI to be installed and configured
- Message format strictly follows Conventional Commits specification
- Subject line must be 50 characters or less
- Body lines wrapped at 72 characters

---

## Examples

**User:**
> Generate a commit message for my staged changes

**Expected behavior:**
- Run `generate_commit_msg.sh`
- Display the generated message with formatting
- Explain the commit type and reasoning
- Provide command to use the message

id: tm-commit-msg-generator
namespace: tm
domain: commit
action: msg
qualifier: generator
version: "1.0.0"
updated: "2026-01-17"
---

**User:**
> Help me write a commit message

**Expected behavior:**
- Same workflow as above
- Show both the raw message and usage command

---

**User:**
> I need a commit description

**Expected behavior:**
- Generate message following conventional commits
- Explain what makes this a good commit message
- Offer to regenerate if user wants different emphasis

id: tm-commit-msg-generator
namespace: tm
domain: commit
action: msg
qualifier: generator
version: "1.0.0"
updated: "2026-01-17"
---

## Commit Message Format

The generated messages follow this format:

```
type(scope): subject line

Optional body explaining what and why, not how.
Can include bullet points for multiple changes.

Co-Authored-By: Gemini AI <noreply@google.com>
```

**Types:**
- `feat`: New feature
- `fix`: Bug fix
- `docs`: Documentation
- `style`: Formatting
- `refactor`: Code restructuring
- `perf`: Performance
- `test`: Tests
- `chore`: Maintenance
- `ci`: CI/CD
- `build`: Build system

**Best Practices:**
- Subject in imperative mood ("add" not "added")
- Subject starts with lowercase
- No period at end of subject
- Body explains "what" and "why", not "how"
