#!/usr/bin/env python3
"""Build minimal contract packets from trace fixtures and optionally compare them."""

from __future__ import annotations

import argparse
from datetime import datetime
from pathlib import Path
from typing import Any
from zoneinfo import ZoneInfo

try:
    import yaml
except ImportError as exc:
    raise SystemExit(f"PyYAML is required: {exc}") from exc


DEFAULT_FIXTURE_PATH = Path("ops/tests/contract-packets/bugfix-15000-v1-fixtures.yaml")
DEFAULT_PACKET_PATH = Path("ops/tests/contract-packets/bugfix-15000-v1-samples.yaml")
DEFAULT_REPORT_DIR = Path("runtime/regression/coconala-reply/contract-packets")
SERVICE_REGISTRY = Path("os/core/service-registry.yaml")
PHASE_SCHEMA = Path("ops/common/phase-contract-schema.yaml")
JST = ZoneInfo("Asia/Tokyo")

CHANNEL_BY_PHASE = {
    "prequote": "coconala_message",
    "quote_sent": "coconala_message",
    "purchased": "coconala_talkroom",
    "delivered": "coconala_talkroom",
    "closed": "coconala_message",
}
STATE_EVIDENCE_SOURCE_BY_PHASE = {
    "prequote": "buyer_latest_message",
    "quote_sent": "prior_thread_summary",
    "purchased": "platform_state",
    "delivered": "platform_state",
    "closed": "platform_state",
}


def load_yaml(path: Path) -> Any:
    with path.open("r", encoding="utf-8") as f:
        return yaml.safe_load(f)


def as_list(value: Any) -> list[Any]:
    return value if isinstance(value, list) else []


def load_services() -> list[dict[str, Any]]:
    registry = load_yaml(SERVICE_REGISTRY) or {}
    return as_list(registry.get("services"))


def public_service_ids() -> list[str]:
    return [str(item.get("service_id")) for item in load_services() if item.get("public") is True]


def hidden_service_ids() -> list[str]:
    return [str(item.get("service_id")) for item in load_services() if item.get("public") is False]


def service_truth_version(service_id: str, updated: str) -> str:
    return f"{service_id}-public-facts-{updated}"


def redaction_policy_for_phase(phase: str) -> str:
    if phase == "purchased":
        return "ignore_and_request_redacted_resend_if_needed"
    return "do_not_request"


def answer_brief_for_question(*, family: str, question_id: str) -> str:
    answers_by_family = {
        "prequote_service_fit": {
            "q1": "原因不明の状態でも、Stripe決済後に注文が作られない不具合として15,000円で依頼できる。ただし成功保証はしない。",
        },
        "prequote_multi_symptom_price_scope": {
            "q1": "優先症状である決済後に注文が作られない不具合を1件として、15,000円で依頼できる。もう1つの症状は同じ原因につながっていればあわせて確認でき、別原因なら先に相談する。",
        },
        "quote_sent_payment_after_share": {
            "q1": "支払い前に送らなくてよい。",
            "q2": "お支払い完了後にトークルームでまとめて共有する流れでよい。",
        },
        "purchased_current_status": {
            "q1": "受領済み材料をもとに、不具合に関係する流れを確認している。",
            "q2": "原因はまだ断定していない。追加で必要なものが出た場合だけ伝える。",
        },
        "purchased_commitment_followup": {
            "q1": "前に伝えていた見通し共有として、受領済み材料をもとに現時点で見えている範囲と次に見る箇所を短く返す。原因はまだ断定しない。",
            "q2": "いま追加で必要なものはない。必要になった場合だけこちらから絞って伝える。",
        },
        "purchased_deadline_followup": {
            "q1": "約束していた返答時刻を過ぎていることを踏まえ、現時点の状況を返す。ただし修正完了時刻は断定しない。",
            "q2": "現時点で見えている範囲と、次に見る箇所を短く返す。原因はまだ断定しない。",
            "q3": "いま追加で必要なものはない。必要になった場合だけこちらから伝える。",
        },
        "purchased_requested_materials_received": {
            "q1": "追加で依頼していたログとスクショは受領済みとして扱う。",
            "q2": "いま追加で必要なものはない。受領済み材料をもとに確認を進め、必要になった場合だけこちらから絞って伝える。",
            "q3": "次は受領済み材料をもとに、不具合に関係する流れを確認する。原因はまだ断定しない。",
        },
        "purchased_redacted_resend_received": {
            "q1": "伏せ直したZIPは受領済みとして扱い、その内容をもとに確認を進められる。",
            "q2": "前のZIPの秘密値は確認対象にせず、送り直し分をもとに確認する。",
        },
        "delivered_light_supplement": {
            "q1": "反映する修正ファイルだけ短く整理して返す。",
            "q2": "画面スクショは必要になった場合だけこちらから依頼する。",
        },
        "closed_relation_check": {
            "q1": "このメッセージ上で送られた範囲をもとに、前回修正との関係確認まではできる。実作業は別途相談する。",
        },
    }
    family_answers = answers_by_family.get(family) or {}
    return family_answers.get(question_id, "主質問に対して、この phase で答えられる範囲を短く返す。")


def build_answer_map(explicit_questions: list[dict[str, Any]], *, family: str) -> list[dict[str, Any]]:
    return [
        {
            "question_id": item.get("id"),
            "disposition": "answer_now",
            "answer_brief": answer_brief_for_question(family=family, question_id=str(item.get("id"))),
        }
        for item in explicit_questions
    ]


def build_ask_map(*, family: str, primary_question_id: str) -> list[dict[str, Any]]:
    if family != "closed_relation_check":
        return []
    return [
        {
            "id": "ask1",
            "question_ids": [primary_question_id],
            "ask_text": "今出ているエラー内容やログ、画面の状況をこのメッセージ上で送ってもらう",
            "why_needed": "前回修正との関係確認に必要なため",
            "evidence_kind": "safe_material_summary",
        }
    ]


def blocking_missing_facts_for_family(family: str) -> list[str]:
    if family == "closed_relation_check":
        return ["今回のエラー内容やログは未受領"]
    return []


def direct_answer_line_for_family(family: str) -> str:
    lines = {
        "prequote_service_fit": "原因が分からない状態でも、15,000円の不具合修正としてご依頼いただけます。",
        "prequote_multi_symptom_price_scope": "この場合は、「決済後に注文が作られない」不具合を1件として、15,000円でご依頼いただけます。",
        "quote_sent_payment_after_share": "スクショやログは、お支払い完了後にトークルームでまとめて共有してください。",
        "purchased_current_status": "今は、いただいたログとスクショをもとに、今回の不具合に関係する流れを確認しています。",
        "purchased_commitment_followup": "前にお伝えしていた見通し共有として、今はいただいたログとスクショをもとに、現時点で見えている範囲と次に見る箇所を整理しています。",
        "purchased_deadline_followup": "お待たせしています。前にお伝えしていた状況共有として、現時点で見えている範囲と次に見る箇所を整理してお返しします。",
        "purchased_requested_materials_received": "追加でお願いしていたログとスクショは受け取りました。まずはいただいた内容をもとに確認を進めます。",
        "purchased_redacted_resend_received": "伏せ直していただいたZIPを受け取りました。前のZIPの秘密値は確認対象にせず、送り直し分をもとに確認します。",
        "delivered_light_supplement": "反映する修正ファイルだけ、こちらで短く整理します。",
        "closed_relation_check": "このメッセージ上では、届いた内容をもとに前回修正との関係を確認するところまで対応します。",
    }
    return lines.get(family, "この phase で答えられる範囲を短く返します。")


def issue_plan_for_family(family: str) -> list[dict[str, str]]:
    plans = {
        "prequote_service_fit": [
            {
                "issue": "依頼可否と価格",
                "disposition": "answer_now",
                "reason": "service scope に合う bugfix 相談。購入前診断は不要。",
            }
        ],
        "prequote_multi_symptom_price_scope": [
            {
                "issue": "優先症状1件としての価格・範囲",
                "disposition": "answer_now",
                "reason": "buyer は一番困っている症状と価格範囲を明示している。",
            },
            {
                "issue": "2つ目の症状の扱い",
                "disposition": "answer_now",
                "reason": "同じ原因か別原因か未確定の不安を短く回収する。",
            },
        ],
        "quote_sent_payment_after_share": [
            {
                "issue": "材料共有のタイミング",
                "disposition": "answer_now",
                "reason": "quote_sent では購入後共有の通常フローを先に案内する。",
            }
        ],
        "purchased_current_status": [
            {
                "issue": "購入後の現在地説明",
                "disposition": "answer_now",
                "reason": "received_materials にある範囲だけで説明する。",
            }
        ],
        "purchased_commitment_followup": [
            {
                "issue": "既存コミットメント付きの購入後進捗共有",
                "disposition": "answer_now",
                "reason": "known_commitments と received_materials を踏まえ、見通し共有を浮かせず返す。",
            }
        ],
        "purchased_deadline_followup": [
            {
                "issue": "約束済み返答時刻を過ぎた後の購入後進捗共有",
                "disposition": "answer_now",
                "reason": "known_commitments の時刻を無視せず、過剰な完了保証や新しい時刻追加は避ける。",
            }
        ],
        "purchased_requested_materials_received": [
            {
                "issue": "依頼済み追加材料の受領確認と次の確認",
                "disposition": "answer_now",
                "reason": "seller が依頼した材料が届いた状態として扱い、同じ材料を再要求しない。",
            }
        ],
        "purchased_redacted_resend_received": [
            {
                "issue": "秘密値を伏せた送り直しZIPの受領と確認対象",
                "disposition": "answer_now",
                "reason": "secret 値を扱わず、redacted resend を正として確認する。",
            }
        ],
        "delivered_light_supplement": [
            {
                "issue": "納品後の軽い補足",
                "disposition": "answer_now",
                "reason": "delivered の承諾前補足として扱える。",
            }
        ],
        "closed_relation_check": [
            {
                "issue": "closed 後の関係確認",
                "disposition": "answer_now",
                "reason": "関係確認だけならメッセージ上で受ける。実作業は別相談。",
            }
        ],
    }
    return plans.get(
        family,
        [
            {
                "issue": "主質問への回答",
                "disposition": "answer_now",
                "reason": "この phase で答えられる範囲を固定する。",
            }
        ],
    )


def required_moves_for_family(family: str) -> list[str]:
    moves = {
        "prequote_service_fit": ["answer_directly_now", "give_purchase_path"],
        "prequote_multi_symptom_price_scope": ["answer_directly_now", "explain_scope_boundary", "give_purchase_path"],
        "quote_sent_payment_after_share": ["answer_directly_now", "give_purchase_path"],
        "purchased_current_status": ["answer_directly_now", "confirm_receipt"],
        "purchased_commitment_followup": ["answer_directly_now", "confirm_receipt"],
        "purchased_deadline_followup": ["react_briefly_first", "answer_directly_now"],
        "purchased_requested_materials_received": ["answer_directly_now", "confirm_receipt"],
        "purchased_redacted_resend_received": ["answer_directly_now", "confirm_receipt"],
        "delivered_light_supplement": ["answer_directly_now"],
        "closed_relation_check": ["answer_directly_now", "request_minimum_evidence", "explain_scope_boundary"],
    }
    return list(moves.get(family, ["answer_directly_now"]))


def forbidden_moves_for_family(family: str) -> list[str]:
    moves = {
        "prequote_service_fit": [
            "internal_term_exposure",
            "vague_hold_without_reason",
            "frontload_branching_risk_when_not_asked",
        ],
        "prequote_multi_symptom_price_scope": [
            "internal_term_exposure",
            "vague_hold_without_reason",
            "overexplain_branching",
        ],
        "quote_sent_payment_after_share": [
            "internal_term_exposure",
            "overexplain_branching",
            "frontload_scope_explanation_when_not_asked",
        ],
        "purchased_current_status": [
            "internal_term_exposure",
            "vague_hold_without_reason",
            "ask_client_to_prioritize_when_burden_owner_us",
        ],
        "purchased_commitment_followup": [
            "internal_term_exposure",
            "vague_hold_without_reason",
            "ask_client_to_prioritize_when_burden_owner_us",
        ],
        "purchased_deadline_followup": [
            "internal_term_exposure",
            "vague_hold_without_reason",
            "ask_client_to_prioritize_when_burden_owner_us",
        ],
        "purchased_requested_materials_received": [
            "internal_term_exposure",
            "vague_hold_without_reason",
            "ask_client_to_prioritize_when_burden_owner_us",
        ],
        "purchased_redacted_resend_received": [
            "internal_term_exposure",
            "vague_hold_without_reason",
            "ask_client_to_prioritize_when_burden_owner_us",
        ],
        "delivered_light_supplement": [
            "internal_term_exposure",
            "overexplain_branching",
            "frontload_scope_explanation_when_not_asked",
        ],
        "closed_relation_check": [
            "internal_term_exposure",
            "vague_hold_without_reason",
            "overexplain_branching",
        ],
    }
    return list(moves.get(family, ["internal_term_exposure"]))


def primary_concern_for_family(family: str) -> str:
    concerns = {
        "prequote_service_fit": "依頼可否と価格",
        "prequote_multi_symptom_price_scope": "優先症状1件として15,000円で依頼できるか",
        "quote_sent_payment_after_share": "材料共有のタイミング",
        "purchased_current_status": "現在地の短い共有",
        "purchased_commitment_followup": "既存コミットメントを踏まえた現在地共有",
        "purchased_deadline_followup": "約束済み返答時刻を過ぎた後の現在地共有",
        "purchased_requested_materials_received": "依頼済み追加材料の受領確認と次の確認",
        "purchased_redacted_resend_received": "秘密値を伏せた送り直しZIPの受領と確認対象",
        "delivered_light_supplement": "反映箇所の短い補足",
        "closed_relation_check": "closed 後の関係確認可否",
    }
    return concerns.get(family, "主質問への回答")


def facts_known_for_family(family: str) -> list[str]:
    facts = {
        "prequote_service_fit": [
            "Stripe決済後に注文が作られない",
            "原因は未特定",
        ],
        "prequote_multi_symptom_price_scope": [
            "症状は2つある",
            "buyer は決済後に注文が作られない症状を一番困っていると明示している",
            "同じ原因か別原因かは未確認",
        ],
        "quote_sent_payment_after_share": [
            "見積り提案済み",
            "buyer はまだ支払い前",
        ],
        "purchased_current_status": [
            "ログとスクショは受領済み",
            "原因未断定",
        ],
        "purchased_commitment_followup": [
            "ログとスクショは受領済み",
            "次の見通しを返すコミットメントが active",
            "原因未断定",
        ],
        "purchased_deadline_followup": [
            "本日18:00までに状況を返すコミットメントが active",
            "buyer は18:00を過ぎていると伝えている",
            "原因未断定",
        ],
        "purchased_requested_materials_received": [
            "seller は追加でログとスクショを依頼済み",
            "buyer は追加のログとスクショを送付済み",
            "原因未断定",
        ],
        "purchased_redacted_resend_received": [
            "seller は秘密値を伏せた形で送り直すよう依頼済み",
            "buyer は APIキーと .env の値を伏せたZIPを送り直した",
            "buyer は前のZIPを見ないでほしいと伝えている",
            "原因未断定",
        ],
        "delivered_light_supplement": [
            "修正ファイルは納品済み",
            "buyer は承諾前",
        ],
        "closed_relation_check": [
            "前回トークルームは closed",
            "似た Stripe エラーが出ている",
        ],
    }
    return list(facts.get(family, []))


def response_order_for_family(family: str) -> list[str]:
    orders = {
        "prequote_service_fit": [
            "direct_answer",
            "no_success_guarantee",
            "after_purchase_flow",
            "purchase_path",
        ],
        "prequote_multi_symptom_price_scope": [
            "direct_answer_to_price_scope",
            "secondary_symptom_boundary",
            "no_success_guarantee",
            "purchase_path",
        ],
        "quote_sent_payment_after_share": [
            "normal_flow_first",
            "after_payment_material_share",
            "purchase_path",
        ],
        "purchased_current_status": [
            "receipt_and_current_status",
            "not_yet_concluded",
            "next_update_or_extra_material_policy",
        ],
        "purchased_commitment_followup": [
            "acknowledge_existing_commitment",
            "receipt_and_current_status",
            "not_yet_concluded",
            "extra_material_policy",
        ],
        "purchased_deadline_followup": [
            "acknowledge_missed_or_due_commitment",
            "current_status",
            "not_yet_concluded",
            "extra_material_policy",
        ],
        "purchased_requested_materials_received": [
            "confirm_requested_materials_received",
            "next_check_focus_without_overclaiming",
            "extra_material_policy",
        ],
        "purchased_redacted_resend_received": [
            "confirm_redacted_resend_received",
            "confirm_previous_secret_zip_excluded",
            "next_check_focus_without_overclaiming",
            "extra_material_policy",
        ],
        "delivered_light_supplement": [
            "direct_supplement_commitment",
            "screenshot_policy",
            "send_supplement",
        ],
        "closed_relation_check": [
            "receive_goodwill_briefly",
            "relation_check_boundary",
            "ask_safe_material_summary",
            "work_if_needed_consultation",
        ],
    }
    return list(orders.get(family, ["direct_answer"]))


def reply_contract_extra_for_family(family: str) -> dict[str, Any]:
    if family != "prequote_multi_symptom_price_scope":
        return {}
    return {
        "final_question_id": "q1",
        "issues": [
            {
                "id": "i1",
                "text": "決済後に注文が作られない",
                "buyer_priority": "primary",
            },
            {
                "id": "i2",
                "text": "一部ユーザーだけ有料プランに切り替わらない",
                "buyer_priority": "secondary",
            },
        ],
        "implicit_concerns": [
            {
                "id": "c1",
                "text": "2つの症状が同じ原因なら同じ範囲で見られるか、別原因ならどうなるか",
                "target_issue_ids": ["i1", "i2"],
            }
        ],
        "primary_decision_need": {
            "type": "can_order_priority_issue_as_one_bug_for_15000",
            "target_issue_ids": ["i1"],
            "price": 15000,
            "unit": "one_bug_or_same_cause",
        },
        "primary_selection_evidence": [
            "buyer_says_primary_issue",
            "final_action_question",
            "price_scope_asked",
        ],
    }


def response_decision_extra_for_family(family: str) -> dict[str, Any]:
    if family != "prequote_multi_symptom_price_scope":
        return {}
    return {
        "direct_answer_intent": "優先症状である注文作成不具合を1件として15,000円で依頼できる。",
        "suggested_answer_line": "この場合は、「決済後に注文が作られない」不具合を1件として、15,000円でご依頼いただけます。",
        "preserve_policy": "intent_not_exact_wording",
        "answer_focus": {
            "primary_decision_need": "2つ症状がある状態で、優先症状の注文作成不具合を1件として15,000円で依頼できるか",
            "target_issue_ids": ["i1"],
            "answer_frame": "対象症状 + 1件扱い + 15,000円可否 + 2つ目の症状の同一原因条件",
            "selection_evidence": [
                "buyer_says_primary_issue",
                "final_action_question",
                "price_scope_asked",
            ],
            "non_primary_but_covered": [
                "有料プランに切り替わらない件は、同じ原因につながっていればあわせて確認できる"
            ],
        },
    }


def build_packet(
    fixture: dict[str, Any],
    *,
    root_service_id: str,
    updated: str,
    phase_schema: dict[str, Any],
    visible_services: list[str],
) -> dict[str, Any]:
    phase = str(fixture.get("phase"))
    family = str(fixture.get("family"))
    phase_def = (phase_schema.get("phases") or {}).get(phase) or {}
    explicit_questions = [
        {
            "id": item.get("id"),
            "text": item.get("text"),
            "priority": "primary" if item.get("id") == fixture.get("primary_question_id") else "secondary",
        }
        for item in as_list(fixture.get("explicit_questions"))
    ]
    primary_question_id = str(fixture.get("primary_question_id"))
    ask_map = build_ask_map(family=family, primary_question_id=primary_question_id)
    return {
        "packet_id": fixture.get("expected_packet_id"),
        "generated_from_fixture_id": fixture.get("fixture_id"),
        "phase": phase,
        "family": family,
        "channel": CHANNEL_BY_PHASE.get(phase, fixture.get("channel")),
        "packet_source": "generated",
        "source_type": fixture.get("source_type"),
        "service_truth_version": service_truth_version(root_service_id, updated),
        "transaction_state_evidence": {
            "state": phase,
            "source": STATE_EVIDENCE_SOURCE_BY_PHASE.get(phase, "fixture"),
            "confidence": "high",
        },
        "sendability": fixture.get("sendability"),
        "redaction_policy": {
            "raw_secret_values": redaction_policy_for_phase(phase),
        },
        "memory_packet": {
            "platform": "coconala",
            "service_id": root_service_id,
            "phase": phase,
            "visible_public_services": list(visible_services),
            "buyer_latest_message": fixture.get("raw_message"),
        },
        "phase_contract": {
            "allowed": as_list(phase_def.get("allowed")),
            "forbidden": as_list(phase_def.get("forbidden")),
        },
        "reply_contract": {
            "primary_question_id": fixture.get("primary_question_id"),
            **reply_contract_extra_for_family(family),
            "explicit_questions": explicit_questions,
            "answer_map": build_answer_map(explicit_questions, family=family),
            "ask_map": ask_map,
            "issue_plan": issue_plan_for_family(family),
            "required_moves": required_moves_for_family(family),
            "forbidden_moves": forbidden_moves_for_family(family),
        },
        "response_decision_plan": {
            "primary_concern": primary_concern_for_family(family),
            "facts_known": facts_known_for_family(family),
            "blocking_missing_facts": blocking_missing_facts_for_family(family),
            "direct_answer_line": direct_answer_line_for_family(family),
            **response_decision_extra_for_family(family),
            "response_order": response_order_for_family(family),
        },
    }


def build_packets(fixture_doc: dict[str, Any], phase_schema: dict[str, Any]) -> dict[str, Any]:
    service_id = str(fixture_doc.get("service_id"))
    updated = str(fixture_doc.get("updated"))
    visible_services = [sid for sid in public_service_ids() if sid == service_id]
    return {
        "version": 1,
        "updated": updated,
        "service_id": service_id,
        "packet_source": "generated",
        "source_fixtures": str(DEFAULT_FIXTURE_PATH),
        "packets": [
            build_packet(
                fixture,
                root_service_id=service_id,
                updated=updated,
                phase_schema=phase_schema,
                visible_services=visible_services,
            )
            for fixture in as_list(fixture_doc.get("fixtures"))
        ],
    }


def enrich_generated_doc(
    generated_doc: dict[str, Any],
    *,
    generated_at: datetime,
    fixture_path: Path,
    sample_path: Path,
) -> dict[str, Any]:
    enriched = {
        "version": generated_doc.get("version"),
        "generated_at": generated_at.strftime("%Y-%m-%d %H:%M:%S %Z"),
        "updated": generated_doc.get("updated"),
        "service_id": generated_doc.get("service_id"),
        "packet_source": generated_doc.get("packet_source"),
        "generator": "scripts/build-contract-packets.py",
        "runtime_protocol_stage": "generated_packet_export",
        "source_fixtures": str(fixture_path),
        "sample_reference": str(sample_path),
    }
    for key, value in generated_doc.items():
        if key not in enriched:
            enriched[key] = value
    return enriched


def write_yaml_doc(path: Path, doc: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(yaml.safe_dump(doc, allow_unicode=True, sort_keys=False), encoding="utf-8")


def save_generated_report(doc: dict[str, Any], *, generated_at: datetime) -> tuple[Path, Path]:
    stamp = generated_at.strftime("%Y%m%d-%H%M%S")
    latest_path = DEFAULT_REPORT_DIR / "latest.generated.yaml"
    history_path = DEFAULT_REPORT_DIR / f"{stamp}.generated.yaml"
    write_yaml_doc(latest_path, doc)
    write_yaml_doc(history_path, doc)
    return latest_path, history_path


def question_map(packet: dict[str, Any]) -> dict[str, str]:
    reply_contract = packet.get("reply_contract") or {}
    return {
        str(item.get("id")): str(item.get("text"))
        for item in as_list(reply_contract.get("explicit_questions"))
        if item.get("id")
    }


def compare_to_samples(generated_doc: dict[str, Any], sample_doc: dict[str, Any]) -> list[str]:
    errors: list[str] = []
    hidden_services = set(hidden_service_ids())
    samples_by_id = {
        str(packet.get("packet_id")): packet
        for packet in as_list(sample_doc.get("packets"))
        if packet.get("packet_id")
    }
    for generated in as_list(generated_doc.get("packets")):
        packet_id = str(generated.get("packet_id"))
        sample = samples_by_id.get(packet_id)
        if not sample:
            errors.append(f"{packet_id}: generated packet has no sample counterpart")
            continue
        for field in ("phase", "family", "channel", "source_type", "sendability", "service_truth_version"):
            if generated.get(field) != sample.get(field):
                errors.append(f"{packet_id}: {field} differs: generated={generated.get(field)!r} sample={sample.get(field)!r}")

        generated_memory = generated.get("memory_packet") or {}
        sample_memory = sample.get("memory_packet") or {}
        for field in ("platform", "service_id", "phase", "buyer_latest_message"):
            if generated_memory.get(field) != sample_memory.get(field):
                errors.append(f"{packet_id}: memory_packet.{field} differs")

        visible_services = set(as_list(generated_memory.get("visible_public_services")))
        if hidden_services & visible_services:
            errors.append(f"{packet_id}: generated visible_public_services contains hidden service")
        if visible_services != set(as_list(sample_memory.get("visible_public_services"))):
            errors.append(f"{packet_id}: visible_public_services differs from sample")

        if generated.get("transaction_state_evidence", {}).get("state") != sample.get("transaction_state_evidence", {}).get("state"):
            errors.append(f"{packet_id}: transaction_state_evidence.state differs")
        if generated.get("redaction_policy", {}).get("raw_secret_values") != sample.get("redaction_policy", {}).get("raw_secret_values"):
            errors.append(f"{packet_id}: redaction_policy.raw_secret_values differs")

        generated_questions = question_map(generated)
        sample_questions = question_map(sample)
        if generated_questions != sample_questions:
            errors.append(f"{packet_id}: explicit_questions differ")

        generated_reply_contract = generated.get("reply_contract") or {}
        sample_reply_contract = sample.get("reply_contract") or {}
        if generated_reply_contract.get("primary_question_id") != sample_reply_contract.get("primary_question_id"):
            errors.append(f"{packet_id}: primary_question_id differs")

        sample_answer_ids = {
            item.get("question_id")
            for item in as_list(sample_reply_contract.get("answer_map"))
        }
        sample_answers = {
            item.get("question_id"): item
            for item in as_list(sample_reply_contract.get("answer_map"))
        }
        generated_answers = {
            item.get("question_id"): item
            for item in as_list(generated_reply_contract.get("answer_map"))
        }
        generated_answer_ids = set(generated_answers)
        if not sample_answer_ids.issubset(generated_answer_ids):
            errors.append(f"{packet_id}: generated answer_map does not cover sample answer_map ids")
        for question_id, sample_answer in sample_answers.items():
            generated_answer = generated_answers.get(question_id) or {}
            if generated_answer.get("disposition") != sample_answer.get("disposition"):
                errors.append(f"{packet_id}: answer_map disposition differs for {question_id}")
            if not generated_answer.get("answer_brief"):
                errors.append(f"{packet_id}: generated answer_map missing answer_brief for {question_id}")

        sample_ask_map = as_list(sample_reply_contract.get("ask_map"))
        generated_ask_map = as_list(generated_reply_contract.get("ask_map"))
        if bool(sample_ask_map) != bool(generated_ask_map):
            errors.append(f"{packet_id}: ask_map presence differs")
        if sample_ask_map and generated_ask_map:
            sample_ask = sample_ask_map[0]
            generated_ask = generated_ask_map[0]
            for field in ("question_ids", "why_needed", "evidence_kind"):
                if generated_ask.get(field) != sample_ask.get(field):
                    errors.append(f"{packet_id}: ask_map.{field} differs")

        for field in ("issue_plan", "required_moves", "forbidden_moves"):
            if generated_reply_contract.get(field) != sample_reply_contract.get(field):
                errors.append(f"{packet_id}: reply_contract.{field} differs")

        generated_decision = generated.get("response_decision_plan") or {}
        sample_decision = sample.get("response_decision_plan") or {}
        for field in ("primary_concern", "facts_known", "response_order"):
            if generated_decision.get(field) != sample_decision.get(field):
                errors.append(f"{packet_id}: response_decision_plan.{field} differs")
        if bool(as_list(sample_decision.get("blocking_missing_facts"))) != bool(as_list(generated_decision.get("blocking_missing_facts"))):
            errors.append(f"{packet_id}: response_decision_plan.blocking_missing_facts presence differs")
        if not generated_decision.get("direct_answer_line"):
            errors.append(f"{packet_id}: generated response_decision_plan.direct_answer_line is missing")

        generated_phase = generated.get("phase_contract") or {}
        sample_phase = sample.get("phase_contract") or {}
        for key in ("allowed", "forbidden"):
            generated_values = set(as_list(generated_phase.get(key)))
            sample_values = set(as_list(sample_phase.get(key)))
            missing = sorted(sample_values - generated_values)
            if missing:
                errors.append(f"{packet_id}: generated phase_contract.{key} missing sample values: {', '.join(missing)}")
    return errors


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--fixtures", default=str(DEFAULT_FIXTURE_PATH))
    parser.add_argument("--samples", default=str(DEFAULT_PACKET_PATH))
    parser.add_argument("--check-against-samples", action="store_true")
    parser.add_argument("--write-generated", help="Write generated contract packet YAML to this path.")
    parser.add_argument("--save-report", action="store_true", help="Save latest/history generated packet YAML under runtime/regression.")
    args = parser.parse_args()

    fixture_path = Path(args.fixtures)
    sample_path = Path(args.samples)
    generated_at = datetime.now(JST)
    fixture_doc = load_yaml(fixture_path) or {}
    phase_schema = load_yaml(PHASE_SCHEMA) or {}
    generated_doc = build_packets(fixture_doc, phase_schema)
    generated_doc = enrich_generated_doc(
        generated_doc,
        generated_at=generated_at,
        fixture_path=fixture_path,
        sample_path=sample_path,
    )

    if args.check_against_samples:
        sample_doc = load_yaml(sample_path) or {}
        errors = compare_to_samples(generated_doc, sample_doc)
        if errors:
            print("FAIL generated contract packet comparison")
            for error in errors:
                print(f"- {error}")
            return 1
        print(f"OK generated contract packet comparison: {len(as_list(generated_doc.get('packets')))} packet(s)")
    if args.write_generated:
        write_path = Path(args.write_generated)
        write_yaml_doc(write_path, generated_doc)
        print(f"generated_packet_file: {write_path}")
    if args.save_report:
        latest_path, history_path = save_generated_report(generated_doc, generated_at=generated_at)
        print(f"generated_packet_latest: {latest_path}")
        print(f"generated_packet_history: {history_path}")
    if args.check_against_samples:
        return 0

    print(yaml.safe_dump(generated_doc, allow_unicode=True, sort_keys=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
