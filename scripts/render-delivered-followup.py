#!/usr/bin/env python3
from __future__ import annotations

import argparse
import importlib.util
import re
from datetime import datetime, timedelta
from pathlib import Path
from zoneinfo import ZoneInfo

import yaml


ROOT_DIR = Path(__file__).resolve().parents[1]
PREQUOTE_RENDERER = ROOT_DIR / "scripts/render-prequote-estimate-initial.py"
SERVICE_REGISTRY_PATH = ROOT_DIR / "os/core/service-registry.yaml"
PUBLIC_BUGFIX_SERVICE_ID = "bugfix-15000"
JST = ZoneInfo("Asia/Tokyo")


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
        (item for item in registry.get("services") or [] if item.get("service_id") == PUBLIC_BUGFIX_SERVICE_ID),
        None,
    )
    if service is None:
        raise RuntimeError(f"missing public delivered service grounding: {PUBLIC_BUGFIX_SERVICE_ID}")
    if not service.get("public"):
        raise RuntimeError(f"delivered service is not public: {PUBLIC_BUGFIX_SERVICE_ID}")

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
        "talkroom_only_rule": "必要なやり取りはこのトークルーム内で進めます。",
        "same_cause_rule": "同じ原因なら差し戻しの続きとして見ます。別の原因なら、その時点で切り分けて案内します。",
        "deployment_boundary_rule": "本番反映の代行は前提にしていません。必要なら反映手順が分かる形で返します。",
        "support_window_rule": "補足で答えられる範囲ならこのまま返します。",
    }


SERVICE_GROUNDING = load_service_grounding()


def time_commit(hours: int = 2) -> str:
    target = datetime.now(JST) + timedelta(hours=hours)
    return f"本日{target:%H:%M}までに、確認結果をお返しします。"


def is_complaint_like(source: dict, scenario: str | None = None) -> bool:
    raw = source.get("raw_message", "")
    tone = source.get("emotional_tone", "")
    if tone == "complaint_like":
        return True
    if scenario in {"price_complaint", "delivery_scope_mismatch"}:
        return True
    return any(marker in raw for marker in ["期待していた内容と違います", "高い気が", "高かったかも", "モヤモヤ"])


def build_temperature_plan_for_case(source: dict, scenario: str) -> dict:
    if scenario == "price_complaint":
        plan = shared.build_temperature_plan(source, case_type="after_close")
        plan["opening_move"] = "receive_and_own"
        plan["support_goal"] = "receive_feedback"
        return plan
    if scenario in {
        "approval_ok",
        "generic_delivered",
        "delivery_scope_mismatch",
        "same_cause_check",
        "doc_to_bugfix_addon",
        "deployment_help_request",
        "future_architecture_question",
        "doc_explanation_request",
        "postdelivery_question_window",
    }:
        return shared.build_temperature_plan(source, case_type="boundary")
    return shared.build_temperature_plan(source, case_type="bugfix")


def opener_for(source: dict) -> str:
    if is_complaint_like(source):
        return ""
    if source.get("scenario") == "approval_wait_request":
        return "大丈夫です。"
    return "ご連絡ありがとうございます。"


def detect_scenario(source: dict) -> str:
    raw = source.get("raw_message", "")
    note = source.get("note", "")
    service_hint = source.get("service_hint", "")
    combined = f"{raw}\n{note}"

    if "高い気が" in combined or "await が一つ" in combined or "1箇所の修正" in combined:
        return "price_complaint"
    if "価値があったのか" in combined or "モヤモヤ" in combined or "高かったかも" in combined:
        return "price_complaint"
    if "ビルドが通らなくなりました" in combined or "手順通りにやったつもり" in combined:
        return "apply_followup_issue"
    if "承諾はもう少し待って" in combined or "正式な承諾" in combined or "待ってもらっていいですか" in combined:
        return "approval_wait_request"
    if "承諾に進んで大丈夫" in combined:
        return "approval_ok"
    if "期待していた内容と違います" in combined or "診断レポートだけ" in combined:
        return "delivery_scope_mismatch"
    if "未確認" in combined and ("できなかった" in combined or "スコープ外" in combined):
        return "doc_status_question"
    if "そのまま追加でお願い" in combined or "修正依頼として別件への移行" in combined or "修正後の状態に合わせてもらう" in combined:
        return "doc_to_bugfix_addon"
    if "ここも危なそう" in combined or "予防的に知っておきたくて" in combined:
        return "future_risk_question"
    if "本番に反映作業まで" in combined or "Vercelへの上げ方がわかりません" in combined:
        return "deployment_help_request"
    if "全体の構成見直し" in combined or "おいくらくらい" in combined:
        return "future_architecture_question"
    if "もう少しかみ砕いた説明" in combined:
        return "doc_explanation_request"
    if "質問が出たら聞いてもいいですか" in combined:
        return "postdelivery_question_window"
    if "同じ原因ですか" in combined or "前と違う動き" in combined:
        return "same_cause_check"
    if "今後また同じことが起きる可能性" in combined or "予防できるなら" in combined:
        return "prevention_question"
    if "Vercelにデプロイすると500エラー" in combined or "差し戻しというか" in combined or "また違うエラー" in combined:
        return "redelivery_same_error"
    if "影響ですか" in combined or "別の機能が動かなく" in combined or "せいじゃないですか" in combined:
        return "side_effect_question"
    if "テスト" in combined and "ダッシュボード" in combined:
        return "dashboard_test_label"
    if service_hint == "handoff" and "メモ" in combined and "わかりやすかった" in combined:
        return "postdelivery_question_window"
    return "generic_delivered"


def extract_facts_known(raw: str, scenario: str) -> list[str]:
    facts: list[str] = []
    if "納品" in raw or "承諾" in raw:
        facts.append("delivery_context_present")
    if "エラー" in raw or "止まって" in raw or "動いて" in raw or "ビルド" in raw:
        facts.append("symptom_surface_described")
    if "15,000" in raw or "15000" in raw or "高い" in raw:
        facts.append("price_context_present")
    if "メモ" in raw or "資料" in raw:
        facts.append("document_context_present")
    if scenario in {"deployment_help_request", "future_architecture_question"}:
        facts.append("scope_boundary_question_present")
    if "テスト" in raw and "ダッシュボード" in raw:
        facts.append("dashboard_test_label_present")
    if "メール送信" in raw:
        facts.append("mail_flow_mentioned")
    if "診断レポートだけ" in raw:
        facts.append("report_only_named")
    if "修正ファイル" in raw:
        facts.append("fix_file_named")
    if "承諾" in raw:
        facts.append("approval_question_present")
    return facts


def build_primary_concern(source: dict, scenario: str, facts_known: list[str]) -> str:
    raw = source.get("raw_message", "")

    if scenario == "dashboard_test_label":
        return "ダッシュボードの「テスト」表示が異常か確認したい"
    if scenario == "side_effect_question":
        return "別の機能停止が今回の修正の影響か知りたい"
    if scenario == "prevention_question":
        return "今後の再発可能性と予防の考え方を知りたい"
    if scenario == "redelivery_same_error":
        return "本番だけ残る同じエラーが修正不足か環境差か知りたい"
    if scenario == "approval_ok":
        return "問題なく動いたので承諾に進んでよいか確認したい"
    if scenario == "delivery_scope_mismatch":
        return "納品内容が期待とずれていた点をどう埋めるか確認したい"
    if scenario == "apply_followup_issue":
        return "反映後のビルドエラーを今回の続きで見てもらいたい"
    if scenario == "doc_status_question":
        return "納品物の「未確認」の意味を知りたい"
    if scenario == "doc_to_bugfix_addon":
        return "納品後の流れからそのまま修正相談に移れるか知りたい"
    if scenario == "future_risk_question":
        return "他に危なそうな箇所があるかを知りたい"
    if scenario == "deployment_help_request":
        return "反映で止まっているので代替支援の範囲を知りたい"
    if scenario == "future_architecture_question":
        return "全体見直しの相談入口と範囲感を知りたい"
    if scenario == "doc_explanation_request":
        return "納品資料をもう少しかみ砕いて説明してほしい"
    if scenario == "postdelivery_question_window":
        return "後から出た質問をこのままここで聞いてよいか確認したい"
    if scenario == "same_cause_check":
        return "追加で出た症状が前回と同じ原因か知りたい"
    if scenario == "price_complaint":
        return "納品内容に対して料金が高く感じる"
    if scenario == "approval_wait_request":
        return "承諾を少し待ってほしい"
    if raw:
        return shared.summarize_raw_message(raw)
    return "納品後の追加連絡をどう進めるか確認したい"


def build_hard_constraints(scenario: str, grounding: dict) -> dict:
    return {
        "service_id": grounding.get("service_id"),
        "public_service_only": bool(grounding.get("public_service")),
        "answer_before_procedure": True,
        "ask_only_if_blocking": True,
        "no_prod_deploy": scenario == "deployment_help_request",
        "no_external_contact": False,
        "same_cause_scope_rule": grounding.get("scope_unit") == "same_cause_and_same_flow_and_same_endpoint",
    }


def build_response_decision_plan(source: dict, scenario: str, contract: dict) -> dict:
    raw = source.get("raw_message", "")
    primary_id = contract["primary_question_id"]
    answer_map = contract["answer_map"]
    primary = next(item for item in answer_map if item["question_id"] == primary_id)
    facts_known = extract_facts_known(raw, scenario)
    blocking_missing_facts: list[str] = []
    direct_answer_line = primary["answer_brief"]

    if primary["disposition"] in {"answer_now", "decline"}:
        response_order = ["opening", "direct_answer", "answer_detail"]
    else:
        response_order = ["opening", "direct_answer", "answer_detail", "ask", "next_action"]

    if scenario == "dashboard_test_label":
        blocking_missing_facts = ["dashboard_mode_screen"]
        direct_answer_line = "修正した決済フローが動いているなら、その表示だけで異常とは限りません。"
    elif scenario == "side_effect_question":
        blocking_missing_facts = ["mail_error_surface"]
        direct_answer_line = "今の文面だけでは、今回の修正の影響かどうかはまだ切り分けられていません。"
    elif scenario == "redelivery_same_error":
        blocking_missing_facts = ["post_deploy_error_surface"]
        direct_answer_line = "今の時点では、修正が足りていないとはまだ言い切れません。"
    elif scenario == "delivery_scope_mismatch":
        if "report_only_named" in facts_known and "fix_file_named" in facts_known:
            direct_answer_line = "期待と違っていた点として、診断レポートだけで修正ファイルが入っていなかった点は確認しました。"
            response_order = ["opening", "direct_answer", "answer_detail", "next_action"]
        else:
            blocking_missing_facts = ["missing_points"]
            direct_answer_line = "期待と違っていた点は確認しました。"
    elif scenario == "apply_followup_issue":
        blocking_missing_facts = ["build_error_text"]
    elif scenario == "doc_to_bugfix_addon":
        blocking_missing_facts = ["target_fix_points"]
    elif scenario == "future_architecture_question":
        blocking_missing_facts = ["target_review_scope"]
    elif scenario == "doc_explanation_request":
        blocking_missing_facts = ["hard_sections"]
        response_order = ["opening", "direct_answer", "answer_detail", "ask", "next_action"]
    elif scenario == "same_cause_check":
        blocking_missing_facts = ["current_symptom"]
    elif scenario == "future_risk_question":
        response_order = ["opening", "direct_answer", "answer_detail", "next_action"]
    elif scenario == "price_complaint":
        direct_answer_line = "ご指摘の通り、結果として小さく見える内容だったと思います。"
        response_order = ["opening", "direct_answer", "answer_detail"]
    elif scenario == "generic_delivered":
        response_order = ["opening", "direct_answer", "answer_detail", "next_action"]

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
        "src": source.get("route", "talkroom"),
        "state": "delivered",
        "emotional_tone": source.get("emotional_tone"),
        "raw_message": raw,
        "summary": shared.derive_summary(source),
        "known_facts": shared.extract_known_facts(source),
        "routing_meta": shared.build_routing_meta(source, scenario),
        "scenario": scenario,
        "service_grounding": dict(SERVICE_GROUNDING),
        "hard_constraints": build_hard_constraints(scenario, SERVICE_GROUNDING),
        "temperature_plan": build_temperature_plan_for_case(source, scenario),
        "reply_stance": {
            "burden_owner": "us",
            "empathy_first": source.get("emotional_tone") in {"anxious", "frustrated", "complaint_like"},
            "reply_skeleton": "delivery",
        },
    }

    if scenario == "dashboard_test_label":
        case["reply_contract"] = {
            "primary_question_id": "q1",
            "explicit_questions": [{"id": "q1", "text": "Stripeのダッシュボードにテストと出るのは正常か", "priority": "primary"}],
            "answer_map": [
                {
                    "question_id": "q1",
                    "disposition": "answer_after_check",
                    "answer_brief": "修正した決済フローが動いているなら、その表示だけで異常とは限りません。",
                    "hold_reason": "まずはStripeのテストモードと本番モードの見分けを確認したいです。",
                    "revisit_trigger": "画面を受領したあとに、見えているモードをお返しします。",
                }
            ],
            "ask_map": [
                {
                    "id": "a1",
                    "question_ids": ["q1"],
                    "ask_text": "Stripeダッシュボード上部のモード切り替えが見える画面を1枚送ってください。",
                    "why_needed": "テストモードを見ているだけかを先に切るため",
                }
            ],
            "required_moves": ["react_briefly_first", "defer_with_reason", "request_minimum_evidence", "commit_next_update_time"],
        }
        return case

    if scenario == "side_effect_question":
        case["reply_contract"] = {
            "primary_question_id": "q1",
            "explicit_questions": [{"id": "q1", "text": "今回の修正の影響か", "priority": "primary"}],
            "answer_map": [
                {
                    "question_id": "q1",
                    "disposition": "answer_after_check",
                    "answer_brief": "今の文面だけでは、今回の修正の影響かどうかはまだ切り分けられていません。",
                    "hold_reason": "修正箇所と、止まっているメール送信のつながりを先に確認します。",
                    "revisit_trigger": "状況を受領したあとに、今回の修正との関係をお返しします。",
                }
            ],
            "ask_map": [
                {
                    "id": "a1",
                    "question_ids": ["q1"],
                    "ask_text": "メール送信が止まっていることが分かる画面か、操作手順を送ってください。",
                    "why_needed": "今回の修正とのつながりが強いかを先に見るため",
                }
            ],
            "required_moves": ["react_briefly_first", "defer_with_reason", "request_minimum_evidence", "commit_next_update_time"],
        }
        return case

    if scenario == "prevention_question":
        case["reply_contract"] = {
            "primary_question_id": "q1",
            "explicit_questions": [
                {"id": "q1", "text": "今後また同じことが起きる可能性はあるか", "priority": "primary"},
                {"id": "q2", "text": "承諾に進んでよいか", "priority": "secondary"},
            ],
            "answer_map": [
                {
                    "question_id": "q1",
                    "disposition": "answer_now",
                    "answer_brief": "今回直した箇所が同じ原因なら、起きにくくはしています。ただ、別の変更が入ると再発の可能性はゼロとは言い切れません。",
                },
                {
                    "question_id": "q2",
                    "disposition": "answer_now",
                    "answer_brief": "今回の確認内容で問題なければ、このまま承諾に進んでいただいて大丈夫です。",
                },
            ],
            "ask_map": [],
            "required_moves": ["react_briefly_first", "answer_directly_now"],
        }
        return case

    if scenario == "redelivery_same_error":
        case["reply_contract"] = {
            "primary_question_id": "q1",
            "explicit_questions": [{"id": "q1", "text": "修正が足りていないのか", "priority": "primary"}],
            "answer_map": [
                {
                    "question_id": "q1",
                    "disposition": "answer_after_check",
                    "answer_brief": "今の時点では、修正が足りていないとはまだ言い切れません。",
                    "hold_reason": "ローカルでは直っているので、デプロイ後に変わる条件から見ます。",
                    "revisit_trigger": "本番の状況を受領したあとに、次に見る場所をお返しします。",
                }
            ],
            "ask_map": [
                {
                    "id": "a1",
                    "question_ids": ["q1"],
                    "ask_text": "デプロイ後に出ているエラーの画面かメッセージを送ってください。",
                    "why_needed": "ローカルとの差分を先に切るため",
                }
            ],
            "required_moves": ["react_briefly_first", "defer_with_reason", "request_minimum_evidence", "commit_next_update_time"],
        }
        return case

    if scenario == "approval_ok":
        case["reply_contract"] = {
            "primary_question_id": "q1",
            "explicit_questions": [{"id": "q1", "text": "承諾に進んでよいか", "priority": "primary"}],
            "answer_map": [
                {
                    "question_id": "q1",
                    "disposition": "answer_now",
                    "answer_brief": "今回は問題なく動いているなら、このまま承諾に進んでいただいて大丈夫です。",
                }
            ],
            "ask_map": [],
            "required_moves": ["react_briefly_first", "answer_directly_now"],
        }
        return case

    if scenario == "delivery_scope_mismatch":
        mismatch_is_specific = "診断レポートだけ" in raw and "修正ファイル" in raw
        case["reply_contract"] = {
            "primary_question_id": "q1",
            "explicit_questions": [{"id": "q1", "text": "期待していた内容と違う", "priority": "primary"}],
            "answer_map": [
                {
                    "question_id": "q1",
                    "disposition": "answer_after_check",
                    "answer_brief": "期待と違っていた点として、診断レポートだけで修正ファイルが入っていなかった点は確認しました。"
                    if mismatch_is_specific
                    else "期待と違っていた点は確認しました。",
                    "hold_reason": "まず、『原因特定と修正』の認識だった点も含めて、納品内容とのずれを確認します。"
                    if mismatch_is_specific
                    else "まずは今回の認識差を確認して、差し戻しで埋める範囲かを切ります。",
                    "revisit_trigger": "今回の認識差を確認したうえで、どの形で対応するかをお伝えします。"
                    if mismatch_is_specific
                    else "足りなかった点を受領したあとに、どの形で対応するかをお伝えします。",
                }
            ],
            "ask_map": []
            if mismatch_is_specific
            else [
                {
                    "id": "a1",
                    "question_ids": ["q1"],
                    "ask_text": "足りないと感じた点を1〜2点だけそのまま送ってください。",
                    "why_needed": "差し戻しで埋める話か、認識差の整理が先かを切るため",
                }
            ],
            "required_moves": ["react_briefly_first", "defer_with_reason", "commit_next_update_time"]
            if mismatch_is_specific
            else ["react_briefly_first", "defer_with_reason", "request_minimum_evidence", "commit_next_update_time"],
        }
        return case

    if scenario == "apply_followup_issue":
        case["reply_contract"] = {
            "primary_question_id": "q1",
            "explicit_questions": [{"id": "q1", "text": "反映後にビルドが通らない", "priority": "primary"}],
            "answer_map": [
                {
                    "question_id": "q1",
                    "disposition": "answer_after_check",
                    "answer_brief": "反映後にビルドが通らなくなった件、こちらでも一緒に確認します。",
                    "hold_reason": "手順の抜けか差分の反映違いかを先に切りたいです。",
                    "revisit_trigger": "エラー内容を受領したあとに、どこから確認するかをお返しします。",
                }
            ],
            "ask_map": [
                {
                    "id": "a1",
                    "question_ids": ["q1"],
                    "ask_text": "出ているエラー文が分かれば、そのまま送ってください。",
                    "why_needed": "反映漏れか別のビルド要因かを先に切るため",
                }
            ],
            "required_moves": ["react_briefly_first", "defer_with_reason", "request_minimum_evidence", "commit_next_update_time"],
        }
        return case

    if scenario == "doc_status_question":
        case["reply_contract"] = {
            "primary_question_id": "q1",
            "explicit_questions": [{"id": "q1", "text": "未確認の意味は何か", "priority": "primary"}],
            "answer_map": [
                {
                    "question_id": "q1",
                    "disposition": "answer_now",
                    "answer_brief": "ここでの「未確認」は、今回はそこまで確認していないという意味です。できなかったのか、今回の範囲外だったのかは必要なら補足します。",
                }
            ],
            "ask_map": [],
            "required_moves": ["react_briefly_first", "answer_directly_now"],
        }
        return case

    if scenario == "doc_to_bugfix_addon":
        case["reply_contract"] = {
            "primary_question_id": "q1",
            "explicit_questions": [{"id": "q1", "text": "このまま修正相談へ移れるか", "priority": "primary"}],
            "answer_map": [
                {
                    "question_id": "q1",
                    "disposition": "answer_after_check",
                    "answer_brief": "修正の相談には移れます。まず今の依頼の補足で足りるか、別の修正相談として切るかを確認します。",
                    "hold_reason": "納品後なので、そのまま続きとして扱う前に今回見たい内容を先に切りたいです。",
                    "revisit_trigger": "直したい点を受領したあとに、次の入口をお返しします。",
                }
            ],
            "ask_map": [
                {
                    "id": "a1",
                    "question_ids": ["q1"],
                    "ask_text": "直したい箇所か、修正後に合わせたい部分をそのまま送ってください。",
                    "why_needed": "補足で足りるか、修正相談に切るかを先に判断するため",
                }
            ],
            "required_moves": ["react_briefly_first", "defer_with_reason", "request_minimum_evidence", "commit_next_update_time"],
        }
        return case

    if scenario == "future_risk_question":
        case["reply_contract"] = {
            "primary_question_id": "q1",
            "explicit_questions": [{"id": "q1", "text": "他に危なそうな箇所があるか", "priority": "primary"}],
            "answer_map": [
                {
                    "question_id": "q1",
                    "disposition": "answer_after_check",
                    "answer_brief": "気になる箇所があればお伝えできます。まず今回の修正範囲の近くで見えているものがあるかを確認します。",
                    "hold_reason": "納品時に確定していない点を、その場で言い切るより確認してから返した方がずれません。",
                    "revisit_trigger": "確認できたところまでをお返しします。",
                }
            ],
            "ask_map": [],
            "required_moves": ["react_briefly_first", "defer_with_reason", "commit_next_update_time"],
        }
        return case

    if scenario == "deployment_help_request":
        case["reply_contract"] = {
            "primary_question_id": "q1",
            "explicit_questions": [{"id": "q1", "text": "本番反映までやってもらえるか", "priority": "primary"}],
            "answer_map": [
                {
                    "question_id": "q1",
                    "disposition": "answer_now",
                    "answer_brief": "本番反映の代行は前提にしていません。必要なら、このトークルーム内で反映手順が分かる形にして返します。",
                }
            ],
            "ask_map": [],
            "required_moves": ["react_briefly_first", "answer_directly_now"],
        }
        return case

    if scenario == "future_architecture_question":
        case["reply_contract"] = {
            "primary_question_id": "q1",
            "explicit_questions": [{"id": "q1", "text": "全体の見直しを相談するとしたらどうなるか", "priority": "primary"}],
            "answer_map": [
                {
                    "question_id": "q1",
                    "disposition": "answer_after_check",
                    "answer_brief": "全体の見直し相談としては受けられます。まず今回どこまで見たいかを確認してから入口をご案内します。",
                    "hold_reason": "納品後の追加相談なので、いきなり金額を決めるより内容を先に切った方がずれません。",
                    "revisit_trigger": "見たい範囲を受領したあとに、今回の入口をお返しします。",
                }
            ],
            "ask_map": [
                {
                    "id": "a1",
                    "question_ids": ["q1"],
                    "ask_text": "見直したい範囲が分かれば、そのまま送ってください。",
                    "why_needed": "相談の入口を先に切るため",
                }
            ],
            "required_moves": ["react_briefly_first", "defer_with_reason", "request_minimum_evidence", "commit_next_update_time"],
        }
        return case

    if scenario == "doc_explanation_request":
        case["reply_contract"] = {
            "primary_question_id": "q1",
            "explicit_questions": [
                {"id": "q1", "text": "もう少しかみ砕いた説明をお願いできるか", "priority": "primary"},
                {"id": "q2", "text": "追加料金がかかるか", "priority": "secondary"},
            ],
            "answer_map": [
                {
                    "question_id": "q1",
                    "disposition": "answer_now",
                    "answer_brief": "はい、説明をもう少しかみ砕いて補足することはできます。",
                },
                {
                    "question_id": "q2",
                    "disposition": "answer_after_check",
                    "answer_brief": "料金は、補足で足りる範囲かを見てからお伝えします。",
                    "hold_reason": "まずはどの部分が難しかったかを見て、補足で足りるかを先に切りたいです。",
                    "revisit_trigger": "分かりにくかった箇所を受領したあとにお返しします。",
                }
            ],
            "ask_map": [
                {
                    "id": "a1",
                    "question_ids": ["q1", "q2"],
                    "ask_text": "特に分かりにくかった箇所があれば、そのまま送ってください。",
                    "why_needed": "補足の範囲で足りるかを判断するため",
                }
            ],
            "required_moves": ["react_briefly_first", "answer_directly_now", "defer_with_reason", "request_minimum_evidence", "commit_next_update_time"],
        }
        return case

    if scenario == "postdelivery_question_window":
        case["reply_contract"] = {
            "primary_question_id": "q1",
            "explicit_questions": [{"id": "q1", "text": "後から出た質問をここで聞いてよいか", "priority": "primary"}],
            "answer_map": [
                {
                    "question_id": "q1",
                    "disposition": "answer_now",
                    "answer_brief": "はい、ここで聞いてもらって大丈夫です。補足で答えられる範囲ならそのまま返します。",
                }
            ],
            "ask_map": [],
            "required_moves": ["react_briefly_first", "answer_directly_now"],
        }
        return case

    if scenario == "same_cause_check":
        case["reply_contract"] = {
            "primary_question_id": "q1",
            "explicit_questions": [{"id": "q1", "text": "これも同じ原因か", "priority": "primary"}],
            "answer_map": [
                {
                    "question_id": "q1",
                    "disposition": "answer_after_check",
                    "answer_brief": "同じ原因かどうかは、まず今回の症状を見てからお返しします。",
                    "hold_reason": "納品後の追加確認なので、前回と同じ流れかを先に切りたいです。",
                    "revisit_trigger": "症状が分かるものを受領したあとに、前回とのつながりをお返しします。",
                }
            ],
            "ask_map": [
                {
                    "id": "a1",
                    "question_ids": ["q1"],
                    "ask_text": "気になっている画面か、前と違って見える点をそのまま送ってください。",
                    "why_needed": "同じ原因かを先に切るため",
                }
            ],
            "required_moves": ["react_briefly_first", "defer_with_reason", "request_minimum_evidence", "commit_next_update_time"],
        }
        return case

    if scenario == "price_complaint":
        case["reply_contract"] = {
            "primary_question_id": "q1",
            "explicit_questions": [
                {"id": "q1", "text": "修正量に対して高く感じる", "priority": "primary"},
                {"id": "q2", "text": "料金の考え方", "priority": "secondary"},
            ],
            "answer_map": [
                {
                    "question_id": "q1",
                    "disposition": "answer_now",
                    "answer_brief": "高く感じられたことは受け止めています。ご指摘の通り、結果として小さく見える内容だったと思います。",
                },
                {
                    "question_id": "q2",
                    "disposition": "answer_now",
                    "answer_brief": "料金は調査と切り分け、確認を含めた1件分です。",
                },
            ],
            "ask_map": [],
            "required_moves": ["react_briefly_first", "answer_directly_now"],
        }
        return case

    if scenario == "approval_wait_request":
        case["reply_contract"] = {
            "primary_question_id": "q1",
            "explicit_questions": [{"id": "q1", "text": "正式な承諾を待ってほしい", "priority": "primary"}],
            "answer_map": [
                {
                    "question_id": "q1",
                    "disposition": "answer_now",
                    "answer_brief": "確認が終わってから承諾いただければ問題ありません。",
                },
            ],
            "ask_map": [],
            "required_moves": ["react_briefly_first", "answer_directly_now"],
        }
        return case

    case["reply_contract"] = {
        "primary_question_id": "q1",
        "explicit_questions": [{"id": "q1", "text": "今回どう進めるか", "priority": "primary"}],
        "answer_map": [
            {
                "question_id": "q1",
                "disposition": "answer_after_check",
                "answer_brief": "今回のご連絡内容は確認しました。まず前回対応の続きで見られる話かを確認します。",
                "hold_reason": "納品後のご相談なので、今の確認ポイントを整理してからお返しします。",
                "revisit_trigger": "必要な情報を受領したあとに、どの形で進めるかをお伝えします。",
            }
        ],
        "ask_map": [],
        "required_moves": ["react_briefly_first", "defer_with_reason", "commit_next_update_time"],
    }
    return case


def reaction_line(case: dict) -> str:
    scenario = case["scenario"]
    temperature_plan = case.get("temperature_plan") or {}
    opening_move = temperature_plan.get("opening_move")
    user_signal = temperature_plan.get("user_signal")
    if scenario == "price_complaint":
        return "率直に伝えていただいてありがとうございます。高く感じられた点は受け止めています。"
    if scenario == "redelivery_same_error":
        return "デプロイ後に別のエラーが出ているとのこと、確認しました。"
    if opening_move == "action_first":
        if scenario in {"redelivery_same_error", "side_effect_question"}:
            return "まず今の状況から確認します。"
        return "まず必要なところから確認します。"
    if opening_move == "pressure_release":
        return "気を遣わなくて大丈夫です。"
    if opening_move == "normalize_then_clarify":
        return "いまの段階で迷うのは自然です。"
    if opening_move == "receive_and_own":
        return "率直に伝えていただいてありがとうございます。"
    if opening_move == "yes_no_first":
        if user_signal == "negative_feedback":
            return "率直に伝えていただいてありがとうございます。"
        return ""
    if scenario == "dashboard_test_label":
        return "納品後の確認ありがとうございます。Stripe画面の表示で気になっている点、確認しました。"
    if scenario == "side_effect_question":
        return "確認ありがとうございます。別の機能で気になる点が出ている件、確認しました。"
    if scenario == "prevention_question":
        return "動作確認ありがとうございます。再発予防についてのご質問、確認しました。"
    if scenario == "redelivery_same_error":
        return "デプロイ後に別のエラーが出ているとのこと、確認しました。"
    if scenario == "approval_ok":
        return "再確認ありがとうございます。今回は問題なく動いているとのこと、確認しました。"
    if scenario == "delivery_scope_mismatch":
        return "納品内容が期待と違っていたとのこと、確認しました。"
    if scenario == "apply_followup_issue":
        return "反映後にビルドが通らなくなった件、確認しました。"
    if scenario == "doc_status_question":
        return "納品物の表記についての確認ありがとうございます。"
    if scenario == "doc_to_bugfix_addon":
        return "追加で修正も相談したいとのこと、確認しました。"
    if scenario == "future_risk_question":
        return "予防的に見ておきたい点があるとのこと、確認しました。"
    if scenario == "deployment_help_request":
        return "反映のところで止まっている件、確認しました。"
    if scenario == "future_architecture_question":
        return "次のご相談も考えていただいている件、ありがとうございます。"
    if scenario == "doc_explanation_request":
        return "資料が少し難しかったとのこと、確認しました。"
    if scenario == "postdelivery_question_window":
        return "後から出た質問の扱いについての確認ありがとうございます。"
    if scenario == "same_cause_check":
        return "追加で気になる点が出ている件、確認しました。"
    if scenario == "price_complaint":
        return "率直に伝えていただいてありがとうございます。"
    if scenario == "approval_wait_request":
        return "ご連絡ありがとうございます。"
    return "納品後のご連絡、確認しました。"


def with_period(text: str) -> str:
    cleaned = shared.compact_text(text)
    if not cleaned:
        return ""
    return cleaned if cleaned.endswith("。") else f"{cleaned}。"


def _normalized(text: str) -> str:
    return re.sub(r"[\s。、，,.！？?「」『』（）()・:：/／\\-]+", "", text)


def _same_text(left: str, right: str) -> bool:
    nl = _normalized(left)
    nr = _normalized(right)
    return bool(nl and nr and nl == nr)


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


def _paragraph_from_lines(lines: list[str]) -> str:
    paragraph_lines: list[str] = []
    for line in lines:
        cleaned = with_period(line)
        if not cleaned:
            continue
        if any(_same_meaning(cleaned, existing) for existing in paragraph_lines):
            continue
        paragraph_lines.append(cleaned)
    return "\n".join(paragraph_lines)


def current_focus_line(case: dict) -> str | None:
    scenario = case["scenario"]
    if scenario == "dashboard_test_label":
        return "まず、Stripeの表示がテストモードを見ているだけか確認します。"
    if scenario == "side_effect_question":
        return "そこを見て、今回の修正とのつながりを切り分けます。"
    if scenario == "redelivery_same_error":
        return "ローカルでは直っているので、デプロイ後に変わる条件から見ます。"
    if scenario == "delivery_scope_mismatch":
        return "まず、『原因特定と修正』の認識だった点も含めて、納品内容とのずれを確認します。"
    if scenario == "apply_followup_issue":
        return "まず手順の抜けか差分の反映違いかを切り分けます。"
    if scenario == "doc_to_bugfix_addon":
        return "まず今回の補足で足りるか、別の修正相談として切るかを確認します。"
    if scenario == "future_risk_question":
        return "まず今回の修正範囲の近くで気になる点があるかを見ます。"
    if scenario == "future_architecture_question":
        return "まず今回どこまで見直したいかが分かると、入口を整理しやすいです。"
    if scenario == "doc_explanation_request":
        return "まず分かりにくかった箇所を見て、補足で足りるかを確認します。"
    if scenario == "same_cause_check":
        return "まず前回と同じ流れの話かを確認します。"
    if scenario == "generic_delivered":
        return "まず前回対応の続きとして見られる話かを確認します。"
    return None


def draft_opening_anchor(case: dict) -> str:
    scenario = case["scenario"]
    raw = case.get("raw_message", "")
    if scenario == "dashboard_test_label":
        return "Stripeダッシュボードの「テスト」表示が気になっているとのこと、確認しました。"
    if scenario == "side_effect_question":
        if "メール送信" in raw:
            return "まずメール送信の件から見ます。"
        return "まず別の機能で出ている症状から確認します。"
    if scenario == "prevention_question":
        return "動作確認ありがとうございます。再発予防についてのご質問、確認しました。"
    if scenario == "redelivery_same_error":
        if "Vercel" in raw:
            return "Vercelにデプロイすると500エラーが残るとのこと、確認しました。"
        return "まずデプロイ後に変わる条件から確認します。"
    if scenario == "approval_ok":
        return "今回は問題なく動いているとのこと、確認しました。"
    if scenario == "delivery_scope_mismatch":
        if "診断レポートだけ" in raw and "修正ファイル" in raw:
            return "納品内容にずれがあったとのこと、確認しました。"
        return "納品内容が期待と違っていたとのこと、確認しました。"
    if scenario == "apply_followup_issue":
        return "まず反映後のビルドエラーから確認します。"
    if scenario == "doc_status_question":
        return "納品物の表記についての確認、ありがとうございます。"
    if scenario == "doc_to_bugfix_addon":
        return "追加で修正も相談したいとのこと、確認しました。"
    if scenario == "future_risk_question":
        return "予防的に見ておきたい点があるとのこと、確認しました。"
    if scenario == "deployment_help_request":
        return "反映のところで止まっている件、確認しました。"
    if scenario == "future_architecture_question":
        return "次のご相談も考えていただいている件、ありがとうございます。"
    if scenario == "doc_explanation_request":
        return "資料が少し難しかったとのこと、確認しました。"
    if scenario == "postdelivery_question_window":
        return "後から出た質問の扱いについての確認、ありがとうございます。"
    if scenario == "same_cause_check":
        return "追加で気になる点が出ている件、確認しました。"
    if scenario == "price_complaint":
        return "率直に伝えていただいてありがとうございます。高く感じられた点は受け止めています。"
    if scenario == "approval_wait_request":
        return "承諾を少し待ちたいとのこと、承知しました。"
    return reaction_line(case)


def draft_body_paragraphs(case: dict) -> list[str]:
    scenario = case["scenario"]
    contract = case["reply_contract"]
    decision_plan = case.get("response_decision_plan") or {}
    primary_id = contract["primary_question_id"]
    primary = next(item for item in contract["answer_map"] if item["question_id"] == primary_id)
    secondary_now = [item for item in contract["answer_map"] if item["question_id"] != primary_id and item["disposition"] == "answer_now"]
    secondary_after = [
        item for item in contract["answer_map"] if item["question_id"] != primary_id and item["disposition"] == "answer_after_check"
    ]
    ask_map = contract.get("ask_map") or []
    blocking_missing_facts = decision_plan.get("blocking_missing_facts") or []
    direct_answer = with_period(decision_plan.get("direct_answer_line") or primary["answer_brief"])
    focus_line = current_focus_line(case)
    paragraphs: list[str] = []

    if scenario == "dashboard_test_label":
        _append_unique(paragraphs, direct_answer)
        _append_unique(
            paragraphs,
            _paragraph_from_lines(
                [
                    focus_line or "",
                    "Stripeダッシュボード上部のモード切り替えが見える画面を1枚送ってください。",
                ]
            ),
        )
        return paragraphs

    if scenario == "side_effect_question":
        _append_unique(paragraphs, direct_answer)
        _append_unique(
            paragraphs,
            _paragraph_from_lines(
                [
                    "メール送信が止まっていることが分かる画面か、操作手順を送ってください。",
                    focus_line or "",
                ]
            ),
        )
        return paragraphs

    if scenario == "delivery_scope_mismatch":
        _append_unique(paragraphs, direct_answer)
        if blocking_missing_facts:
            _append_unique(
                paragraphs,
                _paragraph_from_lines(
                    [
                        "足りないと感じた点を1〜2点だけそのまま送ってください。",
                        "その内容を見て、差し戻しで埋める範囲かをこちらで確認します。",
                    ]
                ),
            )
        else:
            _append_unique(
                paragraphs,
                _paragraph_from_lines(
                    [
                        "ご期待に沿えていない点、すみません。",
                        focus_line or "",
                    ]
                ),
            )
        return paragraphs

    if scenario == "redelivery_same_error":
        _append_unique(paragraphs, direct_answer)
        _append_unique(
            paragraphs,
            _paragraph_from_lines(
                [
                    focus_line or "",
                    "デプロイ後に出ているエラーの画面かメッセージを送ってください。",
                ]
            ),
        )
        return paragraphs

    if scenario == "apply_followup_issue":
        _append_unique(paragraphs, direct_answer)
        _append_unique(
            paragraphs,
            _paragraph_from_lines(
                [
                    focus_line or "",
                    "出ているエラー文が分かれば、そのまま送ってください。",
                ]
            ),
        )
        return paragraphs

    if scenario == "price_complaint":
        _append_unique(
            paragraphs,
            _paragraph_from_lines(
                [direct_answer] + [item["answer_brief"] for item in secondary_now if item.get("answer_brief")]
            ),
        )
        return paragraphs

    answer_lines = [direct_answer]
    answer_lines.extend(item["answer_brief"] for item in secondary_now if item.get("answer_brief"))
    _append_unique(paragraphs, _paragraph_from_lines(answer_lines))

    detail_lines: list[str] = []
    if primary["disposition"] == "answer_after_check":
        if focus_line:
            detail_lines.append(focus_line)
        elif primary.get("hold_reason"):
            detail_lines.append(primary["hold_reason"])
    for item in secondary_after:
        if item.get("answer_brief"):
            detail_lines.append(item["answer_brief"])
        if item.get("hold_reason"):
            detail_lines.append(item["hold_reason"])
    detail_paragraph = _paragraph_from_lines(detail_lines)
    if detail_paragraph:
        _append_unique(paragraphs, detail_paragraph)

    if blocking_missing_facts:
        _append_unique(paragraphs, _paragraph_from_lines([ask.get("ask_text", "") for ask in ask_map]))

    return paragraphs


def build_delivered_render_payload(case: dict, opening_block: str, body_paragraphs: list[str], next_action: str) -> dict:
    fixed_slots: dict[str, str] = {}
    if body_paragraphs:
        fixed_slots["answer_core"] = body_paragraphs[0]
    if len(body_paragraphs) > 1:
        fixed_slots["detail_core"] = "\n\n".join(body_paragraphs[1:])
    if next_action:
        fixed_slots["next_action"] = next_action
    return {
        "fixed_slots": fixed_slots,
        "editable_slots": {
            "ack": opening_block,
            "closing": next_action,
        },
        "draft_paragraphs": [opening_block, *body_paragraphs, next_action],
    }


def render_case(case: dict) -> str:
    if not case.get("response_decision_plan"):
        case["response_decision_plan"] = build_response_decision_plan(
            {"raw_message": case.get("raw_message", "")},
            case.get("scenario", "generic_delivered"),
            case["reply_contract"],
        )
    if not case.get("service_grounding"):
        case["service_grounding"] = dict(SERVICE_GROUNDING)
    if not case.get("hard_constraints"):
        case["hard_constraints"] = build_hard_constraints(case.get("scenario", "generic_delivered"), SERVICE_GROUNDING)

    decision_plan = case.get("response_decision_plan") or {}
    first_lines = [opener_for(case)]
    reaction = draft_opening_anchor(case)
    direct_answer = decision_plan.get("direct_answer_line") or ""
    if reaction and not _same_meaning(reaction, direct_answer):
        first_lines.append(reaction)
    opening_block = "\n".join(line for line in first_lines if line.strip())

    body_paragraphs: list[str] = []
    for paragraph in draft_body_paragraphs(case):
        _append_unique(body_paragraphs, paragraph)

    contract = case["reply_contract"]
    primary_id = contract["primary_question_id"]
    primary = next(item for item in contract["answer_map"] if item["question_id"] == primary_id)
    next_action = time_commit() if (primary["disposition"] == "answer_after_check" or decision_plan.get("blocking_missing_facts")) else ""

    sections: list[str] = []
    _append_unique(sections, opening_block)
    for paragraph in body_paragraphs:
        _append_unique(sections, paragraph)
    if next_action:
        _append_unique(sections, next_action)

    case["render_payload"] = build_delivered_render_payload(case, opening_block, body_paragraphs, next_action)
    return "\n\n".join(section for section in sections if section.strip())


def main() -> int:
    parser = argparse.ArgumentParser(description="Render delivered follow-up replies from flat delivered cases.")
    parser.add_argument("--fixture", required=True)
    parser.add_argument("--case-id")
    parser.add_argument("--limit", type=int)
    parser.add_argument("--save", action="store_true")
    args = parser.parse_args()

    cases = shared.load_cases(Path(args.fixture))
    selected = [case for case in cases if case.get("state") == "delivered"]
    if args.case_id:
        selected = [case for case in selected if case.get("case_id") == args.case_id or case.get("id") == args.case_id]
    if args.limit is not None:
        selected = selected[: args.limit]
    if not selected:
        print("[NG] no delivered cases selected")
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
