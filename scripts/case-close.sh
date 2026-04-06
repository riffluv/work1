#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
OPEN_DIR="$ROOT_DIR/ops/cases/open"
CLOSED_DIR="$ROOT_DIR/ops/cases/closed"
ACTIVE_CASE_FILE="$ROOT_DIR/runtime/active-case.txt"
MODE_FILE="$ROOT_DIR/runtime/mode.txt"
CASE_LOG="$ROOT_DIR/ops/case-log.csv"
LATEST_MEMORY_FILE="$ROOT_DIR/runtime/replies/latest-memory.json"

case_id=""
final_phase="closed"
amount=""
outcome=""
scope_status=""
additional_handling=""
review_risk=""
reuse_hint=""
notes=""

while [[ $# -gt 0 ]]; do
  case "$1" in
    --case-id) case_id="${2:-}"; shift 2 ;;
    --final-phase) final_phase="${2:-}"; shift 2 ;;
    --amount) amount="${2:-}"; shift 2 ;;
    --outcome) outcome="${2:-}"; shift 2 ;;
    --scope-status) scope_status="${2:-}"; shift 2 ;;
    --additional-handling) additional_handling="${2:-}"; shift 2 ;;
    --review-risk) review_risk="${2:-}"; shift 2 ;;
    --reuse-hint) reuse_hint="${2:-}"; shift 2 ;;
    --notes) notes="${2:-}"; shift 2 ;;
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

open_dir="$OPEN_DIR/$case_id"
open_readme="$open_dir/README.md"
closed_dir="$CLOSED_DIR/$case_id"
closed_readme="$closed_dir/README.md"

if [[ ! -f "$open_readme" ]]; then
  echo "[NG] open case README not found: $open_readme" >&2
  exit 1
fi

extract_field() {
  local key="$1"
  sed -n "s/^- ${key}: //p" "$open_readme" | head -n 1
}

started_at="$(extract_field started_at)"
service_id="$(extract_field service_id)"
route="$(extract_field route)"
next_action="$(extract_field next_action)"

if [[ -z "$scope_status" ]]; then
  scope_status="$(extract_field scope_status)"
fi

mid_snapshots="$(awk '/^## Mid Snapshots/{flag=1; next} /^## Delivery Notes/{flag=0} flag{print}' "$open_readme")"
closed_at="$(date '+%Y-%m-%d %H:%M JST')"

mkdir -p "$CLOSED_DIR"
mv "$open_dir" "$closed_dir"

cat > "$closed_readme" <<EOF
# ${case_id}

- started_at: ${started_at}
- closed_at: ${closed_at}
- service_id: ${service_id}
- route: ${route}
- final_phase: ${final_phase}
- scope_status: ${scope_status}
- amount: ${amount}
- outcome: ${outcome}

## What Happened
- issue:
- fix:
- verification:

## Scope Notes
- additional_handling: ${additional_handling}

## Ops Memo
- review_risk: ${review_risk}
- reuse_hint: ${reuse_hint}

## Mid Snapshots
${mid_snapshots}
EOF

if [[ ! -f "$CASE_LOG" ]] || ! head -n 1 "$CASE_LOG" | grep -Fq 'date,case_id,service_id,route,final_phase,scope_status,next_action,outcome,notes'; then
  cat > "$CASE_LOG" <<'EOF'
date,case_id,service_id,route,final_phase,scope_status,next_action,outcome,notes
EOF
fi

printf '%s,%s,%s,%s,%s,%s,%s,%s,%s\n' \
  "$(date +%Y-%m-%d)" \
  "$case_id" \
  "$service_id" \
  "$route" \
  "$final_phase" \
  "$scope_status" \
  "$next_action" \
  "$outcome" \
  "$notes" >> "$CASE_LOG"

: > "$ACTIVE_CASE_FILE"
printf 'coconala\n' > "$MODE_FILE"
mkdir -p "$(dirname "$LATEST_MEMORY_FILE")"
cat > "$LATEST_MEMORY_FILE" <<'EOF'
{
  "followup_count": 0,
  "prior_tone": "neutral",
  "previous_assistant_commitment": "none",
  "previous_deadline_promised": null,
  "commitment_fulfilled": true
}
EOF

printf 'closed_case=%s\n' "$closed_dir"
