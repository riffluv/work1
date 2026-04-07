#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
MODE_FILE="$ROOT_DIR/runtime/mode.txt"
ACTIVE_CASE_FILE="$ROOT_DIR/runtime/active-case.txt"
REPLY_FILE="$ROOT_DIR/runtime/replies/latest.txt"
LATEST_MEMORY_FILE="$ROOT_DIR/runtime/replies/latest-memory.json"
SERVICE_REGISTRY="$ROOT_DIR/os/core/service-registry.yaml"

mode="(missing)"
active_case="(none)"

if [[ -f "$MODE_FILE" ]]; then
  mode="$(tr -d '\n' < "$MODE_FILE")"
fi

if [[ -f "$ACTIVE_CASE_FILE" ]] && [[ -s "$ACTIVE_CASE_FILE" ]]; then
  active_case="$(tr -d '\n' < "$ACTIVE_CASE_FILE")"
fi

echo "現在モード=$mode"
echo "進行中案件=$active_case"
echo "返信保存先=$REPLY_FILE"

if [[ "$active_case" != "(none)" ]]; then
  readme="$ROOT_DIR/ops/cases/open/$active_case/README.md"
  reply_memory="$ROOT_DIR/ops/cases/open/$active_case/reply-memory.json"
  if [[ -f "$readme" ]]; then
    echo "案件メモ=$readme"
    sed -n 's/^- service_id: /サービスID=/p' "$readme" | head -n 1
    sed -n 's/^- route: /経路=/p' "$readme" | head -n 1
    sed -n 's/^- phase: /フェーズ=/p' "$readme" | head -n 1
    sed -n 's/^- scope_status: /スコープ状態=/p' "$readme" | head -n 1
    sed -n 's/^- next_action: /次アクション=/p' "$readme" | head -n 1
    sed -n 's/^- delivery_status: /納品状態=/p' "$readme" | head -n 1
    if [[ -f "$reply_memory" ]]; then
      echo "返信memory=$reply_memory"
      followup_count="$(sed -n 's/.*"followup_count":[[:space:]]*\([0-9][0-9]*\).*/\1/p' "$reply_memory" | head -n 1)"
      previous_deadline="$(sed -n 's/.*"previous_deadline_promised":[[:space:]]*"\([^"]*\)".*/\1/p' "$reply_memory" | head -n 1)"
      prior_tone="$(sed -n 's/.*"prior_tone":[[:space:]]*"\([^"]*\)".*/\1/p' "$reply_memory" | head -n 1)"
      echo "followup回数=${followup_count:-0}"
      if [[ -n "${previous_deadline:-}" ]]; then
        echo "前回約束時刻=$previous_deadline"
      fi
      if [[ -n "${prior_tone:-}" ]]; then
        echo "前回トーン=$prior_tone"
      fi
    else
      echo "返信memory=(missing)"
    fi
  else
    echo "案件メモ=(missing)"
  fi
else
  if [[ -f "$LATEST_MEMORY_FILE" ]]; then
    echo "直近memory=$LATEST_MEMORY_FILE"
  fi
fi

echo "公開中サービス="
awk '
  /^services:/ { in_services = 1; next }
  /^rules:/ { in_services = 0 }
  in_services && /service_id:/ {
    current = $NF
    next
  }
  in_services && /public:[[:space:]]*true/ && current != "" {
    print "- " current
  }
' "$SERVICE_REGISTRY"
