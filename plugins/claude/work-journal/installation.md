# 安裝與設定 CLI 套件

本指南說明 Claude Code 和 Codex 的命令列版本（CLI）如何安裝及管理套件，不包含桌面版。Marketplace 是套件目錄；照[中文 README 的指令](https://github.com/tomwangowa/agent-skills/blob/main/README.zh.md#直接從-marketplace-安裝)加入目錄，再安裝想用的套件即可。加入目錄後，每條套件安裝指令一次安裝一包，不必全裝。套件用途見[套件清單](https://github.com/tomwangowa/agent-skills/blob/main/docs/plugins/README.md)；不確定要選哪些，可先看[使用情境範例](https://github.com/tomwangowa/agent-skills/blob/main/docs/plugins/usage-examples-zh.md)。安裝或更新後，重新啟動 CLI 才會載入新內容。

## 設定 work-journal

`work-journal` 可以記錄工作，也能搜尋活動紀錄和你選定的筆記。設定時必須指定活動紀錄資料夾，建議放在 `~/.agent-skills/activities`；筆記資料夾可不填，填入時查詢也會搜尋那些筆記。

第一次設定會在 `~/.config/agent-skills/` 建立 `work-journal.json`，並建立尚不存在的活動紀錄和筆記資料夾。它不會搬動或讀取資料夾裡已有的內容。如果你已經有活動紀錄，請在設定時選原本的資料夾。兩套 CLI 共用這份設定；若已有 `work-journal.json`，設定程式會保留原內容，不會覆蓋。之後要加入筆記資料夾，請把路徑加到檔案的 `sources.notes.paths`，再重新啟動 CLI。

若已設定 `AGENT_SKILLS_CONFIG_DIR`，會使用它指定的資料夾；若只有設定 `XDG_CONFIG_HOME`，則使用 `$XDG_CONFIG_HOME/agent-skills/`。語言偏好檔也放在同一個設定根目錄。

執行設定需要 Python 3；MCP 查詢工具需要 Node.js。先安裝 `work-journal`，再選一段符合你所用 CLI 的指令。將已安裝的套件位置存到 `AGENT_SKILLS_PLUGIN_ROOT`，供後面的設定命令使用。範例依照 README 的個人安裝方式查找套件，並使用 Bash；Windows PowerShell 的原生設定流程尚未驗收。

Claude Code：

```bash
export AGENT_SKILLS_PLUGIN_ROOT="$(
  claude plugin list --json |
  python3 -c 'import json,sys; print(next(p["installPath"] for p in json.load(sys.stdin) if p["id"] == "work-journal@tomwangowa" and p["scope"] == "user"))'
)"
```

Codex：先執行 `codex plugin list --marketplace tomwangowa --json` 查看已安裝的 `work-journal` 版本，再把下面的 `<version>` 換成該版本：

```bash
export AGENT_SKILLS_PLUGIN_ROOT="${CODEX_HOME:-$HOME/.codex}/plugins/cache/tomwangowa/work-journal/<version>"
```

先預覽活動紀錄會存在哪裡：

```bash
PYTHONPATH="$AGENT_SKILLS_PLUGIN_ROOT/runtime" python3 -m agent_skills_runtime.setup \
  --activities "$HOME/.agent-skills/activities" --preview
```

若也要搜尋筆記，在指令中加入 `--notes "$HOME/你的筆記資料夾"`；多個資料夾可以一起列在 `--notes` 後面。預覽確認路徑正確後，用相同指令再執行一次，並移除 `--preview`。這時程式會建立設定檔和缺少的資料夾。

`work-journal` 套件附有 MCP 查詢工具（讓 CLI 呼叫資料查詢服務的連線方式）。設定後重新啟動 CLI，再確認工具是否出現；若沒有出現，先確認套件已啟用並查看[驗收紀錄](https://github.com/tomwangowa/agent-skills/blob/main/docs/validation/skill-plugins/README.md)。不要另外新增全域 MCP 設定，以免和套件內的設定重複。

## 檢查 hooks

Hooks 是 CLI 在工作階段開始或執行特定操作時，自動執行的小命令。`quality-gates`、`technical-decisions`、`skill-toolbox` 和 `session-preferences` 含有 hooks。

如果 CLI 要求檢視或信任 hooks，先看清楚它會執行什麼，再依 CLI 的提示決定。Codex 可用 `/hooks` 檢視 hooks；不要略過宿主提供的檢查，也不要手動改信任設定。

## 預設回應語言（選用）

安裝並啟用 `session-preferences` 後，若想讓新工作階段預設使用繁體中文回覆，可以在 `~/.config/agent-skills/agent-skills.json` 加入以下設定。若檔案已有其他內容，只加入 `session_preferences` 欄位，不要整份覆蓋：

```json
{
  "session_preferences": {
    "response_language": "繁體中文"
  }
}
```

設定會在新工作階段載入；目前工作階段可執行 Claude Code 的 `/session-preferences` 或 Codex 的 `$session-preferences` 立即重載。你在當次訊息明確指定其他語言時，會以當次要求為準。個人偏好與更新細節見 [session-preferences 使用手冊](https://github.com/tomwangowa/agent-skills/blob/main/plugins/claude/session-preferences/skills/session-preferences/README.md)。

## 更新套件

先更新 Marketplace 清單，再更新套件。以下以 `work-journal` 為例；若要更新其他套件，換成該套件名稱。Claude Code 會在更新後要求重新啟動，才能套用新版本：

```bash
claude plugin marketplace update tomwangowa
claude plugin update work-journal@tomwangowa --scope user
```

Codex 從 GitHub 套件目錄更新目前只驗證過 `session-preferences`；其他套件、版本和平台尚未驗證。Windows、Linux 和其他 CLI 版本也尚未完成原生驗收，完整紀錄見[驗收說明](https://github.com/tomwangowa/agent-skills/blob/main/docs/validation/skill-plugins/README.md)。以下是已驗證情況使用的指令：

```bash
codex plugin marketplace upgrade tomwangowa
codex plugin add session-preferences@tomwangowa
```


## 停用或移除套件

以下以 `work-journal` 為例；處理其他套件時，換成該套件名稱。停用會讓套件保持安裝、但暫時不載入；移除則會解除安裝。這些操作不會刪除活動紀錄、筆記或共用設定。

Claude Code：

```bash
claude plugin disable work-journal@tomwangowa --scope user
```

要移除時執行：

```bash
claude plugin uninstall work-journal@tomwangowa --scope user --keep-data
```

Codex 要長期停用時，在 `~/.codex/config.toml` 將該套件的 `enabled` 設為 `false`；要重新啟用時改回 `true`：

```toml
[plugins."work-journal@tomwangowa"]
enabled = false
```

移除 Codex 套件：

```bash
codex plugin remove work-journal@tomwangowa
```

要搬移或恢復舊版設定，請看[遷移與恢復指南](migration.md)。

套件的原生驗收結果適用於紀錄中列出的版本；套件變更後，發布前需要重新驗收。詳見[驗收紀錄](https://github.com/tomwangowa/agent-skills/blob/main/docs/validation/skill-plugins/acceptance.json)。
