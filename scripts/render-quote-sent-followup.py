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
        "private_repo_share_question",
        "zip_share_question",
        "multi_symptom_same_cause_scope_question",
        "code_vs_setting_scope_question",
        "subscription_bug_scope_question",
        "general_bugfix_scope_question",
        "secret_key_value_question",
        "can_you_fix_direct",
        "checkout_not_opening_scope_question",
        "service_interruption_anxiety",
        "price_trust_question",
        "response_speed_anxiety",
        "stage_only_before_fix_question",
        "generic_quote_sent",
    }:
        return shared.build_temperature_plan(source, case_type="boundary")
    return shared.build_temperature_plan(source, case_type="bugfix")


def opener_for(source: dict) -> str:
    return "ご連絡ありがとうございます。"


def purchase_closing(scenario: str, raw: str) -> str:
    if scenario == "general_bugfix_scope_question":
        if any(marker in raw for marker in ["Bubble", "非エンジニア", "手探り"]):
            return "この進め方で問題なければ、そのままご購入いただいて大丈夫です。"
        if any(marker in raw for marker in ["Shopify", "Liquid", "0円", "カート情報"]):
            return "問題なければ、そのままご購入いただければ大丈夫です。"
        if any(marker in raw for marker in ["Connect", "Destination Charge", "送金が動いていない", "送金が動いていません"]):
            return "この内容で問題なければ、そのままご購入いただいて大丈夫です。"
        if any(marker in raw for marker in ["本番", "テスト", "タイムアウト", "時間帯だけ", "深夜"]):
            return "内容が合えば、そのままご購入いただいて大丈夫です。"
    if scenario in {"subscription_bug_scope_question", "checkout_not_opening_scope_question"}:
        return "この内容で問題なければ、そのままご購入いただければ大丈夫です。"
    if scenario == "multi_symptom_same_cause_scope_question":
        return "問題なければ、このままご購入いただければ大丈夫です。"
    if scenario == "service_interruption_anxiety":
        return "問題なければ、そのままご購入いただいて進められます。"
    if scenario == "secret_key_value_question":
        return "問題なければ、そのままご購入いただければ大丈夫です。"
    if scenario == "zip_share_question":
        return "問題なければ、そのままご購入後にZIPで共有いただければ大丈夫です。"
    if scenario == "price_trust_question":
        return "この内容で問題なければ、そのままご購入いただければ問題ありません。"
    if scenario == "response_speed_anxiety":
        return "この前提で問題なければ、そのままご購入いただければ大丈夫です。"
    if scenario == "stage_only_before_fix_question":
        return "問題なければ、そのまま進め方をそろえてご案内できます。"
    if scenario == "can_you_fix_direct":
        return "問題なければ、そのままご購入いただければ大丈夫です。"
    if "内容" in raw:
        return "この内容で問題なければ、そのままご購入いただいて大丈夫です。"
    return "この前提で問題なければ、そのままご購入いただいて大丈夫です。"


def subscription_scope_detail_line(raw: str) -> str:
    if (
        any(marker in raw for marker in ["Laravel", "Cashier", "SDK"])
        and any(marker in raw for marker in ["プラン変更", "アップグレード", "旧プラン", "新プラン"])
    ):
        return "購入後に、Laravel で SDK を直接使っている前提も含めて、アップグレード時の請求の重なりを優先して確認します。"
    if any(marker in raw for marker in ["プラン変更", "アップグレード", "旧プラン", "新プラン"]):
        return "購入後に、プラン変更時だけ起きる請求の重なりかどうかを優先して確認して進めます。"
    if "解約" in raw and "請求" in raw:
        return "購入後に、解約後も請求が走るような症状かどうかを優先して確認して進めます。"
    return "購入後に、影響が大きい症状でも優先して状況を確認して進めます。"


def subscription_scope_support_line(raw: str) -> str:
    if any(marker in raw for marker in ["ドキュメント通り", "やったつもり"]):
        return "ドキュメント通りに進めていても起きうるので、その前提で切り分けます。"
    return ""


def general_bugfix_direct_answer_line(raw: str) -> str:
    if any(marker in raw for marker in ["Shopify", "Liquid", "0円", "カート情報"]):
        return "はい、Shopify と Stripe のつなぎ込みで起きている不具合でも確認できます。"
    if any(marker in raw for marker in ["Bubble", "決済プラグイン"]) and any(marker in raw for marker in ["Safari", "iOS"]):
        return "はい、Bubble.io の決済プラグインまわりでも確認できます。"
    if any(marker in raw for marker in ["Connect", "Destination Charge", "送金が動いていない", "送金が動いていません"]):
        return "はい、Stripe Connect の送金まわりでも確認できます。"
    if any(marker in raw for marker in ["Nuxt", "Nginx", "VPS", "タイムアウト", "時間帯だけ", "深夜"]):
        return "はい、Stripe の Webhook が不安定になる症状でも確認できます。"
    return "はい、Stripeや決済まわりの不具合であれば、このサービスでまず確認できます。"


def general_bugfix_scope_detail_line(raw: str) -> str:
    if any(marker in raw for marker in ["時間帯だけ", "深夜", "タイムアウト"]) and "Webhook" in raw:
        if any(marker in raw for marker in ["Nuxt", "Nginx", "VPS"]):
            return "購入後に、Nuxt 3 側の処理に加えて、さくらのVPS と Nginx を通した時だけタイムアウトが出ていないかも含めて確認します。"
        return "購入後に、時間帯で変わるWebhookの失敗かどうかも含めて確認します。"
    if any(marker in raw for marker in ["0円", "カート情報"]) and any(marker in raw for marker in ["Shopify", "Liquid"]):
        if "テスト環境" in raw or "テスト" in raw:
            return "購入後に、Shopify の Liquid とカスタムJSの間で、テスト環境でもカート情報と金額の受け渡しがどこで崩れているかを確認します。"
        return "購入後に、Shopify のカート情報と金額の受け渡しがどこで崩れているかも含めて確認します。"
    if any(marker in raw for marker in ["Safari", "iOS"]) and "決済画面" in raw:
        return "購入後に、iOS の Safari だけで起きる症状かどうかを切り分けながら確認します。"
    if any(marker in raw for marker in ["Connect", "Destination Charge", "送金が動いていない", "送金が動いていません"]):
        return "購入後に、Destination Charge 前提で入金から接続先アカウントへの送金までの流れがどこで止まっているかも含めて確認します。"
    if any(marker in raw for marker in ["たらい回し", "どこに頼めばいいか分から", "どこに頼めばいいか"]) :
        return "購入後に、切り分け先が曖昧な状態でもこちらで確認の入口を整理しながら進めます。"
    if any(marker in raw for marker in ["真っ白", "5回に1回", "再現条件がよく分から", "再現条件"]) :
        return "購入後に、毎回ではない症状でも再現条件を追いながら確認します。"
    if ("特定の商品" in raw or "他の商品" in raw) and ("メール" in raw or "飛ばない" in raw):
        return "購入後に、一部の商品だけ起きる症状でもイベントや通知の流れを含めて確認します。"
    if any(marker in raw for marker in ["テスト環境", "テストキー", "本番に出した途端", "本番だけ"]) :
        return "購入後に、テストでは出ず本番でだけ出る症状かどうかも含めて環境差を確認します。"
    if any(marker in raw for marker in ["YouTube", "エンジニアではなく", "説明が分かりにくかったら"]) :
        return "購入後に、説明は分かる範囲で大丈夫な前提で今見えている症状から確認します。"
    return "購入後にまず状況を確認して、原因の切り分けから進めます。"


def general_bugfix_scope_support_line(raw: str) -> str:
    if any(marker in raw for marker in ["非エンジニア", "Bubble", "説明が分かりにくかったら", "YouTube"]):
        return "非エンジニアの方でも大丈夫なので、分かる範囲の情報から進められます。"
    if any(marker in raw for marker in ["手探り", "Connectの経験がほとんどなくて", "Connectの経験がほとんどなく"]):
        return "手探りの状態でも進められるので、その前提で整理します。"
    if any(marker in raw for marker in ["自分のコードの問題だと思う", "自分のコードの問題"]):
        return "ご自身のコード側が原因かもしれない段階でも、その前提で確認できます。"
    if any(marker in raw for marker in ["たらい回し", "どこに頼めばいいか分から", "どこに頼めばいいか"]):
        return "切り分け先が曖昧な状態でも、こちらで入口を整理しながら進めます。"
    return ""


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
    if "SendGrid" in raw:
        facts.append("sendgrid_present")
    if "Stripe以外" in raw:
        facts.append("non_stripe_scope_question_present")
    if "送り忘れてたファイル" in raw or "送り忘れてた" in raw or "ファイルがあって" in raw:
        facts.append("additional_file_offer_present")
    if "Stripe関連のユーティリティ" in raw:
        facts.append("stripe_utility_file_present")
    if "自分で" in raw and any(marker in raw for marker in ["書き直して", "触っ", "壊してる可能性", "余計に壊して"]):
        facts.append("self_edit_risk_present")
    if "追加料金" in raw and any(marker in raw for marker in ["申し訳", "変に触っ", "自分で触っ"]):
        facts.append("self_edit_fee_anxiety_present")
    if "GitHub" in raw and "プライベートリポジトリ" in raw:
        facts.append("private_repo_present")
    if "招待" in raw:
        facts.append("invite_question_present")
    if "STRIPE_SECRET_KEY" in raw:
        facts.append("stripe_secret_key_name_present")
    if "sk_live_" in raw:
        facts.append("secret_key_prefix_mentioned")
    if any(marker in raw for marker in ["そのまま貼って", "貼って送れ", "貼って送れば"]):
        facts.append("secret_value_paste_question_present")
    if any(marker in raw for marker in ["どの範囲まで共有", "どこまで共有", "共有方法"]):
        facts.append("share_scope_question_present")
    if any(marker in raw for marker in ["どのくらい", "大体どのくらい", "どれくらい"]):
        facts.append("timeline_question_present")
    if "今日中" in raw:
        facts.append("same_day_check_requested")
    if "売上" in raw:
        facts.append("sales_impact_present")
    if "今週末" in raw or "確認会" in raw:
        facts.append("weekend_deadline_present")
    if "調査結果だけでも" in raw or ("調査結果" in raw and "先に" in raw):
        facts.append("investigation_first_requested")
    if "定期課金" in raw or "サブスクリプション" in raw:
        facts.append("subscription_context_present")
    if "二重に請求" in raw or "二重請求" in raw:
        facts.append("double_charge_present")
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
    if scenario == "self_edit_fee_anxiety":
        return "自分で触った影響があっても対応してもらえるかと、追加料金が自動で増えないか不安"
    if scenario == "self_apply_support":
        return "納品後に自分で反映した場合のサポート範囲を確認したい"
    if scenario == "secret_share_reassurance":
        return "本番URLや秘密情報を出さずに調査できるか確認したい"
    if scenario == "no_meeting_request":
        return "Zoomなしでも進められる代替手段を確認したい"
    if scenario == "private_repo_share_question":
        return "プライベートリポジトリをどの形で共有すればよいかと、どこまで見せればよいか不安"
    if scenario == "zip_share_question":
        return "GitHubではなくZIP共有でも進められるか知りたい"
    if scenario == "multi_symptom_same_cause_scope_question":
        return "似た症状が複数あっても1回の購入でまとめて見てもらえるか、金額が分かれるのか不安"
    if scenario == "code_vs_setting_scope_question":
        return "原因がコード側でも設定側でも見てもらえるのか、範囲の切れ目が不安"
    if scenario == "secret_key_value_question":
        return "STRIPE_SECRET_KEY の値をそのまま送ってよいか不安"
    if scenario == "subscription_bug_scope_question":
        return "Stripeの定期課金まわりの不具合も今回のサービスで対応できるか確認したい"
    if scenario == "general_bugfix_scope_question":
        return "いま起きている決済まわりの不具合を今回のサービスで見てもらえるか確認したい"
    if scenario == "checkout_not_opening_scope_question":
        return "チェックアウト画面に進まない不具合も今回のサービスで対応できるか確認したい"
    if scenario == "service_interruption_anxiety":
        return "作業中にサイトが止まることがあるのか不安"
    if scenario == "price_trust_question":
        return "15,000円で内容が足りるのか、本当にちゃんと見てもらえるのか不安"
    if scenario == "response_speed_anxiety":
        return "購入後に何日も返事が来ないことがないか不安"
    if scenario == "can_you_fix_direct":
        return "結局この不具合を見てもらえるのか、端的に知りたい"
    if scenario == "timeline_question":
        if "same_day_check_requested" in facts_known:
            return "購入後に今日中に見てもらえるかと、売上影響が大きいので早めに動いてもらえるか確認したい"
        return "調査から修正までの目安と、難しい場合に調査結果だけ先に受け取れるか確認したい"
    if "sendgrid_present" in facts_known and "additional_file_offer_present" in facts_known:
        return "Stripe以外に見えているSendGrid処理まで今回の提案で見られるかと、追加ファイルをどう渡せばよいか確認したい"
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
    has_bugfix_stack_context = any(
        marker in combined
        for marker in [
            "Stripe",
            "決済",
            "Checkout",
            "Webhook",
            "Next.js",
            "Vercel",
            "GitHub",
            "Firebase",
            "microCMS",
            "API Routes",
            "Nuxt",
            "Nginx",
            "VPS",
            "Shopify",
            "Liquid",
            "Bubble",
            "Laravel",
            "Cashier",
            "Connect",
            "Destination Charge",
        ]
    )
    has_bugfix_surface = any(
        marker in combined
        for marker in [
            "困って",
            "根本原因が分から",
            "イベントが来ていない",
            "決済が通らなく",
            "メールが飛ばない",
            "真っ白になる",
            "たらい回し",
            "どこに頼めばいいか分から",
            "再現条件がよく分から",
            "ログを見てもどこが悪いかよく分から",
            "タイムアウト",
            "0円",
            "Safariだけ",
            "iOS",
            "送金が動いていません",
            "送金が動いていない",
            "受け取れなくなる",
            "請求が同時に走る",
            "アップグレードの時だけ",
        ]
    )

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
    if (
        any(marker in combined for marker in ["書き直してみた", "自分で触った", "余計に壊してる可能性", "変に触っちゃった"])
        and any(marker in combined for marker in ["対応してもらえますか", "追加料金", "申し訳ない"])
    ):
        return "self_edit_fee_anxiety"
    if (
        "GitHub" in combined
        and "プライベートリポジトリ" in combined
        and any(marker in combined for marker in ["招待", "共有方法", "どの範囲まで共有", "どこまで共有"])
    ):
        return "private_repo_share_question"
    if ("githubじゃなくてzip" in combined.lower() or "zipで送ってもいい" in combined.lower() or "zipで送ってもいい？" in combined.lower()):
        return "zip_share_question"
    if (
        any(marker in combined for marker in ["1回の購入", "1つのバグだけ", "3箇所", "まとめて見てもら", "別々に購入"])
        and any(marker in combined for marker in ["同じ原因", "同じ原因っぽい", "似たような症状"])
    ):
        return "multi_symptom_same_cause_scope_question"
    if (
        any(marker in combined for marker in ["整理だけ", "まず整理だけ", "様子を見る", "メモを見てから判断"])
        and any(marker in combined for marker in ["修正を頼むか", "追加で修正", "判断したい", "15000の方", "15,000の方", "直しじゃなく"])
    ):
        return "stage_only_before_fix_question"
    if (
        any(marker in combined for marker in ["コード側", "自分のコード側", "Stripeの設定", "設定の問題"])
        and any(marker in combined for marker in ["範囲外", "直してもらえる", "直してもらえるんですか", "このサービス"])
    ):
        return "code_vs_setting_scope_question"
    if "STRIPE_SECRET_KEY" in combined and ("sk_live_" in combined or "貼って送" in combined or "そのまま貼って" in combined):
        return "secret_key_value_question"
    if (
        any(marker in combined for marker in ["定期課金", "サブスクリプション", "プラン変更", "アップグレード"])
        and (
            any(marker in combined for marker in ["対応可能", "対応でしょうか", "対応できますか", "こちらのサービスで", "見ていただけ", "見てもらえ"])
            or any(marker in combined for marker in ["請求が同時に走る", "旧プラン", "新プラン", "解約したあとも"])
        )
    ):
        return "subscription_bug_scope_question"
    if (
        any(marker in combined for marker in ["購入ボタン", "チェックアウト画面", "飛ばなくなりました", "飛ばなくなった"])
        and any(marker in combined for marker in ["対応いただける", "お願いしたい", "お願いしたいです", "対応可能", "見ていただけ", "見てもらえ"])
    ):
        return "checkout_not_opening_scope_question"
    if (
        any(marker in combined for marker in ["見ていただくことは可能", "見ていただけますでしょうか", "見ていただける", "対応いただけるか教えて", "一度見てもらうことは可能", "対応いただけるか"])
        and has_bugfix_stack_context
    ):
        return "general_bugfix_scope_question"
    if has_bugfix_stack_context and has_bugfix_surface:
        return "general_bugfix_scope_question"
    if (
        any(marker in combined for marker in ["5万円", "5万", "15000", "15,000", "安かろう悪かろう", "内容に差"])
        and any(marker in combined for marker in ["本当にちゃんと直りますか", "迷ってます", "迷っています", "率直にお聞きします"])
    ):
        return "price_trust_question"
    if (
        any(marker in combined for marker in ["使えなくなったりする", "営業時間中", "止まると困る", "環境が使えなく"])
        and any(marker in combined for marker in ["困る", "不安", "止まる"])
    ):
        return "service_interruption_anxiety"
    if (
        any(marker in combined for marker in ["何日も返事がなくて", "何日も返事", "キャンセルになった", "レスポンスって大体どのくらい", "レスポンスって", "失礼な質問"])
        and any(marker in combined for marker in ["購入後", "返事", "レスポンス", "キャンセル"])
    ):
        return "response_speed_anxiety"
    if "直りますか" in combined and any(marker in combined for marker in ["で、結局", "結局これ"]):
        return "can_you_fix_direct"
    if "別原因" in combined and ("金額が増える" in combined or "キャンセル" in combined or "怖くて" in combined):
        return "extra_fee_fear"
    if any(
        marker in combined
        for marker in [
            "どのくらいかかりますか",
            "大体どのくらい",
            "調査結果だけでも",
            "今週末に社内で確認会",
            "今日中に見てもらえ",
            "今日中に見てもら",
            "売上に直結",
        ]
    ):
        return "timeline_question"
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
    elif scenario == "self_edit_fee_anxiety":
        direct_answer_line = "はい、その場合でもまず今の状態を見て対応可否を確認できます。"
        response_order = ["reaction", "direct_answer", "answer_detail", "next_action"]
    elif scenario == "self_apply_support":
        direct_answer_line = "今回の提案では、本番への反映自体は依頼者様でお願いしていますが、確認手順はお渡しします。"
        response_order = ["reaction", "direct_answer", "answer_detail", "next_action"]
    elif scenario == "private_repo_share_question":
        direct_answer_line = "必ずリポジトリ全体を共有いただく必要はなく、不具合に関係する範囲からで大丈夫です。"
        response_order = ["reaction", "direct_answer", "answer_detail", "next_action"]
    elif scenario == "zip_share_question":
        direct_answer_line = "はい、GitHubではなくZIPで送っていただいて大丈夫です。"
        response_order = ["reaction", "direct_answer", "answer_detail", "next_action"]
    elif scenario == "multi_symptom_same_cause_scope_question":
        direct_answer_line = "同じ原因なら、1回の購入としてまとめて確認できる場合があります。"
        response_order = ["reaction", "direct_answer", "answer_detail", "next_action"]
    elif scenario == "code_vs_setting_scope_question":
        direct_answer_line = "原因がご自身のコード側でも、このサービスで確認できます。"
        response_order = ["reaction", "direct_answer", "answer_detail", "next_action"]
    elif scenario == "secret_key_value_question":
        direct_answer_line = "STRIPE_SECRET_KEY は通常 sk_live_ で始まりますが、値そのものは送らないでください。"
        response_order = ["reaction", "direct_answer", "answer_detail", "next_action"]
    elif scenario == "subscription_bug_scope_question":
        if any(marker in raw for marker in ["Laravel", "Cashier", "SDK"]):
            direct_answer_line = "はい、Laravel のサブスクリプション処理でも確認できます。"
        else:
            direct_answer_line = "はい、Stripeの定期課金まわりの不具合であれば、このサービスで確認できます。"
        response_order = ["reaction", "direct_answer", "answer_detail", "next_action"]
    elif scenario == "general_bugfix_scope_question":
        direct_answer_line = general_bugfix_direct_answer_line(raw)
        response_order = ["reaction", "direct_answer", "answer_detail", "next_action"]
    elif scenario == "checkout_not_opening_scope_question":
        direct_answer_line = "はい、Stripeのチェックアウトに進まない不具合でも、このサービスで確認できます。"
        response_order = ["reaction", "direct_answer", "answer_detail", "next_action"]
    elif scenario == "service_interruption_anxiety":
        direct_answer_line = "こちらで確認や修正内容を整理するだけで、依頼者様の環境がそのまま使えなくなる前提ではありません。"
        response_order = ["reaction", "direct_answer", "answer_detail", "next_action"]
    elif scenario == "price_trust_question":
        direct_answer_line = f"{fee_text}でも、今回の不具合1件の範囲で原因確認と修正判断まで見ます。"
        response_order = ["reaction", "direct_answer", "answer_detail", "next_action"]
    elif scenario == "response_speed_anxiety":
        direct_answer_line = "購入後は、まず受領確認と次の流れをお返しします。"
        response_order = ["reaction", "direct_answer", "answer_detail", "next_action"]
    elif scenario == "stage_only_before_fix_question":
        direct_answer_line = "追加で修正を頼むかどうかを、整理した内容を見てから判断する進め方はできます。"
        response_order = ["reaction", "direct_answer", "answer_detail", "next_action"]
    elif scenario == "can_you_fix_direct":
        direct_answer_line = "購入前の段階で必ず直るとまでは断定できませんが、今回の不具合として確認して進めます。"
        response_order = ["reaction", "direct_answer", "answer_detail", "next_action"]
    elif scenario == "secret_share_reassurance":
        direct_answer_line = "はい、本番のURLをそのまま送っていただかなくても進められます。"
        response_order = ["reaction", "direct_answer", "answer_detail", "next_action"]
    elif scenario == "no_meeting_request":
        direct_answer_line = "Zoomや通話での進行はしていません。"
        response_order = ["reaction", "direct_answer", "answer_detail", "next_action"]
    elif scenario == "timeline_question":
        if "今日中" in raw:
            direct_answer_line = "購入後、まず調査結果を先にお返しして、今日中にどこまで確認できるかもあわせてお伝えします。"
        else:
            direct_answer_line = "まず調査結果を先にお返しして、その時点で修正まで進められそうかもあわせてお伝えします。"
        response_order = ["reaction", "direct_answer", "answer_detail", "next_action"]
    else:
        if "sendgrid_present" in facts_known and "additional_file_offer_present" in facts_known:
            blocking_missing_facts = ["stripe_related_file"]
            direct_answer_line = "Stripeに関係する範囲であれば、SendGrid側の処理も今回の件として一緒に確認できる可能性があります。"
            response_order = ["reaction", "direct_answer", "answer_detail", "ask"]
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
                    "hold_reason": "決済エラーとメール通知が同じ原因かどうかを先に切ります。",
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

    if scenario == "self_edit_fee_anxiety":
        case["reply_contract"] = {
            "primary_question_id": "q1",
            "explicit_questions": [{"id": "q1", "text": "自分で触った影響があっても対応してもらえるか、追加料金になるのか", "priority": "primary"}],
            "answer_map": [
                {
                    "question_id": "q1",
                    "disposition": "answer_now",
                    "answer_brief": "自分で触った部分があっても、まず今の状態を見て今回の件として進められるか確認できます。",
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

    if scenario == "private_repo_share_question":
        case["reply_contract"] = {
            "primary_question_id": "q1",
            "explicit_questions": [
                {"id": "q1", "text": "GitHubのプライベートリポジトリは招待が必要か", "priority": "primary"},
                {"id": "q2", "text": "どの範囲まで共有すればよいか", "priority": "secondary"},
            ],
            "answer_map": [
                {
                    "question_id": "q1",
                    "disposition": "answer_now",
                    "answer_brief": "必ずリポジトリ全体を共有いただく必要はなく、不具合に関係する範囲からで大丈夫です。",
                }
            ],
            "ask_map": [],
            "required_moves": ["react_briefly_first", "answer_directly_now"],
        }
        case["response_decision_plan"] = build_response_decision_plan(source, scenario, case["reply_contract"])
        return case

    if scenario == "zip_share_question":
        case["reply_contract"] = {
            "primary_question_id": "q1",
            "explicit_questions": [
                {"id": "q1", "text": "GitHubではなくZIPで送ってよいか", "priority": "primary"},
            ],
            "answer_map": [
                {
                    "question_id": "q1",
                    "disposition": "answer_now",
                    "answer_brief": "はい、GitHubではなくZIPで送っていただいて大丈夫です。",
                }
            ],
            "ask_map": [],
            "required_moves": ["react_briefly_first", "answer_directly_now"],
        }
        case["response_decision_plan"] = build_response_decision_plan(source, scenario, case["reply_contract"])
        return case

    if scenario == "multi_symptom_same_cause_scope_question":
        case["reply_contract"] = {
            "primary_question_id": "q1",
            "explicit_questions": [
                {"id": "q1", "text": "似た症状を1回の購入でまとめて見られるか", "priority": "primary"},
                {"id": "q2", "text": "別々に購入しないといけないのか", "priority": "secondary"},
            ],
            "answer_map": [
                {
                    "question_id": "q1",
                    "disposition": "answer_now",
                    "answer_brief": "同じ原因なら、1回の購入としてまとめて確認できる場合があります。",
                },
                {
                    "question_id": "q2",
                    "disposition": "answer_now",
                    "answer_brief": "別原因なら分かれますが、その場合も勝手に増やさず事前にご相談します。",
                },
            ],
            "ask_map": [],
            "required_moves": ["react_briefly_first", "answer_directly_now"],
        }
        case["response_decision_plan"] = build_response_decision_plan(source, scenario, case["reply_contract"])
        return case

    if scenario == "code_vs_setting_scope_question":
        case["reply_contract"] = {
            "primary_question_id": "q1",
            "explicit_questions": [
                {"id": "q1", "text": "原因がコード側でも対応してもらえるか", "priority": "primary"},
                {"id": "q2", "text": "Stripe設定だけの問題なら範囲外か", "priority": "secondary"},
            ],
            "answer_map": [
                {
                    "question_id": "q1",
                    "disposition": "answer_now",
                    "answer_brief": "原因がご自身のコード側でも、このサービスで確認できます。",
                },
                {
                    "question_id": "q2",
                    "disposition": "answer_now",
                    "answer_brief": "Stripe設定側でも、今回の不具合に関係する範囲なら確認対象です。別の話まで広がる場合は、その時点で事前にご相談します。",
                },
            ],
            "ask_map": [],
            "required_moves": ["react_briefly_first", "answer_directly_now"],
        }
        case["response_decision_plan"] = build_response_decision_plan(source, scenario, case["reply_contract"])
        return case

    if scenario == "secret_key_value_question":
        case["reply_contract"] = {
            "primary_question_id": "q1",
            "explicit_questions": [
                {"id": "q1", "text": "STRIPE_SECRET_KEY は sk_live_ で始まるものか", "priority": "primary"},
                {"id": "q2", "text": "購入後に値をそのまま貼って送ってよいか", "priority": "secondary"},
            ],
            "answer_map": [
                {
                    "question_id": "q1",
                    "disposition": "answer_now",
                    "answer_brief": "STRIPE_SECRET_KEY は通常 sk_live_ で始まりますが、値そのものは送らないでください。",
                },
                {
                    "question_id": "q2",
                    "disposition": "answer_now",
                    "answer_brief": "購入後も、キー名だけ共有いただければ大丈夫です。",
                },
            ],
            "ask_map": [],
            "required_moves": ["react_briefly_first", "answer_directly_now"],
        }
        case["response_decision_plan"] = build_response_decision_plan(source, scenario, case["reply_contract"])
        return case

    if scenario == "subscription_bug_scope_question":
        case["reply_contract"] = {
            "primary_question_id": "q1",
            "explicit_questions": [{"id": "q1", "text": "Stripeの定期課金まわりも対応可能か", "priority": "primary"}],
            "answer_map": [
                {
                    "question_id": "q1",
                    "disposition": "answer_now",
                    "answer_brief": "Stripeの定期課金まわりの不具合であれば、このサービスでまず確認できます。",
                }
            ],
            "ask_map": [],
            "required_moves": ["react_briefly_first", "answer_directly_now"],
        }
        case["response_decision_plan"] = build_response_decision_plan(source, scenario, case["reply_contract"])
        return case

    if scenario == "general_bugfix_scope_question":
        case["reply_contract"] = {
            "primary_question_id": "q1",
            "explicit_questions": [{"id": "q1", "text": "今回の不具合を見てもらえるか", "priority": "primary"}],
            "answer_map": [
                {
                    "question_id": "q1",
                    "disposition": "answer_now",
                    "answer_brief": "はい、Stripeや決済まわりの不具合であれば、このサービスでまず確認できます。",
                }
            ],
            "ask_map": [],
            "required_moves": ["react_briefly_first", "answer_directly_now"],
        }
        case["response_decision_plan"] = build_response_decision_plan(source, scenario, case["reply_contract"])
        return case

    if scenario == "checkout_not_opening_scope_question":
        case["reply_contract"] = {
            "primary_question_id": "q1",
            "explicit_questions": [{"id": "q1", "text": "チェックアウト画面に進まない不具合も対応可能か", "priority": "primary"}],
            "answer_map": [
                {
                    "question_id": "q1",
                    "disposition": "answer_now",
                    "answer_brief": "Stripeのチェックアウトに進まない不具合であれば、このサービスでまず確認できます。",
                }
            ],
            "ask_map": [],
            "required_moves": ["react_briefly_first", "answer_directly_now"],
        }
        case["response_decision_plan"] = build_response_decision_plan(source, scenario, case["reply_contract"])
        return case

    if scenario == "service_interruption_anxiety":
        case["reply_contract"] = {
            "primary_question_id": "q1",
            "explicit_questions": [{"id": "q1", "text": "作業中にサイトが止まることはあるか", "priority": "primary"}],
            "answer_map": [
                {
                    "question_id": "q1",
                    "disposition": "answer_now",
                    "answer_brief": "こちらで確認や修正内容を整理するだけで、依頼者様の環境がそのまま使えなくなる前提ではありません。",
                }
            ],
            "ask_map": [],
            "required_moves": ["react_briefly_first", "answer_directly_now"],
        }
        case["response_decision_plan"] = build_response_decision_plan(source, scenario, case["reply_contract"])
        return case

    if scenario == "price_trust_question":
        case["reply_contract"] = {
            "primary_question_id": "q1",
            "explicit_questions": [{"id": "q1", "text": "15,000円でちゃんと見てもらえるか", "priority": "primary"}],
            "answer_map": [
                {
                    "question_id": "q1",
                    "disposition": "answer_now",
                    "answer_brief": f"{SERVICE_GROUNDING['fee_text']}でも、今回の不具合1件の範囲で原因確認と修正判断まで見ます。",
                }
            ],
            "ask_map": [],
            "required_moves": ["react_briefly_first", "answer_directly_now"],
        }
        case["response_decision_plan"] = build_response_decision_plan(source, scenario, case["reply_contract"])
        return case

    if scenario == "response_speed_anxiety":
        case["reply_contract"] = {
            "primary_question_id": "q1",
            "explicit_questions": [{"id": "q1", "text": "購入後のレスポンスはどのくらいか", "priority": "primary"}],
            "answer_map": [
                {
                    "question_id": "q1",
                    "disposition": "answer_now",
                    "answer_brief": "購入後は、まず受領確認と次の流れをお返しします。",
                }
            ],
            "ask_map": [],
            "required_moves": ["react_briefly_first", "answer_directly_now"],
        }
        case["response_decision_plan"] = build_response_decision_plan(source, scenario, case["reply_contract"])
        return case

    if scenario == "stage_only_before_fix_question":
        case["reply_contract"] = {
            "primary_question_id": "q1",
            "explicit_questions": [{"id": "q1", "text": "整理内容を見てから追加修正を判断できるか", "priority": "primary"}],
            "answer_map": [
                {
                    "question_id": "q1",
                    "disposition": "answer_now",
                    "answer_brief": "追加で修正を頼むかどうかを、整理した内容を見てから判断する形にできます。",
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

    if scenario == "timeline_question":
        case["reply_contract"] = {
            "primary_question_id": "q1",
            "explicit_questions": [{"id": "q1", "text": "調査から修正までどのくらいかかるか", "priority": "primary"}],
            "answer_map": [
                {
                    "question_id": "q1",
                    "disposition": "answer_now",
                    "answer_brief": "まず調査結果を先にお返しして、その時点で修正まで進められそうかもあわせてお伝えします。",
                }
            ],
            "ask_map": [],
            "required_moves": ["react_briefly_first", "answer_directly_now"],
        }
        case["response_decision_plan"] = build_response_decision_plan(source, scenario, case["reply_contract"])
        return case

    if scenario == "can_you_fix_direct":
        case["reply_contract"] = {
            "primary_question_id": "q1",
            "explicit_questions": [
                {"id": "q1", "text": "結局直るのか", "priority": "primary"},
            ],
            "answer_map": [
                {
                    "question_id": "q1",
                    "disposition": "answer_now",
                    "answer_brief": "購入前の段階で必ず直るとまでは断定できませんが、今回の不具合として確認して進めます。",
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
                "hold_reason": "まずは変更点や気になっている点を短く確認します。",
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
        return "Webhook受信口に加えて、Stripeダッシュボード設定の件、確認しました。"
    if scenario == "extra_fee_fear":
        return "金額が増えるのでは、というご不安はもっともです。"
    if scenario == "self_edit_fee_anxiety":
        return "ご自身で触った影響も不安とのこと、確認しました。"
    if scenario == "self_apply_support":
        return "ご自身で反映する場合のサポート範囲ですね。確認しました。"
    if scenario == "private_repo_share_question":
        return "コード共有の方法が不安とのこと、確認しました。"
    if scenario == "zip_share_question":
        return "ZIPでの共有方法が気になっている件、確認しました。"
    if scenario == "multi_symptom_same_cause_scope_question":
        return "似た症状が複数ある件、確認しました。"
    if scenario == "code_vs_setting_scope_question":
        return "コード側か設定側かが気になっている件、確認しました。"
    if scenario == "secret_key_value_question":
        return "STRIPE_SECRET_KEY の共有方法が気になっている件、確認しました。"
    if scenario == "subscription_bug_scope_question":
        if any(marker in raw for marker in ["プラン変更", "アップグレード", "旧プラン", "新プラン"]):
            return "プラン変更時に請求が重なる件、確認しました。"
        if "解約" in raw and "請求" in raw:
            return "解約後も請求が走っている件、確認しました。"
        return "定期課金の二重請求が出ていてお困りとのこと、確認しました。"
    if scenario == "general_bugfix_scope_question":
        if any(marker in raw for marker in ["時間帯だけ", "深夜", "タイムアウト"]) and "Webhook" in raw:
            return "特定の時間帯だけWebhookが失敗する件、確認しました。"
        if any(marker in raw for marker in ["0円", "カート情報"]) and any(marker in raw for marker in ["Shopify", "Liquid"]):
            return "カート情報が渡らず0円で決済される件、確認しました。"
        if any(marker in raw for marker in ["Safari", "iOS"]) and "決済画面" in raw:
            return "iOSのSafariだけ決済画面が開かない件、確認しました。"
        if any(marker in raw for marker in ["Connect", "Destination Charge", "送金が動いていません", "送金が動いていない"]):
            return "接続先アカウントへの送金が動いていない件、確認しました。"
        if "たらい回し" in raw or "どこに頼めばいいか分から" in raw:
            return "たらい回しになっていてお困りとのこと、確認しました。"
        if ("特定の商品" in raw or "他の商品" in raw) and ("メール" in raw or "飛ばない" in raw):
            return "特定の商品だけ購入完了後のメールが飛ばない件、確認しました。"
        if ("本番に出した途端" in raw or "本番だけ" in raw) and ("エラー" in raw or "決済" in raw):
            return "本番でだけ決済時エラーが出る件、確認しました。"
        if "メールが飛ばない" in raw:
            return "購入完了後のメールが飛ばない件、確認しました。"
        if "真っ白" in raw:
            return "決済完了後の画面が真っ白になる件、確認しました。"
        if "決済が通らなく" in raw:
            return "決済が通らなくなっている件、確認しました。"
        if "お支払い処理中にエラー" in raw:
            return "決済時エラーが出ている件、確認しました。"
        return "決済まわりの不具合の件、確認しました。"
    if scenario == "checkout_not_opening_scope_question":
        return "チェックアウト画面に進まなくなったとのこと、確認しました。"
    if scenario == "service_interruption_anxiety":
        return "作業中に環境が使えなくならないかご不安とのこと、確認しました。"
    if scenario == "price_trust_question":
        return "金額差があるとご不安になりますよね。確認しました。"
    if scenario == "response_speed_anxiety":
        return "購入後のレスポンスが気になっている件、確認しました。"
    if scenario == "stage_only_before_fix_question":
        return "整理だけで一度判断したい件、確認しました。"
    if scenario == "can_you_fix_direct":
        return "ご不安な点、確認しました。"
    if scenario == "secret_share_reassurance":
        if "evt_" in raw:
            return "evt_... まで確認できているとのこと、ありがとうございます。"
        return "共有範囲についてのご不安、確認しました。"
    if scenario == "no_meeting_request":
        return "文章で伝えるのが大変な点、確認しました。"
    if scenario == "timeline_question":
        if "今日中" in raw:
            return "売上に直結していてお急ぎとのこと、まず優先して確認に入ります。"
        return "今週末の確認会に間に合わせたいとのこと、確認しました。"
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
    facts_known = decision_plan.get("facts_known") or []

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
        paragraphs.append(purchase_closing(scenario, raw))
        return paragraphs

    if scenario == "payment_method":
        return [f"{direct_answer}\n{grounding.get('payment_platform_rule', '')}".strip()]

    if scenario == "dashboard_scope_question":
        return [
            f"{direct_answer}\nStripe 以外の別機能や別原因まで広がる場合だけ、その時点で切り分けて事前にご相談します。".strip(),
            purchase_closing(scenario, raw),
        ]

    if scenario == "extra_fee_fear":
        return [
            f"{direct_answer}\nその場合は状況を共有し、追加対応に進まずそこで止める形も含めて事前にご相談します。".strip(),
            "キャンセルの扱いは、ココナラ上の案内に沿う形になります。",
            purchase_closing(scenario, raw),
        ]

    if scenario == "self_edit_fee_anxiety":
        return [
            f"{direct_answer}\n自分で触ったことだけを理由に追加料金が決まるわけではなく、必要なら状況を見てから事前にご相談します。".strip(),
            purchase_closing(scenario, raw),
        ]

    if scenario == "self_apply_support":
        return [
            f"{direct_answer}\n{grounding.get('same_cause_followup_rule', '')}".strip(),
            purchase_closing(scenario, raw),
        ]

    if scenario == "private_repo_share_question":
        return [
            f"{direct_answer}\n招待が必要な場合でも、確認に必要な部分だけ共有いただければ進められます。".strip(),
            "最初から全部そろっていなくても大丈夫です。",
            purchase_closing(scenario, raw),
        ]

    if scenario == "zip_share_question":
        return [
            f"{direct_answer}\ngit を使っていない場合でも、その形で進められます。".strip(),
            purchase_closing(scenario, raw),
        ]

    if scenario == "multi_symptom_same_cause_scope_question":
        return [
            f"{direct_answer}\n別原因なら分かれますが、その場合も勝手に増やさず事前にご相談します。".strip(),
            purchase_closing(scenario, raw),
        ]

    if scenario == "code_vs_setting_scope_question":
        return [
            direct_answer,
            "Stripe設定側でも、今回の不具合に関係する範囲なら確認対象です。別の話まで広がる場合は、その時点で事前にご相談します。",
            purchase_closing(scenario, raw),
        ]

    if scenario == "secret_key_value_question":
        return [
            f"{direct_answer}\n購入後も、キー名だけ共有いただければ大丈夫です。".strip(),
            purchase_closing(scenario, raw),
        ]

    if scenario == "subscription_bug_scope_question":
        paragraphs = [
            f"{direct_answer}\n{subscription_scope_detail_line(raw)}".strip(),
        ]
        support = subscription_scope_support_line(raw)
        if support:
            paragraphs.append(support)
        paragraphs.append(purchase_closing(scenario, raw))
        return paragraphs

    if scenario == "general_bugfix_scope_question":
        paragraphs = [
            f"{direct_answer}\n{general_bugfix_scope_detail_line(raw)}".strip(),
        ]
        support = general_bugfix_scope_support_line(raw)
        if support:
            paragraphs.append(support)
        paragraphs.append(purchase_closing(scenario, raw))
        return paragraphs

    if scenario == "checkout_not_opening_scope_question":
        return [
            f"{direct_answer}\n先週までは動いていた症状でも、購入後にまず状況を確認して進めます。".strip(),
            purchase_closing(scenario, raw),
        ]

    if scenario == "service_interruption_anxiety":
        return [
            f"{direct_answer}\n本番反映は依頼者様側でお願いしているため、営業時間を避けて進めることもできます。".strip(),
            purchase_closing(scenario, raw),
        ]

    if scenario == "price_trust_question":
        return [
            f"{direct_answer}\n価格だけで作業内容を削っているわけではありません。".strip(),
            "ただ、購入前の段階で「必ず直る」とまでは断定せず、状況を確認したうえで進めます。",
            purchase_closing(scenario, raw),
        ]

    if scenario == "response_speed_anxiety":
        return [
            f"{direct_answer}\n確認に時間がかかる場合も、何日も無反応のまま止める進め方にはしません。".strip(),
            "途中で見えてきたことや次の見通し、連絡目安もその時点でお返しします。",
            purchase_closing(scenario, raw),
        ]

    if scenario == "stage_only_before_fix_question":
        return [
            f"{direct_answer}\nまず整理した内容を見て、そのあとで追加対応が必要かを判断いただく形で大丈夫です。".strip(),
        ]

    if scenario == "can_you_fix_direct":
        return [
            direct_answer,
            purchase_closing(scenario, raw),
        ]

    if scenario == "secret_share_reassurance":
        return [
            f"{direct_answer}\n{grounding.get('no_secret_share_rule', '')}".strip(),
            purchase_closing(scenario, raw),
        ]

    if scenario == "no_meeting_request":
        return [
            f"{direct_answer}\n{grounding.get('text_only_support_rule', '')}".strip(),
            "その形で問題なければ、そのままご購入いただいて大丈夫です。",
        ]

    if scenario == "timeline_question":
        if "今日中" in raw:
            return [
                direct_answer,
                "今日中に修正まで進められるかは見てからの判断になりますが、難しい場合でも確認できたところから先にお返しします。",
                purchase_closing(scenario, raw),
            ]
        return [
            f"{direct_answer}\n今週末までに直せるかは見てからの判断になりますが、難しい場合でも調査結果だけ先にお送りします。".strip(),
            purchase_closing(scenario, raw),
        ]

    if "sendgrid_present" in facts_known and "additional_file_offer_present" in facts_known:
        return [
            f"{direct_answer}\nStripe以外の別の原因まで広がる場合だけ、その時点で切り分けてお返しします。".strip(),
            "送り忘れていたファイルは、そのまま送ってください。",
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
