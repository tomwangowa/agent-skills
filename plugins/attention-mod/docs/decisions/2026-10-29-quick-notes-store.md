# 決策：Quick Notes 用 $.store 保存，key 以 git 共用目錄為準

日期：2026-10-29  
狀態：Tom 於 2026-10-29 確認設計（見 `docs/superpowers/specs/2026-10-29-attention-mod-tab-pages-design.md`）。目標版本 0.6.0，已實作，實機手動檢查（第 9 項）尚未完成。

## 脈絡

面板要新增 Quick Notes 頁，讓使用者記下臨時文字，跨啟動保留，並依專案分開。

現有的不變條件寫明「不用 store、檔案、http」。跨啟動保留的需求只有插件自己的存檔空間（`$.store`）能滿足，檔案寫入會碰到路徑與權限問題，而且同樣違反不變條件。所以這條規則要改，改動範圍只限 Quick Notes 文字。

專案的劃分方式有兩種：

- 以 cwd（目前目錄）為 key：每個 worktree 各自一份。這個專案常用 worktree，使用者在主 checkout 寫的內容，在功能 worktree 看不到。
- 以 git 共用目錄為 key：同一個 repo 的所有 worktree 共用一份。代價是 key 依賴工作樹讀取的時序，而且要在 `worktree.js` 多保留一個欄位。

## 決策

- 只有 Quick Notes 文字寫入 `$.store`。觀察資料（提示、工具結果、摘要）仍不寫入 store、檔案或 http。
- key：有 git 時為 `notes:<git 共用目錄>`；不在 git 裡時為 `notes-cwd:<目錄>`。
- 讀不到就不寫。讀取失敗時不寫入，避免空白內容蓋掉已存的筆記。
- 每份上限 32,768 個 code point。超過就不存。
- 文字清空時呼叫 `$.store.delete`。
- 頁碼規則與 `collapsed` 相同：跨 `/clear` 與 resume 保留，只有插件 reload 才重設。

## 後果

- `CLAUDE.md` 的不變條件與 calls inventory 要改寫，這是實作的一部分。
- `$.store` 是整個插件共用的空間，超過 4 MiB 會拒絕寫入，因此需要單份上限。
- key 含有絕對路徑，只存在使用者本機，不進 repo。
- 沒有刪除單份筆記的介面。使用者只能清空文字。

## 驗證

已查證：型別檔（2.1.312）確認 `$.store` 的語意與 4 MiB 上限；探針確認跨重啟保留。

尚未驗證：key 依賴的讀取時序在實際 `cd` 後的表現；`$.store.set` 失敗時面板的顯示，要在實作的手動檢查中確認。
