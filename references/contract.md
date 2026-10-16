# 共同契約(五條 loop 一致)

每條 loop 的 SKILL.md 開頭已經給你兩個值:**PLANNING**(planning repo,`owner/name`)與 **WORKSPACE**(本機工作區資料夾)。這份文件定義其餘所有 loop 共用的規則。

## 第 0 步:每一輪先讀設定

```bash
gh api -H "Accept: application/vnd.github.raw" repos/<PLANNING>/contents/wayfinder.yml
```

欄位定義見 `references/config.md`。讀不到或格式錯 → 這一輪不做任何事,回報「wayfinder.yml 讀不到,請執行 /wayfinder-loops:doctor」後結束。**不要猜預設值去跑。**

以下用到的名詞:

- **CODE repo** = 設定檔 `code_repos[].repo` 列出的 repo。implementation ticket 與 PR 只在這些 repo。
- **本機 clone** = `<WORKSPACE>/<code_repos[].dir>`。**只准在 WORKSPACE 底下工作**,不碰工作區以外的同名 repo(那是人類的日常工作區)。
- **CI 指令** = `code_repos[].ci`;`ci_optional[]` 的 `when` 條件成立才加跑(`docker` = `docker info` 成功)。

## 身分與發言

- 所有 loop 共用同一個 GitHub 帳號,**不能用 comment 作者判斷是不是人類**。loop 發的每一則 comment 都以 `🤖 [loop名]` 開頭;**沒有這個前綴的 comment 一律視為人類發言**。
- `decision:*` label 依契約只有人會貼。
- 對外文字(issue、comment、PR body)用繁體中文(台灣用語);commit message 依該 CODE repo 自己的規範(沒有規範時用英文)。

## claim 與欄位

- claim lock 是 `agent:in-progress` label,**不是 self-assign**。mattpocock 的 skill 或 wayfinder 流程叫你 assign yourself 時,一律改貼 label。
- assignee 欄位保留給「輪到人類」。
- **map body 只有 Cartographer 寫**。其他 loop 要告訴 map 的事,用自己前綴的 comment 貼在 map issue 上。
- 任何 loop、任何 workflow 都**不讀 Project Status 做判斷**;判斷一律讀 label。Status 由 `sync-project-status` workflow 鏡射。

## 叫用 mattpocock-skills

loop 依賴 `mattpocock-skills` plugin。它的 `implement`、`to-spec`、`to-tickets`、`wayfinder` 設了 `disable-model-invocation`,用 Skill 工具叫不到。**一律直接讀它的 SKILL.md 照做**:

```bash
MP=$(claude plugin list --json | python3 -c "import sys,json; print(next(p['installPath'] for p in json.load(sys.stdin) if p['id'].startswith('mattpocock-skills@')))")
# 例:$MP/skills/engineering/implement/SKILL.md
```

可以用 Skill 工具直接叫的(沒設該旗標):`mattpocock-skills:tdd`、`mattpocock-skills:code-review`、`mattpocock-skills:pr`、`mattpocock-skills:prototype`、`mattpocock-skills:grilling`、`mattpocock-skills:research`。派 subagent 時,把 `MP` 的實際路徑寫進 prompt。

**本 loop 的規則與 mattpocock skill 衝突時,以本 loop 為準。**

## 派工的通則

- 會留下大量讀檔/查證殘渣的工作(實作、查證、開 ticket、原型)一律交給 subagent;loop 本身只做掃描、claim、派工、驗收、回報,讓 loop session 的 context 不隨輪數膨脹。
- subagent 的 prompt 必須自帶完整契約(它看不到這份文件):把用到的規則、設定值、路徑都寫進去。例外是 `wayfinder-loops:reviewer` agent,它的契約寫在 `agents/reviewer.md`,派工時只需傳入該張 PR 的資料。
- 模型上限以設定檔 `models` 為準;沒寫時預設 `sonnet`,上限 `opus`。

## 平行度

**絕對不要同時開兩條同名 loop。** label 鎖沒有身分資訊,兩個 session 搶同一張 ticket 時都會以為是自己貼的。平行度一律靠「同一條 loop 內依序 claim、平行派工」取得。
