#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
LOCAL_SKILLS_DIR="$ROOT_DIR/.codex/skills"
GLOBAL_SKILLS_DIR="$HOME/.codex/skills"
STAMP="$(date +%Y%m%d-%H%M%S)"
ARCHIVE_DIR="$HOME/.codex/skills-archive/work-overlap-$STAMP"

targets=(
  "coconala-listing-ja"
  "coconala-reply-bugfix-ja"
  "coconala-reply-ja"
  "delivery-pack-ja"
  "japanese-chat-natural-ja"
  "scope-judge-ja"
)

moved=0
mkdir -p "$ARCHIVE_DIR"

for name in "${targets[@]}"; do
  if [[ -d "$LOCAL_SKILLS_DIR/$name" && -d "$GLOBAL_SKILLS_DIR/$name" ]]; then
    mv "$GLOBAL_SKILLS_DIR/$name" "$ARCHIVE_DIR/$name"
    echo "[OK] archived overlapping global skill: $GLOBAL_SKILLS_DIR/$name -> $ARCHIVE_DIR/$name"
    moved=1
  fi
done

if [[ $moved -eq 0 ]]; then
  rmdir "$ARCHIVE_DIR" 2>/dev/null || true
  echo "[OK] no overlapping global work skills found under: $GLOBAL_SKILLS_DIR"
  exit 0
fi

echo "[INFO] archived overlapping global work skills under: $ARCHIVE_DIR"
echo "[INFO] built-in global system skills remain under: $GLOBAL_SKILLS_DIR/.system"
