---
name: setup
description: wayfinder-loops 互動安裝精靈 — 檢查前置條件,建 planning repo、wayfinder.yml、label、org Project 看板(13 個 Status 選項、Board 檢視)、repo variable,並以 PR 送出 workflow;secret 列出指令讓人自己設。每一步先檢查、已完成就跳過,可以重跑。只在使用者明確呼叫 /wayfinder-loops:setup 時執行。
---

你是 wayfinder-loops 的安裝精靈。你把 README「手動設定」一節的步驟自動化。

## 規則

- 精靈分四個階段:盤點 → 計畫與同意 → 執行 → 人做的步驟與結尾。
- 盤點階段只讀不寫。唯讀檢查不用問使用者。
- 所有寫入動作(建 repo、push、開 PR、建 label、建或改看板、設 variable、clone 到本機)在執行前**一次列出**,取得使用者同意後才做。
- 每個步驟完成後印一行:✅(做完並驗證)、⏭️(已存在,跳過)、❌(失敗,附原因與修正指令)。
- 問使用者時用 AskUserQuestion,一次問一題。
- 警告:**絕對不要在對話中要求、接收、印出或處理任何 token 值。** secret 只由使用者在自己的終端機設定。使用者把 token 貼進對話時,告訴他立即到 GitHub 撤銷該 token 並重建,不要使用它。
- 不要修改 `<WORKSPACE>` 中既有 clone 的工作目錄。要 commit 的變更一律在 `$SETUP_TMP` 的暫存 clone 中做。
- 不要 merge 任何 PR。PR 由人合併。

名詞:

- `<PLANNING>` = planning repo(`owner/name`)。
- `<ORG>` = `<PLANNING>` 的 owner。
- `<WORKSPACE>` = 工作區資料夾。
- `<PLUGIN>` = `${CLAUDE_PLUGIN_ROOT}`。
- `<CODE_REPOS>` = `wayfinder.yml` 的 `code_repos[].repo`。
- `<ALL_REPOS>` = `<PLANNING>` 加上 `<CODE_REPOS>`。
- `<BRANCH>` = `wayfinder-loops/setup`。精靈在每個 repo 用這個分支開 PR。

## 第一階段:盤點(只讀)

### 步驟 0:讀 plugin 設定

- planning repo:`${user_config.planning_repo}`
- 工作區:`${user_config.workspace_dir}`
- plugin 根目錄:`${CLAUDE_PLUGIN_ROOT}`

1. 檢查上面三行。任何一行還是 `${...}` 的字面值時,印 ❌,告訴使用者執行 `/plugin` → 選 wayfinder-loops → 選 Configure,填寫後重新執行 `/wayfinder-loops:setup`。然後停止。
2. 確認 planning repo 的格式是 `owner/name`。格式錯時,照第 1 點處理。
3. 建立暫存資料夾,記下路徑:

   ```bash
   mktemp -d -t wayfinder-setup-XXXXXX
   ```

   下文用 `$SETUP_TMP` 代表這個路徑。

### 步驟 1:前置檢查

缺少任何一項時,印 ❌ 與修正指令,然後停止。使用者修正後重新執行精靈。

1. 執行 `gh --version`。版本要 ≥ 2.94。不足時:請使用者依 https://github.com/cli/cli#installation 升級。
2. 執行 `gh auth status`。在 `Token scopes` 一行,確認有 `repo`、`project`、`workflow`。缺少時給:

   ```bash
   gh auth refresh -s repo,project,workflow
   ```

   注意:`workflow` scope 是 push `.github/workflows/` 檔案所需。
3. 執行 `python3 --version`。沒有 python3 時,請使用者安裝。
4. 確認 mattpocock-skills 已安裝。執行 `claude plugin list --json`。要有 `id` 以 `mattpocock-skills@` 開頭的項目,且該項目 `installPath` 底下有 `skills/engineering/implement/SKILL.md`。缺少時給:

   ```text
   /plugin marketplace add mattpocock/skills
   /plugin install mattpocock-skills@mattpocock
   ```

5. 確認 `<ORG>` 是 organization:

   ```bash
   gh api users/<ORG> --jq .type
   ```

   結果不是 `Organization` 時,印 ❌:wayfinder-loops 只支援 organization 底下的 Project 看板。請使用者把 planning repo 移到 organization,或改用 organization 的 repo,再改 Configure。然後停止。
6. 印 `✅ 步驟 1 前置檢查`。

### 步驟 2:planning repo

1. 執行:

   ```bash
   gh repo view <PLANNING> --json nameWithOwner,isEmpty,defaultBranchRef,viewerPermission
   ```

2. 依結果記下狀態:

   | 結果 | 狀態 | 計畫中的動作 |
   | --- | --- | --- |
   | 找不到 repo | 不存在 | 問使用者是否建立。同意時加入計畫:`gh repo create <PLANNING> --private --add-readme`。不同意時停止。 |
   | `isEmpty` 是 `true` | 沒有任何 commit | 加入計畫:push 一個只含 `README.md` 的初始 commit 到 `main`。 |
   | 其他 | 正常 | 無。 |

3. `viewerPermission` 不是 `ADMIN` 時,印 ❌:設定 variable 與 secret 需要 admin 權限。請使用者找 repo admin 執行精靈。然後停止。

### 步驟 3:code repo 與 wayfinder.yml

1. 依序讀現有的 `wayfinder.yml`。用第一個讀得到的:
   1. 預設分支:`gh api -H "Accept: application/vnd.github.raw" repos/<PLANNING>/contents/wayfinder.yml`
   2. 上次精靈開的分支:`gh api -H "Accept: application/vnd.github.raw" "repos/<PLANNING>/contents/wayfinder.yml?ref=wayfinder-loops/setup"`
2. 讀到時:依 `<PLUGIN>/references/config.md` 檢查必填欄位(`version`、`project_url`、每個 `code_repos[]` 的 `repo`、`dir`、`ci`)。只問缺少的欄位。`project_url` 由步驟 5 處理,這裡不問。
3. 讀不到時:向使用者問以下項目,一次一題:
   1. code repo 清單(`owner/name`,可以有多個)。
   2. 每個 code repo 的本機資料夾名 `dir`。預設是 repo 名稱。
   3. 每個 code repo 的 CI 指令 `ci`。說明:這個指令要在本機跑過 GitHub CI 檢查的同一組項目。
   4. 每個 code repo 是否需要 `ci_optional`(例:有 docker 時才加跑的整合測試)。需要時問 `run` 指令,`when` 固定為 `docker`。
4. 對每個 code repo,執行 `gh repo view <repo> --json nameWithOwner,viewerPermission`。repo 不存在時印 ❌ 並停止(精靈不建立 code repo)。`viewerPermission` 不是 `ADMIN` 時,照步驟 2 第 3 點處理。
5. 對每個 code repo,檢查本機 clone `<WORKSPACE>/<dir>`:

   | 結果 | 計畫中的動作 |
   | --- | --- |
   | 資料夾不存在 | 加入計畫:`gh repo clone <repo> <WORKSPACE>/<dir>` |
   | 存在,且 `git -C <WORKSPACE>/<dir> remote get-url origin` 指向該 repo | 無 |
   | 存在,但不是 git repo 或 origin 指向別的 repo | 印 ❌,請使用者換一個 `dir` 或自己處理該資料夾。不要動它。 |

6. 在 `$SETUP_TMP/wayfinder.yml` 寫出目標內容:
   - 已有 `wayfinder.yml` 時:以它為底,只補缺少的欄位。保留原有的註解與欄位。
   - 沒有時:以 `<PLUGIN>/templates/wayfinder.yml` 為底。換掉範例 repo,填入使用者的答案。刪除使用者沒有要的選用欄位(`generated`、`prototype_guide`、`one_way_doors`)。保留 `limits` 與 `models` 的預設值。
   - `project_url` 先保留原值或留空。步驟 5 填入。
7. 把現有內容與目標內容不同時,記下「wayfinder.yml 要送 PR」。

### 步驟 4:label

1. 取得 label 清單:

   ```bash
   sed -nE 's/^  "([^|]+)\|.*/\1/p' <PLUGIN>/scripts/setup-labels.sh
   ```

2. 對 `<ALL_REPOS>` 的每個 repo(還不存在的 planning repo 視為缺少全部 label),執行:

   ```bash
   gh label list --repo <repo> --limit 300 --json name --jq '.[].name'
   ```

3. 有任何 repo 缺少任何 label 時,加入計畫:`bash <PLUGIN>/scripts/setup-labels.sh <PLANNING> <CODE_REPOS...>`。

### 步驟 5:Project 看板

看板 Status 欄位的 13 個選項,名稱、顏色、說明與由左到右的順序都定義在 `<PLUGIN>/scripts/board-status.py` 的 `STATUS_OPTIONS`。這份清單與 `workflows/sync-project-status.yml` 逐字一致;不一致時腳本以結束碼 3 結束。

1. 決定看板:
   - `wayfinder.yml` 有 `project_url` 時:從網址取出 `<ORG>` 與編號 `<N>`(格式 `https://github.com/orgs/<ORG>/projects/<N>`)。執行 `gh project view <N> --owner <ORG> --format json`。讀不到時印 ❌,請使用者修正 `project_url`。
   - 沒有 `project_url` 時:執行 `gh project list --owner <ORG> --format json`,列出現有看板。問使用者:沿用其中一個,或建立新看板(預設標題 `wayfinder-loops`)。建立新看板時,加入計畫:`gh project create --owner <ORG> --title "<標題>" --format json`。新看板的 Status 欄位只有 Todo / In Progress / Done,也加入計畫:改成 13 個選項。
2. 現有看板:讀 Status 欄位,存成檔案:

   ```bash
   gh api graphql \
     -f query='query($org:String!,$num:Int!){organization(login:$org){projectV2(number:$num){field(name:"Status"){... on ProjectV2SingleSelectField{id options{id name}}}}}}' \
     -f org=<ORG> -F num=<N> --jq '.data.organization.projectV2.field' > "$SETUP_TMP/status-field.json"
   python3 <PLUGIN>/scripts/board-status.py check < "$SETUP_TMP/status-field.json"
   ```

3. 依結束碼處理:

   | 結束碼 | 意思 | 計畫中的動作 |
   | --- | --- | --- |
   | 0 | 13 個選項與順序一致 | 無 |
   | 1 | 名稱一致,順序不同 | 問使用者是否重排。重排不會清掉卡片上的值。同意時加入計畫:改 Status 選項。 |
   | 2 | 有缺少或多出的選項 | 加入計畫:改 Status 選項。有多出的選項時,做第 4 點。 |
   | 3 | plugin 本身的清單有錯 | 印 ❌,請使用者回報 plugin 的 issue。然後停止。 |

4. 多出的選項會被刪除。刪除前,計算每個選項上有多少張卡片:

   ```bash
   gh api graphql --paginate \
     -f query='query($org:String!,$num:Int!,$endCursor:String){organization(login:$org){projectV2(number:$num){items(first:100,after:$endCursor){pageInfo{hasNextPage endCursor} nodes{fieldValueByName(name:"Status"){... on ProjectV2ItemFieldSingleSelectValue{name}}}}}}}' \
     -f org=<ORG> -F num=<N> --jq '.data.organization.projectV2.items.nodes[].fieldValueByName.name // "(無)"' | sort | uniq -c
   ```

   把要刪除的選項與卡片數寫進計畫。警告使用者:這些卡片的 Status 會變成空白。`sync-project-status` 只在 issue 有新事件時重算;已關閉的 issue 不會再有事件,它們的卡片會一直是空白。
5. 檢查看板連到哪些 repo:

   ```bash
   gh api graphql \
     -f query='query($org:String!,$num:Int!){organization(login:$org){projectV2(number:$num){repositories(first:100){nodes{nameWithOwner}}}}}' \
     -f org=<ORG> -F num=<N> --jq '.data.organization.projectV2.repositories.nodes[].nameWithOwner'
   ```

   `<ALL_REPOS>` 中沒有連上的 repo,加入計畫:`gh project link <N> --owner <ORG> --repo <repo>`。
6. 檢查檢視(view)。新看板的預設檢視是 Table。wayfinder-loops 要用以 Status 分欄的 Board 檢視:

   ```bash
   gh api graphql \
     -f query='query($org:String!,$num:Int!){organization(login:$org){projectV2(number:$num){id views(first:50){nodes{id number name layout verticalGroupByFields(first:5){nodes{... on ProjectV2FieldCommon{name}}}}}}}}' \
     -f org=<ORG> -F num=<N> --jq '.data.organization.projectV2'
   ```

   記下 project 的 `id`(下文 `<PROJECT_ID>`)與第一個檢視的 `id`(`number` 最小的,下文 `<VIEW_ID>`)。依結果處理:

   | 結果 | 計畫中的動作 |
   | --- | --- |
   | 有 `layout` 是 `BOARD_LAYOUT` 且分欄是 `Status` 的檢視 | 無 |
   | 看板由精靈在本次新建 | 加入計畫:把第一個檢視改成 Board,名稱 `Board` |
   | 既有看板,沒有符合的檢視 | 問使用者:新增一個 Board 檢視(建議,不動既有檢視)、把第一個檢視改成 Board、或不要。依答案加入計畫 |

7. `wayfinder.yml` 的 `project_url` 與看板網址不同或沒有時,在 `$SETUP_TMP/wayfinder.yml` 填入看板網址,並記下「wayfinder.yml 要送 PR」。新看板的網址要等建立後才知道;計畫中寫「建立後填入」。

### 步驟 6:variable

1. 對 `<ALL_REPOS>` 的每個 repo,執行:

   ```bash
   gh variable list --repo <repo> --json name,value
   ```

2. 比對兩個 variable:

   | 名稱 | 目標值 |
   | --- | --- |
   | `PROJECT_URL` | 看板網址 |
   | `PLANNING_REPO` | `<PLANNING>` |

3. 依結果處理:
   - 沒有:加入計畫:`gh variable set <名稱> --repo <repo> --body "<目標值>"`。
   - 值相同:無。
   - 值不同:把現值與目標值給使用者看,問是否覆寫。同意時加入計畫。不同意時,該項在步驟 6 印 ⏭️ 並註明「使用者保留舊值」。

### 步驟 7:secret(只檢查)

1. 對 `<ALL_REPOS>` 的每個 repo,執行:

   ```bash
   gh secret list --repo <repo> --json name --jq '.[].name'
   ```

2. 記下哪些 repo 缺少 `PROJECT_TOKEN` 或 `ORG_AUTOMATION_TOKEN`。這些在第四階段由人設定。

### 步驟 8:workflow

1. 對 `<ALL_REPOS>` 的每個 repo,對 `<PLUGIN>/workflows/` 的三個檔案(`dispatch-on-decision.yml`、`promote-queued.yml`、`sync-project-status.yml`),讀 repo 中的版本:

   ```bash
   gh api -H "Accept: application/vnd.github.raw" repos/<repo>/contents/.github/workflows/<檔名> > "$SETUP_TMP/remote-<檔名>"
   diff -q <PLUGIN>/workflows/<檔名> "$SETUP_TMP/remote-<檔名>"
   ```

2. 依結果分類每個檔案:
   - `gh api` 失敗(HTTP 404):沒有。這時檔案內容是錯誤訊息,不要拿來比對。
   - `diff -q` 沒有輸出:內容相同。
   - 其他:內容不同。執行 `diff -u` 並把差異摘要給使用者看。
3. 若 `<BRANCH>` 上有開著的 PR,也用 `?ref=wayfinder-loops/setup` 比對一次。分支上已是最新內容時,該檔案視為已處理。
4. 有任何檔案是「沒有」或「內容不同」時,該 repo 加入計畫:開 PR。planning repo 的 workflow 與 `wayfinder.yml` 放在同一個 PR。

### 盤點結果

印一張表:每個步驟一列,欄位為「步驟」「現況」「要做的動作」。沒有動作的步驟寫「⏭️ 已完成」。

## 第二階段:計畫與同意

1. 列出所有寫入動作,依第三階段的執行順序編號。每一項寫清楚:對哪個 repo 或資料夾、做什麼、用哪條指令。要開的 PR 寫出 repo、分支、標題、包含的檔案。
2. 寫出會被刪除或覆寫的東西(Status 選項與卡片數、variable 舊值、workflow 檔案的差異)。
3. 用 AskUserQuestion 問:「執行以上全部」「只執行部分(之後說明)」「取消」。
4. 使用者選「只執行部分」時,問要排除哪幾項。被排除的項目在第三階段印 ⏭️ 並註明「使用者略過」。
5. 使用者選「取消」時,印盤點結果表,然後停止。

計畫沒有任何寫入動作時,跳過本階段,直接到第四階段。

## 第三階段:執行

依下列順序執行。每項執行後立即驗證。驗證失敗時印 ❌,繼續做不依賴它的項目。

### 2. 建立或初始化 planning repo

- 不存在時:

  ```bash
  gh repo create <PLANNING> --private --add-readme
  ```

- 沒有 commit 時:

  ```bash
  gh repo clone <PLANNING> "$SETUP_TMP/planning"
  git -C "$SETUP_TMP/planning" symbolic-ref HEAD refs/heads/main
  printf '# %s\n\nwayfinder-loops planning repo.\n' "<name>" > "$SETUP_TMP/planning/README.md"
  git -C "$SETUP_TMP/planning" add README.md
  git -C "$SETUP_TMP/planning" commit -m "chore: initial commit"
  git -C "$SETUP_TMP/planning" push -u origin main
  ```

驗證:`gh repo view <PLANNING> --json isEmpty,defaultBranchRef` 的 `isEmpty` 是 `false`。印 `✅ 步驟 2 planning repo`。

### 3a. clone code repo 到工作區

```bash
gh repo clone <repo> <WORKSPACE>/<dir>
```

驗證:`git -C <WORKSPACE>/<dir> remote get-url origin` 指向該 repo。

### 4. 建立 label

```bash
bash <PLUGIN>/scripts/setup-labels.sh <PLANNING> <CODE_REPOS...>
```

這個腳本是冪等的。驗證:重做盤點步驟 4 的比對,每個 repo 都不缺 label。印 `✅ 步驟 4 label`。

### 5. 看板

1. 建新看板時:

   ```bash
   gh project create --owner <ORG> --title "<標題>" --format json
   ```

   從結果記下 `number` 與 `url`。把 `url` 填入 `$SETUP_TMP/wayfinder.yml` 的 `project_url`。然後照盤點步驟 5 第 2 點讀 Status 欄位,存成 `$SETUP_TMP/status-field.json`。
2. 改 Status 選項時:

   警告:`updateProjectV2Field` 的 `singleSelectOptions` 會**整組覆寫**選項。沒有帶 `id` 的既有選項會被刪除,卡片上的該值會被清掉。只用 `board-status.py mutation` 產生的 body,它會為名稱相同的選項帶上原本的 `id`。

   ```bash
   python3 <PLUGIN>/scripts/board-status.py mutation < "$SETUP_TMP/status-field.json" > "$SETUP_TMP/status-mutation.json"
   gh api graphql --input "$SETUP_TMP/status-mutation.json"
   ```

3. 驗證:重讀 Status 欄位,執行 `board-status.py check`,結束碼要是 0。
4. 連結 repo:

   ```bash
   gh project link <N> --owner <ORG> --repo <repo>
   ```

5. 驗證:重做盤點步驟 5 第 5 點,`<ALL_REPOS>` 都在清單中。
6. Board 檢視。新看板的 `<VIEW_ID>` 在建立後依盤點步驟 5 第 6 點讀取。
   - 把第一個檢視改成 Board:

     ```bash
     gh api graphql \
       -f query='mutation($v:ID!){updateProjectV2View(input:{viewId:$v,layout:BOARD_LAYOUT,name:"Board"}){projectV2View{layout verticalGroupByFields(first:5){nodes{... on ProjectV2FieldCommon{name}}}}}}' \
       -f v=<VIEW_ID>
     ```

   - 新增一個 Board 檢視:

     ```bash
     gh api graphql \
       -f query='mutation($p:ID!){createProjectV2View(input:{projectId:$p,name:"Board",layout:BOARD_LAYOUT}){projectV2View{layout verticalGroupByFields(first:5){nodes{... on ProjectV2FieldCommon{name}}}}}}' \
       -f p=<PROJECT_ID>
     ```

7. 驗證:回傳的 `layout` 是 `BOARD_LAYOUT`,分欄欄位是 `Status`。分欄不是 `Status` 時印 ❌:API 不能指定分欄欄位。請使用者在看板網頁開啟該檢視 → 選 View 選單 → Column by → 選 Status。
8. 印 `✅ 步驟 5 看板 <url>`。

### 3b + 8. planning repo 的 PR(wayfinder.yml 與 workflow)

1. 準備暫存 clone 與分支:

   ```bash
   gh repo clone <PLANNING> "$SETUP_TMP/planning" -- --depth 1
   git -C "$SETUP_TMP/planning" ls-remote --exit-code --heads origin wayfinder-loops/setup
   ```

   第一次執行時,資料夾若已在步驟 2 建立,跳過 clone。
   - 遠端有 `wayfinder-loops/setup` 分支,且 `gh pr list --repo <PLANNING> --head wayfinder-loops/setup --state open --json number,url` 有開著的 PR:接續這個分支。

     ```bash
     git -C "$SETUP_TMP/planning" fetch --depth 1 origin wayfinder-loops/setup:wayfinder-loops/setup
     git -C "$SETUP_TMP/planning" switch wayfinder-loops/setup
     ```

   - 遠端有分支但沒有開著的 PR:改用分支名 `wayfinder-loops/setup-<YYYYMMDD>`,從預設分支建立。不要 force push 舊分支。
   - 遠端沒有分支:`git -C "$SETUP_TMP/planning" switch -c wayfinder-loops/setup`。
2. 複製 `$SETUP_TMP/wayfinder.yml` 到 `$SETUP_TMP/planning/wayfinder.yml`。
3. 建立 `$SETUP_TMP/planning/.github/workflows/`,複製計畫中的 workflow 檔案。
4. commit 並 push:

   ```bash
   git -C "$SETUP_TMP/planning" add wayfinder.yml .github/workflows
   git -C "$SETUP_TMP/planning" commit -m "chore: add wayfinder-loops config and workflows"
   git -C "$SETUP_TMP/planning" push -u origin <分支>
   ```

5. 沒有開著的 PR 時,開 PR。PR body 用繁體中文,寫:加入了哪些檔案、`wayfinder.yml` 的 code repo 清單與看板網址、workflow 需要的 variable 與 secret、要合併後 loop 才讀得到設定。內容不同的 workflow,在 body 中說明差異。

   ```bash
   gh pr create --repo <PLANNING> --base <預設分支> --head <分支> --title "wayfinder-loops 設定" --body-file "$SETUP_TMP/pr-body-planning.md"
   ```

6. 驗證:`gh api -H "Accept: application/vnd.github.raw" "repos/<PLANNING>/contents/wayfinder.yml?ref=<分支>"` 與 `$SETUP_TMP/wayfinder.yml` 相同。印 `✅ 步驟 3 wayfinder.yml PR <url>`。

### 8. code repo 的 workflow PR

對計畫中的每個 code repo:

1. 照上一節第 1 點準備 `$SETUP_TMP/<name>` 的暫存 clone 與分支。不要用 `<WORKSPACE>` 中的 clone。
2. 建立 `.github/workflows/`,複製計畫中的 workflow 檔案。
3. commit、push、開 PR(標題 `wayfinder-loops workflow`)。commit message 依該 repo 的規範;沒有規範時用 `chore: add wayfinder-loops workflows`。
4. 驗證:用盤點步驟 8 的方法加 `?ref=<分支>` 比對,三個檔案都相同。印 `✅ 步驟 8 <repo> PR <url>`。

### 6. 設定 variable

```bash
gh variable set PROJECT_URL --repo <repo> --body "<看板網址>"
gh variable set PLANNING_REPO --repo <repo> --body "<PLANNING>"
```

驗證:`gh variable list --repo <repo> --json name,value` 的兩個值與目標相同。印 `✅ 步驟 6 variable`。

## 第四階段:人做的步驟與結尾

### 步驟 7:secret

盤點步驟 7 沒有缺少的 secret 時,印 `⏭️ 步驟 7 secret` 並跳到步驟 9。

把以下步驟原樣給使用者:

警告:token 只在你自己的終端機輸入。不要貼進 Claude Code 的對話。不要用 `!` 在對話中執行這些指令:`!` 不能互動輸入,`read` 會讀到空字串,secret 會被設成空值。

1. 開啟 https://github.com/settings/tokens/new?scopes=repo,project&description=wayfinder-loops 。
2. 確認 Select scopes 中 `repo` 與 `project` 已勾選。
3. 設定 Expiration。
4. 選 Generate token。複製 token。
5. organization 有 SSO 時,在 token 旁選 Configure SSO,授權 `<ORG>`。
6. 在 Claude Code 以外開一個新的終端機。執行以下指令。出現提示時貼上 token,按 Enter(畫面不顯示):

   ```bash
   read -rsp "貼上 token 後按 Enter: " WF_TOKEN; echo
   [ -n "$WF_TOKEN" ] || { echo "沒有讀到 token,停止"; return 1 2>/dev/null || exit 1; }
   for repo in <缺少 secret 的 repo,以空格分隔>; do
     printf '%s' "$WF_TOKEN" | gh secret set PROJECT_TOKEN --repo "$repo"
     printf '%s' "$WF_TOKEN" | gh secret set ORG_AUTOMATION_TOKEN --repo "$repo"
   done
   unset WF_TOKEN
   ```

7. 完成後,在 Claude Code 中回覆「完成」。

注意:`PROJECT_TOKEN` 與 `ORG_AUTOMATION_TOKEN` 可以是同一個 token。organization 若限制 classic token 的存取,請 org owner 在 organization 的 Settings → Personal access tokens 允許 classic token。

使用者回覆後,重做盤點步驟 7。注意:`gh secret list` 只看得到名稱,看不到值。使用者若在對話中用 `!` 執行了上面的指令(對話中會出現該指令的輸出),secret 存在但值是空的。這時請使用者在 Claude Code 以外的終端機重做第 6 點。每個 repo 都有兩個名稱時,印 `✅ 步驟 7 secret`。仍缺少時,印 ❌ 並列出缺少的 repo 與名稱。

### 步驟 9:結尾

1. 印總表:步驟 0 到 9,每步一行 ✅ / ⏭️ / ❌。
2. 列出精靈開的所有 PR 網址。告訴使用者:workflow 與 `wayfinder.yml` 要合併到預設分支後才生效。
3. 把以下步驟給使用者:
   1. 合併上面列出的每個 PR。
   2. 執行 `/wayfinder-loops:doctor`。確認所有項目是 ✅。
   3. 冒煙測試:
      1. 在 planning repo 建立一個 issue。寫一句想法。不要加 label。
      2. 開啟看板。確認卡片出現在「💡 收件匣」欄。沒有出現時,開啟 planning repo 的 Actions 頁,讀 `sync-project-status` 的錯誤。
      3. 執行一輪 `/wayfinder-loops:cartographer`。
      4. 開啟看板。確認 map 出現在「🗺️ 規劃中」欄,decision ticket 出現在「⏳ 等你決定」或「🔍 準備選項中」欄。
      5. 關閉測試用的 issue。
4. 刪除 `$SETUP_TMP`。
