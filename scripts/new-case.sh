#!/usr/bin/env bash
set -euo pipefail

if [ "$#" -lt 1 ]; then
  echo "Usage: $0 <case-slug>"
  echo "Example: $0 20260210-coconala-stripe-webhook-fix"
  exit 1
fi

ROOT="$(cd "$(dirname "$0")/.." && pwd)"
TEMPLATE="$ROOT/cases/_case-template"
DEST="$ROOT/cases/ACTIVE/$1"

if [ -e "$DEST" ]; then
  echo "Case already exists: $DEST"
  exit 1
fi

cp -R "$TEMPLATE" "$DEST"

# Quick metadata stub
cat > "$DEST/CASE.md" <<CASE
# CASE

- Case ID: $1
- Status: ACTIVE
- Created: $(date +%F)
- Platform: Coconala
- Plan: (LIGHT/STANDARD/PREMIUM)
- Scope:
CASE

echo "Created case: $DEST"
echo "Next: edit $DEST/CASE.md and $DEST/README.md"
