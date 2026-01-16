---
name: Activity Logger
description: Records work activities from the current session for cross-session aggregation and work log generation
id: tm-activity-logger
namespace: tm
domain: activity
action: logger
version: "1.0.0"
updated: "2026-01-17"
---

# Activity Logger Skill

## Purpose

Records activities from the current Claude Code session to enable cross-session activity aggregation and work log generation. This skill is designed to work with multiple concurrent Claude Code instances across different projects.

## When to Use

**Automatic triggers:**
- After completing a significant task or feature
- Before switching to a different project
- At the end of a work session

**Manual triggers:**
- "log this activity"
- "record what I just did"
- "save session activity"
- "log my work"

## How It Works

When triggered, this skill will:

1. **Collect session information:**
   - Generate or retrieve session ID
   - Record current timestamp
   - Identify current project (from git repo or directory name)
   - Get current working directory

2. **Gather activity details:**
   - Prompt user for activity description (if not provided)
   - List recently modified files (from git status)
   - Capture recent commits (if any)
   - Record task context

3. **Save activity record:**
   - Create JSON file in `~/.claude/activities/`
   - Filename format: `{session_id}_{timestamp}.json`
   - Ensure directory structure exists

4. **Confirm to user:**
   - Display saved activity summary
   - Show file path where activity was saved

## Activity Record Format

Each activity record is saved as a JSON file with the following structure:

```json
{
  "session_id": "unique-session-identifier",
  "timestamp": "2026-01-13T14:05:30Z",
  "project_path": "/Users/username/projects/my-app",
  "project_name": "my-app",
  "git_branch": "main",
  "activities": [
    {
      "type": "task_completed",
      "description": "Implemented user authentication feature",
      "files_changed": ["src/auth.ts", "src/middleware.ts"],
      "commits": ["a1b2c3d4"]
    }
  ],
  "context": "Working on security improvements",
  "tags": ["authentication", "security"]
}
```

## Activity Types

- `task_completed` - Finished a specific task or feature
- `bug_fixed` - Resolved a bug or issue
- `refactoring` - Code refactoring work
- `research` - Investigation or exploration work
- `documentation` - Documentation updates
- `review` - Code review activities

## Usage Examples

### Example 1: Simple activity logging
```
User: "log my work"
Claude: What activity would you like to log?
User: "Implemented OAuth2 login flow"
Claude: [Collects info and saves activity]
```

### Example 2: Automatic logging after task completion
```
User: "I've finished implementing the dashboard"
Claude: [Completes implementation work]
        Great! Would you like me to log this activity? [logs automatically]
```

## Configuration

Activity logger uses the following directory structure:

```
~/.claude/
├── activities/           # Activity records
│   ├── session_*.json   # Unprocessed activities
│   └── processed/       # Processed activities (archived)
└── config/
    └── activity-config.json  # Configuration (optional)
```

## Integration with Work Log Analyzer

Activity records saved by this skill can be aggregated using the `work-log-analyzer` skill with the `--aggregate` flag:

```
User: "aggregate my activities"
Claude: [Uses work-log-analyzer to process all activity records]
```

## Environment Variables

- `CLAUDE_ACTIVITIES_DIR` - Override default activities directory (default: `~/.claude/activities`)
- `CLAUDE_SESSION_ID` - Provide custom session ID (auto-generated if not set)

## Dependencies

### Required
- `jq` - JSON processor (install: `brew install jq` on macOS, `apt-get install jq` on Ubuntu)
- `git` - Version control system (required for project context)

### Optional
- `openssl` - For secure random ID generation (falls back to `/dev/urandom` or `$RANDOM` if not available)

## Implementation Notes

The skill implementation:
1. Creates directory structure if it doesn't exist
2. Generates a session ID based on timestamp + random string
3. Uses git commands when available to gather context
4. Falls back to directory scanning if not in a git repo
5. Validates JSON output before saving
