#!/usr/bin/env bash
set -euo pipefail

if [ "$#" -ne 2 ]; then
  echo "Usage: $0 <case-id> <ACTIVE|HOLD|CLOSED>"
  echo "Example: $0 case-001 HOLD"
  exit 1
fi

ROOT="$(cd "$(dirname "$0")/.." && pwd)"
CASE="$1"
TARGET="$2"

if [[ "$TARGET" != "ACTIVE" && "$TARGET" != "HOLD" && "$TARGET" != "CLOSED" ]]; then
  echo "Target must be ACTIVE, HOLD, or CLOSED"
  exit 1
fi

SRC=""
for s in ACTIVE HOLD CLOSED; do
  if [ -d "$ROOT/cases/$s/$CASE" ]; then
    SRC="$ROOT/cases/$s/$CASE"
    break
  fi
done

if [ -z "$SRC" ]; then
  echo "Case not found: $CASE"
  exit 1
fi

DEST="$ROOT/cases/$TARGET/$CASE"
if [ "$SRC" = "$DEST" ]; then
  echo "Already in $TARGET"
  exit 0
fi

mv "$SRC" "$DEST"
echo "Moved: $CASE -> $TARGET"
