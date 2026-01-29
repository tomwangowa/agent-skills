# quality-driven-dev

以資深架構師思維執行開發，強調測試先行、深度上下文分析與防禦性編程，確保代碼的高質量與可維護性。

## Overview

**Complexity Level**: complex
**Estimated Tokens**: 1394

## Complexity Factors

- MCP integration required
- Multi-step sub-skills required
- Additional resources required

## Structure

```
quality-driven-dev/
├── SKILL.md          # Main skill definition
├── README.md         # This file
├── sub-skills/       # Multi-step sub-skills
└── resources/        # MCP configuration
    └── mcp-config.json
```

## Getting Started

### Prerequisites

1. **Context7 MCP Server**（必須）
   - 安裝並配置 Context7 MCP server
   - 確認 `~/.claude/mcp-config.json` 包含 context7 配置

2. **開發環境**（建議）
   - 已安裝測試框架（Jest, pytest, etc.）
   - 已配置 linter 與 formatter
   - Git 已初始化並配置

### 快速開始步驟

1. **啟用 Skill**
   ```
   使用高質量開發模式實作使用者認證功能
   ```

2. **查看輸出**
   - [Context Analysis]：確認技術文檔查詢結果
   - [Test Plan]：審查測試案例是否完整
   - [Implementation Strategy]：確認實作策略符合需求

3. **執行代碼**
   - 複製 [Code Block] 中的測試代碼
   - 執行測試（應該失敗 - Red phase）
   - 複製實作代碼
   - 執行測試（應該通過 - Green phase）

4. **自我審查**
   - 使用 [Review Checklist] 逐項檢查
   - 確認所有項目都打勾

### 範例工作流程

```bash
# 1. 觸發 skill
> 使用高質量開發模式實作 POST /api/users API

# 2. 檢視生成的測試
# 複製測試代碼到 tests/users.test.js

# 3. 運行測試（應該失敗）
npm test

# 4. 複製實作代碼到 routes/users.js

# 5. 運行測試（應該通過）
npm test

# 6. 自我審查
# 確認 Review Checklist 所有項目
```

## TODO: Implementation Checklist

### MCP Setup

- [x] Configure MCP tool: context7
- [ ] Test MCP connection

### Sub-Skills

- [ ] Implement sub-skill: Context Acquisition
- [ ] Implement sub-skill: Planning & TDD
- [ ] Implement sub-skill: Implementation
- [ ] Implement sub-skill: Self-Review & Validation
- [ ] Test multi-step workflow

## Usage

1. Complete all TODO items above
2. Test the skill with sample inputs
3. Deploy to Claude Code skills directory

## Notes

This skill was generated automatically. Review and customize as needed.
