# 設計修正紀錄

這份是 wayfinder-loops 早期從一份內部交接文件演進成可用系統時的修正紀錄:交接文件的設計拿到實際的 org 與 repo 上查證後,哪些地方不成立、改成了什麼。表格裡的 ticket 編號、repo 名稱與指令都是當時那個專案的,保留下來當歷史;現行規則以各 skill 與 `references/contract.md` 為準。

## 與交接文件的差異(全部來自地端查證,不是重新設計)

| # | 查到的事實 | 修正 |
|---|---|---|
| 1 | ~~wayfinder 會貼 `wayfinder:ticket`~~ **更正**:`wayfinder:ticket` 在 mattpocock-skills 規格裡**完全不存在**(全 repo grep = 0 次),是先前 session 自創的本地擴充,只有 backend 有、已用在 61 張 issue | 保留為**明示的本地擴充**(見下方 label 權威清單),frontend 一併補上以求兩 repo 一致;skill 不讀它,不影響相容性 |
| 2 | to-tickets SKILL.md 預設貼 `ready-for-agent`,不是 `agent:queued`;但寫明 "unless instructed otherwise" | 呼叫 /to-tickets 時要指示「改貼 `agent:queued`」;loop command 已寫入此 override |
| 3 | wayfinder SKILL.md 把「self-assign = claim」寫死("That assignee _is_ the claim") | 四個 command 檔都明文 override:claim 一律用 `agent:in-progress` label,assignee 只留給人類 |
| 4 | 所有 loop 共用你的帳號 → **無法用 comment 作者分辨人類** | 約定:loop comment 一律 `🤖 [loop名]` 開頭;無前綴 = 人類。Resolver 靠這個判斷「人類已出手」 |
| 5 | 交接文件自相矛盾:「map 只有 Cartographer 能寫」vs「Resolver 更新 map 的 Decisions so far」 | 採單一 writer:Resolver/Researcher/Implementer 只在 map 留 comment,Cartographer 每輪用 body 內 `<!-- folded-through: ... -->` 標記收斂 |
| 6 | Status 表沒定義 `agent:implement`(已升級未 claim)和 closed 的欄位 | Status 多兩個值:`🚀 可實作`、`✔️ 已關閉` |
| 7 | 文件的四條 loop 沒人負責 AFK 的 `wayfinder:task` | Researcher 兼收「明確可 AFK 執行」的 task;HITL task 仍歸人類/Resolver |
| 8 | 事件可能漏接(dependency 在 blocker 關掉之後才補上) | promote-queued 加 `workflow_dispatch` 手動重掃 |
| 9 | `ready-for-agent` / `needs-triage` 等是 mattpocock triage 詞彙(現役,不是舊系統) | 共存不動(你已裁定);新系統只讀寫 `wayfinder:*` / `agent:*` / `decision:*` |
| 10 | dependencies / sub-issue 的 REST 與 GraphQL 端點在 org 實測可用(backend #444 已有原生 blocker 與 parent) | workflow 直接用原生端點,無需 fallback |
| 11 | **frontend 缺 7 個 canonical label**:`needs-triage`、`needs-info`、`wayfinder:*` 全五個(但 `docs/agents/triage-labels.md` 已存在並宣告要用它們——設定跑過了,label 沒建) | setup-labels.sh 補齊 canonical triage 五角色 + wayfinder 五類型 |
| 12 | `ready-for-human` 與 `wayfinder:ticket` 在 backend 撞色(都是 `1D76DB`) | `wayfinder:ticket` 改 `0969DA` |
| 13 | `decision:discuss` 是非終止 label:原設計會讓 ticket 顯示成「已決定」,且 Resolver 每輪重新命中、重複回覆 | discuss 改門鈴語意:**Resolver 回覆後拔除**;Status 新增 `💬 討論中`(判斷順序在通用 `decision:*` 之前)。終止型 a/b/c/approve 關 ticket 後留著當紀錄 |
| 14 | `decision:*` label 只到 c,超過三個選項沒有對應操作 | 選項數紀律(cartographer.md):>3 先拆成兩層決策;攤平同儕選項照列 A–E 改用留言回覆;>5 先開 research 收斂 shortlist |
| 15 | 使用者含 PM/SA(非工程師):不知道功能歸前端還是後端、code repo 又有大量既有 backlog 筆記 issue 會被 intake 誤吞 | 新增 **`my-org/planning`** repo:想法/map/decision ticket 全住這裡,單一入口零判斷;implementation ticket 在 /to-tickets 階段才建到對的 code repo。Cartographer 只掃 planning,code repo 的 backlog 一張都不會被碰 |
| 16 | org 是 Free 方案,Auto-add workflow 可能只有一條;且原 sync 對「無 label 想法」「map」「task」算不出狀態,永遠不入板 | sync 補三個分支:planning 無管線 label → `💡 收件匣`、`wayfinder:map` → `🗺️ 規劃中`、`wayfinder:task` → 依 assignee 進 `⏳/🤖`。入板不再依賴 Auto-add;唯一的 Auto-add 給 planning 加速即可 |
| 17 | loop session 的 ctx 會隨輪數累積,主因是查證網頁、程式碼、建圖探索的殘渣留在對話裡 | **subagent dispatch 架構**:Researcher / Implementer 全面派工、Cartographer 的「接想法」與「spec/切 ticket」派工,loop 本體只做掃描、claim、驗收、回報;契約(🤖 前綴、claim 規則、禁令)必須寫進每個 subagent 的 prompt。Resolver 工作量小,維持 inline。派工後一律**核對實況不信自述**,subagent 死掉由 loop 本體善後拔 claim |
| 18 | 想要實作平行度時,**多開 implementer loop 會壞**:四條 loop 共用同一個 GitHub 帳號,`agent:in-progress` label 沒有內文可標記身分、timeline actor 也分不出來,兩條 loop 同時搶 ticket 會雙雙誤判搶到 → 同一張 ticket 實作兩次 | 平行度改由**單一 loop 內依序 claim + 平行派工**取得(K ≤ 3):`agent:implement` 依定義 blocker 全清,故互相獨立、天生可平行;上限 3 的理由是測試資源與人類 review 頻寬。另加**模型分級**:haiku(機械改動)/ sonnet(預設)/ opus(跨模組推理、動 contract、或 blocked 重試升級一次),上限 opus |
| 19 | 大 spec 的 integration branch 模式(session 2f4209c7 實證):PR 併進非預設分支時 `Closes #N` 不關 ticket → promote-queued 斷鏈;模式若靠人在對話中臨時指定,無人值守的 loop 只能猜 | **spec-train 契約**:/to-tickets 決定模式並寫在 ticket 上(body 第一行 `Integration-Branch: spec/<N>-<slug>`)+ 建 integration branch + 切 integrate-and-verify ticket;implementer 讀標記決定 base 與 Closes,每輪先「harvest」CI 綠的 batch PR(merge + **手動關 ticket** 以觸發 promote-queued;guardrail-gate 由最後 spec→main PR 把關)。人類唯一認證點 = spec→main 的 PR |
| 20 | Resolver 原本只認 label 為終止訊號:人類留言「decision:c」被歸為非終止型 → 回覆但不關 ticket、反覆要求貼 label(實測 #17/#18 卡住);且命中條件只看「最新一則 comment」,🤖 回過一次後就再也抓不到 | 分流改為**先判終止型**(label,或留言明確指名恰好一個選項/採用建議且無疑問無猶豫);終止型留言由 Resolver **轉錄成 `decision:*` label**(comment 必引用原句)再結案。命中條件改看「最後一則人類 comment」,補上漏接救援路徑。禁令收窄為「不替人決定」,轉錄除外 |
| 21 | 新 spec 切出的第一張 ticket 出生就 0 blocker,但 promote-queued 只聽 `issues.closed`——沒有 close 事件就永遠不升級,每份 spec 都會在起點停擺(實測 backend#503);另外 08-31 十幾張 ticket 同秒關閉時 promote 全部 failure(疑 secondary rate limit,log 已過期) | promote-queued 加聽 `issues.labeled`(僅 `agent:queued`),等 45 秒讓依賴串好再檢查;cartographer 契約補「`agent:queued` 必須是依賴串好後最後貼的 label」。`workflow_dispatch` 重掃仍是通用救援 |
| 22 | ticket-stream 預設(每張 ticket 各自 PR 進 main)讓每張 ticket 都變成人類停等點:planning#31 八張 ticket 要等四波 merge,和「人只認證一次」的目標相反;而且模式二選一讓 implementer 在讀不到標記時預設走 main,Cartographer 漏寫就靜默走錯 | **只保留 spec-train**:Cartographer 切 ticket 一律建 integration branch + 每張 ticket 首行 `Integration-Branch:` + integrate-and-verify ticket(首行同標記、次行 `Role: integrate-and-verify`);implementer 防呆 3 檢查標記,缺就 `agent:blocked` 退回,**絕不預設走 main**;PR 開完 `agent:in-progress` 保留到 harvest 關 ticket(看板顯示實作中)。**batch PR 不走 GitHub Actions**(ci.yml 刻意只對 main 觸發,人類的決定,不要改):實作 subagent 在本地跑 CI 對應指令(backend `uv run nox -s ci`、frontend `pnpm check`)+ `/code-review`,綠了把 PR 轉 ready;harvest 時再派 subagent 在本地把 PR 併到 integration branch HEAD 重跑一次,綠才 merge。GitHub CI 只在最後 spec→main 的 PR 跑一次 |
