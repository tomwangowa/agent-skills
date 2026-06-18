# Output Styles (tracked here, symlinked into `~/.claude/output-styles/`)

Claude Code reads output styles from `~/.claude/output-styles/*.md`. To keep them
under version control, the **real file lives here** and the live location is a
**symlink** back to this directory:

```
~/.claude/output-styles/deai-tom.md  ->  ../skills/output-styles/deai-tom.md
```

So this repo is the single source of truth; editing the file here (or via the live
symlink path — same inode) is the same change.

**Activate**: `/config` → Output style. (The standalone `/output-style` command was
removed; activation is the `/config` menu.) A style needs `/clear` or a new session
to take effect, and is stored in `.claude/settings.local.json`.

`output-styles` is listed in `.skill-sync-ignore`, so `skill-sync` does **not** mirror
these Claude-Code-specific files into other agents' (Codex/Gemini/Cursor) skill folders.

## Styles

- **deai-tom.md** — de-AI'd + plain-language responses; outward-facing deliverables I
  generate follow Tom's voice, ordinary conversation stays plain-but-me. Pairs with the
  `deai-voice-rewrite` skill, which holds the single source of truth for the de-AI rules.
  Uses `keep-coding-instructions: true` so engineering behavior is unaffected.

## Re-create the symlink (if it ever goes missing)

```sh
ln -s ../skills/output-styles/deai-tom.md ~/.claude/output-styles/deai-tom.md
```
