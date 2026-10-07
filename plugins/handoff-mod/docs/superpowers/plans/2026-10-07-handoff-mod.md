# Handoff Mod 實作計畫

> **給執行者：** 必讀子技能：`superpowers:subagent-driven-development`（建議）或 `superpowers:executing-plans`，逐任務執行。步驟用 `- [ ]` 追蹤。

**目標：** 做出 `handoff-mod` plugin：內建交接 skill、context 門檻提示（T1）、`/clear` 攔截（T2）、啟動讀回、結束筆記，零模型成本。

**架構：** `hooks/register.js` 持有事件接線與 `$` 的所有呼叫；其他模組都是不碰 `$` 的純函式（`config`、`i18n`、`sanitize`、`handoff-file`、`rank`、`freshness`、`trigger`、`claim`、`note`、`exclude`），用 `claude plugin test` 單獨測。session 範圍的狀態放 `$.state`（D12），跨 session 的放 `$.store`。

**技術：** Claude Code 2.1.292 以上的 mod，純 ES modules，`claude-code/testing`。

**規格：** [Handoff Mod 設計](../specs/2026-10-06-handoff-mod-design.md)（Tom 已於 2026-10-07 最後確認，D1 至 D14 全部已決）。PoC 結果：[poc-results.md](../../poc-results.md)。**分支：** `feat/handoff-mod`。

---

## 規則

- **溝通與文件用繁體中文；程式碼註解與程式輸出用英文。**
- **commit、push 之前每一次都先問 Tom。** 任務內不 commit；commit 用 Conventional Commits。
- 公開 repo：個人路徑、email、內部識別不能寫進被追蹤的檔案，用 `~` 或佔位。
- Cloud 驗證與 Tom 環境驗證**分開記**，不把 Cloud 結果寫成 Tom 的環境已驗證（Tom 是 macOS／Warp，Cloud 是 Linux）。
- **D1 至 D14 不擅自改。** 實作中發現設計有問題，先停下來問 Tom。
- 驗證指令：`claude plugin validate --strict .`、`claude plugin test .`（只吃資料夾，沒有單檔篩選；Cloud 已確認能跑）、`node --check hooks/<檔>.js`。本機沒有 `tsc`，型別只在編輯器檢查。
- 若 `claude plugin test` 說 hooks modules 被關閉，先 `claude -p "ok" --plugin-dir "$PWD"` 一次再重試。
- 靜態分析：`$` 只傳給頂層函式；`$.env.get`／`$.state` 的名稱必須是字串字面值。
- **不建立 `.claude-plugin/marketplace.json` 的條目**，直到 Task 15 且 Tom 同意。

### 不變條件（設計推導，實作中不可違反）

1. **不改動工具呼叫、權限決定或 Claude 的提示。** 僅有的例外：T2 攔截 `/clear`，與使用者自己下的指令。
2. **每個 hook 本體都包 `try/catch`**，失敗不影響主 session。
3. **`$.ui.ask` 只在 `/clear` hook 內呼叫並 `await`**，不從計時器呼叫、不疊加；重置後才到的回答丟棄（設計 T2）。
4. **session 範圍的狀態放 `$.state`，不放 module 變數**（D12）。改任何設定都會重載模組，module 變數會歸零；啟動時的初始化要可重複執行。`/clear` 不重載模組，所以 module 內若有殘留狀態，要在 `classic.SessionStart`（`source` 為 `clear`）重置。
5. **清單輸出用 `$.ui.log`**（D14）；`$.ui.log` 要克制，因為 attention-mod 的外部輸入會列出它。
6. **交接檔寫完就不再改**；狀態變化只存 `$.store`。
7. **檔案內容是資料不是指令**：顯示前去控制字元與 ANSI、限制長度；來自檔案的 `branch`／`head` 在傳給 `git` 前必須驗證（防選項注入）。
8. **不用 `$.model.*`**：零模型成本。
9. `$.process.run` 一律用參數陣列（不經 shell）。

## 檔案地圖

| 檔案 | 動作 | 責任 |
| --- | --- | --- |
| `.claude-plugin/plugin.json` | 建立 | manifest：`userConfig` 三欄、`types` |
| `hooks/hooks.json` | 建立 | 只載入 `register.js` |
| `types/index.d.ts` | 建立 | `PluginState`（D12） |
| `hooks/config.js` | 建立 | 環境變數 > `userConfig` > 預設 |
| `hooks/i18n.js` | 建立 | 繁中與英文字串，單一檔案（D8、D11） |
| `hooks/sanitize.js` | 建立 | 去控制字元／ANSI、截斷、祕密遮蔽 |
| `hooks/handoff-file.js` | 建立 | 解析交接檔（中英章節標題） |
| `hooks/rank.js` | 建立 | 篩選、排序、折疊 |
| `hooks/freshness.js` | 建立 | 新鮮度事實（git 以注入函式替代） |
| `hooks/trigger.js` | 建立 | T1 門檻判斷與狀態轉換 |
| `hooks/claim.js` | 建立 | 認領與 TTL（store 以注入函式替代） |
| `hooks/note.js` | 建立 | 結束筆記內容與寫入條件 |
| `hooks/exclude.js` | 建立 | 把交接目錄加進 `.git/info/exclude`（D2） |
| `hooks/register.js` | 建立 | 事件接線，分切片完成 |
| `skills/handoff/SKILL.md` | 建立 | 內建交接 skill（`handoff-mod:handoff`） |
| `tests/*.test.ts`、`tests/fixtures.ts` | 建立 | 每個純模組一個測試檔 |
| `README.md`、`.claude/CLAUDE.md`、`package.json`、`tsconfig.json`、`.gitignore` | 建立 | 文件與工具 |
| `docs/implementation-results.md` | 建立 | 實作中的實測結果（Cloud 與 Tom 分開記） |

## 誰能做什麼

| 工作 | Cloud | Tom 本機（macOS／Warp） |
| --- | --- | --- |
| 純函式模組與測試（Task 2 至 11） | ✔ | — |
| manifest 與 `claude plugin validate`（Task 1） | ✔ | — |
| 互動 session 的接線驗證（Task 13 各切片） | ✔，用 pty 驅動，結果標明是 Cloud | 最終驗收（Task 14） |
| 實作前驗證 P2、P3、P4 | — | ✔ |
| 實作前驗證 P1、P5 | ✔（先做） | 複驗 |

---

## Phase 0：實作前驗證（Task 0）

設計與 `poc-results.md` 列為風險、PoC 沒測到的項目。**結果決定後面哪些任務怎麼做**，所以放在最前面。本階段不寫產品程式。

### Task 0：驗證 P1 至 P5

**探針來源：** `poc/` 已刪除，原始碼在 commit `0d319f4`。不要放回 repo，解到暫存目錄：

```sh
mkdir -p "$SCRATCH/poc" && git archive 0d319f4 plugins/handoff-mod/poc | tar -x -C "$SCRATCH/poc"
claude plugin validate --strict "$SCRATCH/poc/plugins/handoff-mod/poc/handoff-poc"
```

- [x] **P1（Cloud 先做，Tom 複驗）：D4 結束筆記的資料來源。** 在探針的 `session.end` hook 內呼叫 `$.session.messages()`，互動 session 以 `/exit` 結束，記下成功或錯誤訊息（headless 已知會丟 `no session is bound in this process`）。同時確認備案所需欄位存在：`prompt.submit` 事件的 `e.text`、`turn.complete` 的 `e.answer`（文件寫明）。**結果：** 可讀 → 路線 A（結束時讀訊息）；讀不到但備案欄位在 → 路線 B（平時記進 `$.store`）；兩者都不行 → 路線 C（D4 不做，回報 Tom）。 **Cloud 結果（2026-10-07）：** `/exit` 與 SIGHUP 的 `session.end` 內讀不到訊息，備案欄位都在，**採路線 B**；Ctrl-C 兩次未重現，待 Tom 複驗，見 poc-results.md「實作前驗證」。
- [ ] **P2（Tom 本機）：D9 的 `$.ui.status`、`$.ui.toast` 在 Warp。** 載入 attention-mod 與探針，窄視窗先 `/attention`，再 `/poc-status 測試` 與 `/poc-toast`；記下 status 是否在輸入框下方、toast 是否可見、位置。Cloud 已在 Linux 驗證可見。
- [ ] **P3（Tom 本機，一行指令）：** `ls -l ~/.claude/plugins/store/`。記下目錄與檔案權限。
- [ ] **P4（Tom 本機）：D13 的 T2 流程。** `/poc-t2` 後 `/clear`，依序測：方向鍵加 Enter、Esc、直接 Enter、對話框開著時打字再 Enter。記下選到什麼、是否送出文字（Tom 的 `$.ui.ask` 不能單獨按數字，Cloud 沒有比對）。
- [x] **P5（Cloud，可選）：** `/cd <目錄>` 後的 `session.root()`。`/cd` 不存在就記下「這個版本沒有」並略過；不阻擋後面任務。 **Cloud 結果：** `/cd` 到專案內子目錄成功且 `root()` 跟著移動，到專案外被拒絕；git repo 內不受影響（D10）。
- [ ] **記錄：** 把結果追加到 `docs/poc-results.md` 的新小節「實作前驗證」，Cloud 與 Tom 分開。

**決策表：**

| 結果 | 後面的處理 |
| --- | --- |
| P1 路線 A | Task 13 切片 f 在 `session.end` 內讀訊息 |
| P1 路線 B | Task 13 切片 f 改在 `prompt.submit`、`turn.complete` 記最後一組，存 `$.store`（先遮蔽再存，設計元件 8 的備案措施），`session.end` 只寫檔 |
| P1 路線 C | D4 不做；Task 10 與 Task 13 切片 f 移除，回報 Tom |
| P2 看不到 status 或 toast | D9 降級改為只靠指令與 `$.ui.log`，回報 Tom 重新決定 |
| P3 不是 `0600`／`0700` | 回報 Tom；D4 備案的 store 副本需另議，或只用路線 A |
| P4 與 Cloud 不同 | 回報 Tom，D13 的措辭與選項順序重新確認 |
| P5 `root()` 會跟著 `/cd` 變 | 非 git 目錄的範圍鍵照設計用 `session.root()`；不變則在文件註明限制 |

**Gate（2026-10-07 Tom 同意放寬）：** P1 有結果（已完成，路線 B）即可進 Task 1。P3 只擋 Task 13 切片 f（路線 B 的 `$.store` 副本），P2 只擋切片 b 的窄視窗降級細節，P4 只擋切片 c 的措辭與選項；Task 1 至 12 不等它們。P3、P2、P4 的結果出來後照上面的決策表處理，若推翻設計就回報 Tom。

---

## Phase 1：骨架與純函式（Cloud）

**狀態（2026-10-07，Cloud）：Task 1 至 11 已完成，未 commit。** `claude plugin validate --strict .` 通過；`claude plugin test .` 為 **88 pass、0 fail**（10 個測試檔）。每個模組先寫失敗測試（RED：10 個檔案都因模組不存在而載入失敗）再實作。另做變異檢查：故意弄壞四組實作（先截斷再遮蔽、放寬 branch 驗證、拿掉 7 天與 3 筆上限、拿掉已問過與 TTL 判斷），各有 1 至 3 個對應測試失敗，還原後恢復全過。結果見 `docs/implementation-results.md`。

**實作中與計畫不同或補充的決定：**

1. `hooks/register.js` 不能寫 `void on;`：驗證器規定 `on` 只能用在 `on("<event>", hook)` 的呼叫。空骨架寫成不使用參數的 `register(on, options) {}`。
2. 結束筆記把引用的最後一個要求與最後一段回應**逐行加 `> ` 引用**：Claude 的回應常含 Markdown 標題，沒有引用的話，其中的 `## 下一步` 會被解析器當成筆記自己的章節。
3. 祕密遮蔽的「名稱加值」規則用前綴字元類而不是 `\b`，因為 `GITHUB_TOKEN` 的底線不是字邊界。
4. `rankHandoffs` 多回傳 `hidden`（超過 7 天的自動筆記數）；`i18n` 多出 `clearOptions(lang)` 與結束筆記、清單、新鮮度用的字串；`initialState()` 含 `handoffStartedAt`，與 `PluginState` 一致。
5. `parseHandoff` 把 `status: resumed` 當成無效（`ok:false`），因為清單只列未完成的；`resumed` 由 `$.store` 的覆寫值表達，不寫回檔案。

### Task 1：plugin 骨架

**Files:** 建立 `.claude-plugin/plugin.json`、`hooks/hooks.json`、`types/index.d.ts`、`package.json`、`tsconfig.json`、`.gitignore`。`hooks/register.js` 先放只註冊空 `register` 的版本。

- [x] **Step 1：** `plugin.json`：`name` 為 `handoff-mod`（D6）、`version` `0.1.0`、`types` 指向 `./types/index.d.ts`、`userConfig` 三欄（Cloud 已驗證的宣告）：

```json
"userConfig": {
  "thresholdPct": { "type": "number", "title": "Handoff threshold (% used)", "description": "Ask about a handoff when the context window is this full.", "default": 60, "min": 1, "max": 99 },
  "lang": { "type": "string", "title": "UI language", "description": "Language of the prompts and of new handoff files.", "options": ["zh-TW", "en"], "default": "zh-TW" },
  "autoNote": { "type": "boolean", "title": "End-of-session note", "description": "Write a facts-only note when a session ends.", "default": true }
}
```

- [x] **Step 2：** `types/index.d.ts` 宣告 `PluginState['handoff-mod']`：`nextAt: number`（0 表示用設定值）、`askedAt: number`、`suppressed: boolean`、`askPending: boolean`、`handoffStartedAt: number`（0 表示沒有）、`lastRequest`／`lastResponse` 不放這裡（見 Task 13 切片 f 路線 B，放 `$.store`）。
- [x] **Step 3：** `claude plugin validate --strict .` → 通過；`state` 欄位尚未被 `register.js` 讀寫，不應報錯。
- [x] **Step 4：** `.gitignore` 含 `.claude-plugin/types/`（本機型別，與 attention-mod 相同）。

### Task 2：設定解析（`hooks/config.js`、`tests/config.test.ts`）

`resolveConfig({env, userConfig})` → `{thresholdPct, lang, autoNote}`。`env` 是呼叫端用 `$.env.get` 讀到的三個字串（`HANDOFF_THRESHOLD_PCT`、`HANDOFF_LANG`、`HANDOFF_AUTO_NOTE`，可為 `undefined`）。

- [x] **Step 1：失敗測試：**
  - 優先順序：環境變數 > `userConfig` > 預設（`60`、`zh-TW`、`true`）。
  - `HANDOFF_THRESHOLD_PCT=10` → `10`；`0`、`100`、`abc`、`5.5` 無效，退回 `userConfig`／預設。
  - `HANDOFF_LANG` 只接受 `zh-TW`、`en`，其餘退回。
  - `HANDOFF_AUTO_NOTE=off`（不分大小寫）→ `false`；`on` → `true`；其他退回 `userConfig`，再退回 `true`。
  - `userConfig` 缺欄位或型別不對時用預設，不丟例外。
- [x] **Step 2：** `claude plugin test .` → 新測試失敗。
- [x] **Step 3：實作**（純函式，不碰 `$`）：

```js
const DEFAULTS = {thresholdPct:60, lang:'zh-TW', autoNote:true};
const LANGS = ['zh-TW', 'en'];
const asPct = (v) => { const n = typeof v === 'string' && /^\d+$/.test(v.trim()) ? Number(v) : v; return Number.isInteger(n) && n >= 1 && n <= 99 ? n : undefined; };

/** Resolve settings: test-only env overrides win, then userConfig, then defaults. */
export function resolveConfig({env = {}, userConfig = {}} = {}) {
  const lang = LANGS.includes(env.HANDOFF_LANG) ? env.HANDOFF_LANG : LANGS.includes(userConfig.lang) ? userConfig.lang : DEFAULTS.lang;
  const flag = String(env.HANDOFF_AUTO_NOTE ?? '').toLowerCase();
  const autoNote = flag === 'off' ? false : flag === 'on' ? true : typeof userConfig.autoNote === 'boolean' ? userConfig.autoNote : DEFAULTS.autoNote;
  return {thresholdPct: asPct(env.HANDOFF_THRESHOLD_PCT) ?? asPct(userConfig.thresholdPct) ?? DEFAULTS.thresholdPct, lang, autoNote};
}
```

- [x] **Step 4：** `claude plugin test .` 全過；`node --check hooks/config.js`。

### Task 3：字串（`hooks/i18n.js`、`tests/i18n.test.ts`）

`t(lang, key, vars)`，字串集中在一個檔（D8）。繁中與英文的 key 集合必須相同。

- [x] **Step 1：失敗測試：** 兩種語言 key 集合相同；每個字串的 `{var}` 佔位符在兩種語言一致；`t` 找不到語言退回 `zh-TW`、找不到 key 丟錯（開發期就發現）；替換後沒有殘留 `{…}`；band 按鈕文字在單行 67 欄內放得下（以兩種語言中較長者量，按 Unicode 顯示寬度，CJK 算 2）。
- [x] **Step 2：** 實作並 `claude plugin test .`。字串範圍：T1 band 三個按鈕與說明、窄視窗 status 一行、T2 的問題與三個選項（順序：取消／先交接再清除／直接清除，D13）與 `{text}` 說明、清單各欄標籤、「自動留下，未經審查」、`/handoff-resume` 輸出、toast 與錯誤訊息。**`$.ui.status` 與 `$.ui.log` 的文案要短、不用嚇人的字。**

### Task 4：淨化與遮蔽（`hooks/sanitize.js`、`tests/sanitize.test.ts`）

三個函式：`stripControl(text)`（去控制字元與 ANSI／OSC，保留換行與 tab）、`truncateCodePoints(text, max)`（以 Unicode code point 計，超過加 `…`）、`redactSecrets(text)`；以及組合 `cleanForNote(text, max)`，**順序固定：去控制字元 → 遮蔽 → 截斷**（先遮蔽再截斷，避免秘密被截成一半留下殘片）。

- [x] **Step 1：失敗測試。** 遮蔽規則逐條列出並測正反例（規則寫在檔案頂端註解，測試與它一一對應）：`Authorization:` 的 `Bearer`／`Basic`；`password`／`passwd`／`secret`／`token`／`api_key` 加 `=` 或 `:` 後的值；`AKIA` 開頭的 AWS key；`ghp_`／`gho_`／`github_pat_` 開頭的 GitHub token；`sk-` 開頭的長字串；`xox[baprs]-` 的 Slack token；PEM 私鑰區塊；JWT 三段式；URL 內的 `user:pass@`。
  - 正例：每條規則至少一個，被取代為 `[redacted]`。
  - 反例：「token count」「password policy」之類沒有 `=`／`:` 加值的字樣不變。
  - 邊界：一個秘密剛好跨過 2000 字截斷點，輸出裡不含它的任何一段。
  - 文件寫明：**這是降低風險，不是保證**，仍可能漏掉；測試不得宣稱能擋所有秘密。
  - `stripControl`：CSI（`\x1b[31m`）、OSC（`\x1b]0;…\x07`）、`\x00`、`\x7f` 都被去除；中文、emoji、換行保留。
  - `truncateCodePoints`：emoji 不被切半（以 code point 計）。
- [x] **Step 2：** 實作並 `claude plugin test .`。

### Task 5：解析交接檔（`hooks/handoff-file.js`、`tests/handoff-file.test.ts`）

`parseHandoff(text)` → `{ok:true, meta, fields}` 或 `{ok:false, reason}`。只讀前 64 KiB。

- [x] **Step 1：失敗測試：**
  - 完整中文檔：取得 `status`、`created`（轉成毫秒）、`branch`、`head`、`root`、`repo`、`task`、`source`。
  - **章節標題中英都認**（D11）：`## 任務／Task`、`## 已完成／Done`、`## 未完成／Remaining`、`## 下一步／Next`、`## 前提（人工確認）／Premises`、`## 規矩（不能違反）／Rules`、`## 已驗證／未驗證（AI 自述）／Verified`。
  - 缺 `status` 或 `created`、`status` 不是 `in-progress`／`blocked`／`ready-for-review`、`created` 無法解析 → `ok:false`。
  - 不認得的欄位忽略；`worktree` 視為 `root` 的別名；`assertions`（巢狀清單）不讓解析壞掉。**以 Tom 現有 `handoff` skill 實際產出的 frontmatter 當夾具之一**（含 `assertions: - kind: …`）。
  - 顯示欄位淨化：`task` ≤80 字、「下一步」第一行 ≤120 字，去除項目符號、控制字元與 ANSI（呼叫 `sanitize.js`）。
  - CRLF、缺章節、空檔、只有 frontmatter 都不丟例外。
  - **來自檔案的 `branch`／`head` 不做任何執行**；解析只回傳字串，驗證留給 Task 7。
- [x] **Step 2：** 實作並 `claude plugin test .`。

### Task 6：排序與折疊（`hooks/rank.js`、`tests/rank.test.ts`）

`rankHandoffs(items, {base, repo, now})`，`item = {path, meta, effectiveStatus, claimedByOther}`，回傳 `{shown, collapsed, hidden}`。

- [x] **Step 1：失敗測試：**
  - 只列有效狀態為 `in-progress`／`blocked`／`ready-for-review` 的；`resumed`、`done`、`abandoned` 不列。
  - 排序：同 `base` 優先，其次同 `repo`，其餘依 `created` 由新到舊。
  - 預設展開 3 筆，其餘折疊成「還有 N 筆」。
  - `created` 超過 14 天的預設折疊。
  - `source: auto` 且超過 7 天的**不顯示也不計入折疊數**（D4 緩解措施 4）。
  - `claimedByOther` 的保留在清單、帶旗標。
  - 同時間排序穩定，輸入順序不影響結果。
- [x] **Step 2：** 實作並 `claude plugin test .`。

### Task 7：新鮮度（`hooks/freshness.js`、`tests/freshness.test.ts`）

`freshnessFacts({meta, git})`，`git(args)` 是注入函式，回傳 `{exitCode, stdout}`；回傳事實陣列（key 加變數，由 `i18n` 轉成文字），**是事實不是結論**。

- [x] **Step 1：失敗測試：** 用假 `git` 驗證：branch 不存在 → 一筆事實；交接後多 N 個 commit → 帶 N；HEAD 已包含在預設分支 → 一筆事實；任何一個 git 指令失敗（`exitCode !== 0` 或丟例外）只省略該行，不影響其他；`repo` 為空或沒有 `head`／`branch` → 回傳「無法驗證」；**驗證不通過的 `branch`／`head`（含空白、開頭 `-`、`..`、`;`、換行、`--upload-pack=…`）完全不傳給 `git`**，且斷言假 `git` 沒被呼叫；傳給 `git` 的參數一律放在 `--` 之後。
- [x] **Step 2：** 實作（branch 允許 `[A-Za-z0-9._/-]`、不得以 `-` 或 `/` 開頭、不得含 `..`；head 允許 `[0-9a-f]{4,40}`）並 `claude plugin test .`。

### Task 8：T1 門檻判斷（`hooks/trigger.js`、`tests/trigger.test.ts`）

純函式，不碰 `$`。狀態欄位對應 `PluginState`（Task 1）。

```js
/** The threshold in force: a snoozed value if there is one, else the configured one. */
export const effectiveThreshold = (state, config) => (state.nextAt > 0 ? state.nextAt : config.thresholdPct);

/** Ask only when every condition holds; anything unknown means "do not ask". */
export function decideTrigger({percent, config, state, idle, hasUnfinishedSign, handoffRunning}) {
  const at = effectiveThreshold(state, config);
  if (typeof percent !== 'number' || state.suppressed || state.askPending || handoffRunning) return {action:'none', at};
  if (!idle || !hasUnfinishedSign || percent < at || state.askedAt >= at) return {action:'none', at};
  return {action:'ask', at};
}
```

- [x] **Step 1：失敗測試（表格式，每列一個案例）：** `percent` 缺值（壓縮後到下一個回應之前）不問；低於門檻不問；剛好等於門檻會問；沒有未完成跡象不問；非閒置（回合進行中、有等待）不問；`suppressed` 不問；同一個門檻問過（`askedAt >= at`）不再問；handoff 進行中不問。
- [x] **Step 2：狀態轉換測試：** `afterAsk(state, at)` 設 `askedAt`；`snooze(state, {percent, at})` 把下一個門檻設為 `min(99, max(percent, at) + 10)`（設計元件 2 的「再多 10% 再問」）；`suppress(state)`；`resetThreshold(state)` 清 `nextAt` 與 `askedAt`（用於 `session.compact`、`/clear`）；`onPercentSeen(state, percent)`：`percent < state.askedAt` 時自動重置（壓縮後 % 會掉，本機量到 9% → 5%）。
- [x] **Step 3：** 實作並 `claude plugin test .`。`hasUnfinishedSign({editedFile, gitDirty})` 同檔：任一為真即真。

### Task 9：認領（`hooks/claim.js`、`tests/claim.test.ts`）

`tryClaim({id, sessionId, now, store})`，`store` 是注入的 `{get, set}`；`claimView(entry, sessionId, now)` 給清單用。

- [x] **Step 1：失敗測試：** 沒有認領 → 寫入後讀回是自己 → 贏；已有他人且未過期 → 輸，不覆寫；已有他人但超過 12 小時 → 覆寫並贏；**競爭：** 假 store 在 `set` 與讀回之間被另一個 session 覆寫 → 讀回不是自己 → 輸；同一個 session 重複認領 → 贏（冪等）；store 丟例外 → 回傳 `{won:true, degraded:true}`（設計：store 失敗時不認領、仍可接續）。
- [x] **Step 2：** 實作並 `claude plugin test .`。

### Task 10：結束筆記（`hooks/note.js`、`tests/note.test.ts`）

`shouldWriteNote({interactive, turns, hasUnfinishedSign, reason, config})`；`buildEndNote({lastRequest, lastResponse, branch, head, dirtyFiles, root, repo, now, lang})` → `{fileName, content}`。（若 Task 0 的 P1 為路線 C，本任務與 Task 13 切片 f 一起移除。）

- [x] **Step 1：失敗測試：**
  - 寫入條件：互動、`turns > 0`、有未完成跡象、`reason !== 'clear'`、`config.autoNote` 為真；任一不成立不寫。
  - 內容：frontmatter 含 `schema: 1`、`status: in-progress`、`source: auto`、`task`（最後一個要求，截斷）；本文只有「最後一個要求」「最後一段回應」「branch／HEAD」「有改動的檔案」；**不含工具輸出、不含更早的對話**。
  - 兩段原文各截斷到 2000 字，走 `cleanForNote`；含祕密的輸入被遮蔽；含 ANSI 的被去除。
  - 檔名 `<branch 淨化>--<YYYYMMDD-HHMMSS>--auto.md`；沒有 git 時 branch 用 `no-branch`；branch 中的 `/` 與非 `[A-Za-z0-9._-]` 字元換成 `-`。
  - 兩種語言的章節標題都能被 Task 5 的解析器讀回（往返測試）。
  - `withDeadline(fn, ms)`：逾時回傳 `{timedOut:true}`，不留半個結果。
- [x] **Step 2：** 實作並 `claude plugin test .`。

### Task 11：`.git/info/exclude`（`hooks/exclude.js`、`tests/exclude.test.ts`）

`ensureExcluded({git, fs, pattern})`，`git` 與 `fs` 是注入函式。

- [x] **Step 1：失敗測試：** 路徑用 `git rev-parse --git-path info/exclude` 取得（worktree 也正確）；已被忽略（`git check-ignore -q` 為 0）就不動；檔案不存在就建立；檔案已含該行不重複寫（冪等）；結尾沒有換行時先補換行；任何一步失敗回傳 `{ok:false}` 不丟例外；非 git 目錄直接略過。
- [x] **Step 2：** 實作並 `claude plugin test .`。

---

## Phase 2：skill 與接線

**狀態（2026-10-07，Cloud）：Task 12 與 Task 13 的切片 a、c、d、e 完成。**（切片 a、d、e 與 skill 已 commit 為 `c87d6db`；切片 c 尚未 commit。）切片 b、f、g 未做。`claude plugin validate --strict .` 通過（呼叫清單沒有 `$.model`、`$.prompt.submit`、`$.command.run`）；`claude plugin test .` 為 **109 pass、0 fail**（含 `tests/register.test.ts` 的接線測試，用測試 kit 驅動事件並 stub 檔案系統、git、store）。另在 Cloud 的真實互動 session 驗證（見 `docs/implementation-results.md`）。

**實作中與計畫不同或補充的決定（待 Tom 確認）：**

1. **驗證新檔要跨多個回合。** 計畫寫「交接回合之後的 `turn.complete`」，但審閱關卡讓一次交接至少有兩個回合（草稿、確認），第一個回合結束時一定還沒有檔案。實作改成：只要有交接進行中，每個 `turn.complete` 都檢查，找到有效新檔就報告；**第 4 個回合仍沒有檔案才提示一次**「未偵測到有效交接檔」，之後繼續檢查，找到仍會報告；10 個回合或 60 分鐘後放棄。
2. **偵測交接開始：三個訊號任一個即可**（`skill.prompt`、`prompt.submit` 文字以 `/handoff-mod:handoff` 開頭、`command.run` 的 `handoff-mod:handoff`；`markHandoffStarted` 保證只啟動一次）。**原本只用 `skill.prompt`，在 Tom 的 macOS 環境輸入指令時它不會觸發（見 `docs/implementation-results.md` 的 L1），已修正；Tom 環境的修正結果待驗證。**
3. **skill 的語言要能處理「沒替換」：** `${user_config.lang}` 在使用者沒有儲存這個設定時**不會被替換**（skill 看到字面的 `${user_config.lang}`，預設值不會代入），存進設定後才會替換。skill 因此加一句：值不是 `zh-TW` 或 `en` 就用 `zh-TW`。測試用的 `HANDOFF_LANG` 環境變數**不會**傳給 skill。
4. 啟動讀回的窄視窗降級還沒有偵測 attention-mod（P2 未做）：目前**一律同時**畫 band 並設 `$.ui.status` 一行，如計畫切片 b 所寫的保守做法。
5. `/handoff-resume` 只列排序後的前 3 筆，折疊的筆數只能在 band 看到「還有 N 筆」，沒有指令可以展開。
6. 啟動清單的按鈕沒有數字 hotkey（避免使用者開頭輸入數字時被誤觸發）。
7. **切片 c（T2）：** 只攔截使用者自己的 `/clear`（`origin.kind` 不是 `plugin`）、互動 session、`turns() > 0`；另一個外掛程式或 headless 的 `/clear` 直接放行。問題被關掉、Esc、輸入其他文字、預設的 Enter（第一項是「取消」）一律取消，只有完全相符的「直接清除」才放行（D13）。已有一個提問在等時，第二個 `/clear` 直接取消、不再問第二次。問題開著時 session 換了，什麼都不做（回 `{}`）。**如果提問本身失敗，就照使用者的意思放行 `/clear`**，不吞掉它。驗證器會警告這是「會擋指令的 hook 沒有 `.catch`」，這是刻意的：hook 本身出錯或逾時時，引擎會略過它、`/clear` 照常執行（fail-open），不讓使用者被卡住。
8. 交接剛寫完後下一個 `/clear` 仍會再問一次（D3 一律詢問）。

### Task 12：內建 skill（`skills/handoff/SKILL.md`）

- [x] **Step 1：** 寫 skill（指令名為 `handoff-mod:handoff`）。內容須包含：唯讀收集（`git branch --show-current`、`git status --short --branch`、近期 commit、當前對話）；**草擬後完整顯示並等使用者確認，未經確認不寫檔**；寫入路徑由 skill **明確指定**：git repo 內用 `git rev-parse --show-toplevel` 加 `.claude/handoffs/`，不在 git 內用目前目錄（D10），檔名 `<branch 淨化>--<YYYYMMDD-HHMMSS>.md`；frontmatter 照設計 schema 1；「已驗證」只能列**這個回合實際跑過的指令或讀過的檔案**並寫出是哪個指令（L2：Tom 的 `handoff` 曾把沒跑過的「看過 diff」標成已驗證）；不寫金鑰、token、客戶資料；標明「已驗證／未驗證」是 AI 自述；章節標題語言依 `${user_config.lang}`（manifest 文件寫明非敏感的 `userConfig` 值會在 skill 內容中替換，**這一點沒有實測**，Step 3 要驗證；替換不成立就改成讓 skill 同時產出兩種標題之一並由使用者指定，回報 Tom）。
- [x] **Step 2：** `claude plugin validate --strict .`。
- [x] **Step 3（Cloud 與 Tom）：** 先確認 `${user_config.lang}` 在 skill 內容中確實被替換（兩種語言各看一次展開後的內容）。再在拋棄式 git repo 與非 git 目錄各跑一次 `/handoff-mod:handoff`，檢查寫出的路徑、frontmatter 能被 Task 5 的解析器讀回、「已驗證」沒有捏造。Tom 的 `handoff` 不受影響（`handoff-mod:handoff` 是不同的指令名）。

### Task 13：`register.js` 接線（分切片，每片結束都驗證）

每一片：寫接線 → `node --check` → `claude plugin validate --strict .` → 在互動 session 驗證（Cloud 用 pty，結果標「Cloud」；最終驗收在 Task 14）。**所有 hook 本體都包 `try/catch`。**

- [x] **切片 a：註冊與設定。** `session.start` 註冊 `/handoff-resume`；讀三個環境變數（字面名稱）與 `register(on, options)` 的 `userConfig`，餵給 `resolveConfig`；`$.state` atoms 依 Task 1 的型別。初始化要可重複執行。驗證：改任何一個設定後（`$.config.set`），`$.state` 的值保留、`session.start` 再觸發而不出錯。
- [ ] **切片 b：T1 提示。** 收 `turn.complete`、`session.measure`；呼叫 `onPercentSeen`、`decideTrigger`。要問時：寬視窗畫 band（三個按鈕，數字 hotkey 1／2／3，文字來自 `i18n`）；窄視窗且有 attention-mod 時用 `$.ui.status` 常駐一行加指令（D9）；選項 1 開始交接（`$.clock.after` 內呼叫 `$.command.run({command:'handoff-mod:handoff'})`，設 `handoffStartedAt`）、2 呼叫 `snooze`、3 呼叫 `suppress`。band 的內容要與 `next(e)` 的結果並排（共存）。**偵測「窄視窗且有 attention-mod」的方法在 Task 0 之後定**（可能用 `$.command.list()` 看 attention-mod 的指令，或看 band 收到的 `viewport`）；定不出來就先一律同時用 band 與 status，並回報 Tom。
- [x] **切片 c：T2 `/clear` 攔截。** `command.run` 的 `clear` hook：互動 session 且 `turns() > 0` 才攔截（D3：不看未完成跡象）；`$.ui.ask` 選項順序依 D13：取消／先交接再清除／直接清除；`askPending` 旗標防疊加；選「直接清除」呼叫 `next(e)`；取消、Esc（reject）、其他任何回答都回 `{text}` 不執行；選「先交接」回 `{text}` 說明「已暫停清除，交接完成後請再下 `/clear`」並從計時器開始交接；`-p` 或非互動時不攔截；回答若在 session 重置之後才到就丟棄。驗證（Cloud pty）：四條路徑，與設計的 W8 一致。
- [x] **切片 d：驗證新檔。** 交接回合之後的 `turn.complete`：用 `$.fs.list` 找交接目錄中 mtime 晚於 `handoffStartedAt` 的新檔，經 `parseHandoff` 驗證；成功 → 呼叫 `ensureExcluded`、`$.ui.toast` 顯示路徑、累計寫入次數（D5，`$.store`）；失敗 → toast「未偵測到有效交接檔」，不標成功。交接目錄用 D10 的基準：git repo 內 `git rev-parse --show-toplevel`，否則 `$.session.root()`。
- [x] **切片 e：啟動讀回。** `classic.SessionStart`，`source` 為 `startup` 或 `clear`、互動、`turns() === 0`。來源：目前 worktree 的目錄；`repo().root` 不同時再加主 checkout；同 repo 其他 worktree 由 `git worktree list --porcelain` 取得（D2）；不另做索引。逐個 `parseHandoff` → 讀 `$.store` 取得有效狀態與認領 → `freshnessFacts` → `rankHandoffs`。介面：寬視窗 band（接續、略過）；窄視窗且有 attention-mod 用 `$.ui.status` 一行「有 N 筆未完成交接」加 `/handoff-resume`；**清單輸出用 `$.ui.log`**（D14）。「接續」→ `tryClaim`、`$.prompt.fill`（內容只有路徑與驗證前提的提示）、`$.store` 記 `resumed`、累計接續次數（D5）。`/handoff-resume <編號>` 同「接續」。啟動清單那行 status 在 `turns() > 0` 時移除；與 T1 的 status 不同時存在。`classic.SessionStart` 的 `source` 為 `clear` 時，**明確重置** module 內任何殘留與 T1 狀態（`resetThreshold`）。
- [ ] **切片 f：結束筆記（依 P1 路線）。** 路線 A：`session.end` 內讀訊息，`withDeadline` 在約 1.5 秒預算內完成。路線 B：`prompt.submit` 記最後一個要求、`turn.complete` 記最後一段回應，**先 `cleanForNote` 再存 `$.store`**（每 session 一組、key 含 session id、寫完筆記即刪、`/clear` 或新 session 時刪舊的、啟動時清掉超過 7 天的）；`session.end` 只組檔案並寫入。兩路線的寫檔相同：`$.fs.write` 之後 `$.process.run(['chmod', '600', path])`（`$.fs.write` 沒有權限參數）；寫之前呼叫 `ensureExcluded`；逾時就放棄、不留半個檔案；檔名 `…--auto.md`。`reason` 為 `clear` 不寫。
- [ ] **切片 g：使用計數（D5）。** `$.store` 只存本機計數（交接寫入次數、接續次數）；不外傳；加一個指令印出計數（用 `$.ui.log`）。

---

## Phase 3：驗收與收尾

### Task 14：驗收（Tom 本機，macOS／Warp）

依設計「驗證與測試」的實機劇本，**逐項記錄到 `docs/implementation-results.md`**（Cloud 與 Tom 分開）：

- [ ] T1：三個選項各走一次；再多 10% 的下一個門檻；`HANDOFF_THRESHOLD_PCT=10` 測試覆寫。
- [ ] T2：`/clear` 的四條路徑；純問答 session 也會被問（D3）。
- [ ] 啟動讀回：沒有交接檔（什麼都不畫）、有一筆、有多筆、同 repo 的 worktree、非 git 目錄、`/clear` 之後再讀。
- [ ] 兩個終端機同時接續同一份：只有一個贏。
- [ ] 交接回合沒寫出有效檔案：看到「未偵測到有效交接檔」。
- [ ] 結束筆記：`/exit`、Ctrl-C 兩次、關分頁各一次；內容、權限 `0600`、含祕密的輸入被遮蔽；`HANDOFF_AUTO_NOTE=off` 關閉；啟動讀回標「自動留下，未經審查」、超過 7 天不顯示。
- [ ] 改設定（`/config`）不破壞進行中的狀態。
- [ ] 與 attention-mod 同載入：寬、窄視窗。
- [ ] 同事環境（版本、managed settings、公司對 plugin 的政策）：**需要 Tom 向同事確認，不是這份計畫能代做的。**
- [ ] 交接檔內容準確度：用真實 session 人工抽查（不在自動測試範圍）。

### Task 15：文件與 marketplace

- [ ] **Step 1：** `README.md`（繁中與英文）：安裝、設定（`/config` 與測試用環境變數）、行為、風險（Mod 不在 sandbox、結束筆記含對話原文、遮蔽只降低風險）、移除。`.claude/CLAUDE.md`：架構、不變條件、指令，格式比照 attention-mod。`docs/implementation-results.md` 完成。
- [ ] **Step 2：** **經 Tom 同意後**才在 `.claude-plugin/marketplace.json` 加 `handoff-mod` 的條目，並把 `docs/superpowers/plans/2026-10-06-handoff-mod-poc.md` 的 Task 3 標完成。
- [ ] **Step 3：** `claude plugin validate --strict .`、`claude plugin test .` 全過；個人資訊掃描（`/Users/`、email、內部識別）沒有命中。

## 這份計畫沒有涵蓋

- 交接內容的品質（模型寫出來準不準）、成本實測、同事環境。
- T4（壓縮前攔截）與 `model.fork` 起草：設計列為日後。
- 跨機器同步、稽核用途的證據保證。
