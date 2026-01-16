# Skill Naming Conventions

This document defines the naming standards for Claude Code skills in this repository.

## Table of Contents

- [Overview](#overview)
- [Naming Format](#naming-format)
- [Domain Categories](#domain-categories)
- [YAML Frontmatter Standards](#yaml-frontmatter-standards)
- [File Structure Requirements](#file-structure-requirements)
- [Migration from Legacy Names](#migration-from-legacy-names)
- [Examples](#examples)
- [Version History](#version-history)

---

## Overview

### Purpose

- **Namespace isolation**: Prevent naming conflicts when sharing skills across teams or publishing publicly
- **Consistency**: Maintain uniform naming patterns across all skills
- **Discoverability**: Make it easy to identify skill ownership and purpose
- **Scalability**: Support future growth and organization of skills

### Namespace

All skills use the `tm-` namespace prefix:
- **tm**: Short, memorable, easy to type
- Stands for the skill repository owner/maintainer
- Distinguishes these skills from other skill repositories

---

## Naming Format

### Directory Names

**Format:** `tm-<domain>-<action>[-<qualifier>]`

**Rules:**
- Use **kebab-case** (all lowercase with hyphens)
- Start with `tm-` namespace prefix
- Include descriptive domain and action
- Add optional qualifier for specificity (e.g., tool name)
- Keep names concise but self-explanatory (max 4-5 words)

**Examples:**
```
✅ tm-code-review-gemini
✅ tm-spec-generator
✅ tm-ui-design-analyzer
✅ tm-commit-msg-generator

❌ code-review-gemini           (missing namespace)
❌ tm_code_review_gemini        (wrong separator)
❌ tm-CodeReviewGemini          (wrong case)
❌ tm-gemini-code-reviewer      (tool name should be qualifier, not primary)
```

### Components Breakdown

| Component | Description | Examples | Required |
|-----------|-------------|----------|----------|
| **namespace** | Owner/team identifier | `tm` | ✅ Yes |
| **domain** | Functional area | `code`, `spec`, `ui`, `pr` | ✅ Yes |
| **action** | What the skill does | `review`, `generator`, `analyzer` | ✅ Yes |
| **qualifier** | Additional specificity | `gemini`, `ai`, `auto` | ⚪ Optional |

---

## Domain Categories

Skills are organized into functional domains:

| Domain | Purpose | Examples |
|--------|---------|----------|
| **code** | Code analysis, review, quality | `tm-code-review-gemini`, `tm-code-story-teller` |
| **spec** | Specification documents | `tm-spec-generator`, `tm-spec-review-assistant` |
| **commit** | Git commit operations | `tm-commit-msg-generator` |
| **pr** | Pull request operations | `tm-pr-review-assistant` |
| **ui** | UI/UX design analysis | `tm-ui-design-analyzer` |
| **work** | Work logging and tracking | `tm-work-log-analyzer` |
| **activity** | Activity tracking | `tm-activity-logger` |
| **skill** | Meta-skills (skill management) | `tm-skill-auditor` |
| **presentation** | Content generation | `tm-interactive-presentation-generator` |

### Adding New Domains

When creating a skill that doesn't fit existing domains:
1. Consider if it can be categorized under an existing domain
2. If truly unique, propose a new domain name (1-2 words, lowercase)
3. Update this document with the new domain
4. Document the purpose and provide examples

---

## YAML Frontmatter Standards

Every `SKILL.md` file must include standardized frontmatter:

```yaml
---
name: "Skill Display Name"
id: tm-skill-id
description: "Brief description of when to use this skill (1-2 sentences)."
version: "1.0.0"
namespace: tm
domain: code
action: review
qualifier: gemini
tags:
  - code-quality
  - automation
  - review
dependencies:
  - gemini-cli
  - git
author: "Your Name"
created: "2025-01-17"
updated: "2025-01-17"
---
```

### Field Descriptions

| Field | Type | Required | Description | Example |
|-------|------|----------|-------------|---------|
| **name** | string | ✅ | Human-readable title (Title Case) | `"Code Review with Gemini"` |
| **id** | string | ✅ | Unique identifier (matches directory name) | `tm-code-review-gemini` |
| **description** | string | ✅ | When and why to use this skill (1-2 sentences) | `"Perform automated code review..."` |
| **version** | string | ✅ | Semantic version | `"1.0.0"` |
| **namespace** | string | ✅ | Namespace prefix | `tm` |
| **domain** | string | ✅ | Primary functional domain | `code` |
| **action** | string | ✅ | Primary action | `review` |
| **qualifier** | string | ⚪ | Optional specifier | `gemini` |
| **tags** | array | ⚪ | Searchable keywords | `["code-quality", "automation"]` |
| **dependencies** | array | ⚪ | External tool requirements | `["gemini-cli", "git"]` |
| **author** | string | ⚪ | Creator name or team | `"Tom Wang"` |
| **created** | string | ⚪ | Creation date (YYYY-MM-DD) | `"2025-01-17"` |
| **updated** | string | ⚪ | Last update date (YYYY-MM-DD) | `"2025-01-17"` |

---

## File Structure Requirements

### Standard Skill Structure

```
tm-skill-name/
├── SKILL.md                    # Required: Skill definition
├── README.md                   # Optional: Detailed documentation
├── scripts/                    # Optional: Supporting scripts
│   ├── main_script.sh         # Primary execution script
│   └── helper_script.sh       # Helper utilities
├── templates/                  # Optional: Templates or examples
├── tests/                      # Optional: Test files
├── .skillrc                    # Optional: Skill configuration
└── CHANGELOG.md               # Optional: Version history
```

### SKILL.md Structure

```markdown
---
[YAML frontmatter as defined above]
---

# [Skill Display Name]

## Overview

Brief introduction (2-3 sentences) explaining what this skill does.

## When to Use

Explain scenarios where this skill should be triggered.

## Trigger Phrases

List natural language phrases that should activate this skill:
- "phrase one"
- "phrase two"
- "phrase three"

## How It Works

Step-by-step workflow:
1. Step one
2. Step two
3. Step three

## Requirements

### Dependencies
- List external dependencies
- Include installation instructions

### Environment Variables
- `ENV_VAR_NAME`: Description

## Examples

### Example 1: [Scenario Name]
```
User input and expected behavior
```

### Example 2: [Another Scenario]
```
User input and expected behavior
```

## Configuration

Optional configuration options.

## Troubleshooting

Common issues and solutions.

## Related Skills

Links to related skills in the repository.
```

---

## Migration from Legacy Names

### Legacy to New Naming

| Legacy Name | New Name | Status |
|-------------|----------|--------|
| `ui-design-analyzer` | `tm-ui-design-analyzer` | 🔄 Migration needed |
| `activity-logger` | `tm-activity-logger` | 🔄 Migration needed |
| `code-review-gemini` | `tm-code-review-gemini` | 🔄 Migration needed |
| `code-story-teller` | `tm-code-story-teller` | 🔄 Migration needed |
| `commit-msg-generator` | `tm-commit-msg-generator` | 🔄 Migration needed |
| `interactive-presentation-generator` | `tm-interactive-presentation-generator` | 🔄 Migration needed |
| `skill-auditor` | `tm-skill-auditor` | 🔄 Migration needed |
| `pr-review-assistant` | `tm-pr-review-assistant` | 🔄 Migration needed |
| `spec-generator` | `tm-spec-generator` | 🔄 Migration needed |
| `spec-review-assistant` | `tm-spec-review-assistant` | 🔄 Migration needed |
| `work-log-analyzer` | `tm-work-log-analyzer` | 🔄 Migration needed |

### Backward Compatibility

During the migration period:
1. **Symlinks**: Legacy names symlinked to new names
2. **Deprecation notices**: Added to legacy SKILL.md files
3. **Documentation**: All docs updated to reference new names
4. **Grace period**: 30 days before removing legacy names

See [MIGRATION.md](./MIGRATION.md) for detailed migration steps.

---

## Examples

### Example 1: Code Review Skill

**Directory:** `tm-code-review-gemini/`

**SKILL.md frontmatter:**
```yaml
---
name: "Code Review with Gemini"
id: tm-code-review-gemini
description: "Perform automated code review on staged changes using Gemini AI to detect security issues, bugs, and quality problems."
version: "1.2.0"
namespace: tm
domain: code
action: review
qualifier: gemini
tags:
  - code-quality
  - security
  - automation
  - gemini-ai
dependencies:
  - gemini-cli
  - git
author: "Tom Wang"
created: "2024-12-01"
updated: "2025-01-17"
---
```

### Example 2: Spec Generator Skill

**Directory:** `tm-spec-generator/`

**SKILL.md frontmatter:**
```yaml
---
name: "Spec Generator"
id: tm-spec-generator
description: "Generate complete specification documents (150+ lines, 8 sections) from simple ideas or requirements."
version: "1.0.0"
namespace: tm
domain: spec
action: generator
tags:
  - documentation
  - specification
  - requirements
dependencies: []
author: "Tom Wang"
created: "2024-12-15"
updated: "2025-01-17"
---
```

### Example 3: UI Design Analyzer Skill

**Directory:** `tm-ui-design-analyzer/`

**SKILL.md frontmatter:**
```yaml
---
name: "UI Design Analyzer"
id: tm-ui-design-analyzer
description: "Analyze UI/UX design from screenshots with 6-dimensional analysis covering usability, accessibility, and visual design."
version: "1.1.0"
namespace: tm
domain: ui
action: design-analyzer
tags:
  - ui-ux
  - design
  - accessibility
  - multimodal
dependencies: []
author: "Tom Wang"
created: "2024-11-20"
updated: "2025-01-17"
---
```

---

## Version History

| Version | Date | Changes |
|---------|------|---------|
| 1.0.0 | 2025-01-17 | Initial naming conventions document |
|  |  | Established `tm-` namespace standard |
|  |  | Defined domain categories and YAML frontmatter |
|  |  | Created migration plan for legacy skills |

---

## Questions or Suggestions?

If you have questions about naming conventions or suggestions for improvements:
1. Open an issue in the repository
2. Propose changes via pull request
3. Discuss in team meetings

**Maintainer:** Tom Wang
**Last Updated:** 2025-01-17
