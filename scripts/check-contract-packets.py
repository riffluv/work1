#!/usr/bin/env python3
"""Validate reply contract packet sample files."""

from __future__ import annotations

import argparse
import sys
from pathlib import Path
from typing import Any

try:
    import yaml
except ImportError as exc:
    raise SystemExit(f"PyYAML is required: {exc}") from exc


DEFAULT_PATH = Path("ops/tests/contract-packets/bugfix-15000-v1-samples.yaml")
MEMORY_SCHEMA = Path("ops/common/reply-memory-schema.yaml")
PHASE_SCHEMA = Path("ops/common/phase-contract-schema.yaml")
OUTPUT_SCHEMA = Path("ops/common/output-schema.yaml")
CHANNELS = {"coconala_message", "coconala_talkroom", "quote_room", "email_future"}
PACKET_SOURCES = {"sample", "generated", "human_adjusted", "regression"}
SOURCE_TYPES = {"synthetic_rehearsal", "real_stock", "regression", "live_case"}
SENDABILITY = {"draft_candidate", "send_ready", "human_review_required"}
REDACTION_POLICIES = {"do_not_request", "ignore_and_request_redacted_resend_if_needed"}


def load_yaml(path: Path) -> Any:
    with path.open("r", encoding="utf-8") as f:
        return yaml.safe_load(f)


def as_list(value: Any) -> list[Any]:
    return value if isinstance(value, list) else []


def add_error(errors: list[str], packet_id: str, message: str) -> None:
    errors.append(f"{packet_id}: {message}")


def add_warning(warnings: list[str], packet_id: str, message: str) -> None:
    warnings.append(f"{packet_id}: {message}")


def collect_strings(value: Any) -> list[str]:
    if isinstance(value, str):
        return [value]
    if isinstance(value, list):
        result: list[str] = []
        for item in value:
            result.extend(collect_strings(item))
        return result
    if isinstance(value, dict):
        result = []
        for item in value.values():
            result.extend(collect_strings(item))
        return result
    return []


def scan_external_text_for_hidden_terms(
    *,
    packet_id: str,
    field_name: str,
    value: Any,
    forbidden_terms: set[str],
    errors: list[str],
) -> None:
    for text in collect_strings(value):
        for term in forbidden_terms:
            if term and term in text:
                add_error(errors, packet_id, f"{field_name} contains hidden/private term: {term}")


def warn_exact_phrase_pressure(
    *,
    packet_id: str,
    writer_notes: dict[str, Any],
    warnings: list[str],
) -> None:
    for phrase in as_list(writer_notes.get("use")):
        if not isinstance(phrase, str):
            continue
        if len(phrase) >= 14 and any(mark in phrase for mark in ("。", "、", "ます", "ません")):
            add_warning(
                warnings,
                packet_id,
                "writer_notes.use may be an exact phrase pressure; keep it as an anchor, not a template",
            )
            return


def validate_packet(
    packet: dict[str, Any],
    *,
    memory_required: set[str],
    memory_platforms: set[str],
    memory_phases: set[str],
    commitment_statuses: set[str],
    pending_actors: set[str],
    phase_schema: dict[str, Any],
    hidden_services: set[str],
    forbidden_public_terms: set[str],
    output_schema: dict[str, Any],
    errors: list[str],
    warnings: list[str],
) -> None:
    packet_id = str(packet.get("packet_id", "<missing packet_id>"))
    phase = packet.get("phase")

    if not packet.get("packet_id"):
        add_error(errors, packet_id, "missing packet_id")
    if phase not in memory_phases:
        add_error(errors, packet_id, f"unknown phase: {phase!r}")
    if packet.get("channel") not in CHANNELS:
        add_error(errors, packet_id, f"unknown channel: {packet.get('channel')!r}")
    if packet.get("packet_source") not in PACKET_SOURCES:
        add_error(errors, packet_id, f"unknown packet_source: {packet.get('packet_source')!r}")
    if packet.get("source_type") not in SOURCE_TYPES:
        add_error(errors, packet_id, f"unknown source_type: {packet.get('source_type')!r}")
    if packet.get("sendability") not in SENDABILITY:
        add_error(errors, packet_id, f"unknown sendability: {packet.get('sendability')!r}")
    if not packet.get("service_truth_version"):
        add_error(errors, packet_id, "service_truth_version is required")
    transaction_state_evidence = packet.get("transaction_state_evidence") or {}
    if transaction_state_evidence.get("state") != phase:
        add_error(errors, packet_id, "transaction_state_evidence.state must match packet.phase")
    redaction_policy = packet.get("redaction_policy") or {}
    if redaction_policy.get("raw_secret_values") not in REDACTION_POLICIES:
        add_error(errors, packet_id, f"unknown redaction_policy.raw_secret_values: {redaction_policy.get('raw_secret_values')!r}")

    memory = packet.get("memory_packet") or {}
    missing_memory = sorted(memory_required - set(memory))
    if missing_memory:
        add_error(errors, packet_id, f"memory_packet missing fields: {', '.join(missing_memory)}")
    if memory.get("phase") != phase:
        add_error(errors, packet_id, "packet.phase and memory_packet.phase differ")
    if memory.get("platform") not in memory_platforms:
        add_error(errors, packet_id, f"unknown platform: {memory.get('platform')!r}")
    if hidden_services & set(as_list(memory.get("visible_public_services"))):
        add_error(errors, packet_id, "hidden service appears in visible_public_services")

    for item in as_list(memory.get("known_commitments")):
        if item.get("status") not in commitment_statuses:
            add_error(errors, packet_id, f"unknown known_commitments.status: {item.get('status')!r}")
    for item in as_list(memory.get("pending_actions")):
        if item.get("actor") not in pending_actors:
            add_error(errors, packet_id, f"unknown pending_actions.actor: {item.get('actor')!r}")

    phase_contract = packet.get("phase_contract") or {}
    phase_def = (phase_schema.get("phases") or {}).get(phase) or {}
    for key in ("allowed", "forbidden"):
        allowed_values = set(as_list(phase_def.get(key)))
        actual_values = set(as_list(phase_contract.get(key)))
        unknown = sorted(actual_values - allowed_values)
        if unknown:
            add_error(errors, packet_id, f"phase_contract.{key} has unknown values: {', '.join(unknown)}")

    reply_contract = packet.get("reply_contract") or {}
    explicit_ids = {q.get("id") for q in as_list(reply_contract.get("explicit_questions"))}
    primary_id = reply_contract.get("primary_question_id")
    if primary_id not in explicit_ids:
        add_error(errors, packet_id, "primary_question_id is not in explicit_questions")
    final_id = reply_contract.get("final_question_id")
    if final_id and final_id not in explicit_ids:
        add_error(errors, packet_id, "final_question_id is not in explicit_questions")
    if final_id and final_id != primary_id and not as_list(reply_contract.get("primary_selection_evidence")):
        add_error(errors, packet_id, "final_question_id differs from primary_question_id but primary_selection_evidence is empty")

    answer_ids = {a.get("question_id") for a in as_list(reply_contract.get("answer_map"))}
    unknown_answer_ids = sorted(x for x in answer_ids - explicit_ids if x)
    if unknown_answer_ids:
        add_error(errors, packet_id, f"answer_map references unknown question ids: {', '.join(unknown_answer_ids)}")

    answer_or_ask_ids = set(answer_ids)

    for ask in as_list(reply_contract.get("ask_map")):
        ask_ids = set(as_list(ask.get("question_ids")))
        answer_or_ask_ids |= ask_ids
        unknown_ask_ids = sorted(x for x in ask_ids - explicit_ids if x)
        if unknown_ask_ids:
            add_error(errors, packet_id, f"ask_map references unknown question ids: {', '.join(unknown_ask_ids)}")

    uncovered_ids = sorted(x for x in explicit_ids - answer_or_ask_ids if x)
    if uncovered_ids:
        add_error(errors, packet_id, f"explicit_questions not covered by answer_map or ask_map: {', '.join(uncovered_ids)}")

    for answer in as_list(reply_contract.get("answer_map")):
        if answer.get("disposition") == "answer_after_check":
            if not answer.get("hold_reason"):
                add_error(errors, packet_id, f"answer_after_check missing hold_reason for {answer.get('question_id')}")
            if not answer.get("revisit_trigger"):
                add_error(errors, packet_id, f"answer_after_check missing revisit_trigger for {answer.get('question_id')}")

    decision = packet.get("response_decision_plan") or {}
    if not decision.get("direct_answer_line"):
        add_error(errors, packet_id, "response_decision_plan.direct_answer_line is required")
    if not decision.get("response_order"):
        add_error(errors, packet_id, "response_decision_plan.response_order is required")
    if as_list(reply_contract.get("ask_map")) and not as_list(decision.get("blocking_missing_facts")):
        add_error(errors, packet_id, "ask_map exists but response_decision_plan.blocking_missing_facts is empty")
    answer_focus = decision.get("answer_focus") or {}
    if answer_focus:
        if not answer_focus.get("primary_decision_need"):
            add_error(errors, packet_id, "response_decision_plan.answer_focus.primary_decision_need is required when answer_focus exists")
        if not answer_focus.get("answer_frame"):
            add_error(errors, packet_id, "response_decision_plan.answer_focus.answer_frame is required when answer_focus exists")
        if not as_list(answer_focus.get("selection_evidence")):
            add_error(errors, packet_id, "response_decision_plan.answer_focus.selection_evidence is required when answer_focus exists")
        issue_ids = {issue.get("id") for issue in as_list(reply_contract.get("issues")) if isinstance(issue, dict)}
        unknown_focus_issues = sorted(
            issue_id
            for issue_id in as_list(answer_focus.get("target_issue_ids"))
            if issue_id and issue_ids and issue_id not in issue_ids
        )
        if unknown_focus_issues:
            add_error(errors, packet_id, f"answer_focus.target_issue_ids references unknown issue ids: {', '.join(unknown_focus_issues)}")
    if decision.get("suggested_answer_line"):
        if not decision.get("direct_answer_intent"):
            add_error(errors, packet_id, "suggested_answer_line requires direct_answer_intent")
        if decision.get("preserve_policy") != "intent_not_exact_wording":
            add_error(errors, packet_id, "suggested_answer_line requires preserve_policy=intent_not_exact_wording")

    reply_schema = (output_schema.get("nested_field_rules") or {}).get("reply_contract") or {}
    required_moves_allowed = set(as_list((reply_schema.get("required_moves") or {}).get("allowed")))
    forbidden_moves_allowed = set(as_list((reply_schema.get("forbidden_moves") or {}).get("allowed")))
    unknown_required_moves = sorted(set(as_list(reply_contract.get("required_moves"))) - required_moves_allowed)
    unknown_forbidden_moves = sorted(set(as_list(reply_contract.get("forbidden_moves"))) - forbidden_moves_allowed)
    if unknown_required_moves:
        add_error(errors, packet_id, f"reply_contract.required_moves has unknown values: {', '.join(unknown_required_moves)}")
    if unknown_forbidden_moves:
        add_error(errors, packet_id, f"reply_contract.forbidden_moves has unknown values: {', '.join(unknown_forbidden_moves)}")

    external_text_fields = {
        "response_decision_plan": decision,
        "reply_contract.answer_map": [
            {"answer_brief": item.get("answer_brief")}
            for item in as_list(reply_contract.get("answer_map"))
        ],
        "reply_contract.ask_map": [
            {"ask_text": item.get("ask_text")}
            for item in as_list(reply_contract.get("ask_map"))
        ],
    }
    for field_name, value in external_text_fields.items():
        scan_external_text_for_hidden_terms(
            packet_id=packet_id,
            field_name=field_name,
            value=value,
            forbidden_terms=forbidden_public_terms,
            errors=errors,
        )

    warn_exact_phrase_pressure(
        packet_id=packet_id,
        writer_notes=packet.get("writer_notes") or {},
        warnings=warnings,
    )


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("path", nargs="?", default=str(DEFAULT_PATH))
    args = parser.parse_args()

    path = Path(args.path)
    data = load_yaml(path)
    memory_schema = load_yaml(MEMORY_SCHEMA)
    phase_schema = load_yaml(PHASE_SCHEMA)
    output_schema = load_yaml(OUTPUT_SCHEMA)

    memory_fields = memory_schema.get("fields") or {}
    memory_required = set(as_list(memory_schema.get("required_fields")))
    memory_platforms = set(as_list(memory_fields.get("platform", {}).get("allowed")))
    memory_phases = set(as_list(memory_fields.get("phase", {}).get("allowed")))
    commitment_statuses = set(as_list(memory_fields.get("known_commitments", {}).get("status_allowed")))
    pending_actors = set(as_list(memory_fields.get("pending_actions", {}).get("actor_allowed")))
    global_public_context = data.get("global_public_context") or {}
    hidden_services = set(as_list(global_public_context.get("hidden_services")))
    forbidden_public_terms = hidden_services | set(as_list((global_public_context.get("live_service_constraints") or {}).get("forbidden_public_mentions")))

    source_schemas = data.get("source_schemas") or {}

    errors: list[str] = []
    warnings: list[str] = []
    for key, value in source_schemas.items():
        if isinstance(value, str) and value.startswith("/"):
            add_warning(warnings, "<source_schemas>", f"{key} uses an absolute path; keep app portability in mind")

    seen_ids: set[str] = set()
    packets = as_list(data.get("packets"))
    for packet in packets:
        packet_id = packet.get("packet_id")
        if packet_id in seen_ids:
            errors.append(f"{packet_id}: duplicate packet_id")
        seen_ids.add(packet_id)
        validate_packet(
            packet,
            memory_required=memory_required,
            memory_platforms=memory_platforms,
            memory_phases=memory_phases,
            commitment_statuses=commitment_statuses,
            pending_actors=pending_actors,
            phase_schema=phase_schema,
            hidden_services=hidden_services,
            forbidden_public_terms=forbidden_public_terms,
            output_schema=output_schema,
            errors=errors,
            warnings=warnings,
        )

    for warning in warnings:
        print(f"WARN {warning}", file=sys.stderr)

    if errors:
        for error in errors:
            print(f"FAIL {error}", file=sys.stderr)
        return 1

    print(f"OK {len(packets)} contract packet(s): {path} ({len(warnings)} warning(s))")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
