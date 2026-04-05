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

    if scenario == "extra_fee_fear":
        if not has_any(rendered, ["自動", "事前", "止める"]):
            errors.append("extra fee fear case does not explain the stop / prior-consult rule")
        if not has_any(rendered, ["料金", "追加対応"]):
            errors.append("extra fee fear case does not address the fee anxiety directly")
        if not has_any(rendered, ["キャンセル", "ココナラ"]):
            errors.append("extra fee fear case does not land the cancellation question")

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

    forbidden_terms = ["GitHubに招待", "Driveに置いて", "Dropbox", "外部決済", "無料で対応"]
    for term in forbidden_terms:
        if term in rendered:
            errors.append(f"forbidden term leaked into rendered text: {term}")

    if "提案" in raw and not has_any(rendered, ["提案"]):
        errors.append("quote_sent case does not mention proposal context")

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
