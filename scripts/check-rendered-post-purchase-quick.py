#!/usr/bin/env python3
from __future__ import annotations

import argparse
import importlib.util
import re
from pathlib import Path

from reply_quality_lint_common import collect_quality_style_errors, collect_reasoning_preservation_errors

ROOT_DIR = Path(__file__).resolve().parents[1]
RENDERER_PATH = ROOT_DIR / "scripts/render-post-purchase-quick.py"


def load_renderer():
    spec = importlib.util.spec_from_file_location("render_post_purchase_quick", RENDERER_PATH)
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


def first_nonempty_line(rendered: str) -> str:
    for raw_line in rendered.splitlines():
        line = raw_line.strip()
        if line:
            return line
    return ""


def is_complaint_like_source(source: dict) -> bool:
    raw = source.get("raw_message", "")
    tone = source.get("emotional_tone", "")
    if tone == "complaint_like":
        return True
    return any(
        marker in raw
        for marker in [
            "放置",
            "まだ何も進んでいません",
            "何度もやり取りしているのに",
            "1週間経っています",
            "いつになったら結果",
            "おっしゃっていたのに",
            "連絡がない",
        ]
    )


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


def buyer_word_pickup_ok(rendered: str, raw: str, scenario: str | None) -> bool:
    expected_markers = {
        "cancel_request": ["キャンセル", "返金", "進捗"],
        "progress_anxiety": ["進み", "進捗", "原因"],
        "evidence_offer_question": ["スクショ", "管理画面", "Stripe"],
        "repo_access_confirm": ["見られ", "アクセス"],
        "info_sufficiency_check": ["足り", "追加"],
        "suspected_cause_found": ["原因", "ログ", "priceId", "Webhook"],
        "symptom_shift_after_user_edit": ["コード", "症状", "送り直"],
        "handoff_fix_addon": ["修正", "費用", "内容"],
        "external_channel_request": ["トークルーム", "電話", "Slack", "LINE", "Zoom"],
        "direct_push_request": ["push", "トークルーム", "修正内容"],
        "deployment_help_request": ["本番反映", "手順"],
        "live_secrets_pasted": [".env", "キー名", "秘密"],
        "secret_handling_question": [".env", "キー名", "秘密"],
        "external_api_shift": ["外部API", "料金", "依頼側"],
        "multiple_new_issues": ["つなが", "管理画面", "メール"],
        "which_environment_screen": ["テスト環境", "本番環境"],
        "extra_scope_question": ["読み込み", "ページ", "画面", "金額", "今回の件"],
        "keys_shared": ["キー名", "値", "この情報"],
        "timeline_anxiety": ["完了", "見通し", "目安"],
        "delay_complaint_refund": ["進捗", "返金", "進み具合"],
        "price_pushback": ["料金", "固定料金", "キャッシュバック"],
        "extra_fee_anxiety": ["追加料金", "別原因", "料金"],
    }.get(scenario or "", [])

    if not expected_markers:
        return True
    if not any(marker in raw for marker in expected_markers):
        return True

    opening_window = "\n".join(split_sections(rendered)[:2])
    return any(marker in opening_window for marker in expected_markers)


def has_negation_only_answer(rendered: str, scenario: str | None) -> bool:
    answer_window = "\n".join(split_sections(rendered)[:2])
    if scenario == "external_channel_request":
        return has_any(answer_window, ["切り替えず", "しません"]) and "トークルーム" not in answer_window
    if scenario == "direct_push_request":
        return has_any(answer_window, ["前提にしていません", "できません"]) and not has_any(answer_window, ["トークルーム", "返します"])
    if scenario == "deployment_help_request":
        return has_any(answer_window, ["前提にしていません", "できません"]) and not has_any(answer_window, ["手順", "トークルーム"])
    if scenario in {"live_secrets_pasted", "secret_handling_question"}:
        return has_any(answer_window, ["扱わない", "送らず"]) and "キー名" not in answer_window
    return False


def buyer_compliance_respected(rendered: str, raw: str) -> bool:
    if not has_any(raw, ["キー名だけ共有", "値は送らなくて大丈夫"]):
        return True
    if has_any(rendered, ["秘密情報が貼られている", "以後は送らず"]):
        return False
    return has_any(rendered, ["キー名", "この情報で確認", "引き続き送らなくて大丈夫"])


def word_density_errors(rendered: str) -> list[str]:
    checks = {
        "現時点": 3,
        "お返しします": 3,
        "すみません": 2,
        "申し訳ありません": 2,
    }
    errors: list[str] = []
    for term, threshold in checks.items():
        if rendered.count(term) >= threshold:
            errors.append(f"word_density_check failed: `{term}` appears too often")
    return errors


def has_bad_emotion_label(rendered: str, source: dict) -> bool:
    if not is_complaint_like_source(source):
        return False
    return has_any(rendered, ["ご不安", "不安にさせ", "不安なお気持ち"])


def lint_case(module, source: dict) -> list[str]:
    case = module.build_case_from_source(source)
    rendered = module.render_case(case)
    contract = case["reply_contract"]
    temperature_plan = case.get("temperature_plan") or {}
    decision_plan = case.get("response_decision_plan") or {}
    service_grounding = case.get("service_grounding") or {}
    hard_constraints = case.get("hard_constraints") or {}
    scenario = case.get("scenario")
    raw = source.get("raw_message", "")
    complaint_like = is_complaint_like_source(source)
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
    if not case.get("render_payload"):
        errors.append("render_payload is missing")
    if case.get("render_payload_violations"):
        for violation in case["render_payload_violations"]:
            errors.append(f"render payload validator violation: {violation}")

    opening_line = first_nonempty_line(rendered)
    if complaint_like:
        if "ありがとう" in opening_line:
            errors.append("complaint_opening_check failed: complaint/anger reply still starts with gratitude")
        if not has_any(opening_line, ["すみません", "申し訳", "お待たせ"]):
            errors.append("complaint opening does not start with apology/ownership")
    elif not has_any(rendered, ["ありがとうございます", "確認しました"]):
        errors.append("missing brief reaction at the top")
    if not has_any(rendered, ["本日", "までに"]):
        errors.append("closing_present is missing")
    if "本日" not in rendered or "までに" not in rendered:
        errors.append("missing time commitment")
    if has_near_echo(rendered):
        errors.append("near_echo_check failed: adjacent sections still overlap too much")
    if not buyer_word_pickup_ok(rendered, raw, scenario):
        errors.append("buyer_word_pickup check failed")
    if has_negation_only_answer(rendered, scenario):
        errors.append("negation_only_answer check failed")
    if not buyer_compliance_respected(rendered, raw):
        errors.append("buyer_compliance_respect failed")
    if has_bad_emotion_label(rendered, source):
        errors.append("emotion_label_check failed")
    errors.extend(word_density_errors(rendered))
    if decision_plan.get("blocking_missing_facts") and any(ask.get("default_path_text") for ask in contract.get("ask_map") or []):
        if not has_any(rendered, ["なければ", "まだ", "すぐ出せなければ"]):
            errors.append("optional ask exists but rendered text has no default-path language")

    for answer in contract["answer_map"]:
        qid = answer["question_id"]
        qtext = next(item["text"] for item in contract["explicit_questions"] if item["id"] == qid)
        disposition = answer["disposition"]

        if disposition == "answer_now":
            if "料金" in qtext and not has_any(rendered, ["料金", "金額", "別で請求", "変えません", "見積り"]):
                errors.append("price-related answer_now question is not answered directly")
            if ".env" in qtext and not has_any(rendered, [".env", "キー名だけ"]):
                errors.append("secret-sharing answer_now question is not blocked directly")

        if disposition == "answer_after_check":
            if not has_any(rendered, ["まだ", "確認します", "未確定", "断定", "見ています", "整理して"]):
                errors.append("answer_after_check exists but defer language is weak")
            if "bridge_to_hold" in (decision_plan.get("response_order") or []) and not has_any(rendered, ["いまは", "先に確認しています", "先に見ています", "整理しています", "見立てを先に固めています"]):
                errors.append("answer_after_check exists but rendered text does not show current focus")

    direct_answer_line = decision_plan.get("direct_answer_line", "")
    if direct_answer_line and direct_answer_line not in rendered:
        errors.append("direct answer line is missing from rendered text")
    if direct_answer_line:
        direct_index = rendered.find(direct_answer_line)
        for marker in ["トークルーム", "そのまま無料追記では進めません", "確認が必要です"]:
            if marker in rendered and rendered.find(marker) < direct_index:
                errors.append("direct answer appears after procedure text")
                break
        for ask in contract.get("ask_map") or []:
            ask_text = ask.get("ask_text", "")
            if ask_text and ask_text in rendered and rendered.find(ask_text) < direct_index:
                errors.append("direct answer appears after ask")
                break

    if not decision_plan.get("blocking_missing_facts") and case.get("scenario") != "evidence_offer_question":
        for ask in contract.get("ask_map") or []:
            ask_text = ask.get("ask_text", "")
            if ask_text and ask_text in rendered:
                errors.append("rendered text re-asks despite no blocking missing facts")
        known_facts = set(decision_plan.get("facts_known", []))
        if known_facts.intersection({"zip_already_sent", "symptom_surface_described", "extra_fee_question_present", "same_cause_relation_question_present"}) and has_any(rendered, ["送ってください", "教えてください"]):
            errors.append("rendered text asks for information already present in the buyer message")
    if case.get("scenario") == "progress_anxiety":
        if not has_any(direct_answer_line, ["まだ", "断定できていません", "切り分け中"]):
            errors.append("progress anxiety direct answer does not state current status clearly")
    if case.get("scenario") == "delay_complaint_refund":
        if not has_any(rendered, ["進捗", "進み具合", "整理"]):
            errors.append("delay/refund case does not state the current progress handling")
        if not has_any(rendered, ["返金"]):
            errors.append("delay/refund case does not land the refund concern")
    if "Googleドライブ" in raw or "Google Drive" in raw:
        if not has_any(rendered, ["トークルーム", "Googleドライブは使わず"]):
            errors.append("external share suggestion exists but rendered text does not stop it clearly")
    if ".env" in raw and "値は送らなくて大丈夫" not in raw:
        if not has_any(rendered, [".env", "キー名だけ"]):
            errors.append("raw .env mention exists but rendered text does not mention secret handling")
    if has_any(raw, ["別なんですが", "別のところ", "一緒に見てもら", "これも一緒", "今回とは別", "別の画面"]):
        if not has_any(rendered, ["今回の件", "別の話", "つながっている", "同じ流れ", "同じ原因"]):
            errors.append("scope-addition case exists but rendered text does not mention relation/scope split")
    if case.get("scenario") == "extra_scope_question" and "追加料金" in raw:
        if not has_any(rendered, ["追加見積り", "追加料金"]):
            errors.append("scope-addition case does not answer the fee concern")
    if case.get("scenario") == "generic_followup" and has_any(
        raw,
        [
            "キャッシュバック",
            "追加料金",
            "話が違う",
            "返金",
            "どっち",
            "安く",
            "キャンセル",
            "進捗",
            "スクショ",
            "Slack",
            "電話",
            "Zoom",
            "LINE",
            "GitHub",
            "push",
            "デプロイ",
            "unittest",
            "priceId",
            "Cannot read properties",
            "Webhook",
            "URLパス",
            "引き継ぎメモ",
            "修正もお願い",
            "大丈夫そうですか",
            "ちゃんと見れましたか",
            "足りてますか",
            "忘れてて",
            "差額払う",
            "送り直す",
            "前のは破棄",
            "フローは",
            "重複決済",
        ],
    ):
        errors.append("generic_followup fallback survived a concrete purchased follow-up request")

    forbidden_terms = ["GitHubに招待", "Driveに置いて", "Dropbox", "外部決済"]
    for term in forbidden_terms:
        if term in rendered:
            errors.append(f"forbidden term leaked into rendered text: {term}")

    errors.extend(collect_quality_style_errors(rendered))
    errors.extend(collect_reasoning_preservation_errors(rendered, raw, decision_plan, case.get("scenario")))
    return errors


def main() -> int:
    parser = argparse.ArgumentParser(description="Lint rendered post_purchase_quick replies.")
    parser.add_argument("--fixture", required=True)
    parser.add_argument("--case-id")
    parser.add_argument("--limit", type=int)
    args = parser.parse_args()

    module = load_renderer()
    cases = module.shared.load_cases(Path(args.fixture))
    cases = [case for case in cases if case.get("state") == "purchased"]
    if args.case_id:
        cases = [case for case in cases if case.get("case_id") == args.case_id or case.get("id") == args.case_id]
    if args.limit is not None:
        cases = cases[: args.limit]
    if not cases:
        print("[NG] no purchased cases selected")
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
    print(f"[OK] rendered post_purchase_quick lint passed: {len(cases)} case(s)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
