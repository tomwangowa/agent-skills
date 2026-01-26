# var-namer Skill

A simple skill that generates meaningful variable names following Clean Code principles with type prefixes.

## What This Skill Does

This skill helps you create well-named variables for different programming languages. It follows these rules:
- Uses lowerCamelCase naming
- Adds type prefixes (str, n, is, arr, etc.)
- Generates code snippets with comments
- Follows language-specific syntax

## How to Use

Simply ask Claude to generate a variable name:

```
Generate a variable name for storing user login failure count in Java
```

Claude will respond with:
```java
// Record the cumulative number of failed login attempts for account lockout mechanism
int nLoginFailureCount = 0;
```

## Understanding the Skill Structure

This skill has one main file: `SKILL.md`

### Anatomy of SKILL.md

```markdown
---
name: var-namer                    # Skill identifier
description: Brief description     # What the skill does
tools:                            # Tools this skill can use
  - Write
  - Edit
---

# Overview                         # Main instructions for Claude

## When to Use                     # Trigger conditions

## Process                         # Step-by-step workflow

## Output Format                   # How to format responses

## Guidelines and Constraints      # Rules to follow

## Examples                        # Sample inputs/outputs
```

## How It Works

1. **User invokes**: User asks for variable naming help
2. **Claude loads**: Claude reads SKILL.md instructions
3. **Claude follows**: Claude follows the Process section
4. **Claude outputs**: Claude formats response per Output Format section

## Extending This Skill (Workshop Exercise)

Here are some ways you can extend this skill:

### Option 1: Add More Language Support
Add examples for more languages in the Examples section (Go, Rust, Swift, etc.)

### Option 2: Add Naming Conventions
Extend Guidelines to support different conventions:
- SCREAMING_SNAKE_CASE for constants
- PascalCase for classes
- snake_case for Python

### Option 3: Add Function Naming
Expand the skill to also generate function/method names following Clean Code principles.

### Option 4: Add Validation Rules
Add a section that validates variable names against common anti-patterns:
- Too short (single letters)
- Too generic (data, info, temp)
- Contains abbreviations

## File Structure

```
var-namer/
├── SKILL.md      # Main skill definition (required)
└── README.md     # This documentation (optional)
```

## Tips for Workshop Learners

1. **Start Simple**: Read through SKILL.md to understand the basic structure
2. **Test It**: Try invoking the skill with different requests
3. **Modify**: Make small changes to the instructions and see how Claude's behavior changes
4. **Add Examples**: More examples = better Claude understanding
5. **Be Specific**: Clear instructions in Process and Guidelines lead to consistent outputs

## Key Takeaways

- Skills are just markdown files with YAML frontmatter
- The Overview section contains Claude's instructions
- Structure helps Claude understand what to do and how to do it
- Examples are crucial for demonstrating expected behavior
