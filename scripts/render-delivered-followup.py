#!/usr/bin/env python3
from __future__ import annotations

import argparse
import importlib.util
from datetime import datetime, timedelta
from pathlib import Path
from zoneinfo import ZoneInfo


ROOT_DIR = Path(__file__).resolve().parents[1]
PREQUOTE_RENDERER = ROOT_DIR / "scripts/render-prequote-estimate-initial.py"
JST = ZoneInfo("Asia/Tokyo")


def load_shared_module():
    spec = importlib.util.spec_from_file_location("render_prequote_estimate_initial", PREQUOTE_RENDERER)
    if spec is None or spec.loader is None:
        raise RuntimeError(f"failed to load shared renderer: {PREQUOTE_RENDERER}")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


shared = load_shared_module()


def time_commit(hours: int = 2) -> str:
    target = datetime.now(JST) + timedelta(hours=hours)
    return f"本日{target:%H:%M}までに、確認結果をお返しします。"


def opener_for(source: dict) -> str:
    return "ご連絡ありがとうございます。"


def detect_scenario(source: dict) -> str:
    raw = source.get("raw_message", "")
    note = source.get("note", "")
    combined = f"{raw}\n{note}"

    if "承諾に進んで大丈夫" in combined:
        return "approval_ok"
    if "期待していた内容と違います" in combined or "診断レポートだけ" in combined:
        return "delivery_scope_mismatch"
    if "今後また同じことが起きる可能性" in combined or "予防できるなら" in combined:
        return "prevention_question"
    if "Vercelにデプロイすると500エラー" in combined or "差し戻しというか" in combined:
        return "redelivery_same_error"
    if "影響ですか" in combined or "別の機能が動かなく" in combined:
        return "side_effect_question"
    if "テスト" in combined and "ダッシュボード" in combined:
        return "dashboard_test_label"
    return "generic_delivered"


def build_case_from_source(source: dict) -> dict:
    raw = source.get("raw_message", "")
    scenario = detect_scenario(source)
    case = {
        "id": source.get("case_id") or source.get("id"),
        "src": source.get("route", "talkroom"),
        "state": "delivered",
        "raw_message": raw,
        "summary": shared.derive_summary(source),
        "scenario": scenario,
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
                    "answer_brief": "修正した決済フローが動いているなら、その表示だけで異常とはまだ断定しません。",
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
                    "answer_brief": "今の時点では、今回の修正の影響とはまだ断定しません。",
                    "hold_reason": "修正箇所と、止まっているメール送信のつながりを先に確認します。",
                    "revisit_trigger": "状況を受領したあとに、今回の修正との関係をお返しします。",
                }
            ],
            "ask_map": [
                {
                    "id": "a1",
                    "question_ids": ["q1"],
                    "ask_text": "メール送信が止まっていることが分かる画面か、操作手順を1点だけ送ってください。",
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
                    "answer_brief": "ローカルでは直っていて本番だけ残るなら、修正不足と決め打ちせず環境差も含めて確認します。",
                    "hold_reason": "Vercel側の設定や本番側の動きも含めて見直したいです。",
                    "revisit_trigger": "本番の状況を受領したあとに、次に見る場所をお返しします。",
                }
            ],
            "ask_map": [
                {
                    "id": "a1",
                    "question_ids": ["q1"],
                    "ask_text": "Vercelの500エラー画面か、その直前の操作手順を1点だけ送ってください。",
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
        case["reply_contract"] = {
            "primary_question_id": "q1",
            "explicit_questions": [{"id": "q1", "text": "期待していた内容と違う", "priority": "primary"}],
            "answer_map": [
                {
                    "question_id": "q1",
                    "disposition": "answer_after_check",
                    "answer_brief": "期待と違っていた点は確認しました。",
                    "hold_reason": "まずは今回の認識差を確認して、差し戻しで埋める範囲かを切ります。",
                    "revisit_trigger": "足りなかった点を受領したあとに、対応の進め方をお返しします。",
                }
            ],
            "ask_map": [
                {
                    "id": "a1",
                    "question_ids": ["q1"],
                    "ask_text": "足りないと感じた点を1〜2点だけそのまま送ってください。",
                    "why_needed": "差し戻しで埋める話か、認識差の整理が先かを切るため",
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
                "answer_brief": "状況を確認してから、次の進め方をお返しします。",
                "hold_reason": "納品後の追加確認なので、まず今の状態を整理したいです。",
                "revisit_trigger": "必要な情報を受領したあとに、進め方をお返しします。",
            }
        ],
        "ask_map": [
            {
                "id": "a1",
                "question_ids": ["q1"],
                "ask_text": "いちばん気になっている点を1点だけそのまま送ってください。",
                "why_needed": "次に見る場所を先に絞るため",
            }
        ],
        "required_moves": ["react_briefly_first", "defer_with_reason", "request_minimum_evidence", "commit_next_update_time"],
    }
    return case


def reaction_line(case: dict) -> str:
    scenario = case["scenario"]
    if scenario == "dashboard_test_label":
        return "納品後の確認ありがとうございます。Stripe画面の表示で気になっている点、確認しました。"
    if scenario == "side_effect_question":
        return "確認ありがとうございます。別の機能で気になる点が出ている件、確認しました。"
    if scenario == "prevention_question":
        return "動作確認ありがとうございます。再発予防についてのご質問、確認しました。"
    if scenario == "redelivery_same_error":
        return "差し戻しのご連絡ありがとうございます。本番だけまだ残っている件、確認しました。"
    if scenario == "approval_ok":
        return "再確認ありがとうございます。今回は問題なく動いているとのこと、確認しました。"
    if scenario == "delivery_scope_mismatch":
        return "納品内容が期待と違っていたとのこと、確認しました。"
    return "納品後のご連絡、確認しました。"


def render_case(case: dict) -> str:
    contract = case["reply_contract"]
    primary_id = contract["primary_question_id"]
    answer_map = contract["answer_map"]
    primary = next(item for item in answer_map if item["question_id"] == primary_id)
    secondary_now = [item for item in answer_map if item["question_id"] != primary_id and item["disposition"] == "answer_now"]
    ask_map = contract.get("ask_map") or []

    sections: list[str] = []
    sections.append("\n".join([opener_for(case), reaction_line(case)]))

    now_lines: list[str] = []
    if primary["disposition"] in {"answer_now", "decline"}:
        now_lines.append(primary["answer_brief"])
    for item in secondary_now:
        now_lines.append(item["answer_brief"])
    if now_lines:
        sections.append("\n".join(now_lines))

    if primary["disposition"] == "answer_after_check":
        sections.append(
            "\n".join(
                line if line.endswith("。") else f"{line}。"
                for line in [primary["answer_brief"], primary["hold_reason"]]
            )
        )

    if ask_map:
        sections.append("\n".join(ask["ask_text"] for ask in ask_map))

    if primary["disposition"] == "answer_after_check":
        sections.append(time_commit())

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
