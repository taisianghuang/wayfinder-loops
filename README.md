# wayfinder-loops kit

wayfinder + GitHub Issues + 多 session `/loop` 自動化的完整交付物。
對應雲端交接文件第 7 節,並依地端查證結果修正(見下方差異表)。

**三個 repo,兩個世界:**

```
my-org/planning              💡想法 → map → 決策票     ← PM/SA 的唯一入口
                                        │ /to-spec → /to-tickets
                                        ▼(這時才決定前端/後端)
my-org/api  實作票(agent:queued)→ PR  ← 工程師/機器的世界
my-org/web
```

PM/SA 只需要 planning 的權限,在 Project 看板的側邊面板就能完成所有決策操作;
code repo 既有的 backlog 筆記 issue 完全不受管線影響(Cartographer 只掃 planning)。

```
wayfinder-loops/
├── README.md                     ← 本檔:安裝步驟 + 與交接文件的差異
├── LOOP.md                       ← 人類日常操作(裝完後照這份過日子)
├── scripts/
│   └── setup-labels.sh           ← 三個 repo 建齊所有 label(冪等)
├── workflows/                    ← 複製到三個 repo 的 .github/workflows/
│   ├── promote-queued.yml        ← blocker 清空 → agent:queued 升級 agent:implement
│   ├── sync-project-status.yml   ← label/assignee/PR → Project Status(唯一 writer)
│   └── dispatch-on-decision.yml  ← decision:* → repository_dispatch(hook point)
├── commands/                     ← 審完後複製到 ~/.claude/commands/
│   ├── cartographer.md
│   ├── resolver.md
│   ├── researcher.md
│   └── implementer.md
└── templates/
    └── decision-packet.md
```

---

## 與交接文件的差異(全部來自地端查證,不是重新設計)

| # | 查到的事實 | 修正 |
|---|---|---|
| 1 | ~~wayfinder 會貼 `wayfinder:ticket`~~ **更正**:`wayfinder:ticket` 在 mattpocock-skills 規格裡**完全不存在**(全 repo grep = 0 次),是先前 session 自創的本地擴充,只有 backend 有、已用在 61 張 issue | 保留為**明示的本地擴充**(見下方 label 權威清單),frontend 一併補上以求兩 repo 一致;skill 不讀它,不影響相容性 |
| 2 | to-tickets SKILL.md 預設貼 `ready-for-agent`,不是 `agent:queued`;但寫明 "unless instructed otherwise" | 呼叫 /to-tickets 時要指示「改貼 `agent:queued`」;loop command 已寫入此 override |
| 3 | wayfinder SKILL.md 把「self-assign = 認領」寫死("That assignee _is_ the claim") | 四個 command 檔都明文 override:認領一律用 `agent:in-progress` label,assignee 只留給人類 |
| 4 | 所有 loop 共用你的帳號 → **無法用 comment 作者分辨人類** | 約定:loop comment 一律 `🤖 [loop名]` 開頭;無前綴 = 人類。Resolver 靠這個判斷「人類已出手」 |
| 5 | 交接文件自相矛盾:「map 只有 Cartographer 能寫」vs「Resolver 更新 map 的 Decisions so far」 | 採單一 writer:Resolver/Researcher/Implementer 只在 map 留 comment,Cartographer 每輪用 body 內 `<!-- folded-through: ... -->` 標記收斂 |
| 6 | Status 表沒定義 `agent:implement`(已升級未認領)和 closed 的欄位 | Status 多兩個值:`🚀 可實作`、`✔️ 已關閉` |
| 7 | 文件的四條 loop 沒人負責 AFK 的 `wayfinder:task` | Researcher 兼收「明確可 AFK 執行」的 task;HITL task 仍歸人類/Resolver |
| 8 | 事件可能漏接(dependency 在 blocker 關掉之後才補上) | promote-queued 加 `workflow_dispatch` 手動重掃 |
| 9 | `ready-for-agent` / `needs-triage` 等是 mattpocock triage 詞彙(現役,不是舊系統) | 共存不動(你已裁定);新系統只讀寫 `wayfinder:*` / `agent:*` / `decision:*` |
| 10 | dependencies / sub-issue 的 REST 與 GraphQL 端點在 org 實測可用(backend #444 已有原生 blocker 與 parent) | workflow 直接用原生端點,無需 fallback |
| 11 | **frontend 缺 7 個 canonical label**:`needs-triage`、`needs-info`、`wayfinder:*` 全五個(但 `docs/agents/triage-labels.md` 已存在並宣告要用它們——設定跑過了,label 沒建) | setup-labels.sh 補齊 canonical triage 五角色 + wayfinder 五類型 |
| 12 | `ready-for-human` 與 `wayfinder:ticket` 在 backend 撞色(都是 `1D76DB`) | `wayfinder:ticket` 改 `0969DA` |
| 13 | `decision:discuss` 是非終止 label:原設計會讓票顯示成「已決定」,且 Resolver 每輪重新命中、重複回覆 | discuss 改門鈴語意:**Resolver 回覆後拔除**;Status 新增 `💬 討論中`(判斷順序在通用 `decision:*` 之前)。終止型 a/b/c/approve 關票後留著當紀錄 |
| 14 | `decision:*` label 只到 c,超過三個選項沒有對應操作 | 選項數紀律(cartographer.md):>3 先拆成兩層決策;攤平同儕選項照列 A–E 改用留言回覆;>5 先開 research 收斂 shortlist |
| 15 | 使用者含 PM/SA(非工程師):不知道功能歸前端還是後端、code repo 又有大量既有 backlog 筆記 issue 會被 intake 誤吞 | 新增 **`my-org/planning`** repo:想法/map/決策票全住這裡,單一入口零判斷;實作票在 /to-tickets 階段才建到對的 code repo。Cartographer 只掃 planning,code repo 的 backlog 一張都不會被碰 |
| 16 | org 是 Free 方案,Auto-add workflow 可能只有一條;且原 sync 對「無 label 想法」「map」「task」算不出狀態,永遠不入板 | sync 補三個分支:planning 無管線 label → `💡 收件匣`、`wayfinder:map` → `🗺️ 規劃中`、`wayfinder:task` → 依 assignee 進 `⏳/🤖`。入板不再依賴 Auto-add;唯一的 Auto-add 給 planning 加速即可 |
| 17 | loop session 的 ctx 會隨輪數累積,主因是查證網頁、程式碼、建圖探索的殘渣留在對話裡 | **subagent dispatch 架構**:Researcher / Implementer 全面派工、Cartographer 的「接想法」與「spec/切票」派工,loop 本體只做掃描、認領、驗收、回報;契約(🤖 前綴、認領規則、禁令)必須寫進每個 subagent 的 prompt。Resolver 工作量小,維持 inline。派工後一律**核對實況不信自述**,subagent 死掉由 loop 本體善後拔 claim |
| 18 | 想要實作平行度時,**多開 implementer loop 會壞**:四條 loop 共用同一個 GitHub 帳號,`agent:in-progress` label 沒有內文可標記身分、timeline actor 也分不出來,兩條 loop 同時搶票會雙雙誤判搶到 → 同票實作兩次 | 平行度改由**單一 loop 內依序認領 + 平行派工**取得(K ≤ 3):`agent:implement` 依定義 blocker 全清,故互相獨立、天生可平行;上限 3 的理由是測試資源與人類 review 頻寬。另加**模型分級**:haiku(機械改動)/ sonnet(預設)/ opus(跨模組推理、動 contract、或 blocked 重試升級一次),上限 opus |
| 19 | 大 spec 的整合分支模式(session 2f4209c7 實證):PR 併進非預設分支時 `Closes #N` 不關票 → promote-queued 斷鏈;模式若靠人在對話中臨時指定,無人值守的 loop 只能猜 | **spec-train 契約**:/to-tickets 決定模式並寫在票上(body 第一行 `Integration-Branch: spec/<N>-<slug>`)+ 建整合分支 + 切 integrate-and-verify 票;implementer 讀標記決定 base 與 Closes,每輪先「收割」CI 綠的批次 PR(merge + **手動關票**以觸發 promote-queued;guardrail-gate 由最後 spec→main PR 把關)。人類唯一認證點 = spec→main 的 PR |
| 20 | Resolver 原本只認 label 為終止訊號:人類留言「decision:c」被歸為非終止型 → 回覆但不關票、反覆要求貼 label(實測 #17/#18 卡住);且命中條件只看「最新一則 comment」,🤖 回過一次後就再也抓不到 | 分流改為**先判終止型**(label,或留言明確指名恰好一個選項/採用建議且無疑問無猶豫);終止型留言由 Resolver **轉錄成 `decision:*` label**(comment 必引用原句)再結案。命中條件改看「最後一則人類 comment」,補上漏接救援路徑。禁令收窄為「不替人決定」,轉錄除外 |
| 21 | 新 spec 切出的第一張票出生就 0 blocker,但 promote-queued 只聽 `issues.closed`——沒有 close 事件就永遠不升級,每份 spec 都會在起點停擺(實測 backend#503);另外 08-31 十幾張票同秒關閉時 promote 全部 failure(疑 secondary rate limit,log 已過期) | promote-queued 加聽 `issues.labeled`(僅 `agent:queued`),等 45 秒讓依賴串好再檢查;cartographer 契約補「`agent:queued` 必須是依賴串好後最後貼的 label」。`workflow_dispatch` 重掃仍是通用救援 |
| 22 | ticket-stream 預設(每票各自 PR 進 main)讓每張票都變成人類停等點:planning#31 八張票要等四波 merge,和「人只認證一次」的目標相反;而且模式二選一讓 implementer 在讀不到標記時預設走 main,Cartographer 漏寫就靜默走錯 | **只保留 spec-train**:Cartographer 切票一律建整合分支 + 每張票首行 `Integration-Branch:` + integrate-and-verify 票(首行同標記、次行 `Role: integrate-and-verify`);implementer 防呆 3 檢查標記,缺就 `agent:blocked` 退回,**絕不預設走 main**;PR 開完 `agent:in-progress` 保留到收割關票(看板顯示實作中)。**批次 PR 不走 GitHub Actions**(ci.yml 刻意只對 main 觸發,人類的決定,不要改):實作 subagent 在本地跑 CI 對應指令(backend `uv run nox -s ci`、frontend `pnpm check`)+ `/code-review`,綠了把 PR 轉 ready;收割時再派 subagent 在本地把 PR 併到整合分支 HEAD 重跑一次,綠才 merge。GitHub CI 只在最後 spec→main 的 PR 跑一次 |

---

## Label 權威清單(以 mattpocock-skills 為準)

**canonical —— skill 自己會讀寫的,共 10 個。**
可改字串,但要同步改 repo 內 `docs/agents/triage-labels.md` 的右欄(你兩個 repo 目前都是預設值,左右欄相同)。

| Label | writer | 出處 |
|---|---|---|
| `needs-triage` / `needs-info` / `ready-for-agent` / `ready-for-human` / `wontfix` | triage skill、to-spec、to-tickets | `setup-matt-pocock-skills/triage-labels.md`(五角色) |
| `wayfinder:map` | wayfinder | `wayfinder/SKILL.md:21` |
| `wayfinder:research` / `wayfinder:prototype` / `wayfinder:grilling` / `wayfinder:task` | wayfinder | `wayfinder/SKILL.md:65`(`wayfinder:<type>`) |

**非 canonical —— skill 從不讀,純粹是我們自己的。**

| Label | writer | 用途 |
|---|---|---|
| `wayfinder:ticket` | wayfinder(需在 command 裡指示) | 本地擴充:一次撈出所有決策票,不必分四型查 |
| `agent:queued` / `agent:implement` / `agent:in-progress` / `agent:blocked` | 升級 workflow / loop | 實作管線位置 |
| `decision:a` / `b` / `c` / `approve` / `discuss` | 人 | 人類的決定 |
| `tech-debt` / `arch-audit` / `guardrail-approved` / `in-progress` | 你既有的流程 | 與本系統無關,共存不動 |

---

## 安裝步驟

### 0. 前置(只有你能做,各一次)

```bash
sudo apt install -y gh
```
(2.85.0 → 2.96.0;`--parent` / `--blocked-by` 等 flag 需要 ≥ 2.94)

```bash
gh auth refresh -h github.com -s project
```
(現有 token 沒有 `project` scope,建 org Project 和本機除錯都需要)

### 1. 建 label

```bash
bash ~/wayfinder-loops/scripts/setup-labels.sh
```

### 2. 建 org Project

1. https://github.com/orgs/my-org/projects → New project → Board
2. **Status 欄位改成這 13 個值**(順序即看板欄位順序,「等你決定」最左):
   `⏳ 等你決定`,`🔍 準備選項中`,`💬 討論中`,`💡 收件匣`,`🗺️ 規劃中`,`🤖 查證中`,`✅ 已決定,待收斂`,`📋 排隊中`,`🚀 可實作`,`⚡ 實作中`,`👀 待你 review`,`🚫 卡住`,`✔️ 已關閉`
   ※ 名稱要**逐字一致**(含 emoji 和空格),sync workflow 是用字串比對的。
   ※ `💡 收件匣` = planning 上還沒有管線 label 的新想法;`🗺️ 規劃中` = map 本體(配 Sub-issues progress 看進度)。
3. 欄位加上:**Sub-issues progress**(原生)、**Assignees**、**Repository**
4. Views 只開兩個:Board(日常)、Table 按 parent issue 分組(看全貌)
5. Project 右上 **Workflows** → **Auto-add to project**:repo 選 `planning`,filter 填 `is:issue`,Save and turn on。能 Duplicate 就再給兩個 code repo 各一條(Free 方案可能限一條——**沒關係**,code repo 的票出生就帶 label,sync workflow 的 `addProjectV2ItemById` 會自動入板;planning 的無 label 想法也有 sync 的 `💡 收件匣` fallback 兜底,auto-add 是加速不是必要)
6. 記下 Project URL(如 `https://github.com/orgs/my-org/projects/3`)

### 3. 設 secrets / vars(三個 repo 都要)

1. 建一顆 classic PAT,scope 勾 `project` + `repo`(https://github.com/settings/tokens)
2. 三個 repo 各設:
   - Settings → Secrets → Actions → `PROJECT_TOKEN` = 那顆 PAT
   - Settings → Variables → Actions → `PROJECT_URL` = Project URL
3. `ORG_AUTOMATION_TOKEN` secret(classic PAT,`repo` scope):planning 架構下**必要**——決策票關在 planning、被解鎖的實作票在 code repo,promote-queued 的跨 repo 寫入靠它(可以和 `PROJECT_TOKEN` 用同一顆,scope 已涵蓋)

### 4. 部署 workflows

把 `workflows/` 三個檔案複製到**三個 repo** 的 `.github/workflows/`(planning 直接 push 即可,code repo 開 branch 走 PR 合入)。
(不會和既有的 ci / guardrail-gate / doc-coupling-advice / react-doctor 撞名)

**不要動 code repo 的 `ci.yml`**:它刻意只對 base 是 `main` 的 PR 觸發。spec-train 的批次 PR 靠 implementer 在本地跑 CI 對應指令驗證,GitHub Actions 只在最後 spec→main 的 PR 跑一次。

### 5. 部署 loop commands(審完再做)

```bash
cp ~/wayfinder-loops/commands/*.md ~/.claude/commands/
```

※ cartographer.md 引用 `~/wayfinder-loops/templates/decision-packet.md`,kit 目錄搬家的話記得改路徑。

### 6. frontend 的 mattpocock 前置

**不用重跑 `/setup-matt-pocock-skills`** —— frontend 的 `docs/agents/`
(`issue-tracker.md` / `triage-labels.md` / `domain.md` / `adr-governance.md`)都已存在,
設定跑過了。缺的只是 GitHub 上的 label 本體(7 個),步驟 1 的 setup-labels.sh 已補齊。

### 7. 冒煙測試(強烈建議)

1. 在 planning 開一張測試 issue,寫一個小的模糊想法
2. 手動跑一輪 `/cartographer` → 應該長出 map + 決策票 + 你被 assign + 看板出現在「等你決定」
3. 對決策票貼 `decision:approve` → 手動跑 `/resolver` → 票被關、map 收到 comment
4. 都通了再照 [LOOP.md](LOOP.md) 常駐四條 loop

---

## 日常操作

見 [LOOP.md](LOOP.md)。

## 不變式(健檢用)

- 任何 loop、任何 workflow 都**不准讀 Project Status 做判斷**;判斷一律讀 label
- 每個 label 只有一個 writer(見 setup-labels.sh 內的描述)
- map body 只有 Cartographer 寫
- HITL ticket 沒有人類新動作 → 所有 loop 對它 no-op;**永不 timeout auto-approve**
- sub-issue 永不自動升級成實作票
- 實作票的 PR base 永遠是 `spec/*` 整合分支;**人類只 merge spec→main 的 PR**。任何 base 是 main 的 `implement/*` PR 都是契約違規
- 批次 PR 的驗證在本地(nox / pnpm check + /code-review),不靠 GitHub Actions;GitHub CI 只在 spec→main 跑。loop 不改 `.github/workflows/`
