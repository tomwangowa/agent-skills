# 32 個 Skills 之後，我找不到該用哪一個

> *這是「當 AI 越來越好用，品質反而越來越差」系列的第 11 篇，也是第二幕「長出體系」的最後一篇。*
> *這一篇講的是：當你的工具箱太滿，工具箱本身就變成了問題。*

---

前面 10 篇講了我怎麼從踩坑開始，一步一步長出一套 skill 體系。tech-feasibility、critical-research、brainstorming、research pipeline、role system、activity logger⋯⋯每一個都解決了一個真實的問題。

然後我遇到了一個新的問題：**我不記得自己有哪些 skills 了。**

---

## 工具箱太滿

32 個 skills。我認真數過。

有些我每天在用（brainstorming、code-review-gemini、completion-gate）。有些我偶爾用（tech-research-pipeline、role-orchestrator）。有些我造好之後幾乎沒用過——不是因為它不好，而是因為我忘了它存在。

最荒謬的一次：我手動做了一件事，做完之後才想起來我有一個 skill 就是專門做這件事的。我造了工具然後忘記用，用人工完成了工具本來該自動化的事。

這不是記憶力的問題。這是**數量的問題**。人腦能隨時記住的東西大概就 7 個左右。32 個 skills，每個有不同的觸發條件和使用場景，我不可能全部記在腦子裡。

---

## CLAUDE.md 路由的極限

第 5 篇講過，我用 CLAUDE.md 做 skill 路由：遇到 bug 觸發 debugging、新功能觸發 brainstorming、完成功能觸發 completion-gate。

這在 skills 數量少的時候很好用。但到了 32 個，我的 CLAUDE.md 路由表變得又長又難維護。有些 skills 的觸發條件重疊（tech-feasibility 和 tech-research-pipeline 什麼時候該用哪個？）。有些 skills 我根本忘了加路由規則。

更大的問題是：CLAUDE.md 路由是**被動的**。它只在特定條件觸發時才會啟動。但如果我不知道有某個 skill 存在，我就不會觸發它的條件——因為我根本不會做那個動作。

我需要的不只是路由，而是**發現機制**。

---

## 所以我造了這個

`skill-router` 是一個 meta skill——它不做任何具體的工作，它幫你找到該做這件工作的 skill。

它有三種模式：

**Smart Routing**：你描述你的需求，它從 registry 裡找最匹配的 skill。比如你說「我想評估一個技術方案」，它會推薦 tech-feasibility（單一問題）或 tech-research-pipeline（複雜決定），並解釋差別。

**Category Browse**：列出所有 skills，按分類整理。這是我自己最常用的模式——不是因為我不知道要做什麼，而是因為我想確認「有沒有什麼我忘了」。

**Workflow Browse**：列出預設的工作流程。比如「新功能開發」的流程是 brainstorming → role-pm → role-rd → superpowers:writing-plans → superpowers:executing-plans。你不需要記住每一步，router 會告訴你下一步是什麼。

---

## 品質控管：skill-auditor

skill 多了之後還有另一個問題：品質參差不齊。

我早期造的 skills 寫得比較粗糙——沒有安全考量、沒有錯誤處理、路徑是 hardcode 的。後期造的比較嚴謹，但誰來確保一致性？

`skill-auditor` 做的事情是：拿到一個 SKILL.md，用一套標準去審核它。有沒有安全考量？有沒有錯誤處理？路徑是不是可攜的？文件夠不夠清楚？

它不是只找問題，而是打分數——100 分制，安全佔 30%、錯誤處理佔 20%、文件品質佔 20%⋯⋯。這讓我可以快速看出哪些 skills 需要回頭改善。

我在 CLAUDE.md 裡加了一條規則：每次建立或修改 skill 之後，必須跑 skill-auditor。這讓品質檢查變成流程的一部分，而不是事後想到才做的事。

---

## 跨工具同步：skillshare

最後一個 meta 問題來自教學場景。我在公司內部開了 skill workshop，教同事怎麼寫自己的 AI skills。但不是每個人都用 Claude Code——有人用 Cursor，有人用 Windsurf。

我總不能叫每個學員手動把 skill 複製到自己工具的對應目錄吧。後來找到了 [skillshare](https://github.com/runkids/skillshare) 這個開源工具——它從一個 source of truth 把 skills 同步到不同的 AI CLI 工具。

一份 skill 寫好，跑一次 sync，Claude Code、Cursor、Windsurf 都更新。學員不用管「我的工具把 skill 放在哪個目錄」，skillshare 幫你搞定。又是一個站在別人肩膀上的例子。

---

## Meta 問題的啟示

回頭看，我造的這幾個 skills（router、auditor）以及開源工具 skillshare 有一個共同點：**它們解決的不是工作上的問題，而是 skill 體系本身的問題。**

- 找不到該用哪個 skill → 造 router
- skill 品質不一致 → 造 auditor
- skill 散在不同工具裡 → 造 skillshare

這代表什麼？當一個系統長到一定規模，它就會開始需要**管理自己的工具**。這不是 AI skills 特有的現象——任何工具鏈、任何基礎設施、任何團隊的流程，長到一定程度都會遇到同樣的問題。

第二幕到這裡結束。從第 5 篇的「想清楚再動手」到第 11 篇的「管理工具的工具」，這 7 篇講的是一個體系從單點修補到系統性思維的成長過程。

---

## 帶走一件事

如果你開始覺得「我有太多 AI 工具 / prompts / rules 但不知道什麼時候該用哪一個」——恭喜，你遇到了一個好問題。這代表你的體系正在長大。

解法不是減少工具。是**加一層導航**。

可以是一個列表、一個路由表、或一個查詢機制。形式不重要，重要的是：讓你（和你的 AI）在需要的時候能找到對的工具。

我自己也為我的 skill set 做了兩個 Cheatsheets（中文版和英文版），方便快速查詢每個 skill 的用途和觸發時機。

---

`#AISkills旅程` `#ClaudeCode` `#AI工程紀律` `#SkillRouter` `#MetaTooling` `#SystemDesign`
