# readme-generator

Generate comprehensive README.md files automatically by analyzing your project structure.

## Overview

The readme-generator skill creates production-ready README documentation by:
- Automatically detecting your tech stack (Node.js, Python, Go, Rust, Ruby, Java, C#)
- Analyzing project structure and dependencies
- Generating all essential sections with meaningful content
- Creating working installation and usage examples

## Features

- **Auto-detection**: Identifies tech stack from package manager files
- **Comprehensive Sections**: Includes overview, installation, usage, development, contributing, and more
- **Tech Stack Aware**: Generates platform-specific commands (npm, pip, cargo, etc.)
- **Safe Operations**: Read-only analysis, confirms before overwriting
- **Fast Generation**: Complete README in ~30-40 seconds

## When to Use

Trigger this skill with phrases like:
- "create readme"
- "generate readme"
- "write project documentation"
- "create README.md"

## Quick Start

### Basic Usage

In your project directory:
```
create a readme for this project
```

The skill will:
1. Analyze your project structure
2. Identify tech stack and dependencies
3. Ask clarifying questions if needed
4. Generate comprehensive README.md
5. Save to project root

### With Existing README

If README.md exists, you'll be prompted:
```
Found existing README.md.

Options:
1. Overwrite (backup suggested)
2. Create README-new.md instead
3. Cancel
```

## Generated Sections

The readme-generator creates READMEs with:

1. **Project Overview** - Description and key features
2. **Prerequisites** - Required software and accounts
3. **Installation** - Step-by-step setup instructions
4. **Usage** - Basic and advanced examples
5. **Development** - Running locally, testing, building
6. **Project Structure** - Directory layout
7. **Dependencies** - Core and dev dependencies
8. **Contributing** - Guidelines for contributors
9. **License** - License information
10. **Support** - Documentation and contact info

## Supported Tech Stacks

- **Node.js/JavaScript** (package.json, npm/yarn/pnpm)
- **Python** (requirements.txt, pyproject.toml, pip/poetry)
- **Go** (go.mod, go get)
- **Rust** (Cargo.toml, cargo)
- **Ruby** (Gemfile, bundle)
- **Java** (pom.xml, build.gradle, maven/gradle)
- **C#/.NET** (*.csproj, dotnet)

## Examples

### Node.js Project
```
User: "Generate a README"

Output: README.md with:
- npm install commands
- npm start/test/build scripts
- All package.json dependencies
- Node.js version requirements
```

### Python Project
```
User: "Create project documentation"

Output: README.md with:
- pip install instructions
- Virtual environment setup
- python main.py usage
- pytest commands
```

## Security

This skill:
- ✅ Performs read-only analysis of your project
- ✅ All operations are local (no external API calls)
- ✅ Confirms before overwriting files
- ✅ No execution of project code
- ✅ No modification of project files (except README creation)

See [SKILL.md](SKILL.md#security-considerations) for detailed security information.

## Error Handling

### No Tech Stack Detected
If the skill can't identify your tech stack, it will ask:
- What language/framework are you using?
- What package manager?

### Insufficient Project Information
For minimal projects, you'll be prompted for:
- Project purpose
- Target audience
- Key features

## Related Skills

- **spec-generator** - Generate complete specification documents
- **commit-msg-generator** - Generate commit messages for README updates

## Troubleshooting

### Issue: Generated README is too generic
**Solution**: Ensure your project has:
- Package manager file (package.json, requirements.txt, etc.)
- Some source code files
- Clear project structure

### Issue: Skill doesn't detect my tech stack
**Solution**:
- Verify package manager file exists in project root
- Check file format is correct
- Provide tech stack manually when prompted

### Issue: Want to customize sections
**Solution**:
- Generate initial README
- Manually edit sections as needed
- Skill provides solid foundation to build on

## Version

**Version**: 1.0.0
**Created**: 2026-01-22
**Pattern**: Document Generator

## License

Part of Claude Code Skills collection.
