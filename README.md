
這個 repository 計畫收錄我在實務工作中使用的 Claude Code Skills，
主要目的是將一些重複性高、容易出錯、但又需要一致品質的工程任務（例如 code review、生成 commit message、分析 git history、生成並且審查規格書等）流程化、標準化。

這些 Skills 都是以「工程可預期、可審計、不依賴魔法」為設計原則，
可以直接安裝到本機的 Claude Code 環境中使用，也歡迎依照團隊需求自行擴充或修改。

另外，我在 Claude Code 裡加入「Review Code with Gemini」的 Skill，主要目的不是追求多一個 AI，而是降低單一模型的盲點。Claude 負責主要開發與上下文理解，但它在檢視自己產生的程式碼時，容易對既有結構過度合理化；Gemini 則扮演相對保守的 reviewer，特別擅長抓邏輯漏洞、邊界條件與防禦性不足的地方。

目前流程是：每完成一個小任務就自動調用 Gemini review，依回饋修正直到 fully approved，確保風險在早期被攔下；最後再用 Gemini 產生一致且可讀的 commit message。這樣做的價值在於把 code review 前移、系統化，並模擬實際團隊中「作者與 reviewer 分工」的狀態，而不是取代人類判斷。

---

# Claude Code Skills

A collection of custom skills for [Claude Code](https://claude.ai/code) that extend its capabilities with specialized workflows.

## 🚀 Quick Start - 30 Second Overview

**First time here?** Check out this visual presentation for a quick understanding of the complete workflow:

**[📄 A Developer's Day, Reimagined](./docs/AI_Developer_Workflow.pdf)** ⭐ Recommended Entry Point

Complete workflow from idea to deployment | 3 days → 1 day efficiency boost | Dual-AI collaboration value | 7 Skills visualized

**More Resources**: [UI/UX Skills Plan](./docs/UI-UX-Skills-Plan.md) · [Skills Roadmap](./SKILLS_ROADMAP.md) · [Docs Index](./docs/README.md)

---

## What are Skills?

Skills are user-defined prompts that Claude Code can invoke when specific phrases are detected. They allow you to create reusable, specialized workflows that integrate with external tools and scripts.

## Available Skills

### 📊 Skills by Category

#### 🔍 Code Quality & Review (3 skills)

| Skill | Description | Score |
|-------|-------------|-------|
| [tm-code-review-gemini](./tm-code-review-gemini/) | Automated code review on staged changes using Gemini AI - detects security issues, bugs, and quality problems | 88/100 ✅ |
| [tm-pr-review-assistant](./tm-pr-review-assistant/) | Comprehensive pull request reviewer with structured feedback and risk assessment | ⭐ |
| [tm-skill-auditor](./tm-skill-auditor/) ⭐ NEW | Meta-skill that audits other skills for quality, security, and production readiness | 103/100 ✅ |

#### 📝 Documentation & Specification (2 skills)

| Skill | Description | Score |
|-------|-------------|-------|
| [tm-spec-generator](./tm-spec-generator/) | Generate complete specification documents (150+ lines, 8 sections) from simple ideas | ⭐ |
| [tm-spec-review-assistant](./tm-spec-review-assistant/) | Review specs before implementation - 5-dimensional analysis for completeness, feasibility, clarity | ⭐ |

#### 🔀 Git & Version Control (2 skills)

| Skill | Description | Score |
|-------|-------------|-------|
| [tm-commit-msg-generator](./tm-commit-msg-generator/) | Generate high-quality commit messages following Conventional Commits specification | ⭐ |
| [tm-code-story-teller](./tm-code-story-teller/) | Analyze git history to tell the evolutionary story and design decisions of code files | ⭐ |

#### 🎨 Design & UI/UX (1 skill)

| Skill | Description | Score |
|-------|-------------|-------|
| [tm-ui-design-analyzer](./tm-ui-design-analyzer/) | Analyze UI/UX from screenshots - 6-dimensional analysis covering usability, accessibility, visual design | ⭐ |

#### 🚀 Productivity & Content Creation (3 skills)

| Skill | Description | Score |
|-------|-------------|-------|
| [tm-interactive-presentation-generator](./tm-interactive-presentation-generator/) ⭐ NEW | Generate interactive presentations (reveal.js/Marp/Slidev) with 20 professional styles | 75/100 ✅ |
| [tm-work-log-analyzer](./tm-work-log-analyzer/) | Analyze work logs to track evolution, manage TODOs, aggregate activities - 5 query types | ⭐ |
| [tm-activity-logger](./tm-activity-logger/) | Record work activities from current session for cross-session tracking and reporting | ⭐ |

---

### 📈 Quality Scores

Skills audited by [tm-skill-auditor](./tm-skill-auditor/):
- **103/100** - tm-skill-auditor (meta-validated ✅)
- **88/100** - tm-code-review-gemini (production-ready ✅)
- **75/100** - tm-interactive-presentation-generator (production-ready ✅)

**Total:** 11 skills across 5 categories

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

### Using tm-code-review-gemini

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

### Using tm-commit-msg-generator

1. Stage your changes:
   ```bash
   git add <files>
   ```

2. In Claude Code, request a commit message:
   ```
   > generate commit message
   > help me write a commit message
   > create commit description
   ```

3. Claude Code will:
   - Analyze the staged changes
   - Generate a commit message following Conventional Commits
   - Provide a command to use the message

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

### Using tm-activity-logger

The tm-activity-logger skill helps you track work activities across multiple Claude Code sessions.

**Initial Setup:**

```bash
# Initialize the activity logger (creates directory structure)
~/.claude/skills/tm-activity-logger/scripts/init_activities.sh init
```

**Logging Activities:**

You can log activities in two ways:

1. **Direct command:**
   ```bash
   ~/.claude/skills/tm-activity-logger/scripts/log_activity.sh \
     -d "Implemented user authentication" \
     -t task_completed \
     -c "Added OAuth2 support" \
     --tags "security,auth"
   ```

2. **Via Claude Code:**
   ```
   > log this activity
   > record what I just did
   > save session activity
   ```

**Activity Types:**
- `task_completed` - Finished a task or feature
- `bug_fixed` - Resolved a bug
- `refactoring` - Code refactoring work
- `research` - Investigation or exploration
- `documentation` - Documentation updates
- `review` - Code review activities

**Managing Activities:**

```bash
# View current session info
~/.claude/skills/tm-activity-logger/scripts/init_activities.sh info

# List all activity records
~/.claude/skills/tm-activity-logger/scripts/init_activities.sh list

# Show statistics by type
~/.claude/skills/tm-activity-logger/scripts/init_activities.sh stats

# Archive old activities (default: 30 days)
~/.claude/skills/tm-activity-logger/scripts/init_activities.sh archive 30
```

**What Gets Recorded:**
- Session ID (unique per session)
- Timestamp
- Project path and name
- Git branch and remote (with credentials stripped)
- Changed files (from git status)
- Recent commits
- Activity type and description
- Context and tags

**Activity Records Location:**
- Active: `~/.claude/activities/`
- Archived: `~/.claude/activities/processed/`

**Integration with work-log-analyzer:**
Activity records can be aggregated and analyzed using the work-log-analyzer skill for comprehensive work logging across multiple projects and sessions.

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

### tm-code-review-gemini

- [Gemini CLI](https://github.com/google-gemini/gemini-cli): `npm install -g @google/gemini-cli`
- Git (must be run inside a git repository)

### tm-commit-msg-generator

- [Gemini CLI](https://github.com/google-gemini/gemini-cli): `npm install -g @google/gemini-cli`
- Git (must be run inside a git repository with staged changes)

### tm-code-story-teller

- [Gemini CLI](https://github.com/google-gemini/gemini-cli): `npm install -g @google/gemini-cli`
- Git (must be run inside a git repository with commit history)

### tm-pr-review-assistant

- [Gemini CLI](https://github.com/google-gemini/gemini-cli): `npm install -g @google/gemini-cli`
- [GitHub CLI](https://cli.github.com/): Install from https://cli.github.com/
- Git with access to the PR repository

### tm-spec-review-assistant

- [Gemini CLI](https://github.com/google-gemini/gemini-cli): `npm install -g @google/gemini-cli`
- jq: `brew install jq` (macOS) or `apt-get install jq` (Ubuntu)
- Git (optional, for codebase integration)

### tm-spec-generator

- **No external dependencies required!** Uses Claude Code's native capabilities
- Works immediately out of the box

### tm-ui-design-analyzer

- **No external dependencies required!** Uses Claude Code's native multimodal capabilities
- Works immediately out of the box
- Can analyze PNG, JPG, and other image formats

### tm-work-log-analyzer

- **Core features:** No external dependencies - uses Claude Code's native capabilities
- **Activity Aggregation feature:** Requires `jq` and `date` (standard on most systems)
  - `jq` - JSON processor: `brew install jq` (macOS) or `apt-get install jq` (Ubuntu)
  - `date` - Date utilities (built-in on macOS/Linux)
- Analyzes Markdown, plain text, and various log formats
- Aggregates and filters activity records from tm-activity-logger

### tm-activity-logger

- **Required dependencies:**
  - `jq` - JSON processor: `brew install jq` (macOS) or `apt-get install jq` (Ubuntu)
  - `git` - Version control system
- **Optional:** `openssl` (falls back to `/dev/urandom` or `$RANDOM`)

### tm-interactive-presentation-generator

- **No external dependencies required!** Works out of the box
- Generates reveal.js HTML, Marp markdown, or Slidev presentations
- Includes 20 professional style templates (324KB)
- All styles bundled - zero configuration needed

### tm-skill-auditor

- **Required dependencies:**
  - `bash` 4.0+ (standard on macOS/Linux)
  - `grep`, `sed`, `find`, `mktemp` (standard Unix tools)
- **Optional:** Gemini CLI (for AI-powered semantic analysis)
- Performs automated quality audits on skills in < 5 seconds

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
