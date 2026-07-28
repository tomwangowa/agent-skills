# Deprecated: Code Review with Gemini

`code-review-gemini` is retained only as a migration reference. It is not a
supported review path, and its script exits without reading or sending a diff.

Use `code-review-claude` in Claude Code or `code-review-codex` in Codex. A
future RDSec endpoint reviewer will require an explicit model choice and
approval of the exact diff or data scope before anything is sent externally.
