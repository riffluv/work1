#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
TARGET_FILE="${1:-$ROOT_DIR/ops/tests/prequote-contract-v2-top5.yaml}"

python3 - "$TARGET_FILE" <<'PY'
import sys
from pathlib import Path

import yaml


target = Path(sys.argv[1])
if not target.is_file():
    print(f"[NG] fixture not found: {target}")
    sys.exit(1)

with target.open("r", encoding="utf-8") as f:
    data = yaml.safe_load(f)

cases = data.get("cases") or []
errors = []

timing_map = {
    "answer_now": "now",
    "answer_after_check": "after_check",
}

for case in cases:
    case_id = case.get("id", "<unknown>")
    reply_stance = case.get("reply_stance") or {}
    reply_contract = case.get("reply_contract") or {}
    explicit_questions = reply_contract.get("explicit_questions") or []
    answer_map = reply_contract.get("answer_map") or []
    ask_map = reply_contract.get("ask_map") or []
    issue_plan = reply_contract.get("issue_plan") or []

    if not explicit_questions:
        errors.append(f"{case_id}: explicit_questions is empty")
        continue
    if not answer_map:
        errors.append(f"{case_id}: answer_map is empty")
        continue

    question_ids = [q.get("id") for q in explicit_questions]
    if len(question_ids) != len(set(question_ids)):
        errors.append(f"{case_id}: explicit_questions ids must be unique")

    primary_question_id = reply_contract.get("primary_question_id")
    if not primary_question_id:
        errors.append(f"{case_id}: primary_question_id missing")
    elif primary_question_id not in question_ids:
        errors.append(f"{case_id}: primary_question_id {primary_question_id} not found in explicit_questions")

    answer_question_ids = [item.get("question_id") for item in answer_map]
    if len(answer_question_ids) != len(set(answer_question_ids)):
        errors.append(f"{case_id}: answer_map question_id must be unique")

    primary_answer = None
    for item in answer_map:
        qid = item.get("question_id")
        if qid not in question_ids:
            errors.append(f"{case_id}: answer_map question_id {qid} not declared in explicit_questions")
        disposition = item.get("disposition")
        if disposition == "answer_after_check":
            if not item.get("hold_reason"):
                errors.append(f"{case_id}: answer_after_check for {qid} missing hold_reason")
            if not item.get("revisit_trigger"):
                errors.append(f"{case_id}: answer_after_check for {qid} missing revisit_trigger")
        if qid == primary_question_id:
            primary_answer = item

    if primary_question_id and not primary_answer:
        errors.append(f"{case_id}: primary_question_id {primary_question_id} missing from answer_map")

    ask_ids = [item.get("id") for item in ask_map]
    if len(ask_ids) != len(set(ask_ids)):
        errors.append(f"{case_id}: ask_map id must be unique")

    for ask in ask_map:
        linked_ids = ask.get("question_ids") or []
        if not linked_ids:
            errors.append(f"{case_id}: ask_map {ask.get('id')} must link to at least one question_id")
        for qid in linked_ids:
            if qid not in question_ids:
                errors.append(f"{case_id}: ask_map {ask.get('id')} references unknown question_id {qid}")
        if not ask.get("ask_text"):
            errors.append(f"{case_id}: ask_map {ask.get('id')} missing ask_text")
        if not ask.get("why_needed"):
            errors.append(f"{case_id}: ask_map {ask.get('id')} missing why_needed")

    ask_count = case.get("ask_count")
    if ask_count is not None and ask_count != len(ask_map):
        errors.append(f"{case_id}: ask_count={ask_count} does not match ask_map size={len(ask_map)}")

    answer_timing = reply_stance.get("answer_timing")
    if answer_timing and primary_answer:
        expected_timing = timing_map.get(primary_answer.get("disposition"))
        if expected_timing and answer_timing != expected_timing:
            errors.append(
                f"{case_id}: answer_timing={answer_timing} conflicts with primary disposition={primary_answer.get('disposition')}"
            )

    required_moves = set(reply_contract.get("required_moves") or [])
    if "answer_directly_now" in required_moves and primary_answer and primary_answer.get("disposition") != "answer_now":
        errors.append(f"{case_id}: required_moves has answer_directly_now but primary disposition is not answer_now")
    if "defer_with_reason" in required_moves and primary_answer and primary_answer.get("disposition") != "answer_after_check":
        errors.append(f"{case_id}: required_moves has defer_with_reason but primary disposition is not answer_after_check")
    if "request_minimum_evidence" in required_moves and not ask_map:
        errors.append(f"{case_id}: required_moves has request_minimum_evidence but ask_map is empty")

    ask_plan_count = sum(1 for item in issue_plan if item.get("disposition") == "ask_client")
    if ask_map and ask_plan_count == 0:
        errors.append(f"{case_id}: ask_map exists but issue_plan has no ask_client item")

if errors:
    for error in errors:
        print(f"[NG] {error}")
    sys.exit(1)

print(f"[OK] reply_contract v2 fixture lint passed: {target}")
print(f"[OK] cases checked: {len(cases)}")
PY
