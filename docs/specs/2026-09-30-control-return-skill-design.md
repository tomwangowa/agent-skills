# Control Return Skill Design

## Purpose

Split the `control-return` module out of `session-preferences` into its own
manually triggered skill. Once invoked, it applies to the rest of the current
session. The rule text is rewritten by the user; this is not a verbatim move.

## Decisions

| Decision | Choice | Reason |
| --- | --- | --- |
| Duration after invocation | Persistent for the whole session | The current rule already works this way; a one-shot effect can be had by asking "what next" |
| Old copy in `session-preferences` | Removed | One source of truth; two copies drift |
| Rule text | User-authored version (below), with the exception and no-padding lines kept | Without the exception, a question that already offers A/B gets a second set of options stacked on it |
| Off switch | None | It is a conversational instruction; the user can tell the assistant to stop |

## Rule text

```text
當你歸還控制權時，要順帶給我三個可行的下一步，並推薦其中一個且說明理由。
三個 Next Steps 的描述要清楚，不要簡略，以免我又要問你釐清問題。
不要為了湊數硬編選項。
例外：向我提問確認需求，或工作還在進行中的回報，不附。
```

Known tension: "three" is a fixed count while "do not pad" discourages filler.
The original rule had the same tension. Left as-is by user choice; revisit
separately if padding shows up in practice.

## Activation

- Manual only: `disable-model-invocation: true` in `SKILL.md`, and
  `allow_implicit_invocation: false` in `agents/openai.yaml`, matching
  `session-preferences`.
- On invocation, reply once:
  `已啟用 control-return；本 session 後續回應會附三個下一步。`
- Applies from that reply onward, not retroactively, not to a new session.
  A session-level instruction, not a runtime-enforced guarantee.

## Files

New:

```text
control-return/
├── SKILL.md              # frontmatter + activation + rule text (no references/)
└── agents/
    └── openai.yaml
```

Changed in `session-preferences/`:

| File | Change |
| --- | --- |
| `references/control-return.md` | Delete |
| `references/INDEX.md` | Remove the `control-return` row |
| `SKILL.md` | Replace Example 3 (uses `control-return` as the target module) with one that targets an existing module, e.g. `deai-voice` |
| `README.md` | Remove the `control-return.md` bullet from the module list; replace the `add-rule 不要在簡單回答後硬給下一步` example; add a one-line pointer to `control-return` |

## Out of scope

- Historical files under `docs/specs/` and `docs/plans/` that mention
  `control-return` are records; not edited.
- Repo `CLAUDE.md` skill list: `session-preferences` is not listed there
  either, so `control-return` is not added.
- No `skill-sync` run. Sync stays a separate explicit action.
- No rewording of the rule beyond the text above.

## Verification

1. `grep -rn "control-return" session-preferences/` returns no hits except any
   deliberate pointer line in `README.md`.
2. `session-preferences/references/INDEX.md` lists only modules whose files
   exist.
3. `skill-auditor` passes on both `control-return` and `session-preferences`.
4. Fresh-session smoke (manual): `/control-return` prints the activation line,
   and the next reply ends with three next steps, one marked recommended; a
   clarification question does not carry the block.

Commit only after separate user approval, suggested message:
`feat(control-return): split into a manual-trigger skill`.
