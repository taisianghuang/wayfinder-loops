---
name: doctor
description: wayfinder-loops 健檢 — 印出目前生效的設定(planning repo、工作區、plugin 路徑)並檢查 wayfinder.yml 讀得到。只在使用者明確呼叫 /wayfinder-loops:doctor 時執行。
---

你是 wayfinder-loops 的健檢。只讀不寫:不建 label、不改任何檔案、不留 comment。

## 生效的設定

- planning repo:`${user_config.planning_repo}`
- 工作區:`${user_config.workspace_dir}`
- plugin 根目錄:`${CLAUDE_PLUGIN_ROOT}`

上面任何一行如果還是 `${...}` 的字面值,代表設定沒有被替換,回報「設定未生效」與是哪一個,然後停止。

## 檢查

1. `gh --version` ≥ 2.94;`gh auth status` 的 token scope 含 `project`。
2. 讀設定檔:`gh api -H "Accept: application/vnd.github.raw" repos/<planning repo>/contents/wayfinder.yml`。讀不到 → 回報缺 wayfinder.yml,請執行 `/wayfinder-loops:setup`。
3. 對 wayfinder.yml 的每個 `code_repos[]`:`<工作區>/<dir>` 存在且是 git repo、`git -C <path> remote get-url origin` 指向該 repo。
4. 確認 mattpocock-skills 已安裝:`claude plugin list --json` 有 `mattpocock-skills@` 開頭的項目,且它的 `installPath` 底下有 `skills/engineering/implement/SKILL.md`(這個 skill 設了 disable-model-invocation,不會出現在 skill 清單,要看檔案)。
5. 對 wayfinder.yml 的每個 repo 與 planning repo:`gh variable list --repo <repo>` 有 `PROJECT_URL` 與 `PLANNING_REPO`,`gh secret list --repo <repo>` 有 `PROJECT_TOKEN` 與 `ORG_AUTOMATION_TOKEN`。

## 回報

每項一行:✅ / ❌ + 一句說明。❌ 的項目附上修正指令。
