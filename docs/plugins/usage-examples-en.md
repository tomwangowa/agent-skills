# Using the agent-skills CLI plugins

These examples follow recurring patterns from real work records: clarifying a task, reviewing a change, resuming work, keeping a journal, preparing a presentation, and maintaining skills. Project names and private details are omitted.

Most of the time, describe the task in plain language. When an example shows an explicit command, enter it yourself. Installing a package makes its skills available; it does not run every skill automatically.

## 1. Turn a rough request into an agreed design

**Packages:** `technical-decisions`, `quality-gates`; optionally install Superpowers separately.

**Try saying:**

> I want to improve [feature]. Before editing files, ask me one question at a time. Compare the practical options, list the assumptions and open decisions, and give me a short design to approve.

After approving the design:

> Turn the approved design into a task plan. Implement it, review the changes, and tell me which checks you actually ran and what remains unverified.

**Expect:** a clear design before implementation, followed by reviewed changes and evidence. Superpowers adds its planning and implementation workflows, but it is a separate optional plugin.

## 2. Understand an unfamiliar repository and start a task

**Package:** `repo-workflow`; add `quality-gates` when you want a review before finishing.

First ask for a source-backed tour of the relevant code, then preview an isolated task setup (a separate branch and worktree). For a direct entry:

- Claude Code: `/repo-workflow:understand-repo <path>`
- Codex: `$repo-workflow:understand-repo <path>`

You can then ask it to prepare a branch/worktree for a named task. Before stopping, explicitly run `/repo-workflow:handoff` or `$repo-workflow:handoff`. In the next session, run `/repo-workflow:session-start` or `$repo-workflow:session-start` to recheck the handoff assumptions.

**Expect:** a map of the code that matters, a preview before starting isolated work, and a handoff another session can verify.

## 3. Review a change before merging or calling it complete

**Package:** `quality-gates`.

**Try saying:**

> Review my current changes for bugs, security problems, and regressions. Do not edit files. Put actionable findings first with file and line references. Then list the checks that ran and the gaps they do not cover.

**Expect:** findings tied to the actual change and a clear account of verification. A review does not replace running the project's required checks.

## 4. Make a technical decision using evidence

**Package:** `technical-decisions`.

**Try saying:**

> Compare [option A] and [option B] for [constraint]. Look for the strongest evidence against the leading option, use primary sources where possible, and separate verified facts from inference. Recommend one option and list what still needs validation.

**Expect:** a decision you can inspect, including counter-evidence, trade-offs, and remaining unknowns.

## 5. Use Codex with a company AI endpoint

**Scenario:** use Codex through a company model endpoint without a ChatGPT account login.

Keep the existing endpoint and authentication settings. The installer does not configure or test them. Plugin downloads still need access to the selected marketplace or GitHub source.

**Verified boundary:** the macOS Codex CLI 0.167.0 test installed without an account login and preserved a synthetic company-provider setting. A real company endpoint connection, other CLI versions, and other platforms remain unverified. See the [company-endpoint test record](../../docs/validation/plugin-installer/codex-no-account-native-results.md) and [installer guide](../../installer/README.md) for evidence and setup details.

## 6. Keep a journal and prepare a weekly update

**Package:** `work-journal`.

**Try saying:**

> Record today's completed work and the documents I actually consulted.

Later, ask:

> Summarize this week's completed work, decisions, and unfinished items. Link each point to its activity record where possible.

**Expect:** dated activity records and a report grounded in those records. New setups store activities under `~/.agent-skills/activities`. Adding a notes folder is optional; it lets journal searches include your own notes.

## 7. Turn technical work into a presentation or translated document

**Packages:** `content-tools`; add `work-journal` when the source should be grounded in recorded work.

**Try saying:**

> Make a 10-minute presentation plan for new teammates from this work summary. Keep the key claims and decisions, and mark anything that still needs confirmation.

Or:

> Translate this Markdown document into English and Traditional Chinese. Preserve code, links, and identifiers.

**Expect:** an audience-focused outline or a translation that keeps technical content intact. Review the result before sharing it.

## 8. Keep response preferences consistent

**Package:** `session-preferences`.

**Try saying:**

> Show me my current language, explanation-depth, and next-step preferences. Suggest a concise Traditional Chinese setting that defines unfamiliar terms. Do not save changes until I approve them.

**Expect:** a review of the current session rules and, if requested, a separate change to your saved personal preferences.

## 9. Find or improve a skill

**Package:** `skill-toolbox`.

**Try saying:**

> Find the skills that fit [task]. Mark which are installed, which are available to install, and which are unavailable.

For a skill you maintain:

> Audit this skill for unclear triggers, missing steps, unsafe instructions, and weak examples. Show each finding and a suggested fix.

**Expect:** a useful shortlist or a review with concrete findings. A skill appearing in a catalog does not mean it is installed.

## 10. Keep a long Claude Code session easy to follow

**Claude Code only:** add `attention-mod` and `handoff-mod`.

Use `/attention` to open the attention panel, `/handoff-mod:handoff` to create a handoff, and `/handoff-resume` to list work you can resume.

**Expect:** a quick view of session context and a note for the next session. Attention summaries send conversation/tool excerpts to Haiku and use model tokens. This is separate from the general `repo-workflow` handoff.

## Quick package map

| Package | Good fit |
| --- | --- |
| `technical-decisions` | Requirements, research, and technical choices |
| `quality-gates` | Code review and evidence before completion claims |
| `repo-workflow` | Understand a repository, start isolated work, and resume later |
| `work-journal` | Record work and find decisions or unfinished items |
| `content-tools` | Presentations, translation, and writing |
| `session-preferences` | Language, explanation depth, and how work is handed back |
| `skill-toolbox` | Skill discovery and skill audits |
| `attention-mod`, `handoff-mod` | Claude Code session visibility and handoff |
| Superpowers | Optional planning and implementation workflows; installed separately |

See the [package inventory](../../SKILLS_CATALOG.md) and [installer instructions](../../installer/README.md) for package details.
