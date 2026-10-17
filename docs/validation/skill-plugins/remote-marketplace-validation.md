# 遠端 Git marketplace 驗證

日期：2026-10-17。這份紀錄補充 `acceptance.json` 的本機 fixture 驗收，範圍是 Git 遠端 marketplace 的安裝、刷新與更新。這次沒有修改或發布插件套件。

## Claude Code CLI

使用 Claude Code CLI 2.1.302，來源為 `https://github.com/tomwangowa/agent-skills.git`。遠端 `main`、本機 `HEAD` 與 `origin/main` 均為 `3f674e4152aa241ff8577d80004be15086feaf73`。

測試以全新的暫存 `HOME`、`CLAUDE_CONFIG_DIR`、外掛快取、`XDG_CONFIG_HOME`、`TMPDIR` 和空白工作目錄執行；以 `env -i` 清除呼叫端環境變數，並停用 system/global Git 設定與互動式認證。`CLAUDE_CONFIG_DIR` 將 Claude Code 設定和外掛資料導向指定路徑，詳見 [Claude Code 環境變數文件](https://code.claude.com/docs/en/env-vars)。

marketplace 列出的 9 個外掛（這次打包的七包，加上原本就有的 `attention-mod` 與 `handoff-mod`）均能從 GitHub marketplace 安裝，安裝路徑都在暫存目錄。`claude plugin marketplace update tomwangowa --json` 成功；接著對每個套件執行 `claude plugin update --scope user --json <plugin>@tomwangowa`，9 次都回報 `up_to_date`。版本與安裝檔案雜湊沒有變化，因為遠端 `main` 沒有新版。

| 外掛 | 版本 | 更新檢查 |
|---|---:|---|
| attention-mod | 0.4.6 | `up_to_date` |
| handoff-mod | 0.2.0 | `up_to_date` |
| quality-gates | 0.1.0 | `up_to_date` |
| technical-decisions | 0.1.0 | `up_to_date` |
| repo-workflow | 0.1.0 | `up_to_date` |
| content-tools | 0.1.0 | `up_to_date` |
| work-journal | 0.1.0 | `up_to_date` |
| session-preferences | 0.1.0 | `up_to_date` |
| skill-toolbox | 0.1.0 | `up_to_date` |

為了驗證實際版本轉換，另建立只存在於系統暫存目錄的 bare Git fixture。暫存 Git 設定將 CLI 接受的 HTTPS marketplace URL 改寫到這個本機遠端。先安裝 `content-tools` 0.1.0，再將 fixture 的 `main` 推進至 0.1.1，執行 marketplace refresh 與 plugin update。CLI 回報 `updated`、`oldVersion: 0.1.0`、`newVersion: 0.1.1`；安裝清單和標記檔也都確認 0.1.1。這驗證 Claude CLI 的 Git marketplace 更新流程，但網路傳輸使用本機 Git 遠端，不能代替 GitHub 上實際發布新版的測試。

測試後已移除 9 個套件與 marketplace；正向升級 fixture 也已刪除。未啟動 Claude session，因此沒有測試 skills、hooks 或 MCP 在 session 中的執行情形。

## Codex CLI

先前的原生驗收已用 Codex CLI 0.162.1 和唯一的本機 marketplace fixture 測過安裝、MCP、啟動、路由、更新及遷移；詳見 [`acceptance.json`](acceptance.json)。這次沒有用 Codex CLI 安裝 Git 遠端 marketplace，也沒有測 Codex 的遠端升級流程。

目前 Codex CLI 有 `plugin marketplace add/list/upgrade/remove`、`plugin add/list/remove` 命令；`CODEX_HOME` 可將 Codex 指向獨立設定與插件環境。全新 `CODEX_HOME` 的隔離探測回報 `{"marketplaces":[]}`，`codex login status` 顯示未登入，探測目錄隨後已刪除。OpenAI 官方的 [插件文件](https://developers.openai.com/plugins/build/plugins) 說明 CLI Git marketplace 命令；[Codex 插件評估範例](https://developers.openai.com/cookbook/examples/partners/harness_aware_plugin_evals/harness_aware_plugin_evals)示範以 `CODEX_HOME` 載入獨立插件設定。

## 手動隔離測試方式

可在空白工作目錄，用新的 `HOME`、`CODEX_HOME`、`XDG_CONFIG_HOME` 和 `TMPDIR` 執行 Codex CLI。下列命令示範測試安裝、遠端 marketplace refresh、重新安裝更新和清理；每次命令都以 `env -i` 啟動，僅傳入明確設定。請存成腳本檔再用 `bash` 執行；開頭的 `set -euo pipefail` 和 `trap` 若直接貼進互動式 shell，出錯或結束時會連 shell 一起關掉：

```bash
set -euo pipefail
TEST_ROOT="$(mktemp -d)"
trap 'rm -rf -- "$TEST_ROOT"' EXIT
CODEX_BIN="$(command -v codex)"
GIT_BIN="$(command -v git)"
TEST_PATH="$(dirname "$CODEX_BIN"):$(dirname "$GIT_BIN"):/usr/bin:/bin:/usr/sbin:/sbin"
mkdir -p "$TEST_ROOT/home" "$TEST_ROOT/codex-home" "$TEST_ROOT/xdg" \
  "$TEST_ROOT/tmp" "$TEST_ROOT/work"
touch "$TEST_ROOT/gitconfig"

run_codex() {
  (cd "$TEST_ROOT/work" && env -i \
    PATH="$TEST_PATH" HOME="$TEST_ROOT/home" \
    CODEX_HOME="$TEST_ROOT/codex-home" XDG_CONFIG_HOME="$TEST_ROOT/xdg" \
    TMPDIR="$TEST_ROOT/tmp" GIT_CONFIG_GLOBAL="$TEST_ROOT/gitconfig" \
    GIT_CONFIG_NOSYSTEM=1 GIT_TERMINAL_PROMPT=0 \
    "$CODEX_BIN" "$@")
}

run_codex plugin marketplace add https://github.com/tomwangowa/agent-skills.git --ref main --json
run_codex plugin add work-journal@tomwangowa --json
run_codex plugin list --marketplace tomwangowa --json
run_codex plugin marketplace upgrade tomwangowa --json
run_codex plugin add work-journal@tomwangowa --json
run_codex plugin remove work-journal@tomwangowa --json
run_codex plugin marketplace remove tomwangowa --json
```

安裝和更新測試應記錄版本、插件快取內容及 marketplace inventory。若要手動驗證模型 session 或插件功能，需在這個隔離的 `CODEX_HOME` 內另外登入；不要複製目前 `~/.codex` 的認證資料。Claude Code 可用同樣方式隔離 `HOME`、`CLAUDE_CONFIG_DIR`、Git 設定和工作目錄。Codex 的 marketplace 與登入狀態由隔離探測確認；上面的遠端安裝序列尚未執行。

## 未涵蓋範圍

- Codex CLI 的遠端 Git marketplace 安裝、刷新和套件更新尚未驗證。
- GitHub 上正式發布新版本後的正向升級尚未驗證；目前只有 `up_to_date` 結果和本機 Git fixture 的 0.1.0 → 0.1.1 升級。
- Claude Code 與 Codex CLI 的 session runtime、hooks、skills、MCP 需分別在新 session 測試；本紀錄只測 Claude CLI 安裝／更新命令和 Codex 的空白隔離設定。
