# Contributing to Claude Code Skills

Thank you for your interest in contributing! This guide will help you create new skills or improve existing ones.

## Table of Contents

- [Getting Started](#getting-started)
- [Creating a New Skill](#creating-a-new-skill)
- [Skill Best Practices](#skill-best-practices)
- [Testing Your Skill](#testing-your-skill)
- [Submitting Changes](#submitting-changes)
- [Code Review Process](#code-review-process)

## Getting Started

### Prerequisites

- Familiarity with Claude Code
- Basic understanding of bash scripting (for skills with scripts)
- Git knowledge

### Development Setup

1. Fork and clone the repository
2. Create a new branch for your feature
3. Make your changes
4. Test thoroughly
5. Submit a pull request

## Creating a New Skill

### Step 1: Plan Your Skill

Before coding, consider:

- **Purpose:** What problem does this skill solve?
- **Trigger phrases:** What natural language should invoke it?
- **Dependencies:** What tools or APIs does it need?
- **Output:** What information will it provide?

### Step 2: Create the Directory Structure

```bash
cd ~/.claude/skills/
mkdir my-new-skill
cd my-new-skill
```

### Step 3: Create SKILL.md

The `SKILL.md` file is required. It defines your skill's behavior.

**Template:**

```markdown
---
name: My Skill Name
description: Brief description. Use this Skill when the user asks to [describe use cases].
---

# My Skill Name

## Purpose

Explain what this skill does and why it's useful.

## Instructions

When the user expresses intent to [describe intent], follow these steps:

1. [Step 1]
2. [Step 2]
3. [Step 3]

### Execution steps

Detailed instructions for Claude Code on how to execute this skill.

### Output requirements

What Claude should provide to the user after execution.

## Constraints

- List any limitations
- Specify what the skill should NOT do

## Examples

**User:**
> Example trigger phrase

**Expected behavior:**
- What should happen
- Expected output format
```

### Step 4: Create Supporting Scripts (Optional)

If your skill needs external scripts:

```bash
mkdir scripts
touch scripts/my_script.sh
chmod +x scripts/my_script.sh
```

**Script template:**

```bash
#!/bin/bash
set -euo pipefail

############################
# Configuration
############################

OUTPUT_FILE="${TMPDIR:-/tmp}/my_skill_result.txt"

############################
# Pre-flight checks
############################

if ! command -v required_tool >/dev/null 2>&1; then
  echo "Error: 'required_tool' is not installed." >&2
  echo "Install it with: ..." >&2
  exit 1
fi

############################
# Main logic
############################

# Your script logic here

############################
# Output result
############################

cat "$OUTPUT_FILE"
```

### Step 5: Add Documentation

Create a README in your skill directory:

```markdown
# My Skill Name

Brief description.

## Dependencies

- Tool 1: Installation instructions
- Tool 2: Installation instructions

## Configuration

Required environment variables or setup.

## Usage

Example commands and expected output.

## Troubleshooting

Common issues and solutions.
```

## Skill Best Practices

### SKILL.md Guidelines

1. **Clear Description:** Make it obvious when this skill should be used
2. **Specific Triggers:** List common phrases that should invoke the skill
3. **Step-by-Step Instructions:** Claude should know exactly what to do
4. **Error Handling:** Describe how to handle failures
5. **Output Format:** Specify how results should be presented

### Script Guidelines

1. **Robust Error Handling:** Use `set -euo pipefail`
2. **Pre-flight Checks:** Verify dependencies before running
3. **Clear Output:** Use structured output that's easy to parse
4. **Temp Files:** Store output in `${TMPDIR:-/tmp}/`
5. **Cleanup:** Remove temporary files when done
6. **Documentation:** Add comments explaining complex logic

### Security Considerations

1. **No Hardcoded Secrets:** Never include API keys, passwords, or tokens
2. **Input Validation:** Validate and sanitize all inputs
3. **Safe Execution:** Be careful with `eval`, command substitution, etc.
4. **Minimal Permissions:** Request only necessary permissions
5. **Secure Dependencies:** Use trusted, maintained tools

### Performance Tips

1. **Efficient Parsing:** Use appropriate tools (awk, jq, etc.)
2. **Limit Output Size:** Truncate or paginate large outputs
3. **Caching:** Consider caching expensive operations
4. **Async When Possible:** Don't block on long-running operations
5. **Resource Cleanup:** Always clean up resources

## Testing Your Skill

### Manual Testing

1. **Install your skill:**
   ```bash
   cd ~/.claude/skills/
   # Your skill should be in this directory
   ```

2. **Test the script directly:**
   ```bash
   bash my-new-skill/scripts/my_script.sh
   ```

3. **Test with Claude Code:**
   ```bash
   claude
   > [Your trigger phrase]
   ```

### Test Checklist

- [ ] Script runs without errors
- [ ] All dependencies are checked
- [ ] Error messages are clear and helpful
- [ ] Output is formatted correctly
- [ ] Temporary files are cleaned up
- [ ] Works on different platforms (if applicable)
- [ ] Edge cases are handled (empty input, large input, etc.)
- [ ] Documentation is accurate

### Testing Different Scenarios

1. **Happy Path:** Normal, expected usage
2. **Missing Dependencies:** Simulate missing tools
3. **Invalid Input:** Test with malformed or empty input
4. **Large Input:** Test with large files or long content
5. **Error Conditions:** Verify error handling works

## Submitting Changes

### Before Submitting

1. **Test thoroughly** using the checklist above
2. **Update documentation** (README, SETUP.md if needed)
3. **Follow code style** consistent with existing skills
4. **Add examples** showing how to use your skill
5. **Check for secrets** - no API keys or sensitive data

### Commit Message Format

Follow conventional commits:

```
type(scope): brief description

Longer description if needed.

- Detail 1
- Detail 2
```

**Types:**
- `feat`: New feature (new skill)
- `fix`: Bug fix
- `docs`: Documentation changes
- `refactor`: Code refactoring
- `test`: Adding or updating tests
- `chore`: Maintenance tasks

**Examples:**

```
feat(review): Add code review skill with Gemini

Add a new skill that performs code reviews on staged changes using
the Gemini CLI. Includes error handling, clear output formatting,
and comprehensive documentation.

- Created SKILL.md with trigger phrases and instructions
- Added review_with_gemini.sh script
- Updated main README with new skill
```

```
fix(review): Handle first commit edge case

Fix error when reviewing in a repository with only one commit.
Now uses git's empty tree hash as the base for the first commit.
```

### Pull Request Guidelines

1. **Descriptive Title:** Clearly state what the PR does
2. **Detailed Description:** Explain the changes and motivation
3. **Testing Notes:** Describe how you tested the changes
4. **Screenshots/Examples:** Show the skill in action (if applicable)
5. **Link Issues:** Reference any related issues

**PR Template:**

```markdown
## Description

Brief description of changes.

## Type of Change

- [ ] New skill
- [ ] Bug fix
- [ ] Documentation update
- [ ] Enhancement to existing skill

## Testing

- [ ] Tested script directly
- [ ] Tested with Claude Code
- [ ] Tested edge cases
- [ ] Updated documentation

## Dependencies

List any new dependencies or requirements.

## Additional Notes

Any other relevant information.
```

## Code Review Process

### What Reviewers Look For

1. **Functionality:** Does it work as described?
2. **Code Quality:** Is the code clean and maintainable?
3. **Documentation:** Is it well-documented?
4. **Security:** Are there any security concerns?
5. **Performance:** Is it efficient?
6. **Compatibility:** Works on different systems?

### Addressing Feedback

1. **Be Open:** Accept feedback graciously
2. **Ask Questions:** If something is unclear, ask
3. **Make Changes:** Update your PR based on feedback
4. **Explain Decisions:** If you disagree, explain your reasoning
5. **Stay Engaged:** Respond to comments in a timely manner

## Questions or Need Help?

- Check [SETUP.md](./SETUP.md) for setup instructions
- See [TROUBLESHOOTING.md](./TROUBLESHOOTING.md) for common issues
- Review existing skills for examples
- Open an issue for questions or discussions

## Thank You!

Your contributions help make Claude Code Skills better for everyone!
