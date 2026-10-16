#!/usr/bin/env python3
"""看板 Status 欄位的 13 個選項:比對現況,或產生 updateProjectV2Field 的 GraphQL body。

用法:
  board-status.py check    < field.json
  board-status.py mutation < field.json > body.json

field.json 是 Status 欄位的 GraphQL 結果:{"id": "...", "options": [{"id", "name", ...}]}。
取得方法見 skills/setup/SKILL.md 步驟 5。

check 的結束碼:0 = 13 個選項與順序都一致;1 = 名稱一致但順序不同;
2 = 有缺少或多出的選項;3 = 本檔清單與 sync-project-status.yml 不一致(plugin 本身有錯)。

mutation 產生的 body 用 `gh api graphql --input body.json` 送出。名稱相同的既有選項
會帶上原本的 id,卡片上的 Status 值不會被清掉;不在清單中的選項會被刪除。
"""

import json
import re
import sys
from pathlib import Path

# 看板上由左到右的順序。名稱必須與 workflows/sync-project-status.yml 逐字一致。
STATUS_OPTIONS = [
    ("⏳ 等你決定", "ORANGE", "HITL decision ticket 的 decision packet 已備好,等人貼 decision label"),
    ("🔍 準備選項中", "GRAY", "decision ticket 已開,尚未 assign 給人"),
    ("💬 討論中", "PINK", "已貼 decision:discuss,等 agent 回覆"),
    ("💡 收件匣", "YELLOW", "planning repo 上剛開的想法,等 cartographer 接手"),
    ("🗺️ 規劃中", "BLUE", "wayfinder:map,決策進行中"),
    ("🤖 查證中", "BLUE", "wayfinder:research 或未 assign 的 task,由 agent 處理"),
    ("✅ 已決定,待收斂", "GREEN", "人已貼 decision label,等 resolver 記錄並關閉"),
    ("📋 排隊中", "GRAY", "agent:queued,還有 open 的 blocker"),
    ("🚀 可實作", "PURPLE", "agent:implement,blocker 已全部關閉,等 implementer claim"),
    ("⚡ 實作中", "YELLOW", "agent:in-progress,有 session 正在處理"),
    ("👀 待你 review", "ORANGE", "有 open 的 PR 會關閉這張 ticket"),
    ("🚫 卡住", "RED", "agent:blocked,錯誤旗標,需要人處理"),
    ("✔️ 已關閉", "GRAY", "issue 已關閉"),
]

SYNC_WORKFLOW = Path(__file__).resolve().parent.parent / "workflows" / "sync-project-status.yml"

MUTATION = (
    "mutation($input:UpdateProjectV2FieldInput!){"
    "updateProjectV2Field(input:$input){projectV2Field{"
    "... on ProjectV2SingleSelectField{id name options{id name}}}}}"
)


def workflow_status_names():
    text = SYNC_WORKFLOW.read_text(encoding="utf-8")
    return set(re.findall(r'status="([^"]+)"', text))


def self_check():
    expected = {name for name, _, _ in STATUS_OPTIONS}
    actual = workflow_status_names()
    if expected != actual or len(STATUS_OPTIONS) != 13:
        print("❌ board-status.py 的清單與 sync-project-status.yml 不一致:", file=sys.stderr)
        print(f"   只在本檔:{sorted(expected - actual)}", file=sys.stderr)
        print(f"   只在 workflow:{sorted(actual - expected)}", file=sys.stderr)
        sys.exit(3)


def read_field():
    field = json.load(sys.stdin)
    if not field or "options" not in field:
        print("❌ 輸入不是 Status 欄位(沒有 options)。", file=sys.stderr)
        sys.exit(2)
    return field


def check(field):
    current = [o["name"] for o in field["options"]]
    wanted = [name for name, _, _ in STATUS_OPTIONS]
    missing = [n for n in wanted if n not in current]
    extra = [n for n in current if n not in wanted]
    if missing or extra:
        print(f"缺少:{missing}")
        print(f"多出:{extra}")
        return 2
    if current != wanted:
        print("名稱一致,順序不同。")
        print(f"現在:{current}")
        print(f"建議:{wanted}")
        return 1
    print("13 個選項與順序一致。")
    return 0


def mutation(field):
    existing = {o["name"]: o["id"] for o in field["options"]}
    options = []
    for name, color, description in STATUS_OPTIONS:
        option = {"name": name, "color": color, "description": description}
        if name in existing:
            option["id"] = existing[name]
        options.append(option)
    body = {
        "query": MUTATION,
        "variables": {"input": {"fieldId": field["id"], "singleSelectOptions": options}},
    }
    json.dump(body, sys.stdout, ensure_ascii=False, indent=2)
    print()
    return 0


def main():
    if len(sys.argv) != 2 or sys.argv[1] not in ("check", "mutation"):
        print(__doc__, file=sys.stderr)
        sys.exit(64)
    self_check()
    field = read_field()
    if sys.argv[1] == "check":
        sys.exit(check(field))
    sys.exit(mutation(field))


if __name__ == "__main__":
    main()
