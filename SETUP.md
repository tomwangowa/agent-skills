# Setup Guide

Detailed setup instructions for Claude Code Skills.

## Table of Contents

- [Initial Setup](#initial-setup)
- [Installing Dependencies](#installing-dependencies)
- [Configuration](#configuration)
- [Verification](#verification)
- [Team Setup](#team-setup)

## Initial Setup

### Step 1: Install Claude Code

If you haven't already installed Claude Code:

```bash
# Follow the official installation guide at:
# https://claude.ai/code
```

### Step 2: Clone the Skills Repository

Choose one of the following methods:

#### Method A: Direct Clone (Easiest)

```bash
# Clone directly to the skills directory
git clone <repository-url> ~/.claude/skills

# If ~/.claude/skills already exists, clone to a subdirectory
git clone <repository-url> ~/.claude/skills/team-skills
```

#### Method B: Symlink (For Development)

If you're developing skills or want to keep the repo in a different location:

```bash
# Clone to your preferred location
git clone <repository-url> ~/projects/claude-skills

# Create a symlink
ln -s ~/projects/claude-skills ~/.claude/skills
```

#### Method C: Multiple Skill Repositories

If you have multiple skill repositories:

```bash
# Claude Code scans all subdirectories in ~/.claude/skills/
mkdir -p ~/.claude/skills
cd ~/.claude/skills
git clone <repo1-url> repo1
git clone <repo2-url> repo2
```

## Installing Dependencies

### Install Node.js

**macOS (using Homebrew):**
```bash
brew install node
```

**Ubuntu/Debian:**
```bash
curl -fsSL https://deb.nodesource.com/setup_lts.x | sudo -E bash -
sudo apt-get install -y nodejs
```

**Windows:**
Download from [nodejs.org](https://nodejs.org/)

### Install Gemini CLI

```bash
npm install -g @google/gemini-cli

# Verify installation
gemini --version
```

## Configuration

### Get Your Gemini API Key

1. Visit [Google AI Studio](https://aistudio.google.com/app/apikey)
2. Sign in with your Google account
3. Click "Create API Key"
4. Copy the generated key

### Set Up Environment Variables

**For bash (~/.bashrc):**
```bash
echo 'export GEMINI_API_KEY="your-api-key-here"' >> ~/.bashrc
source ~/.bashrc
```

**For zsh (~/.zshrc):**
```bash
echo 'export GEMINI_API_KEY="your-api-key-here"' >> ~/.zshrc
source ~/.zshrc
```

**For fish (~/.config/fish/config.fish):**
```bash
echo 'set -gx GEMINI_API_KEY "your-api-key-here"' >> ~/.config/fish/config.fish
source ~/.config/fish/config.fish
```

**Temporary (current session only):**
```bash
export GEMINI_API_KEY="your-api-key-here"
```

### Optional: Configure Default Gemini Model

You can set a default model for the Gemini CLI:

```bash
# Add to your shell profile
export GEMINI_MODEL="gemini-3-flash-preview"
# Or you can configure the preferred model using the Gemini CLI slash command "/model" 
```

## Verification

### Verify Directory Structure

```bash
ls -la ~/.claude/skills/
# Should show your cloned skills repository
```

### Test Gemini CLI

```bash
# Test with a simple prompt
gemini "Hello, world!"

# Should return a response from Gemini
```

### Test Code Review Script

```bash
# Navigate to a git repository
cd ~/your-project

# Make some changes and stage them
echo "test" >> test.txt
git add test.txt

# Run the review script directly
bash ~/.claude/skills/code-review-gemini/scripts/review_with_gemini.sh
```

### Test with Claude Code

```bash
# Start Claude Code in a git repository
cd ~/your-project
claude

# In Claude Code, try:
> Review the staged files
```

## Team Setup

### Sharing Skills Across a Team

#### Option 1: Git Submodule (Recommended for teams)

Add skills as a submodule to your project:

```bash
# In your project repository
git submodule add <skills-repo-url> .claude/skills
git submodule init
git submodule update
```

Team members clone with:
```bash
git clone --recurse-submodules <your-project-url>
```

#### Option 2: Shared Installation Script

Create an installation script for your team:

```bash
#!/bin/bash
# install-skills.sh

set -e

echo "Installing Claude Code Skills..."

# Clone skills repository
if [ ! -d ~/.claude/skills ]; then
  mkdir -p ~/.claude/skills
fi

cd ~/.claude/skills
git clone <repository-url> team-skills

# Install dependencies
npm install -g @google/gemini-cli

echo "✓ Skills installed successfully!"
echo "Please set your GEMINI_API_KEY environment variable."
echo "Visit: https://aistudio.google.com/app/apikey"
```

#### Option 3: Team Configuration File

Create a shared configuration file in your project:

```yaml
# .claude/team-skills.yaml
skills:
  - name: code-review-gemini
    repo: <repository-url>
    dependencies:
      - gemini-cli
```

### API Key Management

**Important:** Never commit API keys to git!

For teams, consider:

1. **Individual Keys:** Each team member uses their own API key
2. **Shared Key:** Store in a secure password manager (1Password, LastPass, etc.)
3. **Environment Variables:** Document in your team wiki

## Troubleshooting

If you encounter issues, see [TROUBLESHOOTING.md](./TROUBLESHOOTING.md).

## Next Steps

- Read the [README.md](./README.md) for usage examples
- Check [TROUBLESHOOTING.md](./TROUBLESHOOTING.md) for common issues
- Explore skill customization in individual skill directories
