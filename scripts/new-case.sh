#!/usr/bin/env bash
set -euo pipefail

if [ "$#" -gt 1 ]; then
  echo "Usage: $0 [case-id]"
  echo "Examples:"
  echo "  $0            # auto -> case-001, case-002..."
  echo "  $0 7          # -> case-007"
  echo "  $0 case-015   # explicit"
  exit 1
fi

ROOT="$(cd "$(dirname "$0")/.." && pwd)"
TEMPLATE="$ROOT/cases/_case-template"

next_case_id() {
  local max_num next_num
  max_num="$(
    find "$ROOT/cases/ACTIVE" "$ROOT/cases/HOLD" "$ROOT/cases/CLOSED" \
      -mindepth 1 -maxdepth 1 -type d -printf '%f\n' 2>/dev/null \
      | sed -n 's/^case-\([0-9][0-9][0-9]\)$/\1/p' \
      | sort -n \
      | tail -n 1
  )"

  if [ -z "${max_num:-}" ]; then
    next_num=1
  else
    next_num=$((10#$max_num + 1))
  fi

  printf "case-%03d" "$next_num"
}

normalize_case_id() {
  local raw="$1"
  if [[ "$raw" =~ ^[0-9]+$ ]]; then
    printf "case-%03d" "$((10#$raw))"
    return
  fi

  if [[ "$raw" =~ ^case-[0-9]{3}$ ]]; then
    printf "%s" "$raw"
    return
  fi

  return 1
}

if [ "$#" -eq 0 ]; then
  CASE_ID="$(next_case_id)"
else
  if ! CASE_ID="$(normalize_case_id "$1")"; then
    echo "Invalid case-id: $1"
    echo "Use numeric (e.g. 7) or case-XXX (e.g. case-007)."
    exit 1
  fi
fi

DEST="$ROOT/cases/ACTIVE/$CASE_ID"

if [ -e "$DEST" ]; then
  echo "Case already exists: $DEST"
  exit 1
fi

cp -R "$TEMPLATE" "$DEST"

# Quick metadata stub
cat > "$DEST/CASE.md" <<CASE
# CASE

- Case ID: $CASE_ID
- Service ID: bugfix-15000
- Service Name: Next.js/Stripe不具合診断・修正
- Status: ACTIVE
- Created: $(date +%F)
- Platform: Coconala
- Pricing Model: Base 15000 + Option(Add Fix 15000 / Add Research 30m 5000)
- Scope:
CASE

echo "Created case: $DEST"
echo "Next: edit $DEST/CASE.md and $DEST/README.md"
