#!/usr/bin/env bash
set -euo pipefail

if ! command -v agent-reach >/dev/null 2>&1; then
  echo "[NG] agent-reach is not installed."
  echo "Install path expected in user space, for example: ~/.local/bin/agent-reach"
  exit 1
fi

echo "agent-reach=$(command -v agent-reach)"
echo
agent-reach doctor
