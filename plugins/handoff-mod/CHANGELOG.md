# Changelog

## 0.2.2（2026-10-23）

- 不再註冊 `skill.prompt` hook。在受管機器上（有 managed settings，或 Team／Enterprise 組織），內建的 `cc-plugin-sec-default` 會把 `skill.prompt` 直接送過使用者裝的 plugin，這個 hook 永遠收不到事件，只會讓每次啟動 handoff 時出現「its skill.prompt hook was skipped」的通知。交接 skill 設了 `disable-model-invocation`，只能由使用者打字或 mod 以指令執行，這兩條路徑本來就由 `prompt.submit`（輸入文字以 `/handoff-mod:handoff` 開頭）與 `command.run`（`handoff-mod:handoff`）偵測，所以啟動偵測從三個訊號變成兩個，預期功能不變。在 2.1.308 的 `claude -p` 實測，這兩個訊號打字時都收得到；互動 session（2.1.309）也由作者確認：打字 `/handoff-mod:handoff` 後 `command.run` 與 `prompt.submit` 都會到達，run 只啟動一次（`handoff run started`）。沒有 sec-default 的環境（例如 Cloud）、以及寫檔後的「交接已寫入」toast 沒有在這次改動後重測。

---

- The mod no longer registers a `skill.prompt` hook. On a managed machine (managed settings, or a Team or Enterprise organization), the built-in `cc-plugin-sec-default` passes `skill.prompt` straight over user-installed plugins, so the hook never received an event and only produced an "its skill.prompt hook was skipped" notice each time a handoff started. The handoff skill sets `disable-model-invocation`, so it starts only when typed or run as a command by the mod; those paths were already detected by `prompt.submit` (text starting with `/handoff-mod:handoff`) and `command.run` (`handoff-mod:handoff`), so start detection goes from three signals to two, with no change in behavior expected. Measured with `claude -p` on 2.1.308: both signals arrive when the command is typed. An interactive session (2.1.309) was also confirmed by the author: after typing `/handoff-mod:handoff`, both `command.run` and `prompt.submit` arrive and the run starts once (`handoff run started`). Environments without sec-default (such as Cloud), and the "handoff written" toast after the file is written, were not re-tested after this change.

## 0.2.1（2026-10-20）

- 不再用 `classic.SessionStart`。在有 managed settings 的機器上（例如公司 MDM 派發了 Claude Code 設定），內建的 `cc-plugin-sec-default` 會讓 `classic.*` 事件繞過使用者裝的 plugin，啟動時會看到「its classic.SessionStart hook was skipped」，`/clear` 之後也不會重新列出交接。現在改成在 `session.end`（`reason=clear`）之後等 session id 換掉（最多 10 秒），再列出交接、重設門檻記憶。

---

- No longer uses `classic.SessionStart`. On a machine with managed settings (such as a Claude Code profile pushed by MDM), the built-in `cc-plugin-sec-default` routes `classic.*` events past user-installed plugins: startup showed "its classic.SessionStart hook was skipped", and `/clear` did not list handoffs again. The mod now waits, after `session.end` with `reason=clear`, for the session id to change (up to 10 seconds), then lists handoffs and resets the threshold memory.

## 0.2.0（2026-10-14）

- 同一份交接複製到多個 worktree（或搬目錄留下副本）時，只列一筆。以前每個副本各算一筆。
- 放棄、接續的狀態不再只綁在檔案路徑上。從 0.1.x 升級，以前放棄、接續過的交接，只要檔案還在原位，狀態都保留。0.2.x 也會繼續寫 0.1.x 讀得懂的紀錄，所以升級當下還開著的舊 session、或降版，都看得到新版的放棄與接續。
- **行為改變：** 結束時的自動筆記只在這個 session 改動了工作樹時才寫。以前只要工作樹有任何未提交的變更（包括一個放著不管的 untracked 檔）就寫，每個 session 都會多一份。
- **行為改變：** context 用量到門檻時一律詢問，不再看工作樹乾不乾淨；非 git 目錄也會問。
- 自動筆記「有改動的檔案」裡的中文檔名，不再顯示成 git 的跳脫字串；untracked 資料夾會逐檔列出（仍最多 50 筆），不再只列資料夾名稱。

---

- Copies of one handoff in several worktrees (or left behind by a moved folder) are listed once. Each copy used to count separately.
- Abandoned and resumed states are no longer tied to the file path alone. After upgrading from 0.1.x, handoffs you abandoned or resumed keep that state as long as the file is where it was. 0.2.x also keeps writing records that 0.1.x reads, so an old session still open during the upgrade, or a downgrade, sees what the new version did.
- **Behavior change:** the end-of-session note is written only when this session changed the working tree. It used to be written whenever the tree had any uncommitted change (an untracked file left alone included), one more note per session.
- **Behavior change:** the context threshold prompt is shown whatever the working tree looks like, and outside git too.
- Non-ASCII file names in the note's changed-file list are no longer shown as git's escaped strings; an untracked folder is listed file by file (still at most 50 entries) instead of by its name.
