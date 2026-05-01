#!/usr/bin/env python3
"""Check contract packet samples are traceable to fixture-like inputs."""

from __future__ import annotations

import argparse
from pathlib import Path
from typing import Any

try:
    import yaml
except ImportError as exc:
    raise SystemExit(f"PyYAML is required: {exc}") from exc


DEFAULT_FIXTURE_PATH = Path("ops/tests/contract-packets/bugfix-15000-v1-fixtures.yaml")
DEFAULT_PACKET_PATH = Path("ops/tests/contract-packets/bugfix-15000-v1-samples.yaml")


def load_yaml(path: Path) -> Any:
    with path.open("r", encoding="utf-8") as f:
        return yaml.safe_load(f)


def as_list(value: Any) -> list[Any]:
    return value if isinstance(value, list) else []


def add_error(errors: list[str], fixture_id: str, message: str) -> None:
    errors.append(f"{fixture_id}: {message}")


def question_map(packet: dict[str, Any]) -> dict[str, str]:
    reply_contract = packet.get("reply_contract") or {}
    return {
        str(item.get("id")): str(item.get("text"))
        for item in as_list(reply_contract.get("explicit_questions"))
        if item.get("id")
    }


def validate_fixture(
    fixture: dict[str, Any],
    *,
    packets_by_id: dict[str, dict[str, Any]],
    root_service_id: str,
    errors: list[str],
) -> None:
    fixture_id = str(fixture.get("fixture_id") or "<missing fixture_id>")
    packet_id = fixture.get("expected_packet_id")
    packet = packets_by_id.get(packet_id)
    if not packet:
        add_error(errors, fixture_id, f"expected_packet_id not found: {packet_id!r}")
        return

    for field in ("phase", "family", "channel", "source_type", "sendability"):
        if fixture.get(field) != packet.get(field):
            add_error(
                errors,
                fixture_id,
                f"{field} differs from packet {packet_id}: fixture={fixture.get(field)!r} packet={packet.get(field)!r}",
            )

    memory = packet.get("memory_packet") or {}
    if memory.get("service_id") != root_service_id:
        add_error(errors, fixture_id, f"memory_packet.service_id differs from root service_id: {memory.get('service_id')!r}")
    if memory.get("phase") != fixture.get("phase"):
        add_error(errors, fixture_id, "memory_packet.phase differs from fixture.phase")
    if memory.get("buyer_latest_message") != fixture.get("raw_message"):
        add_error(errors, fixture_id, "raw_message differs from memory_packet.buyer_latest_message")

    reply_contract = packet.get("reply_contract") or {}
    if reply_contract.get("primary_question_id") != fixture.get("primary_question_id"):
        add_error(errors, fixture_id, "primary_question_id differs from packet")

    packet_questions = question_map(packet)
    expected_questions = {
        str(item.get("id")): str(item.get("text"))
        for item in as_list(fixture.get("explicit_questions"))
        if item.get("id")
    }
    if packet_questions != expected_questions:
        add_error(errors, fixture_id, "explicit_questions differ from packet")

    primary_text = packet_questions.get(str(fixture.get("primary_question_id")))
    if primary_text != fixture.get("primary_question"):
        add_error(errors, fixture_id, "primary_question text differs from packet explicit question")

    visible_services = set(as_list(memory.get("visible_public_services")))
    for service_id in as_list(fixture.get("expected_visible_public_services")):
        if service_id not in visible_services:
            add_error(errors, fixture_id, f"expected visible service missing from memory_packet: {service_id}")
    for service_id in as_list(fixture.get("expected_hidden_services_not_visible")):
        if service_id in visible_services:
            add_error(errors, fixture_id, f"hidden service appears in memory_packet.visible_public_services: {service_id}")


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--fixtures", default=str(DEFAULT_FIXTURE_PATH))
    parser.add_argument("--packets", default=str(DEFAULT_PACKET_PATH))
    args = parser.parse_args()

    fixture_path = Path(args.fixtures)
    packet_path = Path(args.packets)
    fixture_doc = load_yaml(fixture_path) or {}
    packet_doc = load_yaml(packet_path) or {}

    root_service_id = fixture_doc.get("service_id")
    packet_service_id = packet_doc.get("service_id")
    errors: list[str] = []
    if root_service_id != packet_service_id:
        errors.append(f"<root>: fixture service_id differs from packet service_id: {root_service_id!r} != {packet_service_id!r}")

    packets_by_id = {
        str(packet.get("packet_id")): packet
        for packet in as_list(packet_doc.get("packets"))
        if packet.get("packet_id")
    }
    fixture_count = 0
    for fixture in as_list(fixture_doc.get("fixtures")):
        fixture_count += 1
        validate_fixture(
            fixture,
            packets_by_id=packets_by_id,
            root_service_id=str(root_service_id),
            errors=errors,
        )

    if errors:
        print("FAIL contract packet fixture trace")
        for error in errors:
            print(f"- {error}")
        return 1

    print(f"OK contract packet fixture trace: {fixture_count} fixture(s)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
