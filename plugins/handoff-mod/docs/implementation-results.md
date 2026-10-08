# Handoff Mod 實作結果

實作計畫：[2026-10-07-handoff-mod.md](superpowers/plans/2026-10-07-handoff-mod.md)。**Cloud 與 Tom 環境分開記**，不把 Cloud 結果寫成 Tom 的環境已驗證。

## Phase 1：骨架與純函式（Cloud，2026-10-07）

環境：Linux container、Claude Code 2.1.292。

| 項目 | 結果 |
| --- | --- |
| `claude plugin validate --strict .` | 通過；`register.js` 目前沒有接線，`calls: nothing on $`。 |
| `claude plugin test .` | **88 pass、0 fail**，10 個測試檔：`config`、`i18n`、`sanitize`、`handoff-file`、`rank`、`freshness`、`trigger`、`claim`、`note`、`exclude`。 |
| RED | 寫完測試先跑：0 pass、10 個檔案都因 `../hooks/<模組>.js` 不存在而載入失敗；之後才實作。 |
| 變異檢查 | 先截斷再遮蔽 → 1 個測試失敗；放寬 branch 驗證 → 2 個；拿掉 7 天隱藏與 3 筆上限 → 3 個；拿掉已問過與認領 TTL 判斷 → 3 個。還原後 88 pass。 |

限制：

- 測試只覆蓋純函式。事件接線（Task 13）尚未做，沒有任何互動 session 的驗證。
- 祕密遮蔽只列舉 9 種形狀，**是降低風險，不是保證**；測試沒有宣稱能擋所有祕密。
- 測試裡的祕密形狀值都在執行時組合，檔案內沒有可被掃描器標記的字面值。
- 型別編譯（`tsc`）本機沒有，測試通過不代表型別編譯通過。

## Phase 2：skill 與接線切片 a、d、e（Cloud，2026-10-07）

環境：Linux container、Claude Code 2.1.292，pty 驅動真實互動 session（拋棄式 git repo，100／110 欄）。**不是 Tom 的 macOS／Warp。**

| 項目 | 結果 |
| --- | --- |
| 驗證與測試 | `claude plugin validate --strict .` 通過；`claude plugin test .` **109 pass、0 fail**（新增 `register.test.ts` 21 項、`world.ts` 夾具）。 |
| 變異檢查（接線） | 弄壞六處（所有 source 都列清單、忽略輸掉的認領、不呼叫 exclude、每回合都警告、不比對 mtime、斜線指令也結束清單）：一開始 5 個被抓到，**認領競爭那個沒被抓到**，補了一個「清單畫出後才輸掉認領」的測試後也被抓到。 |
| 啟動清單（真實 session） | 在放了一份交接檔的 repo 啟動：band 顯示「有 1 筆未完成交接」、標題（任務、branch、1 分鐘前）、下一步、「接續」「略過」；輸入框下方同時有 `⚠ handoff-mod: 有 1 筆未完成交接，輸入 /handoff-resume 查看`。 |
| `/handoff-resume` | 無參數：用 `$.ui.log` 列出；`/handoff-resume 1`：輸入框出現「請先讀 <路徑>，驗證其中前提是否仍成立，再接續「下一步」。」，store 寫入認領、`resumed` 狀態與計數。**`command.run` hook 內直接 `fill` 有效**（W6 的結論成立）；中途我曾誤判為被清掉，原因是驗證腳本結尾的 Ctrl-C 先清了輸入框，已更正。 |
| 內建 skill 的真實執行 | `/handoff-mod:handoff`：用 git 指令收集、顯示完整草稿並問「Is this right?」，確認後才寫檔；「已驗證」只列這個回合實際跑過的 5 個 git 指令並標明是 AI 自述；寫出的檔案 frontmatter 有效，能被解析器讀回。 |
| 寫入後的偵測（切片 d） | `skill.prompt` 偵測到開始；寫出檔案後出現 toast「交接已寫入 …」，`.git/info/exclude` 新增 `.claude/handoffs/`，`git status` 乾淨，store 計數 `written: 1`，沒有出現「未偵測到有效交接檔」。 |
| 語言 | `${user_config.lang}` **在值沒有儲存時不會被替換**（skill 看到字面 `${user_config.lang}`，第一次真實執行因此產出英文標題）；值存進設定後會替換（測試輸出 `en`）。skill 加了「值不是 `zh-TW` 或 `en` 就用 `zh-TW`」後，真實執行產出繁中標題。 |

限制與沒驗證的：

- **band 的按鈕在真實 session 沒有按過。** 用 Ctrl+X 再 Tab 嘗試把焦點移進 band，沒有生效；按鈕行為只由測試 kit 的 `press` 覆蓋（認領、狀態、清除）。
- 沒有與 attention-mod 同載入、也沒有窄視窗的實際外觀（P2 待 Tom）；沒有 `/clear` 後再讀取的真實驗證（只有測試）。
- `en` 語言的完整 skill 流程沒有跑真實模型（只驗證替換機制）。
- 交接內容的準確度只看了一份「幾乎空的 session」，不能代表真實工作的草稿品質。
- 型別編譯（`tsc`）本機沒有。

## Phase 2：切片 c，T2 `/clear` 攔截（Cloud，2026-10-07）

環境同上。

| 項目 | 結果 |
| --- | --- |
| 驗證與測試 | `claude plugin validate --strict .` 通過（會警告 `command.run{command=clear}` 是沒有 `.catch` 的 gating hook，刻意 fail-open，見計畫決定 7）；`claude plugin test .` **118 pass、0 fail**（新增 9 項）。 |
| 變異檢查 | 弄壞五處（沒有 `turns` 判斷、非精確答案也放行、旗標不釋放、在 hook 內啟動交接、session 換了仍放行）：一開始 4 個被抓到，**session 換了那個沒被抓到**，補測試後也被抓到。 |
| 對話框（真實 session） | `☐ Plugin`、問題「要先交接再清除嗎？」，選項 `1. 取消`、`2. 先交接再清除`、`3. 直接清除`，加上引擎自動附的 `4. Type something.` 與 `5. Chat about this`；**預設標在「取消」**（D13）。 |
| 四條路徑（真實 session） | Esc → 取消，顯示「已取消清除。」；預設 Enter → 同樣取消；↓ 加 Enter（先交接再清除）→ 顯示「已暫停清除，交接完成後請再下 /clear。」，約 300 ms 後**由計時器啟動交接 skill，真的出現草稿並問「這樣對嗎」**；↓↓ 加 Enter（直接清除）→ 對話被清掉。草稿沒有確認，所以沒有寫出交接檔，與預期一致。 |

限制：

- 對話框的數字鍵在你的環境不能單獨選（L4／P4），這次用方向鍵；P4 的本機結果仍待你。
- 「對話框開著時打字再 Enter」在真實 session 沒有再測；Cloud 先前（W8）的結果是文字不會送出、Enter 選預設項。
- 沒有測 `/clear` 之後的啟動讀回（只有測試）。

## Task 14（部分）：Tom 本機實測（macOS、Claude Code 2.1.292、模型 `claude-sonnet-5-5`，2026-10-07）

環境：Tom 的 macOS，拋棄式 git repo（分支 `feat/demo`），`claude --plugin-dir`。結果是 Tom 回報加截圖，**我沒有親眼驗證**；這批對應切片 a、c、d、e（還沒有 T1 與結束筆記）。

| 項目 | 結果 | 狀態 |
| --- | --- | --- |
| L1 手動交接 | 第一次：交接檔有寫出，但 **toast 沒有出現**（原因是偵測沒啟動，見下）。**修正後重跑（`541ba97`，`HANDOFF_DEBUG=1`）：第 1 回合掃描 `exists=false`、`nothing valid yet`；第 2 回合 `valid=true`、`found …`，右上角出現 toast「Handoff written to …」（截圖）。** | 通過（修正後）；`stats.written` 與哪個啟動訊號有效沒有確認 |
| L2 啟動讀回 | band 列出 2 筆未完成交接（任務、分支、幾分鐘前、下一步、「接續」「略過」），輸入框下方有 `⚠ handoff-mod: 有 2 筆未完成交接，輸入 /handoff-resume 查看`。 | 通過 |
| L3 `/handoff-resume` | 接續後輸入框被填入「請先讀 `<路徑>/.claude/handoffs/…md`，驗證其中前提是否仍成立，再接續「下一步」。」，沒有自動送出。 | 通過 |
| L4 band 按鈕 | **Tab 與滑鼠點擊都能按。** 這是 Cloud 做不到的項目。 | 通過 |
| L5 `/clear` | Tom 回報「沒問題」，沒有逐一記錄四條路徑與數字鍵的結果。 | 通過（細節未記錄） |
| L6 / P3 store 權限 | `~/.claude/plugins/store/handoff-mod_inline-<hash>.json` 為 `-rw-------`（0600）。同目錄的內建 plugin 檔有 `-rw-r--r--` 也有 `-rw-------`。**目錄 `~/.claude/plugins/store` 是 `drwxr-xr-x@`（0755）**，與 Cloud 的 0700 不同；同機器的其他使用者能列出檔名，但讀不到 0600 檔案的內容。目錄由 Claude Code 建立，不是本 plugin 控制。 | 通過（檔案 0600）；目錄 0755 是**與 Cloud 不同的事實**，已記錄 |
| L7 / P2 與 attention-mod 同載入 | 窄視窗、attention-mod 在輸入框上方的 inline 面板：**band 被面板遮住，看不到**；`$.ui.status` 那一行在輸入框下方**看得到**。寬視窗（面板在右側）：band 與 status **都看得到**。 | 通過（D9 的假設成立） |
| L8 語言 | `HANDOFF_LANG=en`：band 變成 `1 unfinished handoff(s)`、`Next:`、`Resume`、`Skip`，status 變成 `1 unfinished handoff(s). Run /handoff-resume to see them`；檔案內容仍是原本寫的中文，符合預期。 | 通過（介面）；skill 在 `en` 的流程 Tom 沒回報 |

### L1：toast 沒出現（未解）

可能原因：

| 假設 | 依據 | 怎麼分辨 |
| --- | --- | --- |
| H1：toast 有呼叫，但沒看到 | 型別文件寫 toast 預設只停 **4 秒**，畫在 transcript 的**右上角**（滾動模式下才是通知列一行）；又因為 `$.ui.toast` 前面還有 `ensureExcluded` 與寫 store，toast 出現在模型回答的最後一刻 | store 的 `stats.written` ≥ 1，且 `.git/info/exclude` 有 `.claude/handoffs/` |
| H2：`checkHandoff` 沒走到 toast | `checkHandoff` 被 `try { … } catch { /* ignore */ }` 包住（`register.js` 的 `turn.complete`），例外會被吞；`ensureExcluded` 或 `$.fs.stat` 在 macOS 失敗都會讓 toast 不出現 | 同上；`stats.written` 不存在或為 0 |

**第一次診斷無效（2026-10-07）：** Tom 在沒有交接資料的位置跑了診斷（`git status` 只有 `?? hello.txt`，store 沒有 `handoff-mod_inline-*.json`，該檔已在清理步驟刪掉），所以 H1／H2 仍分不出來。另外，`ensureExcluded` 的第一步是 `git check-ignore`：Tom 的**全域 gitignore 已有 `**/.claude/handoffs/`**（`git check-ignore -v` 實測，第 7 行），它會直接回傳「不需要改」，`.git/info/exclude` 維持預設是**正常行為**，不是 bug；因此在 Tom 的機器上看不到排除功能的效果，也不能拿 exclude 當 H2 的證據，要看 `stats.written`。要在他的機器驗證排除，需用 `git -c core.excludesFile=/dev/null check-ignore -v .claude/handoffs/x`（略過全域設定）。

**第二次診斷（2026-10-07）：** `check-ignore` 命中全域規則（exit 0）；`~/.claude/plugins/store/handoff-mod_*.json` **完全不存在**。若 Tom 這次確實在新 repo 跑完了交接，代表 `bumpStat` 沒被執行，偵測沒走到「找到檔案」；但**尚未確認他這次是否真的跑了交接、輸入的是 `/handoff-mod:handoff` 還是自己的 `/handoff`**（後者不會觸發本 mod 的偵測），結論未定。

**Tom 的回覆（2026-10-07）：跑了完整流程，且輸入的是 `/handoff-mod:handoff`。** 所以 L1 是真的：寫入後偵測在 Tom 的環境沒走到「找到檔案」。啟動清單與偵測讀的是同一個目錄、同一個解析器，唯一差別是偵測多呼叫 `$.fs.stat` 並比對 `mtimeMs`；讀程式看不出失敗點（Cloud 的真實 session 同一段是通過的）。下一步是加 `HANDOFF_DEBUG=1` 追蹤（`[handoff-mod debug]` 行，經 `$.ui.log`，Claude 讀不到），讓 Tom 重跑一次看停在哪一步：`skill.prompt` 有沒有觸發與技能名稱、`turn.complete` 有沒有進來、掃描的目錄與每個檔案的 `mtimeMs`／解析結果。

**追蹤結果（Tom 重跑，2026-10-08）：L1 的原因找到了。** 輸入 `/handoff-mod:handoff` 後，只有 `turn.complete` 的追蹤行，**沒有 `skill.prompt` 行，也沒有 `handoff run started`**，所以偵測從未啟動，`checkHandoff` 每回合都在 `since <= 0` 直接返回，不會掃描、不會 toast、不會寫 store。結論：**在 Tom 的環境，輸入 plugin skill 不會觸發 `skill.prompt`**（Cloud 會）。這與本檔 poc-results L2 的紀錄（user skill 經 `$.command.run` 不觸發）和設計文件的「偵測 handoff 是否被啟動要看 `prompt.submit`，不能靠 `skill.prompt`」一致；實作計畫決定 2 卻改成 `skill.prompt`，只憑 Cloud 通過就採用，**是我的疏漏**。

修正（Cloud 驗證，**尚未在 Tom 環境驗證**）：偵測改由三個訊號啟動，`markHandoffStarted` 保證只啟動一次：`skill.prompt`、`prompt.submit` 的文字以 `/handoff-mod:handoff` 開頭、`command.run` 的 `handoff-mod:handoff`。`claude plugin test .` 124 pass；變異檢查（拿掉 `prompt.submit` 或 `command.run` 其一）各被一個新測試抓到。三個訊號在 Tom 環境各自會不會來，仍要用 `HANDOFF_DEBUG=1` 看追蹤行確認。

**修正後重跑（Tom，2026-10-08，截圖）：** 啟動偵測成立，掃描目錄存在、檔案 `valid=true`、`found`，toast 出現在右上角（含完整路徑，被截斷）。**沒有確認的：** 三個啟動訊號（`skill.prompt`、`prompt.submit`、`command.run`）哪個在 Tom 環境有效（截圖只拍到第 1 回合之後，啟動那幾行沒入鏡）；`stats.written` 沒有查；`.git/info/exclude` 的寫入因 Tom 的全域 gitignore 而無法在他的機器看到（要用 `GIT_CONFIG_GLOBAL=/dev/null` 啟動才能驗證）。畫面是英文是因為 Tom 先前在 `/config` 把 `lang` 存成了 `en`。

macOS 特有的疑點：`/var` 是 `/private/var` 的符號連結，畫面上同時出現這兩種寫法；`findNewHandoff` 用 `git rev-parse --show-toplevel` 的結果拼路徑，啟動清單用同一個基準且有找到檔案，所以路徑本身應該沒問題，但**沒有驗證**。

### 對決策的影響

- **P2**：D9 成立。窄視窗時 band 不可靠，`$.ui.status` 是唯一保證看得到的訊號，所以 T1（門檻提示）在窄視窗必須以 status 為主。
- **L4**：band 的按鈕在 Tom 的環境可用（Tab、點擊），T1 的 band 按鈕做法可行。
- **P3**：檔案 0600、目錄 0755。內容不會被其他使用者讀到，但**檔名與存在**可見；結束筆記（切片 f）要不要做，改成需要 Tom 決定的取捨（見回覆），不再是「等驗證」。
- **toast 不應當作唯一的成功訊號**：不論 H1 或 H2，4 秒的右上角提示都太容易錯過。

限制：

- 以上是 Tom 的回報與截圖；沒有 log，沒有逐項重現。
- Warp 是 Tom 的終端機（依先前對話），截圖裡看不出是不是 Warp。
- L5 沒有逐項記錄；P4（打字後 Enter）沒有回報。

## Phase 2：切片 b，T1 門檻提示（Cloud，2026-10-08）

環境：Linux container、Claude Code 2.1.292，pty 驅動真實互動 session（拋棄式 git repo，120 欄，`HANDOFF_THRESHOLD_PCT=1`，工作樹有一個未追蹤檔）。**不是 Tom 的 macOS／Warp，也還沒按過按鈕。**

| 項目 | 結果 |
| --- | --- |
| 驗證與測試 | `claude plugin validate --strict .` 通過；`claude plugin test .` **139 pass、0 fail**（新增 15 項）。 |
| 變異檢查 | 弄壞八處（髒樹判斷恆為真、不記錄已問過的門檻、不重置壓縮後的百分比、「別再問」沒存、啟動交接不收起提示、T1 status 壓過清單、`/clear` 不重置、「再多 10%」沒存）：七個一開始就被抓到，**「別再問」沒存那個沒被抓到**（同一門檻本來就只問一次，會掩蓋它），補了「壓縮後再升到門檻仍不問」的測試後也被抓到。 |
| 真實 session | 回答後出現 band：「Context 已用 4%，要先交接嗎？」與「同意」「再多 10% 再問」「這個 session 別再問」；輸入框下方 `⚠ handoff-mod: Context 已用 4%。需要時輸入 /handoff-mod:handoff 交接`；追蹤顯示 `threshold: percent=4 at=1 dirty=true -> ask`。 |

限制：

- 按鈕在 Cloud 沒按過（Tom 的 L4 證明 Tab 與點擊可用，但沒有按過這三個）；「同意」會走計時器啟動 skill，這條只有測試覆蓋，真實 session 沒走過。
- 「未完成跡象」只看 `git status`（計畫決定 9）；非 git 目錄不會被問。
- 窄視窗加 attention-mod 時 band 看不到、只剩 status（P2 已證明 status 看得到），所以 T1 在那種情況靠 status 與手動輸入指令。
- 門檻預設 60%，這次測試用 1%；60% 的實際體驗（多久會被問到）還沒有人用過。

### Tom 的本機實測：T1（macOS、Claude Code 2.1.292，2026-10-08，`cebb240`，`HANDOFF_THRESHOLD_PCT=1 HANDOFF_DEBUG=1`）

結果是 Tom 回報加兩張截圖，我沒有親眼驗證。

| 項目 | 結果 |
| --- | --- |
| T1-1 出現 | band「Context 已用 5%，要先交接嗎？」、三個按鈕，輸入框下方 `⚠ handoff-mod: Context 已用 5%。需要時輸入 /handoff-mod:handoff 交接`；追蹤 `percent=5 at=1 dirty=true -> ask` |
| T1-2 不重複 | 再送提示沒有第二個 band |
| T1-3 再多 10% | 按鈕可按，band 與 status 消失 |
| T1-4 別再問 | 按鈕可按，band 與 status 消失 |
| T1-5 同意 | 草稿有出現 |
| T1-6 與 attention-mod 同載入 | 截圖：attention-mod 收合成一行（「展開面板」），band 與 status 都看得到，band 右上有 `[-]` |
| T1-7 沒有未完成跡象 | 沒被問 |

限制：

- T1-6 的截圖是 attention-mod **收合**時，不是先前 P2 的「展開的 inline 面板」，所以不能證明展開時 band 看得到；P2 先前的結果（展開時 band 被遮、status 看得到）仍然成立。
- 預設 60% 的實際體驗（多久被問到、是否太吵）沒有人用過；這次門檻是 1%。
- 決定 9 到 12 Tom 沒有回應，目前視為沿用。
- 窄視窗（約 80 欄）沒有單獨回報。

## Phase 2：切片 g，使用計數指令（Cloud，2026-10-08）

環境同切片 b。指令名 `/handoff-stats` 是我取的（D6 沒有規定計數指令的名字）。

| 項目 | 結果 |
| --- | --- |
| 驗證與測試 | `claude plugin validate --strict .` 通過；`claude plugin test .` **142 pass、0 fail**（新增 3 項，並修改註冊測試）。 |
| 變異檢查 | 弄壞三處（寫入不計數、讀錯 store 的 key、指令沒註冊）：全部一開始就被抓到。 |
| 真實 session | `/handoff-stats` 印出 `交接寫入 0 次，接續 0 次`（Cloud 的 store 這次是空的）。 |

計數只存在 `$.store`，不外傳；指令用 `$.ui.log` 輸出，Claude 讀不到。限制：Tom 的環境沒試過；損壞的計數紀錄會讀成 0。

## Phase 2：切片 f，結束筆記（D4 做法 2，路線 B；Cloud，2026-10-08）

D4 由 Tom 於 2026-10-08 決定照原設計存對話片段（做法 2）。路線 B：`session.end` 讀不到訊息（P1），所以平時記、結束時寫。環境同切片 b，**不是 Tom 的 macOS**。

| 項目 | 結果 |
| --- | --- |
| 驗證與測試 | `claude plugin validate --strict .` 通過；`claude plugin test .` **153 pass、0 fail**（新增 11 項）。 |
| 變異檢查 | 弄壞九處（請求或回應沒遮蔽、記錄沒刪、`/clear` 仍寫、沒有逾時放棄的保護、沒有 `chmod 600`、清掃判斷反向、乾淨樹仍寫、斜線與 plugin 提示也記錄）：八個直接被抓到，**「逾時放棄」那個一開始沒被抓到**（我的測試每個 git 呼叫延遲 5 秒，整段流程超過測試推進的時間，根本沒走到寫檔），改成每個呼叫 1 秒、推進足夠久後被抓到。 |
| 真實 session（Cloud，`/exit`） | 送一個含 `password = hunter2hunter2` 的提示，再 `/exit`：寫出 `feat-demo--<時間>--auto.md`，權限 `-rw-------`；請求與任務中的密碼變成 `[redacted]`；有「最後一個要求」「最後一段回應」「branch／HEAD」「有改動的檔案」；`.git/info/exclude` 新增 `.claude/handoffs/`；store 的暫存紀錄已刪（檔案只剩 `{}`）。下次啟動：清單顯示該筆並標「自動留下，未經審查」。 |

行為：

- 平時每個真正的提示（`composer`、`bridge`、`sdk` 來源，不以 `/` 開頭，互動 session）把**已遮蔽、截斷到 2000 字**的請求存進 `$.store` 的 `last:<session id>`（每 session 一筆，每個提示覆蓋），每個回合結束時補上回應。
- `session.end` 時：有記錄、`reason` 不是 `clear`、工作樹有未提交變更、`HANDOFF_AUTO_NOTE` 不是 `off`，才組檔寫入（`$.fs.write` 之後 `chmod 600`），預算取 `min(1500 ms, 剩餘預算 − 200 ms)`，逾時就不寫。**記錄一律刪除**。
- 啟動時清掉超過 7 天的 `last:*`（當機或 `kill -9` 的殘留）。

限制與沒驗證的：

- **遮蔽只認有特徵的形式**（`password = …`、`sk-…`、Bearer 等九種）。回應或請求裡單獨出現的密碼字串（例如「用 hunter2 部署」）**不會**被遮蔽；這是設計就寫明的「降低風險、不是保證」。
- Tom 的 macOS：store 目錄是 0755、檔案 0600（P3），所以暫存紀錄的**內容**別的使用者讀不到，但檔名可見；筆記檔本身 `chmod 600`，**在 macOS 沒驗證**。
- 結束方式只在 Cloud 驗過 `/exit`。Ctrl-C 兩次、關分頁（SIGHUP）、`reason: other` 沒有在真實 session 驗證（P1c 在 Cloud 沒重現過 `session.end`）。
- 沒有未完成跡象（乾淨樹、非 git 目錄）就不寫；決定 9 同樣適用。
- `$.fs.write` 之後到 `chmod` 之前有一小段時間檔案是預設權限（已遮蔽內容，視窗很短）。
- 逾時之後背景裡的呼叫仍會跑完，但不會寫檔（有保護，已測）。

### Tom 的本機實測：結束筆記（macOS、Claude Code 2.1.292，2026-10-08，`d91df57`）

結果是 Tom 回報的 `ls -l` 輸出，我沒有親眼驗證。

| 項目 | 結果 |
| --- | --- |
| E-1 `/exit` | 寫出一個 `feat-demo--20261008-101525--auto.md`，830 位元組，權限 `-rw-------@`（0600） |
| E-2 連按兩次 Ctrl-C | 同一個目錄新增 `feat-demo--20261008-101745--auto.md`，825 位元組，權限 `-rw-------@`（0600）。**這也回答了 P1c：Ctrl-C 兩次在 macOS 會觸發 `session.end`，且筆記寫得出來。** |
| E-3 關閉終端機分頁 | Tom 當時找不到測試路徑，事後用 `$TMPDIR/tmp.*/.claude/handoffs/` 找回：同一個 repo 有第三個 `feat-demo--20261008-101936--auto.md`，767 位元組，權限 `-rw-------@`（0600），時間在 E-2 之後兩分鐘，符合「關分頁」那一輪。**通過**（以時間先後判斷是 E-3 的筆記，沒有其他證據）。 |

事後補查（Tom，同一批 `tmp.*` 目錄）：

| 項目 | 結果 |
| --- | --- |
| 密碼遮蔽 | 三個筆記對明文密碼的 `grep -c` 都是 **0**（輸入是 `password = abc12345` 形式，有特徵，符合預期）。 |
| `.git/info/exclude` | 用 `GIT_CONFIG_GLOBAL=/dev/null` 啟動的那個 repo 有 `.claude/handoffs/`；其他較早的測試 repo 沒有，是因為當時全域 gitignore 已涵蓋該路徑（`ensureExcluded` 先 `check-ignore`，符合預期）。 |
| store 暫存 | `grep -c '"last:'` 為 **0**，暫存紀錄已刪。 |

仍**未確認**：下次啟動清單在 macOS 是否顯示該筆並標「自動留下，未經審查」（Cloud 看過）；遮蔽對「沒有特徵的單獨密碼字串」仍無效（設計限制，不是測試項目）；`/handoff-stats` 與 `stats.written` 在 Tom 環境的計數；P4。

## 尚未做

Task 14 的其餘驗收、Task 15（文件與 marketplace）。L1 已通過；`stats.written`、排除功能在無全域 gitignore 時的行為、P4 沒有確認。
