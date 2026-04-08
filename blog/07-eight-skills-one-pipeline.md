# 8 個 Skills 串成一條管線

> *這是「當 AI 越來越好用，品質反而越來越差」系列的第 7 篇。*
> *這一篇講的是：為什麼單獨的 skills 不夠用，以及我怎麼把 8 個研究 skills 串成一條有紀律的管線。*

---

到第 6 篇為止，我已經有了好幾個獨立的研究工具：tech-feasibility 做可行性評估、assumption-extractor 挖出隱藏假設、micro-poc-validator 用真的 code 驗證、critical-research 先找反證、narrative-auditor 做事實查核、research-cross-validator 交叉比對。

每一個都解決了一個具體的問題。每一個都是從踩坑裡長出來的。

但我發現了一個新的問題：**有這麼多工具，我不知道什麼時候該用哪一個。**

---

## 做了研究，但做了錯誤的研究

有一次我在評估一個技術選型——具體的場景不重要，重要的是我的行為模式。

我先跑了 tech-feasibility，得到一份 Conditional-Go 的報告。看起來合理，我就準備往下做了。

但是上次的教訓告訴我要先找反證，所以我又跑了 critical-research。反證沒找到太致命的東西。好，那應該沒問題了吧？

問題是：tech-feasibility 報告裡有 12 個假設，其中 3 個是 CRITICAL。我沒有跑 assumption-extractor，所以我根本不知道有這些假設。我也沒有跑 micro-poc-validator，所以這 3 個 CRITICAL 假設全都是紙上談兵。

我用 AI 做了研究，但這是**不完整的研究**。

糟糕的是，因為我做了「一些」研究，我反而比完全沒做研究時更有信心——後來證實這份信心是虛假的。跑了兩個 skills 讓我覺得自己已經很嚴謹了，但我跳過了最關鍵的步驟：用真的 code 去驗證那些假設。

這個體驗貼近一個概念：**局部最佳化的陷阱**。每個 skill 在它的領域裡是最佳的，但如果你用錯順序、漏掉某個步驟，整體結果可能比什麼都不做更危險——因為你有了虛假的信心。

---

## ScraperAPI 的假如

這時候我又想起了第 2 篇講的 ScraperAPI 遷移。

那次的災難不是因為缺少工具，而是因為缺少**流程**。如果當時有一條這樣的管線，事情會完全不一樣：

Phase 0，brainstorming 先把範圍釐清：我們到底在決定什麼？是要遷移到 ScraperAPI 的結構化 API，還是要換到遠端瀏覽器方案，還是用 raw HTML 自己 parse？

Phase 1，tech-feasibility 做可行性評估。其中一個子假設：「nodriver 支援 WSS 連線」——標記為「不確定」。

Phase 2，assumption-extractor 把報告裡的假設全部挖出來。15 個假設，6 個 CRITICAL。其中 A-1：「nodriver 支援 WSS」——CRITICAL、未驗證、建議用 Micro-PoC 驗證。

Phase 3，micro-poc-validator 寫 5 分鐘的測試 code。結果：**FAIL**。nodriver 根本沒有 WSS 支援。

到這裡，管線就會停下來。不是因為我記得要停，而是因為管線的設計裡有一個叫 **Gate A** 的關卡：任何 BLOCKING 假設驗證失敗，管線就自動停止。

第 1 天就會發現的問題，我當時花了好幾天才遇到。

---

## Gate 的哲學

設計這條管線的時候，我花最多時間想的不是「要串哪些 skills」，而是「在哪裡放 Gate」。

Gate 不是 checkpoint。Checkpoint 是「到這裡了，看一下，繼續走」。Gate 是「到這裡了，如果條件不滿足，**不准走**」。

管線裡有兩個 Gate：

**Gate A** 在 Phase 3（Micro-PoC）之後。問的問題是：**BLOCKING 假設都驗證通過了嗎？**

如果任何一個 BLOCKING 假設失敗，管線停止。不是「記錄一下然後繼續」，是停止。你要跟我討論：是要 pivot 到另一個方案，還是修改假設重新跑。

這很反直覺。你已經花了時間跑完 Phase 0 到 Phase 3，sunk cost 的心理壓力很大。但 Gate A 的設計原則是：**已經花掉的時間不是繼續的理由。** 如果地基是錯的，上面蓋什麼都會倒。

**Gate B** 在 Phase 6（Cross-Validation）之後。問的問題不一樣：**各個 Phase 的發現是否收斂？**

到了 Gate B，你已經有了 feasibility 報告、假設驗證結果、反證搜尋、自我審計、交叉驗證——五六個不同角度的發現。Gate B 檢查的是：這些發現有沒有在講同一件事？還是有矛盾？

如果有重大矛盾——比如 Phase 1 說「Go」但 Phase 4 找到了嚴重的反證——管線不會幫你解決矛盾，它會把矛盾攤在你面前，讓你做決定。

兩個 Gate，兩種不同的風險：Gate A 防的是「建在錯誤假設上」，Gate B 防的是「忽略矛盾的證據」。

---

## 所以我造了這個

`tech-research-pipeline` 是一個 orchestrator skill——它自己不做研究，它指揮其他 skills 做研究。

完整的管線是 8 個 Phase：

```
Phase 0: brainstorming         → 範圍定義
Phase 1: tech-feasibility      → 可行性評估
Phase 2: assumption-extractor  → 假設清單
Phase 3: micro-poc-validator   → 實證驗證
        ─── Gate A ───
Phase 4: critical-research     → 反證搜尋
Phase 5: narrative-auditor     → 自我審計
Phase 6: research-cross-validator → 交叉驗證
        ─── Gate B ───
Phase 7: research-synthesis    → 決策文件
```

每個 Phase 的輸出是下一個 Phase 的輸入。Phase 2 從 Phase 1 的報告裡挖出假設；Phase 3 拿 Phase 2 的 CRITICAL 假設去驗證；Phase 4 拿 Phase 0 的方案去找反證。不是平行跑，是序列的——每一步都建立在前一步的結果上。

最後一個 Phase，`research-synthesis`，做的事情不只是把結果整理在一起。它要做的是**解決矛盾**。如果 Phase 1 說 Go 但 Phase 4 找到了反證，synthesis 不能假裝矛盾不存在——它必須說清楚哪一邊的證據更強、為什麼，然後給出一個有根據的建議。

每個建議都必須回溯到具體的 Phase。不能說「經過研究，建議用方案 A」，要說「Phase 3 驗證了核心假設（PASS），Phase 4 的反證搜尋沒有找到致命問題，Phase 6 交叉驗證確認了 3/4 的關鍵主張——建議 Go」。

這叫 **evidence traceability**——每個結論都能追溯到產生它的證據。

---

## 不是每次都需要跑完

完整管線要 60-120 分鐘。不是每個決定都值得花這麼多時間。

所以管線有一個 abbreviated mode：跳過 Phase 5（自我審計）和 Phase 6（交叉驗證），從 Phase 4 直接跳到 Phase 7。大概 30-60 分鐘。

判斷標準很簡單：**做錯了的代價是什麼？**

如果做錯了要返工兩個月，跑完整管線。如果做錯了最多浪費一天，用 abbreviated 或者根本不用管線，直接跑單個 skill 就好。

工具的價值不在於你永遠使用它，而在於你在對的時機使用它。

---

## 帶走一件事

如果你已經有了幾個獨立的 AI 工作流程——不管是研究、review、還是別的——問自己一個問題：

**這些 skills 之間有沒有一個「正確」的順序？如果有，你有沒有把這個順序記下來？**

單獨的工具解決單獨的問題。但真正的品質來自工具之間的**銜接**——前一步的輸出成為後一步的輸入，中間的 Gate 決定要不要繼續走。

不需要一開始就有 8 個 Phase。從「先做 A，再做 B，如果 B 失敗就停下來」開始，你就已經有了一條管線。

---

`#AISkills旅程` `#ClaudeCode` `#AI工程紀律` `#ResearchPipeline` `#GateDesign` `#EvidenceTraceability`
