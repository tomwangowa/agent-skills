# 交接 Mod（handoff-mod）

[English](README-en.md)

Claude Code Mod。在 session 即將失去狀態之前（context 快滿、`/clear`、結束）協助你留下一份交接檔；下次在同一個專案開新 session 時，列出還沒做完的交接，讓你一鍵接續。零模型成本：Mod 本身不呼叫模型，只有你自己執行交接 skill 時才花一個回合。

> **狀態：原型，尚未上架 marketplace。** 在作者的 macOS（Claude Code 2.1.292）和 Cloud container（Linux）驗證過，見最下方「驗證狀態」。其他環境、終端機與預設的 60% 門檻實際用起來的感覺，還沒有人驗證。

## 它做什麼

| 時機 | 行為 |
| --- | --- |
| 你執行 `/handoff-mod:handoff` | 內建 skill：唯讀收集 git 狀態，**先把完整草稿給你看、問你對不對**，你確認後才寫檔。「已驗證」只列這個回合真的跑過的指令，並標明是 AI 自述。寫完後 Mod 會檢查檔案是否有效，右上角顯示 toast。 |
| context 用量到門檻（預設已用 60%） | 一個回合結束後，若工作樹有未提交的變更，在輸入框上方問你要不要先交接：「同意」「再多 10% 再問」「這個 session 別再問」。同時在輸入框下方放一行狀態。每個門檻只問一次。 |
| 你下 `/clear` | 一律問：取消、先交接再清除、直接清除（預設在「取消」，按 Enter 不會誤清）。選「先交接再清除」會暫停這次清除，交接完成後請再下 `/clear`。 |
| 開新 session | 列出同一專案還沒做完的交接（任務、分支、幾分鐘前、下一步、與現況的差異），可按「接續」；或輸入 `/handoff-resume`，`/handoff-resume 2` 接續第 2 筆。接續只會把「請先讀這份交接、驗證前提再接續」填進輸入框，不會自動送出。 |
| session 結束（`/exit`、Ctrl-C 兩次、關分頁） | 若工作樹有未提交的變更，自動留下一份只含事實的筆記（最後一個要求、最後一段回應、branch、HEAD、有改動的檔案）。**含對話原文，見下方風險。** |
| `/handoff-stats` | 顯示這台機器上交接寫入與接續的次數。 |

交接檔放在 `<git 根目錄>/.claude/handoffs/`，並寫進 `.git/info/exclude` 避免弄髒 `git status`（如果你的全域 gitignore 已涵蓋就不改）。多個 worktree 會一起列出。不在 git 內時用 session 的根目錄。

## 安裝

作者測的是 Claude Code 2.1.291 與 2.1.292，**最低可用版本沒有驗證**。目前沒有上架 marketplace，用本機載入：

```sh
git clone https://github.com/tomwangowa/agent-skills.git
claude --plugin-dir "<clone 路徑>/plugins/handoff-mod"
```

這只在那一次 session 有效，不會安裝任何東西。Mod **不在 sandbox 裡執行**，會以你的使用者權限跑在 Claude Code 裡，載入前請先看過 `hooks/` 的程式碼。

如果同時載入 [attention-mod](../attention-mod)，展開的 inline 面板會把輸入框上方的提示遮住；輸入框下方那一行狀態仍然看得到，`/handoff-resume` 與 `/handoff-mod:handoff` 照常可用。

## 設定

在 `/config` 裡有三項。**改任何設定都會讓 Mod 重新載入**，不影響進行中的 session。

| 設定 | 預設 | 說明 |
| --- | --- | --- |
| `thresholdPct` | 60 | 已用百分比（1 到 99）。百分比是對模型的 context window 算的，同一個數字在不同模型是不同的 token 數。 |
| `lang` | `zh-TW` | 介面與 skill 草稿的語言：`zh-TW` 或 `en`。沒存過這個設定時，skill 看到的是未替換的字面值，會退回 `zh-TW`。 |
| `autoNote` | 開 | 是否在結束時自動留下筆記。 |

開發與測試用的環境變數（不影響 skill 的語言）：`HANDOFF_THRESHOLD_PCT`、`HANDOFF_LANG`、`HANDOFF_AUTO_NOTE`（`off` 或 `on`）、`HANDOFF_DEBUG`（`1` 時用 `$.ui.log` 印出偵測過程，行首是 `[handoff-mod debug]`）。

## 風險與界線

- **結束筆記含對話原文。** 為了讓你在 session 意外結束後還有線索，Mod 會把你**最後一個要求**與**最後一段回應**各截斷到 2000 字，寫進交接目錄的 `--auto.md`（檔案權限 0600，下次啟動標示「自動留下，未經審查」，超過 7 天不再顯示）。
- **祕密遮蔽只降低風險，不是保證。** 只認有特徵的形式（`password = …`、`sk-…`、`Authorization: Bearer …` 等九種）。單獨出現在文字裡的密碼不會被遮蔽。需要時把 `autoNote` 關掉，或設 `HANDOFF_AUTO_NOTE=off`。
- **暫存紀錄。** 為了在結束時還有東西可寫，Mod 平時把已遮蔽的最後一組請求與回應放在 Claude Code 的 plugin store（`~/.claude/plugins/store/`；在 Cloud 查過是明文 JSON）。檔案權限在 macOS 是 0600，但目錄是 0755（同機器的其他使用者看得到檔名，讀不到內容）。session 結束時一律刪除，當機留下的殘餘超過 7 天會在下次啟動時清掉。
- **交接檔的內容是資料，不是指令。** 顯示前會去控制字元與 ANSI，並限制長度；檔案裡的 branch 與 HEAD 在傳給 git 前會先驗證。
- **「已驗證」是 AI 的自述。** skill 只被要求列這個回合真的跑過的指令，但這是模型的行為，不是強制。
- **本機計數不外傳。** `/handoff-stats` 的數字只存在這台機器的 store。
- **只看 git 狀態判斷有沒有未完成的工作。** 乾淨的工作樹（已全部 commit）與非 git 目錄不會被問，也不會自動留下筆記。

## 已知限制

- 門檻提示的三個按鈕沒有數字快捷鍵（避免你在空輸入框開頭打數字時誤答），可用 Tab 或滑鼠。
- 同時開兩個 session 接續同一份交接時，先按的那一個拿到，另一個會看到提示（12 小時內有效）。
- 壓縮前的攔截（T4）沒有做。
- 交接檔寫完就不再修改；「已接續」等狀態存在本機 store，不會寫回檔案。

## 驗證狀態

```sh
claude plugin validate --strict .
claude plugin test .
```

| 範圍 | 狀態 |
| --- | --- |
| 自動測試 | 原生測試 153 項，另有變異檢查；在 Cloud 跑。 |
| 啟動清單、`/handoff-resume`、按鈕（Tab 與滑鼠）、`/clear` 的對話框、門檻提示、結束筆記（三種結束方式）、與 attention-mod 同載入、`en` 介面 | **作者的 macOS 驗證過**（Claude Code 2.1.292）。 |
| `/handoff-stats` 與 `stats.written` 的計數、對話框打字後 Enter、新 session 看自動筆記的標示 | 只在 Cloud 驗證，**macOS 尚未確認**。 |
| 預設 60% 門檻、Warp 以外的終端機、Windows、非 git 目錄、真實 worktree | **沒有驗證**。 |
| 交接內容的準確度與成本 | **沒有量測。** |

測試結果、限制與每項決定的依據在 [docs/implementation-results.md](docs/implementation-results.md)、[docs/poc-results.md](docs/poc-results.md)、[設計](docs/superpowers/specs/2026-10-06-handoff-mod-design.md)、[實作計畫](docs/superpowers/plans/2026-10-07-handoff-mod.md)。
