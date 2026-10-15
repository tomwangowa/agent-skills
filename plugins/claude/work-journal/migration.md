# 遷移與恢復

先盤點、備份，安裝並驗證替代 plugin，再切換舊 hook／MCP／明確的 routing 文字。資料目錄與 standalone user skills 保留；此工具不搬移活動、不安裝 plugin、不修改 native trust，也不掃描全域私人設定。只讀取 inventory 明確指定的檔案。

## 預覽

使用已安裝 work-journal 或 session-preferences 包內的 runtime。選一個快取外的工作目錄，準備 inventory；示例路徑要換成實際位置：

```json
{
  "replacement_verified": false,
  "files": [
    {"path": "/absolute/claude-settings.json", "format": "json", "legacy_roots": ["/absolute/old-skills"]},
    {"path": "/absolute/codex-hooks.json", "format": "json", "legacy_roots": ["/absolute/old-skills"]},
    {"path": "/absolute/codex-config.toml", "format": "toml", "legacy_roots": ["/absolute/old-skills"]}
  ]
}
```

不需要的檔案移除。只匹配選到的套件、舊根目錄及受支援的直接執行入口：session-preferences／control-return hooks 與 skills-query MCP。其他入口保留。含複雜 shell wrapper、TOML multiline strings 或不同格式時需另做明確審查，不猜測刪除。舊全域 routing 文字用 `format: "routing"`，提供逐條 `{package, before, after}`；before 必須恰好出現一次，其他文字逐位元保留。

```bash
PYTHONPATH="$AGENT_SKILLS_PLUGIN_ROOT/runtime" python3 -m agent_skills_runtime.migration preview \
  --inventory "/absolute/inventory.json" --packages work-journal session-preferences \
  --output "/absolute/reviewed-plan.json"
```

Plan 以 0600 建立，列出每個目標、動作、舊 hash、權限、備份檔名與被切換的 selector；stdout 不印完整設定。先核對 plan 內的具體 after 內容。`confirmed` 初始為 false，預覽本身不修改設定；output 已存在就拒絕覆蓋。

## 套用與恢復

實際驗證新 plugin 後，才把 inventory 的 `replacement_verified` 改為 true 並重新預覽。這個欄位是操作者的實際驗證紀錄，不能靠手動填 true 偽造驗收。確認新 plan 的完整 `preview_hash` 後：

```bash
PYTHONPATH="$AGENT_SKILLS_PLUGIN_ROOT/runtime" python3 -m agent_skills_runtime.migration apply \
  --plan "/absolute/reviewed-plan.json" --confirm "<full-reviewed-preview-hash>" \
  --backup-root "$AGENT_SKILLS_CONFIG_DIR/migrations"
```

只套用該 hash 綁定的清單。任何目標內容或權限在預覽後變更，就拒絕套用；需要新預覽與新確認。備份 run directory 為 0700，檔案與 manifest 為 0600。先保存全部 before bytes，再替換；一般寫入失敗時撤回已套用且未再變更的檔案。輸出 manifest 路徑供恢復：

```bash
PYTHONPATH="$AGENT_SKILLS_PLUGIN_ROOT/runtime" python3 -m agent_skills_runtime.migration restore \
  --manifest "/absolute/migrations/<run-id>/manifest.json"
```

恢復前核對全部 backup hash 與目前設定。遷移後若有新修改，不會覆蓋它，也不會先恢復其他檔案再發現衝突。備份保留供人工核對；不自動清理。JSON 設定切換會重新排版，但恢復後 bytes 與原始權限一致；TOML 與明確 routing 文字盡量保留原格式。

兩平台都已在隔離 fixture 完成預覽、確認套用與恢復，並核對恢復後 bytes、原始權限及不相關設定。這不代表已遷移真實使用者設定或整套既有 hooks／MCP。這也不是跨多檔交易：locks 只能協調使用同一 backup root 的工具程序，不能約束任意編輯器在核對與 rename 之間修改檔案；遇到程序中止或外部衝突，先檢查 manifest 與當下 hashes。任意時點的崩潰／恢復仍未驗證。
