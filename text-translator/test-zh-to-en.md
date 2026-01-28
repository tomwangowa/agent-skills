## 測試文件：繁中轉英文

這是測試用的技術文件。

### 功能說明

使用 REST API 處理請求：

```javascript
async function fetchData() {
  const response = await fetch('/api/data');
  return response.json();
}
```

主要特點：
- 使用 `async/await` 語法
- 支援 JSON 格式
- 包含錯誤處理

| 參數 | 類型 | 說明 |
|------|------|------|
| `url` | string | API 端點 |
| `method` | string | HTTP 方法 |

> **注意：** 確保 API 端點使用 HTTPS。
