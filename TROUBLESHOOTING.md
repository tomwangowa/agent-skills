# Troubleshooting Guide

Common issues and solutions for Claude Code Skills.

## Table of Contents

- [Installation Issues](#installation-issues)
- [Gemini CLI Issues](#gemini-cli-issues)
- [Skill Execution Issues](#skill-execution-issues)
- [Git Issues](#git-issues)
- [General Tips](#general-tips)

## Installation Issues

### Skills Not Found by Claude Code

**Problem:** Claude Code doesn't recognize your skills.

**Solutions:**

1. Verify the skills directory location:
   ```bash
   ls ~/.claude/skills/
   ```

2. Check that `SKILL.md` files exist:
   ```bash
   find ~/.claude/skills/ -name "SKILL.md"
   ```

3. Ensure proper directory structure:
   ```
   ~/.claude/skills/
   └── code-review-gemini/
       ├── SKILL.md
       └── scripts/
           └── review_with_gemini.sh
   ```

4. Restart Claude Code after installing new skills.

### Permission Denied on Scripts

**Problem:** `bash: permission denied: ./review_with_gemini.sh`

**Solution:**

```bash
# Make scripts executable
chmod +x ~/.claude/skills/code-review-gemini/scripts/review_with_gemini.sh

# Or for all scripts in the repository
find ~/.claude/skills/ -name "*.sh" -exec chmod +x {} \;
```

## Gemini CLI Issues

### "gemini: command not found"

**Problem:** Gemini CLI is not installed or not in PATH.

**Solutions:**

1. Install Gemini CLI:
   ```bash
   npm install -g @google/gemini-cli
   ```

2. Verify installation:
   ```bash
   which gemini
   gemini --version
   ```

3. If installed but not found, check your PATH:
   ```bash
   echo $PATH
   # Make sure npm global bin directory is in PATH
   npm config get prefix
   ```

4. Add npm global bin to PATH (if needed):
   ```bash
   # For bash
   echo 'export PATH="$(npm config get prefix)/bin:$PATH"' >> ~/.bashrc
   source ~/.bashrc

   # For zsh
   echo 'export PATH="$(npm config get prefix)/bin:$PATH"' >> ~/.zshrc
   source ~/.zshrc
   ```

### API Key Not Set

**Problem:** `Error: GEMINI_API_KEY environment variable is not set`

**Solutions:**

1. Set the environment variable:
   ```bash
   export GEMINI_API_KEY="your-api-key-here"
   ```

2. Add to your shell profile permanently:
   ```bash
   # For zsh
   echo 'export GEMINI_API_KEY="your-api-key-here"' >> ~/.zshrc
   source ~/.zshrc
   ```

3. Verify it's set:
   ```bash
   echo $GEMINI_API_KEY
   ```

### API Quota Exceeded

**Problem:** `Error: 429 Resource exhausted`

**Solutions:**

1. Check your API quota at [Google AI Studio](https://aistudio.google.com/)
2. Wait for quota reset (usually resets daily)
3. Consider upgrading your API plan
4. Use a different API key if available

### Authentication Failed

**Problem:** `Error: 401 Unauthorized` or `Error: 403 Forbidden`

**Solutions:**

1. Verify your API key is correct:
   ```bash
   echo $GEMINI_API_KEY
   ```

2. Generate a new API key at [Google AI Studio](https://aistudio.google.com/app/apikey)

3. Update your environment variable with the new key.

4. Check if the API key has proper permissions.

## Skill Execution Issues

### "No staged changes detected"

**Problem:** The review script reports no staged changes.

**Solutions:**

1. Stage your changes first:
   ```bash
   git add <files>
   ```

2. Verify staged changes:
   ```bash
   git status
   git diff --cached --name-only
   ```

3. Make sure you're in a git repository:
   ```bash
   git rev-parse --is-inside-work-tree
   ```

### Script Fails with "set -euo pipefail"

**Problem:** Script exits immediately with an error.

**Solutions:**

1. Check for syntax errors in the script:
   ```bash
   bash -n ~/.claude/skills/code-review-gemini/scripts/review_with_gemini.sh
   ```

2. Run with debugging enabled:
   ```bash
   bash -x ~/.claude/skills/code-review-gemini/scripts/review_with_gemini.sh
   ```

3. Check for undefined variables or failed commands in the script output.

### Large Diffs Fail or Timeout

**Problem:** Review fails on large changes or takes too long.

**Solutions:**

1. Review smaller chunks:
   ```bash
   # Stage and review files incrementally
   git add file1.js
   # Request review
   git add file2.js
   # Request review again
   ```

2. Consider splitting large changes into multiple commits.

3. Check if there are any very large files:
   ```bash
   git diff --cached --stat
   ```

### Review Output Shows Wrong Files

**Problem:** The review mentions files that weren't changed.

**Solutions:**

1. Verify what's actually staged:
   ```bash
   git diff --cached --name-only
   ```

2. Unstage unintended files:
   ```bash
   git reset HEAD <file>
   ```

3. Check the "Review Scope" section in the output to confirm which files were reviewed.

## Git Issues

### "fatal: not a git repository"

**Problem:** Script fails because you're not in a git repository.

**Solution:**

1. Navigate to a git repository:
   ```bash
   cd ~/your-project
   ```

2. Or initialize a new repository:
   ```bash
   git init
   ```

### "fatal: bad revision 'HEAD~1'"

**Problem:** Repository has no commits yet.

**Solution:**

This is already handled in the script for staged changes. If you encounter this, make sure you're using the latest version:

```bash
cd ~/.claude/skills/
git pull origin main
```

## General Tips

### Enable Debug Mode

Run scripts with verbose output:

```bash
# Enable bash debugging
bash -x ~/.claude/skills/code-review-gemini/scripts/review_with_gemini.sh
```

### Check Script Output Location

The review output is saved to a temporary file:

```bash
# macOS
ls -la $TMPDIR/gemini_review_result.txt

# Linux
ls -la /tmp/gemini_review_result.txt
```

### Update Skills

Keep your skills up to date:

```bash
cd ~/.claude/skills/
git pull origin main
```

### Verify All Dependencies

Quick check for all requirements:

```bash
# Check Node.js
node --version

# Check npm
npm --version

# Check Gemini CLI
gemini --version

# Check Git
git --version

# Check API key
echo $GEMINI_API_KEY
```

### Clean Temporary Files

If you encounter issues, try cleaning temporary files:

```bash
# macOS
rm -f $TMPDIR/gemini_review_result.txt

# Linux
rm -f /tmp/gemini_review_result.txt
```

## Still Having Issues?

1. Check the [SETUP.md](./SETUP.md) for detailed installation instructions
2. Review the [README.md](./README.md) for usage examples
3. Check individual skill directories for skill-specific documentation
4. Open an issue on the repository with:
   - Your operating system and version
   - Output of `node --version`, `npm --version`, `gemini --version`
   - The full error message
   - Steps to reproduce the issue

## Common Error Messages

| Error | Likely Cause | Quick Fix |
|-------|--------------|-----------|
| `command not found: gemini` | Gemini CLI not installed | `npm install -g @google/gemini-cli` |
| `GEMINI_API_KEY not set` | API key not configured | `export GEMINI_API_KEY="..."` |
| `No staged changes` | Nothing staged | `git add <files>` |
| `permission denied` | Script not executable | `chmod +x *.sh` |
| `429 Resource exhausted` | API quota exceeded | Wait or upgrade plan |
| `401 Unauthorized` | Invalid API key | Generate new key |
