# 設定參考

設定分三層。

## 1. 機器層(plugin userConfig)

安裝時填,之後用 `/plugin` → wayfinder-loops → Configure 修改,或 `claude plugin configure wayfinder-loops@wayfinder-loops`。

| 欄位 | 說明 | 例 |
|---|---|---|
| `planning_repo` | 放想法、map、決策票與 `wayfinder.yml` 的 repo | `my-org/planning` |
| `workspace_dir` | 各 code repo 的本機 clone 都放在這底下;loop 只在這裡面工作 | `~/wayfinder-workspace` |

## 2. 組織層(`wayfinder.yml`,放在 planning repo 根目錄)

整個團隊共用、要版控。每條 loop 每一輪開頭讀一次。範本:`templates/wayfinder.yml`。

| 欄位 | 必填 | 說明 |
|---|---|---|
| `version` | ✅ | 目前是 `1` |
| `project_url` | ✅ | GitHub Project 看板網址。**只支援 organization 底下的 Project**(`https://github.com/orgs/<org>/projects/<N>`),個人帳號的 Project 不支援 |
| `code_repos[].repo` | ✅ | `owner/name` |
| `code_repos[].dir` | ✅ | 在 `workspace_dir` 底下的資料夾名 |
| `code_repos[].ci` | ✅ | 本地 CI 對應指令。批次 PR、收割驗證、整合分支都跑它;要跟 GitHub CI 檢查同一組東西 |
| `code_repos[].ci_optional[]` | | `{when: docker, run: <指令>}`:條件成立才加跑 |
| `code_repos[].generated[]` | | `{paths: [...], regenerate: <指令>}`:這些路徑合併衝突時不手解,取 main 的版本再執行 `regenerate` |
| `code_repos[].prototype_guide` | | planning repo 內的路徑,寫「這個 repo 的原型怎麼做」。沒有就用 prototyper 的通用預設 |
| `one_way_doors[]` | | 追加在預設清單後面的單向門類別(見下) |
| `limits.per_round` | | implementer 一輪最多幾張(含補驗),預設 3 |
| `models.implementer_default` / `implementer_max` / `reviewer` | | 預設 `sonnet` / `opus` / `opus` |

**預設的單向門清單**(reviewer 判斷 Merge Danger 用):資料庫 migration、資料刪除或不可逆的資料改寫、權限字串或認證、對外發送(email、webhook、推播)、金流、公開 API 契約。

## GitHub 端的 variables 與 secrets

每個 repo(planning 與所有 code repo)都要設,workflow 才會動:

| 名稱 | 種類 | 說明 |
|---|---|---|
| `PROJECT_URL` | variable | 同 `project_url` |
| `PLANNING_REPO` | variable | planning repo 的 `owner/name`;`promote-queued` 與 `sync-project-status` 都用它,沒設時 promote-queued 會直接報錯 |
| `PROJECT_TOKEN` | secret | classic PAT,`project` + `repo` scope;寫看板用 |
| `ORG_AUTOMATION_TOKEN` | secret | classic PAT,`repo` scope;跨 repo 升級票用(可與 `PROJECT_TOKEN` 同一顆) |

## 3. repo 層(各 code repo 自己的檔案,全部選用)

| 檔案 | 誰讀 | 沒有時 |
|---|---|---|
| `CODING_STANDARDS.md` | reviewer | 只審 spec、會說謊的測試、Fowler smell baseline |
| `docs/agents/*.md`(`/setup-matt-pocock-skills` 的產物) | mattpocock skills | 照 mattpocock 自己的預設 |
