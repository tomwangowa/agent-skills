# 當 benchmark 翻轉了預設 reviewer

> *這是「當 AI 越來越好用，品質反而越來越差」系列的第 16 篇——上一篇原本是最後一篇，這篇算是番外。*
> *講的是：四個月前我把 code review 的預設交給 Gemini，昨天一場 6 語言的 benchmark 把它翻了過來。*

---

上一篇我說系列要收尾了。這篇算番外。

起因是這樣：這週要在組內分享一個 code review 的 demo。我想做一件看似簡單的事——拿同一段程式碼、6 種語言的 retry client，分別讓 `/code-review-gemini` 和 `/code-review-claude` 跑一遍，把差異整理出來當投影片素材。

原本預期會是：Gemini 一如往常挑得比較深、Claude Native 快但少一些細節。結論是老調「各有用場」，分享的價值大概是示範「兩種工具怎麼搭配」。

結果不是這樣。

---

## 四個月前的劇本

先把脈絡倒回去。

第 3 篇我寫過 `code-review-gemini` 的誕生：Claude Code 自己寫的 code 自己 review，會往「合理」的方向解讀；讓另一個模型來挑剔，才會看到原本看不到的盲點。那時我跑過幾組比較，結論很明確——Gemini 挑毛病的力道遠超 Claude 的自我審視。所以我把 pre-commit auto-review 的預設交給了它。

後來我也做了 `/code-review-claude`。不是因為它品質比較好，是因為它夠快——30 秒以內跑完，適合改一行 typo 或加個 log 的場景。50 行以下用 Claude Native，再多就切 Gemini。這個分工撐了四個月。

中間我給兩個 skill 都加了 adversarial pass——不只列問題，還要問「這段程式在假設什麼沒被驗證過？」「What breaks this？」。加完之後兩邊品質都往上走，但我注意力其實一直在 Gemini 那邊。它是預設、它是主力、它理論上也比較該被調教。

---

## 昨天那場 benchmark

這次分享要做 demo，我就把 6 種語言的 retry client 各丟給兩個 skill 跑一次——Java、TypeScript、PHP、JavaScript、Python、Shell。沒特別挑極端 case，就是我平常會寫的那種 50–120 行的東西。

跑到 Python 那份的時候我愣了一下。

Gemini 把不存在的問題標成 P0：「第 13 行 `@dataclass` 前多了一個空格，會直接引發 `IndentationError`，程式完全無法執行。」

實際上那行在 line 14，沒有任何 leading space。我用 `python3 -c "import ast; ast.parse(...)"` 驗了一下，語法完全 OK。

這不是「找得不夠多」的問題。這是**自信地指向一個不存在的嚴重錯誤**的問題——如果我是那個被 review 的工程師，又剛好沒多想，就會把正常的 `@dataclass` 改掉。改出來的那個 diff 才會真的有問題。

往回翻前幾份 review 結果，我發現 TypeScript 那份也有一次類似的——Gemini 聲稱 email regex `[^\s@]+` 裡面有多餘空白，要求「移除」。實際那個 regex 完全正確，它只是把字元類別 `\s` 的意思讀錯了。

做完最後一份 Shell 之後，第三次出現。Gemini 聲稱 `"$@"` 被寫成 `"$ @"`，列為高優先級語法錯誤。`bash -n` 當然沒抱怨，因為原檔根本沒有那個空格。

三次誤判，都發生在**視覺上容易看錯的字元細節**：regex 字元類別、前導空白、參數展開。都被標為高優先級。都會讓盲信的人去改壞可以運作的程式碼。

---

## 翻過去看數字

我把 6 份 review 結果攤開來數：

| Demo | 檔案 | Claude 發現 | Gemini 發現 | 比例 | Gemini 誤判 |
|---|---|---:|---:|:---:|:---:|
| 1 | Java 59 行 | 15 | 6 | 2.5× | — |
| 2 | TSX 118 行 | 14 | 4 | 3.5× | email regex |
| 3 | PHP 65 行 | 14 | 6 | 2.3× | — |
| 4 | JS 68 行 | 15 | 6 | 2.5× | — |
| 5 | Python 56 行 | 16 | 6 | 2.7× | @dataclass |
| 6 | Shell 53 行 | 20 | 4 | 5.0× | `"$@"` |

Claude 的覆蓋面穩定是 Gemini 的 2.3–5.0 倍。Gemini 在 3 份裡出現 P0/P1 級 hallucination，而且規律高度相似——都在「視覺上容易誤讀的字元」。Claude 的 adversarial pass 在動態型別和 shell-like 語言（Python、JS、Shell）多抓了 3–15 個靜默 bug 場景，例如：

- `body` 傳 `bytes`（protobuf 或 binary upload）時，`isinstance(body, dict)` 和 `isinstance(body, str)` 都 False，body 被靜默丟掉。伺服器收到空請求，**沒有例外、沒有警告**。
- `max_retries=-1` 時 loop 不執行，最後拋出「Failed after 0 attempts. Last error: None」誤導呼叫端。
- shell 版的 `curl ... && true` 會把 curl 的 failure 吞掉，exit code 永遠是 0，retry 邏輯形同失效。

這些不是找碴級的發現。是會在實際系統跑出奇怪行為、而且不會立刻被捕獲的 bug。

Gemini 還是有它獨到的優勢——它會產出完整的 refactored patch，含像 `retry_status_codes` 白名單這種乾淨的重構設計。但**那份 patch 要逐行對照原檔驗證**，因為它可能基於誤判的前提。

---

## 做什麼決定

看完 6 份結果，決定很清楚：把預設翻過來。

- 日常 review、pre-commit auto-review 都改走 `code-review-claude`
- 想要完整 refactored patch 或外部第二意見時，才串 `code-review-gemini`
- `pr-review-assistant`（團隊 PR 層級 review）也跟著翻——現在預設走 Claude native，Gemini 是選配的深度 path

今天花了大半天把 repo 裡所有文件的 cross-reference 同步改了：3 個 README（中英繁各一）、2 份 cheatsheet、skill-router 的 workflow、docs/Meta-Skills-Pattern、pr-review-assistant 重構成 hybrid 架構。不是什麼壯觀的改動——就是把原本寫「Gemini 是預設、Claude 是快速備援」的 18 個檔案，翻成「Claude 是預設、Gemini 是深度選配」。

中間 pre-commit 的 code review 抓到我自己漏的 bug：我在 7 處寫了 `--deep` 和 `--gemini` 這兩個根本不存在的 CLI flag，聽起來很像「有這個 feature」但其實 `scripts/review_pr.sh` 只收 PR 編號。要不是 review 抓到，讀文件的人照著打下去會直接報錯。這個修正後來也併進同一個 commit 了。

---

## 為什麼當初是 Gemini 領先

我沒有太多能完全確定的解釋。有幾個觀察值得記下來：

- **四個月前那批 benchmark 是怎麼跑的，我現在想不起來細節。** 有可能當時的 case 剛好對 Gemini 比較有利；有可能當時 Claude Native 還沒加 adversarial pass；也有可能兩邊模型都進化了但步調不一樣。
- **adversarial pass 加給 Claude Native 之後，覆蓋面的優勢變得很明顯。** 它不只找變數命名、缺 null check，還會問「這段在假設什麼」。這種問題原本只有 Gemini 問得出來。
- **Syntax-level hallucination 是 Gemini 目前比較嚴重的失敗模式。** 特別是視覺上容易混淆的字元——regex 字元類別、前導空白、不可見字元。這類 false positive 特別昂貴，因為它們通常被標成 P0/P1，使用者被引導去改的是**本來正確的程式碼**。

這幾點加起來，兩個 skill 在 2026-04 這個時間點的相對位置，確實跟四個月前不一樣了。這個 n=6 benchmark 當然不是「universal proof」——它只是 HTTP retry client 這一類程式碼。換成資料庫 migration 或 UI 渲染邏輯，結果可能不同。所以我沒把 Gemini 刪掉，只是把它從預設路徑上移開，留在「想要 refactored patch 或外部視角」的選配位置。

---

## 帶走一件事

如果你的工作流裡有一個定期跑的 AI 工具——翻譯、審稿、review、research——**至少每三個月找幾組代表性的輸入重跑一次，對比結果。**

模型在更新、prompt 在演化、你自己的 skill 定義也在演化。四個月前的勝負，不代表今天的勝負。你以為還很好用的東西，可能已經不是最好的選項了。

昨天那場 benchmark 我本來是為了 demo 跑的。跑出來的不是簡報材料——是一個「喔，預設該翻過來」的訊號。

benchmark 不是為了證明你當初的選擇是對的。是為了知道它現在還對不對。

---

`#AISkills旅程` `#ClaudeCode` `#AI工程紀律` `#CodeReview` `#Benchmark` `#WorkflowDesign`
