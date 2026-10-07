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

## 尚未做

Task 13 的切片 b（T1 提示）、f（結束筆記）、g（計數指令）、Task 14（Tom 本機驗收）、Task 15（文件與 marketplace）。實作前驗證 P2、P3、P4 仍待 Tom。
