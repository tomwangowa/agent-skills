# CLI plugin 安裝器

[English](README.md) | **繁體中文**

本壓縮包是供檢視的安裝器候選版，不代表已完成原生平台驗收。請先安裝 Claude Code CLI、Codex CLI，或兩者都安裝，並保留組織要求的登入／認證與模型供應商設定。已透過公司 AI endpoint（公司提供的模型服務網址）正常使用 Codex 的同事，走已驗證的 API-curated 安裝路徑時不需要登入 ChatGPT。安裝器不會設定或測試模型 endpoint、不會安裝任一 CLI，也不會改變 hook 的信任狀態。

在 macOS 解壓完整壓縮包後，開啟 `install-macos.command`，或執行 `bash install-macos.command`。這份 ZIP 只提供 macOS 安裝入口；Linux 與 Windows 啟動器仍在原始碼 repo 中，但不會放進這份壓縮包。macOS 入口會使用內附的 `install.py`；不支援直接把它當成另一個安裝入口執行。

先選 **Install/update** 或 **Remove packages**；按 Enter 會選擇 Install/update。接著選一個編號代表的 CLI，然後用 Up／Down 移動套件、按 Space 勾選或取消勾選，再按 Enter 確認。捲動式選單只列套件名稱及其 skills 名稱。按 `q` 或 Ctrl+C 取消。若取消勾選所有套件，安裝器會結束，不會安裝任何內容。Superpowers 強烈建議安裝，但預設不勾選。已安裝項目預設保留；更新要另外選取。來源準備、依賴安裝與 plugin 安裝會分別顯示提示並要求確認。在是／否提示中按 Enter 代表否。按 `q` 或送出 EOF（輸入結束訊號）會取消；在安裝確認畫面按 `b` 會返回套件選單。先前已核准的寫入會保留。

在 Remove packages 模式中，每個套件預設都不勾選。清單只會列出安裝器能辨識且提供移除的已安裝套件，包括先前以手動方式安裝、但來源已辨識的項目。未勾選的項目不會移除。確認前，預覽會列出實際安裝版本及完整的 marketplace 身分。移除模式不會設定 journal、不會更新來源、不會安裝或清除依賴，也不會清理 marketplace。

Claude 個人安裝的移除功能，是依已檢查過的 Claude Code `2.1.322 (Claude Code)` 命令格式實作。命令會明確帶入 `--scope user --keep-data --json`，因此專案／本機／受管理範圍的安裝和 plugin 資料目錄會保留。移除該 plugin 的最後一份安裝時，Claude Code 仍可能清除該 plugin 自己儲存的選項或密鑰；預覽會先說明。work-journal 設定、工作紀錄、筆記和共用工具都會保留。若來源、身分及原生快取路徑都能辨識，停用中的 plugin 和較新或較舊版本也可選擇移除。若同名 plugin 來自其他來源、有重複的個人安裝紀錄、版本不明，或快取路徑有連結等安全疑慮，安裝器會說明原因並保留。Superpowers 會依實際辨識到的已安裝來源處理；該來源可能與此壓縮包偏好的來源不同。

Codex 移除功能只有在唯讀 help 檢查確認原生介面 `codex plugin remove <plugin>@<marketplace> --json`，且已安裝 plugin 清單／快取符合預期結構時才會提供。它不限定單一 Codex 版本：官方 `0.166.0` 和 `0.167.0` 原始碼都有這個介面。若 CLI 使用不同或不明介面，安裝器會保留不動。原生命令會移除所選 plugin 的整個快取項目及 Codex 使用者設定中的項目，即使專案設定也有引用它。預覽會說明這可能讓那些專案無法載入該 plugin；專案設定和 plugin 資料目錄會保留。marketplace 和其他 plugin 項目不會移除。

每次解除安裝前，安裝器都會重新檢查所選註冊資料和目標快取。預覽也會指出實際使用的設定目錄：若切換 profile 連結或替換該目錄，移除流程會停止，必須重新預覽。穩定的上層目錄連結仍可使用；直接指向快取路徑的連結則不允許操作。只有在原生命令結果和重新讀取的清單都確認目標已移除、其他 plugin 項目仍在，且（對 Claude）受保護的專案檔案相符時，才會回報成功。這是保守的檢查，不是不可分割的檔案系統交易。結果會逐套件回報；失敗或取消後不會自動重試、重新安裝或回復。

來自本機、file 或不明來源的其他 plugin 會保持註冊並維持不受信任；其他能獨立辨識的套件仍可繼續處理。同名但來源不明的 plugin 會保留，不會被當成可信的安裝或移除目標。缺少必要清單欄位或自有 marketplace 資料不明時，仍會停止寫入；清單讀取失敗不代表沒有已安裝的 plugin。

除 `2.1.322` 以外的 Claude Code 版本，目前仍不提供移除功能，等待移除介面驗證。Codex 只有在原生 help、已安裝清單和快取符合已檢查的介面時才符合資格；快取結構不明時會保留不動。離線或假 CLI 檢查不等於已在 macOS、Linux 或 Windows 完成原生移除驗收。

每個所選套件都有自己的進度列，依序檢查目前狀態、執行原生命令，再確認已安裝檔案和版本。這些是已完成的階段，不代表下載百分比。每個套件的結果和訊息會放在同一區塊，套件之間留一行空白。為了驗證，安裝器會截取原生 JSON 命令結果，不會直接印出整段內容；原生權限或輸入提示會立即顯示在 stderr，stdin 則維持互動。失敗時若原生命令有提供錯誤訊息，安裝器會一併顯示，且不會自動重試。已由原生命令確認為 `up_to_date` 的結果會顯示為「已是最新版本」。

若同一個 Claude plugin 同時安裝在個人帳號和專案中，安裝器會保留兩份；這不會阻止其他無關套件繼續處理。安裝器不會自行挑一份來取代。只有在使用者範圍內存在一份已啟用且身分明確的安裝時，才會提供更新；副本關係不明時維持原樣。若確實無法讀取已安裝 plugin 清單，安裝器會指出受影響的 CLI，並在詢問更新或安裝前停止該 app 的流程；其他狀態正常的已選 CLI 可繼續。請保留畫面上的錯誤細節以便排查；移除現有 plugin 不能解決這類問題。

壓縮包會記錄本機 plugin 成品內容的精確雜湊和版本。marketplace 一旦變動，安裝器會先停止並要求檢視，不會拿過期的內容說明繼續安裝。原生安裝期間來源仍可能改變；安裝後檢查無法排除這個競態。不代表已完成原生驗收。

Codex 新安裝的驗證範圍限於已稽核的 CLI 0.167.0。安裝器會檢查原生 JSON 安裝回條、預覽中選定的 CODEX_HOME 設定／快取目標（預設為 `~/.codex`）、實際啟用狀態、manifest 版本及已安裝內容的精確雜湊。回條的 stdout 會被截取；原生 stderr 和 stdin 仍維持互動（stderr 會即時轉送）。快取版本和 manifest 版本會分開檢查。這不能證明專案或受管理設定的歸屬，也不能證明執行時的 skill 行為。既有項目會保留並標示為未驗證；不提供更新。未註冊的快取和含 symlink 的快取上層目錄也會保留。其他 Codex 版本尚待介面驗證。原生 Windows 偏好設定寫入／遷移目前仍需要 POSIX 鎖定；shell 工作流程需要另外提供所需工具。

Superpowers 使用各宿主的官方 catalog，兩邊版本不必相同：Claude 的 `claude-plugins-official`，觀察到的 manifest 版本為 `7.0.0`，指向固定在上游 Git commit `bb92a77741419a4ab5f06e711a283343f1ada0c3` 的 `https://github.com/obra/superpowers.git`；Codex 的 `openai-curated`，觀察到的 manifest 版本為 `6.3.0`，內容則位於其原生管理 catalog 裡的 `./plugins/superpowers`。此安裝包也能辨識使用 `.agents/plugins/api_marketplace.json` 的原生 `openai-api-curated`。安裝器會依原生清單判斷使用哪條路徑，不會根據模型 endpoint 網址或推測登入狀態。必須且只能辨識到一個官方 catalog。每個 catalog 都需要自己的精確原生驗收；一個 catalog 的證據不能替另一個背書。R5 的資料早於這項 adapter 修改和下方的能力紀錄。catalog 來源和 plugin 內容來源會分開檢查。任何既有 Superpowers 來源都會保留，即使版本較新、已停用或來自其他 catalog。

Codex 官方 catalog 必須先透過原生 `/plugins` 流程準備；一般 Git marketplace 新增或更新流程不能初始化這個受保留的 catalog。安裝器只讀取原生已準備好的 catalog 和 commit 回條。若原生清單沒有原始來源 URL，安裝器不會補寫；必須由 catalog 身分、路徑、commit、項目及內容來源證據共同確認其受管理來源。只有 Superpowers 的狀態缺少或不明確時，會暫停 Superpowers；若整體 plugin 清單讀取失敗，則停止受影響宿主的流程。

若同事透過公司 AI endpoint 使用 Codex，請保留既有的 `model_provider`、provider 的 `base_url`、認證環境變數及組織政策。安裝器不會要求 endpoint 網址、金鑰或登入。若 Codex 已提供 `openai-api-curated`，adapter 會檢查該 catalog；若尚未準備任何官方 catalog，請使用原生 `/plugins` 流程。安裝器不會啟動模型對話，也不會暗中初始化 catalog。能連公司模型 endpoint，不代表也能連 GitHub 或 plugin 下載來源。若下載來源被封鎖，或原生政策停用 plugins，安裝器會說明實際限制並請你聯絡管理員；它不會提供鏡像、proxy、略過憑證檢查或繞過政策的功能。公司 endpoint 是否連線成功，和 plugin 是否安裝成功是兩項不同檢查。

`provider-acceptance.json` 中只有兩筆附有已驗證內容雜湊的原生能力紀錄。只有下列組合會啟用自動提出的 Superpowers 安裝選項：

| 宿主／CLI | 平台／架構 | Catalog | 已測試的原生 manifest／帳號狀態 |
| --- | --- | --- | --- |
| Claude Code `2.1.322 (Claude Code)` | macOS arm64 | `claude-plugins-official` | 7.0.0；已登入和未登入 |
| Codex `codex-cli 0.167.0` | macOS arm64 | `openai-api-curated` | 6.3.0；未登入帳號，保留模擬的公司 provider 設定 |

兩份去除敏感資訊的來源摘要放在 `acceptance-evidence/`，每筆紀錄也會直接指向對應摘要。這些資料證明原生 CLI 的能力，不代表曾以這份 ZIP 執行原生安裝。Windows／Linux、其他架構或 CLI 版本，以及 Codex `openai-curated` 都沒有可沿用的驗收紀錄；在這些環境中，Superpowers 和依賴它的安裝選項會維持停用。其他符合資格的套件仍可繼續安裝。Claude 若使用不支援的 archive 格式 catalog，也會被保留並暫停；已驗證的情境使用原生 Git catalog。這裡沒有加入 archive 信任例外。

要啟用 Superpowers 安裝選項，宿主 CLI 版本、平台、架構、catalog、項目、manifest 版本及完整內容雜湊都必須完全符合。若歷史上的 catalog commit 改變，但已驗證的內容本身不變，不會單憑 commit 變更就停用；若使用者核准後觀察到來源再變更，該操作就會停止。Codex 原生快取版本必須等於目前 catalog SHA 的前八碼，並與 manifest 版本分開檢查。安裝器不會修復狀態或快取、不會重試，也不會回復。

安裝完成、重啟宿主後能否看到入口，以及七個工作流程的實際行為，是三種不同的驗證證據。只有 metadata 存在或合成測試成功，無法證明模型行為。repo 中的原生驗收及功能驗證提案，若要執行外部操作，必須另外取得核准。

Claude Code 2.1.322 在使用中的 plugin 快取會建立 `.in_use/<pid>` 檔案。安裝後驗證只會對這個精確 CLI 版本，辨識已檢查過的非執行檔一般檔案標記格式；其他不明標記、symlink、內容變更或額外檔案仍會使驗證失敗。catalog／來源雜湊不會改變，既有 session 標記也不會移除。其他 CLI 版本不適用這項例外。

可選的 `work-journal` 設定會把新的工作紀錄存到 `~/.agent-skills/activities`，除非已有 `CLAUDE_ACTIVITIES_DIR` 覆寫值。加入筆記資料夾後，`work-log-analyzer` 就能和工作紀錄一起搜尋你的筆記；筆記路徑可以先留空，之後再加入 `work-journal.json`。`report-generator` 也會使用這些資料製作報告。若已有有效設定，安裝器會顯示並沿用，不會詢問路徑或寫入；私人擴充欄位不會顯示。無效設定會保留並回報。只有在確認所選宿主安裝了相容版本的 work-journal runtime 後，才會建立含選用筆記路徑的新設定；舊版 runtime 必須先更新。若尚無設定，安裝器會先說明這些功能，再詢問是否加入選用的筆記資料夾，預覽設定與目錄變更，並要求另外核准。安裝器不會取代現有設定檔，也不會搬移或讀取活動紀錄／筆記內容。

安裝狀態、設定狀態和 hook 授權會分開回報。請檢查 `provenance.json`，確認來源版本與精確輸入／內容雜湊。壓縮包不含憑證或個人設定。
