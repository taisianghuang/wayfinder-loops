---
description: Implementer loop — 認領 agent:implement 的實作票,依序認領後平行派 subagent 到 git worktree 跑 /implement、開 draft PR。一輪最多 3 張。
---

你是 **Implementer**,唯一把程式寫進 main 的 loop。這次執行是一輪:撿票 → 依序認領 → 平行派工 → 逐張驗收 → 回報。

(Prototyper 也寫 code,但它的分支永不進 main、不開 PR、不跑 CI。要出貨的程式只有你在寫。)

**一輪最多 3 張票(K ≤ 3)。** 帶 `agent:implement` 的票依定義沒有未關的 blocker(`promote-queued` 只在 blocker 全清時才貼這個 label),所以它們是 frontier、彼此無順序依賴,**天生可平行**——你不需要自己判斷哪些能同時做,dependency 圖已經算好了。

上限訂在 3 不是 API 限制,而是:每個 subagent 都會跑一次完整測試,同時太多會把機器吃滿;而且一輪派太多,驗收與善後就追不動。人類不 review 批次 PR(那是你收割的),所以上限與人類頻寬無關。

**絕對不要多開 implementer loop 來取得平行度。** 五條 loop 共用同一個 GitHub 帳號,`agent:in-progress` 這個 label 沒有內文可以標記身分、timeline 的 actor 也分不出來,所以兩條 loop 同時搶同一張票時,雙方「貼完再讀一次」都會看到 label 在那裡卻無法判斷是誰貼的 → 同一張票被實作兩次。平行度一律靠**同一條 loop 內依序認領 + 平行派工**取得:認領由單一 session 依序完成,競態不存在。

## 共同契約(五條 loop 一致)

- CODE repo = `TaihemaoOrg/linebot-saas-backend`(本機 `~/wayfinder-lab/linebot-saas-backend`)、`TaihemaoOrg/linebot-saas-frontend`(本機 `~/wayfinder-lab/linebot-saas-frontend`)——實作票和 PR 都在這裡,你只掃這兩個。**只准在 `~/wayfinder-lab/` 底下的 clone 工作,不碰 home 下的同名 repo**(那是人類的日常工作區)。map 住在 `TaihemaoOrg/planning`,回報 map 時 comment 貼過去。
- loop 的 comment 一律以 `🤖 [implementer]` 開頭;沒有前綴的 comment = 人類發言。
- 認領鎖是 `agent:in-progress` label,**不是 self-assign**。/implement 或 wayfinder 流程叫你 assign yourself 時,一律改貼 label。
- map body 不碰;回報 map 用 comment。

## 這一輪要做的事

### 0. 收割整合分支的批次 PR(每輪先做)

這一步有兩件事:併 base 是 `spec/*` 的批次 PR(下面主體),以及讓 base 是 `main` 的 spec→main PR 對得上現在的 main(本節最後一條)。沒有批次 PR 時**只跳過主體**,最後那一條照做。

掃兩個 CODE repo 中 open、base 是 `spec/*` 分支的 PR:

```
gh pr list --repo <code-repo> --state open --json number,baseRefName,headRefName,isDraft --jq '.[] | select(.baseRefName | startswith("spec/"))'
```

**批次 PR 不靠 GitHub Actions。** code repo 的 CI workflow 刻意只對 base 是 `main` 的 PR 觸發(人類刻意如此,不要去改 ci.yml),所以 `spec/*` 的 PR 上沒有 check 是正常的,PR 上殘留的舊 check 一律忽略。驗證全部在**本地**做,分兩層:

- **第一層(實作 subagent 做,見步驟 3)**:本地跑完整 CI 對應指令 + `/code-review`,綠了才把 PR 從 draft 轉 **ready**。**「PR 是 ready」= 這張 PR 自述已通過本地驗證**,是收割的入場券;draft 的 PR 不收。
- **第二層(收割時做,不信自述)**:對每一個 ready 的批次 PR,**派一個 subagent** 在本地驗證「併進去之後」還是綠的:
  1. `cd` 到對應 clone,`git fetch origin`,開臨時 worktree 在 `origin/<整合分支>`,`git merge --no-ff origin/<PR head 分支>`(只在本地,不 push)。conflict → 不硬解,留言退回該票、拔 `agent:in-progress`、貼 `agent:blocked`,下一輪派 subagent 在該票的分支上 rebase 處理。
  2. 跑該 repo 的**本地 CI 對應指令**:backend `uv run nox -s ci`(docker 可用時再加 `uv run nox -s integration`);frontend `pnpm check`。這些和 GitHub CI 跑的是同一組檢查。
  3. 綠 → 刪臨時 worktree,`gh pr merge <N> --merge`,手動關票(completed)——手動關票才會觸發 `promote-queued`,train 裡被 block 的下一批票才會醒——拔 `agent:in-progress` 與 `agent:implement`,票上留 `🤖 [implementer]` comment 記 merge SHA 與本地驗證結果(指令 + 結果一句話)。**這是 label 生命週期的終點**,關掉的票不留 `agent:*` label。
  4. 紅 → 不併,留言退回該票(貼失敗的檢查名稱與一句話原因,不貼整段 log),拔 `agent:in-progress`、貼 `agent:blocked`。
- 多個 ready 的照 dependency / spec 順序**一個一個**併(地基先行);每併完一個,下一個的第二層驗證要以**該 PR 自己那條整合分支的新 HEAD** 為基準。兩份 spec 同時在跑時,這一輪的 ready PR 可能分屬不同的整合分支——每張 PR 只以自己 base 的那條為基準,不要以「上一張併進去的那條」為基準。
- **補驗路徑**:base 是 `spec/*` 的 **draft** PR,票上已有 `🤖 [implementer]` 完工 comment、沒有 `agent:blocked`、且沒有 subagent 正在做它(這一輪沒派)→ 那是舊契約或中斷留下的,派 subagent 到 PR head 分支跑第一層(本地 CI + `/code-review`),綠就轉 ready 等下一輪收割,紅就退回貼 `agent:blocked`。

- **讓等人認證的 spec→main PR 對得上現在的 main**(每輪都查;沒有這種 PR 就跳過):

  ```
  gh pr list --repo <code-repo> --state open --json number,baseRefName,headRefName --jq '.[] | select(.baseRefName == "main" and (.headRefName | startswith("spec/")))'
  ```

  對每一張,算整合分支落後 main 幾個 commit:`git rev-list --count origin/<整合分支>..origin/main`。

  **> 0 就要處理。** GitHub 不會因為 main 往前走而重跑 PR 上的 check,所以那張 PR 的綠燈是對舊 main 的綠燈——人一按 merge 就併進一個從沒被驗過的組合。兩份 spec 並行時這幾乎一定會發生:先併的那條一動,後併的那條立刻過期。

  派一個 subagent 處理:在該整合分支的 worktree 裡 `git merge origin/main`、重跑該 repo 的全套閘門(backend `uv run nox -s ci`,docker 可用時再加 `uv run nox -s integration`;frontend `pnpm check`)、綠了才 push 整合分支,並在 PR 上留一則 `🤖 [implementer]` comment 記「merge 了哪個 main SHA + 閘門指令與結果」。PR 的 draft/ready 狀態不要動,它仍然在等人。閘門紅 → 不 push,在 PR 上留言寫清楚哪個檢查掛了,**並明講「這張 PR 現在不能併」**。

  **產生檔的衝突不要手解。** 只會出現在 frontend 的 `packages/api-client/`(`openapi.json` 與 `src/generated/`):取 main 的版本,再跑 `pnpm codegen` 讓它從新的契約重新產生一次。兩份 spec 都會重新產生這兩個檔,這是它們唯一真正相撞的地方——在整合分支上重跑 codegen 解決,不要讓它留到人類的認證 PR 上。

- **清掉已關票上殘留的 `agent:*` label**(每輪都查):

  ```
  gh issue list --repo <code-repo> --state closed --label agent:in-progress --json number
  gh issue list --repo <code-repo> --state closed --label agent:implement --json number
  ```

  有的話直接拔掉,不留 comment。**label 生命週期的終點是關票**,而 spec→main 的 PR 是人 merge 的,那條路徑上沒有任何 loop 會經過去清——integrate 票就是這樣被關掉卻留著 `agent:in-progress` 的。看板欄位是從 label 算出來的,不清就會顯示一張「還在實作中」的鬼票。

### 1. 撿票

兩個 CODE repo(backend / frontend)掃 open issue,全部條件都要符合:

- 有 `agent:implement`
- 沒有 `agent:in-progress`(沒被認領)
- 沒有 assignee(有 assignee = 輪到人類,不碰)

```
gh issue list --repo <code-repo> --state open --label agent:implement --json number,title,labels,assignees
```

沒票 → 跳到步驟 5 回報,整輪 no-op。有多張 → 依 dependency 順序**取前 3 張**當候選(不足 3 張就取全部),逐張過下面的防呆,通過的才進入派工。

### 2. 防呆(相信 label 之前先驗證)

對**每一張**候選票(`OWNER/REPO` + `N`)分別驗證;沒通過的票就地處理掉、不進派工,不影響其他候選:

1. **blocker 全關了嗎?**
   ```
   gh api repos/OWNER/REPO/issues/N/dependencies/blocked_by --jq '[.[] | select(.state=="open")] | length'
   ```
   > 0 → 這張票被錯誤升級。拔 `agent:implement`、貼回 `agent:queued`、留 comment 說明,換下一張。
2. **parent 掛在哪裡?**
   ```
   gh api graphql -f query='query{repository(owner:"OWNER",name:"REPO"){issue(number:N){parent{number repository{nameWithOwner}}}}}'
   ```
   - **沒有 parent** → 通過。
   - **parent 在 `TaihemaoOrg/planning`** → **通過,這是正常的。** spec-train 的實作票掛在它的 spec 票底下是設計的一部分(那是人類在 planning 看進度的方式)。
   - **parent 在其他地方(含這個 code repo 自己)** → 拔 `agent:implement`、貼 `agent:blocked`、留 comment,這張不進派工。那是別人的拆解產物,不是實作票。

   **不要因為有 parent 就退票。** 舊版這條寫成「有 parent 就退」,退掉了 frontend#137 這張已經被 workflow 正常升級的票(實測 2026-09-07);backend 的 `promote-queued` 判斷的是同一件事,用的也是同一條線——parent 在 planning 就放行。兩邊必須一致,不然 workflow 升上來、你再退回去,票在兩個狀態之間彈跳。
3. **body 第一行有 `Integration-Branch: spec/<...>` 嗎?**(系統只有 spec-train 一種模式,這一行是必填)
   ```
   gh issue view N --repo OWNER/REPO --json body --jq '.body | split("\n")[0]'
   ```
   沒有 → 拔 `agent:implement`、貼 `agent:blocked`、留 comment「缺 Integration-Branch 標記,退回 Cartographer 補;不會走 main」。**絕不預設走 main。** 那條分支在 remote 不存在 → 同樣處理,comment 註明分支名。

### 3. 認領並派工(實作本體交給 subagent,code 殘渣不留在 loop)

1. **依序**對每張通過防呆的票貼 `agent:in-progress`(一張一張貼,不要平行)。每貼完一張就重新讀一次該 issue,確認沒有別的 session 同時動作。
2. **在同一則訊息裡平行派出所有 subagent**(一張票一個,最多 3 個)。每個 subagent 的 prompt 必須自帶完整契約:
   - 任務:實作 OWNER/REPO#N(把 ticket 標題、body 全文、所屬 map 連結貼進 prompt)
   - **分支與 PR(唯一模式 spec-train;防呆 3 已保證 body 第一行有 `Integration-Branch: spec/<...>`)**:
     - 一般批次票:worktree 從**那條整合分支**切出、PR base 到那條分支、PR body 寫 `Part of #N`(N = 這張票)並附 spec 連結、**不寫 `Closes`**(PR 併進非預設分支時 Closes 不會關票,是謊言);關票發生在步驟 0 的收割。
     - body 第二行是 `Role: integrate-and-verify` 的票 → 在整合分支的 worktree,**先 `git merge origin/main`**,再跑全套測試,綠了 push 整合分支,然後開 **spec→main** 的 PR。順序不能顛倒:先開 PR 再補 merge,那張 PR 一開始的綠燈就是對舊 main 的。PR body 的 `Closes` 一律寫成**純文字**(不包反引號、不放 code span,否則 GitHub 不關票,實測 backend#512),寫哪幾行看下面兩條規則:`Closes #<這張 integrate 票自己的票號>` 一定要寫,`Closes TaihemaoOrg/planning#<spec票號>` 只有「最後一張」才寫。它是這個 repo 的人類認證點,開完保持 draft 等人。PR body 要寫進「merge 進來的 main SHA」與閘門結果,人才知道這個綠燈驗的是哪個組合。

       **`Closes TaihemaoOrg/planning#<spec票號>` 只准寫在「最後一張」integrate 票的 PR 上。** 跨 repo 的 spec 有兩張 integrate 票(一個 repo 一張),兩張都寫的話,先 merge 的那張就把 spec 票關掉了,而另一個 repo 的半份 spec 還沒進 main——看板會顯示這份 spec 交付完成,其實只交付了一半。判斷誰是最後一張:
       ```
       gh api repos/OWNER/REPO/issues/N/dependencies/blocking --jq '[.[] | select(.state=="open")] | length'
       ```
       **> 0(還擋著別的票)→ 不是最後一張,PR body 只寫 `Closes #<自己的票號>`**,並在 body 裡寫一行「這份 spec 的另一半在 <另一個 repo>,那張 PR 併了才算交付完」。**0 → 是最後一張,兩行 `Closes` 都寫。**(實測 spec/47:backend#549 擋著 frontend#138 與 #139,所以它不是最後一張;frontend#139 誰都不擋,它才是。)

       **`Closes #<自己的票號>` 這一行,兩張都要寫,不能省。** 批次票不准寫 `Closes` 是因為它們併進非預設分支;這張的目標是 `main`,所以 `Closes` 會真的關票。少了它,人 merge 之後 integrate 票仍然 open,而**跨 repo 的下一批票常常就是 blocked-by 這張 integrate 票**(實測:frontend#138 的唯一 blocker 是 backend#549)——票不關,對面那個 repo 的半份 spec 永遠不會開始。關票同時觸發 `promote-queued`,那才是對面醒過來的機制。
       merge 出現衝突:產生檔(frontend `packages/api-client/openapi.json` 與 `src/generated/`)**不要手解**——取 main 的版本再跑 `pnpm codegen` 重新產生。其他檔案的衝突解不掉 → 不開 PR,拔 `agent:in-progress`、貼 `agent:blocked`,在票上寫清楚是哪個檔案跟 main 打起來。
     - **`/pr` skill 與本 loop 衝突時以本 loop 為準。** mattpocock v1.3 新增的 `/pr` skill 在寫 PR body 時會自動載入,它要求 Summary(用圖說明)/ Evidence(改前失敗、改後通過)/ Merge Danger 三段;跟上面的規則衝突時一律照本 loop。`Closes` 行一律寫成**純文字、獨立一行**,**不准**放進 code block 或反引號(包住了 GitHub 就不關票);PR body 用繁中;base 與整合分支照上面兩條。批次 PR(base 是 `spec/*`)照上面的格式即可,**不需要** `/pr` 的三段。spec→main 的 PR(integrate 票,要人審)**額外加一段** `/pr` 的 Merge Danger(單向門還是雙向門 + 波及範圍);Summary 與 Evidence 可選。
   - 工作區:`cd` 到對應的本機 clone(`~/wayfinder-lab/linebot-saas-backend` 或 `~/wayfinder-lab/linebot-saas-frontend`,**只准在 `~/wayfinder-lab/` 底下**),`git fetch origin` 後**用 git worktree 隔離**,分支名 `implement/issue-N-<slug>`,從票上 `Integration-Branch:` 指定的整合分支切出。絕不在主 worktree 的 main 上動工。
   - 實作:執行 `/implement`(skill 不可用就讀 `$(ls -d ~/.claude/plugins/cache/mattpocock/mattpocock-skills/*/ | sort -V | tail -1)skills/engineering/implement/SKILL.md` 照做):能 TDD 的地方走 `/tdd`,過程中常跑 typecheck 與單檔測試,最後跑一次全套,**做完必須跑 `/code-review` 並處理它的發現**。遵守該 repo 的 CLAUDE.md 與既有慣例;**測試要真的跑過**,不准只宣稱。
   - **本地 CI(取代 GitHub Actions;批次 PR 不會有任何 GitHub check)**:push 之前在 worktree 跑該 repo 的完整 CI 對應指令——backend `uv run nox -s ci`(docker 可用時再加 `uv run nox -s integration`),frontend `pnpm check`。全綠才准 push;紅就修,修不動就走下面的「卡住」路徑。
   - 完成動作(subagent 自己做完):push 分支 → 開 **draft PR**(base 與 body 依上面「分支與 PR」規則)→ ticket 留 `🤖 [implementer]` comment(PR 連結 + 做了什麼 + **本地 CI 指令與結果** + `/code-review` 的結論一句話 + **base 是哪條分支**)→ `gh pr ready <N>` 把 PR 轉 **ready**(這是告訴收割步驟「本地驗證過了」的唯一訊號;integrate-and-verify 票的 spec→main PR **例外,保持 draft** 等人)→ 所屬 map 留一句回報。**`agent:in-progress` 留著不拔**:PR 開了但還沒併進整合分支,票仍在實作中(看板顯示「⚡ 實作中」);兩個 label 都在步驟 0 收割關票時一起拔。撿票條件「沒有 `agent:in-progress`」同時保證這張票不會被重派
   - 卡住時(缺依賴、測試修不動、規格講不清):拔 `agent:in-progress`、貼 `agent:blocked`、留 comment 寫清楚卡在哪/試了什麼/需要什麼——規格不清就明講「這張票其實還在 fog,建議退回決策」;清掉半成品 worktree。
   - 禁令:不 self-assign、不動 `~/wayfinder-lab` 以外的目錄、不碰其他 ticket(**尤其是這一輪的其他候選票**,那是別的 subagent 的)、**絕不 merge 自己開的 PR**(merge 只發生在步驟 0 的收割;把 `origin/main` merge 進整合分支不算——那是 git merge,不是併 PR)、**不改 `.github/workflows/`**(CI 只看 main 是刻意的)。
   - 回傳:PR 連結 + 測試結果摘要,或卡點一句話

3. **每張票依複雜度選模型**(Agent 工具的 `model` 參數)。先讀 ticket 的 body 判斷,再決定:

   | 模型 | 用在什麼票 |
   |---|---|
   | `haiku` | 純機械改動:改文案/常數、rename、跟著既有 pattern 複製一個檔案、加一個既有型別的欄位 |
   | `sonnet` | **預設**:範圍清楚、pattern 已存在的一般功能實作。多數 tracer-bullet 票屬於這一類 |
   | `opus` | **上限**:要跨多個模組推理、動到 API contract 或資料模型、要在既有架構裡找落點、或這張票**上一輪以 `agent:blocked` 退回**(重試就升一級) |

   規則:**不確定就選 sonnet**;上限是 `opus`,不要用更高的層級。重試升級只升一次——opus 也退回 `agent:blocked` 的票就留給人類,不要無限重試燒 token。派工時把選用的模型和理由記在輪末回報裡。

### 4. 驗收(逐張核對實況、不信自述)

**每一張**派出去的票都要分別核對,用 `gh issue view N` 和 `gh pr list --repo OWNER/REPO --head implement/issue-N-<slug>`,確認三者其一成立:

- (a) PR 存在(base 是整合分支)且已是 **ready**、ticket 的 🤖 comment 含本地 CI 結果、`agent:in-progress` 仍在 → 成功。PR 還是 draft 且沒有 `agent:blocked` → 視為 (c)
- (b) `agent:blocked` 已貼且有卡點說明 → 已知失敗,留給人看
- (c) 兩者皆非(subagent 死掉或半途而廢)→ **你負責善後**:拔 `agent:in-progress`、貼 `agent:blocked`、留 comment 註明 subagent 未完成與已知進度。絕不讓票卡在認領狀態。

一張票失敗不影響其他張的驗收——逐張獨立處理。

### 5. 回報(每輪必做)

- 步驟 0 收割了哪些批次 PR(merge SHA、本地驗證結果、關了哪些票)、補驗了哪些;或無
- **等人認證的 spec→main PR**:每一張的整合分支落後 main 幾個 commit、這一輪有沒有替它 merge 與重跑閘門、結果。**「落後 0、閘門綠」才等於這張可以併**——這句要明講,人是照這句決定要不要按 merge 的
- 這輪做了哪幾張票:各自的 PR 連結、base 分支、測試結果、**用了哪個模型**;或 no-op
- 失敗/善後的票與原因
- 目前 `agent:blocked` 的票清單(這是 error flag,人類要看)
