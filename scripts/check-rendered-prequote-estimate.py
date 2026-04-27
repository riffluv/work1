#!/usr/bin/env python3
from __future__ import annotations

import argparse
import importlib.util
import re
import sys
from pathlib import Path

from reply_quality_lint_common import collect_quality_style_errors

ROOT_DIR = Path(__file__).resolve().parents[1]
RENDERER_PATH = ROOT_DIR / "scripts/render-prequote-estimate-initial.py"


def load_renderer_module():
    spec = importlib.util.spec_from_file_location("render_prequote_estimate_initial", RENDERER_PATH)
    if spec is None or spec.loader is None:
        raise RuntimeError(f"failed to load renderer: {RENDERER_PATH}")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def has_any(text: str, needles: list[str]) -> bool:
    return any(needle in text for needle in needles)


def has_template_quote_drift(rendered: str) -> bool:
    if "とのことでした" not in rendered:
        return False
    before = rendered.split("とのことでした", 1)[0]
    topic = before.splitlines()[-1].strip()
    return "..." in topic or len(topic) >= 32


def has_concrete_prequote_context(text: str) -> bool:
    lower_text = text.lower()
    if "プラン変更" in text and has_any(text, ["支払いは完了", "決済は完了"]) and has_any(text, ["反映され", "変わっていません"]):
        return True
    if "405" in text and "Vercel" in text and has_any(text, ["POST", "post", "Checkout", "セッション作成"]):
        return True
    if "webhook" in lower_text and has_any(text, ["プレビュー環境", "preview環境", "STRIPE_WEBHOOK_SECRET", "evt_"]):
        return True
    if "webhook" in lower_text and "Vercel" in text and has_any(text, ["400", "署名検証", "endpoint", "環境変数", "Route Handler"]):
        return True
    if has_any(text, ["フロントエンド", "フロント"]) and "Stripe" in text and has_any(text, ["2つ", "管理画面", "ポップアップ"]):
        return True
    if any(marker in text for marker in ["request.text", "stripe-signature", "raw body"]):
        return True
    if "customer.subscription.updated" in text and any(marker in text for marker in ["DB", "ダウングレード", "アップグレード"]):
        return True
    if any(marker in text for marker in ["外注", "引き継ぎ", "コードの中身"]) and any(
        marker in text for marker in ["決済", "不具合", "Webhook", "webhook"]
    ):
        return True
    if any(marker in text for marker in ["メールが2通", "メールが二通", "二重送信", "2通飛ぶ"]) and any(
        marker in text for marker in ["customer.subscription.deleted", "同じイベント", "冪等", "idempot"]
    ):
        return True
    if any(marker in text for marker in ["coupon", "クーポン", "クーポンコード"]) and any(
        marker in text for marker in ["resource_missing", "Checkout Session", "セッション作成"]
    ):
        return True
    if "customer.subscription.updated" in text and "quantity" in text and any(marker in text for marker in ["例外", "エラー", "ハンドラ"]):
        return True
    if "お客さん" in text and "購入履歴" in text and "どう対応" in text:
        return True
    if any(marker in text for marker in ["100%直せ", "原因が特定", "どのくらいの割合"]):
        return True
    return False


def has_generic_prequote_template_fallback(rendered: str, raw: str) -> bool:
    if not has_concrete_prequote_context(raw):
        return False
    return (
        "内容ありがとうございます" in rendered
        and "この不具合なら15,000円で進められます" in rendered
        and "まずはこの不具合がどこで止まっているかを確認します" in rendered
    )


def has_old_three_point_template(rendered: str) -> bool:
    return (
        "内容ありがとうございます" in rendered
        and "この不具合なら15,000円" in rendered
        and "どこで止まっているか" in rendered
    )


def has_service_structure_question(text: str) -> bool:
    return has_any(
        text,
        [
            "5分",
            "難易度",
            "他サービス",
            "返金",
            "キャンセル",
            "保証期間",
            "保証",
            "今日中",
            "何時間",
            "いつ復旧",
            "100%直せ",
            "原因特定",
            "仕様",
            "不具合ですか",
            "対象",
            "見てもらえますか",
            "追加料金",
            "値引",
            "お試し",
        ],
    )


def has_non_stripe_provider(text: str) -> bool:
    return has_any(text, ["PayPay", "paypay", "GMO", "Square", "PayPal", "paypal"])


def collect_prequote_r0_stability_errors(rendered: str, raw: str) -> list[str]:
    errors: list[str] = []

    if has_old_three_point_template(rendered) and has_service_structure_question(raw):
        errors.append("prequote r0 guard failed: service-structure question fell back to old generic bug intake template")

    if has_non_stripe_provider(raw):
        accepts_broadly = has_any(rendered, ["この不具合なら15,000円で対応できます", "この不具合なら15,000円で進められます", "15,000円で対応できます"])
        has_boundary = has_any(rendered, ["Next.js側", "Webhook/API", "Webhook", "API受信", "受信処理", "決済サービス側", "全体ではなく"])
        if accepts_broadly and not has_boundary:
            errors.append("prequote r0 guard failed: non-Stripe provider was accepted without Next.js/Webhook/API boundary")

    if has_any(raw, ["今日中", "何時間", "いつ復旧", "いつ直", "すぐ復旧"]):
        if "48時間以内" in rendered and not has_any(rendered, ["復旧時間", "保証ではありません", "お約束できません", "約束できません"]):
            errors.append("prequote r0 guard failed: emergency timeline may confuse first-result ETA with recovery guarantee")
        if has_any(rendered, ["今日中に復旧できます", "必ず復旧", "すぐ復旧できます"]):
            errors.append("prequote r0 guard failed: emergency recovery time is overpromised")

    if has_any(raw, ["返金", "キャンセル"]) and has_any(rendered, ["返金します", "返金できます", "キャンセルできます", "全額返金"]):
        errors.append("prequote r0 guard failed: refund/cancel outcome is overpromised")

    if has_any(raw, ["保証期間", "保証"]) and has_any(rendered, ["無料保証", "保証します", "必ず直します"]):
        errors.append("prequote r0 guard failed: warranty is overpromised")

    if has_any(rendered, ["トークルーム内", "作業中", "納品します"]):
        errors.append("prequote r0 guard failed: prequote reply uses post-purchase phase vocabulary")

    return errors


def has_technical_cancel_context(text: str) -> bool:
    return "キャンセル" in text and has_any(
        text,
        [
            "Customer Portal",
            "subscription",
            "サブスク",
            "cancelUrl",
            "customer.subscription",
            "解約フロー",
            "キャンセルフロー",
            "キャンセル処理",
            "定期課金",
        ],
    )


def has_transaction_cancel_misroute(rendered: str, raw: str) -> bool:
    if not has_technical_cancel_context(raw):
        return False
    if has_any(rendered, ["Webhook", "Customer Portal", "サブスク", "定期課金", "subscription", "cancelUrl", "customer.subscription"]):
        return False
    return has_any(rendered, ["返金", "途中キャンセル", "取引キャンセル", "作業済み範囲", "ココナラ上の手続き"])


def has_prequote_solution_request(text: str) -> bool:
    if "調べるだけ" in text and not has_any(text, ["対処法", "どうやって直す", "どう直す"]):
        return False
    if has_any(text, ["直し方は分からない", "直し方が分からない", "直し方はわからない", "直し方がわからない"]):
        return False
    return has_any(text, ["対処法", "直し方", "どうやって直す", "どう直す"]) and has_any(
        text,
        ["教えて", "自分で直せ", "だけ"],
    )


def has_solution_request_nonanswer(rendered: str, raw: str) -> bool:
    if not has_prequote_solution_request(raw):
        return False
    if not has_any(rendered, ["購入前"]):
        return True
    return not has_any(rendered, ["具体的な修正手順", "コード上の直し方", "直し方までは"])


def has_budget_completion_gate_context(text: str) -> bool:
    price_or_budget = has_any(
        text,
        [
            "15,000円",
            "15000円",
            "1万5千円",
            "30,000円",
            "30000円",
            "3万",
            "予算",
            "追加費用",
            "追加料金",
            "2件",
            "２件",
            "2つ",
            "二つ",
            "複数",
            "3本",
            "三本",
            "×3",
            "x3",
            "1件15,000円×3",
            "1件15000円×3",
        ],
    )
    completion_risk = has_any(
        text,
        [
            "追加費用が怖",
            "追加料金が怖",
            "金額が増え",
            "返金",
            "無駄になら",
            "原因不明",
            "直せなかった",
            "直らなかった",
            "解決しなかった",
            "解決しない",
            "修正範囲が広",
            "範囲が広",
            "2件だった",
            "２件だった",
            "2件だと",
            "２件だと",
            "2つがあります",
            "両方一緒",
            "全部見てもらって",
            "全部見て",
            "全部直して",
            "3本とも",
            "三本とも",
            "念のため3本",
            "3件分",
            "1件15,000円×3",
            "1件15000円×3",
            "15,000円×3",
            "15000円×3",
        ],
    )
    return price_or_budget and completion_risk


def collect_budget_completion_gate_errors(rendered: str, raw: str) -> list[str]:
    if not has_budget_completion_gate_context(raw):
        return []
    errors: list[str] = []
    if not has_any(rendered, ["勝手に料金", "勝手に費用", "自動で料金", "自動で費用", "そのまま追加作業"]):
        errors.append("budget_completion_gate failed: rendered text does not block automatic fee/additional work")
    if not has_any(rendered, ["修正完了", "正式納品", "修正済みファイル"]):
        errors.append("budget_completion_gate failed: rendered text does not include the unfinished-work completion gate")
    if has_any(raw, ["2件", "２件", "2つ", "二つ", "複数", "両方", "3本", "三本", "×3", "3件"]) and not has_any(rendered, ["同じ原因", "別原因", "1件"]):
        errors.append("budget_completion_gate failed: multi-issue budget concern does not explain same/different cause handling")
    if has_any(raw, ["返金", "キャンセル"]) and has_any(rendered, ["返金します", "返金できます", "キャンセルできます", "全額返金"]):
        errors.append("budget_completion_gate failed: refund/cancel handling is overpromised")
    if has_any(raw, ["全部", "全体"]) and not has_any(rendered, ["断定できません", "断定できない", "1件に絞"]):
        errors.append("budget_completion_gate failed: broad budget-capped request is not narrowed before proceeding")
    return errors


def has_fix_vs_structure_first_context(text: str) -> bool:
    if not has_any(text, ["修正", "直す", "直して"]):
        return False
    if not has_any(text, ["整理", "コード全体", "全体を理解", "把握", "リファクタ"]):
        return False
    return has_any(text, ["どっち", "どちら", "先に", "先か", "まず"])


def collect_fix_vs_structure_first_errors(rendered: str, raw: str) -> list[str]:
    if not has_fix_vs_structure_first_context(raw):
        return []
    errors: list[str] = []
    if not has_any(rendered, ["まず", "不具合修正", "直したいところ"]):
        errors.append("fix_vs_structure_first failed: rendered text does not answer whether repair or structure should come first")
    if not has_any(rendered, ["整理"]) or not has_any(rendered, ["前提ではなく", "範囲とは分け", "別作業"]):
        errors.append("fix_vs_structure_first failed: rendered text does not separate code-structure work from bugfix scope")
    if has_private_service_leak(rendered):
        errors.append("fix_vs_structure_first failed: rendered text leaked private handoff wording")
    return errors


def needs_screenshot_guidance(question_text: str) -> bool:
    return "スクショ" in question_text or ("画面" in question_text and any(marker in question_text for marker in ["送", "見せ", "撮"]))


def is_private_service_case(case: dict) -> bool:
    service_id = case.get("service_id")
    return bool(service_id and service_id != "bugfix-15000")


def is_private_public_boundary_case(source: dict, normalized: dict) -> bool:
    if not is_private_service_case(normalized):
        return False
    service_hint = source.get("service_hint")
    return service_hint == "boundary"


def has_private_service_leak(rendered: str) -> bool:
    return has_any(rendered, ["handoff-25000", "25,000円", "25000円", "25,000円側", "整理側", "主要1フロー"])


def lint_case(module, case: dict) -> list[str]:
    normalized = case if case.get("reply_contract") else module.build_case_from_source(case)
    rendered = module.render_case(normalized)
    if is_private_service_case(normalized):
        if is_private_public_boundary_case(case, normalized) and has_private_service_leak(rendered):
            return ["private service leakage failed: public boundary prequote rendered private handoff wording"]
        return []
    contract = normalized["reply_contract"]
    temperature_plan = normalized.get("temperature_plan") or {}
    primary_id = contract["primary_question_id"]
    primary = next(item for item in contract["answer_map"] if item["question_id"] == primary_id)
    primary_question_type = primary.get("question_type")
    question_map = {item["id"]: item["text"] for item in contract["explicit_questions"]}
    errors: list[str] = []

    if not temperature_plan:
        errors.append("temperature_plan is missing")
    custom_render_scenarios = {
        "budget_completion_gate",
        "fix_vs_structure_first",
        "public_structure_scope_boundary",
        "no_concrete_bug_anxiety",
        "multi_site_non_stripe_scope",
        "plan_change_payment_not_reflected",
        "production_checkout_post_405",
        "preview_webhook_env_error",
        "vercel_webhook_signature_400",
        "frontend_stripe_mixed_scope",
        "stripe_webhook_raw_body_signature",
        "stripe_subscription_upgrade_db_update",
        "code_handoff_bugfix_scope",
        "email_duplicate_idempotency",
        "coupon_resource_missing",
        "subscription_quantity_update_exception",
        "customer_payment_access_response",
        "success_rate_or_guarantee_question",
        "non_stripe_webhook_scope",
        "emergency_recovery_time",
        "spec_vs_bug_boundary",
        "refund_cancel_prequote",
        "feature_addon_scope",
    }
    is_custom_render = normalized.get("scenario") in custom_render_scenarios
    is_custom_budget_completion = normalized.get("scenario") == "budget_completion_gate"

    if not normalized.get("render_payload") and not is_custom_render:
        errors.append("render_payload is missing")
    if normalized.get("render_payload_violations"):
        for violation in normalized["render_payload_violations"]:
            errors.append(f"render payload validator violation: {violation}")

    if primary["disposition"] == "answer_now":
        direct_acceptance_markers = ["15,000円", "対応できます", "対応できる"]
        if primary_question_type == "service_selection":
            direct_acceptance_markers.extend(["まずこの不具合対応から入るのが近い", "まずこの不具合対応から"])
        if primary_question_type == "investigation_only":
            direct_acceptance_markers.extend(["調べるだけでも大丈夫です", "原因の調査から対応"])
        if primary_question_type == "solution_only":
            direct_acceptance_markers.extend(["購入前に具体的な修正手順", "コード上の直し方までは", "購入前は症状"])
        if primary_question_type == "refund_policy":
            direct_acceptance_markers.extend(["返金や途中キャンセル", "正式納品へ進めることはありません", "キャンセルを含めて"])
        if not has_any(rendered, direct_acceptance_markers):
            errors.append("primary answer_now case is missing direct acceptance language")
    if primary["disposition"] == "answer_after_check" and not is_custom_render:
        if not has_any(
            rendered,
            [
                "断定しにくい",
                "断定しません",
                "確認できます",
                "見てから判断",
                "言い切るより",
                "見てから案内",
                "言い切りにくい",
                "判断できます",
                "まず何が起きているかを確認する",
                "まず必要な情報を見てから判断",
                "まず困っている点から見ていく",
                "この入口から見ていけます",
                "今の情報だけではまだ判断し切れない",
                "追加情報を受領したあとに",
                "この内容も確認できますが",
            ],
        ):
            errors.append("primary answer_after_check case is missing defer language")
        if not contract.get("ask_map"):
            errors.append("primary answer_after_check case has no ask_map")
    if contract.get("ask_map") and not is_custom_render and not has_any(rendered, ["教えてください", "送ってください", "ください"]):
        errors.append("ask_map exists but rendered text has no ask request")
    if any(ask.get("default_path_text") for ask in contract.get("ask_map") or []) and not is_custom_render:
        if not has_any(rendered, ["なければ", "難しければ", "決まっていなければ", "すぐ出せなければ", "まだ絞れていなければ"]):
            errors.append("optional ask exists but rendered text has no default-path language")

    forbidden_terms = [
        "GitHubに招待",
        "Driveに置いて",
        "Dropbox",
        "外部決済",
        "無料で対応",
        "sk_live_",
        "whsec_",
    ]
    for term in forbidden_terms:
        if term in rendered:
            errors.append(f"forbidden term leaked into rendered text: {term}")

    for answer in contract["answer_map"]:
        qtext = question_map.get(answer["question_id"], "")
        if ".env" in qtext or "APIキー" in qtext:
            if not has_any(rendered, [".env", "キー名だけ"]):
                errors.append("secret sharing question exists but rendered text does not block raw secret sharing")
        if needs_screenshot_guidance(qtext):
            if not has_any(rendered, ["スクショ", "画面"]):
                errors.append("screenshot question exists but rendered text does not mention screenshot guidance")
        if "税込" in qtext:
            if not has_any(rendered, ["ココナラ画面", "表示される金額"]):
                errors.append("tax question exists but rendered text does not answer displayed price directly")
        if "今週中" in qtext or "今日中" in qtext or "何日" in qtext or "いつ" in qtext:
            if not has_any(rendered, ["納期", "見通し"]):
                errors.append("timeline question exists but rendered text does not mention timing follow-up")
        if "不正アクセス" in qtext:
            if "不正アクセスかどうかは" not in rendered:
                errors.append("security question exists but rendered text does not defer security judgment explicitly")
        if has_any(qtext, ["直接会って", "Zoom", "通話"]):
            if not has_any(rendered, ["トークルーム", "テキスト", "Zoomではなく", "通話やZoomではなく"]):
                errors.append("meeting request exists but rendered text does not keep text-only boundary")
        if "もっと安く" in qtext or "安くなりますか" in qtext:
            if not has_any(rendered, ["15,000円で固定", "15,000円", "公開サービス"]):
                errors.append("discount question exists but rendered text does not keep fixed-price boundary")

    raw_message = normalized.get("raw_message", "")
    if has_template_quote_drift(rendered):
        errors.append("template_quote_drift failed: long buyer quote plus `とのことでした` survived")
    if has_generic_prequote_template_fallback(rendered, raw_message):
        errors.append("generic_prequote_template failed: concrete buyer context fell back to old generic 15,000 yen stop-check template")
    errors.extend(collect_prequote_r0_stability_errors(rendered, raw_message))
    if has_transaction_cancel_misroute(rendered, raw_message):
        errors.append("cancel_word_misroute failed: technical cancel wording was treated as transaction cancellation")
    if has_solution_request_nonanswer(rendered, raw_message):
        errors.append("prequote_solution_request failed: solution-only request did not keep purchase-before boundary")
    errors.extend(collect_budget_completion_gate_errors(rendered, raw_message))
    errors.extend(collect_fix_vs_structure_first_errors(rendered, raw_message))

    if (
        "価値があるか" in raw_message
        or "内容に差があるなら" in raw_message
        or (
            re.search(r"(^|[^0-9])5,000円", raw_message)
            and not has_any(raw_message, ["5,000円とか", "5,000円くらい", "10,000円", "もっと安く", "値引", "お試し"])
        )
    ):
        if not has_any(rendered, ["今の公開サービス", "断定しにくい", "案内できる範囲"]):
            errors.append("value comparison case exists but rendered text does not keep service-boundary framing")

    errors.extend(collect_quality_style_errors(rendered))
    return errors


def main() -> int:
    parser = argparse.ArgumentParser(description="Lint rendered estimate_initial replies against minimal structural checks.")
    parser.add_argument("--fixture", required=True)
    parser.add_argument("--case-id")
    parser.add_argument("--limit", type=int)
    args = parser.parse_args()

    module = load_renderer_module()
    cases = module.load_cases(Path(args.fixture))
    if args.case_id:
        cases = [case for case in cases if case.get("id") == args.case_id or case.get("case_id") == args.case_id]
    if args.limit is not None:
        cases = cases[: args.limit]
    if not cases:
        print("[NG] no cases selected")
        return 1

    had_error = False
    checked = 0
    for case in cases:
        normalized = case if case.get("reply_contract") else module.build_case_from_source(case)
        if normalized.get("state") != "prequote":
            continue
        if normalized.get("reply_stance", {}).get("reply_skeleton") != "estimate_initial":
            continue
        checked += 1
        errors = lint_case(module, case)
        if errors:
            had_error = True
            case_id = normalized.get("id", "<unknown>")
            for error in errors:
                print(f"[NG] {case_id}: {error}")

    if had_error:
        return 1
    print(f"[OK] rendered estimate_initial lint passed: {checked} case(s)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
