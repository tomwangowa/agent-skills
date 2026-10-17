# Task 6：兩個 CLI 的發佈產物

日期：2026-10-14。`feat/skill-plugins`，基準 `69dfe5d`。Source 與產物尚未提交、安裝或發布。

已產生 `plugins/claude/<七包>`、`plugins/codex/<七包>` 與兩個 marketplaces。Claude 原有 attention-mod、handoff-mod entries 保留，版本與來源未改。Codex 採實測的 `.codex-plugin/plugin.json`／`.mcp.json`，沒有會遮蔽它的根目錄 manifest。

來源與產物各自保存 SHA-256 綁定；`--check` 在暫存目錄完整重建後比較檔案內容與 mode，不改動正式產物。`--write` 先產生全部內容，再替換受管目錄；拒絕 symlink parent、無受管 inventory 的既有目錄及非清單內的額外檔案。它不宣稱跨十四個目錄的替換具備整體原子性。

MCP 從明確白名單編譯、用 lockfile 安裝 production dependencies。曾用一次性假資料檔證明舊的 src 遞迴複製會編譯清單外內容，修正後同一行為測試通過。產物没有 tsx、TypeScript、Vitest 或私人 config，安裝者不需要下載或編譯。每包帶 scoped catalog，user-only metadata 保留；router 的 package index 僅描述可安裝成員，不能當安裝證據。

## 實測證據

| 檢查 | 結果 |
| --- | --- |
| 完整 Python 回歸 | 129／129，包含六項 builder 與四項 release checker 測試 |
| 缺檔、過時 source、private config、固定維護者路徑、symlink／parent symlink、缺少 reference、錯版本、shadow manifest | 以一次性 repo 驗證拒絕 |
| `build_plugins.py --write` 後 `--check` | 退出 0，重建無差異 |
| `check_plugin_release.py` | 退出 0，來源、inventory、native manifests、marketplaces 一致 |
| Claude 原生 plugin validate | 七包與 marketplace 全部退出 0；七包缺 author 的可選 warnings 保留 |
| 完整套件搬移 | 兩平台都從含空白／中文的新路徑、不同 cwd 啟動真實 stdio server；各七工具、roundTrip=true |
| catalog、diff check | 退出 0 |

搬移驗證只使用暫存 shared settings 與兩筆合成紀錄，測試結束刪除整個 fixture。首次搬移 fixture 缺 sources 而失敗，server stderr 明確指出設定錯誤；原始失敗與修正後結果均保留。另一次驗證 helper 的 repo parent 層數錯誤也保留，修正後重跑成功。這些失敗不計入成功數。

## 判定與限制

驗證環境為 macOS、Node v23.7.0、Python 3.14.6；不將它們當最低支援版本。Context7 本 session 沒有可呼叫工具，manifest／launch 使用 Task 1 的原生實測契約，Codex marketplace 格式核對已安裝的 upstream native entries。

VERIFIED：本項的來源產生、可攜 server、產物完整性與 Claude manifest schema。NOT VERIFIED：新版十四份套件在兩 CLI 的實際安裝、hook 信任、模型路由、更新／遷移，以及跨平台操作。完整 plugin 語意路由由 Task 7 實作；此報告不把 Task 1 的舊 probes 當新版驗收。

Production 依賴仍有既有的 15 項漏洞（1 critical、10 high、3 moderate、1 low）。Artifact checker 的通過只表示產物完整性，不表示依賴安全或可以發布。完整 branch review、commit／發布批准仍待後續。
