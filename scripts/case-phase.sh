#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
ACTIVE_CASE_FILE="$ROOT_DIR/runtime/active-case.txt"
MODE_FILE="$ROOT_DIR/runtime/mode.txt"

case_id=""
phase=""
delivery_status=""
current_decision=""
next_action=""
implementation_focus=""

escape_replacement() {
  printf '%s' "$1" | sed -e 's/[|&\\]/\\&/g'
}

while [[ $# -gt 0 ]]; do
  case "$1" in
    --case-id) case_id="${2:-}"; shift 2 ;;
    --phase) phase="${2:-}"; shift 2 ;;
    --delivery-status) delivery_status="${2:-}"; shift 2 ;;
    --current-decision) current_decision="${2:-}"; shift 2 ;;
    --next-action) next_action="${2:-}"; shift 2 ;;
    --implementation-focus) implementation_focus="${2:-}"; shift 2 ;;
    *) echo "Unknown argument: $1" >&2; exit 1 ;;
  esac
done

if [[ -z "$case_id" && -f "$ACTIVE_CASE_FILE" ]]; then
  case_id="$(tr -d '\n' < "$ACTIVE_CASE_FILE")"
fi

if [[ -z "$case_id" || -z "$phase" ]]; then
  echo "Usage: $0 --phase <implementation|delivery> [--case-id <case_id>] [--delivery-status ...] [--current-decision ...] [--next-action ...] [--implementation-focus ...]" >&2
  exit 1
fi

case "$phase" in
  implementation|delivery) ;;
  *)
    echo "[NG] phase must be implementation or delivery" >&2
    exit 1
    ;;
esac

readme="$ROOT_DIR/ops/cases/open/$case_id/README.md"
if [[ ! -f "$readme" ]]; then
  echo "[NG] open case README not found: $readme" >&2
  exit 1
fi

if [[ "$phase" == "delivery" && -z "$delivery_status" ]]; then
  delivery_status="preparing"
fi

tmp_file="$(mktemp)"
trap 'rm -f "$tmp_file"' EXIT

sed_script=(
  -e "s|^- phase: .*|- phase: $(escape_replacement "$phase")|"
)

if [[ -n "$delivery_status" ]]; then
  sed_script+=(-e "s|^- delivery_status: .*|- delivery_status: $(escape_replacement "$delivery_status")|")
fi

if [[ -n "$current_decision" ]]; then
  sed_script+=(-e "s|^- current_decision: .*|- current_decision: $(escape_replacement "$current_decision")|")
fi

if [[ -n "$next_action" ]]; then
  sed_script+=(-e "s|^- next_action: .*|- next_action: $(escape_replacement "$next_action")|")
fi

if [[ -n "$implementation_focus" ]]; then
  sed_script+=(-e "s|^- implementation_focus: .*|- implementation_focus: $(escape_replacement "$implementation_focus")|")
fi

sed "${sed_script[@]}" "$readme" > "$tmp_file"
mv "$tmp_file" "$readme"
trap - EXIT

printf '%s\n' "$phase" > "$MODE_FILE"

printf 'case_id=%s\n' "$case_id"
printf 'phase=%s\n' "$phase"
printf 'readme=%s\n' "$readme"
