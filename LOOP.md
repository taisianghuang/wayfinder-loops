# LOOP.md — 你每天實際要做的事

系統跑起來之後,人類的日常只有三個動作。其他一切(開票、查證、寫 code、開 PR、
看板欄位)都是機器的事。

## 每天三個動作

### 1. 開看板,看最左邊那一欄

org Project board,最左欄是 **⏳ 等你決定**。那一欄有卡才需要你;空的就關掉。

### 2. 點進 issue,讀決策封包,點一個 label

每張等你決定的 ticket 都有一份決策封包(選項表 + 建議 + 決策樹)。讀完在
issue 右側 Labels 面板點一個:

| Label | 意思 |
|---|---|
| `decision:a` / `decision:b` / `decision:c` | 選 A / B / C |
| `decision:approve` | 採用 agent 的建議 |
| `decision:discuss` | 有疑慮,想聊(留言寫下疑慮) |

也可以直接留言——你的留言(沒有 `🤖 [` 開頭的)都會被 Resolver 當成人類發言處理。
選項超過 A/B/C 的票(封包裡會標成 A–E)就用留言回選項字母。

**點完 a/b/c/approve 就結束了**,Resolver 會在幾分鐘內記錄結論、關票、解鎖後續的票。
`discuss` 則會開始一段乒乓:票移到 **💬 討論中**(= agent 欠你一則回覆),Resolver
回覆後拔掉 label、票落回 **⏳ 等你決定**(= 你欠 agent 一個決定)。要繼續聊就再貼
一次 `discuss` 或直接留言;聊到發現整張票問錯問題,就把票 close as **not planned**,
Cartographer 會把它退回 map 的 fog 重新規劃。

### 3. Review「👀 待你 review」欄的 draft PR

每張實作票的 PR **不進 main**,而是進那份 spec 的整合分支 `spec/<N>-<slug>`。
CI 綠了 Implementer 會自己 merge、自己關票、自己解鎖下一批——這些 PR 不會出現在
「👀 待你 review」,你不用碰(看板上它們顯示「⚡ 實作中」)。

整份 spec 的票全部併完後,Implementer 會在整合分支跑全套測試,開**一個** spec→main
的 draft PR。這一個才會進「👀 待你 review」。
每張批次 PR 在收割前都先經過一個獨立的 reviewer agent:它直接 commit 修正、判斷這張是
單向門還是雙向門。spec→main PR 的 body 最上面會彙整成「審這裡」清單——只有列在那裡的
單向門(migration、權限、LINE 推播、ERP 寫回、API 契約)需要你細看,其餘可以快速掃過。
你 review 這一個、merge 這一個,spec 票就關了。一份 spec 只需要你動手一次。

## 丟新想法進系統

在 **`my-org/planning`** 開一張 issue,**什麼 label 都不用加**,把模糊的想法寫下來就好——
不用知道它歸前端還是後端,那是管線自己會回答的問題。Cartographer 下一輪會接手:
建 map、拆決策票、把第一批問題送到「等你決定」。

從看板丟也可以:「**+ Add item**」打完字後,對那張卡按 **convert to issue → 選 planning**
(Default repository 已設為 planning,通常直接按就對了)。
⚠️ 沒 convert 的 draft 只存在於看板上,機器永遠看不到它。

開好的想法會立刻出現在「**💡 收件匣**」欄——看到它在那裡就代表機器已收到,
Cartographer 下一輪會把它變成 map(移到「🗺️ 規劃中」)和第一批決策票。

code repo(backend / frontend)裡你自己的筆記 issue 不受影響——管線只認 planning。

## 給 PM / SA:你完全不需要離開 Project

1. **丟想法**:上面兩種方式擇一(建議直接在 planning 開 issue,手機 GitHub app 也行)
2. **做決策**:看板點卡片 → 右側面板會展開整張 issue → 讀決策封包 → 在面板的
   Labels 區點一個 `decision:*` → 關掉面板,結束
3. **有疑慮**:面板裡留言寫下疑慮 + 點 `decision:discuss`,agent 會回覆到同一張卡上

你需要的權限只有 planning repo(write)和這個 Project;code repo 完全不用碰。

## 啟動五條 loop(兩種模式擇一)

### 模式 B:每輪全新 session(headless,ctx 不累積)

`/loop` 的每一輪會累積在同一段對話裡;loop 是無狀態設計(狀態全在 GitHub),
所以也可以改用 wrapper 腳本,每一輪都開全新的 `claude -p` session、跑完即退:

```bash
~/wayfinder-loops/scripts/run-loop.sh resolver 600
~/wayfinder-loops/scripts/run-loop.sh cartographer 1200
~/wayfinder-loops/scripts/run-loop.sh researcher 900
```

代價:不能在 session 裡插話(要溝通就去 issue 上留言——本來就該這樣)、
headless 無法互動授權(腳本內建各 loop 的工具白名單)。
**implementer 與 prototyper 例外**:它們要寫程式、跑測試、發 Artifact 頁,權限列不完,
建議照模式 A 用互動式跑。log 在 `~/wayfinder-loops/logs/`。

### 模式 A:互動式 /loop(五個終端機,各一條)

```bash
cd ~/wayfinder-workspace && claude
```

(`~/wayfinder-workspace/` 是實驗場:code repo 的獨立 clone 都在裡面,implementer 只在
這裡面工作,不碰 home 下的日常工作區;整個資料夾刪掉即可重來。)

然後分別執行:

| 終端機 | 指令 | 節奏 |
|---|---|---|
| 1 | `/loop 10m /resolver` | 最勤——人類決定要立刻被消化 |
| 2 | `/loop 20m /cartographer` | 開票、收斂 map |
| 3 | `/loop 15m /researcher` | AFK 查證 |
| 4 | `/loop 15m /implementer` | 實作 + draft PR |
| 5 | `/loop 30m /prototyper` | 你說「畫」之後做原型,一輪一張 |

Resolver 必須跑得比 Cartographer 勤:新 fog 是票關掉之後才冒出來的。

Prototyper 可以最鬆:它只在你留了「先畫 V1」這種話之後才動,而且一輪一張票。

## 出狀況看哪裡

- **🚫 卡住** 欄位 = error flag。點進去看 `🤖 [...]` comment 寫的卡點。
- 每條 loop 每輪結束都會在終端機回報「還在等你的 HITL ticket 清單」——
  它催你,就是它在工作。
- 看板拖不動是特性不是 bug:欄位是從 issue label 算出來的,要改狀態就到
  issue 上操作(label / assignee / close)。
