# Design: Skill Journey Blog Series

> Date: 2026-04-07
> Status: Approved

## Overview

將 32 個 Claude Code skills 的開發旅程寫成系列 blog 文章，發布於公司內部個人 blog。

## 讀者與目標

- **主要讀者**：工程師，少數跨職能（PM、設計師、主管）
- **目標**：激發行動（「我也想試」）+ 改變認知（「原來可以這樣想」）
- **發文節奏**：不定期，每篇獨立可讀
- **案例**：可具體講真實專案，不需脫敏
- **規模**：15 篇完整系列（第一幕 4 篇 + 第二幕 7 篇 + 第三幕 4 篇）
- **風格**：故事敘事帶入 + 關鍵處切技術細節，語調偏軟、對話感

## 系列命名

**系列名**：當 AI 越來越好用，品質反而越來越差

**Tagline**：一個工程師用 3 個月造了 32 個 AI skills 的故事——以及為什麼最重要的不是 AI 能做什麼，而是你不讓它做什麼。

**每篇定位句**（固定出現在文章開頭）：
> *這是「當 AI 越來越好用，品質反而越來越差」系列的第 N 篇。這一篇講的是：[一句話定位]*

## Hashtags

- **固定（每篇）**：`#AISkills旅程` `#ClaudeCode` `#AI工程紀律`
- **浮動（依主題選 2-3 個）**：`#CodeReview` `#TDD` `#ResearchPipeline` `#DualAIReview` `#FalsificationFirst` `#PromptEngineering` `#AIProductivity` 等
- **風格**：混合——概念用中文、技術名詞用英文

## 三幕結構

### 第一幕「踩坑」— 4 篇

核心問題：*為什麼你需要管 AI？*

| # | 暫定標題 | 核心故事 | 涉及 Skills |
|---|---------|---------|-------------|
| 1 | 當我開始信任 AI，事情開始出錯 | 系列開場。AI 產出品質隨信任增加下降的真實體驗。 | 開場總論 |
| 2 | 那份看起來很完整的可行性報告 | ScraperAPI 遷移踩坑。nodriver 不支援 WSS 的教訓。 | tech-feasibility, assumption-extractor, micro-poc-validator |
| 3 | AI Review 自己的 Code，會發生什麼事？ | 讓 Claude review 自己寫的 code 的災難——過度合理化。 | code-review-gemini, code-review-claude |
| 4 | 「測試通過了」——真的嗎？ | 沒跑測試就說通過的案例。Evidence before assertion 的起點。 | completion-gate |

### 第二幕「長出體系」— 7 篇

核心問題：*從單點修補到系統性思維的轉折*

| # | 暫定標題 | 核心理念 | 涉及 Skills |
|---|---------|---------|-------------|
| 5 | 想清楚再動手 | AI 太快動手的問題。蘇格拉底式對話，先探索需求再設計。 | brainstorming |
| 6 | 先找反證，再找支持 | Falsification-first。對確認偏誤的系統性防禦。 | critical-research, narrative-auditor, research-cross-validator |
| 7 | 8 個 Skills 串成一條管線 | Research pipeline。Gate A / Gate B 的設計。 | tech-research-pipeline, research-synthesis |
| 8 | 當 AI 開始扮演你的 PM 和 RD | 多 Agent 角色系統。subagent + project profile 校準。 | role-orchestrator, role-pm, role-rd |
| 9 | AI 失憶症 | 跨 session 記憶斷裂。怎麼讓工作脈絡不斷線。 | activity-logger, work-log-analyzer |
| 10 | 站在別人肩膀上 | 什麼時候自己造、什麼時候借別人的。sp-* 整合的工程判斷。 | sp-* 系列 (superpowers) |
| 11 | 32 個 Skills 之後，我找不到該用哪一個 | Meta 問題：skills 太多時的導航。 | skill-router, skill-auditor, skillshare |

### 第三幕「質變」— 4 篇

核心問題：*這一切帶來了什麼改變？你也可以。*

| # | 暫定標題 | 切入點 | 涉及 Skills |
|---|---------|-------|-------------|
| 12 | 同一個任務，有紀律 vs 沒紀律 | Before/after 對照。兩條路線完整走一遍。 | 視場景而定 |
| 13 | 不只是 Prompt Engineering | 觀念翻轉。真正的槓桿在 workflow design。 | 全系列回顧 |
| 14 | 從第 0 個到第 1 個：你的 AI Skill 行動指南 | 給讀者的起步指南。找到你自己的第一個痛點。 | sp-writing-skills, skill-auditor |
| 15 | （選寫）三個月後回頭看 | 回顧。哪些每天在用、哪些用不到。 | 全系列回顧 |

## sp-* Skills 出處說明

涉及 `sp-*` 前綴 skills 的篇章（主要為第 10、12、14 篇）需明確說明這些來自 [superpowers](https://github.com/obra/superpowers) 開源專案，是外部引入的行為規範，非自行開發。第 10 篇「站在別人肩膀上」以此為主題，專門探討自己造 vs. 借別人的工程判斷。

## 單篇文章模板

```markdown
# [文章標題]

> *這是「當 AI 越來越好用，品質反而越來越差」系列的第 N 篇。
> 這一篇講的是：[一句話定位]*

---

## 故事（800-1200 字）
敘事帶入。從具體場景、對話、或踩坑開始。
有情緒、有轉折、有頓悟點。
語調偏軟，像跟同事分享經驗。

## 所以我造了這個（500-800 字）
技術切入。介紹 1-3 個 skills 的設計邏輯。
可以有 code snippets、SKILL.md 片段、使用範例。
重點是「為什麼這樣設計」而非 API 文件。

## 帶走一件事
3-5 句話收束。
一個可以立刻行動的建議，或一個改變思考方式的觀點。

---

[固定 hashtags] [浮動 hashtags]
```

## 語氣基調

- 對話式口吻，像在跟同事分享觀察
- 問句引導節奏，特別適合段落開頭
- 具體案例錨定，每個論點有人名、產品、數據支撐
- 坦誠面對不確定，保留探索空間
- 段落短、呼吸快，一段一觀點
- 偏軟，不教條

## 發文順序

```
必須先寫：第 1 篇（系列 hook，定調）
     ↓
第一幕任意順序：第 2、3、4 篇（建議 2 先寫，ScraperAPI 故事最有張力）
     ↓
第二幕任意順序：第 5-11 篇（建議 5 先寫，brainstorming 最貼近日常體驗）
     ↓
第三幕建議順序：12 → 13 → 14 → 15（收束需要有序）
```

## 執行策略

- 先寫完第 1、2 篇就發，看同事反應。Hook 有效，後面的動力自然來。
- 可搭配 `code-story-teller` 回溯特定 skill 的 git 演化歷史作為素材。
- 可搭配 `activity-logger` / `work-log-analyzer` 撈出當時的工作紀錄補充細節。
- 每篇可用 Claude Code 協助起草，但最終文字風格要是自己的聲音。

## 未被分配到的 Skills

newsletter-digest, presentation-planner, interactive-presentation-generator, ui-design-analyzer, qa-to-notes, report-generator, ai-weekly-insight, arxiv-digest, deep-reading, code-story-teller, pr-review-assistant 等可在相關篇章中以配角出現，不需每個都有專屬篇幅。
