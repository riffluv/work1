#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
MODE_FILE="$ROOT_DIR/runtime/mode.txt"
ACTIVE_CASE_FILE="$ROOT_DIR/runtime/active-case.txt"
REPLY_FILE="$ROOT_DIR/runtime/replies/latest.txt"
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
  if [[ -f "$readme" ]]; then
    echo "案件メモ=$readme"
    sed -n 's/^- service_id: /サービスID=/p' "$readme" | head -n 1
    sed -n 's/^- route: /経路=/p' "$readme" | head -n 1
    sed -n 's/^- phase: /フェーズ=/p' "$readme" | head -n 1
    sed -n 's/^- scope_status: /スコープ状態=/p' "$readme" | head -n 1
    sed -n 's/^- next_action: /次アクション=/p' "$readme" | head -n 1
    sed -n 's/^- delivery_status: /納品状態=/p' "$readme" | head -n 1
  else
    echo "案件メモ=(missing)"
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
