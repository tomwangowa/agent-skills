---
name: Code Story Teller
description: Analyze git history to tell the story of how code evolved. Use this Skill when the user asks to understand code history, explain evolution, show file timeline, or understand design decisions behind code.
---

# Code Story Teller

## Purpose

This Skill analyzes the git history of a file to tell its evolutionary story by:
1. Collecting complete commit history for the file
2. Analyzing major changes and design decisions
3. Using Gemini CLI to generate a narrative story
4. Presenting the evolution in an engaging, informative format

The Skill helps developers understand:
- Why code was written the way it is
- What design decisions were made and why
- How the code evolved over time
- Who contributed what to the codebase

---

## Instructions

When the user expresses intent to understand code history (for example: "tell the story of this file", "explain how this code evolved", "show me the history"), follow the steps below strictly.

### Execution steps

1. **Identify the file** the user wants to analyze
   - If the user mentions a specific file path, use it
   - If the user says "this file" or "current file", ask for clarification
   - If the user is discussing code in context, try to infer the file

2. **Run the script** `scripts/tell_code_story.sh <file-path>`
   - The script will collect git history
   - It will analyze commits and changes
   - It will generate a comprehensive story using Gemini

3. **Present the story** to the user in a structured format:
   - Summarize the key findings
   - Highlight interesting insights
   - Explain important design decisions
   - Point out notable patterns

4. **Offer follow-up options**:
   - Analyze another related file
   - Dive deeper into specific commits
   - Generate Architecture Decision Record (ADR)
   - Compare with similar files

### Output requirements

Your response should include:

- **Origin Summary**
  Brief explanation of when and why the file was created

- **Key Milestones**
  Timeline of important changes

- **Design Insights**
  Notable architectural or design decisions

- **Current State**
  How the file looks now and how it evolved

- **Actionable Insights**
  What can we learn from this history

---

## Constraints

- File must exist in the git repository
- File must have commit history
- Analysis is limited to the most recent 20 commits (configurable)
- Large diffs are truncated to avoid context overflow
- Requires Gemini CLI and API key

---

## Examples

**User:**
> Tell me the story of src/api/auth.js

**Expected behavior:**
- Run `tell_code_story.sh src/api/auth.js`
- Wait for Gemini to analyze the history
- Present the story in a structured format
- Highlight key design decisions
- Offer to analyze related files

---

**User:**
> How did this authentication module evolve over time?

**Expected behavior:**
- Ask which specific file to analyze (if not clear from context)
- Run the story teller script
- Focus on authentication-related changes in the summary
- Explain why certain authentication methods were chosen

---

**User:**
> Show me the history of database/migrations

**Expected behavior:**
- Explain that the tool works on individual files
- Ask which specific migration file to analyze
- Or suggest analyzing multiple files sequentially

---

**User:**
> Why was this code written this way?

**Expected behavior:**
- Identify the file being discussed
- Run the story teller
- Focus on design decision sections
- Extract relevant commit messages that explain "why"

---

## Use Cases

### Understanding Legacy Code
When joining a new project or working with unfamiliar code, use this skill to:
- Understand the original intent
- See how requirements changed over time
- Learn from previous design decisions

### Code Review Context
Before reviewing changes:
- Understand the file's history
- See if the change aligns with previous patterns
- Check if there were similar attempts before

### Refactoring Decisions
Before major refactoring:
- Understand why the current design exists
- Learn from previous refactoring attempts
- Avoid repeating past mistakes

### Documentation
Generate historical documentation:
- Create Architecture Decision Records
- Document design rationale
- Onboard new team members

### Technical Debt Analysis
Identify patterns:
- Recurring bug fixes in the same area
- Gradual complexity increase
- Signs of technical debt accumulation

---

## Output Format

The generated story includes:

1. **Origin Story** - Creation context
2. **Evolution Timeline** - Chronological milestones
3. **Design Decisions** - Key architectural choices
4. **Current State** - Present structure
5. **Insights & Patterns** - Emergent patterns
6. **Notable Contributors** - Who shaped the code

All presented in an engaging narrative format in Traditional Chinese, with technical terms and dates in English.

---

## Tips for Users

1. **Start with key files**: Focus on core modules or frequently changed files
2. **Look for patterns**: Similar stories across files may reveal architectural patterns
3. **Share with team**: Use stories for documentation and knowledge sharing
4. **Combine with other tools**: Use with code review skill for comprehensive analysis
5. **Save important stories**: Keep generated stories as part of project documentation
