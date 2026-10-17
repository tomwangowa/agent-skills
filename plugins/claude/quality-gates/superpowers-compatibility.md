# Superpowers 相容性

七包沿用外部 Superpowers，不內嵌它的 skills。僅安裝內容、日誌或偏好套件，不要求 Superpowers。依賴分類與選定分支在 `plugin-packages.json`，hooks 只注入該包路由；偏好 off 不會移除工程路由。

檢查時先比對目前 CLI 真正 exposed 的 skill 與 provider，從該 provider 的原生 manifest 讀 identity／version。Task 1 用 CLI 的原生 inventory、實際 source 讀取與 Superpowers 7.0.0 註冊取得證據；registry 提及、快取目錄存在或目錄名稱都不等於目前 session 已註冊。不同 marketplace 可提供同一 manifest identity；不要以來源 URL 不同就判為不相容。

`check_superpowers(required_skills, installed, tested_versions)` 接受明確的 registered metadata，例如：

```python
installed = {"providers": [{
    "name": "superpowers", "registered": True, "version": "7.0.0",
    "skills": ["writing-plans"], "source": "the-observed-marketplace",
}]}
```

這是資料格式範例，不是偽造 native 驗證的指令。只有從當前 CLI 的實際暴露結果取得的資訊才能用於實務判斷；不掃描私人對話、活動或模型輸入。函式分別回報未註冊、缺必要 skill、多個 identity 及未測版本。完整 flow 未實測前 `tested_versions` 是空清單；不能把相同 major version、舊 probe 註冊或 synthetic fixture 的通過擴大成新流程相容性。

| 使用分支 | 檢查邊界 |
| --- | --- |
| 多步驟設計轉實作 | brainstorming 完成設計後、交給 writing-plans 前 |
| PM／RD 或研究後實作 | 只檢查選到的計畫／執行分支 |
| 完成驗證 | 自有 completion-gate 可單獨使用；TDD／review／收尾整合才檢查對應上游 skills |
| Toolbox workflow discovery | 標示當下 installed／available／unavailable，不推薦缺少入口直接執行 |

跨 marketplace 的 Claude 原生 dependency 安裝尚未對新包實測，Codex 等價行為也尚未驗證；不宣告會自動下載全部依賴。依選定分支提示安裝／驗證，不在 SessionStart 擅自安裝上游。

macOS 隔離 fixture 的 native 驗收使用 Claude Code 2.1.300、Codex 0.162.1，兩者都已註冊 Superpowers 7.0.0。兩個 CLI 都載入自有 `technical-decisions:brainstorming` 與平台 reviewer；明確選取的 `writing-plans` 分支也載入既有 Superpowers skill，回報前置條件並停在規劃邊界。Codex 的自然語言完成檢查讀取了已安裝的 `quality-gates:completion-gate`，並因缺少最後變更後的驗證而拒絕宣稱完成。這只驗證上述分支與版本，不涵蓋完整上游設計／實作流程，因此 `tested_versions` 仍保持空清單。

手動限定的 toolbox 入口以明確 `$skill-toolbox:skill-sync` 呼叫驗證，僅說明 standalone source／cache 限制，沒有執行同步。Codex compaction 後曾重新注入相同五個路由／偏好標記；這些指示具冪等性。Git 遠端 marketplace、其他 CLI 版本與 Linux／WSL／Windows 行為仍未驗證。
