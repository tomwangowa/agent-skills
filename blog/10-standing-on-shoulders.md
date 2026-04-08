# 站在別人肩膀上

> *這是「當 AI 越來越好用，品質反而越來越差」系列的第 10 篇。*
> *這一篇講的是：什麼時候自己造 skill，什麼時候用別人的。*

---

第 5 篇提過，我的 brainstorming skill 是從一個叫 [superpowers](https://github.com/obra/superpowers) 的開源專案改來的。那篇只是順便提了一下出處。這篇要講的是背後更大的問題：我 32 個 skills 裡面，有多少是從零開始造的？

答案是：不到一半。

---

## 我的 sp-* 系列

我的 skill 清單裡有一整排 `sp-` 開頭的 skills：

- `sp-systematic-debugging`：遇到 bug 時的結構化除錯流程
- `sp-test-driven-development`：先寫測試再寫實作
- `sp-writing-plans`：寫實作計畫
- `sp-executing-plans`：執行計畫搭配 review checkpoint
- `sp-requesting-code-review`：完成功能後請求 review
- `sp-receiving-code-review`：收到 review 後怎麼處理
- `sp-dispatching-parallel-agents`：把獨立任務分給平行 agent
- `sp-finishing-a-development-branch`：完成分支時的收尾流程
- `sp-using-git-worktrees`：用 git worktree 做隔離開發

這些全部來自 superpowers。我沒有自己發明這些工作流程——我引入了別人已經想好的行為規範，然後整合到我自己的體系裡。

---

## 為什麼不自己造？

不是因為我造不出來。而是因為我沒有「看見」這些問題。

拿 `sp-receiving-code-review` 來說。這個 skill 規定：收到 code review 的回饋時，不要無條件接受，要先驗證回饋的技術正確性。

我以前的做法是：reviewer 說什麼就改什麼。不是因為我沒有判斷力，而是因為 review 的社交壓力讓我傾向於快速配合。AI 做 code review 的時候這個問題更嚴重——AI 給了 10 條建議，我的本能是全部接受，因為「它分析過了，應該是對的」。

但 superpowers 的設計者顯然踩過這個坑。他們把「不要盲目接受 review」寫成了一個明確的行為規範。我看到的時候才意識到：對，這確實是一個問題，而我一直沒有把它當成問題。

這就是借別人東西的價值：**你看不見的盲區，別人可能已經解決了。**

---

## 什麼時候自己造

但我不是全盤照搬 superpowers。我的 32 個 skills 裡有很多是自己造的：

- `tech-feasibility`、`assumption-extractor`、`micro-poc-validator`——因為 ScraperAPI 的踩坑經驗是我自己的，解法也要針對我自己的問題
- `critical-research`、`narrative-auditor`、`research-cross-validator`——因為 falsification-first 的研究方法是我在自己的工作中發展出來的
- `role-orchestrator`、`role-pm`、`role-rd`——因為多角色系統的需求來自我一個人同時做 PM 和 RD 的處境
- `activity-logger`、`work-log-analyzer`——因為跨 session 記憶斷裂是我每天都在面對的問題
- `skill-router`、`skill-auditor`——因為 skill 太多找不到是我自己造成的 meta 問題

規律是這樣的：**如果問題是通用的（怎麼除錯、怎麼寫計畫、怎麼做 code review），先看別人有沒有解。如果問題是你自己特有的（你的工作流程、你的踩坑經驗、你的組織脈絡），那就自己造。**

通用問題自己造，是在重新發明輪子。特有問題套用別人的，是在削足適履。

---

## 引入不是複製貼上

我從 superpowers 引入 sp-* skills 的時候，不是原封不動地用。我做了幾件事：

第一，**整合到我的路由系統裡。** superpowers 有自己的觸發機制（`sp-using-superpowers` 這個 skill 本身就是一個路由器），但我有自己的 CLAUDE.md 路由規則。我把 sp-* 的觸發條件寫進我的 CLAUDE.md，讓它們跟我自己造的 skills 走同一套路由邏輯。

第二，**跟我自己的 skills 串接。** 比如 `sp-writing-plans` 產出的計畫可以直接交給 `sp-executing-plans` 執行，而 `sp-executing-plans` 裡面用到的 code review 步驟會觸發我自己的 `code-review-gemini`。superpowers 的 skills 和我自己的 skills 不是兩套平行系統，而是同一條管線裡的不同零件。

第三，**我改了一些我不認同的設計。** brainstorming 就是最明顯的例子——第 5 篇講過，我以 superpowers 的版本為基礎重寫了自己的版本，加入了「一次只問一個問題」和「優先用選擇題」的規則。

引入別人的東西不代表放棄判斷。它代表**你選擇了一個更好的起點**。

---

## 帶走一件事

下次你想在 AI 工作流程裡加一個新的環節，先搞清楚：

**有沒有人已經解決了這個問題？**

GitHub 上有越來越多 Claude Code skills、Cursor rules、AI workflow 的開源專案。花些時間瀏覽一下，可能省你 3 天的摸索。

但記得：引入之後要整合，不是堆疊。10 個零散的外部 skills 加上 10 個你自己的 skills，如果沒有統一的路由和串接，那只是 20 個互相不認識的工具——跟第 7 篇講的問題一模一樣。

---

`#AISkills旅程` `#ClaudeCode` `#AI工程紀律` `#BuildVsBorrow` `#OpenSource` `#Superpowers`
