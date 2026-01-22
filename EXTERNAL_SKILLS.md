# External Skills Management

本 repository 使用 symlinks 來整合外部技能集，避免直接提交第三方代碼。

## 目前整合的外部技能源

### Superpowers Skills
- **來源**: `/Users/tom_wang/Development/3rdparty/superpowers/skills`
- **前綴**: `sp-`
- **範例**: `sp-brainstorming`, `sp-systematic-debugging`

## 使用方法

### 建立 Symlinks

```bash
./manage_external_skills.sh link
```

### 移除 Symlinks

```bash
./manage_external_skills.sh unlink
```

### 檢查狀態

```bash
./manage_external_skills.sh status
```

## 架構說明

```
~/.claude/skills/
├── activity-logger/           # 自己的技能
├── code-review-gemini/        # 自己的技能
├── sp-brainstorming/          # symlink -> superpowers
├── sp-systematic-debugging/   # symlink -> superpowers
└── ...
```

## 注意事項

### ✅ 優點
- 避免代碼重複
- 自動同步上游更新
- 版本控制保持乾淨
- 清楚區分自有/外部技能

### ⚠️ 限制
- **路徑依賴**: symlinks 依賴特定路徑，其他機器需要相同設定
- **更新風險**: 上游變更可能影響現有工作流程
- **斷鏈風險**: 如果來源目錄移動，symlinks 會失效

### 🔒 安全建議
- 定期審查外部技能的更新
- 確保來源可信
- 在使用前測試新的外部技能

## 在其他機器上設定

如果你在其他機器上使用這個 repository：

1. Clone superpowers skills 到相同路徑：
   ```bash
   mkdir -p ~/Development/3rdparty
   cd ~/Development/3rdparty
   git clone [superpowers-repo-url] superpowers
   ```

2. 建立 symlinks：
   ```bash
   cd ~/.claude/skills
   ./manage_external_skills.sh link
   ```

## 疑難排解

### Broken Symlinks
如果 symlinks 斷掉（顯示紅色或無法訪問）：

```bash
# 檢查狀態
./manage_external_skills.sh status

# 重新建立
./manage_external_skills.sh unlink
./manage_external_skills.sh link
```

### 名稱衝突
如果有技能名稱衝突，symlink 會自動跳過。你可以：
- 重新命名你自己的技能
- 或修改 `manage_external_skills.sh` 中的 `PREFIX` 變數
