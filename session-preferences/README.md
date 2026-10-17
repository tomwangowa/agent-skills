# session-preferences 使用手冊

`session-preferences` 是一組 session 回應規則。Claude Code CLI 和 Codex CLI 開新 session、接續 session、/clear、壓縮 context 時，SessionStart hook 會自動注入；它不會改 global policy，也不會自己同步到其他 runtime。

## 啟用

平常不用做任何事，hook 會在 session 開始時載入規則。想在某個 session 不套用，開 session 前設 `AGENT_SESSION_PREFS=off`。

hook 沒跑的 session 裡，要手動套用時：

```text
$session-preferences
```

## 新增規則

```text
$session-preferences add-deai 不要用「痛點」當成泛稱
$session-preferences add-deai 翻譯時保留原文刻意的排比
$session-preferences add-rule socratic-dialogue: 每個問題都附一個具體例子
$session-preferences add-rule deai-voice: 避免重複同一種句尾
```

`add-deai` 會先依規則的用途，提議放進最適合的去 AI 味規則檔；不會直接寫入。省略類別的 `add-rule` 也會先提議放置位置；不適合既有類別時，才提議新 module。每次都先顯示完整的新內容與個人目標檔案，只有你確認後才會寫入。預覽時記住的舊內容雜湊必須仍然相同，否則重新預覽、重新取得確認。確認寫入後，會讀回修改過的檔案，新規則立即套用到本 session 後續回應。

## 個人覆寫

Claude Code CLI 與 Codex CLI 使用相同的設定根目錄，依序採用 `AGENT_SKILLS_CONFIG_DIR`、`XDG_CONFIG_HOME/agent-skills`、目前使用者的 `~/.config/agent-skills`。明確設定的環境路徑必須是絕對路徑或 `~/` 路徑。

個人規則存於該根目錄的 `preferences/`，不修改 plugin 快取。與預設同名的檔案會整份取代預設；新增模組則列入個人 `INDEX.md`，接在預設模組後面載入。按需讀取的 reference 也可同名覆寫，但修改它不會讓它每次都載入。`control-return.md` 由自己的 hook 處理，不放進這份 INDEX。

首次覆寫會記下原始預設內容的 SHA-256。更新套件後，個人副本保留；檢查入口會提示被覆寫的預設是否已變更，讓你選擇保留副本或重新採用預設，不自動合併。

從原始 repo 根目錄可以唯讀查看有效內容與更新狀態：

```sh
PYTHONPATH=runtime python3 -m agent_skills_runtime.preferences load --default-dir session-preferences/references
PYTHONPATH=runtime python3 -m agent_skills_runtime.doctor --config preferences --preferences-defaults session-preferences/references --control-return-skill control-return/SKILL.md
```

在安裝的 plugin 中，將 `PYTHONPATH` 換成該 plugin 的 `runtime/`，預設目錄換成 `skills/session-preferences/references/`。需要指定測試設定時，兩個命令都接受位於子命令前的 `--config-root`；這不會修改全域環境設定。

確認後的寫入由 `python3 -m agent_skills_runtime.preferences save` 處理；參數詳見 `--help`。它以排他鎖與原子替換寫檔，舊內容不符時拒絕覆蓋。寫入支援 macOS、Linux 與 WSL，尚不支援原生 Windows。

## 故障排查

個人檔案損壞或不能讀取時，hook 只套用其他可讀模組，並指出未載入項目。它不會悄悄改回同名預設；修好副本後再重新載入。套件缺少 `runtime/` 或設定根目錄無效時，也會明確回報，不能把安裝成功視為規則已套用。

## 規則檔案

`references/INDEX.md` 列出啟用時一定會讀取的 modules：

- `deai-voice.md`：通用、可分享的日常去 AI 味規則、優先序與按需載入判斷。
- `explanation-depth.md`：重要判斷、設計變更和交接內容要交代理由、影響範圍、取捨與驗證方式。
- `socratic-dialogue.md`：brainstorming 這類一問一答時，把問題講清楚並附例子。

「每則回覆附三個下一步」是另一個 skill：`$control-return`，有自己的 SessionStart hook，同一個 `AGENT_SESSION_PREFS=off` 也會關掉它。

去 AI 味規則會依情境讀取以下 reference，不會在每次啟用時全部載入：

| 規則檔 | 何時讀取 | 用途 |
| --- | --- | --- |
| `deai-voice.md` | 啟用時 | 通用語氣、優先序與載入判斷 |
| `deai-longform.md` | 要求草稿或超過兩段的敘述 | 長文去 AI 味與靜默自檢 |
| `deai-translation.md` | 翻譯 | 忠實優先的自然繁中處理 |
| `taiwan-zh.md` | 台灣用語、疑似中國大陸用語或標點需要判斷 | 地區用語與標點 |

台灣繁中是預設，不會蓋過使用者指定的地區、引用原文或既有技術慣用語。程式碼、識別字、路徑、固定格式，以及明確要求的表格或條列，也不會被這組規則改寫。

若 modules 的規則互相衝突，agent 會指出衝突讓你決定，不會自行挑一條覆蓋另一條。

## 不包含什麼

這個 skill 不複製 `deai-voice-rewrite` 的對外稿改寫流程、Tom 個人語氣或事實凍結 checklist，也不會每次輸出一份自檢清單。它不會自動執行 `skill-sync`；同步是另一個需明確呼叫的動作。
