# session-preferences 使用手冊

`session-preferences` 是一組手動啟用的 session 回應規則。它不會自己啟用，也不會改 global policy 或同步到其他 runtime。

## 啟用

```text
$session-preferences
```

看到「已啟用」後，規則從該刻套用到本 session 結束。開新 session 時需要再呼叫一次；這是對話中的指令，不是 runtime 的硬性開關。

## 新增規則

```text
$session-preferences add-deai 不要用「痛點」當成泛稱
$session-preferences add-rule 不要在簡單回答後硬給下一步
$session-preferences add-rule deai-voice: 避免重複同一種句尾
```

`add-deai` 會放進 `deai-voice`。省略類別時，agent 會先提議放置位置；不適合既有類別時，才提議新 module。每次都先顯示整理後的規則與目標檔案，只有你確認後才會寫入。確認寫入後，新規則立即套用到本 session 後續回應。

## 規則檔案

`references/INDEX.md` 列出目前生效的 modules。第一版包含：

- `control-return.md`：有真正需要時才提出三個可行下一步。
- `deai-voice.md`：通用、可分享的日常去 AI 味規則。

若 modules 的規則互相衝突，agent 會指出衝突讓你決定，不會自行挑一條覆蓋另一條。

## 不包含什麼

這個 skill 不複製 `deai-voice-rewrite` 的對外稿改寫流程、Tom 個人語氣或事實凍結 checklist。它也不會自動執行 `skill-sync`；同步是另一個需明確呼叫的動作。
