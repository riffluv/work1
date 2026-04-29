#!/usr/bin/env python3
from __future__ import annotations

import argparse
import importlib.util
import re
from pathlib import Path

import yaml
from reply_quality_lint_common import infer_buyer_emotion


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
        "refund_policy": "全額返金になるかどうかは、この時点でこちらから断定できません。",
        "reissue_support": "期限が切れた場合も、必要なら同内容で再提案できます。",
        "payment_platform_rule": "購入画面に表示されている方法の中から選んで進めてください。",
        "dashboard_scope_rule": "Webhook受信口に関係する範囲であれば、Stripeダッシュボード側の設定も確認対象です。",
        "self_apply_support_rule": "本番への反映自体は依頼者様でお願いします。確認手順はお渡しします。",
        "same_cause_followup_rule": "トークルームが開いている間に同じ原因の範囲で詰まる点があれば、その範囲は基本料金内で確認します。",
        "no_secret_share_rule": "evt_... やログ、設定画面の見える範囲で確認できます。",
        "text_only_support_rule": "スクショや短い箇条書きで送っていただければ大丈夫です。",
        "capability": facts.get("capability") or {},
        "diagnostic_patterns": facts.get("diagnostic_patterns") or [],
        "hard_no": facts.get("hard_no") or [],
    }


SERVICE_GROUNDING = load_service_grounding()


def is_handoff_source(source: dict) -> bool:
    service_hint = source.get("service_hint")
    service_id = source.get("service") or source.get("service_id")
    return service_hint == "handoff" or service_id == "handoff-25000"


def detect_handoff_quote_sent_scenario(raw: str) -> str:
    if any(marker in raw for marker in ["修正が必要だと分かった場合", "そのまま修正もお願い", "続けてお願いできるか"]):
        return "handoff_followon_fix"
    if any(marker in raw for marker in ["追加料金はいくら", "全部まとめて見てもらう", "ユーザー登録", "メール通知"]):
        return "handoff_extra_flow_fee"
    return "handoff_generic_followup"


def build_handoff_quote_sent_reply(source: dict) -> str:
    raw = source.get("raw_message", "")
    scenario = detect_handoff_quote_sent_scenario(raw)

    if scenario == "handoff_followon_fix":
        paragraphs = [
            "\n".join(
                [
                    "ご連絡ありがとうございます。",
                    "はい、整理のあとに修正が必要と分かった場合も、続けてご相談いただけます。",
                ]
            ),
            "今回の整理では、まず主要1フローの構造・危険箇所・次の着手順をまとめます。修正そのものは含みませんが、必要になった場合は別対応として進め方と費用を先にご相談します。",
        ]
        return "\n\n".join(paragraphs)

    if scenario == "handoff_extra_flow_fee":
        paragraphs = [
            "\n".join(
                [
                    "ご連絡ありがとうございます。",
                    "基本は主要1フローごとの整理なので、別の流れに分かれる場合はその時点で範囲を分けてご相談します。",
                ]
            ),
            "同じ起点でつながる1つの流れとして整理できるなら、まずはまとめて見られるかをこちらで確認します。",
            "いま挙がっている内容なら、まずはどこを優先して整理するかをそろえて進めるのが近いです。",
        ]
        return "\n\n".join(paragraphs)

    paragraphs = [
        "\n".join(
            [
                "ご連絡ありがとうございます。",
                "はい、整理後の次の進め方も続けてご相談いただけます。",
            ]
        ),
        "基本料金では主要1フローの整理と引き継ぎメモ作成までで、修正そのものは含みません。必要になった場合は、その時点で別対応としてご案内します。",
    ]
    return "\n\n".join(paragraphs)


def classify_capability_fit(raw: str) -> tuple[str, str | None]:
    capability = SERVICE_GROUNDING.get("capability") or {}

    for entry in capability.get("out_of_scope_or_review") or []:
        markers = entry.get("markers") or []
        if any(marker in raw for marker in markers):
            return "out_of_scope_or_review", entry.get("id")

    for entry in capability.get("cautious_fit") or []:
        markers = entry.get("markers") or []
        if any(marker in raw for marker in markers):
            return "cautious_fit", entry.get("id")

    for entry in capability.get("strong_fit") or []:
        markers = entry.get("markers") or []
        if any(marker in raw for marker in markers):
            return "strong_fit", entry.get("id")

    return "unknown", None


def classify_diagnostic_patterns(raw: str) -> list[dict]:
    patterns = SERVICE_GROUNDING.get("diagnostic_patterns") or []
    matched: list[dict] = []
    for entry in patterns:
        markers = entry.get("markers") or []
        if any(marker in raw for marker in markers):
            matched.append(entry)
    return matched


def diagnostic_priority_line(raw: str) -> str:
    pattern_ids = [entry.get("id") for entry in classify_diagnostic_patterns(raw)]
    if "prod_only_failure" in pattern_ids and "partial_or_branch_failure" in pattern_ids:
        return "まずは本番だけ出る環境差に加えて、プランや条件ごとの差を優先して見ます。"
    if "browser_specific_failure" in pattern_ids and "mobile_sdk_platform_gap" in pattern_ids:
        return "まずは Android 実機と iOS の差に加えて、モバイルSDK側のコールバック処理を優先して見ます。"
    if "database_persistence_gap" in pattern_ids:
        return "まずは Webhook 受信後の保存処理と DB 書き込み経路を優先して見ます。"
    if "mobile_sdk_platform_gap" in pattern_ids:
        return "まずはモバイルSDK差と端末差を優先して見ます。"
    if "prod_only_failure" in pattern_ids:
        return "まずは環境差と環境変数まわりを優先して見ます。"
    if "partial_or_branch_failure" in pattern_ids:
        return "まずは条件差や商品ごとの設定差を優先して見ます。"
    if "intermittent_or_time_window" in pattern_ids:
        return "まずは発生条件や時間帯の偏りを優先して見ます。"
    if "browser_specific_failure" in pattern_ids:
        return "まずは端末差やブラウザ差を優先して見ます。"
    if "subscription_change_overlap" in pattern_ids:
        return "まずはプラン変更時の請求処理の流れを優先して見ます。"
    if "connect_transfer_path" in pattern_ids:
        return "まずは入金から送金までの経路差を優先して見ます。"
    return ""


def build_temperature_plan_for_case(source: dict, scenario: str) -> dict:
    if scenario == "discount_request":
        plan = shared.build_temperature_plan(source, case_type="boundary")
        plan["opening_move"] = "react_briefly"
        return plan
    if scenario in {
        "proposal_change",
        "purchase_timing",
        "reissue_quote",
        "prequote_extra_signal",
        "service_comparison_refund_question",
        "service_comparison_strength_question",
        "risk_refund_question",
        "payment_method",
        "dashboard_scope_question",
        "prepayment_materials_before_payment",
        "extra_fee_fear",
        "self_apply_support",
        "secret_share_reassurance",
        "no_meeting_request",
        "private_repo_share_question",
        "zip_share_question",
        "multi_symptom_same_cause_scope_question",
        "scope_constraints_question",
        "mixed_scope_fee_question",
        "browser_vs_code_question",
        "code_vs_setting_scope_question",
        "subscription_bug_scope_question",
        "general_bugfix_scope_question",
        "secret_key_value_question",
        "can_you_fix_direct",
        "checkout_not_opening_scope_question",
        "service_interruption_anxiety",
        "price_trust_question",
        "discount_request",
        "self_try_webhook_test_question",
        "response_speed_anxiety",
        "stage_only_before_fix_question",
        "feature_addition_scope_question",
        "outline_share_permission_question",
        "auth_boundary_scope_question",
        "provider_unknown_scope_question",
        "cause_and_prevention_scope_question",
        "ai_fix_failure_reassurance_question",
        "price_not_found_self_fix_question",
        "generic_quote_sent",
    }:
        return shared.build_temperature_plan(source, case_type="boundary")
    return shared.build_temperature_plan(source, case_type="bugfix")


def opener_for(source: dict) -> str:
    return "ご連絡ありがとうございます。"


def purchase_closing(scenario: str, raw: str) -> str:
    if scenario == "discount_request":
        return "この条件で問題なければ、ご購入をご検討ください。"
    if scenario == "self_try_webhook_test_question":
        return ""
    if scenario == "prequote_extra_signal":
        return "この前提でよければ、そのままご購入へ進めてください。"
    if scenario == "service_comparison_refund_question":
        return "内容に違和感がなければ、そのままご購入へ進めてください。"
    if scenario == "service_comparison_strength_question":
        return "内容が合いそうなら、そのままご購入をご検討ください。"
    if scenario == "risk_refund_question":
        return "この条件で問題なければ、ご購入をご検討ください。"
    if scenario == "general_bugfix_scope_question":
        if any(marker in raw for marker in ["機会損失", "取りこぼして", "毎日だいたい", "注文が来る"]):
            return "急ぎの前提でよければ、そのままご購入へ進めてください。"
        if any(marker in raw for marker in ["Bubble", "非エンジニア", "手探り"]):
            return "この進め方でよければ、そのままご購入へ進めてください。"
        if any(marker in raw for marker in ["Shopify", "Liquid", "0円", "カート情報"]):
            return "問題なければ、そのままご購入ください。"
        if any(marker in raw for marker in ["Connect", "Destination Charge", "送金が動いていない", "送金が動いていません"]):
            return "この内容でよければ、そのままご購入へ進めてください。"
        if any(marker in raw for marker in ["本番", "テスト", "タイムアウト", "時間帯だけ", "深夜"]):
            return "内容が合いそうであれば、そのままご購入へ進めてください。"
        return "この範囲でよければ、そのままご購入へ進めてください。"
    if scenario in {"subscription_bug_scope_question", "checkout_not_opening_scope_question"}:
        return "この範囲感で問題なければ、そのままご購入ください。"
    if scenario == "multi_symptom_same_cause_scope_question":
        return "問題なければ、このままご購入へ進めてください。"
    if scenario == "scope_constraints_question":
        return "この範囲で問題なければ、そのままご購入へ進めてください。"
    if scenario == "mixed_scope_fee_question":
        return "切り分け方で問題なければ、そのままご購入へ進めてください。"
    if scenario == "browser_vs_code_question":
        return "その前提でよければ、そのままご購入へ進められます。"
    if scenario == "service_interruption_anxiety":
        return "問題なければ、そのままご購入へ進められます。"
    if scenario == "secret_key_value_question":
        return "問題なければ、そのままご購入へ進めてください。"
    if scenario == "zip_share_question":
        return "問題なければ、そのままご購入後にZIPで共有いただければ大丈夫です。"
    if scenario == "price_trust_question":
        return "内容に違和感がなければ、そのままご購入ください。"
    if scenario == "response_speed_anxiety":
        return "この前提でよければ、そのままご購入へ進めてください。"
    if scenario == "stage_only_before_fix_question":
        return "問題なければ、そのまま進め方をそろえてご案内できます。"
    if scenario == "feature_addition_scope_question":
        return ""
    if scenario == "outline_share_permission_question":
        return ""
    if scenario == "auth_boundary_scope_question":
        return "切り分けの進め方で問題なければ、そのままご購入へ進めてください。"
    if scenario == "provider_unknown_scope_question":
        return ""
    if scenario == "ultra_short_fixability_question":
        return ""
    if scenario == "ai_fix_failure_reassurance_question":
        return "問題なければ、そのままご購入へ進めてください。"
    if scenario == "price_not_found_self_fix_question":
        return ""
    if scenario == "can_you_fix_direct":
        return "問題なければ、そのままご購入へ進めてください。"
    if "内容" in raw:
        return "この内容でよければ、そのままご購入へ進めてください。"
    return "この前提でよければ、そのままご購入へ進めてください。"


def subscription_scope_detail_line(raw: str) -> str:
    priority = diagnostic_priority_line(raw)
    if (
        any(marker in raw for marker in ["Laravel", "Cashier", "SDK"])
        and any(marker in raw for marker in ["プラン変更", "アップグレード", "旧プラン", "新プラン"])
    ):
        detail = "購入後に、Laravel で SDK を直接使っている前提も含めて、アップグレード時の請求の重なりを優先して確認します。"
        return detail
    if "proration" in raw and any(marker in raw for marker in ["プラン変更", "途中で変更", "アップグレード", "旧プラン", "新プラン"]):
        return "購入後に、proration 設定も候補として、プラン変更時だけ二重請求が出る条件を優先して確認します。"
    if any(marker in raw for marker in ["プラン変更", "アップグレード", "旧プラン", "新プラン"]):
        return "購入後に、プラン変更時だけ二重請求が出る条件を優先して確認します。"
    if "解約" in raw and "請求" in raw:
        return "購入後に、解約後も請求が走る条件を優先して確認します。"
    detail = "購入後に、影響が大きい症状でも優先して状況を確認して進めます。"
    return f"{detail}\n{priority}".strip()


def subscription_scope_support_line(raw: str) -> str:
    if any(marker in raw for marker in ["コードでは対処できない", "コードで対処できない", "その判断だけでも"]):
        return ""
    if any(marker in raw for marker in ["1件分の料金", "収まりますか", "料金で収まりますか", "15,000円", "15000円", "もっとかかりますか", "済みますか"]):
        if any(marker in raw for marker in ["音沙汰なし", "信用するのが怖い", "何も解決しませんでした"]):
            return "別原因まで広がる場合だけ、その時点で事前にご相談します。確認できたところは止めずに順にお返しします。"
        return "別原因まで広がる場合だけ、その時点で事前にご相談します。"
    if any(marker in raw for marker in ["ドキュメント通り", "やったつもり"]):
        return "ドキュメント通りに進めていても起きうるので、その前提で切り分けます。"
    if any(marker in raw for marker in ["音沙汰なし", "信用するのが怖い", "何も解決しませんでした"]):
        return "進め方が見えにくくならないよう、確認できたところから順にお返しします。"
    return ""


def general_bugfix_direct_answer_line(raw: str) -> str:
    fit_level, _ = classify_capability_fit(raw)
    can_start = "まず確認できます" if fit_level == "cautious_fit" else "確認できます"
    if "API Routes" in raw and any(marker in raw for marker in ["バリデーション", "15,000円", "15000円"]):
        return f"はい、原因が API Routes 側のバリデーションでも、決済まわりの不具合として {SERVICE_GROUNDING['fee_text']} の範囲で進めます。"
    if any(marker in raw for marker in ["切り分けと修正可否", "動作確認まで含ま", "コードを修正して", "どこまでやってもらえる"]):
        return f"{SERVICE_GROUNDING['fee_text']} の範囲で、原因確認からコード修正まで対応しています。"
    if any(marker in raw for marker in ["Stripe も見てもらえるんですよね", "Stripeも見てもらえるんですよね", "Stripe も見てもらえる", "Stripeも見てもらえる"]):
        return f"Stripe を含む決済導線も今回のサービスで{can_start}。"
    if any(marker in raw for marker in ["機会損失", "取りこぼして", "毎日だいたい", "注文が来る"]) and any(
        marker in raw for marker in ["対応可能", "対応可能ですか", "早めに直したい"]
    ):
        return f"売上影響が出ている決済停止でも、{can_start}。"
    if any(marker in raw for marker in ["Webフック", "ウェブソケット", "APIキーが合わない", "認証トークン"]) and "Stripe" in raw:
        return f"Webhook の署名まわりで止まっている症状でも、{can_start}。"
    if any(marker in raw for marker in ["thanks ページ", "success URL", "success ページ"]) and any(marker in raw for marker in ["遷移しない", "戻される", "崩れる"]):
        return f"決済完了後の画面表示トラブルでも、{can_start}。"
    if "カート" in raw and any(marker in raw for marker in ["決済後に消えない", "消えない症状", "残る症状", "残って"]) :
        return f"決済後の状態更新が崩れている症状でも、{can_start}。"
    if (
        any(marker in raw for marker in ["15,000円", "15000円", "15,000", "15000"])
        and "Checkout" in raw
        and any(marker in raw for marker in ["無理そうだったら", "正直に言って", "プロの目で"])
    ):
        return f"Checkout が途中で止まる症状なら、まず {SERVICE_GROUNDING['fee_text']} の範囲で見られるか確認できます。"
    if any(marker in raw for marker in ["15,000円", "15000円", "15,000", "15000"]) and any(
        marker in raw for marker in ["可能ですか", "可能でしょうか", "可能ですか？", "可能でしょうか？"]
    ):
        return f"今回の不具合1件の範囲なら {SERVICE_GROUNDING['fee_text']} でまず確認できます。"
    if any(marker in raw for marker in ["ぐるぐる", "先に進めない"]) and any(
        marker in raw for marker in ["カード", "クレジットカード", "Stripe"]
    ):
        return f"カード入力後に止まる症状でも、{can_start}。"
    if any(marker in raw for marker in ["見てもらうことって可能でしょうか", "見てもらえる感じですか", "見てもらえたりしますか"]) and "Stripe" in raw:
        return "Stripe の決済まわりで困っている段階でも、まず相談できます。"
    if ("http://" in raw or "https://" in raw) and any(marker in raw for marker in ["直せますか", "動かないです"]):
        return "Stripe 決済の不具合でしたら、確認できます。"
    if any(marker in raw for marker in ["直せますか", "修正できますか"]) and "Stripe" in raw:
        return f"Stripe の決済まわりの不具合でも、{can_start}。"
    if any(marker in raw for marker in ["昨日までは", "今朝から", "急にエラー", "急に"]) and "決済" in raw:
        return f"急に出始めた決済エラーでも、{can_start}。"
    if any(marker in raw for marker in ["Checkout", "success ページ", "画面が真っ白", "/checkout に戻される"]):
        return f"決済完了後の画面表示トラブルでも、{can_start}。"
    if any(marker in raw for marker in ["Prisma", "PlanetScale", "注文テーブル", "書き込み"]) and "Webhook" in raw:
        return f"Webhook は届いているのに注文反映が止まる症状でも、{can_start}。"
    if any(marker in raw for marker in ["Vercel", "本番"]) and "500エラー" in raw:
        return f"Vercel の本番でだけ 500 エラーになる症状でも、{can_start}。"
    if any(marker in raw for marker in ["Vercel", "serverless functions", "10秒制限"]) and "Webhook" in raw:
        return f"Vercel のタイムアウトが疑われる Webhook 停止でも、{can_start}。"
    if any(marker in raw for marker in ["React Native", "stripe-react-native", "@stripe/stripe-react-native"]):
        return f"React Native の Stripe 決済まわりでも、{can_start}。"
    if any(marker in raw for marker in ["Shopify", "Liquid"]):
        return f"Shopify と Stripe のつなぎ込みで起きている不具合でも、{can_start}。"
    if any(marker in raw for marker in ["Bubble", "決済プラグイン"]) and any(marker in raw for marker in ["Safari", "iOS"]):
        return f"Bubble.io の決済プラグインまわりでも、{can_start}。"
    if any(marker in raw for marker in ["Connect", "Destination Charge", "送金が動いていない", "送金が動いていません"]):
        return f"Stripe Connect の送金まわりでも、{can_start}。"
    if "payment_intent.succeeded" in raw and any(marker in raw for marker in ["Webhook", "届かなく", "届いていません"]):
        return f"payment_intent.succeeded の Webhook が届かない症状でも、{can_start}。"
    if any(marker in raw for marker in ["メールが行かない", "メールが届かない", "完了メールが届かない"]) and any(
        marker in raw for marker in ["支払い", "決済", "Stripe"]
    ):
        return f"決済完了後のメール通知トラブルでも、{can_start}。"
    if any(marker in raw for marker in ["Nuxt", "Nginx", "VPS", "タイムアウト", "時間帯だけ", "深夜"]):
        return f"Stripe の Webhook が不安定になる症状でも、{can_start}。"
    return f"Stripe や決済まわりの不具合なら、このサービスで{can_start}。"


def general_bugfix_scope_detail_line(raw: str) -> str:
    priority = diagnostic_priority_line(raw)
    if "API Routes" in raw and "バリデーション" in raw:
        return "購入後にまず状況を確認して、どこで止まっているかを見ます。"
    if any(marker in raw for marker in ["切り分けと修正可否", "動作確認まで含ま", "コードを修正して", "どこまでやってもらえる"]):
        return "動作確認も、こちらで確認できる範囲までは含めて進めます。"
    if any(marker in raw for marker in ["ぐるぐる", "先に進めない"]) and any(
        marker in raw for marker in ["カード", "クレジットカード", "Stripe"]
    ):
        detail = "購入後に、カード入力後の処理がどこで止まっているかを確認します。"
        return f"{detail}\n{priority}".strip()
    if any(marker in raw for marker in ["Webフック", "ウェブソケット", "APIキーが合わない", "認証トークン"]) and "Stripe" in raw:
        return "購入後に、Webhook の署名設定や検証まわりでどこがずれているかを確認します。"
    if any(marker in raw for marker in ["thanks ページ", "success URL", "success ページ"]) and any(
        marker in raw for marker in ["遷移しない", "戻される", "崩れる"]
    ):
        detail = "購入後に、thanks ページへ進まず戻り先が崩れる条件と、本番環境だけで出る差を確認します。"
        if "payment_intent.succeeded" in raw:
            detail = f"{detail}\nStripe 側で payment_intent.succeeded になっている前提も含めて、戻り先でどこが崩れているかを確認します。"
        return detail
    if any(marker in raw for marker in ["success ページ", "/checkout に戻される"]) and any(
        marker in raw for marker in ["本番", "localhost", "payment_intent", "succeeded", "Vercel"]
    ):
        detail = "購入後に、success ページへ進まず /checkout に戻る再現条件と、本番環境だけで出る差を確認します。"
        if "payment_intent.succeeded" in raw:
            detail = f"{detail}\nStripe 側で payment_intent.succeeded になっている前提も含めて、戻り先でどこが崩れているかを確認します。"
        return detail
    if "カート" in raw and "消えない" in raw and "決済後" in raw:
        detail = "購入後に、決済後の状態更新でカートが残る条件と、その後の画面遷移を確認します。"
        return f"{detail}\n{priority}".strip()
    if "Webhook" in raw and any(marker in raw for marker in ["たまに失敗", "たまに", "失敗してるみたい"]):
        detail = "購入後に、Webhook が失敗する条件や前後の状態を確認します。"
        priority_line = "まずは発生条件や時間帯の偏りを優先して見ます。"
        return f"{detail}\n{priority_line}".strip()
    if any(marker in raw for marker in ["Prisma", "PlanetScale", "注文テーブル", "書き込み"]) and "Webhook" in raw:
        detail = "購入後に、Prisma と PlanetScale の保存処理を含めて、注文テーブルへの反映がどこで止まっているかを確認します。"
        return f"{detail}\n{priority}".strip()
    if any(marker in raw for marker in ["Vercel", "serverless functions", "10秒制限"]) and "Webhook" in raw:
        detail = "購入後に、Vercel の serverless functions のタイムアウト仮説も候補として、Webhook が止まる条件を確認します。"
        return f"{detail}\n{priority}".strip()
    if any(marker in raw for marker in ["React Native", "stripe-react-native", "@stripe/stripe-react-native"]):
        detail = "購入後に、@stripe/stripe-react-native を使った前提で、Android 実機だけ決済完了コールバックが返らない条件を確認します。"
        return f"{detail}\n{priority}".strip()
    if any(marker in raw for marker in ["時間帯だけ", "深夜", "タイムアウト"]) and "Webhook" in raw:
        if any(marker in raw for marker in ["Nuxt", "Nginx", "VPS"]):
            detail = "購入後に、Nuxt 3 側の処理に加えて、さくらのVPS と Nginx を通した時だけタイムアウトが出ていないかも含めて確認します。"
            return f"{detail}\n{priority}".strip()
        detail = "購入後に、時間帯で変わるWebhookの失敗かどうかも含めて確認します。"
        return f"{detail}\n{priority}".strip()
    if any(marker in raw for marker in ["0円", "カート情報"]) and any(marker in raw for marker in ["Shopify", "Liquid"]):
        if "テスト環境" in raw or "テスト" in raw:
            detail = "購入後に、Shopify の Liquid とカスタムJSの間で、テスト環境でもカート情報と金額の受け渡しがどこで崩れているかを確認します。"
            return f"{detail}\n{priority}".strip()
        detail = "購入後に、Shopify のカート情報と金額の受け渡しがどこで崩れているかも含めて確認します。"
        return f"{detail}\n{priority}".strip()
    if any(marker in raw for marker in ["Safari", "iOS"]) and "決済画面" in raw:
        detail = "購入後に、iOS の Safari だけで起きる症状かどうかを切り分けながら確認します。"
        return f"{detail}\n{priority}".strip()
    if any(marker in raw for marker in ["Connect", "Destination Charge", "送金が動いていない", "送金が動いていません"]):
        detail = "購入後に、Destination Charge 前提で入金から接続先アカウントへの送金までの流れがどこで止まっているかも含めて確認します。"
        return f"{detail}\n{priority}".strip()
    if ("本番環境" in raw or "本番だけ" in raw) and any(marker in raw for marker in ["年額プラン", "月額プラン", "特定のプラン"]) and "500" in raw:
        detail = "購入後に、Vercel の本番環境で年額プランだけ 500 エラーになる条件差を確認します。"
        return f"{detail}\n{priority}".strip()
    if any(marker in raw for marker in ["たらい回し", "どこに頼めばいいか分から", "どこに頼めばいいか"]) :
        return "購入後に、切り分け先が曖昧な状態でもこちらで確認の入口を整理しながら進めます。"
    if any(marker in raw for marker in ["真っ白", "5回に1回", "再現条件がよく分から", "再現条件"]) :
        if any(marker in raw for marker in ["Node.js", "サーバーの移行"]):
            detail = "購入後に、Checkout から戻った後に画面が真っ白になる条件に加えて、移行後の環境差も含めて確認します。"
        else:
            detail = "購入後に、毎回ではない症状でも再現条件を追いながら確認します。"
        return f"{detail}\n{priority}".strip()
    if ("特定の商品" in raw or "他の商品" in raw) and ("メール" in raw or "飛ばない" in raw):
        detail = "購入後に、一部の商品だけ起きる症状でもイベントや通知の流れを含めて確認します。"
        return f"{detail}\n{priority}".strip()
    if any(marker in raw for marker in ["テスト環境", "テストキー", "本番に出した途端", "本番だけ"]) :
        detail = "購入後に、テストでは出ず本番でだけ出る症状かどうかも含めて環境差を確認します。"
        return f"{detail}\n{priority}".strip()
    if any(marker in raw for marker in ["YouTube", "エンジニアではなく", "説明が分かりにくかったら"]) :
        detail = "購入後に、説明は分かる範囲で大丈夫な前提で今見えている症状から確認します。"
        return f"{detail}\n{priority}".strip()
    if "payment_intent.succeeded" in raw and any(marker in raw for marker in ["Webhook", "届かなく", "届いていません"]):
        detail = "購入後に、payment_intent.succeeded の Webhook が届かなくなった経路と設定差を確認します。"
        return f"{detail}\n{priority}".strip()
    if any(marker in raw for marker in ["メールが行かない", "メールが届かない", "完了メールが届かない"]) and any(
        marker in raw for marker in ["支払い", "決済", "Stripe"]
    ):
        detail = "購入後に、決済完了後の通知処理とメール送信の流れがどこで止まっているかを確認します。"
        return f"{detail}\n{priority}".strip()
    detail = "購入後にまず状況を確認して、原因の切り分けから進めます。"
    return f"{detail}\n{priority}".strip()


def general_bugfix_scope_support_line(raw: str) -> str:
    if any(marker in raw for marker in ["Stripe は対象外", "Stripeは対象外"]):
        return "以前そう言われた経緯があっても、今回は Stripe を含む決済導線として見ます。"
    if any(marker in raw for marker in ["友人から紹介", "紹介されて来", "紹介されてき", "紹介されて来ました"]):
        return "今回の症状も、まず同じように切り分けながら確認します。"
    if any(marker in raw for marker in ["支払いが完成", "メールが行かない"]):
        return "詳しい説明はあとからで大丈夫なので、まず今見えている症状から確認できます。"
    if any(marker in raw for marker in ["機会損失", "取りこぼして", "毎日だいたい", "注文が来る"]) and any(
        marker in raw for marker in ["対応可能", "対応可能ですか", "早めに直したい"]
    ):
        return "売上影響が続いている状況なので、購入後に優先して確認します。"
    if any(marker in raw for marker in ["無理そうだったら正直", "無理そうだったら", "正直に言ってもらって大丈夫"]):
        return "難しそうな場合は、その時点でそのままお伝えします。"
    if any(marker in raw for marker in ["再現できませんでした", "2週間待った", "今度こそちゃんと見てもらえる"]):
        return "前回のようにテスト環境だけで切り上げず、本番でだけ出る前提も含めて見ます。"
    if any(marker in raw for marker in ["Vercel", "serverless functions", "10秒制限"]) and any(
        marker in raw for marker in ["多分", "確証はない", "引っかかってるんじゃないか"]
    ):
        return "その推測も候補として見ますが、決めつけずにログや挙動を見ながら確認します。"
    if any(marker in raw for marker in ["非エンジニア", "Bubble", "説明が分かりにくかったら", "YouTube"]):
        return "非エンジニアの方でも大丈夫なので、分かる範囲の情報から進められます。"
    if any(marker in raw for marker in ["手探り", "Connectの経験がほとんどなくて", "Connectの経験がほとんどなく"]):
        return "手探りの状態でも進められるので、その前提で整理します。"
    if any(marker in raw for marker in ["自分のコードの問題だと思う", "自分のコードの問題"]):
        return "ご自身のコード側が原因かもしれない段階でも、その前提で確認できます。"
    if any(marker in raw for marker in ["コードをほぼ理解できていません", "何を送ればいいかも分からない", "ChatGPTとCursor", "AIに書いてもらった", "ChatGPT", "Cursor"]):
        return "コードをすべて理解できていない状態でも大丈夫なので、分かる範囲の情報から進められます。"
    if ("http://" in raw or "https://" in raw) and any(marker in raw for marker in ["直せますか", "動かないです"]):
        return "どこで止まるかだけ、分かる範囲で教えてください。"
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
    if scenario == "prequote_extra_signal":
        return "追記したエラーも今回の件とあわせて見てもらえるか確認したい"
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
    if scenario == "scope_constraints_question":
        return "15,000円で見られる範囲の制約と、同じ原因ならどこまで含まれるか知りたい"
    if scenario == "mixed_scope_fee_question":
        return "決済ボタンの不具合と画像アップロード不具合を一緒に見られるか、別料金になるか知りたい"
    if scenario == "outline_share_permission_question":
        return "まず概要だけ伝えて相談してよいか不安"
    if scenario == "provider_unknown_scope_question":
        return "カード決済がStripeかどうかも分からない状態で、まず相談してよいか不安"
    if scenario == "checkout_not_opening_scope_question":
        return "チェックアウト画面に進まない不具合も今回のサービスで対応できるか確認したい"
    if scenario == "service_interruption_anxiety":
        return "作業中にサイトが止まることがあるのか不安"
    if scenario == "price_trust_question":
        return "15,000円で内容が足りるのか、本当にちゃんと見てもらえるのか不安"
    if scenario == "discount_request":
        return "予算の都合がある中で、10,000円に下げられるか知りたい"
    if scenario == "self_try_webhook_test_question":
        return "購入前に自分で送信テストを試したいが、そのあと直らなければ戻ってきてよいか知りたい"
    if scenario == "service_comparison_refund_question":
        return "他サービスと比較した時の強みと、直らなかった場合の返金の扱いを確認したい"
    if scenario == "price_not_found_self_fix_question":
        return "price_not_found が設定ずれだけで直るのか、自分で直せる範囲かを先に知りたい"
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
    fit_level, fit_id = classify_capability_fit(combined)
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
            "Prisma",
            "PlanetScale",
            "React Native",
            "stripe-react-native",
            "payment_intent.succeeded",
            "Webフック",
            "ウェブソケット",
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
            "届かなくなりました",
            "届かなくなった",
            "請求が同時に走る",
            "アップグレードの時だけ",
            "コールバックが返ってこない",
            "注文テーブル",
            "書き込みが途中で止まって",
            "反映されてない",
            "500エラー",
            "特定のプランだけ",
            "エラーは出てる",
            "エラーが出てる",
            "本番だけかもしれない",
            "テスト環境では動いてる",
            "success ページ",
            "/checkout に戻される",
            "payment_intent は succeeded",
            "APIキーが合わない",
            "認証トークンが違う",
            "直してもらえますか",
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
    if (
        "納品された修正コード" in combined
        or "自分で反映" in combined
        or (
            any(marker in combined for marker in ["修正ファイル", "修正してもらったファイル"])
            and any(marker in combined for marker in ["自分でVercelにデプロイ", "自分でデプロイ", "デプロイする形", "手順も教えて", "デプロイのやり方"])
        )
    ):
        return "self_apply_support"
    if (
        any(marker in combined for marker in ["先ほどメッセージ送った", "追記", "念のためお伝え", "追加でお伝え"])
        and any(marker in combined for marker in ["No signatures found matching the expected signature for payload", "署名", "signature"])
    ):
        return "prequote_extra_signal"
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
        any(marker in combined for marker in ["15,000円", "15000円", "15,000", "15000"])
        and any(marker in combined for marker in ["制約", "Stripe部分だけ", "対象がStripe部分だけ", "期間が決まってる", "逆に何か制約"])
    ):
        return "scope_constraints_question"
    if (
        any(marker in combined for marker in ["画像アップロード", "別料金になりますか", "一緒に見てもらえたら", "決済とは関係ない"])
        and any(marker in combined for marker in ["決済ボタン", "Stripe", "反応しない"])
    ):
        return "mixed_scope_fee_question"
    if (
        any(marker in combined for marker in ["Safari", "iPhone", "ブラウザの問題", "コード側の問題", "完了画面に飛ばない"])
        and "Stripe" in combined
    ):
        return "browser_vs_code_question"
    if (
        any(marker in combined for marker in ["コード側", "自分のコード側", "Stripeの設定", "設定の問題"])
        and any(marker in combined for marker in ["範囲外", "直してもらえる", "直してもらえるんですか", "このサービス"])
    ):
        return "code_vs_setting_scope_question"
    if (
        any(marker in combined for marker in ["ログインしたのに", "認証の問題", "決済ページに行けない"])
        and any(marker in combined for marker in ["Stripeの問題なのか認証の問題なのか", "分からなくて", "見ていただくことは可能", "対応可能", "このサービス"])
    ):
        return "auth_boundary_scope_question"
    if (
        any(marker in combined for marker in ["Stripeかどうかも", "Stripeかどうか", "正直よく分かりません"])
        and any(marker in combined for marker in ["クレジットカード決済", "カード決済", "管理画面くらい", "外注"])
    ):
        return "provider_unknown_scope_question"
    if fit_level == "out_of_scope_or_review" and any(
        marker in combined
        for marker in ["新しく作りたい", "カスタムUI", "Billing Portal", "プラン変更フォーム", "ポータル画面"]
    ):
        return "feature_addition_scope_question"
    if (
        any(marker in combined for marker in ["SendGrid", "Stripe以外の部分", "送り忘れてたファイル", "追加で聞いてもいい"])
        and any(marker in combined for marker in ["含めて1件で見てもらえ", "追加で聞いてもいい", "Stripe関連のユーティリティ"])
    ):
        return "proposal_change"
    if "STRIPE_SECRET_KEY" in combined and ("sk_live_" in combined or "貼って送" in combined or "そのまま貼って" in combined):
        return "secret_key_value_question"
    if (
        any(marker in combined for marker in ["返金してもらえる", "原因が分からなかった場合", "原因がわからなかった場合", "直らなかった場合"])
        and "Stripe" in combined
    ):
        return "risk_refund_question"
    if (
        any(marker in combined for marker in ["定期課金", "サブスクリプション", "プラン変更", "アップグレード"])
        and (
            any(marker in combined for marker in ["対応可能", "対応でしょうか", "対応できますか", "こちらのサービスで", "見ていただけ", "見てもらえ", "1件分の料金", "収まりますか", "15,000円", "15000円", "もっとかかりますか", "済みますか"])
            or any(marker in combined for marker in ["請求が同時に走る", "旧プラン", "新プラン", "解約したあとも", "二重請求"])
        )
    ):
        return "subscription_bug_scope_question"
    if (
        any(marker in combined for marker in ["Stripe。", "Stripe ", "Stripeの"])
        and any(marker in combined for marker in ["Webhook", "動かない"])
        and any(marker in combined for marker in ["直せる？", "直せる?"])
        and len(re.sub(r"\s+", "", combined)) <= 40
    ):
        return "ultra_short_fixability_question"
    if (
        any(marker in combined for marker in ["購入ボタン", "チェックアウト画面", "飛ばなくなりました", "飛ばなくなった"])
        and any(marker in combined for marker in ["対応いただける", "お願いしたい", "お願いしたいです", "対応可能", "見ていただけ", "見てもらえ"])
    ):
        return "checkout_not_opening_scope_question"
    if (
        any(marker in combined for marker in ["機会損失", "取りこぼして", "毎日だいたい", "注文が来る", "早めに直したい"])
        and any(marker in combined for marker in ["対応可能", "対応可能ですか", "直したい"])
        and "Stripe" in combined
    ):
        return "general_bugfix_scope_question"
    if any(marker in combined for marker in ["10,000円", "10000円", "予算が厳しくて", "難しいですかね", "値引き"]):
        return "discount_request"
    if (
        any(marker in combined for marker in ["まだ購入はしてない", "自分でも試してから", "自分で直せなかったら", "またここから連絡"])
        and any(marker in combined for marker in ["Webhook", "送信テスト", "Stripe"])
    ):
        return "self_try_webhook_test_question"
    if (
        any(marker in combined for marker in ["見ていただくことは可能", "見ていただけますでしょうか", "見ていただける", "見てもらえる感じ", "見てもらえるんですよね", "見てもらえますか", "対応いただけるか教えて", "一度見てもらうことは可能", "対応いただけるか", "対応できる範囲", "このサービスで対応できる範囲"])
        and has_bugfix_stack_context
    ):
        return "general_bugfix_scope_question"
    if (
        has_bugfix_stack_context
        and any(
            marker in combined
            for marker in [
                "概要だけお伝えしても",
                "ご相談させていただければ",
                "お願いして良いものか",
                "ご迷惑でなければ",
                "概要だけお伝えしてもよろしいでしょうか",
            ]
        )
    ):
        return "outline_share_permission_question"
    if has_bugfix_stack_context and has_bugfix_surface:
        return "general_bugfix_scope_question"
    if (
        any(marker in combined for marker in ["5万円", "5万", "15000", "15,000", "安かろう悪かろう", "内容に差"])
        and any(marker in combined for marker in ["本当にちゃんと直りますか", "迷ってます", "迷っています", "率直にお聞きします"])
    ):
        return "price_trust_question"
    if (
        any(marker in combined for marker in ["他にも2件", "どこに頼むか迷って", "迷ってます", "迷っています", "強み"])
        and any(marker in combined for marker in ["全額返金", "返金", "直らなかった場合"])
    ):
        return "service_comparison_refund_question"
    if (
        any(marker in combined for marker in ["3つくらいのサービス", "比較してて", "比較している", "比較中"])
        and any(marker in combined for marker in ["強みって何ですか", "強みは何ですか", "強み"])
        and "Stripe" in combined
    ):
        return "service_comparison_strength_question"
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
    if any(marker in combined for marker in ["切り分けと修正可否", "動作確認まで含ま", "コードを修正して", "どこまでやってもらえる"]):
        return "general_bugfix_scope_question"
    if "直りますか" in combined and any(marker in combined for marker in ["で、結局", "結局これ"]):
        return "can_you_fix_direct"
    if has_bugfix_stack_context and any(marker in combined for marker in ["直せますか", "修正できますか"]):
        return "general_bugfix_scope_question"
    if any(
        marker in combined
        for marker in [
            "ChatGPT",
            "Cursor",
            "AIに任せるのが怖い",
            "人が見てくれる",
            "元のコードに戻してある",
            "AIに修正を任せた",
            "翌日には壊れて",
            "全部手作業でやり直しました",
            "品質管理",
            "壊れないような確認",
            "二度とああいう経験はしたくない",
        ]
    ):
        return "ai_fix_failure_reassurance_question"
    if (
        any(marker in combined for marker in ["再発しないような対策", "原因だけじゃなく", "対策まで含めて", "そういう範囲もカバー"])
        and "Stripe" in combined
    ):
        return "cause_and_prevention_scope_question"
    if (
        "price_not_found" in combined
        and any(marker in combined for marker in ["管理画面の設定", "設定が間違ってる", "自分で直せるなら", "お金かけずに"])
    ):
        return "price_not_found_self_fix_question"
    if (
        any(marker in combined for marker in ["支払い", "入金", "購入前"])
        and any(marker in combined for marker in ["先に", "支払い前", "入金前"])
        and any(marker in combined for marker in ["コード", "ログ", "原因"])
    ):
        return "prepayment_materials_before_payment"
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
            "3日後",
            "納品がある",
            "契約に影響",
            "納期感で対応可能",
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
        if "sendgrid_present" in facts_known and "additional_file_offer_present" in facts_known:
            direct_answer_line = "Stripeに関係する範囲であれば、SendGrid側の処理も今回の件として一緒に確認できる可能性があります。"
            blocking_missing_facts = ["stripe_related_file"]
            response_order = ["reaction", "direct_answer", "answer_detail", "ask"]
        elif "sendgrid_present" in facts_known and "stripe_utility_file_present" in facts_known:
            direct_answer_line = "Stripeに関係する範囲であれば、SendGrid側の処理も今回の件として一緒に確認できる可能性があります。"
            blocking_missing_facts = ["stripe_related_file"]
            response_order = ["reaction", "direct_answer", "answer_detail", "ask"]
        else:
            has_change_points = any(
                fact in facts_known for fact in ["payment_error_present", "email_notification_issue_present"]
            )
            if has_change_points:
                direct_answer_line = "同じ提案で進められるかは、決済エラーとメール通知が同じ原因かどうかを確認してからお返しします。"
                response_order = ["reaction", "direct_answer", "next_action"]
            else:
                blocking_missing_facts = ["change_points"]
                direct_answer_line = "同じ提案で進められるかは、追加したい内容が15,000円の範囲に収まるかを確認してからお返しします。"
                response_order = ["reaction", "direct_answer", "ask", "next_action"]
    elif scenario == "purchase_timing":
        direct_answer_line = "来週の購入でも大丈夫です。"
        response_order = ["reaction", "direct_answer", "answer_detail"]
    elif scenario == "prequote_extra_signal":
        direct_answer_line = "ありがとうございます。そのエラーも今回の件とあわせて確認対象です。"
        response_order = ["reaction", "direct_answer", "answer_detail", "next_action"]
    elif scenario == "service_comparison_refund_question":
        direct_answer_line = "このサービスは、Next.js / Stripe まわりの不具合をコードやログを見ながら切り分けて進めるのが軸です。"
        response_order = ["reaction", "direct_answer", "answer_detail", "next_action"]
    elif scenario == "service_comparison_strength_question":
        direct_answer_line = "強みは、Next.js / Stripe まわりの不具合をコードやログを見ながら切り分けて進めるところです。"
        response_order = ["reaction", "direct_answer", "answer_detail", "next_action"]
    elif scenario == "reissue_quote":
        direct_answer_line = "はい、同じ内容で再提案できます。"
        response_order = ["reaction", "direct_answer"]
    elif scenario == "risk_refund_question":
        direct_answer_line = "原因を特定できない場合や、修正済みファイルの返却まで進められない場合は、15,000円の正式納品として進めることはありません。"
        response_order = ["reaction", "direct_answer", "answer_detail", "next_action"]
    elif scenario == "payment_method":
        direct_answer_line = "支払い方法の表示はココナラ側の仕様によるため、こちらで選択肢を増やすことはできません。"
        response_order = ["reaction", "direct_answer", "answer_detail"]
    elif scenario == "dashboard_scope_question":
        direct_answer_line = "Webhook受信口に関係する範囲であれば、Stripeダッシュボード側の設定も確認対象です。"
        response_order = ["reaction", "direct_answer", "answer_detail", "next_action"]
    elif scenario == "prepayment_materials_before_payment":
        blocking_missing_facts = ["payment_completion"]
        direct_answer_line = "支払い前にコードやログを受け取って原因確認を進めることはしていません。"
        response_order = ["reaction", "direct_answer", "answer_detail", "next_action"]
    elif scenario == "extra_fee_fear":
        direct_answer_line = "今回の見積もりは15,000円の範囲で進める前提です。"
        response_order = ["reaction", "direct_answer", "answer_detail", "next_action"]
    elif scenario == "self_edit_fee_anxiety":
        direct_answer_line = "その場合でもまず今の状態を見て対応可否を確認できます。"
        response_order = ["reaction", "direct_answer", "answer_detail", "next_action"]
    elif scenario == "self_apply_support":
        direct_answer_line = "はい、今回の提案では、修正済みファイルをお渡しし、本番反映は依頼者様側で行っていただく形です。"
        response_order = ["reaction", "direct_answer", "answer_detail", "next_action"]
    elif scenario == "private_repo_share_question":
        direct_answer_line = "必ずリポジトリ全体を共有いただく必要はなく、不具合に関係する範囲からで大丈夫です。"
        response_order = ["reaction", "direct_answer", "answer_detail", "next_action"]
    elif scenario == "zip_share_question":
        direct_answer_line = "GitHubではなくZIPで送っていただいて大丈夫です。"
        response_order = ["reaction", "direct_answer", "answer_detail", "next_action"]
    elif scenario == "multi_symptom_same_cause_scope_question":
        direct_answer_line = "同じ原因なら、1回の購入としてまとめて確認できる場合があります。"
        response_order = ["reaction", "direct_answer", "answer_detail", "next_action"]
    elif scenario == "scope_constraints_question":
        direct_answer_line = f"はい、{fee_text}では今回の不具合1件を対象に、決済導線に関わる範囲を見ます。"
        response_order = ["reaction", "direct_answer", "answer_detail", "next_action"]
    elif scenario == "mixed_scope_fee_question":
        direct_answer_line = "決済ボタンの件は今回のサービスで確認できます。"
        response_order = ["reaction", "direct_answer", "answer_detail", "next_action"]
    elif scenario == "browser_vs_code_question":
        direct_answer_line = "どちらの可能性もありますが、ここではまだ片方に決め切らず、まずブラウザ差か実装側かを切り分けて見ます。"
        response_order = ["reaction", "direct_answer", "answer_detail", "next_action"]
    elif scenario == "code_vs_setting_scope_question":
        direct_answer_line = "原因がご自身のコード側でも、このサービスで確認できます。"
        response_order = ["reaction", "direct_answer", "answer_detail", "next_action"]
    elif scenario == "secret_key_value_question":
        direct_answer_line = "STRIPE_SECRET_KEY は通常 sk_live_ で始まりますが、値そのものは送らないでください。"
        response_order = ["reaction", "direct_answer", "answer_detail", "next_action"]
    elif scenario == "subscription_bug_scope_question":
        fit_level, _ = classify_capability_fit(raw)
        can_start = "まず確認できます" if fit_level == "cautious_fit" else "確認できます"
        if any(marker in raw for marker in ["コードでは対処できない", "コードで対処できない", "その判断だけでも"]):
            direct_answer_line = f"コードで対処できない結論になった場合でも、調査と切り分けを含めて {fee_text} です。"
        elif any(marker in raw for marker in ["1件分の料金", "収まりますか", "料金で収まりますか", "15,000円", "15000円", "もっとかかりますか", "済みますか"]):
            direct_answer_line = f"同じ原因の定期課金不具合として整理できる範囲なら、{fee_text} で進める形です。"
        elif any(marker in raw for marker in ["Laravel", "Cashier", "SDK"]):
            direct_answer_line = f"Laravel のサブスクリプション処理でも、{can_start}。"
        else:
            direct_answer_line = f"Stripeの定期課金まわりの不具合であれば、このサービスで{can_start}。"
        response_order = ["reaction", "direct_answer", "answer_detail", "next_action"]
    elif scenario == "ultra_short_fixability_question":
        direct_answer_line = "直せる可能性はあります。"
        blocking_missing_facts = ["symptom_surface"]
        response_order = ["reaction", "direct_answer", "ask"]
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
    elif scenario == "discount_request":
        direct_answer_line = f"今お出ししているご提案は{fee_text}固定で、10,000円への変更はしていません。"
        response_order = ["reaction", "direct_answer", "answer_detail", "next_action"]
    elif scenario == "self_try_webhook_test_question":
        direct_answer_line = "Stripe ダッシュボードに Webhook の送信テスト機能自体はあります。"
        response_order = ["reaction", "direct_answer", "answer_detail"]
    elif scenario == "response_speed_anxiety":
        direct_answer_line = "購入後は、まず受領確認と次の流れをお返しします。"
        response_order = ["reaction", "direct_answer", "answer_detail", "next_action"]
    elif scenario == "stage_only_before_fix_question":
        direct_answer_line = "追加で修正を頼むかどうかを、整理した内容を見てから判断する進め方はできます。"
        response_order = ["reaction", "direct_answer", "answer_detail", "next_action"]
    elif scenario == "feature_addition_scope_question":
        direct_answer_line = "新しい機能追加は、今回の不具合修正の範囲ではありません。"
        response_order = ["reaction", "direct_answer", "answer_detail"]
    elif scenario == "outline_share_permission_question":
        direct_answer_line = "概要だけでも、まず15,000円の範囲か確認できます。"
        response_order = ["reaction", "direct_answer", "answer_detail"]
    elif scenario == "auth_boundary_scope_question":
        direct_answer_line = "決済導線に関わる範囲として、まず確認できます。"
        response_order = ["reaction", "direct_answer", "answer_detail", "next_action"]
    elif scenario == "provider_unknown_scope_question":
        direct_answer_line = "こういう状態でも、まず相談できます。"
        response_order = ["reaction", "direct_answer", "answer_detail"]
    elif scenario == "cause_and_prevention_scope_question":
        direct_answer_line = "原因の確認に加えて、今回の不具合に対して再発しにくくするための対策まではあわせて見ます。"
        response_order = ["reaction", "direct_answer", "answer_detail", "next_action"]
    elif scenario == "ai_fix_failure_reassurance_question":
        if any(marker in raw for marker in ["品質管理", "壊れないような確認", "修正後に壊れない"]):
            direct_answer_line = "はい、現在のコードと症状を確認しながら進め、修正後の確認方法もあわせてお返しします。"
        else:
            direct_answer_line = "はい、現在のコードと症状を確認しながら進めます。"
        response_order = ["reaction", "direct_answer", "answer_detail", "next_action"]
    elif scenario == "price_not_found_self_fix_question":
        direct_answer_line = "price_not_found だけなら、price ID の設定ずれで起きることが多く、ご自身で直せる可能性があります。"
        response_order = ["reaction", "direct_answer", "answer_detail"]
    elif scenario == "can_you_fix_direct":
        direct_answer_line = "購入前の段階で必ず直るとまでは断定できませんが、今回の不具合として確認して進めます。"
        response_order = ["reaction", "direct_answer", "answer_detail", "next_action"]
    elif scenario == "secret_share_reassurance":
        direct_answer_line = "本番のURLをそのまま送っていただかなくても進められます。"
        response_order = ["reaction", "direct_answer", "answer_detail", "next_action"]
    elif scenario == "no_meeting_request":
        direct_answer_line = "Zoomや通話での進行はしていません。"
        response_order = ["reaction", "direct_answer", "answer_detail", "next_action"]
    elif scenario == "timeline_question":
        if "今日中" in raw:
            direct_answer_line = "購入後、まず調査結果を先にお返しして、今日中にどこまで確認できるかもあわせてお伝えします。"
        elif any(marker in raw for marker in ["3日後", "納品がある", "契約に影響", "納期感"]):
            direct_answer_line = "購入後、まず調査結果を先にお返しして、3日以内にどこまで進められるかもあわせてお伝えします。"
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
        "primary_question_id": contract["primary_question_id"],
        "primary_concern": build_primary_concern(source, scenario, facts_known),
        "buyer_emotion": infer_buyer_emotion(raw),
        "facts_known": facts_known,
        "blocking_missing_facts": blocking_missing_facts,
        "direct_answer_line": direct_answer_line,
        "response_order": response_order,
    }


def build_case_from_source(source: dict) -> dict:
    if is_handoff_source(source):
        raw = source.get("raw_message", "")
        return {
            "id": source.get("case_id") or source.get("id"),
            "src": source.get("route", "service"),
            "state": "quote_sent",
            "raw_message": raw,
            "summary": shared.derive_summary(source),
            "scenario": detect_handoff_quote_sent_scenario(raw),
            "temperature_plan": build_temperature_plan_for_case(source, "proposal_change"),
            "service_grounding": {
                "service_id": "handoff-25000",
                "public_service": False,
                "display_name": "AI/外注コードの主要1フロー整理・引き継ぎメモ作成",
                "fee_text": "25,000円",
            },
            "hard_constraints": {
                "service_id": "handoff-25000",
                "public_service_only": False,
                "answer_before_procedure": True,
                "ask_only_if_blocking": True,
            },
            "reply_stance": {
                "burden_owner": "us",
                "empathy_first": False,
                "reply_skeleton": "estimate_followup",
            },
            "reply_contract": {
                "primary_question_id": "q1",
                "explicit_questions": [{"id": "q1", "text": "handoff後に修正も続けて頼めるか", "priority": "primary"}],
                "answer_map": [{"question_id": "q1", "disposition": "answer_now", "answer_brief": "handoff continuation"}],
                "ask_map": [],
                "required_moves": ["react_briefly_first", "answer_directly_now"],
            },
            "response_decision_plan": {"direct_answer_line": "はい、整理のあとに修正が必要と分かった場合も、続けてご相談いただけます。"},
            "custom_rendered_reply": build_handoff_quote_sent_reply(source),
        }

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
                    "answer_brief": "同じ提案でいけるかは、追加された内容が15,000円の範囲に収まるかを見てからお返しします。",
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

    if scenario == "prequote_extra_signal":
        case["reply_contract"] = {
            "primary_question_id": "q1",
            "explicit_questions": [{"id": "q1", "text": "追記したエラーも確認対象になるか", "priority": "primary"}],
            "answer_map": [
                {
                    "question_id": "q1",
                    "disposition": "answer_now",
                    "answer_brief": "ありがとうございます。そのエラーも今回の件とあわせて確認対象です。",
                }
            ],
            "ask_map": [],
            "required_moves": ["react_briefly_first", "answer_directly_now"],
        }
        case["response_decision_plan"] = build_response_decision_plan(source, scenario, case["reply_contract"])
        return case

    if scenario == "service_comparison_refund_question":
        case["reply_contract"] = {
            "primary_question_id": "q1",
            "explicit_questions": [
                {"id": "q1", "text": "このサービスの強みは何か", "priority": "primary"},
                {"id": "q2", "text": "直らなかった場合に全額返金されるか", "priority": "secondary"},
            ],
            "answer_map": [
                {
                    "question_id": "q1",
                    "disposition": "answer_now",
                    "answer_brief": "このサービスは、Next.js / Stripe まわりの不具合をコードやログを見ながら切り分けて進めるのが軸です。",
                },
                {
                    "question_id": "q2",
                    "disposition": "answer_now",
                    "answer_brief": "購入前の段階で、全額返金になるかどうかをこちらから断定することはできません。",
                },
            ],
            "ask_map": [],
            "required_moves": ["react_briefly_first", "answer_directly_now"],
        }
        case["response_decision_plan"] = build_response_decision_plan(source, scenario, case["reply_contract"])
        return case

    if scenario == "service_comparison_strength_question":
        case["reply_contract"] = {
            "primary_question_id": "q1",
            "explicit_questions": [
                {"id": "q1", "text": "このサービスの強みは何か", "priority": "primary"},
            ],
            "answer_map": [
                {
                    "question_id": "q1",
                    "disposition": "answer_now",
                    "answer_brief": "強みは、Next.js / Stripe まわりの不具合をコードやログを見ながら切り分けて進めるところです。",
                },
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
                    "answer_brief": "原因を特定できない場合や、修正済みファイルの返却まで進められない場合は、15,000円の正式納品として進めることはありません。全額返金になるかどうかは、この時点でこちらから断定できません。",
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
                    "hold_reason": "まず購入画面に表示されている支払い方法の中から選んで進めてください。",
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

    if scenario == "prepayment_materials_before_payment":
        case["reply_contract"] = {
            "primary_question_id": "q1",
            "explicit_questions": [{"id": "q1", "text": "支払い前にコードやログを送れば原因だけ先に見てもらえるか", "priority": "primary"}],
            "answer_map": [
                {
                    "question_id": "q1",
                    "disposition": "answer_now",
                    "answer_brief": "支払い前にコードやログを受け取って原因確認を進めることはしていません。",
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
                    "answer_brief": "別原因が見つかった時点で状況を共有し、この金額内で修正完了まで進められない場合は、そこで止めてご説明します。",
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
            "explicit_questions": [
                {"id": "q1", "text": "修正済みファイルは自分で本番反映する形か", "priority": "primary"},
                {"id": "q2", "text": "デプロイ手順も教えてもらえるか", "priority": "secondary"},
            ],
            "answer_map": [
                {
                    "question_id": "q1",
                    "disposition": "answer_now",
                    "answer_brief": "はい、今回の提案では、修正済みファイルをお渡しし、本番反映は依頼者様側で行っていただく形です。",
                },
                {
                    "question_id": "q2",
                    "disposition": "answer_now",
                    "answer_brief": "Vercelのデプロイ手順も、修正ファイルと一緒に分かる形でお渡しします。",
                },
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

    if scenario == "scope_constraints_question":
        case["reply_contract"] = {
            "primary_question_id": "q1",
            "explicit_questions": [
                {"id": "q1", "text": "15,000円で見られる範囲に制約があるか", "priority": "primary"},
                {"id": "q2", "text": "Stripe部分だけに限るのか", "priority": "secondary"},
            ],
            "answer_map": [
                {
                    "question_id": "q1",
                    "disposition": "answer_now",
                    "answer_brief": f"{SERVICE_GROUNDING['fee_text']}では今回の不具合1件を対象に、決済導線に関わる範囲を見ます。",
                },
                {
                    "question_id": "q2",
                    "disposition": "answer_now",
                    "answer_brief": "Stripe部分だけに機械的に区切るのではなく、同じ原因の流れまでを基本の範囲として進めます。",
                },
            ],
            "ask_map": [],
            "required_moves": ["react_briefly_first", "answer_directly_now"],
        }
        case["response_decision_plan"] = build_response_decision_plan(source, scenario, case["reply_contract"])
        return case

    if scenario == "mixed_scope_fee_question":
        case["reply_contract"] = {
            "primary_question_id": "q1",
            "explicit_questions": [
                {"id": "q1", "text": "決済ボタンの不具合を見てもらえるか", "priority": "primary"},
                {"id": "q2", "text": "画像アップロードも一緒に見ると別料金になるか", "priority": "secondary"},
            ],
            "answer_map": [
                {
                    "question_id": "q1",
                    "disposition": "answer_now",
                    "answer_brief": "決済ボタンの件は今回のサービスで確認できます。",
                },
                {
                    "question_id": "q2",
                    "disposition": "answer_now",
                    "answer_brief": "画像アップロードの件は、決済と別原因なら別の相談として切り分けます。",
                },
            ],
            "ask_map": [],
            "required_moves": ["react_briefly_first", "answer_directly_now"],
        }
        case["response_decision_plan"] = build_response_decision_plan(source, scenario, case["reply_contract"])
        return case

    if scenario == "browser_vs_code_question":
        case["reply_contract"] = {
            "primary_question_id": "q1",
            "explicit_questions": [
                {"id": "q1", "text": "ブラウザの問題かコード側の問題か", "priority": "primary"},
            ],
            "answer_map": [
                {
                    "question_id": "q1",
                    "disposition": "answer_now",
                    "answer_brief": "どちらの可能性もありますが、ここではまだ片方に決め切らず、まずブラウザ差か実装側かを切り分けて見ます。",
                }
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
                    "answer_brief": "Stripeの定期課金まわりの不具合であれば、まず確認できます。",
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
                    "answer_brief": "はい、Stripeや決済まわりの不具合であれば、まず確認できます。",
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
                    "answer_brief": "Stripeのチェックアウトに進まない不具合であれば、まず確認できます。",
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

    if scenario == "discount_request":
        case["reply_contract"] = {
            "primary_question_id": "q1",
            "explicit_questions": [
                {"id": "q1", "text": "10,000円くらいで対応できるか", "priority": "primary"},
            ],
            "answer_map": [
                {
                    "question_id": "q1",
                    "disposition": "answer_now",
                    "answer_brief": f"今お出ししているご提案は{SERVICE_GROUNDING['fee_text']}固定で、10,000円への変更はしていません。",
                }
            ],
            "ask_map": [],
            "required_moves": ["react_briefly_first", "answer_directly_now"],
        }
        case["response_decision_plan"] = build_response_decision_plan(source, scenario, case["reply_contract"])
        return case

    if scenario == "self_try_webhook_test_question":
        case["reply_contract"] = {
            "primary_question_id": "q1",
            "explicit_questions": [
                {"id": "q1", "text": "Stripe ダッシュボードで Webhook の送信テストができるか", "priority": "primary"},
                {"id": "q2", "text": "自分で直せなければまたここから連絡してよいか", "priority": "secondary"},
            ],
            "answer_map": [
                {
                    "question_id": "q1",
                    "disposition": "answer_now",
                    "answer_brief": "Stripe ダッシュボードに Webhook の送信テスト機能自体はあります。",
                },
                {
                    "question_id": "q2",
                    "disposition": "answer_now",
                    "answer_brief": "ご自身で試してみて直らなければ、またこのままご連絡ください。",
                },
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

    if scenario == "feature_addition_scope_question":
        case["reply_contract"] = {
            "primary_question_id": "q1",
            "explicit_questions": [{"id": "q1", "text": "新しい機能追加も今回のサービスで見てもらえるか", "priority": "primary"}],
            "answer_map": [
                {
                    "question_id": "q1",
                    "disposition": "answer_now",
                    "answer_brief": "新しい機能追加は、今回の不具合修正の範囲ではありません。",
                }
            ],
            "ask_map": [],
            "required_moves": ["react_briefly_first", "answer_directly_now"],
        }
        case["response_decision_plan"] = build_response_decision_plan(source, scenario, case["reply_contract"])
        return case

    if scenario == "outline_share_permission_question":
        case["reply_contract"] = {
            "primary_question_id": "q1",
            "explicit_questions": [{"id": "q1", "text": "概要だけ伝えて相談してよいか", "priority": "primary"}],
            "answer_map": [
                {
                    "question_id": "q1",
                    "disposition": "answer_now",
                    "answer_brief": "概要だけでも、まず15,000円の範囲か確認できます。",
                }
            ],
            "ask_map": [],
            "required_moves": ["react_briefly_first", "answer_directly_now"],
        }
        case["response_decision_plan"] = build_response_decision_plan(source, scenario, case["reply_contract"])
        return case

    if scenario == "auth_boundary_scope_question":
        case["reply_contract"] = {
            "primary_question_id": "q1",
            "explicit_questions": [{"id": "q1", "text": "認証側か決済側か不明な症状でも見てもらえるか", "priority": "primary"}],
            "answer_map": [
                {
                    "question_id": "q1",
                    "disposition": "answer_now",
                    "answer_brief": "決済導線に関わる範囲として、まず確認できます。",
                }
            ],
            "ask_map": [],
            "required_moves": ["react_briefly_first", "answer_directly_now"],
        }
        case["response_decision_plan"] = build_response_decision_plan(source, scenario, case["reply_contract"])
        return case

    if scenario == "provider_unknown_scope_question":
        case["reply_contract"] = {
            "primary_question_id": "q1",
            "explicit_questions": [{"id": "q1", "text": "Stripeかどうか分からない状態でも相談可能か", "priority": "primary"}],
            "answer_map": [
                {
                    "question_id": "q1",
                    "disposition": "answer_now",
                    "answer_brief": "こういう状態でも、まず相談できます。",
                }
            ],
            "ask_map": [],
            "required_moves": ["react_briefly_first", "answer_directly_now"],
        }
        case["response_decision_plan"] = build_response_decision_plan(source, scenario, case["reply_contract"])
        return case

    if scenario == "cause_and_prevention_scope_question":
        case["reply_contract"] = {
            "primary_question_id": "q1",
            "explicit_questions": [
                {"id": "q1", "text": "原因確認だけでなく再発対策まで見てもらえるか", "priority": "primary"},
            ],
            "answer_map": [
                {
                    "question_id": "q1",
                    "disposition": "answer_now",
                    "answer_brief": "原因の確認に加えて、今回の不具合に対して再発しにくくするための対策まではあわせて見ます。",
                }
            ],
            "ask_map": [],
            "required_moves": ["react_briefly_first", "answer_directly_now"],
        }
        case["response_decision_plan"] = build_response_decision_plan(source, scenario, case["reply_contract"])
        return case

    if scenario == "ai_fix_failure_reassurance_question":
        case["reply_contract"] = {
            "primary_question_id": "q1",
            "explicit_questions": [{"id": "q1", "text": "AIで直そうとして失敗した状態でも、現在のコードを確認しながら見てもらえるか", "priority": "primary"}],
            "answer_map": [
                {
                    "question_id": "q1",
                    "disposition": "answer_now",
                    "answer_brief": "はい、現在のコードと症状を確認しながら進めます。",
                }
            ],
            "ask_map": [],
            "required_moves": ["react_briefly_first", "answer_directly_now"],
        }
        case["response_decision_plan"] = build_response_decision_plan(source, scenario, case["reply_contract"])
        return case

    if scenario == "price_not_found_self_fix_question":
        case["reply_contract"] = {
            "primary_question_id": "q1",
            "explicit_questions": [{"id": "q1", "text": "price_not_found が設定見直しだけで直る可能性があるか", "priority": "primary"}],
            "answer_map": [
                {
                    "question_id": "q1",
                    "disposition": "answer_now",
                    "answer_brief": "price_not_found だけなら、price ID の設定ずれで起きることが多く、ご自身で直せる可能性があります。",
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

    if scenario == "ultra_short_fixability_question":
        case["reply_contract"] = {
            "primary_question_id": "q1",
            "explicit_questions": [{"id": "q1", "text": "直せるか", "priority": "primary"}],
            "answer_map": [
                {
                    "question_id": "q1",
                    "disposition": "answer_now",
                    "answer_brief": "直せる可能性はあります。",
                }
            ],
            "ask_map": [
                {
                    "id": "a1",
                    "question_ids": ["q1"],
                    "ask_text": "どこで止まるかだけ教えてもらえますか。",
                    "why_needed": "切り分けの入口をそろえるため",
                }
            ],
            "required_moves": ["react_briefly_first", "answer_directly_now", "request_minimum_evidence"],
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
            return "決済エラーに加えてメール通知の件ですね。"
        return "提案後に変更したい点が出てきたとのことですね。"
    if scenario == "purchase_timing":
        if "バタバタ" in raw:
            return "お忙しいところ確認いただきありがとうございます。"
        return "購入タイミングについてのご相談ですね。"
    if scenario == "reissue_quote":
        return "期限切れの表示が出たとのことですね。"
    if scenario == "prequote_extra_signal":
        return "追記ありがとうございます。追加で出たエラーも承知しました。"
    if scenario == "service_comparison_refund_question":
        return "比較中で迷っているとのことですね。"
    if scenario == "service_comparison_strength_question":
        return "比較中で、サービスの違いも気になっているのですね。"
    if scenario == "risk_refund_question":
        if any(marker in raw for marker in ["返金", "原因が分からなかった", "直らなかった", "うまくいかなかった"]):
            return "直らなかった場合の扱いについてですね。"
        if "了解" in raw:
            return "金額の件、承知しました。"
        if "不安" in raw:
            return "即決のご不安、ごもっともです。"
        return "料金面のご心配ですね。"
    if scenario == "payment_method":
        if "コンビニ" in raw:
            return "購入画面で支払い方法が限られて見える状況ですね。"
        return "支払い方法の件ですね。"
    if scenario == "dashboard_scope_question":
        return "Webhook受信口に加えて、Stripeダッシュボード設定の件ですね。"
    if scenario == "prepayment_materials_before_payment":
        return "提案内容と、支払い前に原因だけ見てもらえるかの件ですね。"
    if scenario == "extra_fee_fear":
        return "金額が増えるのが不安という点を先に整理します。"
    if scenario == "self_edit_fee_anxiety":
        return "ご自身で触った影響もご不安とのことですね。"
    if scenario == "self_apply_support":
        return "ご自身で反映する場合のサポート範囲ですね。"
    if scenario == "private_repo_share_question":
        return "コード共有の方法がご不安とのことですね。"
    if scenario == "zip_share_question":
        return "ZIPでの共有方法が気になっている件ですね。"
    if scenario == "multi_symptom_same_cause_scope_question":
        return "似た症状が複数ある件ですね。"
    if scenario == "code_vs_setting_scope_question":
        return "コード側か設定側かが気になっている件ですね。"
    if scenario == "secret_key_value_question":
        return "STRIPE_SECRET_KEY の共有方法が気になっている件ですね。"
    if scenario == "subscription_bug_scope_question":
        if any(marker in raw for marker in ["プラン変更", "アップグレード", "旧プラン", "新プラン"]):
            return "プラン変更時に請求が重なる件ですね。"
        if "解約" in raw and "請求" in raw:
            return "解約後も請求が走っている件ですね。"
        return "定期課金の請求まわりでお困りとのことですね。"
    if scenario == "general_bugfix_scope_question":
        if any(marker in raw for marker in ["ぐるぐる", "先に進めない"]) and any(marker in raw for marker in ["買えない", "困って", "おきゃくさん"]):
            return "カード入力後に先へ進めずお困りとのことですね。"
        if any(marker in raw for marker in ["Stripe は対象外", "Stripeは対象外"]) and any(
            marker in raw for marker in ["見てもらえるんですよね", "見てもらえますか", "見てもらえる"]
        ):
            return "Stripe も見てもらえるかご不安とのことですね。"
        if any(marker in raw for marker in ["友人から紹介", "紹介されて来", "紹介されてき", "紹介されて来ました"]) and "カート" in raw and "消えない" in raw:
            return "ご紹介ありがとうございます。決済後にカートが残る件ですね。"
        if any(marker in raw for marker in ["機会損失", "取りこぼして", "毎日だいたい", "注文が来る"]):
            return "売上への影響が出ていてお急ぎとのことですね。"
        if any(marker in raw for marker in ["Prisma", "PlanetScale", "注文テーブル", "書き込み"]) and "Webhook" in raw:
            return "Webhook受信後の保存処理が止まる件ですね。"
        if any(marker in raw for marker in ["Vercel", "serverless functions", "10秒制限"]) and "Webhook" in raw:
            return "Webhookが届かなくなった件ですね。"
        if any(marker in raw for marker in ["React Native", "stripe-react-native", "@stripe/stripe-react-native"]):
            return "Androidだけ決済完了コールバックが返らない件ですね。"
        if any(marker in raw for marker in ["時間帯だけ", "深夜", "タイムアウト"]) and "Webhook" in raw:
            return "特定の時間帯だけWebhookが失敗する件ですね。"
        if any(marker in raw for marker in ["0円", "カート情報"]) and any(marker in raw for marker in ["Shopify", "Liquid"]):
            return "カート情報が渡らず0円で決済される件ですね。"
        if any(marker in raw for marker in ["Safari", "iOS"]) and "決済画面" in raw:
            return "iOSのSafariだけ決済画面が開かない件ですね。"
        if any(marker in raw for marker in ["Connect", "Destination Charge", "送金が動いていません", "送金が動いていない"]):
            return "接続先アカウントへの送金が動いていない件ですね。"
        if ("本番環境" in raw or "本番だけ" in raw) and any(marker in raw for marker in ["年額プラン", "月額プラン", "特定のプラン"]) and "500" in raw:
            return "本番の特定プランだけ500エラーになる件ですね。"
        if "payment_intent.succeeded" in raw and any(marker in raw for marker in ["Webhook", "届かなく", "届いていません"]):
            return "payment_intent.succeeded のWebhookが届かない件ですね。"
        if "たらい回し" in raw or "どこに頼めばいいか分から" in raw:
            return "たらい回しになっていてお困りとのことですね。"
        if ("特定の商品" in raw or "他の商品" in raw) and ("メール" in raw or "飛ばない" in raw):
            return "特定の商品だけ購入完了後のメールが飛ばない件ですね。"
        if ("本番に出した途端" in raw or "本番だけ" in raw) and ("エラー" in raw or "決済" in raw):
            return "本番でだけ決済時エラーが出る件ですね。"
        if any(marker in raw for marker in ["success URL", "/checkout に戻される"]) and "Checkout" in raw:
            return "Checkout 完了後に戻り先が崩れる件ですね。"
        if "メールが飛ばない" in raw:
            return "購入完了後のメールが飛ばない件ですね。"
        if "真っ白" in raw:
            return "決済完了後の画面が真っ白になる件ですね。"
        if "決済が通らなく" in raw:
            return "決済が通らなくなっている件ですね。"
        if any(marker in raw for marker in ["メールが行かない", "メールが届かない", "完了メールが届かない"]):
            return "決済完了後のメールが届かない件ですね。"
        if "直せますか" in raw and "Stripe" in raw:
            return "Stripe決済が動かない件ですね。"
        if "お支払い処理中にエラー" in raw:
            return "決済時エラーが出ている件ですね。"
        if any(marker in raw for marker in ["聞いていいですか", "見てもらえる感じ", "急にエラー"]) and "決済" in raw:
            return "決済エラーの件ですね。"
        return "決済まわりの不具合の件ですね。"
    if scenario == "scope_constraints_question":
        return "15,000円の範囲や制約が気になっている件ですね。"
    if scenario == "mixed_scope_fee_question":
        return "決済ボタンの件と別の不具合を一緒に相談したい件ですね。"
    if scenario == "browser_vs_code_question":
        return "iPhone の Safari だけ完了画面に進まない件ですね。"
    if scenario == "checkout_not_opening_scope_question":
        return "チェックアウト画面に進まなくなったとのことですね。"
    if scenario == "service_interruption_anxiety":
        return "作業中に環境が使えなくならないかご不安とのことですね。"
    if scenario == "price_trust_question":
        return "金額差があるとご不安になりますよね。"
    if scenario == "discount_request":
        return "ご予算の件も気になっているのですね。"
    if scenario == "self_try_webhook_test_question":
        return "購入前にご自身でも試したい件ですね。"
    if scenario == "response_speed_anxiety":
        return "購入後のレスポンスが気になっている件ですね。"
    if scenario == "stage_only_before_fix_question":
        return "整理だけで一度判断したい件ですね。"
    if scenario == "feature_addition_scope_question":
        return "プラン変更フォームの新規実装で詰まっている件ですね。"
    if scenario == "outline_share_permission_question":
        return "そのくらいの段階でも問題ありません。"
    if scenario == "auth_boundary_scope_question":
        return "認証側か決済側か切り分けたい件ですね。"
    if scenario == "provider_unknown_scope_question":
        return "カード決済ができなくなっている状況ですね。"
    if scenario == "ultra_short_fixability_question":
        return "Stripe と Webhook の件ですね。"
    if scenario == "cause_and_prevention_scope_question":
        return "原因確認に加えて再発対策まで含めたい件ですね。"
    if scenario == "ai_fix_failure_reassurance_question":
        return "何度か試してご不安になったとのことですね。"
    if scenario == "price_not_found_self_fix_question":
        return "price_not_found が出ている状況ですね。"
    if scenario == "can_you_fix_direct":
        return "ご不安な点ですね。"
    if scenario == "secret_share_reassurance":
        if "evt_" in raw:
            return "evt_... まで確認できているとのこと、ありがとうございます。"
        return "共有範囲についてのご不安ですね。"
    if scenario == "no_meeting_request":
        return "文章で伝えるのが大変とのことですね。"
    if scenario == "timeline_question":
        if "今日中" in raw:
            return "売上に直結していてお急ぎとのこと、まず優先して確認に入ります。"
        if any(marker in raw for marker in ["3日後", "納品がある", "契約に影響", "納期感"]):
            return "3日後の納品が迫っていてお急ぎとのことですね。"
        return "今週末の確認会に間に合わせたいとのことですね。"
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
    return "提案後のご連絡ですね。"


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
        if "sendgrid_present" in facts_known and "additional_file_offer_present" in facts_known:
            return [
                f"{direct_answer}\nStripe以外の別の原因まで広がる場合だけ、その時点で切り分けてお返しします。".strip(),
                "送り忘れていたファイルは、そのまま送ってください。",
            ]
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

    if scenario == "prequote_extra_signal":
        return [
            f"{direct_answer}\nNo signatures found matching the expected signature for payload が出ているなら、署名シークレットや署名検証まわりも含めて見ます。".strip(),
            purchase_closing(scenario, raw),
        ]

    if scenario == "reissue_quote":
        return [direct_answer]

    if scenario == "service_comparison_refund_question":
        return [
            f"{direct_answer}\n価格だけで作業内容を削っているわけではありません。".strip(),
            "ただ、購入前の段階で「必ず直る」や全額返金までは先に断定できません。原因を特定できず、修正方針にもつながらない状態のまま正式納品として進めることはありません。",
            purchase_closing(scenario, raw),
        ]
    if scenario == "service_comparison_strength_question":
        return [
            f"{direct_answer}\n今回も、まず症状と前提を整理してから進めます。".strip(),
            "必要以上に広げず、今回の不具合1件として切り分けて進めるのが基本です。",
            purchase_closing(scenario, raw),
        ]

    if scenario == "risk_refund_question":
        paragraphs = [
            f"{direct_answer}\n{grounding.get('proposal_scope', '')}".strip(),
            "その場合は、分かった範囲をお伝えし、キャンセルを含めてご相談します。",
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

    if scenario == "prepayment_materials_before_payment":
        return [
            f"{direct_answer}\n原因確認や作業は、ご購入後に始めます。".strip(),
            "ご購入後にコードやログを送ってください。受領後、原因確認から進めます。",
            "この内容で問題なければ、お支払い完了後にトークルームで必要情報を送ってください。",
        ]

    if scenario == "extra_fee_fear":
        return [
            f"{direct_answer}\n確認の結果、別原因が複数あり、この金額内では修正完了まで進められないと分かった場合は、そこで止めてご説明します。".strip(),
            "勝手に料金が増えたり、そのまま追加作業へ進むことはありません。",
            "その場合は、キャンセル扱いを含めて、ココナラ上の手続きに沿ってご相談します。",
            "この前提でよければ、そのままご購入ください。",
        ]

    if scenario == "self_edit_fee_anxiety":
        return [
            f"{direct_answer}\n自分で触ったことだけを理由に追加料金が決まるわけではなく、必要なら状況を見てから事前にご相談します。".strip(),
            purchase_closing(scenario, raw),
        ]

    if scenario == "self_apply_support":
        return [
            f"{direct_answer}\nVercelのデプロイ手順も、修正ファイルと一緒に分かる形でお渡しします。".strip(),
            "この内容で問題なければ、そのままご購入いただいて大丈夫です。",
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

    if scenario == "outline_share_permission_question":
        return [
            direct_answer,
            "まずは今見えている症状や、どこで止まるかを分かる範囲でそのまま送ってください。",
        ]

    if scenario == "provider_unknown_scope_question":
        return [
            direct_answer,
            "まず現在のカード決済が Stripe かどうかも含めて確認します。",
            "Stripe ではない場合は、その時点で切り分けてご案内します。",
        ]

    if scenario == "ultra_short_fixability_question":
        return [
            direct_answer,
            "どこで止まるかだけ教えてもらえますか。",
        ]

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

    if scenario == "discount_request":
        return [
            direct_answer,
            f"ご予算の事情は分かりますが、今回は {SERVICE_GROUNDING['fee_text']} の公開条件でご案内しています。",
            "今回の不具合1件として整理できる範囲なら、その前提で確認します。",
            purchase_closing(scenario, raw),
        ]

    if scenario == "self_try_webhook_test_question":
        return [
            direct_answer,
            "ご自身で試してみて直らなければ、またこのままご連絡ください。",
        ]

    if scenario == "response_speed_anxiety":
        return [
            f"{direct_answer}\n確認に時間がかかる場合も、何日も無反応のまま止める進め方にはしません。".strip(),
            "途中で見えてきたことや次の見通し、連絡目安もその時点でお返しします。",
            purchase_closing(scenario, raw),
        ]

    if scenario == "stage_only_before_fix_question":
        return [
            f"{direct_answer}\nまず整理した内容を見て、そのあとで追加対応が必要かを判断いただければ大丈夫です。".strip(),
        ]

    if scenario == "feature_addition_scope_question":
        return [
            f"{direct_answer}\n今の決済自体が動いているなら、今回は既存不具合の修正ではなく新しい実装の相談になります。".strip(),
            "この不具合修正サービスでは、この内容だけでの購入案内はしていません。",
            "必要であれば、実装したい内容を別の相談として整理します。",
        ]

    if scenario == "auth_boundary_scope_question":
        return [
            direct_answer,
            "NextAuth のバージョン更新後という前提も含めて、まず認証側か決済側かを切り分けます。",
            "認証側だけの問題なら、その時点で切り分けてご相談します。",
            purchase_closing(scenario, raw),
        ]

    if scenario == "scope_constraints_question":
        return [
            direct_answer,
            "Stripe部分だけに機械的に区切るのではなく、同じ原因の流れまでを基本の範囲として進めます。",
            "別原因や別機能まで広がる場合だけ、その時点で事前にご相談します。",
            purchase_closing(scenario, raw),
        ]

    if scenario == "mixed_scope_fee_question":
        return [
            direct_answer,
            "画像アップロードの件は、同じ原因でつながっている場合だけ今回の流れで見ます。",
            "決済とは別原因なら、別の相談として切り分けます。",
            purchase_closing(scenario, raw),
        ]

    if scenario == "browser_vs_code_question":
        paragraphs = [
            direct_answer,
            "iPhone の Safari だけ起きる症状なら、ブラウザ差と実装側のどちらが強いかを切り分けながら確認します。",
            "この件も今回のサービスでまず確認できます。",
        ]
        if any(marker in raw for marker in ["非エンジニア", "Bubble", "分からない"]):
            paragraphs.append("分かる範囲の情報からで大丈夫です。")
        paragraphs.append(purchase_closing(scenario, raw))
        return paragraphs

    if scenario == "ai_fix_failure_reassurance_question":
        paragraphs = [
            direct_answer,
            "AIにそのまま任せて書き換える形ではなく、元に戻してある今の状態を基準に確認します。",
        ]
        if any(marker in raw for marker in ["品質管理", "壊れないような確認", "修正後に壊れない"]):
            paragraphs.append("壊れないことを先に保証する形ではありませんが、修正後に確認すべき点も含めてお返しします。")
        paragraphs.append(purchase_closing(scenario, raw))
        return paragraphs

    if scenario == "cause_and_prevention_scope_question":
        return [
            direct_answer,
            "購入後に、処理中のまま固まる条件と原因を確認したうえで、今の流れに対して取りやすい対策まで整理します。",
            "別の機能追加や大きな作り替えまで広がる場合だけ、その時点で事前にご相談します。",
            purchase_closing(scenario, raw),
        ]

    if scenario == "price_not_found_self_fix_question":
        return [
            direct_answer,
            "まずはコードで参照している price ID と、Stripe 管理画面上の対象 price が一致しているかを見直してみてください。",
            "それでも分からない場合は、その時点でこの件として確認できます。",
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
        if any(marker in raw for marker in ["3日後", "納品がある", "契約に影響", "納期感"]):
            detail = "3日以内に修正まで進められるかは見てからの判断ですが、難しい場合でも確認できたところから先にお返しします。"
            if any(marker in raw for marker in ["本番", "テスト環境", "テスト"]) and "エラー" in raw:
                detail = f"{detail}\n本番だけでテスト環境は通る前提なら、環境差も優先して見ます。"
            return [
                direct_answer,
                detail,
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
    custom_rendered_reply = case.get("custom_rendered_reply")
    if custom_rendered_reply:
        return custom_rendered_reply

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
