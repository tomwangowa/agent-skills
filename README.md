
這個 repository 計畫收錄我在實務工作中使用的 Claude Code Skills，
主要目的是將一些重複性高、容易出錯、但又需要一致品質的工程任務（例如 code review、分析 diff、工具串接）流程化、標準化。

這些 Skills 都是以「工程可預期、可審計、不依賴魔法」為設計原則，
可以直接安裝到本機的 Claude Code 環境中使用，也歡迎依照團隊需求自行擴充或修改。

# Claude Code Skills

A collection of custom skills for [Claude Code](https://claude.ai/code) that extend its capabilities with specialized workflows.

## What are Skills?

Skills are user-defined prompts that Claude Code can invoke when specific phrases are detected. They allow you to create reusable, specialized workflows that integrate with external tools and scripts.

## Available Skills

| Skill | Description |
|-------|-------------|
| [code-review-gemini](./code-review-gemini/) | Perform code reviews on staged changes using the Gemini CLI |

## Quick Start

### Prerequisites

- [Claude Code CLI](https://claude.ai/code) installed
- [Node.js](https://nodejs.org/) (for Gemini CLI)
- Git

### Installation

**Option 1: Clone to skills directory (Recommended)**

```bash
# Clone this repository to your Claude Code skills directory
git clone <repository-url> ~/.claude/skills
```

**Option 2: Symlink existing clone**

```bash
# If you've already cloned this repo elsewhere
ln -s /path/to/cloned/repo ~/.claude/skills
```

### Setup Dependencies

Install the Gemini CLI for code review functionality:

```bash
npm install -g @google/gemini-cli
```

Configure Gemini CLI with your API key:

```bash
# Set your Gemini API key
export GEMINI_API_KEY="your-api-key-here"

# Or add to your shell profile (~/.bashrc, ~/.zshrc, etc.)
echo 'export GEMINI_API_KEY="your-api-key-here"' >> ~/.zshrc
```

Get your API key from: [Google AI Studio](https://aistudio.google.com/app/apikey)

### Verify Installation

```bash
# Check if Claude Code can see your skills
ls ~/.claude/skills/

# Test the Gemini CLI
gemini "Hello, test"
```

## Usage

### Using code-review-gemini

1. Stage your changes:
   ```bash
   git add <files>
   ```

2. In Claude Code, use natural language to trigger the review:
   ```
   > review the staged files
   > check the code quality before I commit
   > analyze my staged changes
   ```

3. Claude Code will:
   - Run the review script
   - Show you which files are being reviewed
   - Provide a prioritized summary of findings

### Example Workflow

```bash
# Make some changes to your code
vim src/app.js

# Stage the changes
git add src/app.js

# Open Claude Code and request a review
claude
> Review the staged files before I commit
```

Claude will analyze your changes and provide feedback on:
- Potential bugs or security issues
- Code quality and best practices
- Readability and maintainability
- Suggested improvements

## Creating a New Skill

1. Create a new directory for your skill:
   ```bash
   mkdir my-skill
   ```

2. Create a `SKILL.md` file with the following structure:
   ```markdown
   ---
   name: My Skill Name
   description: Brief description of what this skill does and when to use it.
   ---

   # My Skill Name

   ## Instructions

   Describe when and how Claude should use this skill.

   ## Examples

   Provide example trigger phrases and expected behavior.
   ```

3. (Optional) Add supporting scripts in a `scripts/` subdirectory.

## Skill Structure

```
skill-name/
├── SKILL.md           # Required: Skill definition and instructions
├── scripts/           # Optional: Supporting shell scripts
│   └── my_script.sh
└── other_files/       # Optional: Any other resources
```

## Dependencies

Each skill may have its own dependencies. Check the individual skill directories for specific requirements.

### code-review-gemini

- [Gemini CLI](https://github.com/google-gemini/gemini-cli): `npm install -g @google/gemini-cli`
- Git (must be run inside a git repository)

## Documentation

- **[SETUP.md](./SETUP.md)** - Detailed setup and installation guide
- **[TROUBLESHOOTING.md](./TROUBLESHOOTING.md)** - Common issues and solutions
- **[CONTRIBUTING.md](./CONTRIBUTING.md)** - Guide for creating new skills or improving existing ones
- **[CLAUDE.md](./CLAUDE.md)** - Instructions for Claude Code when working in this repository

## Team Setup

For team deployment, see the [Team Setup](./SETUP.md#team-setup) section in SETUP.md.

Quick installation for team members:

```bash
# Clone and run installation script
git clone <repository-url> ~/claude-code-skills
cd ~/claude-code-skills
bash install.sh
```

## Contributing

We welcome contributions! Please see [CONTRIBUTING.md](./CONTRIBUTING.md) for guidelines.

## Troubleshooting

Having issues? Check [TROUBLESHOOTING.md](./TROUBLESHOOTING.md) for solutions to common problems.

## License

MIT
