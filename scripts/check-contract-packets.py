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


def load_yaml(path: Path) -> Any:
    with path.open("r", encoding="utf-8") as f:
        return yaml.safe_load(f)


def as_list(value: Any) -> list[Any]:
    return value if isinstance(value, list) else []


def add_error(errors: list[str], packet_id: str, message: str) -> None:
    errors.append(f"{packet_id}: {message}")


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
    errors: list[str],
) -> None:
    packet_id = str(packet.get("packet_id", "<missing packet_id>"))
    phase = packet.get("phase")

    if not packet.get("packet_id"):
        add_error(errors, packet_id, "missing packet_id")
    if phase not in memory_phases:
        add_error(errors, packet_id, f"unknown phase: {phase!r}")

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

    answer_ids = {a.get("question_id") for a in as_list(reply_contract.get("answer_map"))}
    unknown_answer_ids = sorted(x for x in answer_ids - explicit_ids if x)
    if unknown_answer_ids:
        add_error(errors, packet_id, f"answer_map references unknown question ids: {', '.join(unknown_answer_ids)}")

    for ask in as_list(reply_contract.get("ask_map")):
        ask_ids = set(as_list(ask.get("question_ids")))
        unknown_ask_ids = sorted(x for x in ask_ids - explicit_ids if x)
        if unknown_ask_ids:
            add_error(errors, packet_id, f"ask_map references unknown question ids: {', '.join(unknown_ask_ids)}")

    decision = packet.get("response_decision_plan") or {}
    if not decision.get("direct_answer_line"):
        add_error(errors, packet_id, "response_decision_plan.direct_answer_line is required")
    if not decision.get("response_order"):
        add_error(errors, packet_id, "response_decision_plan.response_order is required")


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("path", nargs="?", default=str(DEFAULT_PATH))
    args = parser.parse_args()

    path = Path(args.path)
    data = load_yaml(path)
    memory_schema = load_yaml(MEMORY_SCHEMA)
    phase_schema = load_yaml(PHASE_SCHEMA)

    memory_fields = memory_schema.get("fields") or {}
    memory_required = set(as_list(memory_schema.get("required_fields")))
    memory_platforms = set(as_list(memory_fields.get("platform", {}).get("allowed")))
    memory_phases = set(as_list(memory_fields.get("phase", {}).get("allowed")))
    commitment_statuses = set(as_list(memory_fields.get("known_commitments", {}).get("status_allowed")))
    pending_actors = set(as_list(memory_fields.get("pending_actions", {}).get("actor_allowed")))
    hidden_services = set(as_list((data.get("global_public_context") or {}).get("hidden_services")))

    errors: list[str] = []
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
            errors=errors,
        )

    if errors:
        for error in errors:
            print(f"FAIL {error}", file=sys.stderr)
        return 1

    print(f"OK {len(packets)} contract packet(s): {path}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
