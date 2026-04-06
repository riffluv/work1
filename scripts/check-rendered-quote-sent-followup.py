#!/usr/bin/env python3
from __future__ import annotations

import argparse
import importlib.util
from pathlib import Path

from reply_quality_lint_common import (
    collect_quality_style_errors,
    collect_reasoning_preservation_errors,
    collect_temperature_constraint_errors,
)

ROOT_DIR = Path(__file__).resolve().parents[1]
RENDERER_PATH = ROOT_DIR / "scripts/render-quote-sent-followup.py"


def load_renderer():
    spec = importlib.util.spec_from_file_location("render_quote_sent_followup", RENDERER_PATH)
    if spec is None or spec.loader is None:
        raise RuntimeError(f"failed to load renderer: {RENDERER_PATH}")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def has_any(text: str, needles: list[str]) -> bool:
    return any(needle in text for needle in needles)


def lint_case(module, source: dict) -> list[str]:
    case = module.build_case_from_source(source)
    rendered = module.render_case(case)
    temperature_plan = case.get("temperature_plan") or {}
    decision_plan = case.get("response_decision_plan") or {}
    service_grounding = case.get("service_grounding") or {}
    hard_constraints = case.get("hard_constraints") or {}
    primary = case["reply_contract"]["answer_map"][0]
    scenario = case.get("scenario")
    raw = source.get("raw_message", "")
    errors: list[str] = []

    if not temperature_plan:
        errors.append("temperature_plan is missing")
    if not decision_plan:
        errors.append("response_decision_plan is missing")
    else:
        for field in ["primary_concern", "facts_known", "blocking_missing_facts", "direct_answer_line", "response_order"]:
            if field not in decision_plan:
                errors.append(f"response_decision_plan missing required field: {field}")
        if decision_plan.get("primary_concern") == scenario:
            errors.append("primary_concern is still just the scenario label")

    if not service_grounding:
        errors.append("service_grounding is missing")
    else:
        if service_grounding.get("service_id") != "bugfix-15000":
            errors.append("service_grounding does not point to the public bugfix service")
        if not service_grounding.get("public_service"):
            errors.append("service_grounding is not marked public")

    if not hard_constraints:
        errors.append("hard_constraints is missing")
    else:
        if not hard_constraints.get("answer_before_procedure"):
            errors.append("hard_constraints lost answer_before_procedure")
        if not hard_constraints.get("ask_only_if_blocking"):
            errors.append("hard_constraints lost ask_only_if_blocking")

    direct_answer_line = decision_plan.get("direct_answer_line", "")
    if not has_any(rendered, ["ありがとうございます", "確認しました"]):
        errors.append("missing brief reaction at the top")
    if primary["answer_brief"] not in rendered and direct_answer_line != primary["answer_brief"]:
        pass
    elif primary["answer_brief"] not in rendered:
        errors.append("primary answer is missing from rendered text")
    if direct_answer_line and direct_answer_line not in rendered:
        errors.append("direct answer line is missing from rendered text")
    if direct_answer_line:
        repeated_sections = sum(1 for section in rendered.split("\n\n") if direct_answer_line in section)
        if repeated_sections > 1:
            errors.append("direct answer line is repeated across multiple sections")

    # answer_first_if_answerable: direct answer must appear before hold/procedure/ask.
    if direct_answer_line:
        direct_index = rendered.find(direct_answer_line)
        hold_reason = primary.get("hold_reason", "")
        if hold_reason and hold_reason in rendered and rendered.find(hold_reason) < direct_index:
            errors.append("direct answer appears after hold reason")
        if "トークルーム" in rendered and rendered.find("トークルーム") < direct_index:
            errors.append("direct answer appears after procedure text")
        for ask in case["reply_contract"].get("ask_map") or []:
            ask_text = ask["ask_text"]
            if ask_text in rendered and rendered.find(ask_text) < direct_index:
                errors.append("direct answer appears after ask")

    # no_reask_known_fact: when nothing blocks progress, generic ask should not fire.
    if not decision_plan.get("blocking_missing_facts"):
        for ask in case["reply_contract"].get("ask_map") or []:
            if ask["ask_text"] in rendered:
                errors.append("rendered text re-asks despite no blocking missing facts")
        if has_any(raw, ["提案", "見積もり", "15000", "15,000", "返金", "支払い方法"]) and has_any(rendered, ["送ってください", "教えてください"]):
            errors.append("rendered text asks for information already present in the buyer message")

    if scenario == "proposal_change":
        if decision_plan.get("blocking_missing_facts"):
            if not has_any(rendered, ["変更したい点", "1〜2点"]):
                errors.append("proposal change case does not ask for minimal change points")
        elif not has_any(rendered, ["同じ原因", "別原因"]):
            errors.append("proposal change case does not explain the same-cause scope check")
        if not has_any(rendered, ["同じ提案", "提案"]):
            errors.append("proposal change case does not mention proposal scope")

    if scenario == "purchase_timing" and not has_any(rendered, ["来週", "再提案"]):
        errors.append("purchase timing case does not answer timing directly")

    if scenario == "reissue_quote" and not has_any(rendered, ["再提案", "同じ内容"]):
        errors.append("reissue case does not answer re-proposal directly")

    if scenario == "risk_refund_question":
        if has_any(rendered, ["返金します", "返金できます", "返金をお約束"]):
            errors.append("risk/refund case answers refund too definitively")
        if not has_any(rendered, ["ココナラ", "手続き"]):
            errors.append("risk/refund case does not place refund on coconala-side procedure")
        if not has_any(direct_answer_line, ["15,000", "15000", "提案"]):
            errors.append("risk/refund case direct answer does not anchor the quoted fee clearly")

    if scenario == "payment_method" and not has_any(rendered, ["ココナラ側", "支払い画面"]):
        errors.append("payment method case does not clarify coconala-side limitation")

    if scenario == "dashboard_scope_question":
        if not has_any(rendered, ["ダッシュボード", "設定"]):
            errors.append("dashboard scope case does not answer the dashboard-setting scope directly")
        if not has_any(rendered, ["Webhook", "受信口"]):
            errors.append("dashboard scope case does not anchor the webhook scope")

    if scenario == "general_bugfix_scope_question":
        if not has_any(rendered, ["このサービス", "確認できます"]):
            errors.append("general bugfix scope case does not answer service-fit directly")
        if not has_any(rendered, ["購入後", "原因", "切り分け"]):
            errors.append("general bugfix scope case does not explain the post-purchase next step")
        if has_any(raw, ["Nuxt", "Nginx", "VPS"]) and not has_any(rendered, ["Nuxt", "Nginx", "VPS"]):
            errors.append("general bugfix scope case dropped the buyer's stack context")
        if has_any(raw, ["Shopify", "Liquid", "カスタムJS"]) and not has_any(rendered, ["Shopify", "Liquid", "カスタムJS"]):
            errors.append("general bugfix scope case dropped the buyer's Shopify/Liquid context")
        if has_any(raw, ["Bubble", "非エンジニア"]) and not has_any(rendered, ["Bubble", "非エンジニア", "分かる範囲", "大丈夫"]):
            errors.append("general bugfix scope case dropped the buyer's non-engineer/no-code context")
        if has_any(raw, ["本番", "テスト環境", "テストキー"]) and not has_any(rendered, ["本番", "テスト", "環境差"]):
            errors.append("general bugfix scope case dropped the buyer's prod-vs-test context")
        if has_any(raw, ["特定の商品", "他の商品"]) and not has_any(rendered, ["特定", "商品", "一部"]):
            errors.append("general bugfix scope case dropped the buyer's partial-symptom context")
        if has_any(raw, ["たらい回し", "どこに頼めばいいか分から"]) and not has_any(rendered, ["入口", "整理", "たらい回し"]):
            errors.append("general bugfix scope case dropped the buyer's bounced-around context")
        if has_any(raw, ["真っ白", "5回に1回", "再現条件"]) and not has_any(rendered, ["真っ白", "毎回ではない", "再現条件"]):
            errors.append("general bugfix scope case dropped the buyer's intermittent symptom context")
        if has_any(raw, ["タイムアウト", "深夜", "時間帯だけ"]) and not has_any(rendered, ["時間帯", "タイムアウト", "Webhook"]):
            errors.append("general bugfix scope case dropped the buyer's time-window timeout context")
        if has_any(raw, ["0円", "カート情報"]) and not has_any(rendered, ["0円", "カート", "金額"]):
            errors.append("general bugfix scope case dropped the buyer's zero-amount/cart context")
        if has_any(raw, ["Safari", "iOS"]) and not has_any(rendered, ["Safari", "iOS", "ブラウザ"]):
            errors.append("general bugfix scope case dropped the buyer's browser-specific context")
        if has_any(raw, ["Connect", "Destination Charge", "送金が動いていない", "送金が動いていません"]) and not has_any(rendered, ["送金", "Connect", "Destination Charge", "入金"]):
            errors.append("general bugfix scope case dropped the buyer's connect-transfer context")
        if has_any(raw, ["手探り", "自分のコードの問題だと思う"]) and not has_any(rendered, ["手探り", "コード側", "その前提", "大丈夫"]):
            errors.append("general bugfix scope case dropped the buyer's self-disclosed uncertainty")

    if scenario == "subscription_bug_scope_question":
        if has_any(raw, ["Laravel", "Cashier", "SDK"]) and not has_any(rendered, ["Laravel", "Cashier", "SDK"]):
            errors.append("subscription bug scope case dropped the buyer's Laravel/Cashier/SDK context")
        if has_any(raw, ["ドキュメント通り", "やったつもり"]) and not has_any(rendered, ["ドキュメント", "その前提"]):
            errors.append("subscription bug scope case dropped the buyer's implementation-confidence context")

    if scenario == "extra_fee_fear":
        if not has_any(rendered, ["自動", "事前", "止める"]):
            errors.append("extra fee fear case does not explain the stop / prior-consult rule")
        if not has_any(rendered, ["料金", "追加対応"]):
            errors.append("extra fee fear case does not address the fee anxiety directly")
        if not has_any(rendered, ["キャンセル", "ココナラ"]):
            errors.append("extra fee fear case does not land the cancellation question")

    if scenario == "self_edit_fee_anxiety":
        if not has_any(rendered, ["触った", "今の状態", "対応"]):
            errors.append("self-edit fee anxiety case does not answer the self-edit concern directly")
        if not has_any(rendered, ["追加料金", "事前", "決まるわけではない"]):
            errors.append("self-edit fee anxiety case does not answer the fee concern clearly")
        if not has_any(rendered, ["ご購入", "大丈夫です"]):
            errors.append("self-edit fee anxiety case does not end with a clear quote_sent closing")

    if "SendGrid" in raw and "SendGrid" not in rendered:
        errors.append("quote_sent case dropped the buyer's `SendGrid` scope question")
    if ("送り忘れてたファイル" in raw or "ファイルがあって" in raw) and "ファイル" not in rendered:
        errors.append("quote_sent case dropped the buyer's extra-file follow-up")

    if scenario == "self_apply_support":
        if not has_any(rendered, ["依頼者様", "確認手順"]):
            errors.append("self-apply support case does not state the client-side apply boundary")
        if not has_any(rendered, ["同じ原因", "基本料金内"]):
            errors.append("self-apply support case does not explain same-cause follow-up support")

    if scenario == "secret_share_reassurance":
        if not has_any(rendered, ["本番のURL", "evt_"]):
            errors.append("secret-share reassurance case does not answer the sharing concern concretely")
        if has_any(rendered, [".envの値", "シークレットを送って"]):
            errors.append("secret-share reassurance case asks for raw secrets")
        if not has_any(rendered, ["ご購入", "大丈夫です"]):
            errors.append("secret-share reassurance case does not end with a clear quote_sent closing")

    if scenario == "no_meeting_request":
        if not has_any(rendered, ["Zoom", "通話"]):
            errors.append("no-meeting case does not answer the zoom/call request directly")
        if not has_any(rendered, ["スクショ", "箇条書き", "文章"]):
            errors.append("no-meeting case does not offer a text-based alternative")
        if not has_any(rendered, ["ご購入", "大丈夫です"]):
            errors.append("no-meeting case does not end with a clear quote_sent closing")

    if scenario == "timeline_question":
        if not has_any(rendered, ["調査結果", "共有"]):
            errors.append("timeline question case does not mention investigation-result-first handling")
        if "今週末" in raw and "今週末" not in rendered:
            errors.append("timeline question case dropped the buyer's weekend deadline")
        if not has_any(rendered, ["ご購入", "大丈夫です"]):
            errors.append("timeline question case does not end with a clear quote_sent closing")

    forbidden_terms = ["GitHubに招待", "Driveに置いて", "Dropbox", "外部決済", "無料で対応"]
    for term in forbidden_terms:
        if term in rendered:
            errors.append(f"forbidden term leaked into rendered text: {term}")

    if "提案" in raw and not has_any(rendered, ["提案"]):
        errors.append("quote_sent case does not mention proposal context")
    if scenario == "generic_quote_sent" and has_any(
        raw,
        [
            "で、結局",
            "直りますか",
            "zipで送って",
            "githubじゃなくてzip",
            "githubじゃなくて",
            "見ていただくことは可能",
            "見ていただけますでしょうか",
            "対応いただけるか教えて",
            "メールが飛ばない",
            "たらい回し",
            "真っ白になる",
            "根本原因が分から",
            "タイムアウト",
            "0円",
            "Safari",
            "iOS",
            "送金が動いていない",
            "送金が動いていません",
            "プラン変更",
            "アップグレード",
            "整理だけ",
            "メモを見てから",
        ],
    ):
        errors.append("generic_quote_sent fallback survived a concrete quote_sent question")

    errors.extend(collect_quality_style_errors(rendered))
    errors.extend(collect_temperature_constraint_errors(rendered, temperature_plan))
    errors.extend(collect_reasoning_preservation_errors(rendered, raw, decision_plan, scenario))
    return errors


def main() -> int:
    parser = argparse.ArgumentParser(description="Lint rendered quote_sent follow-up replies.")
    parser.add_argument("--fixture", required=True)
    parser.add_argument("--case-id")
    parser.add_argument("--limit", type=int)
    args = parser.parse_args()

    module = load_renderer()
    cases = module.shared.load_cases(Path(args.fixture))
    cases = [case for case in cases if case.get("state") == "quote_sent"]
    if args.case_id:
        cases = [case for case in cases if case.get("case_id") == args.case_id or case.get("id") == args.case_id]
    if args.limit is not None:
        cases = cases[: args.limit]
    if not cases:
        print("[NG] no quote_sent cases selected")
        return 1

    had_error = False
    for source in cases:
        case_id = source.get("case_id") or source.get("id") or "<unknown>"
        errors = lint_case(module, source)
        for error in errors:
            print(f"[NG] {case_id}: {error}")
            had_error = True

    if had_error:
        return 1
    print(f"[OK] rendered quote_sent follow-up lint passed: {len(cases)} case(s)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
