#!/usr/bin/env python3
from __future__ import annotations

import argparse
import importlib.util
import re
from pathlib import Path

import yaml


ROOT_DIR = Path(__file__).resolve().parents[1]
PREQUOTE_RENDERER = ROOT_DIR / "scripts/render-prequote-estimate-initial.py"
SERVICE_REGISTRY_PATH = ROOT_DIR / "os/core/service-registry.yaml"
PUBLIC_QUOTE_SERVICE_ID = "bugfix-15000"


def load_shared_module():
    spec = importlib.util.spec_from_file_location("render_prequote_estimate_initial", PREQUOTE_RENDERER)
    if spec is None or spec.loader is None:
        raise RuntimeError(f"failed to load shared renderer: {PREQUOTE_RENDERER}")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


shared = load_shared_module()


def load_service_grounding() -> dict:
    with SERVICE_REGISTRY_PATH.open("r", encoding="utf-8") as f:
        registry = yaml.safe_load(f) or {}

    service = next(
        (item for item in registry.get("services") or [] if item.get("service_id") == PUBLIC_QUOTE_SERVICE_ID),
        None,
    )
    if service is None:
        raise RuntimeError(f"missing public quote_sent service grounding: {PUBLIC_QUOTE_SERVICE_ID}")
    if not service.get("public"):
        raise RuntimeError(f"quote_sent service is not public: {PUBLIC_QUOTE_SERVICE_ID}")

    facts_path = Path(service.get("facts_file") or "")
    if not facts_path.is_file():
        raise RuntimeError(f"missing service facts file: {facts_path}")

    with facts_path.open("r", encoding="utf-8") as f:
        facts = yaml.safe_load(f) or {}

    base_price = int(facts.get("base_price") or 15000)
    fee_text = f"{base_price:,}円"
    return {
        "service_id": service.get("service_id"),
        "public_service": bool(service.get("public")),
        "display_name": facts.get("display_name") or "",
        "fee_text": fee_text,
        "base_price": base_price,
        "scope_unit": facts.get("scope_unit") or "",
        "proposal_scope": f"今回は、原因確認と修正判断を含めた{fee_text}の提案です。",
        "same_cause_rule": "同じ原因なら基本料金内、別原因なら追加対応は事前にご相談します。",
        "refund_policy": "返金については、ココナラの規定に沿う形になります。",
        "reissue_support": "期限が切れた場合も、必要なら同内容で再提案できます。",
        "payment_platform_rule": "購入画面に表示されている方法の中で進めていただく形になります。",
        "dashboard_scope_rule": "Webhook受信口に関係する範囲であれば、Stripeダッシュボード側の設定も確認対象です。",
        "self_apply_support_rule": "本番への反映自体は依頼者様でお願いします。確認手順はお渡しします。",
        "same_cause_followup_rule": "トークルームが開いている間に同じ原因の範囲で詰まる点があれば、その範囲は基本料金内で確認します。",
        "no_secret_share_rule": "evt_... やログ、設定画面の見える範囲で確認できます。",
        "text_only_support_rule": "スクショや短い箇条書きで送っていただければ大丈夫です。",
    }


SERVICE_GROUNDING = load_service_grounding()


def build_temperature_plan_for_case(source: dict, scenario: str) -> dict:
    if scenario in {
        "proposal_change",
        "purchase_timing",
        "reissue_quote",
        "risk_refund_question",
        "payment_method",
        "dashboard_scope_question",
        "extra_fee_fear",
        "self_apply_support",
        "secret_share_reassurance",
        "no_meeting_request",
        "generic_quote_sent",
    }:
        return shared.build_temperature_plan(source, case_type="boundary")
    return shared.build_temperature_plan(source, case_type="bugfix")


def opener_for(source: dict) -> str:
    return "ご連絡ありがとうございます。"


def extract_facts_known(raw: str, scenario: str) -> list[str]:
    facts: list[str] = []
    if "提案" in raw or "見積もり" in raw:
        facts.append("proposal_context_present")
    if "15000" in raw or "15,000" in raw:
        facts.append("price_acknowledged")
    if "返金" in raw:
        facts.append("refund_question_present")
    if "直らなかった場合" in raw or "修正がいらなかった場合" in raw:
        facts.append("result_risk_question_present")
    if "決済エラー" in raw:
        facts.append("payment_error_present")
    if "メール通知" in raw or ("通知" in raw and "メール" in raw):
        facts.append("email_notification_issue_present")
    if "来週" in raw:
        facts.append("purchase_next_week_requested")
    if "期限切れ" in raw:
        facts.append("quote_expired_present")
    if "了解" in raw:
        facts.append("quote_acknowledged")
    if "バタバタ" in raw:
        facts.append("busy_schedule_present")
    if "コンビニ" in raw or "支払い方法" in raw:
        facts.append("payment_method_question_present")
    if "コンビニ" in raw:
        facts.append("convenience_store_payment_requested")
    if "ダッシュボード" in raw:
        facts.append("dashboard_setting_question_present")
    if "別原因" in raw and ("怖い" in raw or "金額が増える" in raw):
        facts.append("extra_fee_fear_present")
    if "キャンセル" in raw:
        facts.append("cancel_option_question_present")
    if "自分で反映" in raw or "納品された修正コード" in raw:
        facts.append("self_apply_support_question_present")
    if "evt_" in raw:
        facts.append("event_id_present")
    if "本番のURL" in raw or "見せなくても本当に大丈夫" in raw:
        facts.append("secret_share_anxiety_present")
    if "Zoom" in raw or "口頭で説明" in raw or "画面を見せながら" in raw:
        facts.append("no_meeting_request_present")
    if scenario == "proposal_change":
        facts.append("change_request_present")
    return facts


def build_primary_concern(source: dict, scenario: str, facts_known: list[str]) -> str:
    raw = source.get("raw_message", "")

    if scenario == "proposal_change":
        if "payment_error_present" in facts_known and "email_notification_issue_present" in facts_known:
            return "決済エラーに加えてメール通知も同じ提案内で見られるか確認したい"
        return "追加したい内容が同じ提案の範囲に収まるか確認したい"
    if scenario == "purchase_timing":
        if "busy_schedule_present" in facts_known:
            return "来週まで購入を待っても提案期限に問題がないか知りたい"
        return "購入を少し先にしても問題ないか知りたい"
    if scenario == "reissue_quote":
        return "期限切れの提案を同じ内容で出し直せるか知りたい"
    if scenario == "risk_refund_question":
        if "refund_question_present" in facts_known:
            return "直らなかった場合の料金と返金の扱いを先に確認したい"
        return "直らなかった場合でも15,000円がかかるのか確認したい"
    if scenario == "payment_method":
        if "convenience_store_payment_requested" in facts_known:
            return "コンビニ払いのような別の支払い方法が選べるか知りたい"
        return "購入画面で選べる支払い方法を確認したい"
    if scenario == "dashboard_scope_question":
        return "Webhook受信口の調査にStripeダッシュボード設定も含まれるか確認したい"
    if scenario == "extra_fee_fear":
        return "別原因が見つかった時に料金が増えるのか、そこで止められるのか不安"
    if scenario == "self_apply_support":
        return "納品後に自分で反映した場合のサポート範囲を確認したい"
    if scenario == "secret_share_reassurance":
        return "本番URLや秘密情報を出さずに調査できるか確認したい"
    if scenario == "no_meeting_request":
        return "Zoomなしでも進められる代替手段を確認したい"
    if raw:
        return shared.summarize_raw_message(raw)
    return "提案後の進め方を確認したい"


def build_hard_constraints(scenario: str, grounding: dict) -> dict:
    return {
        "service_id": grounding.get("service_id"),
        "public_service_only": bool(grounding.get("public_service")),
        "answer_before_procedure": True,
        "ask_only_if_blocking": True,
        "no_refund_promise": scenario == "risk_refund_question",
        "no_platform_override": scenario == "payment_method",
        "same_cause_scope_rule": grounding.get("scope_unit") == "same_cause_and_same_flow_and_same_endpoint",
    }


def detect_scenario(source: dict) -> str:
    raw = source.get("raw_message", "")
    note = source.get("note", "")
    combined = f"{raw}\n{note}"

    if "期限切れ" in combined or "再提案" in combined:
        return "reissue_quote"
    if "来週購入してもいい" in combined or "期限が切れたりしませんか" in combined:
        return "purchase_timing"
    if "Zoom" in combined or "口頭で説明" in combined or "画面を見せながら" in combined:
        return "no_meeting_request"
    if "evt_" in combined or "本番のURL" in combined or "見せなくても本当に大丈夫" in combined:
        return "secret_share_reassurance"
    if "納品された修正コード" in combined or "自分で反映" in combined:
        return "self_apply_support"
    if "別原因" in combined and ("金額が増える" in combined or "キャンセル" in combined or "怖くて" in combined):
        return "extra_fee_fear"
    if "Webhook受信口" in combined and ("ダッシュボード" in combined or "設定も見てもらえる" in combined):
        return "dashboard_scope_question"
    if "支払い方法" in combined or "コンビニ払い" in combined:
        return "payment_method"
    if "返金してもらえる" in combined or "直らなかった場合" in combined or "修正がいらなかった場合" in combined:
        return "risk_refund_question"
    if "内容を変更" in combined or "同じ提案で対応可能" in combined or "内容を少し変えたい" in combined:
        return "proposal_change"
    return "generic_quote_sent"


def build_response_decision_plan(source: dict, scenario: str, contract: dict) -> dict:
    raw = source.get("raw_message", "")
    facts_known = extract_facts_known(raw, scenario)
    primary = next(item for item in contract["answer_map"] if item["question_id"] == contract["primary_question_id"])
    blocking_missing_facts: list[str] = []
    direct_answer_line = primary["answer_brief"]
    response_order = ["reaction", "direct_answer"]
    fee_text = SERVICE_GROUNDING["fee_text"]

    if scenario == "proposal_change":
        has_change_points = any(
            fact in facts_known for fact in ["payment_error_present", "email_notification_issue_present"]
        )
        if has_change_points:
            direct_answer_line = "同じ提案で進められるかは、決済エラーとメール通知が同じ原因かどうかを確認してからお返しします。"
            response_order = ["reaction", "direct_answer", "next_action"]
        else:
            blocking_missing_facts = ["change_points"]
            direct_answer_line = "同じ提案で進められるかは、追加したい内容が今回の範囲に収まるかを確認してからお返しします。"
            response_order = ["reaction", "direct_answer", "ask", "next_action"]
    elif scenario == "purchase_timing":
        direct_answer_line = "来週の購入でも大丈夫です。"
        response_order = ["reaction", "direct_answer", "answer_detail"]
    elif scenario == "reissue_quote":
        direct_answer_line = "はい、同じ内容で再提案できます。"
        response_order = ["reaction", "direct_answer"]
    elif scenario == "risk_refund_question":
        direct_answer_line = "調査の結果として修正が不要だった場合でも、作業分として15,000円は発生します。"
        response_order = ["reaction", "direct_answer", "answer_detail", "next_action"]
    elif scenario == "payment_method":
        direct_answer_line = "支払い方法の表示はココナラ側の仕様によるため、こちらで選択肢を増やすことはできません。"
        response_order = ["reaction", "direct_answer", "answer_detail"]
    elif scenario == "dashboard_scope_question":
        direct_answer_line = "はい、Webhook受信口に関係する範囲であれば、Stripeダッシュボード側の設定も確認対象です。"
        response_order = ["reaction", "direct_answer", "answer_detail", "next_action"]
    elif scenario == "extra_fee_fear":
        direct_answer_line = "別原因が見つかっても、自動で料金が増えたり追加対応に進んだりはしません。"
        response_order = ["reaction", "direct_answer", "answer_detail", "next_action"]
    elif scenario == "self_apply_support":
        direct_answer_line = "今回の提案では、本番への反映自体は依頼者様でお願いしていますが、確認手順はお渡しします。"
        response_order = ["reaction", "direct_answer", "answer_detail", "next_action"]
    elif scenario == "secret_share_reassurance":
        direct_answer_line = "はい、本番のURLをそのまま送っていただかなくても進められます。"
        response_order = ["reaction", "direct_answer", "answer_detail", "next_action"]
    elif scenario == "no_meeting_request":
        direct_answer_line = "Zoomや通話での進行はしていません。"
        response_order = ["reaction", "direct_answer", "answer_detail", "next_action"]
    else:
        blocking_missing_facts = ["focus_points"]
        direct_answer_line = "今の提案でそのまま進められるかは、気になっている点を確認してからお返しします。"
        response_order = ["reaction", "direct_answer", "ask", "next_action"]

    return {
        "primary_concern": build_primary_concern(source, scenario, facts_known),
        "facts_known": facts_known,
        "blocking_missing_facts": blocking_missing_facts,
        "direct_answer_line": direct_answer_line,
        "response_order": response_order,
    }


def build_case_from_source(source: dict) -> dict:
    raw = source.get("raw_message", "")
    scenario = detect_scenario(source)
    case = {
        "id": source.get("case_id") or source.get("id"),
        "src": source.get("route", "service"),
        "state": "quote_sent",
        "raw_message": raw,
        "summary": shared.derive_summary(source),
        "scenario": scenario,
        "temperature_plan": build_temperature_plan_for_case(source, scenario),
        "service_grounding": dict(SERVICE_GROUNDING),
        "hard_constraints": build_hard_constraints(scenario, SERVICE_GROUNDING),
        "reply_stance": {
            "burden_owner": "us",
            "empathy_first": False,
            "reply_skeleton": "estimate_followup",
        },
    }

    if scenario == "proposal_change":
        case["reply_contract"] = {
            "primary_question_id": "q1",
            "explicit_questions": [{"id": "q1", "text": "同じ提案で対応可能か", "priority": "primary"}],
            "answer_map": [
                {
                    "question_id": "q1",
                    "disposition": "answer_after_check",
                    "answer_brief": "同じ提案でいけるかは、追加された内容が今回の範囲に収まるかを見てからお返しします。",
                    "hold_reason": "決済エラーとメール通知が同じ原因かどうかを先に切りたいです。",
                    "revisit_trigger": "変更点を受領したあとに、同じ提案で進めるかをお返しします。",
                }
            ],
            "ask_map": [
                {
                    "id": "a1",
                    "question_ids": ["q1"],
                    "ask_text": "変更したい点を1〜2点だけそのまま送ってください。",
                    "why_needed": "同じ提案で収まるかを先に切るため",
                }
            ],
            "required_moves": ["react_briefly_first", "defer_with_reason", "request_minimum_evidence"],
        }
        case["response_decision_plan"] = build_response_decision_plan(source, scenario, case["reply_contract"])
        return case

    if scenario == "purchase_timing":
        case["reply_contract"] = {
            "primary_question_id": "q1",
            "explicit_questions": [{"id": "q1", "text": "来週購入しても大丈夫か", "priority": "primary"}],
            "answer_map": [
                {
                    "question_id": "q1",
                    "disposition": "answer_now",
                    "answer_brief": "来週の購入でも大丈夫です。期限が切れた場合も、必要なら同内容で再提案できます。",
                }
            ],
            "ask_map": [],
            "required_moves": ["react_briefly_first", "answer_directly_now"],
        }
        case["response_decision_plan"] = build_response_decision_plan(source, scenario, case["reply_contract"])
        return case

    if scenario == "reissue_quote":
        case["reply_contract"] = {
            "primary_question_id": "q1",
            "explicit_questions": [{"id": "q1", "text": "同じ内容で再提案できるか", "priority": "primary"}],
            "answer_map": [
                {
                    "question_id": "q1",
                    "disposition": "answer_now",
                    "answer_brief": "はい、同じ内容で再提案できます。",
                }
            ],
            "ask_map": [],
            "required_moves": ["react_briefly_first", "answer_directly_now"],
        }
        case["response_decision_plan"] = build_response_decision_plan(source, scenario, case["reply_contract"])
        return case

    if scenario == "risk_refund_question":
        case["reply_contract"] = {
            "primary_question_id": "q1",
            "explicit_questions": [{"id": "q1", "text": "直らなかった場合でも15000円はかかるか", "priority": "primary"}],
            "answer_map": [
                {
                    "question_id": "q1",
                    "disposition": "answer_now",
                    "answer_brief": "この提案は、原因確認と修正判断を含めた15,000円の提案です。必要な手続きがある場合は、ココナラ上の案内に沿う形になります。",
                }
            ],
            "ask_map": [],
            "required_moves": ["react_briefly_first", "answer_directly_now"],
        }
        case["response_decision_plan"] = build_response_decision_plan(source, scenario, case["reply_contract"])
        return case

    if scenario == "payment_method":
        case["reply_contract"] = {
            "primary_question_id": "q1",
            "explicit_questions": [{"id": "q1", "text": "コンビニ払いができるか", "priority": "primary"}],
            "answer_map": [
                {
                    "question_id": "q1",
                    "disposition": "answer_after_check",
                    "answer_brief": "支払い方法の表示はココナラ側の仕様によるため、こちらで選択肢を増やすことはできません。",
                    "hold_reason": "まず表示されている支払い画面に沿って進めていただく形になります。",
                    "revisit_trigger": "購入画面で進めにくい点があれば、その状況を教えてください。",
                }
            ],
            "ask_map": [],
            "required_moves": ["react_briefly_first", "defer_with_reason"],
        }
        case["response_decision_plan"] = build_response_decision_plan(source, scenario, case["reply_contract"])
        return case

    if scenario == "dashboard_scope_question":
        case["reply_contract"] = {
            "primary_question_id": "q1",
            "explicit_questions": [{"id": "q1", "text": "Webhook受信口の調査にダッシュボード設定も含まれるか", "priority": "primary"}],
            "answer_map": [
                {
                    "question_id": "q1",
                    "disposition": "answer_now",
                    "answer_brief": "Webhook受信口に関係する範囲であれば、Stripeダッシュボード側の設定も確認対象です。",
                }
            ],
            "ask_map": [],
            "required_moves": ["react_briefly_first", "answer_directly_now"],
        }
        case["response_decision_plan"] = build_response_decision_plan(source, scenario, case["reply_contract"])
        return case

    if scenario == "extra_fee_fear":
        case["reply_contract"] = {
            "primary_question_id": "q1",
            "explicit_questions": [{"id": "q1", "text": "別原因が見つかったときに料金が増えるか、そこで止められるか", "priority": "primary"}],
            "answer_map": [
                {
                    "question_id": "q1",
                    "disposition": "answer_now",
                    "answer_brief": "別原因が見つかった時点で状況を共有し、追加対応に進むかどうかは事前にご相談します。",
                }
            ],
            "ask_map": [],
            "required_moves": ["react_briefly_first", "answer_directly_now"],
        }
        case["response_decision_plan"] = build_response_decision_plan(source, scenario, case["reply_contract"])
        return case

    if scenario == "self_apply_support":
        case["reply_contract"] = {
            "primary_question_id": "q1",
            "explicit_questions": [{"id": "q1", "text": "自分で反映した場合のサポート範囲はどこまでか", "priority": "primary"}],
            "answer_map": [
                {
                    "question_id": "q1",
                    "disposition": "answer_now",
                    "answer_brief": "今回の提案では、本番への反映自体は依頼者様でお願いしていますが、確認手順はお渡しします。",
                }
            ],
            "ask_map": [],
            "required_moves": ["react_briefly_first", "answer_directly_now"],
        }
        case["response_decision_plan"] = build_response_decision_plan(source, scenario, case["reply_contract"])
        return case

    if scenario == "secret_share_reassurance":
        case["reply_contract"] = {
            "primary_question_id": "q1",
            "explicit_questions": [{"id": "q1", "text": "本番URLや秘密情報を見せなくても調査できるか", "priority": "primary"}],
            "answer_map": [
                {
                    "question_id": "q1",
                    "disposition": "answer_now",
                    "answer_brief": "本番のURLをそのまま送っていただかなくても進められます。",
                }
            ],
            "ask_map": [],
            "required_moves": ["react_briefly_first", "answer_directly_now"],
        }
        case["response_decision_plan"] = build_response_decision_plan(source, scenario, case["reply_contract"])
        return case

    if scenario == "no_meeting_request":
        case["reply_contract"] = {
            "primary_question_id": "q1",
            "explicit_questions": [{"id": "q1", "text": "進行中にZoomや口頭説明ができるか", "priority": "primary"}],
            "answer_map": [
                {
                    "question_id": "q1",
                    "disposition": "answer_now",
                    "answer_brief": "Zoomや通話での進行はしていません。",
                }
            ],
            "ask_map": [],
            "required_moves": ["react_briefly_first", "answer_directly_now"],
        }
        case["response_decision_plan"] = build_response_decision_plan(source, scenario, case["reply_contract"])
        return case

    case["reply_contract"] = {
        "primary_question_id": "q1",
        "explicit_questions": [{"id": "q1", "text": "今回どう進めるか", "priority": "primary"}],
        "answer_map": [
            {
                "question_id": "q1",
                "disposition": "answer_after_check",
                "answer_brief": "内容を確認して、必要なら提案内容を整え直します。",
                "hold_reason": "まずは変更点や気になっている点を短く確認したいです。",
                "revisit_trigger": "確認後に、次にどう整えるかをお伝えします。",
            }
        ],
        "ask_map": [
            {
                "id": "a1",
                "question_ids": ["q1"],
                "ask_text": "気になっている点を1〜2点だけそのまま送ってください。",
                "why_needed": "次に整える内容を絞るため",
            }
        ],
        "required_moves": ["react_briefly_first", "defer_with_reason", "request_minimum_evidence"],
    }
    case["response_decision_plan"] = build_response_decision_plan(source, scenario, case["reply_contract"])
    return case


def with_period(text: str) -> str:
    return text if text.endswith("。") else f"{text}。"


def draft_opening_anchor(case: dict) -> str:
    scenario = case["scenario"]
    raw = case.get("raw_message", "")
    temperature_plan = case.get("temperature_plan") or {}
    opening_move = temperature_plan.get("opening_move")
    user_signal = temperature_plan.get("user_signal")
    if scenario == "proposal_change":
        if "決済エラー" in raw and "メール通知" in raw:
            return "決済エラーに加えてメール通知の件も確認しました。"
        return "提案後に変更したい点が出てきたとのこと、確認しました。"
    if scenario == "purchase_timing":
        if "バタバタ" in raw:
            return "お忙しいところ確認いただきありがとうございます。"
        return "購入タイミングについてのご相談、確認しました。"
    if scenario == "reissue_quote":
        return "期限切れの表示が出たとのこと、確認しました。"
    if scenario == "risk_refund_question":
        if "了解" in raw:
            return f"{SERVICE_GROUNDING['fee_text']}でのご了解、ありがとうございます。"
        if "不安" in raw:
            return "即決のご不安、ごもっともです。"
        return "料金面のご心配、確認しました。"
    if scenario == "payment_method":
        if "コンビニ" in raw:
            return "購入画面で支払い方法が限られて見える状況、確認しました。"
        return "支払い方法の件、確認しました。"
    if scenario == "dashboard_scope_question":
        return "Webhook受信口に加えて、Stripeダッシュボード設定の範囲も気になっているとのこと、確認しました。"
    if scenario == "extra_fee_fear":
        return "金額が増えるのでは、というご不安はもっともです。"
    if scenario == "self_apply_support":
        return "ご自身で反映する場合のサポート範囲ですね。確認しました。"
    if scenario == "secret_share_reassurance":
        if "evt_" in raw:
            return "evt_... まで確認できているとのこと、ありがとうございます。"
        return "共有範囲についてのご不安、確認しました。"
    if scenario == "no_meeting_request":
        return "文章で伝えるのが大変な点、確認しました。"
    if opening_move == "action_first":
        return "まず気になっている点から確認します。"
    if opening_move == "pressure_release":
        return "気を遣わなくて大丈夫です。まず今の内容からお返しします。"
    if opening_move == "normalize_then_clarify":
        return "いまの段階で迷うのは自然です。まず今の内容からお返しします。"
    if opening_move == "receive_and_own":
        return "率直に伝えていただいてありがとうございます。まず今の内容からお返しします。"
    if opening_move == "yes_no_first":
        if user_signal == "negative_feedback":
            return "率直に伝えていただいてありがとうございます。まず今の内容からお返しします。"
        return "まず今の内容からお返しします。"
    return "提案後のご連絡、確認しました。"


def _normalized(text: str) -> str:
    return re.sub(r"[\s。、，,.！？?「」『』（）()・:：/／\-]+", "", text)


def _same_text(left: str, right: str) -> bool:
    nl = _normalized(left)
    nr = _normalized(right)
    if not nl or not nr:
        return False
    return nl == nr


def _same_meaning(left: str, right: str) -> bool:
    nl = _normalized(left)
    nr = _normalized(right)
    if not nl or not nr:
        return False
    return nl == nr or nl in nr or nr in nl


def _append_unique(paragraphs: list[str], text: str) -> None:
    cleaned = text.strip()
    if not cleaned:
        return
    if any(_same_text(cleaned, existing) for existing in paragraphs):
        return
    paragraphs.append(cleaned)


def draft_body_paragraphs(case: dict) -> list[str]:
    scenario = case["scenario"]
    raw = case.get("raw_message", "")
    decision_plan = case.get("response_decision_plan") or {}
    direct_answer = with_period(decision_plan.get("direct_answer_line") or "")
    blocking_missing_facts = decision_plan.get("blocking_missing_facts") or []
    grounding = case.get("service_grounding") or {}

    if scenario == "proposal_change":
        if blocking_missing_facts:
            return [
                direct_answer,
                "変更したい点を1〜2点だけそのまま送ってください。",
            ]
        return [
            f"{direct_answer}\n{grounding.get('same_cause_rule', '')}".strip(),
            "状況はすでにいただいているので、こちらで範囲を確認します。",
        ]

    if scenario == "purchase_timing":
        return [f"{direct_answer}\n{grounding.get('reissue_support', '')}".strip()]

    if scenario == "reissue_quote":
        return [direct_answer]

    if scenario == "risk_refund_question":
        paragraphs = [
            f"{direct_answer}\n{grounding.get('proposal_scope', '')}".strip(),
            grounding.get("refund_policy", ""),
        ]
        paragraphs.append("この内容で問題なければ、そのままご購入いただいて大丈夫です。")
        return paragraphs

    if scenario == "payment_method":
        return [f"{direct_answer}\n{grounding.get('payment_platform_rule', '')}".strip()]

    if scenario == "dashboard_scope_question":
        return [
            f"{direct_answer}\nStripe 以外の別機能や別原因まで広がる場合だけ、その時点で切り分けて事前にご相談します。".strip(),
            "この前提で問題なければ、そのままご購入いただいて大丈夫です。",
        ]

    if scenario == "extra_fee_fear":
        return [
            f"{direct_answer}\nその場合は状況を共有し、追加対応に進まずそこで止める形も含めて事前にご相談します。".strip(),
            "キャンセルの扱いは、ココナラ上の案内に沿う形になります。",
            "この前提で問題なければ、そのままご購入いただいて大丈夫です。",
        ]

    if scenario == "self_apply_support":
        return [
            f"{direct_answer}\n{grounding.get('same_cause_followup_rule', '')}".strip(),
            "この前提で問題なければ、そのままご購入いただいて大丈夫です。",
        ]

    if scenario == "secret_share_reassurance":
        return [
            f"{direct_answer}\n{grounding.get('no_secret_share_rule', '')}".strip(),
            "この前提で問題なければ、そのままご購入いただいて大丈夫です。",
        ]

    if scenario == "no_meeting_request":
        return [
            f"{direct_answer}\n{grounding.get('text_only_support_rule', '')}".strip(),
            "その形で問題なければ、そのままご購入いただいて大丈夫です。",
        ]

    if blocking_missing_facts:
        return [
            direct_answer,
            "気になっている点を1〜2点だけそのまま送ってください。",
        ]

    return [direct_answer]


def render_case(case: dict) -> str:
    decision_plan = case.get("response_decision_plan") or {}
    first_lines = [opener_for(case)]
    reaction = draft_opening_anchor(case)
    direct_answer = decision_plan.get("direct_answer_line") or ""
    if reaction and not _same_meaning(reaction, direct_answer):
        first_lines.append(reaction)

    paragraphs: list[str] = ["\n".join(line for line in first_lines if line.strip())]
    for paragraph in draft_body_paragraphs(case):
        _append_unique(paragraphs, paragraph)
    return "\n\n".join(section for section in paragraphs if section.strip())


def main() -> int:
    parser = argparse.ArgumentParser(description="Render quote_sent follow-up replies from flat quote_sent cases.")
    parser.add_argument("--fixture", required=True)
    parser.add_argument("--case-id")
    parser.add_argument("--limit", type=int)
    parser.add_argument("--save", action="store_true")
    args = parser.parse_args()

    cases = shared.load_cases(Path(args.fixture))
    selected = [case for case in cases if case.get("state") == "quote_sent"]
    if args.case_id:
        selected = [case for case in selected if case.get("case_id") == args.case_id or case.get("id") == args.case_id]
    if args.limit is not None:
        selected = selected[: args.limit]
    if not selected:
        print("[NG] no quote_sent cases selected")
        return 1

    rendered_blocks = []
    for source in selected:
        case = build_case_from_source(source)
        rendered = render_case(case)
        rendered_blocks.append(f"case_id: {case['id']}\n{rendered}")
        if args.save:
            if len(selected) != 1:
                print("[NG] --save requires exactly one case")
                return 1
            shared.save_reply(rendered, case["raw_message"])

    print("\n\n----\n\n".join(rendered_blocks))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
