> **Read this when**: the user supplies unstructured log content, or you need to verify a TODO / date / decision format variant before parsing. For the full human-facing formatting guide, see `README.md`.

# Work Log Analyzer — Log Formats

## Recommended Format (Structured Markdown)

```markdown
# 2026-01-13

## SellerCheck Implementation

- Decided to use PostgreSQL for seller verification data
- Considered Redis but concerned about persistence
- Next: prototype the schema

## TODOs

- [ ] TODO: Implement SellerCheck API (due: 2026-01-20) #high-priority
- [x] TODO: Fix L10n issues in Lite Engagement (completed: 2026-01-10)
- [ ] TODO: Code review for PR #123

## Decisions

**Decision**: Use PostgreSQL for SellerCheck
**Rationale**: Need ACID guarantees and joins across multiple tables
**Alternatives considered**: Redis, MongoDB
**Date**: 2026-01-13
```

---

## Also Supports

- **Plain text logs**: less structured but still analyzable
- **Bullet point journals**: one-line-per-entry daily logs
- **Unstructured notes**: will extract information best-effort
- **Mixed formats**: adapts to varying styles

---

## TODO Format Recognition

The skill recognizes these TODO patterns:

```markdown
- [ ] TODO: Task description
- [x] TODO: Completed task
- TODO: Task without checkbox
- [ ] Task (due: YYYY-MM-DD)
- [ ] Task #priority-tag
- FIXME: Code fix needed
- HACK: Technical debt item
```

### Format Tolerance

The skill is lenient with common formatting variations:

- Checkboxes with missing spaces: `- []` or `- [X]` (though `- [ ]` and `- [x]` are preferred)
- Various completion markers: `[x]`, `[X]`, `[✓]`, `[✔]`
- In-progress markers: `[~]`, `[→]`, `[...]`
- Different TODO keywords: `TODO`, `FIXME`, `HACK`, `BUG`, `NOTE`

For best results, maintain consistent formatting throughout logs.

---

## Date Parsing

Best results with ISO format (`YYYY-MM-DD`). Other formats (e.g., `Jan 13, 2026`, `13/01/2026`) may work but are ambiguous and less reliable. When a date is ambiguous, always resolve it to an absolute date and state the resolution in the output so the user can verify.

---

## Decision Format Template

Decision Tracking queries return the richest output when the log follows a structured decision template (Context / Decision / Rationale / Alternatives / Consequences / Date / Status). For the full template that the user writes in their logs, see `../README.md` — search for "Decision Format Template".
