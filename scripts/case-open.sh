#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
OPEN_DIR="$ROOT_DIR/ops/cases/open"
CLOSED_DIR="$ROOT_DIR/ops/cases/closed"
TEMPLATE_FILE="$ROOT_DIR/os/case/readme-template.md"
ACTIVE_CASE_FILE="$ROOT_DIR/runtime/active-case.txt"
MODE_FILE="$ROOT_DIR/runtime/mode.txt"

service_id=""
route=""
phase="implementation"
scope_status="undecided"
client_summary=""
current_decision=""
next_action=""
implementation_focus=""
delivery_status="not_started"

escape_replacement() {
  printf '%s' "$1" | sed -e 's/[|&\\]/\\&/g'
}

while [[ $# -gt 0 ]]; do
  case "$1" in
    --service-id) service_id="${2:-}"; shift 2 ;;
    --route) route="${2:-}"; shift 2 ;;
    --phase) phase="${2:-}"; shift 2 ;;
    --scope-status) scope_status="${2:-}"; shift 2 ;;
    --client-summary) client_summary="${2:-}"; shift 2 ;;
    --current-decision) current_decision="${2:-}"; shift 2 ;;
    --next-action) next_action="${2:-}"; shift 2 ;;
    --implementation-focus) implementation_focus="${2:-}"; shift 2 ;;
    --delivery-status) delivery_status="${2:-}"; shift 2 ;;
    *) echo "Unknown argument: $1" >&2; exit 1 ;;
  esac
done

if [[ -z "$service_id" || -z "$route" ]]; then
  echo "Usage: $0 --service-id <service_id> --route <service|profile|message|talkroom> [--phase implementation] [--scope-status ...] [--client-summary ...] [--current-decision ...] [--next-action ...] [--implementation-focus ...] [--delivery-status ...]" >&2
  exit 1
fi

date_part="$(date +%Y%m%d)"
timestamp="$(date '+%Y-%m-%d %H:%M JST')"

max_seq="$(
  find "$OPEN_DIR" "$CLOSED_DIR" -mindepth 1 -maxdepth 1 -type d -printf '%f\n' 2>/dev/null \
    | sed -n "s/^${date_part}-\\([0-9][0-9]\\)-.*$/\\1/p" \
    | sort -n | tail -n 1
)"

if [[ -z "${max_seq:-}" ]]; then
  seq="01"
else
  seq="$(printf '%02d' $((10#$max_seq + 1)))"
fi

case_id="${date_part}-${seq}-${route}"
case_dir="$OPEN_DIR/$case_id"
readme="$case_dir/README.md"

mkdir -p "$case_dir" "$(dirname "$ACTIVE_CASE_FILE")"

sed \
  -e "s|{{CASE_ID}}|$(escape_replacement "$case_id")|g" \
  -e "s|{{STARTED_AT}}|$(escape_replacement "$timestamp")|g" \
  -e "s|{{SERVICE_ID}}|$(escape_replacement "$service_id")|g" \
  -e "s|{{ROUTE}}|$(escape_replacement "$route")|g" \
  -e "s|{{PHASE}}|$(escape_replacement "$phase")|g" \
  -e "s|{{SCOPE_STATUS}}|$(escape_replacement "$scope_status")|g" \
  -e "s|{{CLIENT_SUMMARY}}|$(escape_replacement "$client_summary")|g" \
  -e "s|{{CURRENT_DECISION}}|$(escape_replacement "$current_decision")|g" \
  -e "s|{{NEXT_ACTION}}|$(escape_replacement "$next_action")|g" \
  -e "s|{{IMPLEMENTATION_FOCUS}}|$(escape_replacement "$implementation_focus")|g" \
  -e "s|{{DELIVERY_STATUS}}|$(escape_replacement "$delivery_status")|g" \
  "$TEMPLATE_FILE" > "$readme"

printf '%s\n' "$case_id" > "$ACTIVE_CASE_FILE"
printf '%s\n' "$phase" > "$MODE_FILE"

printf 'case_id=%s\n' "$case_id"
printf 'dir=%s\n' "$case_dir"
printf 'readme=%s\n' "$readme"
