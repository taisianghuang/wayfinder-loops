# 設計:把 wayfinder-loops 做成可安裝的公開 kit

狀態:已核准(2026-10-14);第一階段實作中。實作與本文不同處以 `references/` 與各 SKILL.md 為準。

## 目標

任何人照下面三步就能跑起整套流程,不需要改 kit 的任何檔案:

1. 安裝 plugin:`/plugin marketplace add taisianghuang/wayfinder-loops` → `/plugin install wayfinder-loops@wayfinder-loops`
2. 跑一次 `/wayfinder-loops:setup`:建 label、建看板、產生設定檔、把 workflow 送進各 repo
3. 開終端機下 `/loop 10m /wayfinder-loops:resolver` 等五條 loop

**非目標**

- 不改變現有 loop 的行為與契約(label 生命週期、spec-train、兩層本地驗證、獨立 reviewer)。這次只是把「寫死的值」抽出來、換包裝。
- 不支援 GitHub 以外的 issue tracker。
- 不處理 CI 本身:每個 code repo 的 CI 指令由使用者在設定檔提供,kit 不幫忙建 CI。
- 語言維持繁中(指令、留言、README 都是繁中)。

## 現況:哪些東西寫死了

| 寫死的內容 | 出現位置 | 新的去處 |
|---|---|---|
| `TaihemaoOrg/planning` | 五條 loop、`sync-project-status.yml` | 機器設定 `planning_repo` |
| `TaihemaoOrg/linebot-saas-backend` / `frontend` | 五條 loop、`setup-labels.sh` | `wayfinder.yml` 的 `code_repos` |
| `~/wayfinder-lab/` 本機 clone 位置 | implementer、prototyper、cartographer | 機器設定 `workspace_dir` + `code_repos[].dir` |
| `uv run nox -s ci`、`pnpm check`、`nox -s integration` | implementer(4 處) | `code_repos[].ci` / `ci_optional` |
| frontend 產生檔衝突改跑 `pnpm codegen` | implementer(2 處) | `code_repos[].generated` |
| 原型慣例(`apps/<app>/src/features/.../prototype/`、`pnpm boundaries`、390×844 截圖、wt-35 前例) | prototyper | planning repo 內的原型指南,由 `wayfinder.yml` 的 `code_repos[].prototype_guide` 指過去(選用);kit 只留通用流程。放 planning repo 是為了不必改動 code repo |
| backend 的 `arch-reviewer.md`、Delivery Rules 當過渡審查標準 | implementer 步驟 3b | 拿掉;reviewer 只讀 repo 的 `CODING_STANDARDS.md`(選用) |
| one-way door 清單(migration、LINE 推播、ERP 寫回…) | implementer 步驟 3b | kit 給通用預設,`wayfinder.yml` 的 `one_way_doors` 可以覆寫或追加 |
| `~/wayfinder-loops/templates/...`、`~/wayfinder-loops/scripts/...` 絕對路徑 | cartographer、prototyper | `${CLAUDE_PLUGIN_ROOT}/...` |
| `~/.claude/plugins/cache/mattpocock/...` 的 fallback 路徑 | implementer | 刪掉,改宣告 plugin 相依 |
| 「實測 backend#512」這類專案歷史 | 散落各處 | 保留「為什麼」,拿掉 ticket 編號 |

## Plugin 結構

```
wayfinder-loops/
├── .claude-plugin/
│   ├── plugin.json          ← name、version、dependencies、userConfig
│   └── marketplace.json     ← 這個 repo 本身就是 marketplace
├── skills/
│   ├── cartographer/SKILL.md
│   ├── resolver/SKILL.md
│   ├── researcher/SKILL.md
│   ├── implementer/SKILL.md
│   ├── prototyper/SKILL.md
│   ├── setup/SKILL.md       ← 一次性安裝精靈
│   └── doctor/SKILL.md      ← 健檢 README「不變式」那一節(第二階段再做)
├── agents/
│   └── reviewer.md          ← 步驟 3b 的審查契約搬到這裡
├── templates/
│   ├── decision-packet.md
│   └── wayfinder.yml        ← 設定檔範本
├── workflows/               ← setup 時複製進使用者 repo
├── bin/
│   └── wayfinder-run-loop   ← 原 scripts/run-loop.sh(模式 B)
├── scripts/                 ← build_gallery.py、inline_single_file.py、setup-labels.sh
├── README.md                ← 安裝 + 三步驟
└── LOOP.md                  ← 人類日常操作(內容不變,去掉 Taihemao 字樣)
```

選 skill 而不是 command:官方把 `commands/` 標為舊格式,skill 可以帶自己的支援檔。五條 loop **不設** `disable-model-invocation`,否則 `/loop` 觸發時會被當成純文字;改在 description 寫明「只在被明確呼叫時執行」。

`plugin.json` 重點:

```json
{
  "name": "wayfinder-loops",
  "version": "0.1.0",
  "dependencies": ["mattpocock-skills@mattpocock"],
  "userConfig": {
    "planning_repo": { "type": "string", "title": "Planning repo (owner/name)" },
    "workspace_dir": { "type": "directory", "title": "放 code repo clone 的資料夾" }
  }
}
```

`marketplace.json` 要加 `allowCrossMarketplaceDependenciesOn: ["mattpocock"]`,否則相依的 plugin 不會自動裝上。

## 設定分兩層

**機器層(plugin userConfig)**:每台電腦不同的東西,只有兩個值。

- `planning_repo`:例如 `TaihemaoOrg/planning`
- `workspace_dir`:例如 `~/wayfinder-lab`

skill 內文用 `${user_config.planning_repo}` 取得。

**組織層(`wayfinder.yml`,放在 planning repo 根目錄)**:整個團隊共用、要版控的東西。每條 loop 每一輪開頭用 `gh api repos/<planning_repo>/contents/wayfinder.yml` 讀一次。

```yaml
version: 1
project_url: https://github.com/orgs/TaihemaoOrg/projects/2

code_repos:
  - repo: TaihemaoOrg/linebot-saas-backend
    dir: linebot-saas-backend            # 在 workspace_dir 底下
    ci: uv run nox -s ci                 # 本地 CI 對應指令,batch PR 與 harvest 都跑這個
    ci_optional:                         # 條件成立才跑
      - when: docker                     # docker info 成功
        run: uv run nox -s integration
  - repo: TaihemaoOrg/linebot-saas-frontend
    dir: linebot-saas-frontend
    ci: pnpm check
    generated:                           # 衝突時不手解:取 main 的版本再重新產生
      - paths: [packages/api-client/openapi.json, packages/api-client/src/generated/]
        regenerate: pnpm codegen

one_way_doors:                           # 追加在 kit 預設清單之後
  - LINE 推播或其他對使用者的外送訊息
  - ERP 寫回

limits:
  per_round: 3                           # implementer 一輪最多幾張(含補驗)
models:
  implementer_default: sonnet
  implementer_max: opus
  reviewer: opus
```

kit 預設的 one-way door 清單:資料庫 migration、資料刪除或不可逆改寫、權限與認證、對外發送(email / webhook / 推播)、金流、公開 API 契約。

**repo 層(各 code repo 自己的檔案,全部選用)**:

| 檔案 | 誰讀 | 沒有時 |
|---|---|---|
| `CODING_STANDARDS.md` | reviewer | 只審 spec、會說謊的測試、Fowler smell baseline |
| `docs/agents/*.md`(mattpocock 的 setup 產物) | mattpocock skills | 照 mattpocock 自己的行為 |

## `/wayfinder-loops:setup` 做什麼

一個互動精靈,每一步先檢查,已經做過就跳過(可以重跑):

1. 前置檢查:`gh` 版本 ≥ 2.94、token 有 `project` scope、mattpocock-skills 已裝。缺的就告訴使用者要下什麼指令。
2. 問 planning repo、code repo 清單、各 repo 的 CI 指令 → 產生 `wayfinder.yml`,開 PR 進 planning repo。
3. 三類 repo 建齊 label(原 `setup-labels.sh`,改成讀設定檔)。
4. 看板:有 Project URL 就驗證 Status 的 13 個選項逐字一致;沒有就用 `gh project create` + `gh project field-create` 建。
5. 把 `workflows/` 的三個檔案以 PR 送進每個 repo。
6. 只有人能做的步驟(建 PAT、設 `PROJECT_TOKEN` / `ORG_AUTOMATION_TOKEN` secret、`PROJECT_URL` variable):列清楚、等使用者回報做完,再用 `gh secret list` 驗證。
7. 冒煙測試:在 planning 開一張測試想法,手動跑一輪 cartographer,確認看板出現在「等你決定」。

## 你的專案怎麼遷移

遷移期間現在的 loop 照常跑,切換只花幾分鐘、隨時可以退回。

1. 在分支上做完 plugin;本機用 `/plugin marketplace add ~/wayfinder-loops` 裝本地版。
2. 在 `TaihemaoOrg/planning` 加上 `wayfinder.yml`(內容就是上面的範例)。
3. 停掉五條 loop → 移除 `~/.claude/commands/` 的五個 symlink → 用 `/wayfinder-loops:<名稱>` 重開 loop。
4. 觀察一兩輪。有問題就裝回 symlink、用舊名稱重開。
5. memory 裡提到 `/implementer` 等舊名稱的條目,切換後更新。

## 要實測才能定案的事

官方文件沒寫清楚,第一階段一開始就驗證:

| 項目 | 驗證方式 | 不成立時的退路 |
|---|---|---|
| `/loop 10m /wayfinder-loops:resolver` 能跑 | 本地裝好後直接試 | 用 `bin/wayfinder-run-loop`(模式 B) |
| `${user_config.*}` 在 skill 內文會被替換 | 印出來看 | skill 開頭用 `claude plugin` 指令或讀 settings.json 取值 |
| reviewer 的 `subagent_type` 是 `wayfinder-loops:reviewer` | 派一次看看 | 用 general-purpose,把 `agents/reviewer.md` 內文貼進 prompt |
| mattpocock 的 skill 在 plugin 裡能用 `/implement` 呼叫,還是要寫 `/mattpocock-skills:implement` | 試兩種 | loop 內文一律寫完整名稱 |
| 跨 marketplace 相依會自動裝上 | 在乾淨環境裝一次 | README 寫明先裝 mattpocock-skills |

## 分階段

| 階段 | 內容 | 完成的定義 |
|---|---|---|
| 1. 包裝 + 設定檔 | plugin 骨架、五條 loop 搬成 skill、讀 `wayfinder.yml` 與 userConfig、刪掉寫死的值、上面的實測 | 你的機器用 plugin 跑五條 loop,行為跟現在一樣 |
| 2. reviewer agent + setup | `agents/reviewer.md`、`/setup`、workflow 參數化(`sync-project-status.yml` 的 planning repo 改讀 variable) | 在一個測試 org 從零跑完 setup 並通過冒煙測試 |
| 3. 文件 + 發佈前檢查 | README 重寫成三步驟、LOOP.md 去掉專案名稱、`claude plugin validate`、掃描內部資訊、設 `version` 0.1.0 | 你點頭後才把 repo 改成 public |

`doctor` 健檢 skill 與 retro loop 放在之後。

## 待你決定

1. **plugin 名稱**:決定指令前綴。`wayfinder-loops` → `/wayfinder-loops:implementer`(清楚但長);`wf` → `/wf:implementer`(短但不直觀)。建議 `wayfinder-loops`。
2. **授權**:公開時用什麼 license。建議 MIT,跟 mattpocock-skills 一致。
3. **測試 org**:第二階段要在一個乾淨的 GitHub org 從零驗證 setup。用你個人帳號底下新開的 org,還是先用 TaihemaoOrg 重跑 setup(冪等)驗證?
