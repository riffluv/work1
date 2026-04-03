#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
SKILLS_DIR="$ROOT_DIR/.codex/skills"
GLOBAL_SKILLS_DIR="$HOME/.codex/skills"

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

global_conflicts=(
  "coconala-listing-ja"
  "coconala-reply-bugfix-ja"
  "coconala-reply-ja"
  "delivery-pack-ja"
  "japanese-chat-natural-ja"
  "scope-judge-ja"
)

status=0
for rel in "${required[@]}"; do
  if [[ ! -f "$SKILLS_DIR/$rel" ]]; then
    echo "[NG] missing: $SKILLS_DIR/$rel"
    status=1
  fi
done

for name in "${global_conflicts[@]}"; do
  if [[ -d "$GLOBAL_SKILLS_DIR/$name" ]]; then
    echo "[NG] global overlap still active: $GLOBAL_SKILLS_DIR/$name"
    echo "[HINT] archive it with: $ROOT_DIR/scripts/archive-global-work-skills.sh"
    status=1
  fi
done

if [[ $status -eq 0 ]]; then
  echo "[OK] project-local skills are ready and no overlapping global work skills are active: $SKILLS_DIR"
else
  exit 1
fi
