#!/usr/bin/env bash
set -euo pipefail

ROOT="$(cd "$(dirname "$0")/.." && pwd)"

route=""
state="implementation"
service_id="bugfix-15000"
scope_status="undecided"
client_summary=""
current_decision=""
next_action=""
implementation_focus=""
delivery_status="not_started"

while [ "$#" -gt 0 ]; do
  case "$1" in
    --route) route="${2:-}"; shift 2 ;;
    --state) state="${2:-}"; shift 2 ;;
    --service-id) service_id="${2:-}"; shift 2 ;;
    --scope-status) scope_status="${2:-}"; shift 2 ;;
    --client-summary) client_summary="${2:-}"; shift 2 ;;
    --current-decision) current_decision="${2:-}"; shift 2 ;;
    --next-action) next_action="${2:-}"; shift 2 ;;
    --implementation-focus) implementation_focus="${2:-}"; shift 2 ;;
    --delivery-status) delivery_status="${2:-}"; shift 2 ;;
    *) echo "Unknown argument: $1" >&2; exit 1 ;;
  esac
done

if [ -z "$route" ]; then
  echo "Usage: $0 --route <service|profile|message|talkroom> [--service-id bugfix-15000] [--state implementation] [--scope-status ...] [--client-summary ...] [--current-decision ...] [--next-action ...]" >&2
  exit 1
fi

exec "$ROOT/scripts/case-open.sh" \
  --service-id "$service_id" \
  --route "$route" \
  --phase "$state" \
  --scope-status "$scope_status" \
  --client-summary "$client_summary" \
  --current-decision "$current_decision" \
  --next-action "$next_action" \
  --implementation-focus "$implementation_focus" \
  --delivery-status "$delivery_status"
