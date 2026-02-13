#!/usr/bin/env bash
set -euo pipefail

usage() {
  cat <<'EOF'
Usage:
  ./scripts/strip-leading-space-clipboard.sh [--all|--two]

Options:
  --all  Remove all leading whitespace from each line (default)
  --two  Remove only 2 leading spaces from each line
EOF
}

mode="${1:---all}"

if ! command -v powershell.exe >/dev/null 2>&1 || ! command -v clip.exe >/dev/null 2>&1; then
  echo "Error: powershell.exe and clip.exe are required (WSL on Windows)." >&2
  exit 1
fi

case "$mode" in
  --all)
    powershell.exe -NoProfile -Command "Get-Clipboard -Raw" \
      | sed -E 's/^[[:space:]]+//' \
      | clip.exe
    ;;
  --two)
    powershell.exe -NoProfile -Command "Get-Clipboard -Raw" \
      | sed -E 's/^  //' \
      | clip.exe
    ;;
  -h|--help)
    usage
    exit 0
    ;;
  *)
    usage
    exit 1
    ;;
esac

echo "Clipboard updated: leading spaces stripped (${mode})."
