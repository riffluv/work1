#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
OPEN_DIR="$ROOT_DIR/ops/cases/open"
ACTIVE_CASE_FILE="$ROOT_DIR/runtime/active-case.txt"
MODE_FILE="$ROOT_DIR/runtime/mode.txt"

target_selector="${1:-}"

if [[ -z "$target_selector" ]]; then
  echo "Usage: $0 <case_id|seq>" >&2
  exit 1
fi

trim() {
  printf '%s' "$1" | sed 's/^[[:space:]]*//; s/[[:space:]]*$//'
}

extract_field() {
  local key="$1"
  local file="$2"
  sed -n "s/^- ${key}: //p" "$file" | head -n 1
}

normalize_seq() {
  local raw="$1"
  raw="$(printf '%s' "$raw" | sed 's/^0*//')"
  if [[ -z "$raw" ]]; then
    raw="0"
  fi
  printf '%d' "$raw"
}

resolve_case_id() {
  local selector="$1"
  if [[ -d "$OPEN_DIR/$selector" ]]; then
    printf '%s\n' "$selector"
    return 0
  fi

  if [[ "$selector" =~ ^[0-9]+$ ]]; then
    local wanted
    wanted="$(normalize_seq "$selector")"
    local -a matches=()
    local case_id seq normalized
    while IFS= read -r case_id; do
      seq="$(printf '%s' "$case_id" | cut -d '-' -f 2)"
      [[ -n "$seq" && "$seq" =~ ^[0-9]+$ ]] || continue
      normalized="$(normalize_seq "$seq")"
      if [[ "$normalized" == "$wanted" ]]; then
        matches+=("$case_id")
      fi
    done < <(find "$OPEN_DIR" -mindepth 1 -maxdepth 1 -type d -printf '%f\n' | sort)

    case "${#matches[@]}" in
      1)
        printf '%s\n' "${matches[0]}"
        return 0
        ;;
      0)
        echo "[NG] no open case matched seq: $selector" >&2
        return 1
        ;;
      *)
        echo "[NG] seq is ambiguous: $selector" >&2
        printf '%s\n' "${matches[@]}" >&2
        return 1
        ;;
    esac
  fi

  echo "[NG] case not found: $selector" >&2
  return 1
}

target_case="$(resolve_case_id "$target_selector")"
case_dir="$OPEN_DIR/$target_case"
readme="$case_dir/README.md"
reply_memory="$case_dir/reply-memory.json"

if [[ ! -f "$readme" ]]; then
  echo "[NG] case README not found: $readme" >&2
  exit 1
fi

phase="$(sed -n 's/^- phase: //p' "$readme" | head -n 1)"
case "$phase" in
  implementation|delivery|coconala) ;;
  *) phase="implementation" ;;
esac

client_summary="$(trim "$(extract_field client_summary "$readme")")"
route="$(trim "$(extract_field route "$readme")")"
followup_count="-"
if [[ -f "$reply_memory" ]]; then
  followup_count="$(sed -n 's/.*"followup_count":[[:space:]]*\([0-9][0-9]*\).*/\1/p' "$reply_memory" | head -n 1)"
  if [[ -z "$followup_count" ]]; then
    followup_count="-"
  fi
fi

mkdir -p "$(dirname "$ACTIVE_CASE_FILE")"
printf '%s\n' "$target_case" > "$ACTIVE_CASE_FILE"
printf '%s\n' "$phase" > "$MODE_FILE"

printf '┌────────────────────────────────────────┐\n'
printf '│ ACTIVE CASE: %-25s │\n' "$target_case"
printf '│ MODE: %-32s │\n' "$phase"
printf '│ ROUTE: %-31s │\n' "${route:-unknown}"
printf '│ FOLLOWUP: %-28s │\n' "$followup_count"
printf '└────────────────────────────────────────┘\n'
if [[ -n "$client_summary" ]]; then
  printf 'summary=%s\n' "$client_summary"
fi

if [[ -f "$reply_memory" ]]; then
  printf 'reply_memory=%s\n' "$reply_memory"
else
  printf 'reply_memory=missing\n'
fi
