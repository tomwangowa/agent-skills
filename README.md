# Claude Code Skills

A collection of custom skills for [Claude Code](https://claude.ai/code) that extend its capabilities with specialized workflows.

## What are Skills?

Skills are user-defined prompts that Claude Code can invoke when specific phrases are detected. They allow you to create reusable, specialized workflows that integrate with external tools and scripts.

## Available Skills

| Skill | Description |
|-------|-------------|
| [code-review-gemini](./code-review-gemini/) | Perform code reviews using the Gemini CLI |

## Installation

Skills in this repository are automatically available to Claude Code when placed in the `~/.claude/skills/` directory.

```bash
# This repository should be located at:
~/.claude/skills/
```

## Usage

Simply use natural language to trigger a skill. For example:

```
> review the changed files
> give me a code review
> analyze the code changes
```

Claude Code will automatically detect the intent and invoke the appropriate skill.

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

## License

MIT
