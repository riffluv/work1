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
    return f"本日{target:%H:%M}までに、見立てをお返しします。"


def opener_for(source: dict) -> str:
    return "ご連絡ありがとうございます。"


def detect_scenario(source: dict) -> str:
    raw = source.get("raw_message", "")
    note = source.get("note", "")
    combined = f"{raw}\n{note}"

    if "返金" in combined:
        return "refund_request"
    if "検証手順" in combined or "社内で" in combined:
        return "quality_feedback_manual"
    if "引き継ぎメモ" in combined or "書き直し" in combined:
        return "memo_rewrite"
    if "もう1フロー" in combined or "少し安く" in combined:
        return "new_flow_plus_discount"
    if "別の件" in combined or "別のエンドポイント" in combined or "またお願いしたい" in combined:
        return "new_issue_repeat_client"
    if "コードを少し触った" in combined or "自分のせい" in combined:
        return "self_edit_regression"
    if "新しい機能" in combined or "クーポン機能" in combined:
        return "new_feature_request"
    if "違うイベント" in combined:
        return "similar_but_not_same"
    if (
        "またお金がかかる" in combined
        or "毎回お金を払" in combined
        or "納得いかない" in combined
        or "何万円も払いたくない" in combined
        or "意味がない" in combined
    ):
        return "price_complaint"
    if "直っていない" in combined or "解決していない" in combined:
        return "same_symptom_recur"
    if "また同じ" in combined or "またおかしく" in combined or "前回の続き" in combined:
        return "same_symptom_recur"
    return "generic_closed"


def build_case_from_source(source: dict) -> dict:
    raw = source.get("raw_message", "")
    scenario = detect_scenario(source)
    case = {
        "id": source.get("case_id") or source.get("id"),
        "src": source.get("route", "message"),
        "state": "closed",
        "raw_message": raw,
        "summary": shared.derive_summary(source),
        "scenario": scenario,
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
                    "revisit_trigger": "必要な内容を受領したあとに、進め方をお返しします。",
                },
            ],
            "ask_map": [],
            "required_moves": ["react_briefly_first", "answer_directly_now", "defer_with_reason", "commit_next_update_time"],
        }
        return case

    if scenario == "refund_request":
        case["reply_contract"] = {
            "primary_question_id": "q1",
            "explicit_questions": [
                {"id": "q1", "text": "返金になるのか", "priority": "primary"},
                {"id": "q2", "text": "今回どう進めるか", "priority": "secondary"},
            ],
            "answer_map": [
                {
                    "question_id": "q1",
                    "disposition": "answer_after_check",
                    "answer_brief": "返金の話を先に断定するのではなく、まず今回の症状と前回のつながりを確認します。",
                    "hold_reason": "トークルームは閉じているため、前回の続きとして扱う前に今回の状況確認が必要です。",
                    "revisit_trigger": "症状を受領したあとに、今回の進め方をお返しします。",
                },
                {
                    "question_id": "q2",
                    "disposition": "answer_now",
                    "answer_brief": "最初の1通では、まず状況確認から進めます。",
                },
            ],
            "ask_map": [
                {
                    "id": "a1",
                    "question_ids": ["q1", "q2"],
                    "ask_text": "今の症状が出ている画面かエラー文を1点だけ送ってください。",
                    "why_needed": "前回とのつながりが強いかを先に見るため",
                }
            ],
            "required_moves": ["react_briefly_first", "answer_directly_now", "defer_with_reason", "request_minimum_evidence", "commit_next_update_time"],
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
                    "answer_brief": "料金と進め方は、補足で足りるか書き直しになるかで変わります。",
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

    if scenario == "new_issue_repeat_client":
        case["reply_contract"] = {
            "primary_question_id": "q1",
            "explicit_questions": [
                {"id": "q1", "text": "新しく依頼できるか", "priority": "primary"},
            ],
            "answer_map": [
                {
                    "question_id": "q1",
                    "disposition": "answer_now",
                    "answer_brief": "今回の内容も確認できます。",
                },
            ],
            "ask_map": [
                {
                    "id": "a1",
                    "question_ids": ["q1"],
                    "ask_text": "今出ている症状か、見たい流れを1点だけそのまま送ってください。",
                    "why_needed": "新しい内容の入口を切るため",
                }
            ],
            "required_moves": ["react_briefly_first", "answer_directly_now", "request_minimum_evidence", "commit_next_update_time"],
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
                    "answer_brief": "どこを触ったあとに戻ったかを見てから、今回の進め方をお返しします。",
                    "hold_reason": "トークルームは閉じているため、そのまま前回の続きとして扱う前に状況確認が必要です。",
                    "revisit_trigger": "変更した箇所を受領したあとに、前回修正との関係をお返しします。",
                },
            ],
            "ask_map": [
                {
                    "id": "a1",
                    "question_ids": ["q1"],
                    "ask_text": "変更した箇所か、触ったファイル名を1〜2点だけ送ってください。",
                    "why_needed": "前回修正が戻ったのか、別の変更かを切るため",
                }
            ],
            "required_moves": ["react_briefly_first", "defer_with_reason", "request_minimum_evidence", "commit_next_update_time"],
        }
        return case

    if scenario == "new_feature_request":
        case["reply_contract"] = {
            "primary_question_id": "q1",
            "explicit_questions": [
                {"id": "q1", "text": "新しい機能追加をお願いできるか", "priority": "primary"},
            ],
            "answer_map": [
                {
                    "question_id": "q1",
                    "disposition": "decline",
                    "answer_brief": "新しい機能追加は、今回の bugfix 対応の範囲ではありません。",
                },
            ],
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
                    "hold_reason": "新しい1フロー確認が必要な内容かを先に確認します。",
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
                    "revisit_trigger": "症状を受領したあとに、今回の進め方をお返しします。",
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
                    "answer_brief": "まず、前回と同じ原因かどうかを確認します。",
                    "hold_reason": "トークルームは閉じているため、そのまま継続対応すると決める前に今回の状況確認が必要です。",
                    "revisit_trigger": "今回の症状を受領したあとに、前回とのつながりが強いかをお返しします。",
                },
            ],
            "ask_map": [
                {
                    "id": "a1",
                    "question_ids": ["q1"],
                    "ask_text": "今の症状が出ている画面スクショと、前回と同じ操作で起きているかだけ送ってください。",
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
                    "ask_text": "今の症状が出ている画面スクショと、前回と同じ操作で起きているかを送ってください。",
                    "why_needed": "前回とのつながりが強いかを先に見るため",
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
                "answer_brief": "トークルームは閉じているので、まず今回の内容を見て進め方を決めます。",
                "hold_reason": "前回の続きとしてそのまま扱う前に、今回の状況確認が必要です。",
                "revisit_trigger": "必要な情報を受領したあとに、進め方をお返しします。",
            },
        ],
        "ask_map": [
            {
                "id": "a1",
                "question_ids": ["q1"],
                "ask_text": "今いちばん気になっている症状か箇所を1点だけそのまま送ってください。",
                "why_needed": "今回の入口を先に切るため",
            }
        ],
        "required_moves": ["react_briefly_first", "defer_with_reason", "request_minimum_evidence", "commit_next_update_time"],
    }
    return case


def reaction_line(case: dict) -> str:
    scenario = case["scenario"]
    if scenario == "quality_feedback_manual":
        return "前回の検証まわりについてのご連絡、確認しました。"
    if scenario == "refund_request":
        return "前回対応後のご不安と返金のご質問、確認しました。"
    if scenario == "memo_rewrite":
        return "前回メモで伝わりにくかった部分があったとのこと、承知しました。"
    if scenario == "new_issue_repeat_client":
        return "前回とは別の内容でまたご相談いただいた件、確認しました。"
    if scenario == "self_edit_regression":
        return "前回修正後にコードを触ってから変化があった件、確認しました。"
    if scenario == "new_feature_request":
        return "前回のご利用後に新しい機能追加も検討されている件、確認しました。"
    if scenario == "new_flow_plus_discount":
        return "もう1フロー見たい件と、前回メモの気になる箇所がある件、どちらも確認しました。"
    if scenario == "similar_but_not_same":
        return "前回とは違うイベントで似たエラーが出ているとのこと、確認しました。"
    if scenario == "price_complaint":
        return "前回の件でまたご不便が出ているとのこと、確認しました。"
    if scenario == "same_symptom_recur":
        return "前回と同じような症状がまた出ているとのこと、確認しました。"
    return "クローズ後のご連絡、確認しました。"


def render_case(case: dict) -> str:
    contract = case["reply_contract"]
    primary_id = contract["primary_question_id"]
    answer_map = contract["answer_map"]
    primary = next(item for item in answer_map if item["question_id"] == primary_id)
    direct_answers = [item for item in answer_map if item["disposition"] in {"answer_now", "decline"}]
    deferred_answers = [item for item in answer_map if item["disposition"] == "answer_after_check"]
    ask_map = contract.get("ask_map") or []

    sections: list[str] = []
    sections.append("\n".join([opener_for(case), reaction_line(case)]))

    direct_lines = []
    if primary["disposition"] in {"answer_now", "decline"}:
        direct_lines.append(primary["answer_brief"])
    for item in direct_answers:
        if item["question_id"] == primary_id:
            continue
        direct_lines.append(item["answer_brief"])
    if direct_lines:
        sections.append("\n".join(direct_lines))

    defer_lines = []
    if primary["disposition"] == "answer_after_check":
        defer_lines.append(primary["answer_brief"])
        defer_lines.append(primary["hold_reason"])
    for item in deferred_answers:
        if item["question_id"] == primary_id:
            continue
        defer_lines.append(item["answer_brief"])
        defer_lines.append(item["hold_reason"])
    if defer_lines:
        sections.append("\n".join(line if line.endswith("。") else f"{line}。" for line in defer_lines))

    if ask_map:
        sections.append("\n".join(ask["ask_text"] for ask in ask_map))

    sections.append(time_commit())
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
