#!/usr/bin/env python3
from __future__ import annotations

import argparse
import importlib.util
from datetime import datetime, timedelta
from pathlib import Path
from zoneinfo import ZoneInfo


ROOT_DIR = Path(__file__).resolve().parents[1]
REPLY_SAVE = ROOT_DIR / "scripts/reply-save.sh"
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
    return f"本日{target:%H:%M}までに、現時点の確認結果をお返しします。"


def opener_for(source: dict) -> str:
    route = source.get("route", source.get("src", "talkroom"))
    if route == "message":
        return "ご連絡ありがとうございます。"
    return "ありがとうございます。"


def detect_scenario(source: dict) -> str:
    raw = source.get("raw_message", "")
    note = source.get("note", "")
    combined = f"{raw}\n{note}"

    if any(marker in combined for marker in ["STRIPE_SECRET_KEY", "sk_live_", "whsec_", "DATABASE_URL=", "秘密情報"]):
        return "live_secrets_pasted"
    if "外部API" in combined:
        return "external_api_shift"
    if "Googleドライブ" in combined or "Google Drive" in combined or "さくら" in combined:
        return "external_share_env_change"
    if "これ全部つながってますか" in combined:
        return "multiple_new_issues"
    if "どちらを見ればいい" in combined or "テスト環境と本番環境" in combined or ("テスト環境" in combined and "次は何をすればいい" in combined):
        return "which_environment_screen"
    if (
        "別の原因" in combined
        or "今回の不具合とは別" in combined
        or "一緒に見てもらうことは可能" in combined
        or "これも一緒に見てもら" in combined
        or "依頼した件とは別" in combined
        or "今やってもらってる件とは別" in combined
        or "元の依頼とは別" in combined
        or ("追加料金" in combined and "一緒に" in combined)
    ):
        return "extra_scope_question"
    if "キー名だけ共有" in combined or "値は送らなくて大丈夫" in combined:
        return "keys_shared"
    if "どのくらいかかりそう" in combined or "いつ直るのか" in combined:
        return "timeline_anxiety"
    return "generic_followup"


def build_case_from_source(source: dict) -> dict:
    raw = source.get("raw_message", "")
    scenario = detect_scenario(source)
    summary = shared.derive_summary(source)

    case = {
        "id": source.get("case_id") or source.get("id"),
        "src": source.get("route", "talkroom"),
        "state": "purchased",
        "raw_message": raw,
        "summary": summary,
        "reply_stance": {
            "burden_owner": "us",
            "empathy_first": source.get("emotional_tone") in {"anxious", "mixed", "frustrated"},
            "reply_skeleton": "post_purchase_quick",
        },
        "scenario": scenario,
    }

    if scenario == "live_secrets_pasted":
        case["reply_contract"] = {
            "primary_question_id": "q1",
            "explicit_questions": [
                {"id": "q1", "text": ".envの値を送ってよいか", "priority": "primary"},
            ],
            "answer_map": [
                {
                    "question_id": "q1",
                    "disposition": "answer_now",
                    "answer_brief": ".envや秘密値はこのまま扱わないので、以後は送らず、必要ならキー名だけで大丈夫です。",
                },
            ],
            "ask_map": [],
            "required_moves": ["react_briefly_first", "answer_directly_now", "commit_next_update_time"],
        }
        return case

    if scenario == "external_api_shift":
        case["reply_contract"] = {
            "primary_question_id": "q1",
            "explicit_questions": [
                {"id": "q1", "text": "このまま見てもらえますか", "priority": "primary"},
                {"id": "q2", "text": "料金変わりますか", "priority": "secondary"},
            ],
            "answer_map": [
                {
                    "question_id": "q1",
                    "disposition": "answer_after_check",
                    "answer_brief": "まず今回の件と同じ流れかを確認します。",
                    "hold_reason": "外部API側でも、今の依頼と同じ流れの中で起きているかはまだ未確定です。",
                    "revisit_trigger": "外部API側のエラー情報を受領したあとに、継続可否をお返しします。",
                },
                {
                    "question_id": "q2",
                    "disposition": "answer_now",
                    "answer_brief": "今の時点では料金はまだ変えません。",
                },
            ],
            "ask_map": [
                {
                    "id": "a1",
                    "question_ids": ["q1"],
                    "ask_text": "外部API側のエラーが分かる画面か文言だけ送ってください。",
                    "why_needed": "今回の依頼と同じ流れの中で起きているかを切るため",
                }
            ],
            "required_moves": ["react_briefly_first", "defer_with_reason", "request_minimum_evidence", "commit_next_update_time"],
        }
        return case

    if scenario == "external_share_env_change":
        case["reply_contract"] = {
            "primary_question_id": "q1",
            "explicit_questions": [
                {"id": "q1", "text": "Googleドライブで共有してよいか", "priority": "primary"},
                {"id": "q2", "text": "環境がVercelではなくさくらでも見てもらえるか", "priority": "secondary"},
            ],
            "answer_map": [
                {
                    "question_id": "q1",
                    "disposition": "answer_now",
                    "answer_brief": "Googleドライブは使わず、このトークルーム内で必要な分だけ送ってください。",
                },
                {
                    "question_id": "q2",
                    "disposition": "answer_now",
                    "answer_brief": "さくらのレンタルサーバー前提に切り替えて確認します。",
                },
            ],
            "ask_map": [
                {
                    "id": "a1",
                    "question_ids": ["q1", "q2"],
                    "ask_text": "次は、エラーが出ている画面かログの要点だけこのトークルームで送ってください。",
                    "why_needed": "先に届いている情報から確認を進めるため",
                }
            ],
            "required_moves": ["react_briefly_first", "answer_directly_now", "request_minimum_evidence", "commit_next_update_time"],
        }
        return case

    if scenario == "multiple_new_issues":
        case["reply_contract"] = {
            "primary_question_id": "q1",
            "explicit_questions": [
                {"id": "q1", "text": "これ全部つながっていますか", "priority": "primary"},
            ],
            "answer_map": [
                {
                    "question_id": "q1",
                    "disposition": "answer_after_check",
                    "answer_brief": "今の時点では、今回の件とつながっているかはまだ断定しません。",
                    "hold_reason": "元の不具合と、新しく出た2件の関連がまだ見えていない。",
                    "revisit_trigger": "追加の状況を受領したあとに、つながりがありそうかをお返しします。",
                },
            ],
            "ask_map": [
                {
                    "id": "a1",
                    "question_ids": ["q1"],
                    "ask_text": "管理画面のエラー画面と、メールが届かないことが分かる画面や状況があれば送ってください。",
                    "why_needed": "今回の件とつながっているかを先に切るため",
                }
            ],
            "required_moves": ["react_briefly_first", "defer_with_reason", "request_minimum_evidence", "commit_next_update_time"],
        }
        return case

    if scenario == "which_environment_screen":
        case["reply_contract"] = {
            "primary_question_id": "q1",
            "explicit_questions": [
                {"id": "q1", "text": "テスト環境と本番環境のどちらを見ればいいか", "priority": "primary"},
            ],
            "answer_map": [
                {
                    "question_id": "q1",
                    "disposition": "answer_now",
                    "answer_brief": "今回確認したい症状が出ている方を見てください。迷う場合は本番側を優先で大丈夫です。",
                },
            ],
            "ask_map": [],
            "required_moves": ["react_briefly_first", "answer_directly_now", "commit_next_update_time"],
        }
        return case

    if scenario == "extra_scope_question":
        case["reply_contract"] = {
            "primary_question_id": "q1",
            "explicit_questions": [
                {"id": "q1", "text": "これも一緒に見てもらうことは可能か", "priority": "primary"},
                {"id": "q2", "text": "追加料金はかかるか", "priority": "secondary"},
            ],
            "answer_map": [
                {
                    "question_id": "q1",
                    "disposition": "answer_after_check",
                    "answer_brief": "今回の件とつながっているならこのまま見ます。",
                    "hold_reason": "ただ、元の不具合と別の画面の話が同じ原因かはまだ未確定です。",
                    "revisit_trigger": "追加の症状を受領したあとに、今回の件とつながっているかをお返しします。",
                },
                {
                    "question_id": "q2",
                    "disposition": "answer_now",
                    "answer_brief": "別原因なら追加見積りになる可能性があります。まずは今回の件とつながっているかを先に見ます。",
                },
            ],
            "ask_map": [
                {
                    "id": "a1",
                    "question_ids": ["q1"],
                    "ask_text": "その画面で何が起きているかだけ短く送ってください。",
                    "why_needed": "今回の件と同じ原因かどうかを先に切るため",
                }
            ],
            "required_moves": ["react_briefly_first", "defer_with_reason", "request_minimum_evidence", "commit_next_update_time"],
        }
        return case

    if scenario == "keys_shared":
        case["reply_contract"] = {
            "primary_question_id": "q1",
            "explicit_questions": [
                {"id": "q1", "text": "キー名だけ共有すればよいか", "priority": "primary"},
            ],
            "answer_map": [
                {
                    "question_id": "q1",
                    "disposition": "answer_now",
                    "answer_brief": "はい、その共有の形で大丈夫です。値は引き続き不要です。",
                },
            ],
            "ask_map": [],
            "required_moves": ["react_briefly_first", "answer_directly_now", "commit_next_update_time"],
        }
        return case

    if scenario == "timeline_anxiety":
        case["reply_contract"] = {
            "primary_question_id": "q1",
            "explicit_questions": [
                {"id": "q1", "text": "完了までどのくらいかかりそうか", "priority": "primary"},
            ],
            "answer_map": [
                {
                    "question_id": "q1",
                    "disposition": "answer_after_check",
                    "answer_brief": "完了時期は、今の確認結果を見てからの方が正確です。",
                    "hold_reason": "現時点では原因と修正量がまだ固まっていません。",
                    "revisit_trigger": "現時点の見立てを整理したあとに、見通しをお返しします。",
                },
            ],
            "ask_map": [],
            "required_moves": ["react_briefly_first", "defer_with_reason", "commit_next_update_time"],
        }
        return case

    case["reply_contract"] = {
        "primary_question_id": "q1",
        "explicit_questions": [{"id": "q1", "text": "今回の件をどう進めるか", "priority": "primary"}],
        "answer_map": [
            {
                "question_id": "q1",
                "disposition": "answer_after_check",
                "answer_brief": "今の時点で答えられるところを整理してから返します。",
                "hold_reason": "追加報告の内容をまだ整理しきれていません。",
                "revisit_trigger": "確認後に、次の進め方をお返しします。",
            }
        ],
        "ask_map": [],
        "required_moves": ["react_briefly_first", "defer_with_reason", "commit_next_update_time"],
    }
    return case


def reaction_line(case: dict) -> str:
    scenario = case["scenario"]
    if scenario == "live_secrets_pasted":
        return "秘密情報が貼られている件、確認しました。"
    if scenario == "external_api_shift":
        return "原因がStripe側ではなく、外部API側にありそうとのこと、確認しました。"
    if scenario == "external_share_env_change":
        return "Googleドライブ共有の件と、Vercelではなくさくらのレンタルサーバーとのこと、確認しました。"
    if scenario == "multiple_new_issues":
        return "別のところも壊れた気がするとのこと、確認しました。"
    if scenario == "which_environment_screen":
        return "画面の確認先で迷っている件、確認しました。"
    if scenario == "extra_scope_question":
        return "別の画面の件も気になっているとのこと、確認しました。"
    if scenario == "keys_shared":
        return "キー名の共有ありがとうございます。確認しました。"
    if scenario == "timeline_anxiety":
        return "完了までの目安が気になっている件、確認しました。"
    return "追加のご連絡、確認しました。"


def render_case(case: dict) -> str:
    contract = case["reply_contract"]
    primary_id = contract["primary_question_id"]
    question_map = {item["id"]: item for item in contract["explicit_questions"]}
    answer_map = contract["answer_map"]
    primary = next(item for item in answer_map if item["question_id"] == primary_id)
    secondary_now = [item for item in answer_map if item["question_id"] != primary_id and item["disposition"] == "answer_now"]
    secondary_after = [item for item in answer_map if item["question_id"] != primary_id and item["disposition"] == "answer_after_check"]
    ask_map = contract.get("ask_map") or []

    sections: list[str] = []
    sections.append("\n".join([opener_for(case), reaction_line(case)]))

    now_lines: list[str] = []
    if primary["disposition"] == "answer_now":
        now_lines.append(primary["answer_brief"])
    for item in secondary_now:
        now_lines.append(item["answer_brief"])
    if now_lines:
        sections.append("\n".join(now_lines))

    after_lines: list[str] = []
    if primary["disposition"] == "answer_after_check":
        answer_brief = shared.compact_text(primary.get("answer_brief", ""))
        if answer_brief:
            after_lines.append(answer_brief)
        after_lines.append(primary["hold_reason"])
    for item in secondary_after:
        after_lines.append(item["hold_reason"])
    if after_lines:
        cleaned = []
        for line in after_lines:
            text = shared.compact_text(line)
            if text and text not in cleaned:
                cleaned.append(text if text.endswith("。") else f"{text}。")
        sections.append("\n".join(cleaned))

    if ask_map:
        ask_lines = []
        for ask in ask_map:
            ask_lines.append(ask["ask_text"])
        sections.append("\n".join(ask_lines))

    sections.append(time_commit())
    return "\n\n".join(section for section in sections if section.strip())


def main() -> int:
    parser = argparse.ArgumentParser(description="Render post_purchase_quick replies from flat purchased cases.")
    parser.add_argument("--fixture", required=True)
    parser.add_argument("--case-id")
    parser.add_argument("--limit", type=int)
    parser.add_argument("--save", action="store_true")
    args = parser.parse_args()

    cases = shared.load_cases(Path(args.fixture))
    selected = [case for case in cases if case.get("state") == "purchased"]
    if args.case_id:
        selected = [case for case in selected if case.get("id") == args.case_id or case.get("case_id") == args.case_id]
    if args.limit is not None:
        selected = selected[: args.limit]
    if not selected:
        print("[NG] no purchased cases selected")
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
