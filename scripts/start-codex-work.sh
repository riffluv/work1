#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
export CODEX_HOME="$ROOT_DIR/.codex"

find_codex_bin() {
  if command -v codex >/dev/null 2>&1; then
    command -v codex
    return 0
  fi

  local candidates=(
    "$HOME/.local/bin/codex"
    "$HOME/.npm-global/bin/codex"
    "$HOME/.yarn/bin/codex"
  )
  local candidate=""

  for candidate in /mnt/c/Users/*/AppData/Local/Yarn/Data/global/node_modules/.bin/codex; do
    candidates+=("$candidate")
  done

  for candidate in "${candidates[@]}"; do
    if [[ -x "$candidate" ]]; then
      printf '%s\n' "$candidate"
      return 0
    fi
  done

  return 1
}

if ! CODEX_BIN="$(find_codex_bin)"; then
  echo "[ERROR] codex command not found."
  echo "[HINT] Install codex-cli or add its bin directory to PATH."
  echo "[HINT] Current CODEX_HOME is set to: $CODEX_HOME"
  exit 1
fi

exec "$CODEX_BIN" "$@"
