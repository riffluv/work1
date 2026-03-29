#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
ACTIVE_CASE_FILE="$ROOT_DIR/runtime/active-case.txt"

case_id=""
decision=""
reason=""
scope=""
price=""
next_action=""

while [[ $# -gt 0 ]]; do
  case "$1" in
    --case-id) case_id="${2:-}"; shift 2 ;;
    --decision) decision="${2:-}"; shift 2 ;;
    --reason) reason="${2:-}"; shift 2 ;;
    --scope) scope="${2:-}"; shift 2 ;;
    --price) price="${2:-}"; shift 2 ;;
    --next-action) next_action="${2:-}"; shift 2 ;;
    *) echo "Unknown argument: $1" >&2; exit 1 ;;
  esac
done

if [[ -z "$case_id" && -f "$ACTIVE_CASE_FILE" ]]; then
  case_id="$(tr -d '\n' < "$ACTIVE_CASE_FILE")"
fi

if [[ -z "$case_id" ]]; then
  echo "[NG] no active case" >&2
  exit 1
fi

readme="$ROOT_DIR/ops/cases/open/$case_id/README.md"
if [[ ! -f "$readme" ]]; then
  echo "[NG] open case README not found: $readme" >&2
  exit 1
fi

timestamp="$(date '+%Y-%m-%d %H:%M JST')"
note_block="$(cat <<EOF
### ${timestamp}
- decision: ${decision}
- reason: ${reason}
- scope: ${scope}
- price: ${price}
- next_action: ${next_action}

EOF
)"

tmp_file="$(mktemp)"
trap 'rm -f "$tmp_file"' EXIT

awk -v block="$note_block" '
  BEGIN { inserted = 0 }
  /^## Delivery Notes$/ && !inserted {
    printf "%s\n\n", block
    inserted = 1
  }
  { print }
  END {
    if (!inserted) {
      printf "%s\n\n", block
    }
  }
' "$readme" > "$tmp_file"

mv "$tmp_file" "$readme"
trap - EXIT

printf 'readme=%s\n' "$readme"
