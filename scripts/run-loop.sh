#!/usr/bin/env bash
# 每一輪都用全新的 headless claude session 跑一條 loop,ctx 不累積。
#
# 用法:
#   run-loop.sh resolver 600        # 每 600 秒開一個新 session 跑一輪 /resolver
#   run-loop.sh cartographer 1200
#   run-loop.sh researcher 900
#   run-loop.sh implementer 900     # implementer 需要寬權限,見下方註解
#   run-loop.sh prototyper 1800     # prototyper 同樣需要寬權限
#
# 停止:Ctrl+C 或關掉終端機。log 在 ~/wayfinder-loops/logs/<loop>.log
set -euo pipefail

LOOP="${1:?usage: run-loop.sh <cartographer|resolver|researcher|implementer|prototyper> [interval-seconds]}"
INTERVAL="${2:-900}"
LOG_DIR="$HOME/wayfinder-loops/logs"
mkdir -p "$LOG_DIR"
LOG="$LOG_DIR/$LOOP.log"

# 各 loop 需要的工具白名單(headless 跑不能互動授權,只能事先放行)
case "$LOOP" in
  cartographer|resolver)
    TOOLS=(--allowedTools "Bash(gh:*)" "Read" "Grep" "Glob")
    ;;
  researcher)
    TOOLS=(--allowedTools "Bash(gh:*)" "Read" "Grep" "Glob" "WebFetch" "WebSearch")
    ;;
  implementer|prototyper)
    # 這兩條要寫程式、跑測試、開 worktree(prototyper 還要 build 與發 Artifact 頁),
    # 白名單列不完。兩個選擇:(1) 用互動式 /loop 跑它(建議,起碼初期);
    #                        (2) 信任環境下解開下面這行,改用全權模式。
    # TOOLS=(--dangerously-skip-permissions)
    echo "$LOOP 建議用互動式 /loop 跑;要 headless 請先閱讀本腳本內的註解再解開全權模式。" >&2
    exit 1
    ;;
  *)
    echo "unknown loop: $LOOP" >&2; exit 1
    ;;
esac

while true; do
  echo "===== $(date -Is) $LOOP round start =====" >>"$LOG"
  claude -p "/$LOOP" "${TOOLS[@]}" >>"$LOG" 2>&1 \
    || echo "round failed (exit $?)" >>"$LOG"
  echo "===== $(date -Is) round end, sleep ${INTERVAL}s =====" >>"$LOG"
  sleep "$INTERVAL"
done
