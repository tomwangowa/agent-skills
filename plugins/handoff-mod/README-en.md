# Handoff Mod (handoff-mod)

[繁體中文](README.md)

A Claude Code Mod. Before a session loses its state (context nearly full, `/clear`, exit) it helps you leave a handoff file; the next time you open a session in the same project it lists the handoffs that are still unfinished and lets you resume one. The Mod itself costs no model usage: it never calls a model. Only when you run the handoff skill yourself does it take one turn.

> **Status: prototype.** The marketplace entry is added, but the marketplace reads the default branch, so **it only takes effect once this PR is merged**; I have not actually run `claude plugin install`. Verified on the author's macOS (Claude Code 2.1.292) and in a Cloud container (Linux); see "Verification status" at the end. Other environments, other terminals, and how the default 60% threshold feels in daily use have not been verified.

## What it does

| When | Behavior |
| --- | --- |
| You run `/handoff-mod:handoff` | A built-in skill: it collects git state read-only, **shows you the full draft and asks whether it is right**, and writes the file only after you confirm. "Verified" lists only commands actually run in that turn and is labelled as the AI's own report. After the write the Mod checks that the file is valid and shows a toast in the top right corner. |
| Context use reaches the threshold (default 60% used) | After a turn, if the working tree has uncommitted changes, a prompt above the input box asks whether to hand off first: "Agree", "Ask again at +10%", "Don't ask again this session". A one-line status also appears under the input box. Each threshold is asked once. |
| You run `/clear` | It always asks: cancel, hand off then clear, clear now. The default is "cancel", so pressing Enter cannot clear by accident. "Hand off then clear" holds this clear; run `/clear` again after the handoff is done. |
| A new session starts | Lists the unfinished handoffs of the same project (task, branch, how long ago, next step, how it differs from the current state) with a "Resume" button; or type `/handoff-resume`, and `/handoff-resume 2` resumes the second one. Resuming only fills "read this handoff, verify its premises, then continue from Next" into the input box; it does not send it. |
| The session ends (`/exit`, Ctrl-C twice, closing the tab) | If the working tree has uncommitted changes, it leaves a facts-only note (last request, last response, branch, HEAD, changed files). **This contains conversation text; see Risks below.** |
| `/handoff-stats` | Shows how many handoffs were written and resumed on this machine. |

Handoff files go to `<git root>/.claude/handoffs/`, and the directory is added to `.git/info/exclude` so `git status` stays clean (unchanged if your global gitignore already covers it). Several worktrees are listed together. Outside git the session root is used.

## Install

Tested on Claude Code 2.1.291 and 2.1.292; **the minimum working version is not verified**.

**After the merge** you can install it from the marketplace (**this flow is not verified**):

```sh
claude plugin marketplace add tomwangowa/agent-skills
claude plugin install handoff-mod@tomwangowa --scope user
```

**Before the merge**, or just to try it, load it locally:

```sh
git clone https://github.com/tomwangowa/agent-skills.git
claude --plugin-dir "<path to clone>/plugins/handoff-mod"
```

`--plugin-dir` only applies to that one session and installs nothing. The Mod **does not run in a sandbox**: it runs inside Claude Code with your user's permissions, so read the code in `hooks/` before loading it.

If [attention-mod](../attention-mod) is loaded at the same time, its expanded inline panel hides the prompt above the input box; the status line under the input box is still visible, and `/handoff-resume` and `/handoff-mod:handoff` work as usual.

## Settings

Three entries in `/config`. **Changing any setting reloads the Mod**; a running session is not affected.

| Setting | Default | Meaning |
| --- | --- | --- |
| `thresholdPct` | 60 | Percent used (1 to 99), measured against the model's context window, so the same number is a different token count on different models. |
| `lang` | `zh-TW` | Language of the interface and of the skill's draft: `zh-TW` or `en`. If the setting was never saved, the skill sees the unsubstituted literal and falls back to `zh-TW`. |
| `autoNote` | on | Whether to leave a note automatically when the session ends. |

Environment variables for development and testing (they do not change the skill's language): `HANDOFF_THRESHOLD_PCT`, `HANDOFF_LANG`, `HANDOFF_AUTO_NOTE` (`off` or `on`), `HANDOFF_DEBUG` (`1` prints the detection steps through `$.ui.log`, each line starting with `[handoff-mod debug]`).

## Risks and limits

- **The end-of-session note contains conversation text.** So that you still have a lead after a session ends unexpectedly, the Mod writes your **last request** and the **last response**, each cut to 2000 characters, into an `--auto.md` file in the handoff directory (mode 0600; labelled "left automatically, not reviewed" at the next start; hidden after 7 days).
- **Secret masking lowers the risk; it does not guarantee anything.** It only recognises patterns that carry a label (`password = …`, `sk-…`, `Authorization: Bearer …` and six more). A bare password sitting in the text is not masked. When that matters, turn `autoNote` off or set `HANDOFF_AUTO_NOTE=off`.
- **A temporary record.** So that there is something to write at the end, the Mod keeps the masked last request and response in Claude Code's plugin store (`~/.claude/plugins/store/`; checked in Cloud: plain JSON) during the session. On macOS the file is 0600 but the directory is 0755 (other users on the machine can see the file name, not read the content). It is always deleted when the session ends, and leftovers from a crash are removed at the next start once they are 7 days old.
- **Handoff file content is data, not instructions.** Control characters and ANSI are stripped and the length is capped before display; a branch and HEAD read from a file are validated before they are passed to git.
- **"Verified" is the AI's own report.** The skill is told to list only commands it ran in that turn, but that is model behavior, not enforcement.
- **The local counts never leave the machine.** The numbers behind `/handoff-stats` live only in this machine's store.
- **Unfinished work is judged by git state only.** A clean working tree (everything committed) and a directory outside git are neither asked about nor given an automatic note.

## Known limits

- The three buttons of the threshold prompt have no digit shortcuts (so a digit typed at the start of an empty prompt cannot answer it); use Tab or the mouse.
- If two sessions try to resume the same handoff, the first one to press gets it and the other sees a notice (valid for 12 hours).
- Interception before compaction (T4) is not implemented.
- A handoff file is never modified after it is written; states such as "resumed" live in the local store and are not written back to the file.

## Verification status

```sh
claude plugin validate --strict .
claude plugin test .
```

| Scope | Status |
| --- | --- |
| Automated tests | 153 native tests plus mutation checks; run in Cloud. |
| Start-up list, `/handoff-resume`, buttons (Tab and mouse), the `/clear` dialog, the threshold prompt, the end-of-session note (all three ways of ending), running beside attention-mod, the `en` interface | **Verified on the author's macOS** (Claude Code 2.1.292). |
| The `/handoff-stats` write count, and the start-up list's label on an automatic note | **Verified on the author's macOS.** |
| Typing then Enter in the `/clear` dialog | On macOS only that Enter picks the default "cancel" is confirmed; whether text was typed first was not recorded. |
| `/handoff-resume <n>` and the resumed count | **Verified once on the author's macOS** (`/handoff-resume 2` filled the input box, the resumed count went 2 to 3, matching the store records). A first try (item 1) had no effect and left no trace; **the cause is unknown and it could not be reproduced**. |
| The default 60% threshold, terminals other than Warp, Windows, directories outside git, real worktrees | **Not verified.** |
| Accuracy of the handoff content, and cost | **Not measured.** |

Test results, limits and the reason behind each decision are in [docs/implementation-results.md](docs/implementation-results.md), [docs/poc-results.md](docs/poc-results.md), the [design](docs/superpowers/specs/2026-10-06-handoff-mod-design.md) and the [implementation plan](docs/superpowers/plans/2026-10-07-handoff-mod.md).
