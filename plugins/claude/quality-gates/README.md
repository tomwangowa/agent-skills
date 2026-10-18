# quality-gates

Version 0.1.0; claude CLI.

Included skills:

- `quality-gates:code-review-claude`
- `quality-gates:completion-gate`
- `quality-gates:codebase-audit`
- `quality-gates:pr-review-assistant`
- `quality-gates:secure-ai-development-gate`

Read [installation and setup](installation.md), [migration and recovery](migration.md),
[Superpowers compatibility](superpowers-compatibility.md) and [team instructions](team-instructions.md).

Native acceptance on 2026-10-15 covered all seven packages with Claude Code CLI 2.1.300 and Codex CLI 0.162.1 on isolated macOS fixtures. session-preferences and work-journal changed after that run and need native acceptance again before release. Claude Code CLI 2.1.302 verified GitHub marketplace installation and update checks on 2026-10-17; Codex CLI remote marketplace installation and release approval remain pending.
