#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
export CODEX_HOME="$ROOT_DIR/.codex"

if ! command -v codex >/dev/null 2>&1; then
  echo "[ERROR] codex command not found. Start Codex with CODEX_HOME=$CODEX_HOME manually."
  exit 1
fi

exec codex "$@"
