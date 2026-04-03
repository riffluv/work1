#!/usr/bin/env python3
from __future__ import annotations

import argparse
import importlib.util
from pathlib import Path


ROOT_DIR = Path(__file__).resolve().parents[1]
PREQUOTE_RENDERER = ROOT_DIR / "scripts/render-prequote-estimate-initial.py"


def load_shared_module():
    spec = importlib.util.spec_from_file_location("render_prequote_estimate_initial", PREQUOTE_RENDERER)
    if spec is None or spec.loader is None:
        raise RuntimeError(f"failed to load shared renderer: {PREQUOTE_RENDERER}")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


shared = load_shared_module()


def opener_for(source: dict) -> str:
    return "ご連絡ありがとうございます。"


def detect_scenario(source: dict) -> str:
    raw = source.get("raw_message", "")
    note = source.get("note", "")
    combined = f"{raw}\n{note}"

    if "期限切れ" in combined or "再提案" in combined:
        return "reissue_quote"
    if "来週購入してもいい" in combined or "期限が切れたりしませんか" in combined:
        return "purchase_timing"
    if "支払い方法" in combined or "コンビニ払い" in combined:
        return "payment_method"
    if "返金してもらえる" in combined or "直らなかった場合" in combined or "修正がいらなかった場合" in combined:
        return "risk_refund_question"
    if "内容を変更" in combined or "同じ提案で対応可能" in combined or "内容を少し変えたい" in combined:
        return "proposal_change"
    return "generic_quote_sent"


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
        return case

    if scenario == "risk_refund_question":
        case["reply_contract"] = {
            "primary_question_id": "q1",
            "explicit_questions": [{"id": "q1", "text": "直らなかった場合でも15000円はかかるか", "priority": "primary"}],
            "answer_map": [
                {
                    "question_id": "q1",
                    "disposition": "answer_after_check",
                    "answer_brief": "返金をここで約束する形ではなく、まず今回の提案内容の範囲で進める前提です。",
                    "hold_reason": "返金可否をこちらが先に決める話ではなく、必要ならココナラ上の手続きに沿う形になります。",
                    "revisit_trigger": "進め方で気になる点があれば、その点に絞ってお返しします。",
                }
            ],
            "ask_map": [],
            "required_moves": ["react_briefly_first", "defer_with_reason"],
        }
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
                "revisit_trigger": "確認後に、次の進め方をお返しします。",
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
    return case


def reaction_line(case: dict) -> str:
    scenario = case["scenario"]
    if scenario == "proposal_change":
        return "提案後に変更したい点が出てきた件、確認しました。"
    if scenario == "purchase_timing":
        return "購入タイミングと期限のご質問、確認しました。"
    if scenario == "reissue_quote":
        return "提案期限切れの表示が出た件、確認しました。"
    if scenario == "risk_refund_question":
        return "提案内容に対する不安点、確認しました。"
    if scenario == "payment_method":
        return "購入画面の支払い方法で迷っている件、確認しました。"
    return "提案後のご連絡、確認しました。"


def render_case(case: dict) -> str:
    contract = case["reply_contract"]
    primary_id = contract["primary_question_id"]
    answer_map = contract["answer_map"]
    primary = next(item for item in answer_map if item["question_id"] == primary_id)
    ask_map = contract.get("ask_map") or []

    sections: list[str] = []
    sections.append("\n".join([opener_for(case), reaction_line(case)]))
    sections.append(primary["answer_brief"] if primary["answer_brief"].endswith("。") else f"{primary['answer_brief']}。")
    if primary["disposition"] == "answer_after_check":
        sections.append(primary["hold_reason"] if primary["hold_reason"].endswith("。") else f"{primary['hold_reason']}。")
    if ask_map:
        sections.append("\n".join(ask["ask_text"] for ask in ask_map))
    if primary["disposition"] == "answer_after_check":
        sections.append(primary["revisit_trigger"] if primary["revisit_trigger"].endswith("。") else f"{primary['revisit_trigger']}。")
    return "\n\n".join(section for section in sections if section.strip())


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
