#!/usr/bin/env python3
from __future__ import annotations

import argparse
import importlib.util
import re
from datetime import datetime, timedelta
from pathlib import Path
from zoneinfo import ZoneInfo

import yaml
from reply_quality_lint_common import infer_buyer_emotion


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
        raise RuntimeError(f"missing public closed service grounding: {PUBLIC_BUGFIX_SERVICE_ID}")
    if not service.get("public"):
        raise RuntimeError(f"closed service is not public: {PUBLIC_BUGFIX_SERVICE_ID}")

    facts_path = Path(service.get("facts_file") or "")
    if not facts_path.is_file():
        raise RuntimeError(f"missing service facts file: {facts_path}")

    with facts_path.open("r", encoding="utf-8") as f:
        facts = yaml.safe_load(f) or {}

    base_price = int(facts.get("base_price") or 15000)
    return {
        "service_id": service.get("service_id"),
        "public_service": bool(service.get("public")),
        "display_name": facts.get("display_name") or "",
        "base_price": base_price,
        "fee_text": f"{base_price:,}円",
        "scope_unit": facts.get("scope_unit") or "",
        "closed_room_boundary_rule": "前回のトークルームは閉じているため、そのまま同じトークルームで続ける形にはしません。",
        "same_cause_rule": "同じ原因なら前回の続きに近い話として見ます。別の原因なら切り分けて案内します。",
        "public_scope_rule": "公開中の bugfix 範囲で案内します。",
        "hard_no": facts.get("hard_no") or [],
    }


SERVICE_GROUNDING = load_service_grounding()


def time_commit(hours: int = 2) -> str:
    target = datetime.now(JST) + timedelta(hours=hours)
    remainder = target.minute % 15
    if remainder:
        target = target + timedelta(minutes=15 - remainder)
    target = target.replace(second=0, microsecond=0)
    return f"本日{target:%H:%M}までに、見立てをお返しします。"


def build_temperature_plan_for_case(source: dict, scenario: str) -> dict:
    if scenario == "feedback_for_next_time":
        plan = shared.build_temperature_plan(source, case_type="after_close")
        plan["opening_move"] = "receive_and_own"
        return plan
    if scenario in {
        "refund_request",
        "memo_rewrite",
        "new_feature_request",
        "new_flow_plus_discount",
        "repeat_bugfix_price_check",
        "same_ticket_scope_question",
        "design_maintenance_request",
        "price_discount_request",
        "similar_but_not_same",
        "price_complaint",
        "same_symptom_recur",
        "api_version_notice_question",
        "dashboard_login_issue",
        "generic_closed",
    }:
        return shared.build_temperature_plan(source, case_type="boundary")
    return shared.build_temperature_plan(source, case_type="after_close")


def opener_for(source: dict) -> str:
    if is_complaint_like(source):
        return ""
    return "ご連絡ありがとうございます。"


def is_complaint_like(source: dict, scenario: str | None = None) -> bool:
    raw = source.get("raw_message", "")
    tone = source.get("emotional_tone", "")
    if tone == "complaint_like":
        return True
    if scenario in {"refund_request", "price_complaint"}:
        return True
    return any(marker in raw for marker in ["納得いかない", "返金して", "意味がない", "お金を払いたくない"])


def has_discount_probe(text: str) -> bool:
    return bool(
        re.search(r"(^|[^0-9])5,?000円", text)
        or re.search(r"(^|[^0-9])10,?000円", text)
        or any(marker in text for marker in ["割引", "安く", "リピーター", "パッケージ"])
    )


def detect_scenario(source: dict) -> str:
    raw = source.get("raw_message", "")
    note = source.get("note", "")
    combined = f"{raw}\n{note}"
    service_hint = source.get("service_hint", "")

    if "Google Drive" in combined or "Googleドライブ" in combined or "Dropbox" in combined:
        return "closed_external_large_share"
    if any(marker in combined for marker in [".env", "envファイル", "Stripeのキー", "APIキー", "秘密鍵"]):
        if any(marker in combined for marker in ["そのまま送", "一緒に送", "値", "キーも入って"]):
            return "closed_secret_send_question"
    if any(marker in combined for marker in ["ZIPでコード", "コード一式", "直して返して", "修正して返"]):
        return "closed_zip_fix_return"
    if any(marker in combined for marker in ["ログとスクショ", "ログやスクショ", "関係あるかだけ", "関係があるかだけ"]):
        return "closed_materials_check"
    if any(marker in combined for marker in ["無料で直", "無料で対応", "15,000円かかる", "15000円かかる", "納得できません"]):
        return "closed_free_followup_price"
    if any(marker in combined for marker in ["先に原因だけ", "原因だけ見てもら", "見積り前", "お願いするか決めたい"]):
        return "closed_pre_estimate_cause_check"
    if (
        any(marker in combined for marker in ["どこを直せば", "直し方", "文章で教えて"])
        and any(marker in combined for marker in ["購入なし", "ファイル返却までは不要", "コードをここに貼"])
    ):
        return "closed_pre_estimate_cause_check"
    if any(marker in combined for marker in ["useEffect", "依存配列"]) or (
        "userId" in combined and any(marker in combined for marker in ["入れなくて", "よかった", "本当"])
    ):
        return "closed_technical_followup_question"
    if any(marker in combined for marker in ["知り合い", "エンジニア", "開発者"]) and any(
        marker in combined
        for marker in ["前回の修正範囲", "元のお値段", "予防的", "直しておいた方", "別のところに影響", "ここもおかしい"]
    ):
        return "closed_third_party_scope_concern"

    if service_hint == "handoff" and (
        "そのまま購入" in combined
        or "同じように整理" in combined
        or "別の「" in raw
        or "別のフロー" in combined
    ):
        return "repeat_handoff_request"
    if service_hint == "handoff" and (
        "追記" in combined
        or "深い階層" in combined
        or "DB" in combined
        or "書き込み部分" in combined
    ):
        return "memo_addendum_request"
    if service_hint == "handoff" and (
        "次回は" in combined
        or "歴史的背景" in combined
        or "解説として" in combined
    ):
        return "future_doc_preference"
    if any(marker in combined for marker in ["CSS", "デザイン", "保守", "月額"]):
        return "design_maintenance_request"
    if "手数料を下げる方法" in combined or "直接は関係ない質問" in combined:
        return "out_of_scope_general_question"
    if "管理画面にログインできなく" in combined or ("Stripe" in combined and "ログインでき" in combined):
        return "dashboard_login_issue"
    if "紹介" in combined and any(marker in combined for marker in ["メルマガ", "全然急がない", "いつか見てもらえ", "同じサイト"]):
        return "referral_and_soft_new_issue"
    if any(marker in combined for marker in ["テストモード", "本番モード", "サンドボックス"]) and any(
        marker in combined for marker in ["切り替え", "どこでやる", "どこでやるんでしたっけ", "メモを失く"]
    ):
        return "mode_toggle_reminder"
    if any(marker in combined for marker in ["APIキー", "ローテーション", "Webhookだけ", "新しいキーに切り替えるのを忘れて"]) and any(
        marker in combined for marker in ["また同じエラー", "どこを直せば", "見つけられなくて"]
    ):
        return "webhook_secret_rotation_followup"
    if "APIバージョン" in combined or ("Stripe" in combined and "通知メール" in combined):
        return "api_version_notice_question"
    if "テスト環境がない" in combined or "どうやって確認すれば" in combined or "いきなり本番で試すしかない" in combined:
        return "followup_test_howto"

    if "時々決済が通らない" in combined or "少し不安でもう一度見てほしい" in combined:
        return "recur_uncertainty"
    if "返金" in combined:
        return "refund_request"
    if "お気に入り" in combined or "★5" in combined:
        return "favorite_and_discount"
    if "検証手順" in combined or "社内で" in combined:
        return "quality_feedback_manual"
    if "引き継ぎメモ" in combined or "書き直し" in combined:
        return "memo_rewrite"
    if "専門的すぎ" in combined or "噛み砕いた説明" in combined or "途中で状況を教えて" in combined or "安心だったかな" in combined:
        return "feedback_for_next_time"
    if "もう1フロー" in combined or "別のフロー" in combined or ("少し安く" in combined and "メモ" in combined):
        return "new_flow_plus_discount"
    if "新規でお願いする場合" in combined or "また15,000円ですか" in combined or "買い直す必要ありますか" in combined or "新規依頼の方がいいですか" in combined:
        return "repeat_bugfix_price_check"
    if (
        any(marker in combined for marker in ["次はどうすれば", "先にこのメッセージ", "購入してから相談", "新しく購入してから相談"])
        and any(marker in combined for marker in ["また別", "別の決済エラー", "別のエラー", "新しく購入"])
    ):
        return "closed_next_consult_path"
    if (
        "別の件" in combined
        or "別件" in combined
        or "前回の件とは別" in combined
        or "前回とは別" in combined
        or "別のエンドポイント" in combined
        or "またお願いしたい" in combined
        or "お願いできるものなんでしょうか" in combined
        or ("Stripeとは直接関係ない" in combined and "お願い" in combined)
    ):
        return "new_issue_repeat_client"
    if "コードを少し触った" in combined or "自分のせい" in combined or "自分で触った" in combined:
        return "self_edit_regression"
    if "新しい機能" in combined or "クーポン機能" in combined or (any(marker in combined for marker in ["Invoice", "請求書"]) and "追加" in combined):
        return "new_feature_request"
    if "違うイベント" in combined:
        return "similar_but_not_same"
    if "今回の15000円の範囲内" in combined or "今回の15,000円の範囲内" in combined:
        return "same_ticket_scope_question"
    if has_discount_probe(combined) or "コピペしてもらえませんか" in combined:
        return "price_discount_request"
    if (
        "またお金がかかる" in combined
        or "毎回お金を払" in combined
        or "納得いかない" in combined
        or "何万円も払いたくない" in combined
        or "意味がない" in combined
        or "お金を払いたくない" in combined
        or "高かったかな" in combined
    ):
        return "price_complaint"
    if "直っていない" in combined or "解決していない" in combined:
        return "same_symptom_recur"
    if "また同じ" in combined or "またおかしく" in combined or "前回の続き" in combined or "またエラー" in combined or "似たようなエラー" in combined or "前と同じ原因かもしれない" in combined:
        return "same_symptom_recur"
    return "generic_closed"


def extract_facts_known(raw: str, scenario: str) -> list[str]:
    facts: list[str] = []
    if "前回" in raw or "以前" in raw:
        facts.append("previous_ticket_context_present")
    if "メモ" in raw or "引き継ぎ" in raw:
        facts.append("memo_context_present")
    if "15,000" in raw or "15000" in raw or "5,000" in raw or "5000" in raw or "返金" in raw:
        facts.append("price_or_refund_context_present")
    if any(marker in raw for marker in ["エラー", "症状", "通らない", "おかしい", "崩れ", "直っていない", "解決していない"]):
        facts.append("symptom_surface_described")
    if any(marker in raw for marker in ["別の箇所", "別の件", "また依頼したい", "また別", "不具合が見つかった"]):
        facts.append("new_issue_followup_present")
    if "API Route" in raw:
        facts.append("api_route_context_present")
    if "メールが送れなく" in raw or ("メール" in raw and "送れ" in raw):
        facts.append("mail_send_issue_present")
    if "問題なく動いています" in raw or "問題なく動いてる" in raw:
        facts.append("previous_fix_stable_present")
    if has_discount_probe(raw):
        facts.append("discount_probe_present")
    if scenario in {"design_maintenance_request", "out_of_scope_general_question", "new_feature_request"}:
        facts.append("scope_boundary_question_present")
    if scenario in {"favorite_and_discount", "repeat_handoff_request", "future_doc_preference"}:
        facts.append("positive_repeat_context_present")
    return facts


def build_primary_concern(source: dict, scenario: str, facts_known: list[str]) -> str:
    raw = source.get("raw_message", "")

    if scenario == "refund_request":
        return "返金希望と追加費用がかかるかを知りたい"
    if scenario == "price_complaint":
        return "同じ不具合でまた費用がかかるのか不安"
    if scenario == "same_symptom_recur":
        return "前回と同じ症状が再発したので続きとして見てもらえるか知りたい"
    if scenario == "similar_but_not_same":
        return "似たエラーが前回と同じ原因か知りたい"
    if scenario == "closed_materials_check":
        return "ログやスクショを送れば前回の修正と関係があるか確認してもらえるか知りたい"
    if scenario == "closed_zip_fix_return":
        return "ZIPでコードを送れば修正して返してもらえるか知りたい"
    if scenario == "closed_external_large_share":
        return "大容量コードを外部共有で送ってよいか知りたい"
    if scenario == "closed_secret_send_question":
        return ".env や Stripe キーの値を送った方がよいか知りたい"
    if scenario == "closed_free_followup_price":
        return "前回の続きなら無料で見てもらえるのか、また15,000円かかるのか不安"
    if scenario == "closed_pre_estimate_cause_check":
        return "新規見積り前に原因だけ先に見てもらえるか知りたい"
    if scenario == "closed_technical_followup_question":
        return "クローズ後に前回修正の技術的な意図を確認できるか知りたい"
    if scenario == "closed_third_party_scope_concern":
        return "第三者の指摘が前回の修正範囲に含まれるか知りたい"
    if scenario == "closed_next_consult_path":
        return "クローズ後に別の決済エラーを相談する場合、先にメッセージで症状を送るのか購入後に相談するのか知りたい"
    if scenario == "new_issue_repeat_client":
        if "api_route_context_present" in facts_known and "mail_send_issue_present" in facts_known:
            return "API Route からメールが送れない件もお願いできるか知りたい"
        return "別件をまた依頼できるか知りたい"
    if scenario == "referral_and_soft_new_issue":
        return "紹介してよいかと、メルマガ配信機能の件を後日相談できるか知りたい"
    if scenario == "api_version_notice_question":
        return "StripeのAPIバージョン通知が前回の修正と関係あるか、放置でよいのか判断したい"
    if scenario == "dashboard_login_issue":
        return "Stripeの管理画面にログインできない件が、このサービスの範囲か知りたい"
    if scenario == "mode_toggle_reminder":
        return "前回案内したテストモードと本番モードの見方をすぐ思い出したい"
    if scenario == "webhook_secret_rotation_followup":
        return "APIキーの切り替え後にWebhook側だけ設定が残っていないか確認したい"
    if scenario == "repeat_bugfix_price_check":
        return "別件の依頼がまた15,000円か知りたい"
    if scenario == "self_edit_regression":
        return "自分で触ったあとに戻った症状をどう進めるか知りたい"
    if scenario == "new_feature_request":
        return "新しい機能追加を頼めるか知りたい"
    if scenario == "price_discount_request":
        if "new_issue_followup_present" in facts_known:
            return "別の不具合を見てもらうときに割引があるかと、今回の見積り入口を知りたい"
        return "次回以降の値下げ可否を知りたい"
    if scenario == "same_ticket_scope_question":
        return "この範囲に入るか知りたい"
    if scenario == "repeat_handoff_request":
        return "別フローの引き継ぎ整理を相談したい"
    if scenario == "memo_addendum_request":
        return "前回メモへの追記相談をしたい"
    if scenario == "favorite_and_discount":
        return "次回相談と割引の有無を知りたい"
    if scenario == "recur_uncertainty":
        return "前回修正で十分だったか不安なので見てほしい"
    if raw:
        return shared.summarize_raw_message(raw)
    return "クローズ後の再相談をどう進めるか知りたい"


def build_hard_constraints(scenario: str, grounding: dict) -> dict:
    return {
        "service_id": grounding.get("service_id"),
        "public_service_only": bool(grounding.get("public_service")),
        "answer_before_procedure": True,
        "ask_only_if_blocking": True,
        "closed_room_boundary": True,
        "same_cause_scope_rule": grounding.get("scope_unit") == "same_cause_and_same_flow_and_same_endpoint",
        "no_direct_reopen": True,
    }


def build_response_decision_plan(source: dict, scenario: str, contract: dict) -> dict:
    raw = source.get("raw_message", "")
    facts_known = extract_facts_known(raw, scenario)
    primary_id = contract["primary_question_id"]
    answer_map = contract["answer_map"]
    primary = next(item for item in answer_map if item["question_id"] == primary_id)
    blocking_missing_facts: list[str] = []
    direct_answer_line = primary["answer_brief"]

    if primary["disposition"] in {"answer_now", "decline"}:
        response_order = ["opening", "direct_answer", "answer_detail"]
    else:
        response_order = ["opening", "direct_answer", "answer_detail", "ask", "next_action"]

    if scenario == "repeat_handoff_request":
        blocking_missing_facts = ["target_flow_scope"]
        direct_answer_line = "別のフローの整理として相談できます。"
    elif scenario == "api_version_notice_question":
        blocking_missing_facts = ["notice_text"]
        direct_answer_line = "放っておいて大丈夫とはまだ言い切れません。まず通知内容を見て、前回の修正に関係しているかを確認します。"
    elif scenario == "dashboard_login_issue":
        direct_answer_line = "これはコード修正というより、Stripeアカウント側のログインや権限の話の可能性が高く、このサービスでそのまま確認する内容ではなさそうです。"
        response_order = ["opening", "direct_answer", "answer_detail"]
    elif scenario == "referral_and_soft_new_issue":
        direct_answer_line = "ご紹介いただけるのはありがたいです。ありがとうございます。"
        response_order = ["opening", "direct_answer", "answer_detail"]
    elif scenario == "mode_toggle_reminder":
        direct_answer_line = "テスト/本番の確認は、Stripeダッシュボード左上のアカウント名付近にある「サンドボックス」表示のところです。"
        response_order = ["opening", "direct_answer", "answer_detail"]
    elif scenario == "webhook_secret_rotation_followup":
        direct_answer_line = "その場合は、Webhook側で使っている署名シークレットの見直しが先です。"
        response_order = ["opening", "direct_answer", "answer_detail"]
    elif scenario == "memo_addendum_request":
        blocking_missing_facts = ["blocked_sections"]
        direct_answer_line = "追加で詳しくする相談はできます。"
    elif scenario == "same_ticket_scope_question":
        blocking_missing_facts = ["extra_issue_details"]
        direct_answer_line = "この範囲に入るかは、まず前回と同じ原因かどうかを確認してからお返しします。"
    elif scenario == "refund_request":
        blocking_missing_facts = ["current_symptom"]
        direct_answer_line = "返金可否はここで断定できません。トークルームは閉じているため、この場でキャンセルや返金手続きを進めるとは言えません。まず前回の修正と今回の再発がつながっているか確認します。"
    elif scenario == "memo_rewrite":
        blocking_missing_facts = ["blocked_sections"]
        response_order = ["opening", "direct_answer", "answer_detail", "ask", "next_action"]
    elif scenario == "new_issue_repeat_client":
        blocking_missing_facts = ["current_symptom"]
        if any(marker in raw.lower() for marker in ["webhook"]) and any(
            marker in raw for marker in ["届かなく", "届いていない", "到達していない"]
        ):
            direct_answer_line = "前回とは別の内容でも、今の症状であれば見積りできます。"
        else:
            direct_answer_line = "はい、見積りできます。"
        response_order = ["opening", "direct_answer", "ask", "next_action"]
    elif scenario == "repeat_bugfix_price_check":
        blocking_missing_facts = ["current_symptom"]
        direct_answer_line = "前回とは別の不具合として新規で見る場合は、基本は15,000円です。内容を確認して、見積り提案をお送りします。"
        response_order = ["opening", "direct_answer", "answer_detail", "ask", "next_action"]
    elif scenario == "self_edit_regression":
        blocking_missing_facts = ["edited_area"]
        direct_answer_line = "はい、一度見ます。前回の修正が戻ったのか、今回触った部分の影響かをまず切り分けます。"
    elif scenario == "new_flow_plus_discount":
        blocking_missing_facts = ["target_flow_and_note"]
        direct_answer_line = "別のフローも含めて確認できるかは、まず今回見たい範囲を確認してからお返しします。"
        response_order = ["opening", "direct_answer", "answer_detail", "ask", "next_action"]
    elif scenario == "price_discount_request":
        if "new_issue_followup_present" in facts_known:
            blocking_missing_facts = ["current_symptom"]
            direct_answer_line = "割引前提でのご案内はしておらず、この不具合修正サービスは15,000円固定です。今回の内容を見て見積りをお返しすることはできます。"
            response_order = ["opening", "direct_answer", "answer_detail", "ask", "next_action"]
    elif scenario == "similar_but_not_same":
        blocking_missing_facts = ["current_symptom"]
        direct_answer_line = "トークルームは閉じていますが、まずこのメッセージ上でエラー内容を見て、前回の修正とつながるか確認します。"
    elif scenario == "closed_materials_check":
        blocking_missing_facts = ["log_or_screenshot"]
        direct_answer_line = "はい、ログやスクショで、前回の修正と関係があるかをこのメッセージ上で確認します。"
    elif scenario == "closed_zip_fix_return":
        blocking_missing_facts = ["relevant_files_or_symptom"]
        direct_answer_line = "閉じたトークルームの続きとして、このままコード一式を受け取って修正済みファイルを返すことはできません。"
    elif scenario == "closed_external_large_share":
        direct_answer_line = "申し訳ありませんが、Google Drive などの外部共有は使っていません。"
        response_order = ["opening", "direct_answer", "answer_detail"]
    elif scenario == "closed_secret_send_question":
        direct_answer_line = ".env や Stripe キーの値は送らないでください。値は扱いません。"
        response_order = ["opening", "direct_answer", "answer_detail"]
    elif scenario == "closed_free_followup_price":
        blocking_missing_facts = ["current_error_or_log"]
        direct_answer_line = "まずは、今のエラーが前回の修正とつながる症状かを確認します。確認しないまま、通常料金の新規依頼として進めることはしません。"
    elif scenario == "closed_pre_estimate_cause_check":
        blocking_missing_facts = ["symptom_summary"]
        direct_answer_line = "見積り前の段階で、コードを見て原因調査まで進めることはしていません。"
    elif scenario == "closed_technical_followup_question":
        blocking_missing_facts = ["relevant_code_excerpt"]
        direct_answer_line = "トークルームは閉じていますが、考え方の確認であれば、このメッセージ上で確認できます。"
    elif scenario == "closed_third_party_scope_concern":
        blocking_missing_facts = ["third_party_comment"]
        if "問題ない" in raw or "予防的" in raw:
            direct_answer_line = "現時点で問題が出ていない予防的な修正を前回分として扱えるかは、指摘内容を確認してからでないとまだ判断できません。"
        else:
            direct_answer_line = "元のお値段の中で直せるかは、指摘内容を確認してからでないとまだ判断できません。"
    elif scenario == "closed_next_consult_path":
        blocking_missing_facts = ["current_symptom"]
        direct_answer_line = "まずはこのメッセージ上で症状の概要を送ってください。内容を見て、見積り提案に進むかをご案内します。"
        response_order = ["opening", "direct_answer", "ask", "next_action"]
    elif scenario == "price_complaint":
        blocking_missing_facts = ["current_symptom"]
        direct_answer_line = "追加でまた15,000円と決まっているわけではありません。いまの症状を見てから、前の件とのつながりを確認します。"
    elif scenario == "same_symptom_recur":
        blocking_missing_facts = ["current_symptom"]
        if any(marker in raw for marker in ["お金を払", "払って", "費用"]):
            direct_answer_line = "すぐに追加費用が必要と決まっているわけではありません。まず今の症状を見て、同じ原因かを確認します。"
        else:
            direct_answer_line = "前回と同じ原因かどうかは、まず今の症状を見てからお返しします。"
    elif scenario == "recur_uncertainty":
        blocking_missing_facts = ["current_frequency_or_display"]
        direct_answer_line = "前回の修正でカバーしきれていたかは、今回の状況を見てからお返しします。"
    elif scenario == "feedback_for_next_time":
        direct_answer_line = "修正自体は問題なかったとのこと、ありがとうございます。次回は、もう少し噛み砕いた説明になるよう意識します。"
    elif scenario == "generic_closed":
        response_order = ["opening", "direct_answer", "answer_detail", "next_action"]

    return {
        "primary_question_id": contract["primary_question_id"],
        "primary_concern": build_primary_concern(source, scenario, facts_known),
        "buyer_emotion": infer_buyer_emotion(raw),
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
        "src": source.get("route", "message"),
        "state": "closed",
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
            "empathy_first": source.get("emotional_tone") in {"anxious", "mixed", "frustrated", "complaint_like"},
            "reply_skeleton": "estimate_followup",
        },
    }

    if scenario == "quality_feedback_manual":
        case["reply_contract"] = {
            "primary_question_id": "q1",
            "explicit_questions": [
                {"id": "q1", "text": "次回は検証手順書ももらえるか", "priority": "primary"},
                {"id": "q2", "text": "前回分に追加で検証手順書だけ作れるか", "priority": "secondary"},
            ],
            "answer_map": [
                {
                    "question_id": "q1",
                    "disposition": "answer_now",
                    "answer_brief": "次回は、検証の手順も含めてお渡しします。",
                },
                {
                    "question_id": "q2",
                    "disposition": "answer_after_check",
                    "answer_brief": "前回分の追加作成はできます。",
                    "hold_reason": "トークルームがクローズしているため、そのまま追記ではなく改めて依頼の形に戻します。",
                    "revisit_trigger": "必要な内容を受領したあとに、どの形で進めるかをお伝えします。",
                },
            ],
            "ask_map": [],
            "required_moves": ["react_briefly_first", "answer_directly_now", "defer_with_reason", "commit_next_update_time"],
        }
        return case

    if scenario == "favorite_and_discount":
        case["reply_contract"] = {
            "primary_question_id": "q1",
            "explicit_questions": [
                {"id": "q1", "text": "お気に入りに入れてよいか", "priority": "primary"},
                {"id": "q2", "text": "パッケージ割引はあるか", "priority": "secondary"},
            ],
            "answer_map": [
                {
                    "question_id": "q1",
                    "disposition": "answer_now",
                    "answer_brief": "はい、お気に入りに入れてもらって大丈夫です。次回また必要になった時に見つけやすい形で問題ありません。",
                },
                {
                    "question_id": "q2",
                    "disposition": "answer_now",
                    "answer_brief": "複数件まとめたパッケージ割引は設けていません。",
                },
            ],
            "ask_map": [],
            "required_moves": ["react_briefly_first", "answer_directly_now"],
        }
        return case

    if scenario == "api_version_notice_question":
        case["reply_contract"] = {
            "primary_question_id": "q1",
            "explicit_questions": [
                {"id": "q1", "text": "前回の修正と関係あるか", "priority": "primary"},
                {"id": "q2", "text": "放っておいても大丈夫か", "priority": "secondary"},
            ],
            "answer_map": [
                {
                    "question_id": "q1",
                    "disposition": "answer_after_check",
                    "answer_brief": "放っておいて大丈夫とはまだ言い切れません。まず通知内容を見て、前回の修正に関係しているかを確認します。",
                    "hold_reason": "前回のトークルームは閉じていますが、通知の文面が分かれば前回触れた箇所とのつながりを切りやすくなります。",
                    "revisit_trigger": "通知内容を受領したあとに、どこまで気にするべきかをお返しします。",
                },
            ],
            "ask_map": [
                {
                    "id": "a1",
                    "question_ids": ["q1", "q2"],
                    "ask_text": "通知メールの文面か、APIバージョンが出ている箇所をそのまま送ってください。",
                    "why_needed": "前回の修正との関係と、急ぎで対応が必要かを判断するため",
                }
            ],
            "required_moves": ["react_briefly_first", "defer_with_reason", "request_minimum_evidence", "commit_next_update_time"],
        }
        return case

    if scenario == "dashboard_login_issue":
        case["reply_contract"] = {
            "primary_question_id": "q1",
            "explicit_questions": [
                {"id": "q1", "text": "このサービスで見てもらえるか", "priority": "primary"},
                {"id": "q2", "text": "まず何を確認すればよいか", "priority": "secondary"},
            ],
            "answer_map": [
                {
                    "question_id": "q1",
                    "disposition": "decline",
                    "answer_brief": "これはコード修正というより、Stripeアカウント側のログインや権限の話の可能性が高く、このサービスでそのまま確認する内容ではなさそうです。",
                },
                {
                    "question_id": "q2",
                    "disposition": "answer_now",
                    "answer_brief": "まずは、パスワード再設定、二段階認証、チーム権限の状態を確認してみてください。",
                },
            ],
            "ask_map": [],
            "required_moves": ["react_briefly_first", "answer_directly_now"],
        }
        return case

    if scenario == "feedback_for_next_time":
        case["reply_contract"] = {
            "primary_question_id": "q1",
            "explicit_questions": [
                {"id": "q1", "text": "次回はもう少し噛み砕いた説明にできるか", "priority": "primary"},
            ],
            "answer_map": [
                {
                    "question_id": "q1",
                    "disposition": "answer_now",
                    "answer_brief": "修正自体は問題なかったとのこと、ありがとうございます。次回は、もう少し噛み砕いた説明になるよう意識します。",
                },
            ],
            "ask_map": [],
            "required_moves": ["react_briefly_first", "answer_directly_now"],
        }
        return case

    if scenario == "same_ticket_scope_question":
        case["reply_contract"] = {
            "primary_question_id": "q1",
            "explicit_questions": [
                {"id": "q1", "text": "今回の 15,000円 の範囲内か", "priority": "primary"},
            ],
            "answer_map": [
                {
                    "question_id": "q1",
                    "disposition": "answer_after_check",
                    "answer_brief": "この範囲に入るかは、まず前回の続きとして同じ原因かを確認します。そのうえでお返しします。",
                    "hold_reason": "トークルームは閉じているため、追加の1点でも前回と同じ話かを先に見ます。",
                    "revisit_trigger": "追加で出ている箇所を受領したあとに、この範囲で扱えるかをお返しします。",
                },
            ],
            "ask_map": [
                {
                    "id": "a1",
                    "question_ids": ["q1"],
                    "ask_text": "今回追加で出ているエラー箇所が分かれば、そのまま送ってください。",
                    "why_needed": "前回の修正とつながる内容かを確認するため",
                }
            ],
            "required_moves": ["react_briefly_first", "defer_with_reason", "request_minimum_evidence", "commit_next_update_time"],
        }
        return case

    if scenario == "repeat_handoff_request":
        case["reply_contract"] = {
            "primary_question_id": "q1",
            "explicit_questions": [
                {"id": "q1", "text": "そのまま購入でよいか", "priority": "primary"},
            ],
            "answer_map": [
                {
                    "question_id": "q1",
                    "disposition": "answer_after_check",
                    "answer_brief": "別のフローの整理として相談できます。ただ、そのまま購入ではなく、まず今回見たい内容を確認します。",
                    "hold_reason": "前回のトークルームは閉じているため、今回見たい範囲を確認してから案内します。",
                    "revisit_trigger": "対象フローを受領したあとに、今回の入口をお返しします。",
                },
            ],
            "ask_map": [
                {
                    "id": "a1",
                    "question_ids": ["q1"],
                    "ask_text": "パスワード再発行フローのどこまで見たいかを、そのまま送ってください。",
                    "why_needed": "今回の対象範囲を先にそろえるため",
                }
            ],
            "required_moves": ["react_briefly_first", "defer_with_reason", "request_minimum_evidence", "commit_next_update_time"],
        }
        return case

    if scenario == "memo_addendum_request":
        case["reply_contract"] = {
            "primary_question_id": "q1",
            "explicit_questions": [
                {"id": "q1", "text": "追加で追記してもらえるか", "priority": "primary"},
            ],
            "answer_map": [
                {
                    "question_id": "q1",
                    "disposition": "answer_after_check",
                    "answer_brief": "追記の相談はできます。ただ、このトークルームにそのまま追記する前提ではなく、必要な追記範囲を見て案内します。",
                    "hold_reason": "前回のトークルームは閉じているため、どこまで補足が必要かを見てから案内します。",
                    "revisit_trigger": "止まった箇所を受領したあとに、どの形で進めるのがよいかお返しします。",
                },
            ],
            "ask_map": [
                {
                    "id": "a1",
                    "question_ids": ["q1"],
                    "ask_text": "止まった箇所か、補足したいDBまわりの部分を1〜2点だけ送ってください。",
                    "why_needed": "補足で足りるか、追記が必要かを切るため",
                }
            ],
            "required_moves": ["react_briefly_first", "defer_with_reason", "request_minimum_evidence", "commit_next_update_time"],
        }
        return case

    if scenario == "future_doc_preference":
        case["reply_contract"] = {
            "primary_question_id": "q1",
            "explicit_questions": [
                {"id": "q1", "text": "次回は説明を厚くできるか", "priority": "primary"},
            ],
            "answer_map": [
                {
                    "question_id": "q1",
                    "disposition": "answer_now",
                    "answer_brief": "はい、次回のご依頼時に最初に希望としてもらえれば、その前提で案内できます。",
                },
            ],
            "ask_map": [],
            "required_moves": ["react_briefly_first", "answer_directly_now"],
        }
        return case

    if scenario == "design_maintenance_request":
        case["reply_contract"] = {
            "primary_question_id": "q1",
            "explicit_questions": [
                {"id": "q1", "text": "CSS変更や保守を受けているか", "priority": "primary"},
            ],
            "answer_map": [
                {
                    "question_id": "q1",
                    "disposition": "decline",
                    "answer_brief": "CSSの変更や月額の保守対応は、この不具合修正サービスでは受けていません。",
                },
            ],
            "ask_map": [],
            "required_moves": ["react_briefly_first", "answer_directly_now"],
        }
        return case

    if scenario == "out_of_scope_general_question":
        case["reply_contract"] = {
            "primary_question_id": "q1",
            "explicit_questions": [
                {"id": "q1", "text": "Stripeの手数料を下げる方法を相談できるか", "priority": "primary"},
            ],
            "answer_map": [
                {
                    "question_id": "q1",
                    "disposition": "decline",
                    "answer_brief": "Stripeの手数料を下げる方法のようなご相談は、今回の対応範囲外のためこちらで正確なご案内はしていません。不具合でまたお困りのときは、いつでもご連絡ください。",
                },
            ],
            "ask_map": [],
            "required_moves": ["react_briefly_first", "answer_directly_now"],
        }
        return case

    if scenario == "followup_test_howto":
        case["reply_contract"] = {
            "primary_question_id": "q1",
            "explicit_questions": [
                {"id": "q1", "text": "テスト環境がない場合どう確認すればよいか", "priority": "primary"},
            ],
            "answer_map": [
                {
                    "question_id": "q1",
                    "disposition": "answer_now",
                    "answer_brief": "いきなり本番だけで広く試すより、確認したい操作を絞って順に見る形が安全です。次回必要なら、その前提でも確認手順はお渡しできます。",
                },
            ],
            "ask_map": [],
            "required_moves": ["react_briefly_first", "answer_directly_now"],
        }
        return case

    if scenario == "repeat_bugfix_price_check":
        case["reply_contract"] = {
            "primary_question_id": "q1",
            "explicit_questions": [
                {"id": "q1", "text": "新規でお願いする場合また15,000円か", "priority": "primary"},
            ],
            "answer_map": [
                {
                    "question_id": "q1",
                    "disposition": "answer_now",
                    "answer_brief": "前回とは別の不具合として新規で見る場合は、基本は15,000円です。内容を確認して、見積り提案をお送りします。",
                },
            ],
            "ask_map": [
                {
                    "id": "a1",
                    "question_ids": ["q1"],
                    "ask_text": "更新処理で起きている症状が分かれば、そのまま送ってください。",
                    "why_needed": "今回の入口を先にそろえるため",
                }
            ],
            "required_moves": ["react_briefly_first", "answer_directly_now", "request_minimum_evidence", "commit_next_update_time"],
        }
        return case

    if scenario == "price_discount_request":
        has_new_issue = any(marker in raw for marker in ["別の箇所", "別の件", "また依頼したい", "また別", "不具合が見つかった", "別の不具合"])
        case["reply_contract"] = {
            "primary_question_id": "q1",
            "explicit_questions": [
                {"id": "q1", "text": "次回以降に価格を下げられるか", "priority": "primary"},
                *([{"id": "q2", "text": "今回の内容も見積りできるか", "priority": "secondary"}] if has_new_issue else []),
            ],
            "answer_map": [
                {
                    "question_id": "q1",
                    "disposition": "answer_now",
                    "answer_brief": "次回以降も、内容を見て 5,000円 や 10,000円 に下げる形では受けていません。この不具合修正サービスは 15,000円 固定です。",
                },
                *(
                    [
                        {
                            "question_id": "q2",
                            "disposition": "answer_now",
                            "answer_brief": "今回の内容を見て、見積りをお返しすることはできます。",
                        }
                    ]
                    if has_new_issue
                    else []
                ),
            ],
            "ask_map": (
                [
                    {
                        "id": "a1",
                        "question_ids": ["q2"],
                        "ask_text": "今回見たい不具合の内容をそのまま送ってください。",
                        "why_needed": "今回の見積り入口をそろえるため",
                    }
                ]
                if has_new_issue
                else []
            ),
            "required_moves": ["react_briefly_first", "answer_directly_now"]
            + (["request_minimum_evidence", "commit_next_update_time"] if has_new_issue else []),
        }
        return case

    if scenario == "refund_request":
        case["reply_contract"] = {
            "primary_question_id": "q1",
            "explicit_questions": [
                {"id": "q1", "text": "またお金がかかるのか / 返金になるのか", "priority": "primary"},
            ],
            "answer_map": [
                {
                    "question_id": "q1",
                    "disposition": "answer_after_check",
                    "answer_brief": "またお金がかかるのではというご不安はもっともです。まず前回と同じ原因かを優先して確認します。",
                    "hold_reason": "前回のトークルームは閉じているため、同じ話かどうかで案内が変わる前にまず今回の状況を見ます。",
                    "revisit_trigger": "症状を受領したあとに、今回どう進めるかをお伝えします。",
                },
            ],
            "ask_map": [
                {
                    "id": "a1",
                    "question_ids": ["q1"],
                    "ask_text": "今の症状が分かる画面があれば送ってください。難しければ、分かる範囲の状況だけでも大丈夫です。",
                    "why_needed": "前回とのつながりが強いかを先に見るため",
                }
            ],
            "required_moves": ["react_briefly_first", "defer_with_reason", "request_minimum_evidence", "commit_next_update_time"],
        }
        return case

    if scenario == "memo_rewrite":
        case["reply_contract"] = {
            "primary_question_id": "q1",
            "explicit_questions": [
                {"id": "q1", "text": "メモの書き直しをお願いできるか", "priority": "primary"},
                {"id": "q2", "text": "追加料金がかかるか", "priority": "secondary"},
            ],
            "answer_map": [
                {
                    "question_id": "q1",
                    "disposition": "answer_now",
                    "answer_brief": "書き直し自体はできます。",
                },
                {
                    "question_id": "q2",
                    "disposition": "answer_after_check",
                    "answer_brief": "料金とどの形で進めるかは、補足で足りるか書き直しになるかで変わります。",
                    "hold_reason": "トークルームがクローズしているため、そのまま無料追記では進めません。",
                    "revisit_trigger": "止まった箇所を受領したあとに、どの形で進めるのがよいかお返しします。",
                },
            ],
            "ask_map": [
                {
                    "id": "a1",
                    "question_ids": ["q1", "q2"],
                    "ask_text": "新しく来た開発者の方がどの部分で止まったかを1〜2点だけそのまま送ってください。",
                    "why_needed": "補足で足りるか、整理し直す書き直しかを切るため",
                }
            ],
            "required_moves": ["react_briefly_first", "answer_directly_now", "defer_with_reason", "request_minimum_evidence", "commit_next_update_time"],
        }
        return case

    if scenario == "closed_next_consult_path":
        case["reply_contract"] = {
            "primary_question_id": "q1",
            "explicit_questions": [
                {"id": "q1", "text": "次の相談は先にメッセージで症状を送るのか、新しく購入してから相談するのか", "priority": "primary"},
            ],
            "answer_map": [
                {
                    "question_id": "q1",
                    "disposition": "answer_after_check",
                    "answer_brief": "まずはこのメッセージ上で症状の概要を送ってください。内容を見て、見積り提案に進むかをご案内します。",
                    "hold_reason": "トークルームは閉じているため、このまま原因調査や修正作業には入りません。",
                    "revisit_trigger": "前回の修正と関係がありそうか、別の不具合として見積り提案に進む内容かをお返しします。",
                },
            ],
            "ask_map": [
                {
                    "id": "a1",
                    "question_ids": ["q1"],
                    "ask_text": "今出ている症状の概要やエラー内容を送ってください。",
                    "why_needed": "見積り前に返せる入口の見立てを作るため",
                }
            ],
            "required_moves": ["react_briefly_first", "defer_with_reason", "request_minimum_evidence", "commit_next_update_time"],
        }
        return case

    if scenario == "new_issue_repeat_client":
        webhook_issue = "webhook" in raw.lower() and any(marker in raw for marker in ["届かなく", "届いていない", "到達していない"])
        case["reply_contract"] = {
            "primary_question_id": "q1",
            "explicit_questions": [
                {"id": "q1", "text": "新しく依頼できるか", "priority": "primary"},
            ],
            "answer_map": [
                {
                    "question_id": "q1",
                    "disposition": "answer_now",
                    "answer_brief": "はい、見積りできます。",
                },
            ],
            "ask_map": [
                {
                    "id": "a1",
                    "question_ids": ["q1"],
                    "ask_text": (
                        "Webhook の送信結果が分かる表示や、エンドポイント側の反応があればそのまま送ってください。"
                        if webhook_issue
                        else "今出ている症状か、見たい流れをそのまま送ってください。"
                    ),
                    "why_needed": "新しい内容の入口を切るため",
                }
            ],
            "required_moves": ["react_briefly_first", "answer_directly_now", "request_minimum_evidence", "commit_next_update_time"],
        }
        return case

    if scenario == "referral_and_soft_new_issue":
        case["reply_contract"] = {
            "primary_question_id": "q1",
            "explicit_questions": [
                {"id": "q1", "text": "知り合いを紹介してよいか", "priority": "primary"},
                {"id": "q2", "text": "メルマガ配信機能の件も後日相談できるか", "priority": "secondary"},
            ],
            "answer_map": [
                {
                    "question_id": "q1",
                    "disposition": "answer_now",
                    "answer_brief": "ご紹介いただけるのはありがたいです。ありがとうございます。",
                },
                {
                    "question_id": "q2",
                    "disposition": "answer_now",
                    "answer_brief": "メルマガ配信機能の件も、必要なタイミングで新しい相談として見積りできます。",
                },
            ],
            "ask_map": [],
            "required_moves": ["react_briefly_first", "answer_directly_now"],
        }
        return case

    if scenario == "mode_toggle_reminder":
        case["reply_contract"] = {
            "primary_question_id": "q1",
            "explicit_questions": [{"id": "q1", "text": "Stripeのテストモードと本番モードの切り替え場所はどこか", "priority": "primary"}],
            "answer_map": [
                {
                    "question_id": "q1",
                    "disposition": "answer_now",
                    "answer_brief": "テスト/本番の確認は、Stripeダッシュボード左上のアカウント名付近にある「サンドボックス」表示のところです。",
                }
            ],
            "ask_map": [],
            "required_moves": ["react_briefly_first", "answer_directly_now"],
        }
        return case

    if scenario == "webhook_secret_rotation_followup":
        case["reply_contract"] = {
            "primary_question_id": "q1",
            "explicit_questions": [{"id": "q1", "text": "どこを直せばよいか", "priority": "primary"}],
            "answer_map": [
                {
                    "question_id": "q1",
                    "disposition": "answer_now",
                    "answer_brief": "その場合は、Webhook側で使っている署名シークレットの見直しが先です。",
                }
            ],
            "ask_map": [],
            "required_moves": ["react_briefly_first", "answer_directly_now"],
        }
        return case

    if scenario == "self_edit_regression":
        case["reply_contract"] = {
            "primary_question_id": "q1",
            "explicit_questions": [
                {"id": "q1", "text": "どうすればいいか", "priority": "primary"},
            ],
            "answer_map": [
                {
                    "question_id": "q1",
                    "disposition": "answer_after_check",
                    "answer_brief": "はい、一度見ます。前回の修正が戻ったのか、今回触った部分の影響かをまず切り分けます。",
                    "hold_reason": "トークルームは閉じているため、まず今どこで止まっているかを確認します。",
                    "revisit_trigger": "変更した箇所を受領したあとに、前回修正との関係をお返しします。",
                },
            ],
            "ask_map": [
                {
                    "id": "a1",
                    "question_ids": ["q1"],
                    "ask_text": "PayPay対応で触った箇所か、今どこで止まっているかを1〜2点だけ送ってください。",
                    "why_needed": "前回修正が戻ったのか、別の変更かを切るため",
                }
            ],
            "required_moves": ["react_briefly_first", "defer_with_reason", "request_minimum_evidence", "commit_next_update_time"],
        }
        return case

    if scenario == "new_feature_request":
        raw = source.get("raw_message", "")
        answer_map = [
            {
                "question_id": "q1",
                "disposition": "decline",
                "answer_brief": "新しい機能追加は、今回の不具合修正の範囲ではありません。",
            },
        ]
        if "Invoice" in raw or "請求書" in raw:
            answer_map.append(
                {
                    "question_id": "q2",
                    "disposition": "answer_now",
                    "answer_brief": "いま公開しているこのサービスでは、既存不具合の修正を前提にしています。",
                }
            )
        case["reply_contract"] = {
            "primary_question_id": "q1",
            "explicit_questions": [
                {"id": "q1", "text": "新しい機能追加をお願いできるか", "priority": "primary"},
            ],
            "answer_map": answer_map,
            "ask_map": [],
            "required_moves": ["react_briefly_first", "answer_directly_now"],
        }
        return case

    if scenario == "new_flow_plus_discount":
        case["reply_contract"] = {
            "primary_question_id": "q1",
            "explicit_questions": [
                {"id": "q1", "text": "もう1フロー整理してもらえるか", "priority": "primary"},
                {"id": "q2", "text": "少し安くならないか", "priority": "secondary"},
                {"id": "q3", "text": "前回メモの気になる箇所も確認してもらえるか", "priority": "secondary"},
            ],
            "answer_map": [
                {
                    "question_id": "q1",
                    "disposition": "answer_after_check",
                    "answer_brief": "トークルームは閉じているので、そのまま前回の続きとして進める前提ではありません。",
                    "hold_reason": "トークルームは閉じているため、新しい1フロー確認が必要な内容かを先に確認します。",
                    "revisit_trigger": "見たい流れを受領したあとに、今回の入口をお返しします。",
                },
                {
                    "question_id": "q2",
                    "disposition": "answer_now",
                    "answer_brief": "価格を先に下げる形では進めません。",
                },
                {
                    "question_id": "q3",
                    "disposition": "answer_now",
                    "answer_brief": "前回メモの気になる1箇所は、今回の入口確認とあわせて見ます。",
                },
            ],
            "ask_map": [
                {
                    "id": "a1",
                    "question_ids": ["q1", "q3"],
                    "ask_text": "今回見たい流れと、前回メモで気になっている箇所を1点ずつそのまま送ってください。",
                    "why_needed": "新規の1フロー確認と、前回メモ補足を分けて判断するため",
                }
            ],
            "required_moves": ["react_briefly_first", "answer_directly_now", "defer_with_reason", "request_minimum_evidence", "commit_next_update_time"],
        }
        return case

    if scenario == "similar_but_not_same":
        case["reply_contract"] = {
            "primary_question_id": "q1",
            "explicit_questions": [
                {"id": "q1", "text": "どうすればいいか", "priority": "primary"},
            ],
            "answer_map": [
                {
                    "question_id": "q1",
                    "disposition": "answer_after_check",
                    "answer_brief": "まず今回の症状と前回のつながりを確認します。",
                    "hold_reason": "トークルームは閉じているため、違うイベントで同じようなエラーでも前回と同じ原因かはまだ未確定です。",
                    "revisit_trigger": "症状を受領したあとに、今回どう進めるかをお伝えします。",
                },
            ],
            "ask_map": [
                {
                    "id": "a1",
                    "question_ids": ["q1"],
                    "ask_text": "今出ているエラー内容か画面スクショを送ってください。",
                    "why_needed": "前回とのつながりが強いかどうかを先に見るため",
                }
            ],
            "required_moves": ["react_briefly_first", "defer_with_reason", "request_minimum_evidence", "commit_next_update_time"],
        }
        return case

    if scenario == "price_complaint":
        case["reply_contract"] = {
            "primary_question_id": "q1",
            "explicit_questions": [
                {"id": "q1", "text": "またお金がかかるのか", "priority": "primary"},
            ],
            "answer_map": [
                {
                    "question_id": "q1",
                    "disposition": "answer_after_check",
                    "answer_brief": "またお金がかかるのではというご不安はもっともです。まず、前回と同じ原因かどうかを確認します。",
                    "hold_reason": "前回のトークルームは閉じているため、同じ話かどうかで案内が変わる前にまず今回の状況を見ます。",
                    "revisit_trigger": "今回の症状を受領したあとに、前回とのつながりが強いかをお返しします。",
                },
            ],
            "ask_map": [
                {
                    "id": "a1",
                    "question_ids": ["q1"],
                    "ask_text": "今の症状が分かる画面があれば送ってください。難しければ、分かる範囲の状況だけでも大丈夫です。",
                    "why_needed": "前回と同じ話かどうかを先に切るため",
                }
            ],
            "required_moves": ["react_briefly_first", "defer_with_reason", "request_minimum_evidence", "commit_next_update_time"],
        }
        return case

    if scenario == "same_symptom_recur":
        case["reply_contract"] = {
            "primary_question_id": "q1",
            "explicit_questions": [
                {"id": "q1", "text": "また見てもらえるか", "priority": "primary"},
            ],
            "answer_map": [
                {
                    "question_id": "q1",
                    "disposition": "answer_after_check",
                    "answer_brief": "まずは前回と同じ原因かどうかを確認します。",
                    "hold_reason": "トークルームは閉じているため、同じ箇所に見えても前回と同じ原因とはまだ断定しません。",
                    "revisit_trigger": "症状を受領したあとに、前回との関係をお返しします。",
                },
            ],
            "ask_map": [
                {
                    "id": "a1",
                    "question_ids": ["q1"],
                    "ask_text": "今の症状が出ている画面スクショと、同じ操作で起きているかを送ってください。",
                    "why_needed": "前回とのつながりが強いかを先に見るため",
                }
            ],
            "required_moves": ["react_briefly_first", "defer_with_reason", "request_minimum_evidence", "commit_next_update_time"],
        }
        return case

    if scenario == "recur_uncertainty":
        case["reply_contract"] = {
            "primary_question_id": "q1",
            "explicit_questions": [
                {"id": "q1", "text": "前回の修正でカバーできていたか不安", "priority": "primary"},
            ],
            "answer_map": [
                {
                    "question_id": "q1",
                    "disposition": "answer_after_check",
                    "answer_brief": "時々決済が通らない状態が残っているとのこと、承知しました。前回の修正範囲でカバーできていたかも含めて確認します。",
                    "hold_reason": "前回のトークルームは閉じているため、新しいご依頼として今回の状況を確認してから進めます。",
                    "revisit_trigger": "症状の状況を受領したあとに、見立てをお返しします。",
                },
            ],
            "ask_map": [
                {
                    "id": "a1",
                    "question_ids": ["q1"],
                    "ask_text": "通らないときの表示や、どのくらいの頻度で起きるかが分かれば送ってください。",
                    "why_needed": "前回と同じ原因が残っているのかを先に見るため",
                }
            ],
            "required_moves": ["react_briefly_first", "defer_with_reason", "request_minimum_evidence", "commit_next_update_time"],
        }
        return case

    if scenario == "closed_materials_check":
        case["reply_contract"] = {
            "primary_question_id": "q1",
            "explicit_questions": [{"id": "q1", "text": "ログやスクショを送れば前回との関係を見てもらえるか", "priority": "primary"}],
            "answer_map": [
                {
                    "question_id": "q1",
                    "disposition": "answer_after_check",
                    "answer_brief": "はい、ログやスクショで、前回の修正と関係があるかをこのメッセージ上で確認します。",
                    "hold_reason": "トークルームは閉じているため、ここで修正作業や修正済みファイルの返却までは進めません。",
                    "revisit_trigger": "確認後、実作業が必要な場合は見積り提案または新規依頼としてご案内します。",
                }
            ],
            "ask_map": [
                {
                    "id": "a1",
                    "question_ids": ["q1"],
                    "ask_text": "ログやスクショを送ってください。",
                    "why_needed": "前回の修正との関係を確認するため",
                }
            ],
            "required_moves": ["react_briefly_first", "defer_with_reason", "request_minimum_evidence", "commit_next_update_time"],
        }
        return case

    if scenario == "closed_zip_fix_return":
        case["reply_contract"] = {
            "primary_question_id": "q1",
            "explicit_questions": [{"id": "q1", "text": "ZIPでコードを送れば修正して返してもらえるか", "priority": "primary"}],
            "answer_map": [
                {
                    "question_id": "q1",
                    "disposition": "answer_after_check",
                    "answer_brief": "閉じたトークルームの続きとして、このままコード一式を受け取って修正済みファイルを返すことはできません。",
                    "hold_reason": "まずはこのメッセージ上で、前回の修正と関係がありそうかを確認します。",
                    "revisit_trigger": "実作業が必要な場合は、見積り提案または新規依頼としてご案内します。",
                }
            ],
            "ask_map": [
                {
                    "id": "a1",
                    "question_ids": ["q1"],
                    "ask_text": "必要であれば、不具合に関係する箇所だけ分かる範囲で送ってください。",
                    "why_needed": "前回の修正との関係を見るため",
                }
            ],
            "required_moves": ["react_briefly_first", "defer_with_reason", "request_minimum_evidence", "commit_next_update_time"],
        }
        return case

    if scenario == "closed_external_large_share":
        case["reply_contract"] = {
            "primary_question_id": "q1",
            "explicit_questions": [{"id": "q1", "text": "Google Drive など外部共有で送ってよいか", "priority": "primary"}],
            "answer_map": [
                {
                    "question_id": "q1",
                    "disposition": "decline",
                    "answer_brief": "申し訳ありませんが、Google Drive などの外部共有は使っていません。",
                },
                {
                    "question_id": "q2",
                    "disposition": "answer_now",
                    "answer_brief": "ファイルはココナラのメッセージ添付で送れる範囲でお願いします。",
                },
            ],
            "ask_map": [],
            "required_moves": ["react_briefly_first", "answer_directly_now"],
        }
        return case

    if scenario == "closed_secret_send_question":
        case["reply_contract"] = {
            "primary_question_id": "q1",
            "explicit_questions": [{"id": "q1", "text": ".env や Stripe キーの値を送ってよいか", "priority": "primary"}],
            "answer_map": [
                {
                    "question_id": "q1",
                    "disposition": "decline",
                    "answer_brief": ".env や Stripe キーの値は送らないでください。値は扱いません。",
                },
                {
                    "question_id": "q2",
                    "disposition": "answer_now",
                    "answer_brief": "確認には、必要なキー名だけ分かれば大丈夫です。",
                },
            ],
            "ask_map": [],
            "required_moves": ["react_briefly_first", "answer_directly_now"],
        }
        return case

    if scenario == "closed_free_followup_price":
        case["reply_contract"] = {
            "primary_question_id": "q1",
            "explicit_questions": [{"id": "q1", "text": "無料対応か、また15,000円かかるのか", "priority": "primary"}],
            "answer_map": [
                {
                    "question_id": "q1",
                    "disposition": "answer_after_check",
                    "answer_brief": "まずは、今のエラーが前回の修正とつながる症状かを確認します。確認しないまま、通常料金の新規依頼として進めることはしません。",
                    "hold_reason": "トークルームは閉じているため、この場でそのまま修正作業に入ることはできません。",
                    "revisit_trigger": "このメッセージ上でできるのは、エラー内容やログ、スクショを見て、前回の修正とつながる内容かを確認するところまでです。",
                }
            ],
            "ask_map": [
                {
                    "id": "a1",
                    "question_ids": ["q1"],
                    "ask_text": "今出ているエラー内容、ログ、または画面スクショを送ってください。",
                    "why_needed": "前回の修正とのつながりを見るため",
                }
            ],
            "required_moves": ["react_briefly_first", "defer_with_reason", "request_minimum_evidence", "commit_next_update_time"],
        }
        return case

    if scenario == "closed_pre_estimate_cause_check":
        case["reply_contract"] = {
            "primary_question_id": "q1",
            "explicit_questions": [{"id": "q1", "text": "新規見積り前に原因だけ先に見てもらえるか", "priority": "primary"}],
            "answer_map": [
                {
                    "question_id": "q1",
                    "disposition": "answer_after_check",
                    "answer_brief": "見積り前の段階で、コードを見て原因調査まで進めることはしていません。",
                    "hold_reason": "ただ、症状の概要やエラー内容をこのメッセージ上で送っていただければ、前回の修正と関係がありそうかの見立てはお返しできます。",
                    "revisit_trigger": "その見立てをもとに、見積り提案に進むかどうかをご判断いただけます。",
                }
            ],
            "ask_map": [
                {
                    "id": "a1",
                    "question_ids": ["q1"],
                    "ask_text": "症状の概要やエラー内容を送ってください。",
                    "why_needed": "見積り前に返せる見立てを作るため",
                }
            ],
            "required_moves": ["react_briefly_first", "defer_with_reason", "request_minimum_evidence", "commit_next_update_time"],
        }
        return case

    if scenario == "closed_technical_followup_question":
        case["reply_contract"] = {
            "primary_question_id": "q1",
            "explicit_questions": [{"id": "q1", "text": "クローズ後に前回修正の技術的な意図を確認できるか", "priority": "primary"}],
            "answer_map": [
                {
                    "question_id": "q1",
                    "disposition": "answer_after_check",
                    "answer_brief": "トークルームは閉じていますが、考え方の確認であれば、このメッセージ上で確認できます。",
                    "hold_reason": "ただ、コードを見直して修正する実作業になる場合は、見積り提案または新規依頼としてご案内します。",
                    "revisit_trigger": "該当箇所を確認して、説明で足りるか実作業が必要かをお返しします。",
                }
            ],
            "ask_map": [
                {
                    "id": "a1",
                    "question_ids": ["q1"],
                    "ask_text": "該当する useEffect 周辺だけ送ってください。値や秘密情報は不要です。",
                    "why_needed": "前回修正の考え方として説明できる範囲かを確認するため",
                }
            ],
            "required_moves": ["react_briefly_first", "defer_with_reason", "request_minimum_evidence", "commit_next_update_time"],
        }
        return case

    if scenario == "closed_third_party_scope_concern":
        case["reply_contract"] = {
            "primary_question_id": "q1",
            "explicit_questions": [{"id": "q1", "text": "第三者の指摘が前回の修正範囲に入るか", "priority": "primary"}],
            "answer_map": [
                {
                    "question_id": "q1",
                    "disposition": "answer_after_check",
                    "answer_brief": "元のお値段の中で直せるかは、指摘内容を確認してからでないとまだ判断できません。",
                    "hold_reason": "トークルームは閉じていますが、まず第三者の方が指摘している内容が、前回の修正とつながる確認か、実作業が必要な新規見積りかを切り分けます。",
                    "revisit_trigger": "指摘内容を見たうえで、前回の補足で済む確認か、新規の実作業になるかをお返しします。",
                }
            ],
            "ask_map": [
                {
                    "id": "a1",
                    "question_ids": ["q1"],
                    "ask_text": "指摘された箇所や、具体的におかしいと言われた内容をそのまま送ってください。",
                    "why_needed": "前回の修正範囲とのつながりを確認するため",
                }
            ],
            "required_moves": ["react_briefly_first", "defer_with_reason", "request_minimum_evidence", "commit_next_update_time"],
        }
        return case

    case["reply_contract"] = {
        "primary_question_id": "q1",
        "explicit_questions": [{"id": "q1", "text": "今回どう進めるか", "priority": "primary"}],
        "answer_map": [
            {
                "question_id": "q1",
                "disposition": "answer_after_check",
                "answer_brief": "トークルームは閉じていますが、まずこのメッセージ上で内容を確認します。",
                "hold_reason": "この場でそのまま修正作業やファイル返却へ進める前提にはしません。",
                "revisit_trigger": "内容を見たうえで、メッセージ上の確認で足りるか、実作業として見積り提案または新規依頼へ戻すかをお伝えします。",
            },
        ],
        "ask_map": [],
        "required_moves": ["react_briefly_first", "defer_with_reason", "commit_next_update_time"],
    }
    return case


def reaction_line(case: dict) -> str:
    scenario = case["scenario"]
    if scenario == "price_complaint":
        return "また費用がかかるのではとご不安な点、確認しました。"
    if scenario == "refund_request":
        return "返金のご希望と、また費用がかかるのではというご不安、確認しました。"
    if scenario == "out_of_scope_general_question":
        return "決済が安定しているとのこと、よかったです。"
    if scenario == "favorite_and_discount":
        return "ご評価ありがとうございます。次回のご相談についても確認しました。"
    if scenario == "feedback_for_next_time":
        return "まず、率直に伝えていただいてありがとうございます。"
    if scenario == "repeat_bugfix_price_check":
        return "前回とは別の内容でまたご相談いただいた件、ありがとうございます。"
    if scenario == "repeat_handoff_request":
        return "前回のメモが役に立ったとのこと、ありがとうございます。"
    if scenario == "memo_addendum_request":
        return "まず内容を確認します。メモの追記についてのご相談、確認しました。"
    if scenario == "future_doc_preference":
        return "次回へのご希望を伝えていただきありがとうございます。"
    if scenario == "design_maintenance_request":
        return "ご相談ありがとうございます。"
    if scenario == "out_of_scope_general_question":
        return "決済が安定しているとのこと、よかったです。"
    if scenario == "followup_test_howto":
        return "確認方法についてのご質問ありがとうございます。"
    if scenario == "price_discount_request":
        return "まず、率直に相談していただいてありがとうございます。"
    temperature_plan = case.get("temperature_plan") or {}
    opening_move = temperature_plan.get("opening_move")
    user_signal = temperature_plan.get("user_signal")
    if opening_move == "action_first":
        if scenario in {"refund_request", "same_symptom_recur", "self_edit_regression"}:
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
    if scenario == "quality_feedback_manual":
        return "前回の検証まわりについてのご連絡、確認しました。"
    if scenario == "refund_request":
        return "前回対応後のご不安と返金のご質問、確認しました。"
    if scenario == "memo_rewrite":
        return "前回メモで伝わりにくかった部分があったとのこと、承知しました。"
    if scenario == "new_issue_repeat_client":
        return "前回とは別の内容とのことなので、まず今回の症状から確認します。"
    if scenario == "closed_next_consult_path":
        return "次の相談の入り口ですね。"
    if scenario == "referral_and_soft_new_issue":
        return "ご紹介のお申し出と、メルマガ配信機能の件、ありがとうございます。"
    if scenario == "dashboard_login_issue":
        return "Stripeの管理画面にログインできない件、確認しました。"
    if scenario == "self_edit_regression":
        if "PayPay" in raw and "Stripe" in raw:
            return "PayPay対応後にStripe側も動かなくなったとのこと、確認しました。"
        return "前回修正後にコードを触ってから変化があった件、確認しました。"
    if scenario == "new_feature_request":
        if "Invoice" in raw or "請求書" in raw:
            return "Invoice機能の追加で詰まっている件、確認しました。"
        return "前回のご利用後に新しい機能追加も検討されている件、確認しました。"
    if scenario == "new_flow_plus_discount":
        return "もう1フロー見たい件と、前回メモの気になる箇所がある件、どちらも確認しました。"
    if scenario == "similar_but_not_same":
        return "前回とは違うイベントで似たエラーが出ているとのこと、確認しました。"
    if scenario == "price_complaint":
        return "前回の件でまたご不便が出ているとのこと、確認しました。"
    if scenario == "same_symptom_recur":
        return "前回と同じような症状がまた出ているとのこと、確認しました。"
    if scenario == "recur_uncertainty":
        return "前回の修正で全部カバーできていたかご不安とのこと、確認しました。"
    return "クローズ後のご連絡、確認しました。"


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
    raw = case.get("raw_message", "")
    if scenario == "same_symptom_recur":
        return "トークルームは閉じていますが、いま出ている画面と同じ操作で起きるかが分かれば、前の件とのつながりを確認できます。"
    if scenario == "price_complaint":
        return "トークルームは閉じていますが、いまの症状が分かれば前の件とのつながりを切りやすくなります。"
    if scenario == "refund_request":
        return "短期間で再発しているとのことなので、まず今の症状を見て前の件とのつながりを確認します。"
    if scenario == "similar_but_not_same":
        if "invoice.payment_failed" in raw:
            return "実作業が必要な場合は、見積り提案または新規依頼としてご案内します。"
        return "実作業が必要な場合は、見積り提案または新規依頼としてご案内します。"
    if scenario == "self_edit_regression":
        if "PayPay" in raw and "Stripe" in raw:
            return "トークルームは閉じていますが、PayPay対応で加えた変更とStripe側の止まり方を確認します。"
        return "トークルームは閉じていますが、触った箇所と前の修正のつながりを確認します。"
    if scenario in {"new_issue_repeat_client", "repeat_bugfix_price_check"}:
        if "webhook" in raw.lower() and any(marker in raw for marker in ["送信は成功", "到達していない", "届かなく", "届いていない"]):
            return "送信は成功しているとのことなので、まず受信側でどこまで届いているかを確認します。"
        return "いまの症状が分かると、見積りをお返ししやすくなります。"
    if scenario == "closed_next_consult_path":
        return "トークルームは閉じているため、コードを見て原因調査や修正作業まで入る場合は、見積り提案または新規依頼として費用の有無を先にご相談します。"
    if scenario == "price_discount_request" and "new_issue_followup_present" in (case.get("response_decision_plan") or {}).get("facts_known", []):
        return "トークルームは閉じているので、今回見たい不具合の内容が分かれば見積りの入口を整えられます。"
    if scenario == "same_ticket_scope_question":
        return "トークルームは閉じていますが、追加で出た箇所が前の件と同じ原因か確認します。"
    if scenario == "repeat_handoff_request":
        return "トークルームは閉じていますが、今回どのフローを整理したいか確認します。"
    if scenario == "memo_addendum_request":
        return "トークルームは閉じていますが、どこで止まっているかを見て補足で足りるか確認します。"
    if scenario == "new_flow_plus_discount":
        return "トークルームは閉じていますが、今回見たい流れと前回メモの気になる点を分けて確認します。"
    if scenario == "recur_uncertainty":
        return "トークルームは閉じていますが、通らない時の出方を見て前の修正とのつながりを確認します。"
    if scenario == "generic_closed":
        return "実作業が必要な場合は、作業前にココナラ上でどう進めるかをご相談します。"
    return None


def draft_opening_anchor(case: dict) -> str:
    scenario = case["scenario"]
    raw = case.get("raw_message", "")
    temperature_plan = case.get("temperature_plan") or {}
    if scenario == "dashboard_login_issue":
        return "Stripeの管理画面にログインできない件、確認しました。"
    if scenario == "mode_toggle_reminder":
        if "previous_fix_stable_present" in (case.get("response_decision_plan") or {}).get("facts_known", []):
            return "前回の件が問題なく動いているとのこと、よかったです。"
        return "テストモードと本番モードの件、確認しました。"
    if scenario == "webhook_secret_rotation_followup":
        return "前回の件が安定していたとのこと、ありがとうございます。"
    if scenario == "closed_materials_check":
        return "まず確認材料として見ます。"
    if scenario == "closed_zip_fix_return":
        return "コード一式を送る件、確認しました。"
    if scenario == "closed_external_large_share":
        return "ファイル容量についてのご相談、確認しました。"
    if scenario == "closed_secret_send_question":
        return "秘密情報の扱いについてのご相談、確認しました。"
    if scenario == "closed_free_followup_price":
        return "前回の修正後から同じようなエラーが残っていて、また費用がかかるのは納得できないとのこと、確認しました。"
    if scenario == "closed_pre_estimate_cause_check":
        return "まず症状の概要から見立てをお返しします。"
    if scenario == "closed_technical_followup_question":
        return "useEffect の依存配列についてのご質問、確認しました。"
    if scenario == "closed_third_party_scope_concern":
        return "第三者の方から指摘があった件、確認しました。"
    if temperature_plan.get("opening_move") == "action_first":
        if scenario == "recur_uncertainty":
            return "まず今の出方から確認します。"
        if scenario in {"refund_request", "price_complaint"}:
            return "まず今回の症状から確認します。"
        if scenario == "same_symptom_recur":
            return "まず今の症状から確認します。"
        if scenario == "similar_but_not_same":
            return "まず今回のイベントから確認します。"
        if scenario == "self_edit_regression":
            return "まず触った箇所から確認します。"
    if scenario == "refund_request":
        return "返金のご希望、確認しました。"
    if scenario == "price_complaint":
        if "納得いかない" in raw:
            return "率直に伝えていただきありがとうございます。納得いかないお気持ち、ごもっともです。"
        return "また費用がかかるのではとご不安な点、確認しました。"
    if scenario == "api_version_notice_question":
        return "StripeからAPIバージョンの通知が来ているとのこと、確認しました。"
    if scenario == "same_symptom_recur":
        return "また同じような症状が出ているとのこと、確認しました。"
    if scenario == "similar_but_not_same":
        return "前回とは違うイベントで似たエラーが出ているとのこと、確認しました。"
    if scenario == "new_issue_repeat_client":
        if "よかった" in raw:
            return "前回の対応がよかったとのこと、ありがとうございます。"
        if "webhook" in raw.lower() and any(marker in raw for marker in ["送信は成功", "到達していない", "届かなく", "届いていない"]):
            if any(marker in raw for marker in ["急ぎ", "今朝から"]):
                return "急ぎの状況とのこと、確認しました。"
            return "Webhook が届かなくなっている件、確認しました。"
        if "API Route" in raw and ("メールが送れなく" in raw or "メール" in raw):
            return "API Routeからメールが送れない件でお困りとのこと、確認しました。"
        return "前回とは別の内容とのことなので、まず今回の症状から確認します。"
    if scenario == "referral_and_soft_new_issue":
        return "本当に助かったとのこと、ありがとうございます。"
    if scenario == "repeat_bugfix_price_check":
        return "前回とは別の内容とのことなので、まず今回の症状から確認します。"
    if scenario == "self_edit_regression":
        raw = case.get("raw_message", "")
        if "PayPay" in raw and "Stripe" in raw and "動かなく" in raw:
            return "Stripeが動かなくなった件、確認しました。"
        return "コードを触ったあとに変化があった件、確認しました。"
    if scenario == "new_feature_request":
        if "Invoice" in raw or "請求書" in raw:
            return "Invoice機能の追加で詰まっている件、確認しました。"
        return "前回のご利用後に新しい機能追加も検討されている件、確認しました。"
    if scenario == "price_discount_request":
        if "new_issue_followup_present" in (case.get("response_decision_plan") or {}).get("facts_known", []):
            return "またご相談いただけてありがたいです。"
        return "率直に相談していただいてありがとうございます。"
    if scenario == "same_ticket_scope_question":
        return "追加で出た箇所も今回に含めてよいか気になっているとのこと、確認しました。"
    if scenario == "repeat_handoff_request":
        return "前回のメモが役に立ったとのこと、ありがとうございます。"
    if scenario == "memo_addendum_request":
        return "メモの追記についてのご相談、確認しました。"
    if scenario == "new_flow_plus_discount":
        return "もう1フロー見たい件と、前回メモの気になる箇所がある件、どちらも確認しました。"
    if scenario == "recur_uncertainty":
        return "前回の修正で全部カバーできていたかご不安とのこと、確認しました。"
    if scenario == "favorite_and_discount":
        return "ご評価ありがとうございます。次回のご相談についても確認しました。"
    if scenario == "feedback_for_next_time":
        return "報告書の件、フィードバックありがとうございます。"
    return reaction_line(case)


def draft_body_paragraphs(case: dict) -> list[str]:
    scenario = case["scenario"]
    contract = case["reply_contract"]
    decision_plan = case.get("response_decision_plan") or {}
    primary_id = contract["primary_question_id"]
    primary = next(item for item in contract["answer_map"] if item["question_id"] == primary_id)
    secondary_now = [item for item in contract["answer_map"] if item["question_id"] != primary_id and item["disposition"] in {"answer_now", "decline"}]
    secondary_after = [
        item for item in contract["answer_map"] if item["question_id"] != primary_id and item["disposition"] == "answer_after_check"
    ]
    ask_map = contract.get("ask_map") or []
    blocking_missing_facts = decision_plan.get("blocking_missing_facts") or []
    direct_answer = with_period(decision_plan.get("direct_answer_line") or primary["answer_brief"])
    focus_line = current_focus_line(case)
    paragraphs: list[str] = []

    if scenario == "closed_materials_check":
        _append_unique(paragraphs, direct_answer)
        _append_unique(
            paragraphs,
            _paragraph_from_lines(
                [
                    primary.get("hold_reason", ""),
                    "ログやスクショを送ってください。",
                    "実作業が必要と分かった場合は、見積り提案または新規依頼としてご案内します。",
                ]
            ),
        )
        return paragraphs

    if scenario == "closed_zip_fix_return":
        _append_unique(paragraphs, direct_answer)
        _append_unique(
            paragraphs,
            _paragraph_from_lines(
                [
                    "まずはこのメッセージ上で、前回の修正と関係がありそうかを確認します。",
                    "必要であれば、不具合に関係する箇所だけ分かる範囲で送ってください。",
                    "実作業が必要な場合は、見積り提案または新規依頼としてご案内します。",
                ]
            ),
        )
        return paragraphs

    if scenario == "closed_external_large_share":
        _append_unique(
            paragraphs,
            _paragraph_from_lines(
                [
                    direct_answer,
                    "ファイルはココナラのメッセージ添付で送れる範囲でお願いします。",
                ]
            ),
        )
        _append_unique(
            paragraphs,
            _paragraph_from_lines(
                [
                    "100MBを超える場合は、まず不具合に関係するファイルやログ、スクショだけに絞ってください。",
                    "その内容を見て、実作業が必要な場合は見積り提案または新規依頼としてご案内します。",
                ]
            ),
        )
        return paragraphs

    if scenario == "closed_secret_send_question":
        _append_unique(
            paragraphs,
            _paragraph_from_lines(
                [
                    direct_answer,
                    "確認には、必要なキー名だけ分かれば大丈夫です。",
                ]
            ),
        )
        _append_unique(
            paragraphs,
            _paragraph_from_lines(
                [
                    "ログやスクショを送る場合も、キーの値や秘密情報は伏せてください。",
                    "もし既に送ってしまった場合は、削除できるなら削除し、念のためキーの再発行も検討してください。",
                ]
            ),
        )
        return paragraphs

    if scenario == "closed_free_followup_price":
        _append_unique(paragraphs, direct_answer)
        _append_unique(
            paragraphs,
            _paragraph_from_lines(
                [
                    "恐れ入りますが、トークルームは閉じているため、この場でそのまま修正作業に入ることはできません。",
                    "このメッセージ上でできるのは、エラー内容やログ、スクショを見て、前回の修正とつながる内容かを確認するところまでです。",
                    *(ask.get("ask_text", "") for ask in ask_map),
                ]
            ),
        )
        _append_unique(
            paragraphs,
            "確認したうえで、メッセージ上の補足で済む内容か、コード修正などの作業が必要な内容かをお伝えします。",
        )
        _append_unique(
            paragraphs,
            "コード修正などの作業が必要になりそうな場合は、作業に入る前に、ココナラ上でどう進めるかと費用が発生するかを先にご相談します。",
        )
        return paragraphs

    if scenario == "closed_pre_estimate_cause_check":
        _append_unique(paragraphs, direct_answer)
        _append_unique(
            paragraphs,
            _paragraph_from_lines(
                [
                    "症状の概要やエラー内容を送ってください。",
                    "トークルームは閉じていますが、その内容から前回の修正と関係がありそうかの見立てはお返しできます。",
                    "その見立てをもとに、見積り提案に進むかどうかをご判断いただければ大丈夫です。",
                ]
            ),
        )
        return paragraphs

    if scenario == "closed_technical_followup_question":
        _append_unique(paragraphs, direct_answer)
        _append_unique(
            paragraphs,
            _paragraph_from_lines(
                [
                    primary.get("hold_reason", ""),
                    *(ask.get("ask_text", "") for ask in ask_map),
                    "確認して、説明で足りるか実作業が必要かをお返しします。",
                ]
            ),
        )
        return paragraphs

    if scenario == "closed_third_party_scope_concern":
        _append_unique(paragraphs, direct_answer)
        _append_unique(
            paragraphs,
            _paragraph_from_lines(
                [
                    primary.get("hold_reason", ""),
                    *(ask.get("ask_text", "") for ask in ask_map),
                    "確認後に、前回の補足で済む確認か、新規の実作業になるかをお伝えします。",
                ]
            ),
        )
        return paragraphs

    if scenario in {"refund_request", "price_complaint", "same_symptom_recur", "similar_but_not_same", "self_edit_regression", "api_version_notice_question"}:
        _append_unique(paragraphs, direct_answer)
        _append_unique(
            paragraphs,
            _paragraph_from_lines(
                [
                    focus_line or primary.get("hold_reason", ""),
                    *(ask.get("ask_text", "") for ask in ask_map),
                ]
            ),
        )
        return paragraphs

    if scenario == "mode_toggle_reminder":
        _append_unique(paragraphs, direct_answer)
        _append_unique(
            paragraphs,
            _paragraph_from_lines(
                [
                    "テスト側では「テストデータ」ラベルやオレンジ帯が出ることがあります。",
                    "UIの表示位置は少し変わることがありますが、その付近を見れば大丈夫です。",
                ]
            ),
        )
        return paragraphs

    if scenario == "webhook_secret_rotation_followup":
        _append_unique(paragraphs, direct_answer)
        _append_unique(
            paragraphs,
            _paragraph_from_lines(
                [
                    "StripeダッシュボードのWebhookエンドポイント設定と、受信側で参照している Webhook secret を同じ新しいものにそろえてください。",
                    "値そのものは送らず、設定箇所だけ見直してもらえれば大丈夫です。",
                ]
            ),
        )
        return paragraphs

    if scenario == "dashboard_login_issue":
        _append_unique(
            paragraphs,
            _paragraph_from_lines(
                [
                    direct_answer,
                    "まずは、パスワード再設定、二段階認証、チーム権限の状態を確認してみてください。",
                ]
            ),
        )
        return paragraphs

    if scenario == "new_feature_request":
        _append_unique(
            paragraphs,
            _paragraph_from_lines(
                [
                    direct_answer,
                    "この不具合修正サービスでは、この内容だけをそのまま進められません。",
                    "必要であれば、実装したい内容を別の相談として整理します。",
                ]
            ),
        )
        return paragraphs

    if scenario == "referral_and_soft_new_issue":
        _append_unique(
            paragraphs,
            _paragraph_from_lines(
                [
                    direct_answer,
                    "同じように困っている方がいれば、そのままご相談いただいて大丈夫です。",
                    "メルマガ配信機能の件も、必要なタイミングで症状が分かれば新しい相談として見積りできます。",
                ]
            ),
        )
        return paragraphs

    if scenario == "price_discount_request":
        _append_unique(
            paragraphs,
            _paragraph_from_lines(
                [direct_answer] + [item["answer_brief"] for item in secondary_now if item.get("answer_brief")]
            ),
        )
        if ask_map:
            _append_unique(
                paragraphs,
                _paragraph_from_lines(
                    [
                        focus_line or "",
                        *(ask.get("ask_text", "") for ask in ask_map),
                    ]
                ),
            )
        return paragraphs

    if scenario in {"new_issue_repeat_client", "closed_next_consult_path", "repeat_bugfix_price_check", "same_ticket_scope_question", "repeat_handoff_request", "memo_addendum_request", "new_flow_plus_discount", "recur_uncertainty"}:
        _append_unique(paragraphs, direct_answer)
        detail_lines: list[str] = []
        if focus_line:
            detail_lines.append(focus_line)
        elif primary.get("disposition") == "answer_after_check" and primary.get("hold_reason"):
            detail_lines.append(primary["hold_reason"])
        for item in secondary_now:
            if item.get("answer_brief"):
                detail_lines.append(item["answer_brief"])
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


def build_closed_render_payload(case: dict, opening_block: str, body_paragraphs: list[str], next_action: str) -> dict:
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
            case.get("scenario", "generic_closed"),
            case["reply_contract"],
        )
    if not case.get("service_grounding"):
        case["service_grounding"] = dict(SERVICE_GROUNDING)
    if not case.get("hard_constraints"):
        case["hard_constraints"] = build_hard_constraints(case.get("scenario", "generic_closed"), SERVICE_GROUNDING)

    contract = case["reply_contract"]
    decision_plan = case.get("response_decision_plan") or {}
    primary_id = contract["primary_question_id"]
    primary = next(item for item in contract["answer_map"] if item["question_id"] == primary_id)
    first_lines = [opener_for(case)]
    reaction = draft_opening_anchor(case)
    direct_answer = decision_plan.get("direct_answer_line") or ""
    if reaction and not _same_meaning(reaction, direct_answer):
        first_lines.append(reaction)
    opening_block = "\n".join(line for line in first_lines if line.strip())

    body_paragraphs: list[str] = []
    for paragraph in draft_body_paragraphs(case):
        _append_unique(body_paragraphs, paragraph)

    next_action = time_commit() if (primary["disposition"] == "answer_after_check" or decision_plan.get("blocking_missing_facts")) else ""

    sections: list[str] = []
    _append_unique(sections, opening_block)
    for paragraph in body_paragraphs:
        _append_unique(sections, paragraph)
    if next_action:
        _append_unique(sections, next_action)

    case["render_payload"] = build_closed_render_payload(case, opening_block, body_paragraphs, next_action)
    return "\n\n".join(section for section in sections if section.strip())


def main() -> int:
    parser = argparse.ArgumentParser(description="Render closed follow-up replies from flat closed cases.")
    parser.add_argument("--fixture", required=True)
    parser.add_argument("--case-id")
    parser.add_argument("--limit", type=int)
    parser.add_argument("--save", action="store_true")
    args = parser.parse_args()

    cases = shared.load_cases(Path(args.fixture))
    selected = [case for case in cases if case.get("state") == "closed"]
    if args.case_id:
        selected = [case for case in selected if case.get("case_id") == args.case_id or case.get("id") == args.case_id]
    if args.limit is not None:
        selected = selected[: args.limit]
    if not selected:
        print("[NG] no closed cases selected")
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
