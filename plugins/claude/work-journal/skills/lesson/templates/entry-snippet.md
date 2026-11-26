## Lessons
- 開工第一個動作：執行 `{{SCRIPT}} digest`，並在第一則回覆開頭原樣帶出輸出的第一行。輸出的規則本 session 都要遵守。
- 遇到「踩坑修好」「假設被推翻」「被使用者糾正」時，在自然停頓點提議記錄，一次最多兩條，使用者確認才寫（流程見 /lesson）。
- 沒有 /lesson 可用時，把 JSON（rule、scope、project、why、background、slug）用標準輸入傳給 `{{SCRIPT}} add --json -` 寫入；rule 限一行、不超過 120 字。
