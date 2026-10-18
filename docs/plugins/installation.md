# 安裝、設定與更新

支援 Claude Code CLI 與 Codex CLI，桌面版不在範圍內。2026-10-15 的原生驗收在 macOS 隔離 fixture 上，以 Claude Code 2.1.300、Codex 0.162.1 測過七包的安裝、hooks、MCP、路由、更新與 fixture 遷移；`session-preferences` 與 `work-journal` 在那之後有修改，發布前需要重新驗收。2026-10-17 另以 Claude Code 2.1.302 驗證 GitHub marketplace 安裝、刷新和更新檢查；Codex CLI 的遠端 Git marketplace 尚未測試。正向版本升級使用本機暫存 Git 遠端，不代表 GitHub 已發布新版。完整範圍見 `docs/validation/skill-plugins/remote-marketplace-validation.md` 與 `acceptance.json`。以下安裝指令供產物核准發布後使用；目前可供維護者審查的是 worktree 內的生成目錄。

## 選擇並安裝

不必一次裝七包。以下以 work-journal 為例；其他選擇把套件名稱替換為 README 表中的名字。

Claude Code：

```bash
claude plugin marketplace add tomwangowa/agent-skills --scope user
claude plugin install work-journal@tomwangowa --scope user
claude plugin list
```

Codex：

```bash
codex plugin marketplace add tomwangowa/agent-skills --ref main
codex plugin add work-journal@tomwangowa
codex plugin list --marketplace tomwangowa --json
```

先完成需要的資料設定，再重新啟動 CLI。有 hooks 的套件是 quality-gates、technical-decisions、skill-toolbox、session-preferences。檢視本次安裝的實際程式與資源；Codex 用正常 `/hooks` 對選定的新 hooks 完成信任。不要改寫信任 state 或跳過 review。此處沒有自動安裝 Superpowers；相關分支按相容性文件檢查。

## 首次 work-journal 設定

設定根目錄優先序是 `AGENT_SKILLS_CONFIG_DIR` → `$XDG_CONFIG_HOME/agent-skills` → `~/.config/agent-skills`。它在 plugin 快取外，兩個 CLI 與 shell 共用。可直接引用既有活動／筆記資料，不必搬移。活動目錄須可讀、可寫與可搜尋；notes 至少指定一個非空路徑；首次 setup 建立不存在的目錄。啟動時尚未檢查筆記目錄是否存在，不存在的筆記目錄目前會回傳空集合。

從原生 plugin inventory 找到目前 work-journal 的實際根目錄，再將下面三個示例路徑替換為你的選擇：

```bash
export AGENT_SKILLS_PLUGIN_ROOT="/absolute/installed/work-journal"
export AGENT_SKILLS_CONFIG_DIR="$HOME/.config/agent-skills"
PYTHONPATH="$AGENT_SKILLS_PLUGIN_ROOT/runtime" python3 -m agent_skills_runtime.setup \
  --activities "/absolute/activities" --notes "/absolute/notes" --preview
```

確認預覽後，用相同參數移除 `--preview` 執行一次。既有設定不會被覆蓋。設定檔形狀為：

```json
{
  "sources": {
    "activities": "/absolute/activities",
    "notes": {"paths": ["/absolute/notes"], "recursive": true, "exclude_hidden": true}
  }
}
```

`CLAUDE_ACTIVITIES_DIR` 可明確覆寫活動路徑；相對值以設定根目錄為準。使用覆寫時，Python 與 MCP 程序必須繼承相同環境。設定變更後重新啟動 MCP／CLI；不要新增會與 plugin 重複的全域 MCP entry。

```bash
PYTHONPATH="$AGENT_SKILLS_PLUGIN_ROOT/runtime" python3 -m agent_skills_runtime.doctor \
  --commands node python3 jq bash --config work-journal
```

缺少設定不回退到私人 config。安裝產物帶已編譯 server 與 production dependencies，啟動時不使用 tsx、不下載依賴、不編譯原始碼。

## 偏好設定

session-preferences 的個人模組存於設定根目錄的 `preferences/`，整份取代同名預設；control-return 是獨立模組。先讀該包 SKILL 的載入／預覽／確認流程，確認後使用 bundled CLI 寫入個人副本，保留 base hash 與 expected hash。不要直接修改快取內的 references。

僅此一次停用偏好可從新 session 啟動：

```bash
AGENT_SESSION_PREFS=off codex
AGENT_SESSION_PREFS=off claude
```

這不移除工程套件的路由。工程套件需要 Python；work-journal 另外需要 Node、jq、bash；toolbox 的 standalone sync 需要 rsync。實測環境為 macOS、Node v23.7.0、Python 3.14.6；最低版本、Linux／WSL 的完整 native 行為尚未驗證。個人規則與遷移寫入採 POSIX locks，不支援原生 Windows 寫入。

## 更新、停用與移除

更新前保存舊版本的 hook 資源供比對，保留外部設定與個人副本。以下只操作選定 marketplace／plugin：

```bash
claude plugin marketplace update tomwangowa
claude plugin update work-journal@tomwangowa --scope user
codex plugin marketplace upgrade tomwangowa
codex plugin add work-journal@tomwangowa
```

Codex 的 add 是原生安裝入口；對已安裝插件再次 add 的完整更新行為仍待 native 驗收，不能先宣稱快取已更新。重啟後核對實際版本、資源、七個 MCP 工具及設定根目錄。Session-preferences 更新後，先把 `AGENT_SKILLS_PLUGIN_ROOT` 改成該包目前的根目錄，再用它的 runtime：

```bash
PYTHONPATH="$AGENT_SKILLS_PLUGIN_ROOT/runtime" python3 -m agent_skills_runtime.migration updates \
  --config-root "$AGENT_SKILLS_CONFIG_DIR" \
  --defaults "$AGENT_SKILLS_PLUGIN_ROOT/skills/session-preferences/references"
```

預設變更只提示，不覆蓋個人模組。Native fixture 驗收確認兩平台升級後仍保留個人覆寫與活動設定。Codex 0.162.1 在本機 marketplace fixture 上透過再次 `plugin add` 更新套件快取；本機目錄來源的 `marketplace upgrade` 不受支援。Codex CLI 的遠端 Git marketplace 升級尚未實測；Claude Code 的遠端檢查結果見驗證紀錄。比對舊／新版 hooks：

```bash
PYTHONPATH="$AGENT_SKILLS_PLUGIN_ROOT/runtime" python3 -m agent_skills_runtime.migration hooks \
  --previous "/absolute/old-plugin" --current "$AGENT_SKILLS_PLUGIN_ROOT"
```

它只回報資源差異，不修改 native trust。若 hook 命令有變，到 Codex 正常 `/hooks` 檢視內容並依 CLI 提示重新信任；本次只驗證隔離 fixture 中已審查命令的正常信任流程。

Claude 停用／移除：

```bash
claude plugin disable work-journal@tomwangowa --scope user
claude plugin uninstall work-journal@tomwangowa --scope user --keep-data
```

Codex 此次啟動停用：

```bash
codex -c 'plugins.work-journal@tomwangowa.enabled=false'
```

持續停用則備份並檢視 config.toml 後，把 `[plugins."work-journal@tomwangowa"]` 的 `enabled` 設為 `false`；重新啟用設 `true`。CLI override key 不要內嵌 literal quotes；TOML table 的 quoted key 則遵守 TOML 語法。移除用：

```bash
codex plugin remove work-journal@tomwangowa
```

移除套件不包含刪除外部活動資料、筆記或個人設定。舊入口的回復按 migration 文件，不用重建或刪除資料目錄。
