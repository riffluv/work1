#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"

START_PROMPT="$ROOT_DIR/次セッション用_起動プロンプト.txt"
NEXT_PROMPT="$ROOT_DIR/docs/next-codex-prompt.txt"
README_FILE="$ROOT_DIR/docs/README.ja.md"
AGENTS_FILE="$ROOT_DIR/AGENTS.md"
COMMENT_STYLE_FILE="$ROOT_DIR/docs/code-comment-style.ja.md"
COCONALA_PLATFORM_CONTRACT_FILE="$ROOT_DIR/os/coconala/platform-contract.yaml"
DELIVERY_SKILL_FILE="$ROOT_DIR/.codex/skills/delivery-pack-ja/SKILL.md"
HANDOFF_TEMPLATE_FILE="$ROOT_DIR/docs/handoff-delivery-template.ja.md"
CORE_BOOT_FILE="$ROOT_DIR/os/core/boot.md"
IMPLEMENTATION_BOOT_FILE="$ROOT_DIR/os/implementation/boot.md"
SERVICE_REGISTRY_FILE="$ROOT_DIR/os/core/service-registry.yaml"
CASE_OPEN_SCRIPT="$ROOT_DIR/scripts/case-open.sh"
CASE_NOTE_SCRIPT="$ROOT_DIR/scripts/case-note.sh"
CASE_PHASE_SCRIPT="$ROOT_DIR/scripts/case-phase.sh"
CASE_CLOSE_SCRIPT="$ROOT_DIR/scripts/case-close.sh"
REPLY_SAVE_SCRIPT="$ROOT_DIR/scripts/reply-save.sh"
OS_CHECK_SCRIPT="$ROOT_DIR/scripts/os-check.sh"
FLOW_SMOKE_SCRIPT="$ROOT_DIR/scripts/check-internal-os-flows.sh"
STATUS_SCRIPT="$ROOT_DIR/scripts/internal-os-status.sh"

errors=0

check_file() {
  local path="$1"
  if [[ ! -f "$path" ]]; then
    echo "[NG] missing file: $path"
    errors=1
  fi
}

require_contains() {
  local file="$1"
  local pattern="$2"
  local label="$3"
  if ! grep -Fq "$pattern" "$file"; then
    echo "[NG] $label"
    echo "      file: $file"
    echo "      required text: $pattern"
    errors=1
  fi
}

require_not_contains() {
  local file="$1"
  local pattern="$2"
  local label="$3"
  if grep -Fq "$pattern" "$file"; then
    echo "[NG] $label"
    echo "      file: $file"
    echo "      forbidden text: $pattern"
    errors=1
  fi
}

check_file "$START_PROMPT"
check_file "$NEXT_PROMPT"
check_file "$README_FILE"
check_file "$AGENTS_FILE"
check_file "$COMMENT_STYLE_FILE"
check_file "$COCONALA_PLATFORM_CONTRACT_FILE"
check_file "$DELIVERY_SKILL_FILE"
check_file "$HANDOFF_TEMPLATE_FILE"
check_file "$CORE_BOOT_FILE"
check_file "$IMPLEMENTATION_BOOT_FILE"
check_file "$SERVICE_REGISTRY_FILE"
check_file "$CASE_OPEN_SCRIPT"
check_file "$CASE_NOTE_SCRIPT"
check_file "$CASE_PHASE_SCRIPT"
check_file "$CASE_CLOSE_SCRIPT"
check_file "$REPLY_SAVE_SCRIPT"
check_file "$OS_CHECK_SCRIPT"
check_file "$FLOW_SMOKE_SCRIPT"
check_file "$STATUS_SCRIPT"

if [[ $errors -ne 0 ]]; then
  exit 1
fi

require_contains "$START_PROMPT" "./scripts/check-work-skills.sh" "start prompt must run skill availability check"
require_contains "$START_PROMPT" "./scripts/check-coconala-bootstrap.sh" "start prompt must run bootstrap guard"
require_contains "$START_PROMPT" "/home/hr-hm/Project/work/docs/next-codex-prompt.txt" "start prompt must delegate to next-codex-prompt.txt as the single source of truth"

require_contains "$NEXT_PROMPT" "./scripts/check-work-skills.sh" "next prompt must mention skill availability check"
require_contains "$NEXT_PROMPT" "./scripts/check-coconala-bootstrap.sh" "next prompt must mention bootstrap guard"
require_contains "$NEXT_PROMPT" "./scripts/os-check.sh" "next prompt must mention internal os check"
require_contains "$NEXT_PROMPT" "/home/hr-hm/Project/work/docs/code-comment-style.ja.md" "next prompt must require code-comment-style.ja.md"
require_contains "$NEXT_PROMPT" "coconala-prequote-ops-ja" "next prompt must require the prequote skill"
require_contains "$NEXT_PROMPT" "delivery-pack-ja" "next prompt must require the delivery skill"
require_contains "$NEXT_PROMPT" "japanese-chat-natural-ja" "next prompt must require the final naturalization skill"
require_contains "$NEXT_PROMPT" "/home/hr-hm/Project/work/os/coconala/platform-contract.yaml" "next prompt must mention the coconala platform contract"
require_contains "$NEXT_PROMPT" "/home/hr-hm/Project/work/runtime/replies/latest.txt" "next prompt must require saving sendable replies to runtime"

require_contains "$AGENTS_FILE" "docs/code-comment-style.ja.md" "AGENTS.md must keep the default comment-style rule"
require_contains "$AGENTS_FILE" "/home/hr-hm/Project/work/runtime/replies/latest.txt" "AGENTS.md must keep the reply persistence rule"

require_contains "$README_FILE" "docs/code-comment-style.ja.md" "README must point to the comment-style rule"
require_contains "$README_FILE" "00_結論と確認方法.md" "README must describe the delivery pack around 00_結論と確認方法.md"
require_not_contains "$README_FILE" "納品物3点セット + 正式納品文の作成" "README delivery-pack description must match the current standard"

require_contains "$DELIVERY_SKILL_FILE" "00_結論と確認方法.md" "delivery-pack skill must require 00_結論と確認方法.md"
require_contains "$DELIVERY_SKILL_FILE" "00_結論と要点.md" "delivery-pack skill must require handoff summary output"
require_contains "$DELIVERY_SKILL_FILE" "01_[対象フロー名]_引き継ぎメモ.md" "delivery-pack skill must require handoff memo output"
require_contains "$DELIVERY_SKILL_FILE" "/home/hr-hm/Project/work/docs/handoff-delivery-template.ja.md" "delivery-pack skill must reference the handoff delivery template"
require_contains "$DELIVERY_SKILL_FILE" "Scope Snapshot" "delivery-pack skill must retain the internal scope snapshot guard"
require_contains "$DELIVERY_SKILL_FILE" "正式納品メッセージ" "delivery-pack skill must retain the formal delivery message output"

if [[ $errors -eq 0 ]]; then
  echo "[OK] coconala bootstrap guard passed"
else
  exit 1
fi
