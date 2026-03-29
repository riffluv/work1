#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
MODE_FILE="$ROOT_DIR/runtime/mode.txt"
ACTIVE_CASE_FILE="$ROOT_DIR/runtime/active-case.txt"
REPLY_FILE="$ROOT_DIR/runtime/replies/latest.txt"
CASE_LOG="$ROOT_DIR/ops/case-log.csv"

backup_dir="$(mktemp -d)"
created_case_id=""
created_open_dir=""
created_closed_dir=""

restore_file() {
  local src="$1"
  local dest="$2"
  if [[ -f "$src" ]]; then
    cp "$src" "$dest"
  else
    rm -f "$dest"
  fi
}

cleanup() {
  restore_file "$backup_dir/mode.txt" "$MODE_FILE"
  restore_file "$backup_dir/active-case.txt" "$ACTIVE_CASE_FILE"
  restore_file "$backup_dir/latest.txt" "$REPLY_FILE"
  restore_file "$backup_dir/case-log.csv" "$CASE_LOG"

  if [[ -n "$created_open_dir" && -d "$created_open_dir" ]]; then
    rm -rf "$created_open_dir"
  fi

  if [[ -n "$created_closed_dir" && -d "$created_closed_dir" ]]; then
    rm -rf "$created_closed_dir"
  fi

  rm -rf "$backup_dir"
}

trap cleanup EXIT

mkdir -p "$backup_dir"
cp -f "$MODE_FILE" "$backup_dir/mode.txt" 2>/dev/null || true
cp -f "$ACTIVE_CASE_FILE" "$backup_dir/active-case.txt" 2>/dev/null || true
cp -f "$REPLY_FILE" "$backup_dir/latest.txt" 2>/dev/null || true
cp -f "$CASE_LOG" "$backup_dir/case-log.csv" 2>/dev/null || true

open_output="$("$ROOT_DIR/scripts/case-open.sh" \
  --service-id bugfix-15000 \
  --route talkroom \
  --client-summary "internal os smoke test" \
  --current-decision "implementation start" \
  --next-action "confirm implementation mode" \
  --implementation-focus "mode separation")"

created_case_id="$(printf '%s\n' "$open_output" | sed -n 's/^case_id=//p')"
created_open_dir="$(printf '%s\n' "$open_output" | sed -n 's/^dir=//p')"
open_readme="$(printf '%s\n' "$open_output" | sed -n 's/^readme=//p')"

if [[ -z "$created_case_id" || ! -f "$open_readme" ]]; then
  echo "[NG] case-open smoke failed"
  exit 1
fi

grep -Fq -- "- service_id: bugfix-15000" "$open_readme" || { echo "[NG] service_id missing in open README"; exit 1; }
grep -Fq -- "- phase: implementation" "$open_readme" || { echo "[NG] implementation phase missing after case-open"; exit 1; }
grep -Fxq "implementation" "$MODE_FILE" || { echo "[NG] mode pointer did not switch to implementation"; exit 1; }
grep -Fxq "$created_case_id" "$ACTIVE_CASE_FILE" || { echo "[NG] active case pointer not updated"; exit 1; }

note_output="$("$ROOT_DIR/scripts/case-note.sh" \
  --case-id "$created_case_id" \
  --decision "same_cause" \
  --reason "smoke note" \
  --scope "base_plan" \
  --price "15000" \
  --next-action "switch to delivery")"

grep -Fq -- "- decision: same_cause" "$open_readme" || { echo "[NG] case-note did not append snapshot"; exit 1; }

phase_output="$("$ROOT_DIR/scripts/case-phase.sh" \
  --case-id "$created_case_id" \
  --phase delivery \
  --delivery-status preparing \
  --current-decision "delivery prep" \
  --next-action "package outputs")"

grep -Fq -- "- phase: delivery" "$open_readme" || { echo "[NG] case-phase did not update README phase"; exit 1; }
grep -Fq -- "- delivery_status: preparing" "$open_readme" || { echo "[NG] case-phase did not update delivery status"; exit 1; }
grep -Fxq "delivery" "$MODE_FILE" || { echo "[NG] mode pointer did not switch to delivery"; exit 1; }

reply_output="$("$ROOT_DIR/scripts/reply-save.sh" --text "internal os smoke reply")"
grep -Fxq "internal os smoke reply" "$REPLY_FILE" || { echo "[NG] reply-save did not update runtime reply"; exit 1; }

close_output="$("$ROOT_DIR/scripts/case-close.sh" \
  --case-id "$created_case_id" \
  --final-phase delivered \
  --amount 15000 \
  --outcome fixed \
  --scope-status same_cause \
  --additional-handling none \
  --review-risk low \
  --reuse-hint "flow smoke" \
  --notes "internal os smoke")"

created_closed_dir="$ROOT_DIR/ops/cases/closed/$created_case_id"
closed_readme="$created_closed_dir/README.md"

if [[ ! -f "$closed_readme" ]]; then
  echo "[NG] case-close did not create closed README"
  exit 1
fi

grep -Fq -- "- final_phase: delivered" "$closed_readme" || { echo "[NG] closed README missing final phase"; exit 1; }
grep -Fq -- "internal os smoke" "$CASE_LOG" || { echo "[NG] case-log missing smoke row"; exit 1; }
grep -Fxq "coconala" "$MODE_FILE" || { echo "[NG] mode pointer did not reset to coconala"; exit 1; }
if [[ -s "$ACTIVE_CASE_FILE" ]]; then
  echo "[NG] active case pointer not cleared after close"
  exit 1
fi

echo "[OK] internal os flow smoke passed"
