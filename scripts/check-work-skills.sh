#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
SKILLS_DIR="$ROOT_DIR/.codex/skills"

required=(
  "coconala-intake-router-ja/SKILL.md"
  "coconala-listing-ja/SKILL.md"
  "coconala-prequote-ops-ja/SKILL.md"
  "coconala-reply-bugfix-ja/SKILL.md"
  "coconala-reply-ja/SKILL.md"
  "delivery-pack-ja/SKILL.md"
  "japanese-chat-natural-ja/SKILL.md"
  "reply-review-prompt-ja/SKILL.md"
  "scope-judge-ja/SKILL.md"
)

missing=0
for rel in "${required[@]}"; do
  if [[ ! -f "$SKILLS_DIR/$rel" ]]; then
    echo "[NG] missing: $SKILLS_DIR/$rel"
    missing=1
  fi
done

if [[ $missing -eq 0 ]]; then
  echo "[OK] project-local skills are ready: $SKILLS_DIR"
else
  exit 1
fi
