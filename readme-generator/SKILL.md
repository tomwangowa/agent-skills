---
name: readme-generator
description: Generate comprehensive README files with project overview, setup instructions, usage examples, dependencies, and contributing guidelines. Use this Skill when the user asks to create README, generate documentation, or write project documentation.
---

# README Generator

## Purpose

This Skill generates comprehensive, production-ready README.md files by:
1. Analyzing the current project structure and tech stack
2. Gathering relevant project information
3. Generating a complete README with all essential sections
4. Saving to the project root directory

The Skill eliminates manual README writing by creating well-structured documentation automatically.

---

## Instructions

When the user expresses intent to generate a README (for example: "create readme", "generate readme", "write project documentation"), follow these steps strictly.

### Step 1: Analyze Project Context

**1.1 Identify Tech Stack:**
- Use Glob to find tech stack indicators:
  - `package.json` → Node.js/JavaScript
  - `Cargo.toml` → Rust
  - `go.mod` → Go
  - `requirements.txt` or `pyproject.toml` → Python
  - `Gemfile` → Ruby
  - `pom.xml` or `build.gradle` → Java
  - `*.csproj` → C#/.NET

**1.2 Gather Project Information:**
- Read package manager files for:
  - Project name
  - Version
  - Description
  - Dependencies
  - Scripts/commands
- Use Glob to identify:
  - Entry points (main.js, index.js, main.py, etc.)
  - Test directories (tests/, test/, __tests__)
  - Documentation directories (docs/, documentation/)
  - Configuration files (.env.example, config/)

**1.3 Check for Existing README:**
- Look for `README.md` or `README` in project root
- If exists, ask user: "Overwrite existing README or create README-new.md?"

### Step 2: Gather User Input

Ask clarifying questions if information is missing:

**Required Information:**
- What does this project do? (If not clear from package.json description)
- Who is the target audience? (developers, end-users, both)
- Any special setup requirements? (API keys, environment variables, external services)

**Optional Information:**
- Notable features to highlight?
- Known issues or limitations?
- Roadmap or future plans?

### Step 3: Generate Complete README

Using Claude's capabilities, generate a comprehensive README.md with ALL essential sections:

#### Structure

```markdown
# Project Name

[Badges section - if applicable: build status, version, license]

## Overview

[2-3 paragraphs describing what the project does, key features, and why it exists]

## Features

- Feature 1: Brief description
- Feature 2: Brief description
- Feature 3: Brief description

## Prerequisites

[List required software, tools, accounts]
- Node.js >= 16.0.0
- PostgreSQL >= 13
- API key from [service name]

## Installation

### 1. Clone the repository
\```bash
git clone [repository-url]
cd [project-name]
\```

### 2. Install dependencies
\```bash
[package manager install command]
\```

### 3. Configure environment
\```bash
cp .env.example .env
# Edit .env with your configuration
\```

### 4. Initialize database (if applicable)
\```bash
[database setup commands]
\```

## Usage

### Basic Usage

\```[language]
[Basic usage example with actual code]
\```

### Advanced Usage

\```[language]
[Multi-step example showing key features]
\```

### Configuration

[Explain key configuration options]

## Development

### Running Locally

\```bash
[development server command]
\```

### Running Tests

\```bash
[test command]
\```

### Building for Production

\```bash
[build command]
\```

## Project Structure

\```
project-root/
├── src/            # Source code
├── tests/          # Test files
├── docs/           # Documentation
├── config/         # Configuration files
└── README.md       # This file
\```

## Dependencies

### Core Dependencies
[List main dependencies with brief explanations]

### Development Dependencies
[List dev dependencies if relevant]

## Contributing

We welcome contributions! Please follow these steps:

1. Fork the repository
2. Create your feature branch (\`git checkout -b feature/amazing-feature\`)
3. Commit your changes (\`git commit -m 'Add some amazing feature'\`)
4. Push to the branch (\`git push origin feature/amazing-feature\`)
5. Open a Pull Request

### Development Guidelines
- Write tests for new features
- Follow existing code style
- Update documentation as needed
- Ensure all tests pass before submitting PR

## License

[License type - e.g., MIT, Apache 2.0, GPL-3.0]

## Support

- Documentation: [link]
- Issues: [GitHub issues link]
- Discussions: [link if applicable]

## Acknowledgments

[Credits, inspirations, third-party resources used]
\```

#### Content Guidelines

**Project Overview:**
- Clearly state what the project does in the first paragraph
- Explain the problem it solves
- Highlight key differentiators

**Installation Instructions:**
- Provide step-by-step commands that actually work
- Include all prerequisites
- Mention common pitfalls

**Usage Examples:**
- Show real, working code examples
- Start with basic examples, then show advanced usage
- Include expected output

**Contributing Section:**
- Clear process for contributing
- Link to CONTRIBUTING.md if it exists
- Mention code style and testing requirements

**Keep It Scannable:**
- Use clear headings
- Use bullet points and code blocks
- Keep paragraphs short (2-4 sentences)

### Step 4: Save README

**4.1 Determine Filename:**
- Default: `README.md` in project root
- If overwrite declined: `README-new.md`

**4.2 Write File:**
- Use Write tool to create the README
- Confirm success to user

**4.3 Provide Next Steps:**
- Review the generated README
- Customize sections as needed
- Add project-specific details
- Commit to version control

---

## Examples

### Example 1: Node.js Project

**User Input:**
```
Create a README for this project
```

**Expected Behavior:**
1. Finds `package.json`
2. Extracts project name, description, dependencies, scripts
3. Identifies it's a Node.js project
4. Generates README with npm-specific commands
5. Includes sections for:
   - Installation via npm
   - Running with `npm start`
   - Testing with `npm test`
   - All dependencies from package.json

### Example 2: Python Project

**User Input:**
```
Generate project documentation
```

**Expected Behavior:**
1. Finds `requirements.txt` or `pyproject.toml`
2. Identifies it's a Python project
3. Generates README with pip/poetry commands
4. Includes:
   - Virtual environment setup
   - Installation via pip
   - Running with `python main.py`
   - Testing with pytest

### Example 3: Go Project

**User Input:**
```
Write a README
```

**Expected Behavior:**
1. Finds `go.mod`
2. Extracts module name
3. Generates README with Go-specific commands
4. Includes:
   - Installation via `go get`
   - Building with `go build`
   - Testing with `go test`

---

## Workflow Summary

### Step 1: Analyze (5-10 seconds)
1. Use Glob to find tech stack files
2. Read package manager files
3. Identify project structure

### Step 2: Gather (5-10 seconds)
1. Extract project metadata
2. Ask user for missing info (if needed)
3. Confirm output location

### Step 3: Generate (15-20 seconds)
1. Create comprehensive README content
2. Populate all sections with meaningful content
3. Use project-specific commands and examples

### Step 4: Save (1-2 seconds)
1. Write README.md to project root
2. Confirm success
3. Provide next steps

**Total Time:** ~30-40 seconds for complete README generation

---

## Best Practices

### README Quality Standards

**✅ DO:**
- Start with a clear, concise description
- Include working code examples
- Provide step-by-step installation
- List all prerequisites
- Use badges for at-a-glance status info
- Keep formatting consistent
- Include troubleshooting section if applicable

**❌ DON'T:**
- Assume prior knowledge
- Skip installation steps
- Use vague language without metrics ("easy", "fast", "just")
- Include outdated information
- Make it too long (aim for scannable)
- Forget to update when project changes

### Section Priorities

**Critical (Always Include):**
1. Project description
2. Installation instructions
3. Basic usage example
4. Dependencies

**Important (Usually Include):**
5. Prerequisites
6. Configuration options
7. Contributing guidelines
8. License

**Optional (As Needed):**
9. Advanced usage
10. Troubleshooting
11. FAQ
12. Roadmap

---

## Constraints

- Only generate content based on actual project files
- Don't make up features that don't exist
- Don't include placeholder text like "[TODO]"
- Use actual commands that will work for the tech stack
- Respect existing README if user wants to keep it

---

## Error Handling

### No Tech Stack Found

If no package manager files found:
```
Warning: Could not identify tech stack automatically.

Please specify:
- What language/framework is this project using?
- What package manager (npm, pip, cargo, etc.)?
```

### Existing README Found

```
Found existing README.md.

Options:
1. Overwrite (backup will be suggested)
2. Create README-new.md instead
3. Cancel

Your choice?
```

### Insufficient Information

If project appears empty or has minimal files:
```
This appears to be a new or minimal project.

To generate a helpful README, please provide:
1. What will this project do?
2. What tech stack will you use?
3. Who is the target audience?
```

---

## Security Considerations

### Input Sanitization

**1. Project Metadata**
- Project name, description from package.json are treated as trusted
- User-provided input (answers to questions) is used only for documentation
- No code execution from user input

**2. File Path Safety**
- All file paths are validated before reading
- Uses Glob/Read tools which have built-in path safety
- No directory traversal (../, ..\\) in generated paths
- README always written to project root (validated location)

**3. Content Escaping**
- Generated README is pure markdown (no HTML execution)
- Code examples wrapped in proper markdown code blocks
- No script injection possible in static markdown

### External Dependencies

**1. Package Manager Files**
- Reads package.json, requirements.txt, etc. from local filesystem
- These are trusted as part of the user's project
- No external API calls or network operations

**2. Generated Content Safety**
- No execution of project code during analysis
- Read-only operations on project files
- No modification of project files (except README creation)

### File Operations

**1. README Creation**
- Confirms with user before overwriting existing README
- Offers backup option (README-new.md)
- Write operations use Claude Code's Write tool (safe)

**2. Project Analysis**
- Read-only scanning of project structure
- No execution of scripts found in project
- No modification of project configuration

### Best Practices for Users

**✅ Safe Operations:**
- Generate README for local projects
- Review generated content before committing
- Use in version-controlled projects (easy to revert)

**⚠️ Considerations:**
- Review generated content for accuracy
- Check that sensitive info not included (API keys, credentials)
- Validate installation commands before sharing with others

**❌ Avoid:**
- Generating README for projects with sensitive/confidential info without review
- Blindly accepting generated content without verification

### Privacy

- All operations are local (no external API calls)
- No telemetry or logging of project information
- Project structure and content stay on user's machine
- Generated README contains only information from local project files

---

## Related Skills

- **spec-generator**: Generate complete specification documents
- **spec-review-assistant**: Review specification documents
- **commit-msg-generator**: Generate commit messages for README updates

---

## Version History

| Version | Date | Changes |
|---------|------|---------|
| 1.0.0 | 2026-01-22 | Initial release |
|  |  | Automatic README generation from project analysis |
|  |  | Support for Node.js, Python, Go, Rust, Ruby, Java, C# |
|  |  | Comprehensive sections following best practices |

---

**Created:** 2026-01-22
**Pattern:** Document Generator
