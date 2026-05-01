#!/usr/bin/env python3
"""Smoke check contract packet fixtures against #R writer brief routing.

This is not a full runtime packet builder. It verifies that the v1 packet
fixtures still land on the expected #R writer-brief lane/scenario and keep the
minimum service/phase/buyer-message contract before natural-language writing.
"""

from __future__ import annotations

import argparse
import subprocess
import sys
import tempfile
from pathlib import Path
from typing import Any

try:
    import yaml
except ImportError as exc:
    raise SystemExit(f"PyYAML is required: {exc}") from exc


DEFAULT_FIXTURE_PATH = Path("ops/tests/contract-packets/bugfix-15000-v1-fixtures.yaml")
DEFAULT_PACKET_PATH = Path("ops/tests/contract-packets/bugfix-15000-v1-samples.yaml")
RENDERER = Path("scripts/render-coconala-reply.py")

ROUTE_BY_PHASE = {
    "prequote": "message",
    "quote_sent": "estimate",
    "purchased": "message",
    "delivered": "message",
    "closed": "message",
}

ACCEPTABLE_SCENARIOS_BY_FAMILY = {
    "prequote_service_fit": {"default_bugfix"},
    "quote_sent_payment_after_share": {"after_payment_zip_share_timing"},
    "purchased_current_status": {"progress_anxiety"},
    "purchased_commitment_followup": {"progress_anxiety", "progress_summary_request"},
    "purchased_deadline_followup": {"progress_anxiety"},
    "purchased_requested_materials_received": {"requested_materials_received"},
    "purchased_redacted_resend_received": {"redacted_resend_received"},
    "delivered_light_supplement": {"doc_explanation_request"},
    "closed_relation_check": {"closed_materials_check"},
}


def load_yaml(path: Path) -> Any:
    with path.open("r", encoding="utf-8") as f:
        return yaml.safe_load(f)


def as_list(value: Any) -> list[Any]:
    return value if isinstance(value, list) else []


def extract_yaml_block(text: str) -> dict[str, Any]:
    marker = "```yaml"
    start = text.find(marker)
    if start < 0:
        raise ValueError("writer brief did not contain a yaml block")
    start += len(marker)
    end = text.find("```", start)
    if end < 0:
        raise ValueError("writer brief yaml block was not closed")
    data = yaml.safe_load(text[start:end])
    if not isinstance(data, dict):
        raise ValueError("writer brief yaml block did not parse as mapping")
    return data


def make_quality_fixture(fixture: dict[str, Any]) -> dict[str, Any]:
    return {
        "version": 1,
        "cases": [
            {
                "id": fixture.get("fixture_id"),
                "stock_id": fixture.get("fixture_id"),
                "category": "contract_packet_sync",
                "route": ROUTE_BY_PHASE.get(str(fixture.get("phase")), "message"),
                "state": fixture.get("phase"),
                "scenario": fixture.get("family"),
                "question_type": fixture.get("family"),
                "primary_question": fixture.get("primary_question"),
                "raw_message": fixture.get("raw_message"),
                "note": "contract packet writer brief sync smoke",
            }
        ],
    }


def render_writer_brief(fixture: dict[str, Any]) -> dict[str, Any]:
    with tempfile.NamedTemporaryFile("w", suffix=".yaml", encoding="utf-8", delete=False) as f:
        yaml.safe_dump(make_quality_fixture(fixture), f, allow_unicode=True, sort_keys=False)
        temp_path = Path(f.name)

    try:
        proc = subprocess.run(
            [
                sys.executable,
                str(RENDERER),
                "--fixture",
                str(temp_path),
                "--case-id",
                str(fixture.get("fixture_id")),
                "--writer-brief",
            ],
            text=True,
            capture_output=True,
            check=False,
        )
    finally:
        temp_path.unlink(missing_ok=True)

    if proc.returncode != 0:
        raise RuntimeError(proc.stderr.strip() or proc.stdout.strip() or f"renderer exited {proc.returncode}")
    return extract_yaml_block(proc.stdout)


def answer_count(brief: dict[str, Any]) -> int:
    return len(as_list(((brief.get("reply_contract") or {}).get("answer_map"))))


def validate_sync(
    fixture: dict[str, Any],
    *,
    packet: dict[str, Any],
    errors: list[str],
    warnings: list[str],
) -> None:
    fixture_id = str(fixture.get("fixture_id"))
    family = str(fixture.get("family"))
    phase = fixture.get("phase")
    try:
        brief = render_writer_brief(fixture)
    except Exception as exc:  # noqa: BLE001 - CLI smoke should report all fixture failures.
        errors.append(f"{fixture_id}: cannot render writer brief: {exc}")
        return

    if brief.get("state") != phase:
        errors.append(f"{fixture_id}: writer brief state mismatch: {brief.get('state')!r} != {phase!r}")
    if brief.get("lane") != phase:
        errors.append(f"{fixture_id}: writer brief lane mismatch: {brief.get('lane')!r} != {phase!r}")
    if brief.get("buyer_message") != fixture.get("raw_message"):
        errors.append(f"{fixture_id}: writer brief buyer_message differs from fixture raw_message")

    service = brief.get("service") or {}
    if service.get("service_id") != "bugfix-15000":
        errors.append(f"{fixture_id}: writer brief service_id mismatch: {service.get('service_id')!r}")
    if service.get("public_service") is not True:
        errors.append(f"{fixture_id}: writer brief public_service is not true")
    if str(service.get("fee_text")) != "15,000円":
        errors.append(f"{fixture_id}: writer brief fee_text mismatch: {service.get('fee_text')!r}")

    acceptable_scenarios = ACCEPTABLE_SCENARIOS_BY_FAMILY.get(family)
    if acceptable_scenarios and brief.get("scenario") not in acceptable_scenarios:
        errors.append(
            f"{fixture_id}: writer brief scenario {brief.get('scenario')!r} does not match packet family {family!r}; "
            f"expected one of {sorted(acceptable_scenarios)}"
        )

    packet_answers = as_list((packet.get("reply_contract") or {}).get("answer_map"))
    if answer_count(brief) < len(packet_answers):
        errors.append(
            f"{fixture_id}: writer brief answer_map has fewer answers than packet "
            f"({answer_count(brief)} < {len(packet_answers)})"
        )

    if not as_list((brief.get("reply_contract") or {}).get("required_moves")):
        errors.append(f"{fixture_id}: writer brief required_moves is empty")

    decision = brief.get("response_decision_plan")
    if not isinstance(decision, dict) or not decision:
        warnings.append(f"{fixture_id}: writer brief response_decision_plan is empty")
    else:
        if not decision.get("direct_answer_line"):
            warnings.append(f"{fixture_id}: writer brief response_decision_plan.direct_answer_line is empty")
        if not decision.get("response_order"):
            warnings.append(f"{fixture_id}: writer brief response_decision_plan.response_order is empty")


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--fixtures", default=str(DEFAULT_FIXTURE_PATH))
    parser.add_argument("--packets", default=str(DEFAULT_PACKET_PATH))
    args = parser.parse_args()

    fixtures_doc = load_yaml(Path(args.fixtures)) or {}
    packet_doc = load_yaml(Path(args.packets)) or {}
    packets_by_id = {
        str(packet.get("packet_id")): packet
        for packet in as_list(packet_doc.get("packets"))
        if packet.get("packet_id")
    }

    errors: list[str] = []
    warnings: list[str] = []
    checked = 0
    for fixture in as_list(fixtures_doc.get("fixtures")):
        packet_id = str(fixture.get("expected_packet_id"))
        packet = packets_by_id.get(packet_id)
        if not packet:
            errors.append(f"{fixture.get('fixture_id')}: expected packet not found: {packet_id}")
            continue
        checked += 1
        validate_sync(fixture, packet=packet, errors=errors, warnings=warnings)

    if errors:
        print("FAIL contract packet writer brief sync")
        for error in errors:
            print(f"- {error}")
        if warnings:
            print("\n[warnings]")
            for warning in warnings:
                print(f"- {warning}")
        return 1

    for warning in warnings:
        print(f"WARN {warning}")
    print(f"OK contract packet writer brief sync: {checked} fixture(s), {len(warnings)} warning(s)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
