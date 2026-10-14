# Changelog

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
