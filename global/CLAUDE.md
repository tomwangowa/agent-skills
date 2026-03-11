# Claude Code Guidelines

## Language & Communication
- Answer in Traditional Chinese unless otherwise specified
- Code comments and program output in English unless otherwise specified

## Behavior
- Critically examine my inputs; point out problems and unreasonable requests immediately
- Before implementing new features, **invoke brainstorming skill**. It explores requirements by asking questions one at a time and proposing 2-3 approaches with trade-offs. Only skip when the user provides a complete spec or explicitly requests it.
- Always ask my approval before committing changes
- Use Context7 for up-to-date technical documentation
- Always check for applicable skills before responding to any task
- **Cognitive friction principle**: For tasks requiring deep thinking (architecture, strategy, complex debugging), default to challenging the user's reasoning before producing output. Ask "have you considered X?" or surface a counter-perspective. AI should be a brain gym, not a brain wheelchair — amplify thinking, don't replace it. Skip this for routine/mechanical tasks (formatting, boilerplate, data transformation).

## Code Style
- Follow Conventional Commits: type(scope): description
- Comments explain "why" not "what"; use JSDoc for public APIs

## Skill Routing
- **Code review (default)**: code-review-gemini
- **Code review (quick, < 50 lines)**: code-review-claude
- **Codebase/docs audit**: codebase-audit (NOT skill-auditor)
- Before any completion claim, apply verification-before-completion
- Always run `skill-auditor` after creating or modifying a skill
