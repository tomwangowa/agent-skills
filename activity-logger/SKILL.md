---
name: activity-logger
description: Use when recording work activities, preserving explicitly consulted document paths, or preparing activity data for cross-session aggregation.
---

# Activity Logger Skill

## Purpose

Records activities from the current coding-agent session to enable cross-session activity aggregation and work log generation. Claude Code CLI and Codex CLI share the same selected local journal configuration.

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
   - Resolve the shared settings and activity directory before any data access
   - Generate or retrieve session ID
   - Record current timestamp
   - Identify current project (from git repo or directory name)
   - Get current working directory

2. **Gather activity details:**
   - Prompt user for activity description (if not provided)
   - List recently modified files (from git status)
   - Capture recent commits (if any)
   - Record explicitly referenced document paths when supplied with repeated `--reference`
   - Record task context

3. **Save activity record:**
   - Create JSON file in the resolved activity directory
   - Filename format: `{session_id}_{timestamp}.json`
   - Ensure directory structure exists

4. **Confirm to user:**
   - Display saved activity summary
   - Show file path where activity was saved

### Lesson proposals (optional)

If the `lesson` skill is installed and configured (`lesson/config.json` exists) and this session hit a lesson-worthy event (a pitfall fixed, an assumption disproved, or the user correcting the agent), draft at most two lessons following the `lesson` skill's capture flow and include them in the same closing message as the activity summary, so the user answers once. Write a lesson only after the user confirms it. If the `lesson` skill is missing or not configured, skip this step without comment.

## Activity Record Format

Each activity record is saved as a JSON file with the following structure:

```json
{
  "session_id": "unique-session-identifier",
  "timestamp": "2026-01-13T14:05:30Z",
  "project_path": "$PROJECT_ROOT",
  "project_name": "my-app",
  "git_branch": "main",
  "activities": [
    {
      "type": "task_completed",
      "description": "Implemented user authentication feature",
      "files_changed": ["src/auth.ts", "src/middleware.ts"],
      "commits": ["a1b2c3d4"],
      "references": [
        {
          "path": "docs/auth.md",
          "relative_path": "docs/auth.md",
          "repo_root": "$DESIGN_REPO",
          "branch": "main",
          "commit": "a1b2c3d4",
          "remote": "https://github.com/example/design.git",
          "tracked_at_log_time": true,
          "working_tree_status": "clean",
          "path_status": "tracked"
        }
      ]
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

### Example 3: Preserve documents consulted in another repository

Pass every explicitly consulted path separately. The logger stores locators and
Git state only; it never copies document contents:

```bash
log_activity.sh -d "Reviewed onboarding contract" -t research \
  --reference ../REI-Project/docs/design/onboarding.md \
  --reference "$HIE_REI_WORKTREE/design-handoff/getStartedChat.md"
```

`--reference` may be repeated. Relative paths are resolved against the current
working directory. Existing Git paths record their repo-relative path, branch,
HEAD commit, sanitized origin remote, tracked state, and working-tree status.
Missing paths remain locators with `missing` status; no document content is
read into the activity record.

## Configuration

Resolve the personal settings root from `AGENT_SKILLS_CONFIG_DIR`, otherwise
`XDG_CONFIG_HOME/agent-skills`, otherwise the current user's
`~/.config/agent-skills`. The external `work-journal.json` supplies
`sources.activities` and a non-empty `sources.notes.paths`. Relative data
paths resolve from that settings root; `~/` resolves from the current home.

The logger, initializer, local aggregator and normal MCP startup use the same
root resolver. `CLAUDE_ACTIVITIES_DIR` overrides the selected activity path in
all of them; a relative override also resolves from the settings root, never
the current working directory. Existing data can be selected directly without
moving it.

From the source repo root, resolve the path without writing a record:

```sh
PYTHONPATH=runtime python3 -m agent_skills_runtime.journal_cli activities-dir
```

In an installed plugin, use that plugin's bundled `runtime/` on `PYTHONPATH`.
Do not borrow another installation or infer a data root from an MCP tool name.
Missing or invalid shared settings require explicit first-time setup before
logging; an environment activity override does not hide invalid note settings.
Preview the selected activity/note directories before setting them up:

```sh
PYTHONPATH=runtime python3 -m agent_skills_runtime.setup --activities "<selected-activity-directory>" --notes "<selected-notes-directory>"
```

Replace the placeholders with the user's selected directories. Setup preserves
an existing configuration. The initializer creates only the selected activity
and processed directories; it does not create legacy private configuration.

```
<settings-root>/work-journal.json
<selected-activity-directory>/
├── session_*.json
└── processed/
```

## Integration with work-log-analyzer

Activity records saved by this skill can be aggregated using the `work-log-analyzer` skill with the `--aggregate` flag:

```
User: "aggregate my activities"
Claude: [Uses work-log-analyzer to process all activity records]
```

The `work-log-analyzer` `referenced-documents` query uses the structured
`references` array to find recent documents that are not yet in
`session-start/repos.yaml`, including documents from adjacent repositories.

## Environment Variables

- `AGENT_SKILLS_CONFIG_DIR` - Explicit shared settings root
- `XDG_CONFIG_HOME` - Fallback settings parent when no explicit root is selected
- `CLAUDE_ACTIVITIES_DIR` - Override the shared selected activity directory
- `CLAUDE_SESSION_ID` - Provide custom session ID (auto-generated if not set)

## Error Handling

- Missing bundled runtime, missing `work-journal.json`, invalid JSON or empty
  note paths fail before logging with a concrete setup message. Never fall back
  to an unrelated private `config.json` or the old default data directory.
- A non-writable selected directory reports the filesystem error and fails;
  do not claim the activity was recorded. Restart the MCP process after changing
  settings or environment overrides so its startup snapshot matches the logger.
- A missing `--reference` value exits with an error before an activity record
  is written.
- A missing, non-Git, or deleted reference does not abort logging. The logger
  keeps the normalized locator and uses null Git fields or an explicit status.
- If a Git metadata command fails, the activity still writes valid JSON and
  reports the unavailable field as null or `unknown`.
- Invalid JSON generated by an unexpected shell value is caught by the final
  `jq` validation; the partial activity file is removed.

## Security Considerations

- Only paths explicitly supplied through `--reference` are recorded; the
  logger does not scrape the transcript or scan repositories.
- Reference files are never copied, parsed, or executed. The record contains
  locator metadata only.
- A missing or non-Git reference does not abort activity logging. Its path is
  retained with null Git fields and an explanatory status.
- Treat descriptions, tags, paths, and remotes as data: quote shell arguments,
  do not use `eval`, and do not execute values from an activity record.
- Normalize paths only for locator metadata; the logger does not write to a
  referenced path or follow a reference into a command. Remote credentials
  are removed before an origin URL is stored.
- The output is JSON rather than HTML, so there is no HTML/XSS rendering
  surface in this skill.

## Dependencies

### Required
- Python 3 and this installation's bundled runtime for shared path resolution
- `jq` - JSON processor (install: `brew install jq` on macOS, `apt-get install jq` on Ubuntu)
- `git` - Version control system (required for project context)

### Optional
- `openssl` - For secure random ID generation (falls back to `/dev/urandom` or `$RANDOM` if not available)
- `lesson` skill - when installed and configured, wrap-up also offers lesson proposals (see "Lesson proposals")

## Implementation Notes

The skill implementation:
1. Creates directory structure if it doesn't exist
2. Generates a session ID based on timestamp + random string
3. Uses git commands when available to gather context
4. Falls back to directory scanning if not in a git repo
5. Validates JSON output before saving
