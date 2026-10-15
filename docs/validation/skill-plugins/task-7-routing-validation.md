# Task 7 — owned routing and conditional dependencies

Source and native routing checks passed on 2026-10-15. The evidence covers
Claude Code CLI 2.1.300 and Codex CLI 0.162.1 on macOS with isolated fixture
settings and the seven packages installed from a unique local marketplace.

Both CLIs selected the package-owned `technical-decisions:brainstorming` for a
new design request and the platform reviewer from `quality-gates` for review.
Claude's native Skill call and Codex's installed-cache read both loaded the
right reviewer. A completion-boundary request loaded the package's own
`completion-gate` in both CLIs and rejected a completion claim when the only
test result preceded the last change. Codex's second natural-language case
read `quality-gates/0.1.0/skills/completion-gate/SKILL.md` from the selected
native cache; it ran no tests or writes. The explicitly invoked
`$skill-toolbox:skill-sync` path explained its standalone source/cache boundary
without running a sync.

The paired ordinary question did not invoke a tool or skill in either CLI; its
answer kept the user-only checkpoint. Earlier exploratory versions were
excluded: they read the source checkout and a read-only Git diff, so they do not
count as installed-package evidence. No sync command ran in any case.

The conditional `writing-plans` branch used the already registered Superpowers
7.0.0 provider in both CLIs. It loaded the required planning skill, reported the
prerequisite and stopped at the planning boundary. This does not certify the
full upstream design-to-implementation flow, so package `tested_versions`
remain empty. Codex `/compact` re-injected the same five fixture markers twice;
the instructions are idempotent.

VERIFIED:

- Five policy tests and the full Python suite passed (154 tests). Deterministic
  rebuild, package and marketplace validation passed.
- Startup, resume, clear, compact, preferences-off, owned review/routing,
  completion-gate, manual invocation and selected Superpowers scenarios passed
  in both native CLIs. The current artifact bindings match all fourteen native
  0.1.0 cache packages.
- The native settings were isolated to fixture data. Existing Codex plugins,
  MCP servers and hooks were disabled only for the test invocation; selected
  hook commands were reviewed and trusted through normal CLI controls.

The evidence is summarized in `acceptance.json` and the two surface records.
Git-hosted marketplace installation, non-macOS behavior and other CLI versions
remain unverified.
