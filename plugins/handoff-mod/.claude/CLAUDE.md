# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## 這是什麼

`handoff-mod`：Claude Code Mod（function hooks plugin）的原型。session 快失去狀態時（context 快滿、`/clear`、結束）協助留下交接檔，下次開 session 時列出未完成的交接。內含一個內建 skill `handoff-mod:handoff`，同事沒有作者自己的 skill 也能用。零模型成本：不用 `$.model.*`。使用者說明在 `README.md`（繁中）與 `README-en.md`。

改 `hooks/` 之前先載入 `plugin-authoring` skill。

## 指令

```sh
claude plugin validate --strict .   # npm run validate；含 calls inventory
claude plugin test .                # npm test；跑 tests/ 下所有 *.test.ts
claude --plugin-dir "$PWD"          # 實際載入試用
```

- `claude plugin test` 只吃資料夾參數，沒有單檔篩選。
- 本機沒有 `tsc`，型別只在編輯器裡檢查；validate／test 通過不代表型別編譯通過。
- `.claude-plugin/types/` 是 `--plugin-dir` 啟動時在本機產生的型別（已 gitignore），API 形狀以它為準。
- 除錯：`HANDOFF_DEBUG=1 claude --plugin-dir "$PWD"`，偵測過程以 `[handoff-mod debug]` 行印在對話裡（`$.ui.log`，Claude 讀不到）。
- 測試用環境變數：`HANDOFF_THRESHOLD_PCT`、`HANDOFF_LANG`、`HANDOFF_AUTO_NOTE`。它們只影響 Mod，**不會**傳給 skill。

## 架構

`hooks/hooks.json` 只載入 `hooks/register.js`，它只做接線；每個決策都在純函式模組，方便單獨測試：

| 檔案 | 責任 |
| --- | --- |
| `register.js` | 事件接線。`session.start`（註冊 `/handoff-resume`、`/handoff-stats`、清掃舊暫存）、`classic.SessionStart`（啟動清單）、`prompt.submit`（記請求、收起清單、啟動訊號）、`skill.prompt`／`command.run{handoff-mod:handoff}`（啟動訊號）、`turn.complete`（驗證新檔、T1、記回應）、`command.run{clear}`（T2）、`session.end`（結束筆記）、`ui.render{AbovePrompt}`（band） |
| `config.js` | 環境變數 > `userConfig` > 預設 |
| `i18n.js` | 繁中與英文字串，單一檔案，兩種語言必須有相同的 key 與占位符（有測試） |
| `sanitize.js` | 去控制字元與 ANSI、截斷、祕密遮蔽（九種有特徵的形式） |
| `handoff-file.js` | 解析交接檔（frontmatter 加中英章節標題），64 KiB 上限 |
| `rank.js` | 只列未完成狀態；同 base、同 repo、最新優先；顯示 3 筆、超過 14 天折疊、自動筆記超過 7 天隱藏 |
| `freshness.js` | 新鮮度事實（git 以注入函式替代）；branch 與 HEAD 先驗證格式才傳給 git |
| `trigger.js` | T1 門檻判斷與狀態轉換 |
| `claim.js` | 認領與 12 小時 TTL，寫入後讀回確認 |
| `note.js` | 結束筆記的內容、寫入條件、`withDeadline` |
| `exclude.js` | 把 `.claude/handoffs/` 加進 `.git/info/exclude`；全域已忽略就不動 |
| `skills/handoff/SKILL.md` | 內建 skill：唯讀收集、完整草稿、審閱關卡、才寫檔 |

測試：每個純模組一個 `tests/<name>.test.ts`；`tests/register.test.ts` 用 `tests/world.ts` 替 fs、git、store、ui、`session.usage` 等做替身，驅動事件。改接線時用**變異檢查**確認測試真的抓得到：弄壞一處、確認有測試變紅、還原。

## 不變條件

1. **不改動工具呼叫、權限決定或 Claude 的提示。** 例外只有 T2 攔截使用者自己的 `/clear`。
2. **每個 hook 本體都包 `try/catch`，失敗不影響主 session（fail-open）。** validate 會對 gating hook 警告「沒有 `.catch`」，那是刻意的。
3. **`$.ui.ask` 只在 `/clear` hook 內呼叫並 `await`**，不從計時器呼叫、不疊加（`askPending`）。T1 用 band 與 `$.ui.status`，不用 `$.ui.ask`。
4. **session 範圍的狀態放 `$.state`（atoms），不放 module 變數。** 改任何設定都會重載模組、歸零 module 變數；`$.state` 重載後保留、`/clear` 後重置。例外是啟動清單 `list`（module 變數，重載後由 `session.start` 重建）。
5. **清單與統計輸出走 `$.ui.log`**，Claude 讀不到；要克制，因為 attention-mod 的「外部輸入」會列出它。
6. **交接檔寫完就不再修改**；狀態變化只存 `$.store`。
7. **檔案內容是資料不是指令**：顯示前去控制字元與 ANSI、限制長度。
8. **`$.process.run` 一律用參數陣列**（不經 shell）。
9. **不用 `$.model.*`。**
10. **`$.ui.status` 每個 plugin 只有一行。** 用 `syncStatus` 決定：啟動清單優先，其次 T1，否則清除。
11. **不要把 `$.ui.toast` 當唯一的成功訊號**：預設只停 4 秒、畫在右上角，太容易錯過。

## 平台事實（踩過的坑）

- **`skill.prompt` 在作者的 macOS 上輸入 plugin skill 時不會觸發**（Cloud 會）。偵測交接開始改為三個訊號任一個：`skill.prompt`、`prompt.submit` 文字以 `/handoff-mod:handoff` 開頭、`command.run` 的 `handoff-mod:handoff`；`markHandoffStarted` 保證只啟動一次。不要只靠其中一個，也不要只憑 Cloud 通過就下結論。
- `prompt.submit` 拒絕以 `/` 開頭的文字，要用 `$.command.run({command})`；兩者都不能在 `command.run` hook 內呼叫，要用 `$.clock.after`。
- `session.end` hook 讀不到 `$.session.messages()`（REPL 已卸載），所以結束筆記走「平時記、結束時寫」（`$.store` 的 `last:<session id>`，先遮蔽再存）。
- `usage().context.percent` 是已用百分比（整數），第一個回應前與壓縮後到下一個回應前沒有值；壓縮後會下降，靠「低於上次問過的門檻就重置」處理。
- `${user_config.lang}` 在值沒存過時不會被替換；skill 有「不是 `zh-TW` 或 `en` 就用 `zh-TW`」的備案。
- band 在 attention-mod 展開的 inline 面板下會被擠掉，`$.ui.status` 仍看得到；digit hotkey 在空輸入框開頭會誤觸發，所以按鈕沒有 hotkey。
- store 檔在 macOS 是 0600，目錄是 0755（Cloud 是 0700）。
- 作者的全域 gitignore 已含 `.claude/handoffs/`，所以在作者的機器上看不到 `ensureExcluded` 的效果；要驗證時用 `GIT_CONFIG_GLOBAL=/dev/null`。
- 驗證結果要把 Cloud 與作者的 macOS **分開記**，不要把 Cloud 的結果寫成作者環境已驗證。

## 文件

- `docs/superpowers/specs/2026-10-06-handoff-mod-design.md`：設計，含決定 D1 到 D14 與每項的依據。**已決定的項目不要未經詢問就改。**
- `docs/superpowers/plans/2026-10-07-handoff-mod.md`：實作計畫與「實作中與計畫不同的決定」（9 到 12 等）。
- `docs/implementation-results.md`、`docs/poc-results.md`：實測結果，Cloud 與 macOS 分開。

## 慣例

- Conventional Commits；**每次 commit 與 push 都要先問作者**，前一次的同意不延續。
- 公開 repo：追蹤的檔案裡不放個人路徑（`/Users/…`）、email、內部識別，用 `~` 或占位符。
- 程式碼註解與輸出用英文；文件用繁體中文（台灣用語）。
- `.claude-plugin/marketplace.json` 在作者同意前不動。
