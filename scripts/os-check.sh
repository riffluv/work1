#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
RUNTIME_DIR="$ROOT_DIR/runtime"
REPLIES_DIR="$RUNTIME_DIR/replies"
MODE_FILE="$RUNTIME_DIR/mode.txt"
ACTIVE_CASE_FILE="$RUNTIME_DIR/active-case.txt"

required_paths=(
  "$ROOT_DIR/os/core/boot.md"
  "$ROOT_DIR/os/core/policy.yaml"
  "$ROOT_DIR/os/core/service-registry.yaml"
  "$ROOT_DIR/os/coconala/boot.md"
  "$ROOT_DIR/os/coconala/prequote.md"
  "$ROOT_DIR/os/coconala/reply.md"
  "$ROOT_DIR/os/implementation/boot.md"
  "$ROOT_DIR/os/implementation/protocol.md"
  "$ROOT_DIR/os/delivery/boot.md"
  "$ROOT_DIR/os/case/readme-template.md"
  "$ROOT_DIR/scripts/case-open.sh"
  "$ROOT_DIR/scripts/case-note.sh"
  "$ROOT_DIR/scripts/case-phase.sh"
  "$ROOT_DIR/scripts/case-close.sh"
  "$ROOT_DIR/scripts/reply-save.sh"
  "$ROOT_DIR/scripts/check-internal-os-flows.sh"
  "$ROOT_DIR/scripts/internal-os-status.sh"
)

for path in "${required_paths[@]}"; do
  if [[ ! -e "$path" ]]; then
    echo "[NG] missing internal-os path: $path"
    exit 1
  fi
done

"$ROOT_DIR/scripts/check-work-skills.sh"
"$ROOT_DIR/scripts/check-coconala-bootstrap.sh"

mkdir -p "$REPLIES_DIR"

if [[ ! -f "$MODE_FILE" ]]; then
  printf 'coconala\n' > "$MODE_FILE"
fi

if [[ ! -f "$ACTIVE_CASE_FILE" ]]; then
  : > "$ACTIVE_CASE_FILE"
fi

if [[ ! -f "$REPLIES_DIR/latest.txt" ]]; then
  : > "$REPLIES_DIR/latest.txt"
fi

echo "[OK] internal os runtime ready"
echo "[INFO] mode=$(tr -d '\n' < "$MODE_FILE")"
