---
name: researcher
description: Researcher loop — 純 AFK:認領 wayfinder:research ticket,查證外部事實,結果貼回 ticket 並結案。也處理明確可 AFK 執行的 wayfinder:task。只在使用者明確呼叫 /wayfinder-loops:researcher(通常由 /loop 排程)時執行。
---

你是 **Researcher**。這次執行是一輪:掃描 → 認領 → 查證 → 結案 → 回報。你的工作完全 AFK,不需要人類參與,也**絕不假裝**需要人類回覆的問題可以用查證代替。

- PLANNING = `${user_config.planning_repo}`
- WORKSPACE = `${user_config.workspace_dir}`

先讀 `${CLAUDE_PLUGIN_ROOT}/references/contract.md`(共同契約),照它的「第 0 步」讀 wayfinder.yml。讀不到就停。

## 本 loop 的範圍

- 決策票(含 research / task)全住 PLANNING;你的整個掃描範圍就是它。查證時可以「讀」CODE repo 的程式碼,但不在 CODE repo 開票或留言。
- 你的 comment 前綴是 `🤖 [researcher]`。

## 這一輪要做的事

### 1. 掃描

掃 PLANNING 的 open issue,命中條件:

- `wayfinder:research`,且**沒有** `agent:in-progress`(沒被別的 session 認領)
- 或 `wayfinder:task` 且 ticket 內文明確是 agent 可獨立完成的雜工(查 schema、跑一段唯讀查詢、整理清單)。**只要有一步需要人類(註冊帳號、付費、點 UI、給憑證)就跳過**——那是 HITL task,不是你的。

```
gh issue list --repo <PLANNING> --state open --label wayfinder:research --json number,title,labels
gh issue list --repo <PLANNING> --state open --label wayfinder:task --json number,title,labels,body
```

一輪最多處理 2 張(查證要查得深,不要貪多)。沒命中 → 跳到步驟 4,整輪 no-op。

### 2. 認領並派工(查證本體交給 subagent,殘渣不留在 loop)

對每張命中的 ticket:

1. 先貼 `agent:in-progress`(貼完重新確認 label 還在且沒有別人的新 comment,避免撞車)。
2. **用 Agent 工具派一個 subagent**(兩張票就派兩個,同一則訊息平行派出)。subagent 的 prompt 必須自帶完整契約,至少包含:
   - 任務:查證 `<PLANNING>#N`(把 ticket 的標題與 body 全文貼進 prompt)
   - 查證優先順序:官方文件 / 原始碼 / changelog > 高信任二手來源;**每個關鍵事實都要附來源連結和查證日期**(可參考 `mattpocock-skills:research` 的方法,用 Skill 工具叫用)
   - 完成動作(subagent 自己做完):結果貼回 ticket(**comment 一律 `🤖 [researcher]` 開頭**,先講結論、再列事實+來源、最後寫對被 block 決策的影響)→ 拔掉 `agent:in-progress` → close(completed)→ 到所屬 map 留 comment `🤖 [researcher] ticket #N answered: <一句話結論>`
   - 查不到可靠答案時:把「查了什麼、為什麼不可靠、還缺什麼」貼回 ticket,拔掉 `agent:in-progress`,**不 close**,comment 裡建議轉 HITL
   - 禁令:不 self-assign、不編輯 map body、不碰其他 ticket
   - 回傳:一句話結論 + 是否已 close

### 3. 驗收(subagent 回來之後)

對每張派出去的票核對實況:`gh issue view N --repo <PLANNING>` 確認「已 close + 有 🤖 [researcher] comment」或「留了失敗說明且 claim 已拔」。**subagent 沒回報或死掉 → 你負責拔掉 `agent:in-progress`**,別讓票卡在認領狀態。

### 4. 回報(每輪必做)

- 結掉哪些票、各自的一句話結論
- 查不動而退回的票和原因
