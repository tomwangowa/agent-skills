# Handoff Mod micro-PoC 計畫

> **給執行者：** 這是驗證計畫，不是實作計畫。PoC 通過、Tom 確認設計後，才另外寫實作計畫。步驟用 `- [ ]` 追蹤。

**目的：** 在寫任何產品程式之前，用一個拋棄式探針 mod 確認設計依賴的平台行為。哪一項不成立，設計就在那一項改。

**設計：** [Handoff Mod 設計](../specs/2026-10-06-handoff-mod-design.md)（草案，未經 Tom 確認）。**結果：** [poc-results.md](../../poc-results.md)。

**分支：** `feat/handoff-mod`。**探針：** `poc/handoff-poc/`（拋棄式，結束後刪除）。

---

## 規則

- 探針只觀察與記錄，不改寫工具呼叫、提示或權限決定。唯一例外是 `/poc-block-clear`，只在使用者自己開啟後才攔 `/clear`。
- 每個探針把結果寫進 `$TMPDIR/handoff-poc.log`（沒設 `TMPDIR` 時 `/tmp/handoff-poc.log`），因為 `/clear` 會清掉 transcript。
- 驗證指令：`claude plugin validate --strict plugins/handoff-mod/poc/handoff-poc`。本機型別在第一次 `claude --plugin-dir` 啟動時產生於 `.claude-plugin/types/`（已 gitignore），API 形狀以它為準。
- 不要把「Cloud 已驗證」寫成「Tom 的環境已驗證」。兩者分開記在 `poc-results.md`。

## 探針指令一覽

| 指令 | 驗證 | 備註 |
| --- | --- | --- |
| `/poc-usage` | V1／L1 | 印 `$.session.usage()`；每個 `turn.complete` 也自動記 |
| `/poc-submit plain｜user｜fill｜cmd｜cmd:<名稱>` | V2／L2 | 一律經計時器呼叫；`cmd:handoff` 試你自己的 skill |
| `/poc-band` | V4／L3／L8 | 在 prompt 上方畫 band，hotkey `1`／`2`／`3` |
| `/poc-ask`、`/poc-ask-timer` | V4／L4 | `$.ui.ask` 三個選項；後者 3 秒後從計時器呼叫 |
| `/poc-pane-timer` | V5 | 2 秒後由 mod 自己開 pane，記 `isPlaced` |
| `/poc-facts` | V6／L7 | root／cwd／repo／git／指令清單 |
| `/poc-block-clear` | V3c | 開關：開啟後 `/clear` 被 hook 取代回答 |
| （自動） | V3／L5／L6 | `command.run`（clear／compact／exit）、`session.compact`、`session.end`、`classic.SessionStart`、`skill.prompt`、`prompt.submit`（斜線開頭） |

---

## Task 0：Cloud 能做的部分（已完成，2026-10-06）

- [x] 寫探針並 `claude plugin validate --strict` 通過。
- [x] 讀本機產生的型別（`index.d.ts`，Claude Code 2.1.291），核對 `session.usage`、`prompt.submit`、`command.run`／`list`、`ui.ask`、`session.root`／`repo`、`fs`、`env`、`store` 的簽名。
- [x] V1、V2、V3（`/clear`、`/compact` 進 `command.run`、取消 `/clear`）、V4（band、hotkey、ask）、V5、V6：用 `claude -p` 與 pty 驅動的互動 session 實測，結果見 `poc-results.md`。
- [x] 依實測修正探針：`prompt.submit` 不能送斜線文字、`prompt.submit`／`command.run` 不能從 `command.run` hook 內呼叫，改用 `$.command.run({command})` 加計時器。

## Task 1：Tom 的本機驗證（L1–L8）

**準備（一次）：**

- [ ] `git fetch && git switch feat/handoff-mod`。
- [ ] `claude --plugin-dir plugins/handoff-mod/poc/handoff-poc`。若 `claude plugin test` 或載入說明 hooks modules 被關閉，先 `claude -p "ok"` 一次再重試（attention-mod 的既有經驗）。
- [ ] 同時開第二個終端機 `tail -f "${TMPDIR:-/tmp}/handoff-poc.log"`。

**逐項：**

- [ ] **L1 用量對照。** 在一段真實工作後 `/poc-usage`，再 `/context`。記下 `tokens`、`window`、`percent` 與 `/context` 的數字，以及你預設模型的 `window`。**預期：** `percent = tokens / window`，已用百分比。
- [ ] **L2 你自己的 handoff。** 先 `/poc-facts`，確認 log 的 `handoff-like` 有 `handoff[user]`。再 `/poc-submit cmd:handoff`。記下：skill 有沒有展開、有沒有走到「Review Gate」問你、有沒有真的寫出 `.claude/handoffs/` 檔案。
- [ ] **L3 hotkey 衝突。** `/poc-band` 後，請 Claude 「用 AskUserQuestion 問我一個三選一」，在問題出現時按 `1`。記下按到的是 band 還是問題。
- [ ] **L4 工作中提問。** 請 Claude 跑 `sleep 30` 的 Bash，同時輸入 `/poc-ask-timer`（指令已註冊 `immediate`）。記下 3 秒後的 `$.ui.ask` 是否彈出、是否擋住輸入、答完後 Claude 是否照常。
- [ ] **L5 壓縮。** 在有內容的 session 內 `/compact`。記下 log 裡 `command.run compact`、`session.compact`、`session.measure` 的順序與時間。
- [ ] **L6 真正結束。** 分別用 Ctrl-D、`/exit`、直接關分頁各結束一次，之後看 log 有沒有 `session.end` 及原因。
- [ ] **L7 範圍。** 在下列位置各啟動一次並 `/poc-facts`：repo 根目錄、repo 子目錄、非 git 目錄、`git worktree add` 出來的 worktree、session 中途 `/cd` 之後。記下 `root`、`repo().root`、`repo()` 是否為 null。
- [ ] **L8 共存。** `claude --plugin-dir <attention-mod> --plugin-dir <handoff-poc>`，依序 `/poc-band`、`/poc-ask`，看 band 與 attention-mod 的面板是否互相遮蔽、「需要你」是否因 `$.ui.ask` 亮起。

**回報方式：** 把 log 與觀察貼進 `docs/poc-results.md` 的「待本機」表格（把「待本機」改成「已驗證（本機）」或「失敗」）。

## Task 2：依結果決定設計（決策表）

| 結果 | 設計的處理 |
| --- | --- |
| L1：`percent` 與 `/context` 一致 | 門檻用 `usage().context.percent`，維持設計 |
| L1：不一致 | 改用 `tokens / window` 自算，或 `usage({breakdown:'summary'})`；先查差異來源再定 |
| L2：能啟動、有照格式寫出檔案 | 偵測到 `source:'user'` 的 `handoff` 時可優先用（D7），但仍驗證寫出的 frontmatter |
| L2：無法啟動或格式不同 | 一律用內建 `handoff-mod:handoff`；使用者自己的 skill 不接 |
| L3：衝突 | 有 `AskUserQuestion` 等待時隱藏 band；訊號用 attention-mod 已有的等待判斷 |
| L3：無衝突 | 只要閒置就顯示 band |
| L4：能彈出且不擋工作 | 門檻提示不限於閒置 |
| L4：擋住輸入或打亂工作 | 門檻提示只在 `turn.complete` 之後的閒置時出現，其餘排隊 |
| L5：`session.compact` 前能彈提示 | 加第四個觸發點「壓縮前」 |
| L5：不能 | 只保留門檻與 `/clear` 兩個自動觸發點；壓縮由門檻提前覆蓋 |
| L6：Ctrl-D／`/exit`／關分頁都有 `session.end` | D4（結束時留事實筆記）列為可選功能 |
| L6：有些結束方式沒有 | D4 不做，或改成每回合結束更新一份筆記 |
| L7：worktree 的 `root()` 不同、`repo().root` 相同 | 用 `repo().root` 聚合同一個 repo 的交接，`root()` 標示來源 worktree |
| L7：非 git 目錄 `repo()` 為 null | 以 `root()` 為鍵，不做新鮮度檢查，並在清單標示「無法驗證」 |
| L8：band 互相遮蔽 | 設計要把我們的內容與 `next(e)` 的結果並排（探針已這樣寫），仍不行就改用 toast＋指令 |

- [ ] 把每一列依實測結果標成採用哪一欄，更新設計文件的「待決」與「已查證」。

## Task 3：收尾

- [ ] Tom 確認設計後，刪除 `poc/`（`git rm -r plugins/handoff-mod/poc`），保留 `docs/poc-results.md`。
- [ ] 另寫實作計畫（`plans/…-handoff-mod.md`），依 `claude-workflow-designer` 或 `superpowers:writing-plans`。
- [ ] 實作前不要建立正式的 `.claude-plugin/plugin.json`，也不要動 `.claude-plugin/marketplace.json`。

## 這份 PoC 沒有涵蓋

- 交接檔內容的品質（模型寫出來準不準）。這要用真實 session 抽查，放到實作後。
- 同事的環境（版本、公司對 plugin 的政策、`managed settings`）。需要 Tom 向同事確認。
- 成本。`handoff` 本身是一個回合；沒有量到實際花費。
