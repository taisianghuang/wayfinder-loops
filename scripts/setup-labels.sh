#!/usr/bin/env bash
# 建立 wayfinder + loop 自動化需要的所有 label(三個 repo)。
# 冪等:--force 會更新既有 label 的顏色與描述,不會報錯。
set -euo pipefail

REPOS=(
  "TaihemaoOrg/planning"
  "TaihemaoOrg/linebot-saas-backend"
  "TaihemaoOrg/linebot-saas-frontend"
)

# name|color|description
LABELS=(
  # ── mattpocock-skills canonical:triage 五角色 ──────────────────────
  # writer: triage skill / 人。frontend 目前缺 needs-triage 與 needs-info。
  # 顏色沿用 backend 既有值,避免視覺變動。
  "needs-triage|FBCA04|Maintainer needs to evaluate this issue"
  "needs-info|D4C5F9|Waiting on reporter for more information"
  "ready-for-agent|0E8A16|Triaged PRD, ready for an agent to implement"
  "ready-for-human|1D76DB|Requires human implementation"
  "wontfix|FFFFFF|This will not be worked on"

  # ── mattpocock-skills canonical:wayfinder ─────────────────────────
  # writer: wayfinder skill。frontend 目前五個全缺。
  "wayfinder:map|0E8A16|Wayfinder map (canonical route artifact)"
  "wayfinder:grilling|5319E7|Wayfinder ticket type: grilling (HITL)"
  "wayfinder:prototype|C2E0C6|Wayfinder ticket type: prototype (HITL)"
  "wayfinder:research|0052CC|Wayfinder ticket type: research (AFK)"
  "wayfinder:task|FBCA04|Wayfinder ticket type: task"

  # ── 本地擴充(不在 mattpocock-skills 規格內)────────────────────────
  # wayfinder:ticket 是我們自己加的「所有決策票」聚合 label(backend 已用在 61 張)。
  # skill 不讀它;純粹讓一次查詢就撈出所有決策票,不必分四種類型查。
  # 顏色改用 0969DA,避免與 ready-for-human 的 1D76DB 撞色。
  "wayfinder:ticket|0969DA|[local] Any wayfinder decision ticket (child of a map)"

  # 升級 workflow / 實作 loop 寫的(本設計新增,不在 skills 規格內)
  "agent:queued|9198A1|Authorized for agent, waiting on blockers (writer: to-tickets)"
  "agent:implement|1F6FEB|All blockers closed - implementer loop trigger (writer: promote-queued workflow)"
  "agent:in-progress|D4A72C|An agent session has claimed this (writer: loops)"
  "agent:blocked|CF222E|Error flag: promotion refused or implementation blocked (writer: workflows/loops)"
  # 人寫的(本設計新增,不在 skills 規格內)
  "decision:a|006B75|Human decision: option A"
  "decision:b|8250DF|Human decision: option B"
  "decision:c|BF3989|Human decision: option C"
  "decision:approve|2DA44E|Human decision: adopt the agent's recommendation"
  "decision:discuss|E16F24|Human has concerns, wants to discuss"
)

for repo in "${REPOS[@]}"; do
  echo "== $repo"
  for entry in "${LABELS[@]}"; do
    IFS='|' read -r name color desc <<<"$entry"
    gh label create "$name" --repo "$repo" --color "$color" --description "$desc" --force
    echo "  ok: $name"
  done
done

echo "done."
