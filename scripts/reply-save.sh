#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
REPLIES_DIR="$ROOT_DIR/runtime/replies"
TARGET_FILE="$REPLIES_DIR/latest.txt"
SOURCE_TARGET_FILE="$REPLIES_DIR/latest-source.txt"

file_input=""
text_input=""
source_file_input=""
source_text_input=""

while [[ $# -gt 0 ]]; do
  case "$1" in
    --file) file_input="${2:-}"; shift 2 ;;
    --text) text_input="${2:-}"; shift 2 ;;
    --source-file) source_file_input="${2:-}"; shift 2 ;;
    --source-text) source_text_input="${2:-}"; shift 2 ;;
    *) echo "Unknown argument: $1" >&2; exit 1 ;;
  esac
done

mkdir -p "$REPLIES_DIR"
tmp_file="$(mktemp "$REPLIES_DIR/latest.XXXXXX")"
trap 'rm -f "$tmp_file"' EXIT

if [[ -n "$file_input" ]]; then
  cat "$file_input" > "$tmp_file"
elif [[ -n "$text_input" ]]; then
  printf '%s\n' "$text_input" > "$tmp_file"
else
  cat > "$tmp_file"
fi

mv "$tmp_file" "$TARGET_FILE"
trap - EXIT

if [[ -n "$source_file_input" || -n "$source_text_input" ]]; then
  source_tmp_file="$(mktemp "$REPLIES_DIR/latest-source.XXXXXX")"
  trap 'rm -f "$source_tmp_file"' EXIT

  if [[ -n "$source_file_input" ]]; then
    cat "$source_file_input" > "$source_tmp_file"
  else
    printf '%s\n' "$source_text_input" > "$source_tmp_file"
  fi

  mv "$source_tmp_file" "$SOURCE_TARGET_FILE"
  trap - EXIT
else
  rm -f "$SOURCE_TARGET_FILE"
fi

printf 'reply=%s\n' "$TARGET_FILE"
if [[ -f "$SOURCE_TARGET_FILE" ]]; then
  printf 'source=%s\n' "$SOURCE_TARGET_FILE"
fi
