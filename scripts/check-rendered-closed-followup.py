#!/usr/bin/env python3
from __future__ import annotations

import argparse
import importlib.util
import re
from pathlib import Path

from reply_quality_lint_common import (
    collect_quality_style_errors,
    collect_reasoning_preservation_errors,
    collect_service_binding_errors,
    collect_temperature_constraint_errors,
)

ROOT_DIR = Path(__file__).resolve().parents[1]
RENDERER_PATH = ROOT_DIR / "scripts/render-closed-followup.py"


def load_renderer():
    spec = importlib.util.spec_from_file_location("render_closed_followup", RENDERER_PATH)
    if spec is None or spec.loader is None:
        raise RuntimeError(f"failed to load renderer: {RENDERER_PATH}")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def has_any(text: str, needles: list[str]) -> bool:
    return any(needle in text for needle in needles)


def normalized(text: str) -> str:
    return re.sub(r"[\s。、，,.！？?「」『』（）()・:：/／\\-]+", "", text)


def split_sections(rendered: str) -> list[str]:
    sections: list[str] = []
    current: list[str] = []
    for raw_line in rendered.splitlines():
        line = raw_line.strip()
        if not line:
            if current:
                sections.append("\n".join(current))
                current = []
            continue
        current.append(line)
    if current:
        sections.append("\n".join(current))
    return sections


def has_near_echo(rendered: str) -> bool:
    sections = split_sections(rendered)
    for left, right in zip(sections, sections[1:]):
        nl = normalized(left)
        nr = normalized(right)
        if not nl or not nr:
            continue
        if len(nl) >= 10 and (nl in nr or nr in nl):
            return True
    return False


def lint_case(module, source: dict) -> list[str]:
    case = module.build_case_from_source(source)
    rendered = module.render_case(case)
    contract = case["reply_contract"]
    temperature_plan = case.get("temperature_plan") or {}
    decision_plan = case.get("response_decision_plan") or {}
    service_grounding = case.get("service_grounding") or {}
    hard_constraints = case.get("hard_constraints") or {}
    primary_id = contract["primary_question_id"]
    primary = next(item for item in contract["answer_map"] if item["question_id"] == primary_id)
    raw = source.get("raw_message", "")
    scenario = case.get("scenario")
    errors: list[str] = []

    if not temperature_plan:
        errors.append("temperature_plan is missing")
    if not decision_plan:
        errors.append("response_decision_plan is missing")
    else:
        for field in ["primary_question_id", "primary_concern", "buyer_emotion", "facts_known", "blocking_missing_facts", "direct_answer_line", "response_order"]:
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
        if service_grounding.get("base_price") != 15000:
            errors.append("service_grounding base_price is missing or does not match the public service")
        if not service_grounding.get("hard_no"):
            errors.append("service_grounding is missing hard_no bindings")
    if not hard_constraints:
        errors.append("hard_constraints is missing")
    else:
        if not hard_constraints.get("answer_before_procedure"):
            errors.append("hard_constraints lost answer_before_procedure")
        if not hard_constraints.get("ask_only_if_blocking"):
            errors.append("hard_constraints lost ask_only_if_blocking")

    if not has_any(rendered, ["ありがとうございます", "確認しました", "承知しました"]):
        errors.append("missing brief reaction at the top")
    if has_near_echo(rendered):
        errors.append("near_echo_check failed: adjacent sections still overlap too much")
    if "公開範囲" in rendered:
        errors.append("closed follow-up still exposes internal `公開範囲` wording")
    if "形になります" in rendered:
        errors.append("closed follow-up still uses banned `形になります` wording")
    if "お約束する形" in rendered:
        errors.append("closed follow-up still uses banned `お約束する形` wording")
    if has_any(rendered, ["今回のご相談がどの種類か", "前回の続きとして扱えるか確認します"]):
        errors.append("generic closed fallback survived in rendered text")
    symptom_send_first = (
        scenario == "new_issue_repeat_client"
        and has_any(raw, ["このメッセージ", "メッセージで", "メッセージ上"])
        and has_any(raw, ["症状", "内容", "流れ"])
        and has_any(raw, ["送れば", "送って", "送る", "伝えれば", "相談して", "相談いただいて", "相談"])
    )
    conditional_materials_followup = scenario in {
        "closed_materials_check",
        "closed_old_talkroom_ohineri",
        "closed_pre_estimate_cause_check",
    } and has_any(
        rendered,
        ["送っていただいた範囲で", "いただけた範囲で"],
    )
    if (
        primary["disposition"] == "answer_after_check" or (contract.get("ask_map") and decision_plan.get("blocking_missing_facts"))
    ) and not symptom_send_first and not conditional_materials_followup and ("本日" not in rendered or "までに" not in rendered):
        errors.append("missing time commitment")
    if scenario not in {"price_complaint", "price_discount_request", "repeat_bugfix_price_check", "refund_request", "closed_free_followup_price"} and has_any(rendered, ["15,000円", "25000円", "25,000円"]):
        errors.append("closed follow-up should not front-load price")

    direct_answer_line = decision_plan.get("direct_answer_line", "")
    if direct_answer_line and direct_answer_line not in rendered:
        errors.append("direct answer line is missing from rendered text")
    if direct_answer_line:
        direct_index = rendered.find(direct_answer_line)
        if "トークルーム" in rendered and rendered.find("トークルーム") < direct_index:
            errors.append("direct answer appears after procedure text")
        hold_reason = primary.get("hold_reason", "")
        if hold_reason and hold_reason in rendered and rendered.find(hold_reason) < direct_index:
            errors.append("direct answer appears after hold reason")
        for ask in contract.get("ask_map") or []:
            ask_text = ask.get("ask_text", "")
            if ask_text and ask_text in rendered and rendered.find(ask_text) < direct_index:
                errors.append("direct answer appears after ask")

    if primary["disposition"] == "answer_after_check":
        if not has_any(rendered, ["確認します", "確認して", "断定", "状況確認", "見て", "見たい"]):
            errors.append("answer_after_check exists but defer language is weak")
        if not has_any(rendered, ["トークルーム", "閉じて"]):
            errors.append("closed defer case does not mention closed-room boundary")
        if contract.get("ask_map") and decision_plan.get("blocking_missing_facts") and not has_any(rendered, ["送ってください", "教えてください"]):
            errors.append("answer_after_check case has ask_map but no ask request")

    if primary["disposition"] in {"answer_now", "decline"}:
        if (
            (not primary.get("answer_brief", "") or primary["answer_brief"] not in rendered)
            and direct_answer_line == primary.get("answer_brief", "")
        ):
            errors.append("direct primary answer is missing from rendered text")

    if not decision_plan.get("blocking_missing_facts"):
        for ask in contract.get("ask_map") or []:
            ask_text = ask.get("ask_text", "")
            if ask_text and ask_text in rendered:
                errors.append("rendered text re-asks despite no blocking missing facts")
        if "symptom_surface_described" in decision_plan.get("facts_known", []) and has_any(rendered, ["送ってください", "教えてください"]):
            errors.append("rendered text asks for symptom details already present in the buyer message")

    if "返金" in raw:
        if "Stripe 管理画面" in rendered:
            errors.append("closed refund request confuses coconala transaction refund with Stripe customer refund")
        if "キャンセルを含めて" in rendered:
            errors.append("closed refund request still says `キャンセルを含めて` too vaguely")
        if has_any(rendered, ["返金します", "返金できます"]):
            errors.append("refund request was answered too definitively")
        if not has_any(rendered, ["返金", "状況確認", "つながり"]):
            errors.append("refund request is not acknowledged clearly")
        if not ("トークルーム" in rendered and "閉じ" in rendered):
            errors.append("closed refund request does not mention the closed-room boundary")
        if not has_any(rendered, ["断定できません", "断定せず", "とは言えません"]):
            errors.append("closed refund request does not avoid deciding refund/cancel too early")

    if scenario == "similar_but_not_same" and "トークルーム" in raw:
        if not has_any(rendered, ["メッセージ上", "見積り提案", "新規依頼"]):
            errors.append("closed similar-event case does not explain the post-close path clearly")

    if has_any(raw, ["Google Drive", "Googleドライブ", "Dropbox", "外部共有"]):
        if not has_any(rendered, ["外部共有", "Google Drive など", "使っていません", "メッセージ添付", "送れる範囲"]):
            errors.append("closed external-share request is missing refusal plus coconala attachment alternative")

    if has_any(raw, [".env", "envファイル", "Stripeのキー", "APIキー", "秘密鍵"]):
        if not has_any(rendered, ["送らないでください", "値は扱いません", "キー名", "伏せて"]):
            errors.append("closed secret-sharing question is missing secret-value refusal")

    if has_any(raw, ["ZIPでコード", "コード一式", "直して返して", "修正して返"]):
        if not has_any(rendered, ["修正済みファイルを返すことはできません", "実作業", "見積り提案", "新規依頼"]):
            errors.append("closed zip-fix request does not separate materials review from actual work")

    if has_any(raw, ["先に原因だけ", "原因だけ見てもら", "見積り前", "お願いするか決めたい"]):
        if not has_any(rendered, ["見積り前", "原因調査", "症状の概要", "見立て"]):
            errors.append("closed pre-estimate cause-check request does not separate lightweight triage from actual investigation")

    if has_any(raw, ["おひねり", "同じトークルーム", "前回のトークルームの続き", "前回の続き"]) and has_any(raw, ["クローズ後", "クローズ済み", "閉じ"]):
        if scenario != "closed_old_talkroom_ohineri":
            errors.append("closed old-talkroom ohineri request did not trigger the boundary scenario")
        if not has_any(rendered, ["おひねり追加", "旧トークルーム", "前回のトークルーム"]):
            errors.append("closed old-talkroom ohineri request is not declined directly")
        if not has_any(rendered, ["見積り提案", "新規依頼"]):
            errors.append("closed old-talkroom ohineri request is missing estimate/new-request path")

    if has_any(raw, ["無料で直", "無料で対応", "15,000円かかる", "15000円かかる", "納得できません"]):
        if not has_any(
            rendered,
            [
                "断定できません",
                "断定はしません",
                "決まっているわけでもありません",
                "前提では進めません",
                "通常料金の新規依頼として進めることはしません",
                "前回の補足",
                "新規見積り",
                "費用の有無",
                "費用が発生するか",
            ],
        ):
            errors.append("closed free-followup/price complaint is missing non-commitment and next-path split")
        if not has_any(rendered, ["このメッセージ上でできるのは", "確認材料", "確認するところまで"]):
            errors.append("closed free-followup/price complaint does not limit message-side handling to materials review")
        if not has_any(rendered, ["作業に入る前に", "コード修正などの作業が必要", "修正作業に入ることはできません"]):
            errors.append("closed free-followup/price complaint does not separate message review from actual work")

    if "新しい機能" in raw or "クーポン機能" in raw or "Invoice" in raw or "請求書" in raw:
        if not has_any(rendered, ["範囲ではありません", "機能追加"]):
            errors.append("new feature request is not declined clearly")
        if not has_any(rendered, ["別の相談として整理", "別の相談", "整理する形"]):
            errors.append("new feature request is missing an alternative path after declining")

    if scenario == "new_issue_repeat_client":
        if not has_any(rendered, ["確認できます", "見積りできます"]):
            errors.append("repeat client new issue is not answered positively")
        if symptom_send_first and not has_any(rendered, ["このメッセージでまず相談いただいて大丈夫", "このメッセージで相談"]):
            errors.append("repeat client new issue does not answer the message-side consultation question first")
        if "見積" in raw and "見積" not in rendered:
            errors.append("repeat client new issue does not answer the estimate request directly")
        if not has_any(rendered, ["送ってください"]):
            errors.append("repeat client new issue is missing minimal ask")
        if "API Route" in raw and "API Route" not in rendered and "メール" not in rendered:
            errors.append("repeat client new issue dropped the API Route/mail context")
    if scenario == "price_discount_request" and "メモ" not in raw and "メモ" in rendered:
        errors.append("discount case leaked unrelated memo context")
    if scenario == "price_discount_request" and has_any(raw, ["別の箇所", "別の件", "また依頼したい", "また別", "不具合が見つかった"]):
        if "見積" not in rendered:
            errors.append("discount case with a new issue does not mention estimate guidance")
        if not has_any(rendered, ["送ってください", "そのまま送ってください"]):
            errors.append("discount case with a new issue is missing the minimal symptom ask")
    if scenario == "price_complaint" and "納得いかない" in raw and not has_any(rendered, ["納得いかない", "ごもっとも"]):
        errors.append("closed price complaint did not receive the buyer's `納得いかない` feeling")
    if scenario == "feedback_for_next_time" and "問題なかった" in raw and not has_any(rendered, ["問題なかった", "ありがとうございます"]):
        errors.append("closed feedback case dropped the buyer's positive result acknowledgment")
    if scenario == "referral_and_soft_new_issue":
        if not has_any(rendered, ["紹介", "ご相談いただいて大丈夫"]):
            errors.append("referral follow-up did not acknowledge the introduction clearly")
        if not has_any(rendered, ["見積りできます", "新しい相談"]):
            errors.append("referral follow-up did not guide the soft new issue clearly")
    if scenario == "generic_closed" and has_any(
        raw,
        [
            "購入",
            "追記",
            "次回",
            "CSS",
            "保守",
            "5000",
            "5,000",
            "1万円",
            "10,000",
            "安く",
            "またエラー",
            "買い直す必要",
            "新規依頼",
            "手数料",
            "テスト環境がない",
            "どうやって確認",
            "前と同じ原因かも",
            "高かったかな",
            "お金を払いたくない",
            "お願いできるものなんでしょうか",
            "Stripeとは直接関係ない",
            "API Route",
            "Invoice",
            "請求書",
            "紹介してもいいですか",
            "メルマガ",
        ],
    ):
        errors.append("generic_closed fallback survived a concrete closed follow-up request")

    forbidden_terms = ["GitHubに招待", "Driveに置いて", "Dropbox", "Zoom", "外部決済", "このトークルームでそのまま"]
    for term in forbidden_terms:
        if term in rendered:
            errors.append(f"forbidden term leaked into rendered text: {term}")

    errors.extend(collect_quality_style_errors(rendered))
    errors.extend(collect_temperature_constraint_errors(rendered, temperature_plan))
    errors.extend(collect_reasoning_preservation_errors(rendered, raw, decision_plan, scenario))
    errors.extend(
        collect_service_binding_errors(
            rendered,
            raw,
            service_grounding,
            state="closed",
            scenario=scenario,
        )
    )
    return errors


def main() -> int:
    parser = argparse.ArgumentParser(description="Lint rendered closed follow-up replies.")
    parser.add_argument("--fixture", required=True)
    parser.add_argument("--case-id")
    parser.add_argument("--limit", type=int)
    args = parser.parse_args()

    module = load_renderer()
    cases = module.shared.load_cases(Path(args.fixture))
    cases = [case for case in cases if case.get("state") == "closed"]
    if args.case_id:
        cases = [case for case in cases if case.get("case_id") == args.case_id or case.get("id") == args.case_id]
    if args.limit is not None:
        cases = cases[: args.limit]
    if not cases:
        print("[NG] no closed cases selected")
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
    print(f"[OK] rendered closed follow-up lint passed: {len(cases)} case(s)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
