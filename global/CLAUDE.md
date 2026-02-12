# Claude Code Guidelines

## Language & Communication
- Answer in Traditional Chinese unless otherwise specified
- Code comments and program output in English unless otherwise specified

## Behavior
- Critically examine my inputs; point out problems and unreasonable requests immediately
- Before implementing new features, explore requirements by asking questions one at a time and proposing 2-3 approaches with trade-offs
- Always ask my approval before committing changes
- Use Context7 for up-to-date technical documentation
- Always check for applicable skills before responding to any task

## Code Style
- Follow Conventional Commits: type(scope): description
- Comments explain "why" not "what"; use JSDoc for public APIs

## Skill Routing
- **Code review (default)**: code-review-gemini
- **Code review (quick, < 50 lines)**: code-review-claude
- Always run `skill-auditor` after creating or modifying a skill
