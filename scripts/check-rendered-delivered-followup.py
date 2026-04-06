#!/usr/bin/env python3
from __future__ import annotations

import argparse
import importlib.util
import re
from pathlib import Path

from reply_quality_lint_common import (
    collect_quality_style_errors,
    collect_reasoning_preservation_errors,
    collect_temperature_constraint_errors,
)

ROOT_DIR = Path(__file__).resolve().parents[1]
RENDERER_PATH = ROOT_DIR / "scripts/render-delivered-followup.py"


def load_renderer():
    spec = importlib.util.spec_from_file_location("render_delivered_followup", RENDERER_PATH)
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

    if not has_any(rendered, ["ありがとうございます", "確認しました", "大丈夫です", "承知しました", "お待たせ", "すみません"]):
        errors.append("missing brief reaction at the top")
    if has_near_echo(rendered):
        errors.append("near_echo_check failed: adjacent sections still overlap too much")

    direct_answer_line = decision_plan.get("direct_answer_line", "")
    if direct_answer_line and direct_answer_line not in rendered:
        errors.append("direct answer line is missing from rendered text")
    if direct_answer_line:
        direct_index = rendered.find(direct_answer_line)
        hold_reason = primary.get("hold_reason", "")
        if hold_reason and hold_reason in rendered and rendered.find(hold_reason) < direct_index:
            errors.append("direct answer appears after hold reason")
        for ask in contract.get("ask_map") or []:
            ask_text = ask.get("ask_text", "")
            if ask_text and ask_text in rendered and rendered.find(ask_text) < direct_index:
                errors.append("direct answer appears after ask")

    if primary["disposition"] == "answer_after_check":
        if not has_any(rendered, ["確認", "断定", "見直し"]):
            errors.append("answer_after_check exists but defer language is weak")
        if contract.get("ask_map") and decision_plan.get("blocking_missing_facts") and not has_any(rendered, ["送ってください", "教えてください", "ください"]):
            errors.append("answer_after_check case has ask_map but no ask request")
        if "本日" not in rendered or "までに" not in rendered:
            errors.append("answer_after_check delivered case is missing time commitment")

    if primary["disposition"] == "answer_now":
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

    if scenario == "approval_ok" and "承諾" not in rendered:
        errors.append("approval case does not mention 承諾 directly")
    if scenario == "approval_test_method":
        if not has_any(rendered, ["Webhook", "受信側"]):
            errors.append("approval test method case does not answer the receiver-side scope directly")
        if not has_any(rendered, ["送信テスト", "承諾前", "本番で決済を試さなくても"]):
            errors.append("approval test method case does not answer the safe pre-approval test method clearly")
        if has_any(rendered, ["本番で試してください", "購入して試して"]):
            errors.append("approval test method case pushes a real production test")
    if scenario == "pending_webhook_events":
        if "保留中" not in rendered:
            errors.append("pending webhook events case does not mention 保留中 directly")
        if not has_any(rendered, ["未処理", "表示だけ", "イベント詳細"]):
            errors.append("pending webhook events case does not explain what is being checked")
    if scenario == "prevention_question" and not has_any(rendered, ["再発", "起きにくく", "可能性"]):
        errors.append("prevention case does not answer recurrence directly")
    if scenario == "doc_caution_followup":
        if "環境変数" not in rendered:
            errors.append("doc caution follow-up does not mention environment variables directly")
        if not has_any(rendered, ["急ぎで", "今のところ"]):
            errors.append("doc caution follow-up does not lower the urgency explicitly")
    if (
        scenario == "side_effect_question"
        and has_any(raw, ["体感", "気のせい", "不具合ってほどではない"])
        and "承諾" in raw
    ):
        if "今の文面だけでは" in rendered:
            errors.append("soft side-effect probe still says `今の文面だけでは`")
        if "切り分け" in rendered:
            errors.append("soft side-effect probe still uses heavy `切り分け` language")
        if "本日" in rendered and "までに" in rendered:
            errors.append("soft side-effect probe still carries a time commitment")
        if "承諾" not in rendered:
            errors.append("soft side-effect probe does not answer approval directly")
    if scenario == "side_effect_question" and "Webhook" in raw and "出なくなりました" in raw and not has_any(rendered, ["よかった", "出なくなった"]):
        errors.append("side-effect follow-up dropped acknowledgment that the webhook error is now gone")
    if scenario == "delivery_scope_mismatch" and not has_any(rendered, ["期待と違っていた", "認識差", "差し戻し"]):
        errors.append("delivery mismatch complaint is not acknowledged clearly")
    if scenario == "delivery_scope_mismatch" and "診断レポートだけ" in raw and "診断レポート" not in rendered:
        errors.append("delivery mismatch complaint dropped the buyer's `診断レポートだけ` point")
    if scenario == "delivery_scope_mismatch" and "修正ファイル" in raw and "修正ファイル" not in rendered:
        errors.append("delivery mismatch complaint dropped the buyer's `修正ファイル` point")
    if scenario == "delivery_scope_mismatch" and "修正ファイル" in raw and has_any(rendered, ["足りないと感じた点", "1〜2点だけ"]):
        errors.append("delivery mismatch complaint still re-asks despite already named missing deliverable")
    if scenario == "price_complaint" and rendered.count("受け止め") > 1:
        errors.append("price complaint repeats 受け止め language")
    if scenario == "price_complaint" and has_any(raw, ["価値があったのか", "モヤモヤ", "高い気が", "高かったかも"]) and not has_any(rendered, ["すみません", "申し訳"]):
        errors.append("price complaint with lingering discomfort does not include a brief ownership/apology line")
    if "Stripeのダッシュボードに「テスト」" in raw and "テストモード" not in rendered:
        errors.append("dashboard test label case does not mention mode check")
    if scenario == "generic_delivered" and has_any(
        raw,
        [
            "高い",
            "待って",
            "承諾",
            "送信テスト",
            "本番で試すのが怖い",
            "確認できてません",
            "価格",
            "同じ原因",
            "未確認",
            "追加でお願い",
            "別件への移行",
            "ここも危なそう",
            "本番に反映",
            "おいくら",
            "かみ砕いた説明",
            "質問が出たら",
            "前と違う動き",
            "ビルドが通ら",
            "考えさせてもらって",
            "ちょっと考えさせて",
            "保留中",
            "どのくらいの作業量",
            "自分でも直せた可能性",
        ],
    ):
        errors.append("generic_delivered fallback survived a concrete delivered follow-up request")

    forbidden_terms = ["GitHubに招待", "Driveに置いて", "Dropbox", "外部決済", "無料で対応"]
    for term in forbidden_terms:
        if term in rendered:
            errors.append(f"forbidden term leaked into rendered text: {term}")

    errors.extend(collect_quality_style_errors(rendered))
    errors.extend(collect_temperature_constraint_errors(rendered, temperature_plan))
    errors.extend(collect_reasoning_preservation_errors(rendered, raw, decision_plan, scenario))
    return errors


def main() -> int:
    parser = argparse.ArgumentParser(description="Lint rendered delivered follow-up replies.")
    parser.add_argument("--fixture", required=True)
    parser.add_argument("--case-id")
    parser.add_argument("--limit", type=int)
    args = parser.parse_args()

    module = load_renderer()
    cases = module.shared.load_cases(Path(args.fixture))
    cases = [case for case in cases if case.get("state") == "delivered"]
    if args.case_id:
        cases = [case for case in cases if case.get("case_id") == args.case_id or case.get("id") == args.case_id]
    if args.limit is not None:
        cases = cases[: args.limit]
    if not cases:
        print("[NG] no delivered cases selected")
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
    print(f"[OK] rendered delivered follow-up lint passed: {len(cases)} case(s)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
