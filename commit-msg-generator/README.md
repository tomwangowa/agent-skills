# Commit Message Generator

Automatically generate high-quality commit messages following the Conventional Commits specification.

## Features

- **Analyzes staged changes** to understand what was modified
- **Generates descriptive messages** using AI (Gemini)
- **Follows Conventional Commits** format strictly
- **Saves time** - no more struggling to write commit messages
- **Maintains consistency** across your commit history

## Dependencies

- [Gemini CLI](https://github.com/google-gemini/gemini-cli): `npm install -g @google/gemini-cli`
- Git repository with staged changes
- `GEMINI_API_KEY` environment variable set

## Usage

### Step 1: Stage your changes

```bash
git add <files>
```

### Step 2: Generate commit message

In Claude Code, use natural language:

```
> Generate a commit message
> Help me write a commit message
> Create commit description
```

### Step 3: Use the generated message

Claude will provide a command to use the message:

```bash
git commit -F /tmp/commit_msg_result.txt
```

Or copy the message and edit it:

```bash
git commit
# Paste and edit the message in your editor
```

## Example Workflow

```bash
# Make changes to your code
vim src/api/auth.js

# Stage the changes
git add src/api/auth.js

# Open Claude Code
claude

# In Claude Code:
> Generate commit message

# Claude analyzes and generates:
# feat(auth): add JWT token refresh mechanism
#
# - Implement automatic token refresh before expiration
# - Add refresh token storage in secure cookie
# - Handle refresh failure with re-authentication
#
# Co-Authored-By: Gemini AI <noreply@google.com>

# Use the generated message
git commit -F /tmp/commit_msg_result.txt
```

## Generated Message Format

The generated messages follow the Conventional Commits specification:

```
<type>(<scope>): <subject>

<body>

Co-Authored-By: Gemini AI <noreply@google.com>
```

### Types

- **feat**: New feature
- **fix**: Bug fix
- **docs**: Documentation changes
- **style**: Code style/formatting (no logic change)
- **refactor**: Code refactoring
- **perf**: Performance improvements
- **test**: Adding or updating tests
- **chore**: Maintenance, dependencies, configs
- **ci**: CI/CD changes
- **build**: Build system changes

### Scope (optional)

Component or module name: `api`, `ui`, `auth`, `db`, etc.

### Subject

- Imperative mood ("add" not "added")
- Lowercase start
- No period at end
- Maximum 50 characters

### Body (optional)

- Explains what and why, not how
- Wraps at 72 characters
- Can use bullet points
- Blank line after subject

## Important Security Note

⚠️ **The diff content is sent to the Gemini API to generate the commit message.**

**Never stage files containing:**
- API keys, tokens, or passwords
- Private keys or certificates
- Personal identifiable information (PII)
- Other sensitive data

Always review what you're staging before generating a commit message.

## Tips

1. **Review before committing**: Always review the generated message and adjust if needed
2. **Add context**: The message is based on the diff, but you can add business context
3. **Breaking changes**: Add `BREAKING CHANGE:` in the body if introducing breaking changes
4. **Issue references**: Add issue numbers like `Fixes #123` in the body

## Direct Script Usage

You can also run the script directly:

```bash
# Stage your changes
git add <files>

# Generate message
bash ~/.claude/skills/commit-msg-generator/scripts/generate_commit_msg.sh

# Use the message
git commit -F /tmp/commit_msg_result.txt
```

## Troubleshooting

### "No staged changes found"

**Solution**: Make sure to stage your changes first:
```bash
git add <files>
```

### "gemini: command not found"

**Solution**: Install Gemini CLI:
```bash
npm install -g @google/gemini-cli
```

### "GEMINI_API_KEY not set"

**Solution**: Set your API key:
```bash
export GEMINI_API_KEY="your-api-key"
# Add to ~/.zshrc or ~/.bashrc for persistence
```

### Message doesn't capture the full context

**Solution**: You can:
1. Edit the generated message before committing
2. Add more context in the commit body
3. Regenerate with emphasis on specific aspects

## Configuration

### Custom Model

Set a different Gemini model:

```bash
export GEMINI_MODEL="gemini-2.0-flash-exp"
```

### Custom Output Location

The script outputs to `${TMPDIR:-/tmp}/commit_msg_result.txt` by default.

## Best Practices

1. **Commit often**: Small, focused commits are easier to describe
2. **One concern per commit**: Easier to generate accurate messages
3. **Review the diff**: Make sure the staged changes match your intent
4. **Edit if needed**: The generated message is a starting point
5. **Keep history clean**: Good commit messages help your team

## Examples

### Feature Addition

```
feat(api): add user authentication endpoint

- Implement POST /api/auth/login with JWT
- Add password validation and hashing
- Include rate limiting for security

Co-Authored-By: Gemini AI <noreply@google.com>
```

### Bug Fix

```
fix(ui): resolve infinite scroll not triggering

Fixed issue where scroll event listener was not properly
attached after component re-render. Added cleanup in useEffect.

Co-Authored-By: Gemini AI <noreply@google.com>
```

### Refactoring

```
refactor(db): extract database connection to separate module

- Move connection logic from multiple files to db/connection.js
- Add connection pooling configuration
- Improve error handling

Co-Authored-By: Gemini AI <noreply@google.com>
```

## Related Resources

- [Conventional Commits](https://www.conventionalcommits.org/)
- [How to Write a Git Commit Message](https://chris.beams.io/posts/git-commit/)
- [Semantic Versioning](https://semver.org/)
